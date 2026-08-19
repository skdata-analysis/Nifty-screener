import os
import glob
import pandas as pd

from backtest_engine import (
    run_single_trade,
    run_backtest,
    calculate_backtest_metrics
)
from historical_chain_adapter import (
    convert_historical_snapshot
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

CHAIN_DIR = os.path.join(
    BASE_DIR,
    "data",
    "historical",
    "chains"
)


# ============================================================
# LOAD CHAIN SNAPSHOTS
# ============================================================

def load_chain_snapshots():

    files = sorted(
        glob.glob(
            os.path.join(
                CHAIN_DIR,
                "chain_*.csv"
            )
        )
    )

    if not files:
        raise RuntimeError(
            "No historical chain snapshots found."
        )

    snapshots = []

    for file in files:

        try:

            df = pd.read_csv(file)

            if df.empty:
                continue

            # --------------------------------------------
            # TIMESTAMP
            # --------------------------------------------

            if "timestamp" not in df.columns:
                continue

            df["timestamp"] = pd.to_datetime(
                df["timestamp"],
                errors="coerce"
            )

            # --------------------------------------------
            # STRIKE
            # --------------------------------------------

            if "strike" in df.columns:

                df["strike"] = pd.to_numeric(
                    df["strike"],
                    errors="coerce"
                )

            # --------------------------------------------
            # OPTION TYPE
            # --------------------------------------------

            if "option_type" not in df.columns:

                df["option_type"] = None

            df["option_type"] = (
                df["option_type"]
                .astype(str)
                .str.upper()
                .str.strip()
            )

            # --------------------------------------------
            # RECOVER OPTION TYPE FROM SYMBOL
            # --------------------------------------------

            if "trading_symbol" in df.columns:

                symbol = (
                    df["trading_symbol"]
                    .astype(str)
                    .str.upper()
                    .str.strip()
                )

                df.loc[
                    symbol.str.contains(" CE "),
                    "option_type"
                ] = "CE"

                df.loc[
                    symbol.str.contains(" PE "),
                    "option_type"
                ] = "PE"

            # --------------------------------------------
            # REMOVE INVALID ROWS
            # --------------------------------------------

            df = df.dropna(
                subset=[
                    "timestamp",
                    "strike"
                ]
            )

            df = df[
                df["option_type"].isin(
                    ["CE", "PE"]
                )
            ]

            if df.empty:
                continue

            # --------------------------------------------
            # SNAPSHOT
            # --------------------------------------------

            chain_df = convert_historical_snapshot(
                df
            )

            if chain_df.empty:
                continue

            snapshots.append(
                {
                    "timestamp":
                        df["timestamp"].iloc[0],

                    "data":
                        chain_df
                }
            )

        except Exception as e:

            print(
                f"Skipping {os.path.basename(file)}: {e}"
            )

    if not snapshots:

        raise RuntimeError(
            "No valid historical snapshots found."
        )

    return snapshots


# ============================================================
# TEST STRATEGY
# ============================================================

def create_test_strategy():

    """
    Simple short strangle.

    SELL 21600 PE
    SELL 24400 CE

    This is only a test strategy.
    """

    legs = [

        {
            "strike": 21600,
            "option_type": "PE",
            "action": "SELL",
            "quantity": 65
        },

        {
            "strike": 24400,
            "option_type": "CE",
            "action": "SELL",
            "quantity": 65
        }

    ]

    return legs


# ============================================================
# MAIN BACKTEST
# ============================================================

def main():

    print("\n========================================")
    print("STRATEGY BACKTEST RUNNER")
    print("========================================")

    # --------------------------------------------------------
    # LOAD SNAPSHOTS
    # --------------------------------------------------------

    snapshots = load_chain_snapshots()

    print(
        "\nSnapshots loaded:",
        len(snapshots)
    )

    if len(snapshots) < 2:

        raise RuntimeError(
            "Need at least 2 snapshots."
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
    # STRATEGY
    # --------------------------------------------------------

    legs = create_test_strategy()

    print("\nStrategy:")
    print("SHORT STRANGLE")

    for leg in legs:

        print(
            f'{leg["action"]} '
            f'{leg["strike"]} '
            f'{leg["option_type"]} '
            f'Qty={leg["quantity"]}'
        )

    # --------------------------------------------------------
    # FIND VALID ENTRY
    # --------------------------------------------------------

    entry_index = None
    exit_index = None

    for i, snapshot in enumerate(
        snapshots
    ):

        df = snapshot["data"]

        required = {
            (21600, "PE"),
            (24400, "CE")
        }

        available = set()

        for _, row in df.iterrows():

            strike = row["strike"]

            if pd.notna(row.get("ce_ltp")):

                available.add(
                    (float(strike), "CE")
                )

            if pd.notna(row.get("pe_ltp")):

                available.add(
                    (float(strike), "PE")
                )

        if required.issubset(
            available
        ):

            entry_index = i
            break

    if entry_index is None:

        raise RuntimeError(
            "No snapshot contains both strategy legs."
        )

    # --------------------------------------------------------
    # EXIT
    # --------------------------------------------------------

    for i in range(
        len(snapshots) - 1,
        entry_index,
        -1
    ):

        df = snapshots[i]["data"]

        available = set()

        for _, row in df.iterrows():

            strike = row["strike"]

            if pd.notna(row.get("ce_ltp")):

                available.add(
                    (float(strike), "CE")
                )

            if pd.notna(row.get("pe_ltp")):

                available.add(
                    (float(strike), "PE")
                )

        if {
            (21600, "PE"),
            (24400, "CE")
        }.issubset(
            available
        ):

            exit_index = i
            break

    if exit_index is None:

        raise RuntimeError(
            "No valid exit snapshot found."
        )

    print(
        "\nEntry:",
        snapshots[
            entry_index
        ]["timestamp"]
    )

    print(
        "Exit:",
        snapshots[
            exit_index
        ]["timestamp"]
    )

    # --------------------------------------------------------
    # RUN TRADE
    # --------------------------------------------------------

    trade = run_single_trade(

        legs=legs,

        entry_df=
            snapshots[
                entry_index
            ]["data"],

        exit_df=
            snapshots[
                exit_index
            ]["data"],

        entry_time=
            snapshots[
                entry_index
            ]["timestamp"],

        exit_time=
            snapshots[
                exit_index
            ]["timestamp"]

    )

    print("\n========================================")
    print("TRADE RESULT")
    print("========================================")

    print(
        "Strategy P&L:",
        trade["strategy_pnl"]
    )

    for leg in trade["legs"]:

        print(
            leg["action"],
            leg["strike"],
            leg["option_type"],
            "Entry:",
            leg["entry_premium"],
            "Exit:",
            leg["exit_premium"],
            "P&L:",
            leg["pnl"]
        )

    # --------------------------------------------------------
    # PERFORMANCE TABLE
    # --------------------------------------------------------

    results = run_backtest(
        [trade]
    )

    metrics = calculate_backtest_metrics(
        results
    )

    print("\n========================================")
    print("BACKTEST METRICS")
    print("========================================")

    for key, value in metrics.items():

        print(
            f"{key}: {value}"
        )

    print("\n========================================")
    print("BACKTEST COMPLETE")
    print("========================================")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
    