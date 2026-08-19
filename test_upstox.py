import os
import requests
from dotenv import load_dotenv

load_dotenv()

access_token = os.getenv("UPSTOX_ACCESS_TOKEN")

url = "https://api.upstox.com/v2/user/profile"

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(url, headers=headers)

print("Status Code:", response.status_code)
print("Response:")
print(response.text)