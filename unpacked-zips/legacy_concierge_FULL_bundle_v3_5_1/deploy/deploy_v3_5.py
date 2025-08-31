#!/usr/bin/env python3
import os, sys, json, glob, time, math
from pathlib import Path
from dotenv import load_dotenv
import yaml
import requests

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_VERSION = os.getenv("NOTION_VERSION","2022-06-28")
DEFAULT_PARENT = os.getenv("NOTION_PARENT_PAGEID")
ICON_BASE_URL = os.getenv("ICON_BASE_URL","").rstrip("/")  # optional CDN base for icons

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}" if NOTION_TOKEN else "",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}

STATE_PATH = Path(".state.json")

def load_state():
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except:
            return {}
    return {}

def save_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")

def backoff_request(method, url, **kwargs):
    # Simple retry/backoff for 429/5xx
    delay = 0.5
    for attempt in range(6):
        resp = requests.request(method, url, headers=HEADERS, **kwargs)
        if resp.status_code < 429 or resp.status_code in (200, 201):
            return resp
        if resp.status_code in (429, 500, 502, 503, 504):
            time.sleep(delay)
            delay = min(delay * 2, 8.0)
            continue
        return resp
    return resp

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

def resolve_icon(icon_path_or_emoji, role=None, globals_cfg=None):
    # If ICON_BASE_URL is set and icon looks like a relative asset, convert to public URL
    if ICON_BASE_URL and icon_path_or_emoji and icon_path_or_emoji.startswith("assets/"):
        return {"type":"external","external":{"url": ICON_BASE_URL + "/" + icon_path_or_emoji}}
    # If no CDN, use emoji fallback by role
    emoji_map = {"executor":"◆","family":"◆","owner":"◆","pending":"◇"}
    emoji = emoji_map.get(role or "owner","◆")
    return {"type":"emoji","emoji": emoji}

def create_page_payload(title, parent_id, icon=None, cover=None, description=None, disclaimer=None, role=None, globals_cfg=None):
    payload = {"parent":{"type":"page_id","page_id":parent_id},
               "properties":{"title":{"title":[{"text":{"content":title}}]}}}
    # icon
    if icon:
        payload["icon"] = resolve_icon(icon, role=role, globals_cfg=globals_cfg)
    else:
        payload["icon"] = resolve_icon(None, role=role, globals_cfg=globals_cfg)
    # cover
    if cover:
        payload["cover"] = {"type":"external","external":{"url":cover}}
    # children blocks
    children = []
    if description:
        children.append({"object":"block","type":"paragraph",
                         "paragraph":{"rich_text":[{"type":"text","text":{"content":description}}]}})
    if disclaimer:
        children.append({"object":"block","type":"callout",
                         "callout":{"icon":{"type":"emoji","emoji":"ℹ️"},
                                    "rich_text":[{"type":"text","text":{"content":disclaimer}}]}})
    if children:
        payload["children"] = children
    return payload

# ----- Database support -----
SUPPORTED_KINDS = {"title","select","multi_select","rich_text","date","url","phone_number","number"}

def prop_schema_from_yaml(props, options=None):
    out = {}
    for name, kind in props.items():
        if kind not in SUPPORTED_KINDS:
            kind = "rich_text"
        if kind == "title":
            out[name] = {"title": {}}
        elif kind == "select":
            out[name] = {"select": {"options": []}}
        elif kind == "multi_select":
            out[name] = {"multi_select": {"options": []}}
        elif kind == "rich_text":
            out[name] = {"rich_text": {}}
        elif kind == "date":
            out[name] = {"date": {}}
        elif kind == "url":
            out[name] = {"url": {}}
        elif kind == "phone_number":
            out[name] = {"phone_number": {}}
        elif kind == "number":
            out[name] = {"number": {"format":"number"}}
    # Apply select options
    if options:
        for prop_name, values in options.items():
            if prop_name in out and "select" in out[prop_name]:
                out[prop_name]["select"]["options"] = [{"name": v} for v in values]
            if prop_name in out and "multi_select" in out[prop_name]:
                out[prop_name]["multi_select"]["options"] = [{"name": v} for v in values]
    return out

def prop_values_from_row(row, schema_kinds):
    vals = {}
    for name, value in row.items():
        kind = schema_kinds.get(name, "rich_text")
        if kind == "title":
            vals[name] = {"title":[{"type":"text","text":{"content":str(value)}}]}
        elif kind == "select":
            vals[name] = {"select":{"name":str(value)}}
        elif kind == "multi_select":
            if isinstance(value, list):
                vals[name] = {"multi_select":[{"name":str(v)} for v in value]}
            else:
                vals[name] = {"multi_select":[{"name":str(value)}]}
        elif kind == "rich_text":
            vals[name] = {"rich_text":[{"type":"text","text":{"content":str(value)}}]}
        elif kind == "date":
            vals[name] = {"date":{"start":str(value)}}
        elif kind == "url":
            vals[name] = {"url": str(value)}
        elif kind == "phone_number":
            vals[name] = {"phone_number": str(value)}
        elif kind == "number":
            try:
                vals[name] = {"number": float(value)}
            except:
                vals[name] = {"number": None}
    return vals

def create_db_payload(title, parent_id, properties, options=None):
    return {
        "parent":{"type":"page_id","page_id":parent_id},
        "title":[{"type":"text","text":{"content":title}}],
        "properties": prop_schema_from_yaml(properties, options or {})
    }

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
    state = load_state()

    print(f"Loaded: {len(pages)} pages | {len(letters)} letters | {len(db.get('schemas',{}))} databases")

    parent = os.getenv("NOTION_PARENT_PAGEID") or (Path(".parent_cache").read_text(encoding="utf-8").strip() if Path(".parent_cache").exists() else None)
    if not parent:
        parent = input("Enter Notion parent page ID: ").strip()
        Path(".parent_cache").write_text(parent, encoding="utf-8")

    # PLAN
    print("\nPLAN:")
    for p in pages:
        role = p.get("role","owner")
        mark = {"executor":"[SAGE ◆]","family":"[PEACH ◆]","owner":"[BEIGE ◆]"}.get(role,"[◆]")
        parent_hint = f" → parent: {p.get('parent')}" if p.get("parent") else ""
        print(f"  PAGE  {mark} {p.get('title')}{parent_hint}  (disclaimer={'yes' if p.get('disclaimer') else 'no'})")
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

    # --- Create/ensure top-level helper pages ---
    # Letters parent
    letters_parent_id = state.get("letters_parent_id")
    if not letters_parent_id:
        payload_letters_parent = create_page_payload("Letters", parent,
            icon=globals_cfg.get("icons",{}).get("owner"),
            cover=globals_cfg.get("covers",{}).get("owner"),
            description="Sample letters to help you begin. Adjust details for your situation.",
            role="owner", globals_cfg=globals_cfg)
        resp = backoff_request("POST","https://api.notion.com/v1/pages", data=json.dumps(payload_letters_parent))
        if resp.status_code < 300:
            letters_parent_id = resp.json()["id"]
            state["letters_parent_id"] = letters_parent_id
            print(f"Created Letters parent page: {letters_parent_id}")
        else:
            print(f"ERROR creating Letters parent page: {resp.status_code} {resp.text}")
            sys.exit(1)

    # Diagnostics DB
    diagnostics_db_id = state.get("diagnostics_db_id")
    if not diagnostics_db_id:
        diag_schema = {
            "Page": "title",
            "Severity": "select",
            "Message": "rich_text",
            "Resolved": "select"
        }
        diag_options = {"Severity":["red","yellow","green"], "Resolved":["No","Yes"]}
        payload = create_db_payload("Diagnostics", parent, diag_schema, diag_options)
        r = backoff_request("POST","https://api.notion.com/v1/databases", data=json.dumps(payload))
        if r.status_code < 300:
            diagnostics_db_id = r.json()["id"]
            state["diagnostics_db_id"] = diagnostics_db_id
            print(f"Created Diagnostics DB: {diagnostics_db_id}")
        else:
            print(f"ERROR creating Diagnostics DB: {r.status_code} {r.text}")
            sys.exit(1)

    # Acceptance DB
    acceptance_db_id = state.get("acceptance_db_id")
    if not acceptance_db_id:
        acc_schema = {
            "Page": "title",
            "Role": "select",
            "Check": "rich_text",
            "Status": "select"
        }
        acc_options = {"Role":["executor","family","owner"], "Status":["Pending","Done"]}
        payload = create_db_payload("Acceptance", parent, acc_schema, acc_options)
        r = backoff_request("POST","https://api.notion.com/v1/databases", data=json.dumps(payload))
        if r.status_code < 300:
            acceptance_db_id = r.json()["id"]
            state["acceptance_db_id"] = acceptance_db_id
            print(f"Created Acceptance DB: {acceptance_db_id}")
        else:
            print(f"ERROR creating Acceptance DB: {r.status_code} {r.text}")
            sys.exit(1)

    # Builder's Console page
    console_page_id = state.get("builders_console_id")
    if not console_page_id:
        payload_console = create_page_payload("Builder’s Console", parent,
            icon=globals_cfg.get("icons",{}).get("owner"),
            cover=globals_cfg.get("covers",{}).get("owner"),
            description="For setup only. Delete this branch before sharing.",
            role="owner", globals_cfg=globals_cfg)
        rc = backoff_request("POST","https://api.notion.com/v1/pages", data=json.dumps(payload_console))
        if rc.status_code < 300:
            console_page_id = rc.json()["id"]
            state["builders_console_id"] = console_page_id
            print(f"Created Builder’s Console: {console_page_id}")
        else:
            print(f"ERROR creating Builder’s Console: {rc.status_code} {rc.text}")
            sys.exit(1)

    # Add links to Diagnostics & Acceptance DBs inside Console
    # Use "link_to_page" blocks pointing to those DBs
    console_children = [
        {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"Diagnostics Overview"}}]}},
        {"object":"block","type":"link_to_page","link_to_page":{"type":"database_id","database_id":diagnostics_db_id}},
        {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"Acceptance by Section"}}]}},
        {"object":"block","type":"link_to_page","link_to_page":{"type":"database_id","database_id":acceptance_db_id}},
        {"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"🧭"},
            "rich_text":[{"type":"text","text":{"content":"Read once as if you were the executor. If it feels clear and steady, you’re ready to share."}}]}},
    ]
    backoff_request("PATCH", f"https://api.notion.com/v1/blocks/{console_page_id}/children", data=json.dumps({"children":console_children}))

    save_state(state)

    # --- Create pages with nesting ---
    # First pass: create all pages and remember IDs
    page_ids = state.get("pages", {})
    title_to_id = {t: pid for t, pid in page_ids.items()}
    for i,p in enumerate(pages, start=1):
        title = p["title"]
        if title in title_to_id:
            print(f"[PAGE {i}] Exists: {title}")
            continue
        payload = create_page_payload(title, parent, icon=p.get("icon"), cover=p.get("cover"),
                                      description=p.get("description"), disclaimer=p.get("disclaimer"),
                                      role=p.get("role"), globals_cfg=globals_cfg)
        r = backoff_request("POST","https://api.notion.com/v1/pages", data=json.dumps(payload))
        if r.status_code >= 300:
            print(f"[PAGE {i}] ERROR {title}: {r.status_code} {r.text}")
        else:
            pid = r.json()["id"]
            page_ids[title] = pid
            title_to_id[title] = pid
            print(f"[PAGE {i}] Created: {title}")
        time.sleep(0.2)
    state["pages"] = page_ids
    save_state(state)

    # Second pass: nest children under specified parent titles
    for p in pages:
        par_title = p.get("parent")
        if not par_title:
            continue
        child_id = title_to_id.get(p["title"])
        parent_id = title_to_id.get(par_title, parent)
        if not child_id:
            continue
        # Move page by updating parent (Notion API doesn't support "move" directly via parent change in pages API).
        # Workaround: add a breadcrumb link in the parent and log action. True re-parent needs manual move in UI.
        # We'll add a link_to_page in the intended parent for now.
        link_block = {"children":[{"object":"block","type":"link_to_page","link_to_page":{"type":"page_id","page_id":child_id}}]}
        backoff_request("PATCH", f"https://api.notion.com/v1/blocks/{parent_id}/children", data=json.dumps(link_block))

    # --- Create databases (+ seeds) from YAML ---
    schemas = db.get("schemas") or {}
    db_ids = state.get("databases", {})
    for i,(db_name, spec) in enumerate(schemas.items(), start=1):
        if db_name in db_ids:
            print(f"[DB {i}] Exists: {db_name}")
            database_id = db_ids[db_name]
        else:
            properties = spec.get("properties") or {}
            options = spec.get("options") or {}
            db_payload = create_db_payload(db_name, parent, properties, options)
            r = backoff_request("POST","https://api.notion.com/v1/databases", data=json.dumps(db_payload))
            if r.status_code >= 300:
                print(f"[DB {i}] ERROR {db_name}: {r.status_code} {r.text}")
                continue
            database_id = r.json()["id"]
            db_ids[db_name] = database_id
            print(f"[DB {i}] Created database: {db_name} ({database_id})")

        # Seed rows
        seeds = spec.get("seed_rows") or []
        # Build schema kinds
        schema_kinds = {}
        for n,k in (spec.get("properties") or {}).items():
            schema_kinds[n] = k
        for j,row in enumerate(seeds, start=1):
            props = prop_values_from_row(row, schema_kinds)
            payload = {"parent":{"type":"database_id","database_id":database_id},"properties":props}
            pr = backoff_request("POST","https://api.notion.com/v1/pages", data=json.dumps(payload))
            if pr.status_code >= 300:
                print(f"   [SEED {j}] ERROR: {pr.status_code} {pr.text}")
            else:
                print(f"   [SEED {j}] Row added.")
            time.sleep(0.15)

    state["databases"] = db_ids
    save_state(state)

    # --- Create letter pages + Letters Index DB ---
    letters_index_db = state.get("letters_index_db_id")
    if not letters_index_db:
        idx_schema = {"Title":"title","Audience":"select","Category":"select","URL":"url"}
        idx_options = {"Audience":["Executor","Family"], "Category":["Financial","Insurance","Medical","Legal","Employment","Services","Community","Housing","Personal"]}
        payload = create_db_payload("Letters Index", parent, idx_schema, idx_options)
        r = backoff_request("POST","https://api.notion.com/v1/databases", data=json.dumps(payload))
        if r.status_code < 300:
            letters_index_db = r.json()["id"]
            state["letters_index_db_id"] = letters_index_db
            print(f"Created Letters Index DB: {letters_index_db}")
        else:
            print(f"ERROR creating Letters Index DB: {r.status_code} {r.text}")
            sys.exit(1)

    for i,L in enumerate(letters, start=1):
        title = L.get("Title")
        # idempotency: if a prior letter page exists (by title), skip
        letter_state = state.get("letters_pages", {})
        if title in letter_state:
            page_id = letter_state[title]["page_id"]
            page_url = letter_state[title]["url"]
            print(f"[LETTER {i}] Exists: {title}")
        else:
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
            r = backoff_request("POST","https://api.notion.com/v1/pages", data=json.dumps(payload))
            if r.status_code >= 300:
                print(f"[LETTER {i}] ERROR {title}: {r.status_code} {r.text}")
                continue
            res = r.json()
            page_id = res["id"]; page_url = res.get("url","")
            letter_state[title] = {"page_id":page_id, "url":page_url, "audience":L.get("Audience"), "category":L.get("Category")}
            state["letters_pages"] = letter_state
            save_state(state)
            print(f"[LETTER {i}] Created: {title}")

        # Upsert into Letters Index DB
        props = {
            "Title":{"title":[{"type":"text","text":{"content":title}}]},
            "Audience":{"select":{"name": L.get("Audience")}},
            "Category":{"select":{"name": L.get("Category")}},
            "URL":{"url": page_url}
        }
        pr = backoff_request("POST","https://api.notion.com/v1/pages", data=json.dumps({"parent":{"type":"database_id","database_id":letters_index_db}, "properties":props}))
        if pr.status_code >= 300:
            print(f"   [INDEX] ERROR for {title}: {pr.status_code} {pr.text}")
        else:
            print(f"   [INDEX] Row added for {title}")
        time.sleep(0.15)

    # --- Rollout Summary Page ---
    rollout_id = state.get("rollout_page_id")
    if not rollout_id:
        payload = create_page_payload("Rollout Summary", parent, role="owner", globals_cfg=globals_cfg,
                                      description="Live summary of what was created in this deployment.")
        rr = backoff_request("POST","https://api.notion.com/v1/pages", data=json.dumps(payload))
        if rr.status_code < 300:
            rollout_id = rr.json()["id"]
            state["rollout_page_id"] = rollout_id
            save_state(state)
            print(f"Created Rollout Summary page: {rollout_id}")

    # Add counts and links
    created_pages = [{"title":t, "id":pid} for t,pid in state.get("pages",{}).items()]
    db_items = [{"title":t, "id":did} for t,did in state.get("databases",{}).items()]
    letters_items = [{"title":t, "id":info["page_id"]} for t,info in state.get("letters_pages",{}).items()]

    summary_blocks = [
        {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"Created Counts"}}]}},
        {"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":f"Pages: {len(created_pages)}"}}]}},
        {"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":f"Databases: {len(db_items)}"}}]}},
        {"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":f"Letters: {len(letters_items)}"}}]}},
        {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"Quick Links"}}]}},
    ]
    # link to console, diagnostics, acceptance, letters parent
    quick_ids = [("Builder’s Console", console_page_id),
                 ("Diagnostics DB", diagnostics_db_id),
                 ("Acceptance DB", acceptance_db_id),
                 ("Letters", letters_parent_id)]
    for label, _id in quick_ids:
        summary_blocks.append({"object":"block","type":"link_to_page","link_to_page":{"type":"page_id","page_id":_id}})

    # Append summary
    backoff_request("PATCH", f"https://api.notion.com/v1/blocks/{rollout_id}/children", data=json.dumps({"children":summary_blocks}))

    print("\nAll content created and summarized.")
    print("Note: If you want custom diamond icons, host them and set ICON_BASE_URL in .env to a public base URL.")
    print("Re-run with --deploy to add more pages/dbs/letters; existing items are skipped via .state.json idempotency.")

if __name__ == "__main__":
    main()
