import pandas as pd

from backtest_data import (
    load_historical_snapshots,
)

from backtest_engine import (
    run_single_trade,
    run_backtest,
    calculate_backtest_metrics,
)


# ============================================================
# SNAPSHOT HELPERS
# ============================================================

def find_snapshot_index(
    snapshots,
    timestamp
):
    """
    Find the snapshot index closest to the requested timestamp.
    """

    if not snapshots:
        return None

    target = pd.to_datetime(
        timestamp,
        errors="coerce"
    )

    if pd.isna(target):
        return None

    timestamps = []

    for snapshot in snapshots:

        ts = pd.to_datetime(
            snapshot.get("timestamp"),
            errors="coerce"
        )

        timestamps.append(ts)

    valid = [
        (i, ts)
        for i, ts in enumerate(timestamps)
        if not pd.isna(ts)
    ]

    if not valid:
        return None

    return min(
        valid,
        key=lambda item:
            abs(item[1] - target)
    )[0]


def snapshot_has_legs(
    snapshot,
    legs
):
    """
    Check whether all requested strategy legs
    have valid premiums in a snapshot.
    """

    if not snapshot:
        return False

    df = snapshot.get("data")

    if df is None or df.empty:
        return False

    for leg in legs:

        strike = float(
            leg["strike"]
        )

        option_type = str(
            leg["option_type"]
        ).upper()

        if option_type == "CE":
            column = "ce_ltp"
        elif option_type == "PE":
            column = "pe_ltp"
        else:
            return False

        if column not in df.columns:
            return False

        rows = df[
            pd.to_numeric(
                df["strike"],
                errors="coerce"
            ) == strike
        ]

        if rows.empty:
            return False

        premium = pd.to_numeric(
            rows[column],
            errors="coerce"
        ).iloc[0]

        if pd.isna(premium):
            return False

    return True


# ============================================================
# SINGLE STRATEGY BACKTEST
# ============================================================

def run_single_backtest(
    expiry,
    trade_date,
    entry_time,
    exit_time,
    legs,
):
    """
    Run one historical strategy trade.

    Parameters
    ----------
    expiry:
        Selected option expiry.

    trade_date:
        Historical trading date.

    entry_time:
        Entry timestamp.

    exit_time:
        Exit timestamp.

    legs:
        Strategy leg list.
    """

    if not legs:

        raise ValueError(
            "No strategy legs supplied."
        )

    # --------------------------------------------------------
    # Load only selected expiry/date
    # --------------------------------------------------------

    snapshots = load_historical_snapshots(

        expiry=expiry,

        start_date=trade_date,

        end_date=trade_date,
    )

    if not snapshots:

        raise RuntimeError(
            "No historical snapshots found "
            "for the selected expiry/date."
        )

    # --------------------------------------------------------
    # Locate requested snapshots
    # --------------------------------------------------------

    entry_index = find_snapshot_index(
        snapshots,
        entry_time
    )

    exit_index = find_snapshot_index(
        snapshots,
        exit_time
    )

    if entry_index is None:

        raise RuntimeError(
            "Entry snapshot could not be found."
        )

    if exit_index is None:

        raise RuntimeError(
            "Exit snapshot could not be found."
        )

    if exit_index <= entry_index:

        raise ValueError(
            "Exit time must be after entry time."
        )

    entry_snapshot = snapshots[
        entry_index
    ]

    exit_snapshot = snapshots[
        exit_index
    ]

    # --------------------------------------------------------
    # Validate strategy availability
    # --------------------------------------------------------

    if not snapshot_has_legs(
        entry_snapshot,
        legs
    ):

        raise RuntimeError(
            "One or more strategy legs "
            "are unavailable at entry."
        )

    if not snapshot_has_legs(
        exit_snapshot,
        legs
    ):

        raise RuntimeError(
            "One or more strategy legs "
            "are unavailable at exit."
        )

    # --------------------------------------------------------
    # Execute trade
    # --------------------------------------------------------

    trade = run_single_trade(

        legs=legs,

        entry_df=entry_snapshot["data"],

        exit_df=exit_snapshot["data"],

        entry_time=entry_snapshot["timestamp"],

        exit_time=exit_snapshot["timestamp"],
    )

    # --------------------------------------------------------
    # Performance table
    # --------------------------------------------------------

    results = run_backtest(
        [trade]
    )

    metrics = calculate_backtest_metrics(
        results
    )

    return {
        "trade": trade,
        "results": results,
        "metrics": metrics,
        "snapshots": snapshots,
        "entry_index": entry_index,
        "exit_index": exit_index,
    }


# ============================================================
# MULTI-TRADE BACKTEST
# ============================================================

def run_multi_trade_backtest(
    snapshots,
    legs,
    entry_step=1,
    holding_steps=1,
):
    """
    Run repeated trades across snapshots.

    Example:

        entry_step=1
        holding_steps=1

    means:

        0 -> 1
        1 -> 2
        2 -> 3
        ...
    """

    if not snapshots:

        raise ValueError(
            "No snapshots supplied."
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

        # ----------------------------------------------------
        # Check legs
        # ----------------------------------------------------

        if not snapshot_has_legs(
            entry_snapshot,
            legs
        ):

            entry_index += entry_step
            continue

        if not snapshot_has_legs(
            exit_snapshot,
            legs
        ):

            entry_index += entry_step
            continue

        # ----------------------------------------------------
        # Trade
        # ----------------------------------------------------

        trade = run_single_trade(

            legs=legs,

            entry_df=entry_snapshot["data"],

            exit_df=exit_snapshot["data"],

            entry_time=entry_snapshot["timestamp"],

            exit_time=exit_snapshot["timestamp"],
        )

        trades.append(
            trade
        )

        entry_index += entry_step

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

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
# AVAILABLE SNAPSHOT INFORMATION
# ============================================================

def get_backtest_snapshot_info(
    expiry,
    trade_date
):
    """
    Return snapshot information for the UI.
    """

    snapshots = load_historical_snapshots(

        expiry=expiry,

        start_date=trade_date,

        end_date=trade_date,
    )

    rows = []

    for index, snapshot in enumerate(
        snapshots
    ):

        df = snapshot["data"]

        spot = None
        pcr = None

        if (
            df is not None
            and not df.empty
        ):

            if "spot_price" in df.columns:

                values = pd.to_numeric(
                    df["spot_price"],
                    errors="coerce"
                ).dropna()

                if not values.empty:
                    spot = float(
                        values.iloc[0]
                    )

            if "pcr" in df.columns:

                values = pd.to_numeric(
                    df["pcr"],
                    errors="coerce"
                ).dropna()

                if not values.empty:
                    pcr = float(
                        values.iloc[0]
                    )

        rows.append(
            {
                "index": index,
                "timestamp": snapshot[
                    "timestamp"
                ],
                "spot_price": spot,
                "pcr": pcr,
                "rows": len(df),
            }
        )

    return pd.DataFrame(
        rows
    )


# ============================================================
# TEST
# ============================================================

def main():

    print(
        "\n========================================"
    )

    print(
        "SQLITE BACKTEST RUNNER"
    )

    print(
        "========================================"
    )

    # --------------------------------------------------------
    # Use one known expiry/date for testing
    # --------------------------------------------------------

    expiry = "2026-08-18"

    trade_date = "2026-08-18"

    # --------------------------------------------------------
    # Load snapshots
    # --------------------------------------------------------

    snapshots = load_historical_snapshots(

        expiry=expiry,

        start_date=trade_date,

        end_date=trade_date,
    )

    print(
        "\nSnapshots:",
        len(snapshots)
    )

    if len(snapshots) < 2:

        raise RuntimeError(
            "Need at least two snapshots."
        )

    print(
        "First:",
        snapshots[0]["timestamp"]
    )

    print(
        "Last:",
        snapshots[-1]["timestamp"]
    )

    # --------------------------------------------------------
    # Determine ATM
    # --------------------------------------------------------

    first_df = snapshots[0]["data"]

    spot_values = pd.to_numeric(
        first_df["spot_price"],
        errors="coerce"
    ).dropna()

    if spot_values.empty:

        raise RuntimeError(
            "Spot price unavailable."
        )

    spot = float(
        spot_values.iloc[0]
    )

    strikes = pd.to_numeric(
        first_df["strike"],
        errors="coerce"
    ).dropna().unique()

    atm = min(
        strikes,
        key=lambda x:
            abs(x - spot)
    )

    print(
        "\nSpot:",
        spot
    )

    print(
        "ATM:",
        atm
    )

    # --------------------------------------------------------
    # Test long straddle
    # --------------------------------------------------------

    legs = [

        {
            "strike": atm,
            "option_type": "CE",
            "action": "BUY",
            "quantity": 75,
        },

        {
            "strike": atm,
            "option_type": "PE",
            "action": "BUY",
            "quantity": 75,
        },

    ]

    # --------------------------------------------------------
    # First → last snapshot
    # --------------------------------------------------------

    output = run_single_backtest(

        expiry=expiry,

        trade_date=trade_date,

        entry_time=snapshots[0]["timestamp"],

        exit_time=snapshots[-1]["timestamp"],

        legs=legs,
    )

    metrics = output["metrics"]

    print(
        "\n========================================"
    )

    print(
        "RESULT"
    )

    print(
        "========================================"
    )

    print(
        "Total P&L:",
        metrics.get(
            "total_pnl",
            0
        )
    )

    print(
        "Win Rate:",
        metrics.get(
            "win_rate",
            0
        )
    )

    print(
        "Profit Factor:",
        metrics.get(
            "profit_factor",
            0
        )
    )

    print(
        "Max Drawdown:",
        metrics.get(
            "max_drawdown",
            0
        )
    )

    print(
        "\n========================================"
    )


if __name__ == "__main__":
    main()
    