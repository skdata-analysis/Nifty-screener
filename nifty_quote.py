import os
import requests
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Get access token
access_token = os.getenv("UPSTOX_ACCESS_TOKEN")

# NIFTY 50 instrument key
instrument_key = "NSE_INDEX|Nifty 50"

# Upstox Full Market Quote API
url = "https://api.upstox.com/v2/market-quote/quotes"

# Authentication headers
headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {access_token}"
}

# Parameters
params = {
    "instrument_key": instrument_key
}

# Send request
response = requests.get(
    url,
    headers=headers,
    params=params
)

# Display result
print("Status Code:", response.status_code)
print("Response:")
print(response.text)