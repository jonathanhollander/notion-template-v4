#!/usr/bin/env python3
import os, sys, json, glob, time
from pathlib import Path
from dotenv import load_dotenv
import yaml
import requests

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_VERSION = os.getenv("NOTION_VERSION","2022-06-28")
DEFAULT_PARENT = os.getenv("NOTION_PARENT_PAGEID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}" if NOTION_TOKEN else "",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}

def load_split_yaml(dir_path):
    merged = {"pages": [], "letters": [], "db": {}, "diagnostics": {}, "acceptance": {}, "globals": {}}
    files = sorted(glob.glob(str(Path(dir_path) / "*.yaml")))
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        # Merge keys if present
        for k in ["pages", "letters"]:
            if k in data:
                merged[k].extend(data[k])
        for k in ["db", "diagnostics", "acceptance", "globals", "meta"]:
            if k in data:
                if isinstance(data[k], dict):
                    merged[k].update(data[k])
                else:
                    merged[k] = data[k]
    return merged

def human(title):
    print(f"— {title}")

def create_page(title, parent_id, icon=None, cover=None, description=None):
    payload = {"parent":{"type":"page_id","page_id":parent_id},"properties":{"title":{"title":[{"text":{"content":title}}]}}}
    if icon:
        payload["icon"] = {"type":"external","external":{"url":icon}}
    if cover:
        payload["cover"] = {"type":"external","external":{"url":cover}}
    if description:
        payload.setdefault("children",[]).append({"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":description}}]}})
    return payload

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="split_yaml", help="YAML directory")
    ap.add_argument("--deploy", action="store_true", help="Deploy to Notion")
    ap.add_argument("--dry-run", action="store_true", help="Preview actions without API calls")
    args = ap.parse_args()

    if not NOTION_TOKEN:
        print("ERROR: NOTION_TOKEN missing. Set in environment or .env")
        sys.exit(1)

    merged = load_split_yaml(args.dir)
    pages = merged.get("pages", [])
    print(f"Loaded {len(pages)} pages from split YAML.")

    parent = DEFAULT_PARENT or input("Enter Notion parent page ID: ").strip()
    cache_path = Path(".parent_cache")
    cache_path.write_text(parent, encoding="utf-8")

    # Show plan
    print("\nPLAN:")
    for p in pages:
        role = p.get("role","owner")
        mark = {"executor":"[SAGE ◆]","family":"[PEACH ◆]","owner":"[BEIGE ◆]"}.get(role,"[◆]")
        print(f"  {mark} {p.get('title')} (disclaimer={'yes' if p.get('disclaimer') else 'no'})")

    if args.dry_run and not args.deploy:
        print("\nDry-run complete. Re-run with --deploy to create content.")
        return

    if not args.deploy:
        confirm = input("Deploy now? (y/N): ").lower().strip()
        if confirm != "y":
            print("Canceled.")
            return

    # Deploy (pages only — DBs/letters placeholders to illustrate structure)
    base_url = "https://api.notion.com/v1/pages"
    for i,p in enumerate(pages, start=1):
        payload = create_page(p["title"], parent, icon=p.get("icon"), cover=p.get("cover"), description=p.get("description"))
        if args.deploy:
            resp = requests.post(base_url, headers=HEADERS, data=json.dumps(payload))
            if resp.status_code >= 300:
                print(f"[{i}] ERROR creating {p['title']}: {resp.status_code} {resp.text}")
            else:
                print(f"[{i}] Created: {p['title']}")
        else:
            print(f"[{i}] Would create: {p['title']}")
        time.sleep(0.25)

    print("\nDone.")
if __name__ == "__main__":
    main()
