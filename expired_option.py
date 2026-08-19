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

BASE_URL = "https://api.upstox.com/v2"

NIFTY_KEY = "NSE_INDEX|Nifty 50"


# ============================================================
# ACCESS TOKEN
# ============================================================

def get_access_token():

    token = os.getenv(
        "UPSTOX_ACCESS_TOKEN"
    )

    if not token:

        raise ValueError(
            "UPSTOX_ACCESS_TOKEN not found in .env"
        )

    return token


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
# GET EXPIRED EXPIRIES
# ============================================================

def get_expired_expiries():

    url = (
        f"{BASE_URL}/expired-instruments/expiries"
    )

    params = {
        "instrument_key": NIFTY_KEY
    }

    response = requests.get(
        url,
        headers=get_headers(),
        params=params,
        timeout=30
    )

    print(
        "Expiry API status:",
        response.status_code
    )

    response.raise_for_status()

    data = response.json()

    if data.get("status") != "success":

        raise RuntimeError(
            f"Unable to fetch expired expiries: {data}"
        )

    expiries = data.get(
        "data",
        []
    )

    if not expiries:

        raise RuntimeError(
            "No expired NIFTY expiries returned."
        )

    return sorted(
        expiries
    )


# ============================================================
# GET EXPIRED OPTION CONTRACTS
# ============================================================

def get_expired_option_contracts(
    expiry_date
):

    url = (
        f"{BASE_URL}/expired-instruments/"
        f"option/contract"
    )

    params = {
        "instrument_key": NIFTY_KEY,
        "expiry_date": expiry_date
    }

    response = requests.get(
        url,
        headers=get_headers(),
        params=params,
        timeout=30
    )

    print(
        "Contract API status:",
        response.status_code
    )

    response.raise_for_status()

    data = response.json()

    if data.get("status") != "success":

        raise RuntimeError(
            f"Unable to fetch expired contracts: {data}"
        )

    contracts = data.get(
        "data",
        []
    )

    if not contracts:

        raise RuntimeError(
            f"No expired contracts found for {expiry_date}"
        )

    rows = []

    for contract in contracts:

        rows.append(
            {
                "expiry":
                    contract.get("expiry"),

                "instrument_key":
                    contract.get(
                        "instrument_key"
                    ),

                "trading_symbol":
                    contract.get(
                        "trading_symbol"
                    ),

                "strike":
                    contract.get(
                        "strike_price"
                    ),

                "option_type":
                    contract.get(
                        "instrument_type"
                    ),

                "lot_size":
                    contract.get(
                        "lot_size"
                    ),

                "tick_size":
                    contract.get(
                        "tick_size"
                    ),

                "underlying_key":
                    contract.get(
                        "underlying_key"
                    ),

                "weekly":
                    contract.get(
                        "weekly"
                    )
            }
        )

    df = pd.DataFrame(
        rows
    )

    if df.empty:

        raise RuntimeError(
            "Expired contract dataframe is empty."
        )

    df["strike"] = pd.to_numeric(
        df["strike"],
        errors="coerce"
    )

    df = df.sort_values(
        [
            "strike",
            "option_type"
        ]
    )

    df = df.reset_index(
        drop=True
    )

    return df


# ============================================================
# FILTER CONTRACT
# ============================================================

def find_option_contract(
    contracts,
    strike,
    option_type
):

    option_type = option_type.upper()

    result = contracts[
        (
            contracts["strike"]
            == float(strike)
        )
        &
        (
            contracts["option_type"]
            == option_type
        )
    ]

    if result.empty:

        raise ValueError(
            f"No {option_type} contract found "
            f"for strike {strike}"
        )

    return result.iloc[0].to_dict()


# ============================================================
# GET EXPIRED OPTION CANDLES
# ============================================================

def get_expired_option_history(
    expired_instrument_key,
    from_date,
    to_date,
    interval="5minute"
):

    url = (
        f"{BASE_URL}/expired-instruments/"
        f"historical-candle/"
        f"{expired_instrument_key}/"
        f"{interval}/"
        f"{to_date}/"
        f"{from_date}"
    )

    response = requests.get(
        url,
        headers=get_headers(),
        timeout=30
    )

    print(
        "Historical option API status:",
        response.status_code
    )

    response.raise_for_status()

    data = response.json()

    if data.get("status") != "success":

        raise RuntimeError(
            f"Historical option API error: {data}"
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

    df = pd.DataFrame(
        rows
    )

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
# SAVE CONTRACT DATABASE
# ============================================================

def save_contracts(
    contracts,
    expiry_date
):

    base_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    data_dir = os.path.join(
        base_dir,
        "data",
        "historical",
        "contracts"
    )

    os.makedirs(
        data_dir,
        exist_ok=True
    )

    filename = (
        f"nifty_{expiry_date}_contracts.csv"
    )

    path = os.path.join(
        data_dir,
        filename
    )

    contracts.to_csv(
        path,
        index=False
    )

    print(
        f"Contracts saved: {path}"
    )

    return path


# ============================================================
# SAVE OPTION HISTORY
# ============================================================

def save_option_history(
    df,
    expiry,
    strike,
    option_type
):

    base_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    data_dir = os.path.join(
        base_dir,
        "data",
        "historical",
        "options"
    )

    os.makedirs(
        data_dir,
        exist_ok=True
    )

    filename = (
        f"NIFTY_{expiry}_"
        f"{int(strike)}_"
        f"{option_type}.csv"
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
        f"Option history saved: {path}"
    )

    return path


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("NIFTY EXPIRED OPTION DATA TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Expiries
    # --------------------------------------------------------

    expiries = get_expired_expiries()

    print()
    print("AVAILABLE EXPIRED EXPIRIES:")
    print()

    for expiry in expiries:

        print(expiry)

    # --------------------------------------------------------
    # 2. Select latest available expiry
    # --------------------------------------------------------

    expiry = expiries[-1]

    print()
    print(
        "Selected expiry:",
        expiry
    )

    # --------------------------------------------------------
    # 3. Contracts
    # --------------------------------------------------------

    contracts = get_expired_option_contracts(
        expiry
    )

    print()
    print(
        "Total contracts:",
        len(contracts)
    )

    print()
    print(
        contracts.head(10)
    )

    save_contracts(
        contracts,
        expiry
    )

    # --------------------------------------------------------
    # 4. Select ATM-ish strike
    # --------------------------------------------------------

    strikes = sorted(
        contracts["strike"]
        .dropna()
        .unique()
    )

    if not strikes:

        raise RuntimeError(
            "No strikes found."
        )

    test_strike = strikes[
        len(strikes) // 2
    ]

    print()
    print(
        "Test strike:",
        test_strike
    )

    # --------------------------------------------------------
    # 5. Find CE
    # --------------------------------------------------------

    contract = find_option_contract(
        contracts,
        test_strike,
        "CE"
    )

    print()
    print("SELECTED CONTRACT:")
    print(contract)

    # --------------------------------------------------------
    # 6. Historical candles
    # --------------------------------------------------------

    history = get_expired_option_history(
        expired_instrument_key=
            contract["instrument_key"],
        from_date=expiry,
        to_date=expiry,
        interval="5minute"
    )

    print()
    print(
        "Historical rows:",
        len(history)
    )

    print()
    print(
        history.head()
    )

    # --------------------------------------------------------
    # 7. Save
    # --------------------------------------------------------

    if not history.empty:

        save_option_history(
            history,
            expiry,
            test_strike,
            "CE"
        )

    print()
    print("=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
    