import sqlite3
import os
import pandas as pd

from oi_engine import classify_oi


# ============================================================
# DATABASE PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DB_PATH = os.path.join(
    BASE_DIR,
    "data",
    "nifty_history.db"
)


# ============================================================
# GET SNAPSHOT TIMES
# ============================================================

def get_snapshot_times(expiry=None):

    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT DISTINCT fetch_time
        FROM option_snapshots
        WHERE 1 = 1
    """

    params = []

    if expiry is not None:

        query += """
            AND expiry = ?
        """

        params.append(expiry)

    query += """
        ORDER BY fetch_time ASC
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=params
    )

    conn.close()

    return df


# ============================================================
# GET SNAPSHOT
# ============================================================

def get_snapshot(
    fetch_time,
    expiry=None
):

    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT *
        FROM option_snapshots
        WHERE fetch_time = ?
    """

    params = [fetch_time]

    if expiry is not None:

        query += """
            AND expiry = ?
        """

        params.append(expiry)

    query += """
        ORDER BY strike ASC
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=params
    )

    conn.close()

    return df


# ============================================================
# GET LATEST TWO SNAPSHOTS
# ============================================================

def get_latest_two_snapshots(expiry=None):

    times = get_snapshot_times(
        expiry=expiry
    )

    if len(times) < 2:

        return None, None

    previous_time = times.iloc[-2]["fetch_time"]

    current_time = times.iloc[-1]["fetch_time"]

    previous = get_snapshot(
        previous_time,
        expiry=expiry
    )

    current = get_snapshot(
        current_time,
        expiry=expiry
    )

    return previous, current


# ============================================================
# CALCULATE SNAPSHOT OI CHANGE
# ============================================================

def calculate_oi_change(
    previous,
    current
):

    if previous is None or current is None:

        return pd.DataFrame()

    previous = previous.copy()

    current = current.copy()

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required_columns = [
        "strike",
        "ce_ltp",
        "ce_oi",
        "ce_volume",
        "pe_ltp",
        "pe_oi",
        "pe_volume",
    ]

    previous = previous[
        required_columns
    ].copy()

    current = current[
        required_columns
    ].copy()

    # --------------------------------------------------------
    # Rename previous columns
    # --------------------------------------------------------

    previous = previous.rename(
        columns={
            "ce_ltp": "prev_ce_ltp",
            "ce_oi": "prev_ce_oi",
            "ce_volume": "prev_ce_volume",

            "pe_ltp": "prev_pe_ltp",
            "pe_oi": "prev_pe_oi",
            "pe_volume": "prev_pe_volume",
        }
    )

    # --------------------------------------------------------
    # Match same strike
    # --------------------------------------------------------

    result = current.merge(
        previous,
        on="strike",
        how="inner"
    )

    # --------------------------------------------------------
    # CE changes
    # --------------------------------------------------------

    result["ce_snapshot_oi_change"] = (
        result["ce_oi"]
        - result["prev_ce_oi"]
    )

    result["ce_snapshot_price_change"] = (
        result["ce_ltp"]
        - result["prev_ce_ltp"]
    )

    result["ce_snapshot_volume_change"] = (
        result["ce_volume"]
        - result["prev_ce_volume"]
    )

    # --------------------------------------------------------
    # PE changes
    # --------------------------------------------------------

    result["pe_snapshot_oi_change"] = (
        result["pe_oi"]
        - result["prev_pe_oi"]
    )

    result["pe_snapshot_price_change"] = (
        result["pe_ltp"]
        - result["prev_pe_ltp"]
    )

    result["pe_snapshot_volume_change"] = (
        result["pe_volume"]
        - result["prev_pe_volume"]
    )

    return result


# ============================================================
# ADD OI SIGNALS
# ============================================================

def add_oi_signals(df):

    if df is None or df.empty:

        return df

    result = df.copy()

    # --------------------------------------------------------
    # CE SIGNAL
    # --------------------------------------------------------

    result["ce_signal"] = result.apply(

        lambda row: classify_oi(
            row["ce_snapshot_price_change"],
            row["ce_snapshot_oi_change"]
        ),

        axis=1
    )

    # --------------------------------------------------------
    # PE SIGNAL
    # --------------------------------------------------------

    result["pe_signal"] = result.apply(

        lambda row: classify_oi(
            row["pe_snapshot_price_change"],
            row["pe_snapshot_oi_change"]
        ),

        axis=1
    )

    return result


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("==============================")
    print("HISTORICAL OI ENGINE")
    print("==============================")

    # --------------------------------------------------------
    # SNAPSHOT COUNT
    # --------------------------------------------------------

    times = get_snapshot_times()

    print()
    print(
        "Total snapshots:",
        len(times)
    )

    # --------------------------------------------------------
    # NEED TWO SNAPSHOTS
    # --------------------------------------------------------

    if len(times) < 2:

        print()
        print(
            "Need at least 2 snapshots."
        )

        raise SystemExit


    # --------------------------------------------------------
    # LATEST TWO
    # --------------------------------------------------------

    print()
    print(
        "Latest snapshots:"
    )

    print(
        times.tail(2).to_string(
            index=False
        )
    )


    # --------------------------------------------------------
    # LOAD SNAPSHOTS
    # --------------------------------------------------------

    previous, current = (
        get_latest_two_snapshots()
    )

    print()
    print(
        "Previous rows:",
        len(previous)
    )

    print(
        "Current rows:",
        len(current)
    )


    # --------------------------------------------------------
    # CALCULATE CHANGES
    # --------------------------------------------------------

    result = calculate_oi_change(
        previous,
        current
    )

    print()
    print(
        "Comparison rows:",
        len(result)
    )


    # --------------------------------------------------------
    # ADD SIGNALS
    # --------------------------------------------------------

    result = add_oi_signals(
        result
    )


    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print()
    print(
        "Sample OI movement:"
    )

    print(
        result[
            [
                "strike",

                "ce_snapshot_oi_change",
                "ce_snapshot_price_change",
                "ce_signal",

                "pe_snapshot_oi_change",
                "pe_snapshot_price_change",
                "pe_signal",
            ]
        ]
        .head(10)
        .to_string(
            index=False
        )
    )


    # --------------------------------------------------------
    # SIGNAL SUMMARY
    # --------------------------------------------------------

    print()
    print(
        "========== CE SIGNAL SUMMARY =========="
    )

    print(
        result[
            "ce_signal"
        ].value_counts()
    )


    print()
    print(
        "========== PE SIGNAL SUMMARY =========="
    )

    print(
        result[
            "pe_signal"
        ].value_counts()
    )


    print()
    print(
        "Historical OI analysis completed."
    )