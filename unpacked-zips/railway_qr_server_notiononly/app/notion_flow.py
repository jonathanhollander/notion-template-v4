from typing import List, Dict, Tuple, Optional
from notion_client import Client
import requests, uuid

NOTION_VERSION = "2022-06-28"  # set compatible version if needed

def oauth_token_exchange(client_id, client_secret, redirect_uri, code) -> Dict:
    resp = requests.post("https://api.notion.com/v1/oauth/token", auth=(client_id, client_secret), json={
        "grant_type":"authorization_code",
        "code": code,
        "redirect_uri": redirect_uri
    })
    resp.raise_for_status()
    return resp.json()

def get_client(access_token: str) -> Client:
    return Client(auth=access_token)

def find_roots(notion: Client, menu_page_id: str, family_name: str, executor_name: str) -> Tuple[Optional[str], Optional[str]]:
    # list children of menu and find pages matching names
    children = notion.blocks.children.list(block_id=menu_page_id)
    fam = exe = None
    for b in children.get("results", []):
        if b.get("type") == "child_page":
            title = b["child_page"]["title"]
            if title.strip().lower() == family_name.strip().lower(): fam = b["id"]
            if title.strip().lower() == executor_name.strip().lower(): exe = b["id"]
    return fam, exe

def crawl_subtree(notion: Client, root_page_id: str) -> List[Dict]:
    out = []
    def dfs(bid: str):
        res = notion.blocks.children.list(block_id=bid)
        for b in res.get("results", []):
            t = b.get("type")
            if t == "child_page":
                pid = b["id"]; title = b["child_page"]["title"]
                out.append({"page_id": pid, "title": title})
                dfs(pid)
        if res.get("has_more"):
            cursor = res.get("next_cursor")
            while cursor:
                res = notion.blocks.children.list(block_id=bid, start_cursor=cursor)
                for b in res.get("results", []):
                    if b.get("type") == "child_page":
                        pid = b["id"]; title = b["child_page"]["title"]
                        out.append({"page_id": pid, "title": title})
                        dfs(pid)
                cursor = res.get("next_cursor") if res.get("has_more") else None
    dfs(root_page_id)
    return out

def retrieve_page_url(notion: Client, page_id: str) -> str:
    pg = notion.pages.retrieve(page_id=page_id)
    return pg.get("url","")

def ensure_page(notion: Client, parent_page_id: str, title: str) -> str:
    # try to find existing child with this title
    kids = notion.blocks.children.list(block_id=parent_page_id)
    for b in kids.get("results", []):
        if b.get("type") == "child_page" and b["child_page"]["title"] == title:
            return b["id"]
    # else create
    created = notion.blocks.children.append(block_id=parent_page_id, children=[{
        "object":"block","type":"child_page","child_page":{"title": title}
    }])
    return created["results"][0]["id"]

# --- Notion Direct Upload (documented approach) ---
# Strategy: Create a temporary page property with type 'files' or create an image block using 'file' form
# using the "external_s3_url" returned by an initiate-upload step, then PUT the bytes to that URL.
# This function implements the documented 2-step flow. Adapt if Notion updates their API.
def direct_upload_image_and_get_file_object(access_token: str, file_bytes: bytes, filename: str) -> Dict:
    # 1) Initiate upload
    init = requests.post(
        "https://api.notion.com/v1/files",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"
        },
        json={"file":{"name": filename}}
    )
    init.raise_for_status()
    info = init.json()
    upload_url = info["upload_url"]
    file_id = info["id"]

    # 2) Upload bytes to pre-signed URL
    put = requests.put(upload_url, data=file_bytes, headers={"Content-Type":"image/png"})
    put.raise_for_status()

    # 3) Return file object reference
    return {"type":"file","file":{"file_id": file_id, "name": filename}}

def append_image_block_from_file(notion: Client, parent_page_id: str, file_obj: Dict, caption_text: str):
    # Append an image block using the uploaded file reference
    notion.blocks.children.append(block_id=parent_page_id, children=[{
        "object":"block",
        "type":"image",
        "image": file_obj,
        "has_children": False
    }])
    # Optionally, we could set a caption by following up with a block update if supported.

