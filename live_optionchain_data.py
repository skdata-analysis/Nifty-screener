import os
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()
def get_available_expiries():

    access_token = os.getenv("UPSTOX_ACCESS_TOKEN")

    if not access_token:
        raise ValueError(
            "UPSTOX_ACCESS_TOKEN not found in .env"
        )

    url = "https://api.upstox.com/v2/option/contract"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "instrument_key": "NSE_INDEX|Nifty 50"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    if data.get("status") != "success":
        raise RuntimeError(
            f"Unable to fetch expiries: {data}"
        )

    contracts = data.get("data", [])

    expiries = sorted(
        {
            contract.get("expiry")
            for contract in contracts
            if contract.get("expiry")
        }
    )

    if not expiries:
        raise RuntimeError(
            "No active NIFTY expiries found."
        )

    return expiries


def update_option_chain(expiry_date):

    access_token = os.getenv("UPSTOX_ACCESS_TOKEN")

    if not access_token:
        raise ValueError("UPSTOX_ACCESS_TOKEN not found in .env")

    url = "https://api.upstox.com/v2/option/chain"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "instrument_key": "NSE_INDEX|Nifty 50",
        "expiry_date": expiry_date
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=20
    )

    print("Status Code:", response.status_code)

    response.raise_for_status()

    data = response.json()

    if data.get("status") != "success":
        raise RuntimeError(
            f"Upstox API Error: {data}"
        )

    option_chain = data.get("data", [])
    fetch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    

    if not option_chain:
        raise RuntimeError(
            "Upstox returned an empty option chain."
        )

    rows = []

    for item in option_chain:

        strike = item.get("strike_price")

        call = item.get("call_options") or {}
        put = item.get("put_options") or {}

        call_market = call.get("market_data") or {}
        put_market = put.get("market_data") or {}

        call_greeks = call.get("option_greeks") or {}
        put_greeks = put.get("option_greeks") or {}

        # -----------------------------
        # CALL OI
        # -----------------------------

        ce_oi = call_market.get("oi")
        ce_prev_oi = call_market.get("prev_oi")

        if ce_oi is not None and ce_prev_oi is not None:
            ce_oi_change = ce_oi - ce_prev_oi
        else:
            ce_oi_change = None

        # -----------------------------
        # PUT OI
        # -----------------------------

        pe_oi = put_market.get("oi")
        pe_prev_oi = put_market.get("prev_oi")

        if pe_oi is not None and pe_prev_oi is not None:
            pe_oi_change = pe_oi - pe_prev_oi
        else:
            pe_oi_change = None

        # -----------------------------
        # ROW
        # -----------------------------

        row = {
            "fetch_time": fetch_time,
            "expiry": item.get("expiry"),
            "strike": strike,
            "spot_price": item.get(
                "underlying_spot_price"
            ),
            "pcr": item.get("pcr"),

            # CALL
            "ce_instrument_key": call.get(
                "instrument_key"
            ),
            "ce_ltp": call_market.get("ltp"),
            "ce_volume": call_market.get("volume"),
            "ce_oi": ce_oi,
            "ce_prev_oi": ce_prev_oi,
            "ce_oi_change": ce_oi_change,
            "ce_close": call_market.get(
                "close_price"
            ),
            "ce_bid": call_market.get("bid_price"),
            "ce_bid_qty": call_market.get("bid_qty"),
            "ce_ask": call_market.get("ask_price"),
            "ce_ask_qty": call_market.get("ask_qty"),

            "ce_iv": call_greeks.get("iv"),
            "ce_delta": call_greeks.get("delta"),
            "ce_gamma": call_greeks.get("gamma"),
            "ce_theta": call_greeks.get("theta"),
            "ce_vega": call_greeks.get("vega"),
            "ce_pop": call_greeks.get("pop"),

            # PUT
            "pe_instrument_key": put.get(
                "instrument_key"
            ),
            "pe_ltp": put_market.get("ltp"),
            "pe_volume": put_market.get("volume"),
            "pe_oi": pe_oi,
            "pe_prev_oi": pe_prev_oi,
            "pe_oi_change": pe_oi_change,
            "pe_close": put_market.get(
                "close_price"
            ),
            "pe_bid": put_market.get("bid_price"),
            "pe_bid_qty": put_market.get("bid_qty"),
            "pe_ask": put_market.get("ask_price"),
            "pe_ask_qty": put_market.get("ask_qty"),

            "pe_iv": put_greeks.get("iv"),
            "pe_delta": put_greeks.get("delta"),
            "pe_gamma": put_greeks.get("gamma"),
            "pe_theta": put_greeks.get("theta"),
            "pe_vega": put_greeks.get("vega"),
            "pe_pop": put_greeks.get("pop"),
        }

        rows.append(row)

    # =====================================
    # DATAFRAME
    # =====================================

    df = pd.DataFrame(rows)

    if df.empty:
        raise RuntimeError(
            "No option-chain rows received."
        )

    df = df.sort_values("strike")
    df = df.reset_index(drop=True)

    # =====================================
    # SAVE
    # =====================================

    base_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    data_dir = os.path.join(
        base_dir,
        "data"
    )

    os.makedirs(
        data_dir,
        exist_ok=True
    )

    csv_path = os.path.join(
        data_dir,
        "nifty_option_chain.csv"
    )

    df.to_csv(
        csv_path,
        index=False
    )

    print(
        f"Data saved to: {csv_path}"
    )

    print(
        f"Total rows: {len(df)}"
    )

    return df
if __name__ == "__main__":

    print("\n==============================")
    print("AVAILABLE NIFTY EXPIRIES")
    print("==============================")

    expiries = get_available_expiries()

    for expiry in expiries:
        print(expiry)

    print("\n==============================")
    print("FETCHING NEAREST EXPIRY")
    print("==============================")

    expiry_date = expiries[0]

    print("Selected expiry:", expiry_date)

    df = update_option_chain(
        expiry_date=expiry_date
    )

    print("\n==============================")
    print("FETCH SUCCESS")
    print("==============================")

    print("Rows:", len(df))

    print(
        "Spot:",
        df["spot_price"].iloc[0]
    )

    print(
        "Expiry:",
        df["expiry"].iloc[0]
    )

    print("CSV updated successfully.")
    
    