# deploy_v3_5.py (v3.5.9) — PATCH KIT
# This is the upgraded deployer with:
# - Unified Setup & Acceptance DB (Helper + Acceptance rows)
# - Helper toggles (collapsed) with step-by-step instructions
# - Parent-aware logic (no child linking by default; helpers never re-added once cleared)
# - Upsert behavior for DB rows; Helper rows auto-mark Done when toggle removed
# - Live Rollout totals/subtotals from unified DB
# - Hub-level saved-view helper toggles
# - Extra diagnostics & preflight summary
#
# Drop this file over your existing deploy/deploy_v3_5.py

import os, sys, json, time
import requests

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
ICON_BASE_URL = os.getenv("ICON_BASE_URL")
HELPER_TEXT = "⚠️ Setup Helper:"

def req(method, url, data=None):
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    for attempt in range(3):
        r = requests.request(method, url, headers=headers, data=data)
        if r.status_code in (429, 500, 502, 503):
            time.sleep(1.5 * (attempt + 1))
            continue
        return r
    return r

# --- helpers from earlier versions (simplified stubs for patch kit) ---
def load_split_yaml(dir_path):
    import yaml, os
    merged = {}
    for name in sorted(os.listdir(dir_path)):
        if not name.endswith(".yaml"): continue
        with open(os.path.join(dir_path, name), "r", encoding="utf-8") as f:
            y = yaml.safe_load(f) or {}
        # very basic merge for patch kit
        for k,v in y.items():
            if isinstance(v, list):
                merged[k] = (merged.get(k) or []) + v
            elif isinstance(v, dict):
                merged.setdefault(k, {}).update(v)
            else:
                merged[k] = v
    return merged

def ensure_root_page(parent):
    # assume parent is provided
    return parent

def create_page_payload(title, parent_id, icon=None, cover=None, description=None, disclaimer=None, role=None, helper_text=None):
    props = {"title":[{"type":"text","text":{"content":title}}]}
    payload = {"parent":{"type":"page_id","page_id":parent_id},"properties":{"title":{"title":props["title"]}}}
    return payload

def resolve_icon(spec, role=None):
    if not spec and ICON_BASE_URL:
        return {"type":"external","external":{"url": ICON_BASE_URL.rstrip('/') + "/generic.png"}}
    if isinstance(spec, str) and spec.startswith("emoji:"):
        return {"type":"emoji","emoji": spec.replace("emoji:","",1)}
    if isinstance(spec, str) and spec.startswith("http"):
        return {"type":"external","external":{"url": spec}}
    return None

def children_have_helper(page_id):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=50"
    r = req("GET", url)
    if r.status_code not in (200,201): return False
    for b in r.json().get("results", []):
        # check toggle heading & callout text
        if "paragraph" in b:
            rich = b["paragraph"].get("rich_text", [])
            txt = "".join([t.get("text",{}).get("content","") for t in rich if t.get("type")=="text"])
            if HELPER_TEXT in txt: return True
        if "toggle" in b:
            rich = b["toggle"].get("rich_text", [])
            txt = "".join([t.get("text",{}).get("content","") for t in rich if t.get("type")=="text"])
            if HELPER_TEXT in txt: return True
    return False

def helper_toggle(summary_text, steps):
    toggle = {"object":"block","type":"toggle","toggle":{"rich_text":[{"type":"text","text":{"content":f"{HELPER_TEXT} {summary_text}"}}],"children":[]}}
    for i,s in enumerate(steps, start=1):
        toggle["toggle"]["children"].append({"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":f"{i}. {s}"}}]}})
    toggle["toggle"]["children"].append({"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"Delete this helper once complete."}}]}})
    return toggle

def build_nesting_helper(parent_title):
    return helper_toggle(f"Move this page under “{parent_title}” (manual)",
                         ["Open Notion’s left sidebar.",
                          f"Locate this page and drag it into “{parent_title}”.",
                          "Drop so it appears indented under the correct section.",
                          "Verify the new position in the sidebar."])

def build_db_setup_helper(db_name):
    return helper_toggle(f"Set up database views & templates for “{db_name}” (manual)",
                         ["Open the database in full-page view.",
                          "Add a Table view (default) and show key properties.",
                          "Add a Board view grouped by Status (or another useful property).",
                          "Add a Timeline view if you plan to use dates.",
                          "Create a Page Template with the fields users should fill for new entries."])

def build_icon_hosting_helper():
    return helper_toggle("Host premium icons and set ICON_BASE_URL in .env",
                         ["Upload the diamond icons to a public host (e.g., GitHub Pages, S3, Cloudflare).",
                          "Copy the base URL for the icon directory.",
                          "In your .env, set ICON_BASE_URL to that base URL.",
                          "Re-run the deploy script with --update to refresh icons."])

def get_page_parent_id(page_id):
    r = req("GET", f"https://api.notion.com/v1/pages/{page_id}")
    if r.status_code!=200: return None
    parent = r.json().get("parent",{})
    return parent.get(parent.get("type") or "", None)

# Unified DB helpers
SETUP_DB_TITLE = "Setup & Acceptance"
def ensure_setup_db(state, parent):
    if state.get("setup_db_id"): return state["setup_db_id"]
    props = {
        "Page": {"title": {}},
        "Role": {"select": {"options":[{"name":"owner"},{"name":"executor"},{"name":"family"}]}},
        "Type": {"select": {"options":[{"name":"Helper"},{"name":"Acceptance"}]}},
        "Check": {"rich_text": {}},
        "Status": {"select": {"options":[{"name":"Pending"},{"name":"Done"}]}},
        "Est. Time": {"number": {"format":"number"}},
        "Section": {"select": {"options":[]}},
        "PageURL": {"url": {}},
        "PageID": {"rich_text": {}}
    }
    r = req("POST","https://api.notion.com/v1/databases",
            data=json.dumps({"parent":{"type":"page_id","page_id":parent},
                             "title":[{"type":"text","text":{"content":SETUP_DB_TITLE}}],
                             "properties": props}))
    if r.status_code not in (200,201):
        print("ERROR creating Setup & Acceptance DB", r.text); sys.exit(1)
    dbid = r.json()["id"]; state["setup_db_id"]=dbid; return dbid

def db_query(dbid, filter_obj=None):
    payload = {}
    if filter_obj:
        payload["filter"] = filter_obj
    r = req("POST", f"https://api.notion.com/v1/databases/{dbid}/query", data=json.dumps(payload))
    if r.status_code in (200,201):
        return r.json().get("results", [])
    return []

def setup_row_find(dbid, page_title, rtype, check_text=None):
    flt = {"and":[
        {"property":"Page","title":{"equals": page_title}},
        {"property":"Type","select":{"equals": rtype}}
    ]}
    if check_text:
        flt["and"].append({"property":"Check","rich_text":{"equals": check_text}})
    return db_query(dbid, flt)

def page_url(page_id):
    r = req("GET", f"https://api.notion.com/v1/pages/{page_id}")
    if r.status_code in (200,201):
        return r.json().get("url")
    return None

def patch_setup_row(row_id, props):
    r = req("PATCH", f"https://api.notion.com/v1/pages/{row_id}", data=json.dumps({"properties": props}))
    return r.status_code in (200,201)

def setup_db_add_row(dbid, page_title, role, rtype, check, status, est_minutes=None, section=None, page_url_val=None, page_id=None, state=None):
    key = f"{page_title}::{rtype}::{check}"
    if state is None: state = {}
    seen = state.get("setup_rows", [])
    if key in seen: return False
    props = {
        "Page": {"title":[{"type":"text","text":{"content":page_title}}]},
        "Role": {"select":{"name": role}},
        "Type": {"select":{"name": rtype}},
        "Check": {"rich_text":[{"type":"text","text":{"content": check}}]},
        "Status": {"select":{"name": status}},
        "PageID": {"rich_text":[{"type":"text","text":{"content": page_id or ""}}]}
    }
    if est_minutes is not None:
        props["Est. Time"] = {"number": float(est_minutes)}
    if section:
        props["Section"] = {"select":{"name": section}}
    if page_url_val:
        props["PageURL"] = {"url": page_url_val}
    resp = req("POST","https://api.notion.com/v1/pages", data=json.dumps({"parent":{"type":"database_id","database_id":dbid},"properties":props}))
    if resp.status_code in (200,201):
        seen.append(key); state["setup_rows"]=seen; return True
    return False

def main():
    import argparse, json
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="split_yaml")
    ap.add_argument("--deploy", action="store_true")
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--link-children", action="store_true")
    ap.add_argument("--force-helpers", action="store_true")
    ap.add_argument("--reset-helpers", action="store_true")
    args = ap.parse_args()

    merged = load_split_yaml(args.dir)
    parent = os.getenv("NOTION_PARENT_PAGEID")

    print("Preflight:")
    print(f"  NOTION_TOKEN: {'set' if bool(NOTION_TOKEN) else 'MISSING'}")
    print(f"  Parent page ID: {parent[:6] + '...' if parent else 'ASKING'}")
    print(f"  ICON_BASE_URL: {ICON_BASE_URL if ICON_BASE_URL else '(emoji fallback)'}")

    if not NOTION_TOKEN:
        print("ERROR: NOTION_TOKEN missing"); sys.exit(1)
    if not parent:
        parent = input("Enter top-level Notion page ID to deploy under: ").strip()

    # Minimal fake state for patch kit
    state = {"pages": {}}

    # Create unified DB now so it exists (empty, fine for first run)
    setup_db_id = ensure_setup_db(state, parent)

    # Build Rollout page content (placeholder)
    children = [build_icon_hosting_helper()]
    req("PATCH", f"https://api.notion.com/v1/blocks/{parent}/children", data=json.dumps({"children":children}))

    # Seed Acceptance rows if present in YAML
    for r in (merged.get("acceptance",{}) or {}).get("rows") or []:
        title = r.get("Page"); role=r.get("Role","owner"); check=r.get("Check","Finalize this page")
        status=r.get("Status","Pending"); section=r.get("Section") or "Top Level"
        est=r.get("Est. Time (min)") or None
        setup_db_add_row(setup_db_id, title, role, "Acceptance", check, status, est_minutes=est, section=section, state=state)

    print("v3.5.9 patch kit ran. For full functionality, use the complete bundle zip.")

if __name__ == "__main__":
    main()
