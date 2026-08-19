import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

access_token = os.getenv("UPSTOX_ACCESS_TOKEN")

url = "https://api.upstox.com/v2/option/chain"

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {access_token}"
}

params = {
    "instrument_key": "NSE_INDEX|Nifty 50",
    "expiry_date": "2026-08-18"
}

response = requests.get(
    url,
    headers=headers,
    params=params
)

print("Status Code:", response.status_code)

data = response.json()

if data.get("status") != "success":
    print("API Error:")
    print(data)
    exit()

option_chain = data.get("data", [])

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
    # CREATE ROW
    # -----------------------------

    row = {

        # General
        "expiry": item.get("expiry"),
        "strike": strike,
        "spot_price": item.get("underlying_spot_price"),

        # PCR may not exist on every row
        "pcr": item.get("pcr"),

        # =========================
        # CALL
        # =========================

        "ce_instrument_key": call.get("instrument_key"),

        "ce_ltp": call_market.get("ltp"),
        "ce_volume": call_market.get("volume"),
        "ce_oi": ce_oi,
        "ce_prev_oi": ce_prev_oi,
        "ce_oi_change": ce_oi_change,

        "ce_close": call_market.get("close_price"),

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

        # =========================
        # PUT
        # =========================

        "pe_instrument_key": put.get("instrument_key"),

        "pe_ltp": put_market.get("ltp"),
        "pe_volume": put_market.get("volume"),
        "pe_oi": pe_oi,
        "pe_prev_oi": pe_prev_oi,
        "pe_oi_change": pe_oi_change,

        "pe_close": put_market.get("close_price"),

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
# CREATE DATAFRAME
# =====================================

df = pd.DataFrame(rows)

# Sort by strike
df = df.sort_values("strike")

# Reset index
df = df.reset_index(drop=True)

os.makedirs("data", exist_ok=True)

df.to_csv(
    "data/nifty_option_chain.csv",
    index=False
)

print("\nData saved to: data/nifty_option_chain.csv")


# =====================================
# DISPLAY
# =====================================

print("\nTotal rows:", len(df))

print("\nColumns:")
print(df.columns.tolist())

print("\nFirst 10 rows:")
print(df.head(10).to_string(index=False))

# =====================================
# FIND ATM
# =====================================

spot = df["spot_price"].iloc[0]

atm = min(
    df["strike"],
    key=lambda x: abs(x - spot)
)

print("\nNIFTY Spot:", spot)
print("ATM Strike:", atm)


# =====================================
# FILTER ATM ± 10 STRIKES
# =====================================

strikes = sorted(df["strike"].unique())

atm_index = strikes.index(atm)

lower_index = max(0, atm_index - 10)
upper_index = min(len(strikes), atm_index + 11)

selected_strikes = strikes[
    lower_index:upper_index
]

atm_df = df[
    df["strike"].isin(selected_strikes)
].copy()

atm_df = atm_df.sort_values("strike")

print("\nATM Option Chain:")
print(
    atm_df[
        [
            "strike",
            "ce_oi",
            "ce_oi_change",
            "ce_volume",
            "ce_ltp",
            "pe_ltp",
            "pe_volume",
            "pe_oi_change",
            "pe_oi"
        ]
    ].to_string(index=False)
)
# =====================================
# MAX OI
# =====================================

max_ce_oi_row = df.loc[df["ce_oi"].idxmax()]
max_pe_oi_row = df.loc[df["pe_oi"].idxmax()]

print("\n========== MAX OI ==========")

print(
    "MAX CE OI:",
    max_ce_oi_row["strike"],
    "| OI:",
    max_ce_oi_row["ce_oi"]
)

print(
    "MAX PE OI:",
    max_pe_oi_row["strike"],
    "| OI:",
    max_pe_oi_row["pe_oi"]
)


# =====================================
# MAX OI CHANGE
# =====================================

max_ce_change_row = df.loc[
    df["ce_oi_change"].idxmax()
]

max_pe_change_row = df.loc[
    df["pe_oi_change"].idxmax()
]

print("\n========== MAX OI CHANGE ==========")

print(
    "MAX CE ΔOI:",
    max_ce_change_row["strike"],
    "| ΔOI:",
    max_ce_change_row["ce_oi_change"]
)

print(
    "MAX PE ΔOI:",
    max_pe_change_row["strike"],
    "| ΔOI:",
    max_pe_change_row["pe_oi_change"]
)

# =====================================
# PCR CALCULATIONS
# =====================================

total_ce_oi = df["ce_oi"].fillna(0).sum()
total_pe_oi = df["pe_oi"].fillna(0).sum()

overall_pcr = (
    total_pe_oi / total_ce_oi
    if total_ce_oi != 0
    else None
)


atm_ce_oi = atm_df["ce_oi"].fillna(0).sum()
atm_pe_oi = atm_df["pe_oi"].fillna(0).sum()

atm_pcr = (
    atm_pe_oi / atm_ce_oi
    if atm_ce_oi != 0
    else None
)


print("\n========== PCR ==========")

print("Total CE OI:", total_ce_oi)
print("Total PE OI:", total_pe_oi)

print("Overall PCR:", round(overall_pcr, 3))
print("ATM-range PCR:", round(atm_pcr, 3))