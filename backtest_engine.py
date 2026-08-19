import pandas as pd
import numpy as np


# ============================================================
# SAFE NUMBER
# ============================================================

def safe_number(value, default=0.0):

    try:

        if value is None or pd.isna(value):
            return default

        return float(value)

    except Exception:

        return default


# ============================================================
# OPTION PREMIUM
# ============================================================

def get_option_premium(
    df,
    strike,
    option_type
):
    """
    Get CE/PE LTP for a particular strike.
    """

    if df is None or df.empty:
        return np.nan

    strike = float(strike)

    if "strike" not in df.columns:
        return np.nan

    if option_type == "CE":

        column = "ce_ltp"

    elif option_type == "PE":

        column = "pe_ltp"

    else:

        raise ValueError(
            "option_type must be CE or PE"
        )

    if column not in df.columns:
        return np.nan

    rows = df[
        pd.to_numeric(
            df["strike"],
            errors="coerce"
        ) == strike
    ]

    if rows.empty:
        return np.nan

    return safe_number(
        rows[column].iloc[0],
        np.nan
    )


# ============================================================
# LEG ENTRY
# ============================================================

def create_backtest_entry(
    leg,
    entry_df
):

    entry_premium = get_option_premium(
        entry_df,
        leg["strike"],
        leg["option_type"]
    )

    result = leg.copy()

    result["entry_premium"] = entry_premium

    return result


# ============================================================
# LEG EXIT P&L
# ============================================================

def calculate_leg_exit_pnl(
    leg,
    exit_df
):

    entry_premium = safe_number(
        leg.get("entry_premium"),
        np.nan
    )

    exit_premium = get_option_premium(
        exit_df,
        leg["strike"],
        leg["option_type"]
    )

    quantity = safe_number(
        leg.get("quantity"),
        1
    )

    action = str(
        leg.get("action", "BUY")
    ).upper()

    if pd.isna(entry_premium):
        return np.nan

    if pd.isna(exit_premium):
        return np.nan

    # BUY:
    # profit = exit - entry
    #
    # SELL:
    # profit = entry - exit

    if action == "BUY":

        pnl = (
            exit_premium
            - entry_premium
        ) * quantity

    elif action == "SELL":

        pnl = (
            entry_premium
            - exit_premium
        ) * quantity

    else:

        raise ValueError(
            "action must be BUY or SELL"
        )

    return pnl


# ============================================================
# STRATEGY EXIT P&L
# ============================================================

def calculate_strategy_exit_pnl(
    legs,
    exit_df
):

    total_pnl = 0.0

    leg_results = []

    for leg in legs:

        pnl = calculate_leg_exit_pnl(
            leg,
            exit_df
        )

        leg_result = leg.copy()

        leg_result["exit_premium"] = (
            get_option_premium(
                exit_df,
                leg["strike"],
                leg["option_type"]
            )
        )

        leg_result["pnl"] = pnl

        leg_results.append(
            leg_result
        )

        if not pd.isna(pnl):

            total_pnl += pnl

    return (
        total_pnl,
        leg_results
    )


# ============================================================
# SINGLE BACKTEST TRADE
# ============================================================

def run_single_trade(
    legs,
    entry_df,
    exit_df,
    entry_time=None,
    exit_time=None
):

    # --------------------------------------------------------
    # Create entry legs
    # --------------------------------------------------------

    entry_legs = []

    for leg in legs:

        entry_leg = create_backtest_entry(
            leg,
            entry_df
        )

        entry_legs.append(
            entry_leg
        )

    # --------------------------------------------------------
    # Calculate exit P&L
    # --------------------------------------------------------

    total_pnl, leg_results = (
        calculate_strategy_exit_pnl(
            entry_legs,
            exit_df
        )
    )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    result = {

        "entry_time": entry_time,

        "exit_time": exit_time,

        "strategy_pnl": total_pnl,

        "legs": leg_results
    }

    return result


# ============================================================
# SNAPSHOT BACKTEST
# ============================================================

def backtest_strategy(
    snapshots,
    legs,
    entry_index=0,
    exit_index=None
):
    """
    Run one strategy trade across historical snapshots.

    snapshots:
        List of dictionaries containing:
            timestamp
            data

    Example:

        snapshots = [
            {
                "timestamp": "...",
                "data": dataframe
            },
            ...
        ]
    """

    if not snapshots:

        raise ValueError(
            "No historical snapshots available."
        )

    if entry_index >= len(snapshots):

        raise IndexError(
            "Entry index is outside snapshot range."
        )

    if exit_index is None:

        exit_index = len(snapshots) - 1

    if exit_index >= len(snapshots):

        raise IndexError(
            "Exit index is outside snapshot range."
        )

    if exit_index <= entry_index:

        raise ValueError(
            "Exit must occur after entry."
        )

    entry_snapshot = snapshots[
        entry_index
    ]

    exit_snapshot = snapshots[
        exit_index
    ]

    result = run_single_trade(
        legs=legs,
        entry_df=entry_snapshot["data"],
        exit_df=exit_snapshot["data"],
        entry_time=entry_snapshot.get(
            "timestamp"
        ),
        exit_time=exit_snapshot.get(
            "timestamp"
        )
    )

    return result


# ============================================================
# MULTI-TRADE BACKTEST
# ============================================================

def run_backtest(
    trades
):
    """
    Convert individual trade results
    into a performance DataFrame.
    """

    if not trades:

        return pd.DataFrame()

    rows = []

    for trade in trades:

        rows.append(
            {
                "entry_time":
                    trade.get("entry_time"),

                "exit_time":
                    trade.get("exit_time"),

                "strategy_pnl":
                    trade.get("strategy_pnl", 0)
            }
        )

    result = pd.DataFrame(
        rows
    )

    if result.empty:
        return result

    # --------------------------------------------------------
    # Cumulative P&L
    # --------------------------------------------------------

    result["cumulative_pnl"] = (
        result["strategy_pnl"]
        .fillna(0)
        .cumsum()
    )

    # --------------------------------------------------------
    # Win / Loss
    # --------------------------------------------------------

    result["result"] = np.where(
        result["strategy_pnl"] > 0,
        "WIN",
        np.where(
            result["strategy_pnl"] < 0,
            "LOSS",
            "BREAKEVEN"
        )
    )

    return result


# ============================================================
# PERFORMANCE METRICS
# ============================================================

def calculate_backtest_metrics(
    results
):

    if results is None or results.empty:

        return {}

    pnl = pd.to_numeric(
        results["strategy_pnl"],
        errors="coerce"
    ).fillna(0)

    total_trades = len(
        results
    )

    winning_trades = int(
        (pnl > 0).sum()
    )

    losing_trades = int(
        (pnl < 0).sum()
    )

    breakeven_trades = int(
        (pnl == 0).sum()
    )

    total_pnl = pnl.sum()

    average_pnl = pnl.mean()

    win_rate = (
        winning_trades
        / total_trades
        * 100
        if total_trades
        else 0
    )

    gross_profit = pnl[
        pnl > 0
    ].sum()

    gross_loss = abs(
        pnl[
            pnl < 0
        ].sum()
    )

    profit_factor = (
        gross_profit / gross_loss
        if gross_loss > 0
        else np.inf
    )

    cumulative = pnl.cumsum()

    running_max = cumulative.cummax()

    drawdown = (
        cumulative
        - running_max
    )

    max_drawdown = drawdown.min()

    return {

        "total_trades":
            total_trades,

        "winning_trades":
            winning_trades,

        "losing_trades":
            losing_trades,

        "breakeven_trades":
            breakeven_trades,

        "total_pnl":
            total_pnl,

        "average_pnl":
            average_pnl,

        "win_rate":
            win_rate,

        "gross_profit":
            gross_profit,

        "gross_loss":
            gross_loss,

        "profit_factor":
            profit_factor,

        "max_drawdown":
            max_drawdown
    }
    