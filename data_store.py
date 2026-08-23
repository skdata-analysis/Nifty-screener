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
# DATABASE CONNECTION
# ============================================================

def get_connection():

    return sqlite3.connect(
        DB_PATH
    )


# ============================================================
# TABLE DEFINITION
# ============================================================

REQUIRED_COLUMNS = {

    # -----------------------------
    # BASIC MARKET DATA
    # -----------------------------

    "fetch_time": "TEXT",
    "expiry": "TEXT",
    "strike": "REAL",
    "spot_price": "REAL",
    "pcr": "REAL",

    # -----------------------------
    # CALL DATA
    # -----------------------------

    "ce_instrument_key": "TEXT",
    "ce_ltp": "REAL",
    "ce_volume": "REAL",
    "ce_oi": "REAL",
    "ce_prev_oi": "REAL",
    "ce_oi_change": "REAL",
    "ce_close": "REAL",

    "ce_bid": "REAL",
    "ce_bid_qty": "REAL",
    "ce_ask": "REAL",
    "ce_ask_qty": "REAL",

    # CALL GREEKS
    "ce_iv": "REAL",
    "ce_delta": "REAL",
    "ce_gamma": "REAL",
    "ce_theta": "REAL",
    "ce_vega": "REAL",
    "ce_pop": "REAL",

    # -----------------------------
    # PUT DATA
    # -----------------------------

    "pe_instrument_key": "TEXT",
    "pe_ltp": "REAL",
    "pe_volume": "REAL",
    "pe_oi": "REAL",
    "pe_prev_oi": "REAL",
    "pe_oi_change": "REAL",
    "pe_close": "REAL",

    "pe_bid": "REAL",
    "pe_bid_qty": "REAL",
    "pe_ask": "REAL",
    "pe_ask_qty": "REAL",

    # PUT GREEKS
    "pe_iv": "REAL",
    "pe_delta": "REAL",
    "pe_gamma": "REAL",
    "pe_theta": "REAL",
    "pe_vega": "REAL",
    "pe_pop": "REAL",
}


# ============================================================
# CREATE / MIGRATE DATABASE
# ============================================================

def initialize_database():

    conn = get_connection()

    cursor = conn.cursor()

    # --------------------------------------------------------
    # CREATE TABLE IF IT DOES NOT EXIST
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS option_snapshots (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            fetch_time TEXT,
            expiry TEXT,
            strike REAL,
            spot_price REAL,
            pcr REAL,

            ce_instrument_key TEXT,
            ce_ltp REAL,
            ce_volume REAL,
            ce_oi REAL,
            ce_prev_oi REAL,
            ce_oi_change REAL,
            ce_close REAL,

            ce_bid REAL,
            ce_bid_qty REAL,
            ce_ask REAL,
            ce_ask_qty REAL,

            ce_iv REAL,
            ce_delta REAL,
            ce_gamma REAL,
            ce_theta REAL,
            ce_vega REAL,
            ce_pop REAL,

            pe_instrument_key TEXT,
            pe_ltp REAL,
            pe_volume REAL,
            pe_oi REAL,
            pe_prev_oi REAL,
            pe_oi_change REAL,
            pe_close REAL,

            pe_bid REAL,
            pe_bid_qty REAL,
            pe_ask REAL,
            pe_ask_qty REAL,

            pe_iv REAL,
            pe_delta REAL,
            pe_gamma REAL,
            pe_theta REAL,
            pe_vega REAL,
            pe_pop REAL
        )
        """
    )

    # --------------------------------------------------------
    # MIGRATE EXISTING DATABASE
    # --------------------------------------------------------

    cursor.execute(
        "PRAGMA table_info(option_snapshots)"
    )

    existing_columns = {
        row[1]
        for row in cursor.fetchall()
    }

    for column, data_type in REQUIRED_COLUMNS.items():

        if column not in existing_columns:

            cursor.execute(
                f"""
                ALTER TABLE option_snapshots
                ADD COLUMN {column} {data_type}
                """
            )

            print(
                f"Database migration: added column '{column}'"
            )

    conn.commit()

    conn.close()


# ============================================================
# SAVE SNAPSHOT
# ============================================================

def save_snapshot(df):

    if df is None or df.empty:
        return

    initialize_database()

    # --------------------------------------------------------
    # Columns that can be stored
    # --------------------------------------------------------

    snapshot_columns = [
        "fetch_time",
        "expiry",
        "strike",
        "spot_price",
        "pcr",

        # CE
        "ce_instrument_key",
        "ce_ltp",
        "ce_volume",
        "ce_oi",
        "ce_prev_oi",
        "ce_oi_change",
        "ce_close",
        "ce_bid",
        "ce_bid_qty",
        "ce_ask",
        "ce_ask_qty",
        "ce_iv",
        "ce_delta",
        "ce_gamma",
        "ce_theta",
        "ce_vega",
        "ce_pop",

        # PE
        "pe_instrument_key",
        "pe_ltp",
        "pe_volume",
        "pe_oi",
        "pe_prev_oi",
        "pe_oi_change",
        "pe_close",
        "pe_bid",
        "pe_bid_qty",
        "pe_ask",
        "pe_ask_qty",
        "pe_iv",
        "pe_delta",
        "pe_gamma",
        "pe_theta",
        "pe_vega",
        "pe_pop",
    ]

    available_columns = [
        column
        for column in snapshot_columns
        if column in df.columns
    ]

    if not available_columns:
        return

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


# ============================================================
# DATABASE COLUMN CHECK
# ============================================================

def get_database_columns():

    initialize_database()

    conn = get_connection()

    result = pd.read_sql_query(
        """
        PRAGMA table_info(option_snapshots)
        """,
        conn
    )

    conn.close()

    return result["name"].tolist()


# ============================================================
# TEST / INITIALIZE
# ============================================================

if __name__ == "__main__":

    print("\n==============================")
    print("NIFTY HISTORY DATABASE")
    print("==============================")

    initialize_database()

    print("\nDatabase:")
    print(DB_PATH)

    print("\nColumns:")

    columns = get_database_columns()

    for column in columns:
        print(" -", column)

    print("\nDatabase statistics:")

    print(
        get_snapshot_count()
    )

    print("\nDatabase ready.")