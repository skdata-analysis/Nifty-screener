import os
import requests
import pandas as pd
from dotenv import load_dotenv


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

BASE_URL = "https://api.upstox.com/v2"

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
        "Authorization": (
            f"Bearer {get_access_token()}"
        )
    }


# ============================================================
# GET AVAILABLE EXPIRED EXPIRIES
# ============================================================

def get_expired_expiries(
    instrument_key=NIFTY_INSTRUMENT_KEY
):

    url = (
        f"{BASE_URL}/expired-instruments/expiries"
    )

    response = requests.get(
        url,
        headers=get_headers(),
        params={"instrument_key": instrument_key},
        timeout=30
    )

    print(
        "Expired expiries status:",
        response.status_code
    )

    response.raise_for_status()

    data = response.json()

    if data.get("status") != "success":

        raise RuntimeError(
            f"Upstox API error: {data}"
        )

    expiries = data.get(
        "data",
        []
    )

    if not expiries:

        raise RuntimeError(
            "No expired option expiries returned"
        )

    return sorted(
        str(expiry)
        for expiry in expiries
    )


# ============================================================
# GET EXPIRED OPTION CONTRACTS
# ============================================================

def get_expired_option_contracts(
    expiry_date,
    instrument_key=NIFTY_INSTRUMENT_KEY
):

    url = (
        f"{BASE_URL}/expired-instruments/"
        "option/contract"
    )

    params = {
        "instrument_key": instrument_key,
        "expiry_date": expiry_date
    }

    response = requests.get(
        url,
        headers=get_headers(),
        params=params,
        timeout=30
    )

    print(
        "Expired contracts status:",
        response.status_code
    )

    response.raise_for_status()

    data = response.json()

    if data.get("status") != "success":

        raise RuntimeError(
            f"Upstox API error: {data}"
        )

    contracts = data.get(
        "data",
        []
    )

    if not contracts:

        raise RuntimeError(
            f"No expired option contracts found "
            f"for expiry {expiry_date}"
        )

    return contracts


# ============================================================
# FIND SPECIFIC OPTION CONTRACT
# ============================================================

def find_option_contract(
    contracts,
    strike,
    option_type
):

    option_type = option_type.upper()

    if option_type not in [
        "CE",
        "PE"
    ]:

        raise ValueError(
            "option_type must be CE or PE"
        )

    strike = float(strike)

    for contract in contracts:

        contract_strike = contract.get(
            "strike_price"
        )

        contract_type = contract.get(
            "instrument_type"
        )

        if (
            contract_strike is not None
            and float(contract_strike) == strike
            and contract_type == option_type
        ):

            return contract

    return None


# ============================================================
# GET EXPIRED OPTION HISTORY
# ============================================================

def get_expired_option_history(
    expired_instrument_key,
    interval="5minute",
    from_date=None,
    to_date=None
):

    if not from_date or not to_date:

        raise ValueError(
            "from_date and to_date are required"
        )

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
        "Historical data status:",
        response.status_code
    )

    response.raise_for_status()

    data = response.json()

    if data.get("status") != "success":

        raise RuntimeError(
            f"Upstox API error: {data}"
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
                "open_interest"
            ]
        )

    columns = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "open_interest"
    ]

    df = pd.DataFrame(
        candles,
        columns=columns
    )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "open_interest"
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
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n======================================"
    )

    print(
        "TESTING EXPIRED OPTION API"
    )

    print(
        "======================================\n"
    )

    expiries = get_expired_expiries()
    expiry = expiries[-1]

    print(
        "Expiry:",
        expiry
    )

    contracts = get_expired_option_contracts(
        expiry
    )

    print(
        "Contracts received:",
        len(contracts)
    )

    print("\nFirst contract:")

    print(
        contracts[0]
    )
    