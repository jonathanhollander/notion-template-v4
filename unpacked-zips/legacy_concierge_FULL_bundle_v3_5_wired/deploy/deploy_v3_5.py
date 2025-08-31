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

def prop_schema_from_yaml(props):
    # Map simple YAML property shorthand into Notion DB property definitions
    out = {}
    for name, kind in props.items():
        if kind == "title":
            out[name] = {"title": {}}
        elif kind == "select":
            out[name] = {"select": {"options": []}}
        elif kind == "rich_text":
            out[name] = {"rich_text": {}}
        else:
            out[name] = {"rich_text": {}}
    return out

def prop_values_from_row(row, schema_kinds):
    # Convert seed row dict into Notion property values
    vals = {}
    for name, value in row.items():
        kind = schema_kinds.get(name, "rich_text")
        if kind == "title":
            vals[name] = {"title":[{"type":"text","text":{"content":str(value)}}]}
        elif kind == "select":
            vals[name] = {"select":{"name":str(value)}}
        else:
            vals[name] = {"rich_text":[{"type":"text","text":{"content":str(value)}}]}
    return vals

def create_page_payload(title, parent_id, icon=None, cover=None, description=None):
    payload = {"parent":{"type":"page_id","page_id":parent_id},
               "properties":{"title":{"title":[{"text":{"content":title}}]}}}
    if icon:
        payload["icon"] = {"type":"external","external":{"url":icon}}
    if cover:
        payload["cover"] = {"type":"external","external":{"url":cover}}
    children = []
    if description:
        children.append({"object":"block","type":"paragraph",
                         "paragraph":{"rich_text":[{"type":"text","text":{"content":description}}]}})
    if children:
        payload["children"] = children
    return payload

def create_db_payload(title, parent_id, properties, options=None):
    db_props = prop_schema_from_yaml(properties)
    # Apply select options if provided
    if options:
        for prop_name, values in options.items():
            if prop_name in db_props and "select" in db_props[prop_name]:
                db_props[prop_name]["select"]["options"] = [{"name": v} for v in values]
    payload = {
        "parent":{"type":"page_id","page_id":parent_id},
        "title":[{"type":"text","text":{"content":title}}],
        "properties": db_props
    }
    return payload

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="split_yaml", help="YAML directory")
    ap.add_argument("--deploy", action="store_true", help="Deploy to Notion")
    ap.add_argument("--dry-run", action="store_true", help="Preview only")
    args = ap.parse_args()

    if not NOTION_TOKEN:
        print("ERROR: NOTION_TOKEN missing. Set it in environment or .env")
        sys.exit(1)

    merged = load_split_yaml(args.dir)
    pages = merged.get("pages", [])
    letters = merged.get("letters", [])
    db = merged.get("db", {})
    globals_cfg = merged.get("globals", {})

    print(f"Loaded: {len(pages)} pages | {len(letters)} letters | {len(db.get('schemas',{}))} databases")

    parent = DEFAULT_PARENT or input("Enter Notion parent page ID: ").strip()
    Path(".parent_cache").write_text(parent, encoding="utf-8")

    # PLAN
    print("\nPLAN:")
    for p in pages:
        role = p.get("role","owner")
        mark = {"executor":"[SAGE ◆]","family":"[PEACH ◆]","owner":"[BEIGE ◆]"}.get(role,"[◆]")
        print(f"  PAGE  {mark} {p.get('title')}  (disclaimer={'yes' if p.get('disclaimer') else 'no'})")
    for name in (db.get("schemas") or {}).keys():
        print(f"  DB    [DB] {name}")
    for L in letters:
        print(f"  LETTER [L] {L.get('Title')} → {L.get('Audience')}/{L.get('Category')}")

    if args.dry_run and not args.deploy:
        print("\nDry-run complete. Re-run with --deploy to create content.")
        return

    if not args.deploy:
        confirm = input("Deploy now? (y/N): ").lower().strip()
        if confirm != "y":
            print("Canceled.")
            return

    # --- Create a top-level "Letters" page to contain letter pages ---
    letters_parent_id = None
    # Create "Letters" page under parent
    payload_letters_parent = create_page_payload("Letters", parent,
        icon=globals_cfg.get("icons",{}).get("owner"),
        cover=globals_cfg.get("covers",{}).get("owner"),
        description="Sample letters to help you begin. Adjust details for your situation.")
    resp = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, data=json.dumps(payload_letters_parent))
    if resp.status_code < 300:
        letters_parent_id = resp.json()["id"]
        print(f"Created Letters parent page: {letters_parent_id}")
    else:
        print(f"ERROR creating Letters parent page: {resp.status_code} {resp.text}")
        sys.exit(1)

    # --- Create pages ---
    for i,p in enumerate(pages, start=1):
        payload = create_page_payload(p["title"], parent, icon=p.get("icon"), cover=p.get("cover"), description=p.get("description"))
        r = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, data=json.dumps(payload))
        if r.status_code >= 300:
            print(f"[PAGE {i}] ERROR {p['title']}: {r.status_code} {r.text}")
        else:
            print(f"[PAGE {i}] Created: {p['title']}")
        time.sleep(0.25)

    # --- Create databases ---
    schemas = db.get("schemas") or {}
    for i,(db_name, spec) in enumerate(schemas.items(), start=1):
        properties = spec.get("properties") or {}
        options = spec.get("options") or {}
        db_payload = create_db_payload(db_name, parent, properties, options)
        r = requests.post("https://api.notion.com/v1/databases", headers=HEADERS, data=json.dumps(db_payload))
        if r.status_code >= 300:
            print(f"[DB {i}] ERROR {db_name}: {r.status_code} {r.text}")
            continue
        database_id = r.json()["id"]
        print(f"[DB {i}] Created database: {db_name} ({database_id})")

        # Seed rows
        seeds = spec.get("seed_rows") or []
        # Build a name→kind lookup for property types
        schema_kinds = {}
        for n,k in properties.items():
            schema_kinds[n] = k
        for j,row in enumerate(seeds, start=1):
            props = prop_values_from_row(row, schema_kinds)
            payload = {"parent":{"type":"database_id","database_id":database_id},"properties":props}
            pr = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, data=json.dumps(payload))
            if pr.status_code >= 300:
                print(f"   [SEED {j}] ERROR: {pr.status_code} {pr.text}")
            else:
                print(f"   [SEED {j}] Row added.")
            time.sleep(0.2)

    # --- Create letter pages under Letters parent ---
    for i,L in enumerate(letters, start=1):
        title = L.get("Title")
        body = L.get("Body","")
        disclaimer = L.get("Disclaimer","Sample letter — adjust for your situation.")
        body_children = [
            {"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"ℹ️"},"rich_text":[{"type":"text","text":{"content":disclaimer}}]}},
            {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":body}}]}}
        ]
        payload = {
            "parent":{"type":"page_id","page_id":letters_parent_id},
            "properties":{"title":{"title":[{"text":{"content":title}}]}},
            "children": body_children
        }
        r = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, data=json.dumps(payload))
        if r.status_code >= 300:
            print(f"[LETTER {i}] ERROR {title}: {r.status_code} {r.text}")
        else:
            print(f"[LETTER {i}] Created: {title}")
        time.sleep(0.2)

    print("\nAll content created.")
    print("Tip: Move/organize child pages under their hubs inside Notion as preferred.")

if __name__ == "__main__":
    main()
