import os
import sqlite3
import pandas as pd


# ============================================================
# DATABASE PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

os.makedirs(
    DATA_DIR,
    exist_ok=True
)

DB_PATH = os.path.join(
    DATA_DIR,
    "nifty_history.db"
)


# ============================================================
# CREATE DATABASE
# ============================================================

def get_connection():

    return sqlite3.connect(
        DB_PATH
    )


def initialize_database():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS option_snapshots (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            fetch_time TEXT NOT NULL,

            expiry TEXT NOT NULL,

            strike REAL NOT NULL,

            spot_price REAL,

            pcr REAL,

            ce_ltp REAL,
            ce_volume REAL,
            ce_oi REAL,
            ce_oi_change REAL,
            ce_iv REAL,

            pe_ltp REAL,
            pe_volume REAL,
            pe_oi REAL,
            pe_oi_change REAL,
            pe_iv REAL

        )
        """
    )

    conn.commit()

    conn.close()


# ============================================================
# SAVE SNAPSHOT
# ============================================================

def save_snapshot(df):

    if df.empty:
        return

    initialize_database()

    snapshot_columns = [

        "fetch_time",
        "expiry",
        "strike",
        "spot_price",
        "pcr",

        "ce_ltp",
        "ce_volume",
        "ce_oi",
        "ce_oi_change",
        "ce_iv",

        "pe_ltp",
        "pe_volume",
        "pe_oi",
        "pe_oi_change",
        "pe_iv",
    ]

    available_columns = [
        col
        for col in snapshot_columns
        if col in df.columns
    ]

    snapshot_df = df[
        available_columns
    ].copy()

    conn = get_connection()

    snapshot_df.to_sql(
        "option_snapshots",
        conn,
        if_exists="append",
        index=False
    )

    conn.close()

    print(
        f"Snapshot saved: {len(snapshot_df)} rows"
    )


# ============================================================
# READ HISTORY
# ============================================================

def get_history(
    expiry=None,
    strike=None
):

    initialize_database()

    query = """
        SELECT *
        FROM option_snapshots
        WHERE 1 = 1
    """

    params = []

    if expiry is not None:

        query += """
            AND expiry = ?
        """

        params.append(expiry)

    if strike is not None:

        query += """
            AND strike = ?
        """

        params.append(strike)

    query += """
        ORDER BY fetch_time ASC
    """

    conn = get_connection()

    df = pd.read_sql_query(
        query,
        conn,
        params=params
    )

    conn.close()

    return df


# ============================================================
# DATABASE STATS
# ============================================================

def get_snapshot_count():

    initialize_database()

    conn = get_connection()

    result = pd.read_sql_query(
        """
        SELECT
            COUNT(*) AS total_rows,
            COUNT(DISTINCT fetch_time)
                AS snapshots
        FROM option_snapshots
        """,
        conn
    )

    conn.close()

    return result
if __name__ == "__main__":

    initialize_database()

    print(
        "Database initialized:"
    )

    print(
        DB_PATH
    )
    