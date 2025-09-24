import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# Test both formats
ids_to_test = [
    ("With hyphens", "277a6c4e-badd-8079-9d19-d839db90e901"),
    ("Without hyphens", "277a6c4ebadd80799d19d839db90e901")
]

for label, page_id in ids_to_test:
    print(f"\n{label}: {page_id}")
    url = f"https://api.notion.com/v1/pages/{page_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print(f"✅ SUCCESS - Found page")
        page_data = response.json()
        print(f"Page type: {page_data.get('object')}")
    else:
        print(f"❌ FAILED - {response.status_code}")
        print(f"Error: {response.json().get('message', 'Unknown error')}")
