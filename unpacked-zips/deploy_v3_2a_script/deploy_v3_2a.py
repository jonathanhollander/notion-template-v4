#!/usr/bin/env python3
"""
deploy_v3_2a.py — Notion template deployer (split YAML + centralized strings)
- Loads multiple YAML files (meta, globals, databases, pages, subpages, diagnostics, acceptance, addons, admin)
- Resolves use_global.* string references
- Creates/updates databases and pages in Notion
- Saves parent page ID for future runs (.deploy_state.json)
- Dry-run preview shows a human-readable plan before deploying
- Verbose, human-friendly CLI output

Usage:
  python deploy_v3_2a.py --dir path/to/yaml/ --dry-run
  python deploy_v3_2a.py --dir path/to/yaml/ --deploy

Env:
  NOTION_TOKEN         = secret API token
  NOTION_VERSION       = 2022-06-28 (default)
  NOTION_PARENT_PAGEID = optional; if omitted, script will prompt once and persist in .deploy_state.json
"""
import os, sys, json, time, argparse, re
from pathlib import Path

try:
    import yaml
    import requests
except Exception as e:
    print("Missing dependency. Run: pip install pyyaml requests")
    sys.exit(1)

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = os.getenv("NOTION_VERSION", "2022-06-28")

STATE_FILE = ".deploy_state.json"

def load_yaml_files(directory: Path):
    """Load known YAML files if present; ignore missing gracefully."""
    order = [
        "meta.yaml",
        "globals.yaml",
        "databases.yaml",
        "pages.yaml",
        "subpages.yaml",
        "diagnostics.yaml",
        "acceptance.yaml",
        "addons.yaml",
        "admin.yaml",            # optional admin branch
    ]
    data = {}
    for name in order:
        p = directory / name
        if p.exists():
            with p.open("r", encoding="utf-8") as f:
                data[name] = yaml.safe_load(f) or {}
        else:
            data[name] = {}
    return data

def resolve_use_global(value, globals_obj):
    """Resolve strings starting with 'use_global.' into actual text; otherwise return value unchanged.
       Works recursively on simple containers."""
    if isinstance(value, str) and value.startswith("use_global."):
        # e.g., use_global.strings.pages.home.header
        parts = value.split(".")[1:]  # drop 'use_global'
        obj = globals_obj
        for part in parts:
            if part not in obj:
                raise KeyError(f"Missing globals key: {value}")
            obj = obj[part]
        return obj
    elif isinstance(value, list):
        return [resolve_use_global(v, globals_obj) for v in value]
    elif isinstance(value, dict):
        return {k: resolve_use_global(v, globals_obj) for k, v in value.items()}
    return value

def flatten_blocks(blocks, globals_obj):
    """Resolve use_global.* inside block definitions."""
    out = []
    for b in blocks or []:
        out.append(resolve_use_global(b, globals_obj))
    return out

def get_parent_page_id(args_dir: Path):
    # 1) env override
    env_page = os.getenv("NOTION_PARENT_PAGEID")
    if env_page:
        return env_page.strip()
    # 2) state file
    state_path = args_dir / STATE_FILE
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text())
            if "parent_page_id" in state and state["parent_page_id"]:
                return state["parent_page_id"]
        except Exception:
            pass
    # 3) prompt user
    parent = input("Enter NOTION parent page ID (will be saved for next run): ").strip()
    state = {"parent_page_id": parent}
    state_path.write_text(json.dumps(state, indent=2))
    return parent

def notion_headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json; charset=utf-8",
    }

def create_database(token, parent_page_id, title: str, schema: dict):
    url = f"{NOTION_API}/databases"
    props = {}
    for name, typ in (schema.get("properties") or {}).items():
        props[name] = {"type": typ, typ: {}}
    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": title}}],
        "properties": props,
    }
    r = requests.post(url, headers=notion_headers(token), data=json.dumps(payload))
    r.raise_for_status()
    return r.json()

def create_page(token, parent_page_id, title: str, icon=None, cover=None, children=None):
    url = f"{NOTION_API}/pages"
    payload = {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "properties": {"title": {"title": [{"type": "text", "text": {"content": title}}]}},
    }
    if icon:
        payload["icon"] = icon  # e.g., {"emoji":"📁"} or external
    if cover:
        payload["cover"] = {"type":"external","external":{"url": cover}}
    if children:
        payload["children"] = children
    r = requests.post(url, headers=notion_headers(token), data=json.dumps(payload))
    r.raise_for_status()
    return r.json()

def blockify(blocks):
    """Convert simplified blocks to Notion block payloads."""
    out = []
    for b in blocks or []:
        if not isinstance(b, dict) or len(b) != 1:
            continue
        (k, v), = b.items()
        def rt(txt):  # rich text object
            return [{"type":"text","text":{"content":txt}}]
        if k in ("h1","h2","h3","h4"):
            t = k.replace("h","heading_")+"_rich_text"
            level = k.replace("h","heading_")
            out.append({"object":"block","type":level, level: {"rich_text": rt(v)}})
        elif k in ("p","paragraph"):
            out.append({"object":"block","type":"paragraph","paragraph":{"rich_text": rt(v)}})
        elif k == "callout":
            out.append({"object":"block","type":"callout","callout":{"rich_text": rt(v), "icon":{"type":"emoji","emoji":"💡"}}})
        elif k == "bulleted_list":
            # v is list of strings
            for item in (v or []):
                out.append({"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text": rt(item)}})
        elif k == "numbered_list":
            for item in (v or []):
                out.append({"object":"block","type":"numbered_list_item","numbered_list_item":{"rich_text": rt(item)}})
        elif k == "divider":
            out.append({"object":"block","type":"divider","divider":{}})
        else:
            # fallback to paragraph
            out.append({"object":"block","type":"paragraph","paragraph":{"rich_text": rt(f"{k}: {v}")}})
    return out

def plan_from_yaml(data, globals_obj, addons):
    """Return a human-readable plan and a machine plan of DBs and pages to create."""
    plan = {"databases": [], "pages": []}
    # DBs
    db_section = data.get("databases.yaml", {}).get("db") or {}
    schemas = (db_section.get("schemas") or {})
    seeds = (db_section.get("seeds") or {})
    for db_name, schema in schemas.items():
        plan["databases"].append({"name": db_name, "schema": schema, "seed": seeds.get(db_name)})
    # Admin DBs
    admin_db = data.get("admin.yaml", {}).get("db") or {}
    for db_name, schema in (admin_db.get("schemas") or {}).items():
        plan["databases"].append({"name": db_name, "schema": schema, "seed": (admin_db.get("seeds") or {}).get(db_name)})
    # Pages
    for name in ("pages.yaml","subpages.yaml"):
        arr = (data.get(name) or {}).get("pages") or (data.get(name) or {}).get("subpages") or []
        for p in arr:
            blocks = flatten_blocks(p.get("blocks"), globals_obj)
            plan["pages"].append({
                "title": p["title"],
                "slug": p.get("slug"),
                "type": p.get("type","page"),
                "parent": p.get("parent"),
                "audience": p.get("audience","shared"),
                "disclaimer": resolve_use_global(p.get("disclaimer","NONE"), globals_obj) if isinstance(p.get("disclaimer"), str) else p.get("disclaimer","NONE"),
                "blocks": blocks,
                "note": p.get("note"),
                "is_admin": p.get("is_admin", False)
            })
    # Admin pages (ensure at top-level branch)
    admin_pages = (data.get("admin.yaml") or {}).get("pages") or []
    for p in admin_pages:
        blocks = flatten_blocks(p.get("blocks"), globals_obj)
        plan["pages"].append({
            "title": p["title"],
            "slug": p.get("slug"),
            "type": p.get("type","page"),
            "parent": p.get("parent"),  # admin subpage parent is slug, we’ll resolve after creation
            "audience": p.get("audience","shared"),
            "disclaimer": p.get("disclaimer","NONE"),
            "blocks": blocks,
            "is_admin": True
        })
    return plan

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="Directory containing split YAML files")
    ap.add_argument("--dry-run", action="store_true", help="Preview only (default)")
    ap.add_argument("--deploy", action="store_true", help="Execute creation in Notion")
    args = ap.parse_args()

    d = Path(args.dir)
    if not d.exists():
        print(f"Directory not found: {d}")
        sys.exit(1)

    token = os.getenv("NOTION_TOKEN")
    if not token:
        print("Missing NOTION_TOKEN in environment.")
        sys.exit(1)

    # Load YAML
    data = load_yaml_files(d)
    globals_obj = (data.get("globals.yaml") or {}).get("globals") or {}
    addons = data.get("addons.yaml") or {}

    parent_page_id = get_parent_page_id(d)

    # Build plan
    plan = plan_from_yaml(data, globals_obj, addons)

    # Human-readable preview
    print("=== PLAN ===")
    print(f"Databases to create: {len(plan['databases'])}")
    for i, db in enumerate(plan["databases"], 1):
        print(f"  {i:02d}. {db['name']}  (properties: {len((db['schema'].get('properties') or {}))})"
              f"{' + seeds' if db.get('seed') else ''}")
    print(f"Pages to create: {len(plan['pages'])}")
    for i, p in enumerate(plan["pages"], 1):
        parent = p.get("parent","<top>")
        print(f"  {i:03d}. {p['type']}: {p['title']}  [slug={p.get('slug')}] parent={parent} admin={p.get('is_admin', False)} blocks={len(p['blocks'])}")

    if not args.deploy:
        print("\nDry-run only. Use --deploy to create in Notion.")
        return

    # Deploy
    headers = notion_headers(token)

    # 1) Create all databases (root-level under parent page)
    name_to_dbid = {}
    for db in plan["databases"]:
        print(f"Creating DB: {db['name']} ...", end="", flush=True)
        try:
            res = create_database(token, parent_page_id, db["name"], db["schema"])
            dbid = res.get("id")
            name_to_dbid[db["name"]] = dbid
            print(" ok")
            # seeds
            if db.get("seed"):
                # seeding via page rows in DB
                rows = db["seed"]
                # Seed minimal rows (title only + simple prop values)
                for row in rows:
                    props = {}
                    for k, v in row.items():
                        if k == "Title":
                            props["Name"] = {"title":[{"type":"text","text":{"content": str(v)}}]}
                        else:
                            # best-effort set as rich_text or select
                            props[k] = {"rich_text":[{"type":"text","text":{"content": str(v)}}]}
                    payload = {
                        "parent": {"database_id": dbid},
                        "properties": props
                    }
                    r = requests.post(f"{NOTION_API}/pages", headers=headers, data=json.dumps(payload))
                    r.raise_for_status()
                print(f"  seeded {len(rows)} rows")
        except Exception as e:
            print(f"\n  ERROR creating DB {db['name']}: {e}")
            continue

    # 2) Create pages
    # We first create top-level pages, capture their IDs, then wire subpages that reference a 'parent' slug
    slug_to_pageid = {}

    # helper to get icon/cover from globals addons (optional)
    icons = ((globals_obj.get("icons_map") or {}) | ((addons.get("assets") or {}).get("icons") or {}))
    covers_map = ((globals_obj.get("covers_map") or {}) | ((addons.get("assets") or {}).get("covers") or {}))

    # Create top-level pages (type == 'page' and no parent)
    for p in [pp for pp in plan["pages"] if pp["type"] == "page" and not pp.get("parent")]:
        emoji = icons.get(p.get("slug"))
        icon = {"type":"emoji","emoji":emoji} if emoji else None
        cover = covers_map.get(p.get("slug"))
        children = blockify(p["blocks"])
        print(f"Creating page: {p['title']} ...", end="", flush=True)
        try:
            res = create_page(token, parent_page_id, p["title"], icon=icon, cover=cover, children=children)
            pid = res.get("id")
            slug_to_pageid[p.get("slug")] = pid
            print(" ok")
        except Exception as e:
            print(f"\n  ERROR creating page {p['title']}: {e}")

    # Create subpages and admin subpages (type == 'subpage' or has parent slug)
    # Admin root parent (admin-cockpit) must be resolved to its page id
    for p in [pp for pp in plan["pages"] if pp.get("parent")]:
        parent_slug = p["parent"]
        parent_id = slug_to_pageid.get(parent_slug)
        if not parent_id:
            # If parent not yet created (e.g., admin-cockpit is top-level page we created above), try again:
            print(f"Warning: parent slug not found for {p['title']} → {parent_slug}. Skipping.")
            continue
        emoji = icons.get(p.get("slug"))
        icon = {"type":"emoji","emoji":emoji} if emoji else None
        cover = covers_map.get(p.get("slug"))
        children = blockify(p["blocks"])
        print(f"Creating subpage: {p['title']} (parent={parent_slug}) ...", end="", flush=True)
        try:
            url = f"{NOTION_API}/pages"
            payload = {
                "parent": {"type": "page_id", "page_id": parent_id},
                "properties": {"title": {"title": [{"type": "text", "text": {"content": p['title']}}]}},
                "children": children
            }
            if icon: payload["icon"] = icon
            if cover: payload["cover"] = {"type":"external","external":{"url": cover}}
            r = requests.post(url, headers=notion_headers(token), data=json.dumps(payload))
            r.raise_for_status()
            pid = r.json().get("id")
            slug_to_pageid[p.get("slug")] = pid
            print(" ok")
        except Exception as e:
            print(f"\n  ERROR creating subpage {p['title']}: {e}")

    print("\nDeploy complete. Created:")
    print(f"  Databases: {len(name_to_dbid)}")
    print(f"  Pages: {len(slug_to_pageid)}")

if __name__ == "__main__":
    main()
