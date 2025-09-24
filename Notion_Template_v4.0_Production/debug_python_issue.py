import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
print(f"Token starts with: {NOTION_TOKEN[:10]}...")
print(f"Token length: {len(NOTION_TOKEN)}")

# Test with exact same headers as curl
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28"
}

page_id = "277a6c4ebadd80799d19d839db90e901"
url = f"https://api.notion.com/v1/pages/{page_id}"

print(f"\nRequesting: {url}")
print(f"Headers: {headers}")

response = requests.get(url, headers=headers)
print(f"\nStatus: {response.status_code}")
print(f"Response: {response.text[:500]}")

# Also check what the deploy script is doing
print("\n--- Checking deploy.py req function ---")

# Let's see what's in the actual request
import json
def test_req():
    r = requests.get(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers={
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    )
    return r

r = test_req()
print(f"With Content-Type: {r.status_code}")
print(f"Response: {r.text[:200]}")
