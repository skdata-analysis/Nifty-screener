import os
import requests
from dotenv import load_dotenv
from datetime import datetime, date

load_dotenv()

access_token = os.getenv("UPSTOX_ACCESS_TOKEN")

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
    params=params
)

print("Status Code:", response.status_code)

data = response.json()

if data["status"] != "success":
    print("API Error:")
    print(data)
    exit()

contracts = data["data"]

# ------------------------------------------------
# 1. Extract unique expiry dates
# ------------------------------------------------

expiry_dates = set()

for contract in contracts:

    expiry = contract.get("expiry")

    if expiry:
        expiry_dates.add(expiry)

# Convert string dates to date objects
today = date.today()

future_expiries = []

for expiry in expiry_dates:

    expiry_date = datetime.strptime(
        expiry,
        "%Y-%m-%d"
    ).date()

    if expiry_date >= today:
        future_expiries.append(expiry_date)

# Sort nearest first
future_expiries.sort()

# ------------------------------------------------
# 2. Display available expiries
# ------------------------------------------------

print("\nAvailable Future Expiries:")

for expiry in future_expiries[:10]:

    print(expiry)

# ------------------------------------------------
# 3. Select nearest expiry
# ------------------------------------------------

if not future_expiries:

    print("\nNo future expiry found.")

else:

    nearest_expiry = future_expiries[0]

    print("\nNearest Expiry:")
    print(nearest_expiry)

    # ------------------------------------------------
    # 4. Filter contracts for nearest expiry
    # ------------------------------------------------

    expiry_contracts = []

    for contract in contracts:

        expiry = contract.get("expiry")

        if expiry == nearest_expiry.strftime("%Y-%m-%d"):

            expiry_contracts.append(contract)

    print(
        "\nContracts for nearest expiry:",
        len(expiry_contracts)
    )

    # ------------------------------------------------
    # 5. Show first 10
    # ------------------------------------------------

    print("\nFirst 10 contracts:\n")

    for contract in expiry_contracts[:10]:

        print(
            contract.get("trading_symbol"),
            "| Strike:",
            contract.get("strike_price"),
            "| Type:",
            contract.get("instrument_type")
        )