import pandas as pd
import numpy as np

from backtest_data import load_historical_snapshots
from backtest_engine import (
    run_single_trade,
    run_backtest,
    calculate_backtest_metrics,
)


# ============================================================
# STRATEGY BACKTEST
# ============================================================

def backtest_strategy_over_snapshots(
    snapshots,
    legs,
    entry_step=1,
    holding_steps=1,
):
    """
    Run repeated strategy trades across historical snapshots.

    Example:

        entry_step = 1
        holding_steps = 1

    means:

        Snapshot 0 → Snapshot 1
        Snapshot 1 → Snapshot 2
        Snapshot 2 → Snapshot 3

    """

    if not snapshots:

        raise ValueError(
            "No historical snapshots available."
        )

    if not legs:

        raise ValueError(
            "No strategy legs supplied."
        )

    if entry_step < 1:

        raise ValueError(
            "entry_step must be >= 1."
        )

    if holding_steps < 1:

        raise ValueError(
            "holding_steps must be >= 1."
        )

    trades = []

    entry_index = 0

    while (
        entry_index + holding_steps
        < len(snapshots)
    ):

        exit_index = (
            entry_index
            + holding_steps
        )

        entry_snapshot = (
            snapshots[entry_index]
        )

        exit_snapshot = (
            snapshots[exit_index]
        )

        trade = run_single_trade(

            legs=legs,

            entry_df=entry_snapshot["data"],

            exit_df=exit_snapshot["data"],

            entry_time=entry_snapshot[
                "timestamp"
            ],

            exit_time=exit_snapshot[
                "timestamp"
            ],
        )

        trades.append(trade)

        entry_index += entry_step

    return trades


# ============================================================
# COMPLETE BACKTEST
# ============================================================

def run_strategy_backtest(
    snapshots,
    legs,
    entry_step=1,
    holding_steps=1,
):
    """
    Run strategy backtest and return:

        results
        metrics
        trades
    """

    trades = backtest_strategy_over_snapshots(

        snapshots=snapshots,

        legs=legs,

        entry_step=entry_step,

        holding_steps=holding_steps,
    )

    results = run_backtest(
        trades
    )

    metrics = calculate_backtest_metrics(
        results
    )

    return {
        "trades": trades,
        "results": results,
        "metrics": metrics,
    }


# ============================================================
# FILTER VALID TRADES
# ============================================================

def remove_invalid_trades(
    results
):
    """
    Remove trades where strategy P&L
    could not be calculated.
    """

    if results is None:
        return pd.DataFrame()

    if results.empty:
        return results

    result = results.copy()

    result["strategy_pnl"] = pd.to_numeric(
        result["strategy_pnl"],
        errors="coerce"
    )

    result = result.dropna(
        subset=["strategy_pnl"]
    )

    return (
        result
        .reset_index(drop=True)
    )


# ============================================================
# SUMMARY
# ============================================================

def create_backtest_summary(
    results,
    metrics
):
    """
    Create a compact summary dictionary
    for Streamlit KPI cards.
    """

    if results is None or results.empty:

        return {
            "total_trades": 0,
            "total_pnl": 0,
            "win_rate": 0,
            "average_pnl": 0,
            "max_drawdown": 0,
            "profit_factor": 0,
        }

    return {

        "total_trades":
            metrics.get(
                "total_trades",
                0
            ),

        "total_pnl":
            metrics.get(
                "total_pnl",
                0
            ),

        "win_rate":
            metrics.get(
                "win_rate",
                0
            ),

        "average_pnl":
            metrics.get(
                "average_pnl",
                0
            ),

        "max_drawdown":
            metrics.get(
                "max_drawdown",
                0
            ),

        "profit_factor":
            metrics.get(
                "profit_factor",
                0
            ),
    }


# ============================================================
# TEST STRATEGY
# ============================================================

if __name__ == "__main__":

    print("\n========================================")
    print("STRATEGY BACKTEST TEST")
    print("========================================")

    # --------------------------------------------------------
    # Load snapshots
    # --------------------------------------------------------

    snapshots = load_historical_snapshots(
    expiry="2026-08-18"
)

    print(
        f"\nSnapshots loaded: {len(snapshots)}"
    )

    if len(snapshots) < 2:

        print(
            "\nNot enough snapshots "
            "for backtesting."
        )

        raise SystemExit

    # --------------------------------------------------------
    # Determine ATM strike
    # --------------------------------------------------------

    first_df = snapshots[0]["data"]

    spot = pd.to_numeric(
        first_df["spot_price"],
        errors="coerce"
    ).dropna()

    if spot.empty:

        print(
            "\nSpot price unavailable."
        )

        raise SystemExit

    spot_price = float(
        spot.iloc[0]
    )

    strikes = pd.to_numeric(
        first_df["strike"],
        errors="coerce"
    ).dropna().unique()

    if len(strikes) == 0:

        print(
            "\nNo strikes available."
        )

        raise SystemExit

    atm_strike = min(
        strikes,
        key=lambda x:
            abs(x - spot_price)
    )

    print(
        f"\nSpot price: {spot_price}"
    )

    print(
        f"ATM strike: {atm_strike}"
    )

    # --------------------------------------------------------
    # TEST STRATEGY
    #
    # Long Straddle
    #
    # BUY ATM CE
    # BUY ATM PE
    # --------------------------------------------------------

    legs = [

        {
            "strike": atm_strike,
            "option_type": "CE",
            "action": "BUY",
            "quantity": 75,
        },

        {
            "strike": atm_strike,
            "option_type": "PE",
            "action": "BUY",
            "quantity": 75,
        },

    ]

    # --------------------------------------------------------
    # Run
    # --------------------------------------------------------

    output = run_strategy_backtest(

        snapshots=snapshots,

        legs=legs,

        entry_step=1,

        holding_steps=1,
    )

    results = output["results"]

    metrics = output["metrics"]

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print(
        "\n----------------------------------------"
    )

    print(
        "BACKTEST RESULTS"
    )

    print(
        "----------------------------------------"
    )

    print(
        f"Total Trades   : "
        f"{metrics.get('total_trades', 0)}"
    )

    print(
        f"Winning Trades : "
        f"{metrics.get('winning_trades', 0)}"
    )

    print(
        f"Losing Trades  : "
        f"{metrics.get('losing_trades', 0)}"
    )

    print(
        f"Total P&L      : "
        f"{metrics.get('total_pnl', 0):.2f}"
    )

    print(
        f"Average P&L    : "
        f"{metrics.get('average_pnl', 0):.2f}"
    )

    print(
        f"Win Rate       : "
        f"{metrics.get('win_rate', 0):.2f}%"
    )

    print(
        f"Profit Factor  : "
        f"{metrics.get('profit_factor', 0):.2f}"
    )

    print(
        f"Max Drawdown   : "
        f"{metrics.get('max_drawdown', 0):.2f}"
    )

    print(
        "\n----------------------------------------"
    )

    print(
        "TRADE RESULTS"
    )

    print(
        "----------------------------------------"
    )

    if not results.empty:

        print(
            results.to_string(
                index=False
            )
        )

    else:

        print(
            "No trades generated."
        )

    print(
        "\n========================================"
    )
    