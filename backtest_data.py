import pandas as pd
import sqlite3

from data_store import get_connection, initialize_database


# ============================================================
# LOAD RAW HISTORICAL DATA
# ============================================================

def load_historical_data(
    expiry=None,
    start_date=None,
    end_date=None
):
    """
    Load historical option-chain data from SQLite.
    """

    initialize_database()

    query = """
        SELECT *
        FROM option_snapshots
        WHERE 1 = 1
    """

    params = []

    # --------------------------------------------------------
    # Expiry filter
    # --------------------------------------------------------

    if expiry is not None:

        query += """
            AND expiry = ?
        """

        params.append(expiry)

    # --------------------------------------------------------
    # Date filters
    # --------------------------------------------------------

    if start_date is not None:

        query += """
            AND DATE(fetch_time) >= DATE(?)
        """

        params.append(str(start_date))

    if end_date is not None:

        query += """
            AND DATE(fetch_time) <= DATE(?)
        """

        params.append(str(end_date))

    query += """
        ORDER BY fetch_time ASC, strike ASC
    """

    conn = get_connection()

    df = pd.read_sql_query(
        query,
        conn,
        params=params
    )

    conn.close()

    if df.empty:
        return df

    # --------------------------------------------------------
    # Normalize timestamp
    # --------------------------------------------------------

    df["fetch_time"] = pd.to_datetime(
        df["fetch_time"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Normalize strike
    # --------------------------------------------------------

    df["strike"] = pd.to_numeric(
        df["strike"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["fetch_time", "strike"]
    )

    return df


# ============================================================
# AVAILABLE EXPIRIES
# ============================================================

def get_historical_expiries():

    initialize_database()

    conn = get_connection()

    query = """
        SELECT DISTINCT expiry
        FROM option_snapshots
        WHERE expiry IS NOT NULL
        ORDER BY expiry ASC
    """

    df = pd.read_sql_query(
        query,
        conn
    )

    conn.close()

    if df.empty:
        return []

    return df["expiry"].tolist()


# ============================================================
# AVAILABLE DATES
# ============================================================

def get_historical_dates(
    expiry=None
):

    df = load_historical_data(
        expiry=expiry
    )

    if df.empty:
        return []

    dates = (
        df["fetch_time"]
        .dt.date
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    return dates


# ============================================================
# AVAILABLE SNAPSHOT TIMES
# ============================================================

def get_snapshot_times(
    expiry=None,
    date=None
):

    df = load_historical_data(
        expiry=expiry,
        start_date=date,
        end_date=date
    )

    if df.empty:
        return []

    times = (
        df["fetch_time"]
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    return times


# ============================================================
# BUILD SNAPSHOTS
# ============================================================

def load_historical_snapshots(
    expiry=None,
    start_date=None,
    end_date=None
):
    """
    Convert database rows into the snapshot format
    expected by backtest_engine.py.

    Returns:

        [
            {
                "timestamp": timestamp,
                "data": dataframe
            },
            ...
        ]
    """

    df = load_historical_data(
        expiry=expiry,
        start_date=start_date,
        end_date=end_date
    )

    if df.empty:
        return []

    snapshots = []

    grouped = df.groupby(
        "fetch_time",
        sort=True
    )

    for timestamp, snapshot_df in grouped:

        snapshot_df = snapshot_df.copy()

        snapshot_df = (
            snapshot_df
            .sort_values("strike")
            .reset_index(drop=True)
        )

        snapshots.append(
            {
                "timestamp": timestamp,
                "data": snapshot_df
            }
        )

    return snapshots


# ============================================================
# GET ONE SNAPSHOT
# ============================================================

def get_snapshot(
    timestamp,
    expiry=None
):
    """
    Get one complete option-chain snapshot.
    """

    df = load_historical_data(
        expiry=expiry
    )

    if df.empty:
        return pd.DataFrame()

    timestamp = pd.to_datetime(
        timestamp
    )

    result = df[
        df["fetch_time"] == timestamp
    ].copy()

    return (
        result
        .sort_values("strike")
        .reset_index(drop=True)
    )


# ============================================================
# GET SNAPSHOT INDEX
# ============================================================

def get_snapshot_index(
    snapshots
):
    """
    Create a simple index table for UI selection.
    """

    if not snapshots:
        return pd.DataFrame()

    rows = []

    for index, snapshot in enumerate(
        snapshots
    ):

        data = snapshot["data"]

        spot_price = None
        pcr = None

        if not data.empty:

            if "spot_price" in data.columns:

                spot_values = pd.to_numeric(
                    data["spot_price"],
                    errors="coerce"
                ).dropna()

                if not spot_values.empty:
                    spot_price = spot_values.iloc[0]

            if "pcr" in data.columns:

                pcr_values = pd.to_numeric(
                    data["pcr"],
                    errors="coerce"
                ).dropna()

                if not pcr_values.empty:
                    pcr = pcr_values.iloc[0]

        rows.append(
            {
                "index": index,
                "timestamp": snapshot["timestamp"],
                "spot_price": spot_price,
                "pcr": pcr,
                "rows": len(data)
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("\n========================================")
    print("BACKTEST DATA TEST")
    print("========================================")

    expiries = get_historical_expiries()

    print("\nAvailable expiries:")
    print(expiries)

    snapshots = load_historical_snapshots()

    print(
        f"\nTotal snapshots: {len(snapshots)}"
    )

    if snapshots:

        first = snapshots[0]

        print(
            "\nFirst snapshot:"
        )

        print(
            "Timestamp:",
            first["timestamp"]
        )

        print(
            "Rows:",
            len(first["data"])
        )

        print(
            "\nColumns:"
        )

        print(
            first["data"].columns.tolist()
        )

    print("\n========================================")