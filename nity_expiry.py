import os
import requests
from dotenv import load_dotenv

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

if data["status"] == "success":

    contracts = data["data"]

    print("\nTotal contracts:", len(contracts))

    print("\nFirst 5 contracts:\n")

    for contract in contracts[:5]:

        print(
            "Symbol:",
            contract.get("trading_symbol"),
            "| Strike:",
            contract.get("strike_price"),
            "| Type:",
            contract.get("instrument_type"),
            "| Expiry:",
            contract.get("expiry"),
            "| Lot:",
            contract.get("lot_size")
        )

else:
    print("API Error:")
    print(data)
    