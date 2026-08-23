# ============================================================
# NIFTY CANDLE DATA ENGINE
# Upstox V3 Historical + Intraday Candle Support
# ============================================================

import os
from datetime import datetime, timedelta

import pandas as pd
import requests
from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

UPSTOX_ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")

UPSTOX_BASE_URL = "https://api.upstox.com/v3"

HISTORICAL_CANDLE_URL = (
    f"{UPSTOX_BASE_URL}/historical-candle"
)

INTRADAY_CANDLE_URL = (
    f"{UPSTOX_BASE_URL}/historical-candle/intraday"
)


# ============================================================
# NIFTY 50 INSTRUMENT
# ============================================================

NIFTY_INSTRUMENT_KEY = "NSE_INDEX|Nifty 50"


# ============================================================
# SUPPORTED TIMEFRAMES
# ============================================================

TIMEFRAME_CONFIG = {

    "1m": {
        "unit": "minutes",
        "interval": 1,
    },

    "3m": {
        "unit": "minutes",
        "interval": 3,
    },

    "5m": {
        "unit": "minutes",
        "interval": 5,
    },

    "15m": {
        "unit": "minutes",
        "interval": 15,
    },

    "30m": {
        "unit": "minutes",
        "interval": 30,
    },

    "1H": {
        "unit": "hours",
        "interval": 1,
    },

    "1D": {
        "unit": "days",
        "interval": 1,
    },
}


# ============================================================
# REQUEST HEADERS
# ============================================================

def get_headers():
    """
    Create Upstox API request headers.
    """

    if not UPSTOX_ACCESS_TOKEN:
        raise RuntimeError(
            "UPSTOX_ACCESS_TOKEN not found in .env file."
        )

    return {
        "Accept": "application/json",
        "Authorization": (
            f"Bearer {UPSTOX_ACCESS_TOKEN}"
        ),
    }


# ============================================================
# EMPTY DATAFRAME
# ============================================================

def empty_candle_dataframe():

    return pd.DataFrame(
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "oi",
        ]
    )


# ============================================================
# NORMALIZE CANDLES
# ============================================================

def normalize_candles(candles):
    """
    Convert Upstox candle response into a clean DataFrame.

    Upstox candle format:

    [
        timestamp,
        open,
        high,
        low,
        close,
        volume,
        oi
    ]
    """

    if not candles:
        return empty_candle_dataframe()

    rows = []

    for candle in candles:

        if not candle or len(candle) < 6:
            continue

        rows.append(
            {
                "timestamp": candle[0],
                "open": candle[1],
                "high": candle[2],
                "low": candle[3],
                "close": candle[4],
                "volume": (
                    candle[5]
                    if len(candle) > 5
                    else 0
                ),
                "oi": (
                    candle[6]
                    if len(candle) > 6
                    else 0
                ),
            }
        )

    if not rows:
        return empty_candle_dataframe()

    df = pd.DataFrame(rows)

    # --------------------------------------------------------
    # Timestamp
    # --------------------------------------------------------

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "oi",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # --------------------------------------------------------
    # Remove invalid rows
    # --------------------------------------------------------

    df = df.dropna(
        subset=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
        ]
    )

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    df = df.drop_duplicates(
        subset=["timestamp"],
        keep="last",
    )

    # --------------------------------------------------------
    # Sort chronologically
    # --------------------------------------------------------

    df = df.sort_values(
        "timestamp"
    )

    return df.reset_index(drop=True)


# ============================================================
# FETCH HISTORICAL CANDLES
# ============================================================

def fetch_historical_candles(
    instrument_key=NIFTY_INSTRUMENT_KEY,
    unit="minutes",
    interval=5,
    from_date=None,
    to_date=None,
):
    """
    Fetch historical candles from Upstox V3.

    Example URL:

    /v3/historical-candle/
    NSE_INDEX|Nifty 50/
    minutes/
    5/
    2026-08-20/
    2026-08-15
    """

    if to_date is None:
        to_date = datetime.now().date()

    if from_date is None:
        from_date = (
            to_date - timedelta(days=7)
        )

    # --------------------------------------------------------
    # Convert dates to strings
    # --------------------------------------------------------

    to_date = str(to_date)
    from_date = str(from_date)

    # --------------------------------------------------------
    # URL
    # --------------------------------------------------------

    url = (
        f"{HISTORICAL_CANDLE_URL}/"
        f"{instrument_key}/"
        f"{unit}/"
        f"{interval}/"
        f"{to_date}/"
        f"{from_date}"
    )

    # --------------------------------------------------------
    # Request
    # --------------------------------------------------------

    response = requests.get(
        url,
        headers=get_headers(),
        timeout=30,
    )

    # --------------------------------------------------------
    # Better error handling
    # --------------------------------------------------------

    if response.status_code != 200:

        print("\nUPSTOX API ERROR")
        print("-" * 60)
        print("Status:", response.status_code)
        print("URL:", url)

        try:
            print(
                "Response:",
                response.json(),
            )
        except Exception:
            print(
                "Response:",
                response.text,
            )

        response.raise_for_status()

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    payload = response.json()

    # --------------------------------------------------------
    # Validate response
    # --------------------------------------------------------

    if payload.get("status") != "success":

        raise RuntimeError(
            f"Upstox API returned unexpected response: "
            f"{payload}"
        )

    candles = (
        payload
        .get("data", {})
        .get("candles", [])
    )

    return normalize_candles(candles)


# ============================================================
# FETCH TODAY'S INTRADAY CANDLES
# ============================================================

def fetch_intraday_candles(
    instrument_key=NIFTY_INSTRUMENT_KEY,
    unit="minutes",
    interval=5,
):
    """
    Fetch today's intraday candles.

    This will be used later for the live chart.
    """

    url = (
        f"{INTRADAY_CANDLE_URL}/"
        f"{instrument_key}/"
        f"{unit}/"
        f"{interval}"
    )

    response = requests.get(
        url,
        headers=get_headers(),
        timeout=30,
    )

    if response.status_code != 200:

        print("\nUPSTOX INTRADAY API ERROR")
        print("-" * 60)
        print("Status:", response.status_code)
        print("URL:", url)

        try:
            print(
                "Response:",
                response.json(),
            )
        except Exception:
            print(
                "Response:",
                response.text,
            )

        response.raise_for_status()

    payload = response.json()

    if payload.get("status") != "success":

        raise RuntimeError(
            f"Upstox API returned unexpected response: "
            f"{payload}"
        )

    candles = (
        payload
        .get("data", {})
        .get("candles", [])
    )

    return normalize_candles(candles)


# ============================================================
# GET NIFTY CANDLES
# ============================================================

def get_nifty_candles(
    timeframe="5m",
    days=5,
):
    """
    Main historical candle function.

    Supported:

        1m
        3m
        5m
        15m
        30m
        1H
        1D
    """

    if timeframe not in TIMEFRAME_CONFIG:

        raise ValueError(
            f"Unsupported timeframe: "
            f"{timeframe}. "
            f"Supported: "
            f"{list(TIMEFRAME_CONFIG.keys())}"
        )

    config = TIMEFRAME_CONFIG[
        timeframe
    ]

    end_date = datetime.now().date()

    start_date = (
        end_date
        - timedelta(days=days)
    )

    df = fetch_historical_candles(
        instrument_key=NIFTY_INSTRUMENT_KEY,
        unit=config["unit"],
        interval=config["interval"],
        from_date=start_date,
        to_date=end_date,
    )

    return df


# ============================================================
# GET TODAY'S NIFTY CANDLES
# ============================================================

def get_nifty_intraday_candles(
    timeframe="5m",
):
    """
    Get today's intraday NIFTY candles.
    """

    if timeframe not in TIMEFRAME_CONFIG:

        raise ValueError(
            f"Unsupported timeframe: "
            f"{timeframe}"
        )

    config = TIMEFRAME_CONFIG[
        timeframe
    ]

    return fetch_intraday_candles(
        instrument_key=NIFTY_INSTRUMENT_KEY,
        unit=config["unit"],
        interval=config["interval"],
    )


# ============================================================
# CANDLE VALIDATION
# ============================================================

def validate_candles(df):
    """
    Validate OHLC candle data.
    """

    if df is None:
        return False

    if df.empty:
        return False

    required_columns = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
    ]

    for column in required_columns:

        if column not in df.columns:
            return False

    # --------------------------------------------------------
    # Check for missing values
    # --------------------------------------------------------

    if df[
        required_columns
    ].isnull().any().any():

        return False

    # --------------------------------------------------------
    # High must be >= Open / Close
    # --------------------------------------------------------

    invalid_high = (
        df["high"]
        < df[
            ["open", "close"]
        ].max(axis=1)
    )

    if invalid_high.any():
        return False

    # --------------------------------------------------------
    # Low must be <= Open / Close
    # --------------------------------------------------------

    invalid_low = (
        df["low"]
        > df[
            ["open", "close"]
        ].min(axis=1)
    )

    if invalid_low.any():
        return False

    # --------------------------------------------------------
    # OHLC must be positive
    # --------------------------------------------------------

    if (
        df[
            ["open", "high", "low", "close"]
        ] <= 0
    ).any().any():

        return False

    # --------------------------------------------------------
    # Timestamp must be sorted
    # --------------------------------------------------------

    if not df["timestamp"].is_monotonic_increasing:
        return False

    return True


# ============================================================
# CANDLE SUMMARY
# ============================================================

def candle_summary(df):
    """
    Return useful summary information.
    """

    if df is None or df.empty:

        return {
            "rows": 0,
            "first_timestamp": None,
            "last_timestamp": None,
            "open": None,
            "high": None,
            "low": None,
            "close": None,
            "volume": None,
        }

    return {
        "rows": len(df),

        "first_timestamp":
            df["timestamp"].min(),

        "last_timestamp":
            df["timestamp"].max(),

        "open":
            float(df.iloc[0]["open"]),

        "high":
            float(df["high"].max()),

        "low":
            float(df["low"].min()),

        "close":
            float(df.iloc[-1]["close"]),

        "volume":
            float(df["volume"].sum()),
    }


# ============================================================
# QUICK ENGINE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("NIFTY CANDLE ENGINE TEST")
    print("=" * 60)

    print("\nSupported timeframes:")
    print(
        ", ".join(
            TIMEFRAME_CONFIG.keys()
        )
    )

    try:

        # ----------------------------------------------------
        # Fetch 5-minute historical candles
        # ----------------------------------------------------

        print(
            "\nFetching NIFTY 5-minute candles..."
        )

        df = get_nifty_candles(
            timeframe="5m",
            days=5,
        )

        print(
            "\nRows:",
            len(df),
        )

        if df.empty:

            print(
                "\nNo candle data returned."
            )

        else:

            print(
                "\nColumns:"
            )

            print(
                list(df.columns)
            )

            print(
                "\nFirst 5 candles:"
            )

            print(
                df.head().to_string(
                    index=False
                )
            )

            print(
                "\nLast 5 candles:"
            )

            print(
                df.tail().to_string(
                    index=False
                )
            )

            print(
                "\nValidation:",
                validate_candles(df),
            )

            summary = candle_summary(df)

            print(
                "\nSummary:"
            )

            for key, value in summary.items():

                print(
                    f"{key}: {value}"
                )

    except Exception as e:

        print(
            "\nERROR:"
        )

        print(
            type(e).__name__,
            str(e),
        )