import os
import requests
import pandas as pd

from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# CONSTANTS
# ============================================================

BASE_URL = "https://api.upstox.com/v3"

NIFTY_INSTRUMENT_KEY = "NSE_INDEX|Nifty 50"


# ============================================================
# ACCESS TOKEN
# ============================================================

def get_access_token():

    access_token = os.getenv(
        "UPSTOX_ACCESS_TOKEN"
    )

    if not access_token:

        raise ValueError(
            "UPSTOX_ACCESS_TOKEN not found in .env"
        )

    return access_token


# ============================================================
# HEADERS
# ============================================================

def get_headers():

    return {
        "Accept": "application/json",
        "Authorization":
            f"Bearer {get_access_token()}"
    }


# ============================================================
# HISTORICAL CANDLES
# ============================================================

def get_historical_candles(
    instrument_key,
    unit="minutes",
    interval=5,
    to_date=None,
    from_date=None
):
    """
    Fetch historical OHLCV + OI data from Upstox.

    Example:

        get_historical_candles(
            "NSE_INDEX|Nifty 50",
            "minutes",
            5,
            "2026-08-18",
            "2026-08-01"
        )
    """

    if to_date is None:

        raise ValueError(
            "to_date is required."
        )

    url = (
        f"{BASE_URL}/historical-candle/"
        f"{instrument_key}/"
        f"{unit}/"
        f"{interval}/"
        f"{to_date}"
    )

    if from_date:

        url += f"/{from_date}"

    response = requests.get(
        url,
        headers=get_headers(),
        timeout=30
    )

    print(
        "Historical API status:",
        response.status_code
    )

    response.raise_for_status()

    data = response.json()

    if data.get("status") != "success":

        raise RuntimeError(
            f"Upstox Historical API Error: {data}"
        )

    candles = (
        data
        .get("data", {})
        .get("candles", [])
    )

    if not candles:

        return pd.DataFrame(
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "oi"
            ]
        )

    rows = []

    for candle in candles:

        rows.append(
            {
                "timestamp": candle[0],
                "open": candle[1],
                "high": candle[2],
                "low": candle[3],
                "close": candle[4],
                "volume": candle[5],
                "oi": candle[6]
            }
        )

    df = pd.DataFrame(rows)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "oi"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.sort_values(
        "timestamp"
    )

    df = df.reset_index(
        drop=True
    )

    return df


# ============================================================
# NIFTY HISTORICAL DATA
# ============================================================

def get_nifty_history(
    to_date,
    from_date,
    interval=5
):

    return get_historical_candles(
        instrument_key=NIFTY_INSTRUMENT_KEY,
        unit="minutes",
        interval=interval,
        to_date=to_date,
        from_date=from_date
    )


# ============================================================
# OPTION HISTORICAL DATA
# ============================================================

def get_option_history(
    instrument_key,
    to_date,
    from_date,
    interval=5
):

    return get_historical_candles(
        instrument_key=instrument_key,
        unit="minutes",
        interval=interval,
        to_date=to_date,
        from_date=from_date
    )


# ============================================================
# SAVE HISTORICAL DATA
# ============================================================

def save_historical_data(
    df,
    filename
):

    if df is None or df.empty:

        raise ValueError(
            "Cannot save empty historical data."
        )

    base_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    data_dir = os.path.join(
        base_dir,
        "data",
        "historical"
    )

    os.makedirs(
        data_dir,
        exist_ok=True
    )

    path = os.path.join(
        data_dir,
        filename
    )

    df.to_csv(
        path,
        index=False
    )

    print(
        f"Historical data saved: {path}"
    )

    print(
        f"Rows: {len(df)}"
    )

    return path


# ============================================================
# LOAD HISTORICAL DATA
# ============================================================

def load_historical_data(
    filename
):

    base_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    path = os.path.join(
        base_dir,
        "data",
        "historical",
        filename
    )

    if not os.path.exists(path):

        raise FileNotFoundError(
            f"Historical data not found: {path}"
        )

    df = pd.read_csv(
        path
    )

    if "timestamp" in df.columns:

        df["timestamp"] = pd.to_datetime(
            df["timestamp"]
        )

    return df


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n=============================="
    )

    print(
        "UPSTOX HISTORICAL DATA TEST"
    )

    print(
        "==============================\n"
    )

    print(
        "Fetching NIFTY historical data..."
    )

    df = get_nifty_history(
        to_date="2026-08-18",
        from_date="2026-08-17",
        interval=5
    )

    print(
        "\n=============================="
    )

    print(
        "FETCH SUCCESS"
    )

    print(
        "=============================="
    )

    print(
        "Rows:",
        len(df)
    )

    print(
        "\nColumns:"
    )

    print(
        df.columns.tolist()
    )

    print(
        "\nFirst rows:"
    )

    print(
        df.head()
    )

    print(
        "\nLast rows:"
    )

    print(
        df.tail()
    )

    save_historical_data(
        df,
        "nifty_5min_test.csv"
    )

    print(
        "\nHistorical data test completed."
    )
    