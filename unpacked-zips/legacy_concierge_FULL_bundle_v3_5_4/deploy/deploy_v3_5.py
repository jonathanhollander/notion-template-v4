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
ICON_BASE_URL = os.getenv("ICON_BASE_URL","").rstrip("/")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}" if NOTION_TOKEN else "",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}

STATE_PATH = Path(".state.json")
HELPER_TEXT = "⚠️ Setup Helper:"

def load_state():
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except:
            return {}
    return {}

def save_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")

def req(method, url, **kwargs):
    delay = 0.5
    for attempt in range(1,7):
        resp = requests.request(method, url, headers=HEADERS, **kwargs)
        if resp.status_code in (200,201):
            return resp
        if resp.status_code in (429,500,502,503,504):
            print(f"[retry {attempt}] {resp.status_code} → waiting {delay:.1f}s")
            time.sleep(delay)
            delay = min(delay*2, 8.0)
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

def resolve_icon(icon_path_or_emoji, role=None):
    if ICON_BASE_URL and icon_path_or_emoji and icon_path_or_emoji.startswith("assets/"):
        return {"type":"external","external":{"url": ICON_BASE_URL + "/" + icon_path_or_emoji}}
    emoji_map = {"executor":"◆","family":"◆","owner":"◆","pending":"◇"}
    emoji = emoji_map.get(role or "owner","◆")
    return {"type":"emoji","emoji": emoji}

def helper_callout(text):
    return {"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"🧩"},
            "rich_text":[{"type":"text","text":{"content":f"{HELPER_TEXT} {text}"}}]}}}

def page_children_blocks(description=None, disclaimer=None, role=None, helper_text=None):
    blocks = []
    if role == "executor":
        blocks.append({"object":"block","type":"heading_3","heading_3":{"rich_text":[{"type":"text","text":{"content":"Steps Overview"}}]}})
    elif role == "family":
        blocks.append({"object":"block","type":"heading_3","heading_3":{"rich_text":[{"type":"text","text":{"content":"About this page"}}]}})
    else:
        blocks.append({"object":"block","type":"heading_3","heading_3":{"rich_text":[{"type":"text","text":{"content":"Overview"}}]}})
    blocks.append({"object":"block","type":"divider","divider":{}})
    if description:
        blocks.append({"object":"block","type":"paragraph",
                       "paragraph":{"rich_text":[{"type":"text","text":{"content":description}}]}})
    if disclaimer:
        blocks.append({"object":"block","type":"callout",
                       "callout":{"icon":{"type":"emoji","emoji":"ℹ️"},
                                  "rich_text":[{"type":"text","text":{"content":disclaimer}}]}})
    if helper_text:
        blocks.append(helper_callout(helper_text + " Delete this note once complete."))
    return blocks

def create_page_payload(title, parent_id, icon=None, cover=None, description=None, disclaimer=None, role=None, helper_text=None):
    payload = {"parent":{"type":"page_id","page_id":parent_id},
               "properties":{"title":{"title":[{"text":{"content":title}}]}}}
    payload["icon"] = resolve_icon(icon, role=role)
    if cover:
        payload["cover"] = {"type":"external","external":{"url":cover}}
    children = page_children_blocks(description, disclaimer, role, helper_text)
    if children:
        payload["children"] = children
    return payload

def children_have_helper(page_id):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
    resp = req("GET", url)
    if resp.status_code != 200:
        return False
    data = resp.json()
    for block in data.get("results", []):
        rich = None
        if "paragraph" in block:
            rich = block["paragraph"].get("rich_text")
        elif "callout" in block:
            rich = block["callout"].get("rich_text")
        elif "heading_3" in block:
            rich = block["heading_3"].get("rich_text")
        if rich:
            text = "".join([t.get("text",{}).get("content","") for t in rich if t.get("type")=="text"])
            if HELPER_TEXT in text:
                return True
    return False

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="split_yaml", help="YAML directory")
    ap.add_argument("--dry-run", action="store_true", help="Preview only (no changes)")
    ap.add_argument("--deploy", action="store_true", help="Create content")
    ap.add_argument("--update", action="store_true", help="Patch existing")
    ap.add_argument("--reset-helpers", action="store_true", help="Forget which pages had helpers cleared (re-enable adding them)")
    args = ap.parse_args()

    if not NOTION_TOKEN:
        print("ERROR: NOTION_TOKEN missing. Set it in environment or .env")
        sys.exit(1)

    merged = load_split_yaml(args.dir)
    state = load_state()

    if args.reset_helpers:
        state["helpers_cleared"] = {}
        save_state(state)
        print("Helper cleared-state reset.")

    helpers_cleared = state.get("helpers_cleared", {})  # {page_id: True}

    parent = os.getenv("NOTION_PARENT_PAGEID") or (Path(".parent_cache").read_text(encoding="utf-8").strip() if Path(".parent_cache").exists() else None)
    if not parent:
        parent = input("Enter Notion parent page ID: ").strip()
        Path(".parent_cache").write_text(parent, encoding="utf-8")

    # Change plan
    def compute_change_plan():
        plan = {"pages":{"create":[], "update":[]},
                "databases":{"create":[], "update":[]},
                "letters":{"create":[], "update":[]},
                "notes":[]}
        existing_pages = state.get("pages", {})
        for p in merged.get("pages", []):
            title = p.get("title")
            if title in existing_pages:
                plan["pages"]["update"].append({"title":title, "fields":["icon/cover/desc/disclaimer","(helper may refresh)"], "parent_hint":p.get("parent")})
            else:
                plan["pages"]["create"].append({"title":title, "role":p.get("role"), "parent_hint":p.get("parent")})
        existing_dbs = state.get("databases", {})
        for db_name in (merged.get("db",{}).get("schemas") or {}).keys():
            if db_name in existing_dbs:
                plan["databases"]["update"].append({"name":db_name, "fields":["seed_rows (append only)","DB Setup page refresh"]})
            else:
                plan["databases"]["create"].append({"name":db_name})
        existing_letters = state.get("letters_pages", {})
        for L in merged.get("letters", []):
            title = L.get("Title")
            if title in existing_letters:
                plan["letters"]["update"].append({"title":title, "fields":["re-sync + index"]})
            else:
                plan["letters"]["create"].append({"title":title, "audience":L.get("Audience"), "category":L.get("Category")})
        if not ICON_BASE_URL:
            plan["notes"].append("Icons will use emoji fallback until ICON_BASE_URL is set to a public host for /assets/icons/*")
        plan["notes"].append("True re-parenting via API is not supported; child pages will include a Setup Helper to move manually.")
        plan["notes"].append("Notion API does not create DB views/templates; a DB Setup helper page is created with instructions.")
        return plan

    def print_change_plan(plan):
        print("\nCHANGE PLAN")
        print("Pages:")
        for item in plan["pages"]["create"]:
            print(f"  CREATE  {item['title']}  (role={item.get('role')})  parent_hint={item.get('parent_hint')}")
        for item in plan["pages"]["update"]:
            print(f"  UPDATE  {item['title']}  fields={item['fields']}  parent_hint={item.get('parent_hint')}")
        print("Databases:")
        for item in plan["databases"]["create"]:
            print(f"  CREATE  {item['name']}")
        for item in plan["databases"]["update"]:
            print(f"  UPDATE  {item['name']}  (append seeds + refresh helper)")
        print("Letters:")
        for item in plan["letters"]["create"]:
            print(f"  CREATE  {item['title']}  ({item.get('audience')}/{item.get('category')})")
        for item in plan["letters"]["update"]:
            print(f"  UPDATE  {item['title']}  (re-sync + index)")
        if plan["notes"]:
            print("Notes:")
            for n in plan["notes"]:
                print(f"  - {n}")

    plan = compute_change_plan()
    print_change_plan(plan)

    if args.dry_run and not (args.deploy or args.update):
        print("\nDry-run complete. Re-run with --deploy (create) and/or --update (patch).")
        return
    confirm = input("\nProceed with these changes? (y/N): ").lower().strip()
    if confirm != "y":
        print("Canceled. No changes made.")
        return

    globals_cfg = merged.get("globals", {})

    # Helper infra: Letters, Diagnostics, Acceptance, Console, Rollout
    def ensure_page(title, description=None):
        payload = create_page_payload(title, parent, role="owner", description=description)
        r = req("POST","https://api.notion.com/v1/pages", data=json.dumps(payload))
        if r.status_code >= 300:
            print(f"ERROR creating {title}: {r.status_code} {r.text}"); sys.exit(1)
        return r.json()["id"]

    state.setdefault("letters_parent_id", None)
    if not state["letters_parent_id"]:
        state["letters_parent_id"] = ensure_page("Letters", "Sample letters to help you begin. Adjust details for your situation.")
        print("Created Letters parent page.")

    # Diagnostics DB
    if not state.get("diagnostics_db_id"):
        payload = {"parent":{"type":"page_id","page_id":parent},"title":[{"type":"text","text":{"content":"Diagnostics"}}],
                   "properties":{"Page":{"title":{}},"Severity":{"select":{"options":[{"name":"red"},{"name":"yellow"},{"name":"green"}]}},
                                 "Message":{"rich_text":{}},"Resolved":{"select":{"options":[{"name":"No"},{"name":"Yes"}]}}}}
        r = req("POST","https://api.notion.com/v1/databases", data=json.dumps(payload))
        if r.status_code >= 300: print("ERROR creating Diagnostics DB"); sys.exit(1)
        state["diagnostics_db_id"] = r.json()["id"]; print("Created Diagnostics DB.")

    # Acceptance DB
    if not state.get("acceptance_db_id"):
        payload = {"parent":{"type":"page_id","page_id":parent},"title":[{"type":"text","text":{"content":"Acceptance"}}],
                   "properties":{"Page":{"title":{}},"Role":{"select":{"options":[{"name":"executor"},{"name":"family"},{"name":"owner"}]}},
                                 "Check":{"rich_text":{}},"Status":{"select":{"options":[{"name":"Pending"},{"name":"Done"}]}}}}
        r = req("POST","https://api.notion.com/v1/databases", data=json.dumps(payload))
        if r.status_code >= 300: print("ERROR creating Acceptance DB"); sys.exit(1)
        state["acceptance_db_id"] = r.json()["id"]; print("Created Acceptance DB.")

    # Builder’s Console
    if not state.get("builders_console_id"):
        payload = create_page_payload("Builder’s Console", parent, role="owner",
                                      description="For setup only. Delete this branch before sharing.")
        rc = req("POST","https://api.notion.com/v1/pages", data=json.dumps(payload))
        if rc.status_code >= 300: print("ERROR creating Builder’s Console"); sys.exit(1)
        state["builders_console_id"] = rc.json()["id"]; print("Created Builder’s Console.")
        console_children = [
            {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"Diagnostics Overview"}}]}},
            {"object":"block","type":"link_to_page","link_to_page":{"type":"database_id","database_id":state["diagnostics_db_id"]}},
            {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"Acceptance by Section"}}]}},
            {"object":"block","type":"link_to_page","link_to_page":{"type":"database_id","database_id":state["acceptance_db_id"]}},
        ]
        req("PATCH", f"https://api.notion.com/v1/blocks/{state['builders_console_id']}/children", data=json.dumps({"children":console_children}))

    save_state(state)

    # Create/update pages with helper NEVER re-added once cleared
    page_ids = state.get("pages", {})
    for p in merged.get("pages", []):
        title = p["title"]; role = p.get("role")
        desired_helper = None
        if p.get("parent"):
            desired_helper = f"Move this page under “{p['parent']}” manually (API cannot re-parent)."

        if title in page_ids:
            pid = page_ids[title]
            # Determine helper add-or-not
            has_helper_now = children_have_helper(pid)
            cleared = bool(helpers_cleared.get(pid))
            helper_to_add = (desired_helper and (not has_helper_now) and (not cleared))
            # Patch icon/cover
            patch = {}
            if p.get("icon"): patch["icon"] = resolve_icon(p.get("icon"), role=role)
            if p.get("cover"): patch["cover"] = {"type":"external","external":{"url":p.get("cover")}}
            if patch:
                req("PATCH", f"https://api.notion.com/v1/pages/{pid}", data=json.dumps(patch))
            # Append children blocks (heading/divider/desc/disclaimer) and optionally helper
            children = page_children_blocks(p.get("description"), p.get("disclaimer"), role, helper_text=(desired_helper if helper_to_add else None))
            if children:
                req("PATCH", f"https://api.notion.com/v1/blocks/{pid}/children", data=json.dumps({"children":children}))
            print(f"[UPDATE] {title}  helper_added={'yes' if helper_to_add else 'no'}")
        else:
            # Create
            payload = create_page_payload(title, parent, icon=p.get("icon"), cover=p.get("cover"),
                                          description=p.get("description"), disclaimer=p.get("disclaimer"),
                                          role=role, helper_text=desired_helper)  # first time: add helper if needed
            r = req("POST","https://api.notion.com/v1/pages", data=json.dumps(payload))
            if r.status_code >= 300:
                print(f"[CREATE] ERROR {title}: {r.status_code} {r.text}")
                continue
            pid = r.json()["id"]; page_ids[title]=pid
            print(f"[CREATE] Page: {title}  helper_added={'yes' if desired_helper else 'no'}")

    state["pages"] = page_ids
    save_state(state)

    # Create/update DBs and setup pages (same logic as 3.5.3)
    db_ids = state.get("databases", {})
    db_setup_pages = state.get("db_setup_pages", {})
    schemas = merged.get("db",{}).get("schemas") or {}
    for db_name, spec in schemas.items():
        props = spec.get("properties") or {}
        options = spec.get("options") or {}
        if db_name in db_ids:
            database_id = db_ids[db_name]
        else:
            # create DB
            payload = {"parent":{"type":"page_id","page_id":parent},"title":[{"type":"text","text":{"content":db_name}}],"properties":{}}
            def prop_schema(props, options):
                out={}
                for n,k in props.items():
                    if k=="title": out[n]={"title":{}}
                    elif k=="select": out[n]={"select":{"options":[{"name":v} for v in (options.get(n,[]) if options else [])]}}
                    elif k=="multi_select": out[n]={"multi_select":{"options":[{"name":v} for v in (options.get(n,[]) if options else [])]}}
                    elif k=="rich_text": out[n]={"rich_text":{}}
                    elif k=="date": out[n]={"date":{}}
                    elif k=="url": out[n]={"url":{}}
                    elif k=="phone_number": out[n]={"phone_number":{}}
                    elif k=="number": out[n]={"number":{"format":"number"}}
                    else: out[n]={"rich_text":{}}
                return out
            payload["properties"]=prop_schema(props, options)
            r = req("POST","https://api.notion.com/v1/databases", data=json.dumps(payload))
            if r.status_code >= 300:
                print(f"[DB] ERROR {db_name}: {r.status_code} {r.text}")
                continue
            database_id = r.json()["id"]; db_ids[db_name]=database_id; print(f"[DB] Created: {db_name}")
        # seed rows
        kinds = {n:k for n,k in props.items()}
        for row in spec.get("seed_rows") or []:
            def prop_values(row, kinds):
                vals={}
                for n,v in row.items():
                    k=kinds.get(n,"rich_text")
                    if k=="title": vals[n]={"title":[{"type":"text","text":{"content":str(v)}}]}
                    elif k=="select": vals[n]={"select":{"name":str(v)}}
                    elif k=="multi_select": vals[n]={"multi_select":[{"name":str(x)} for x in (v if isinstance(v,list) else [v]) ]}
                    elif k=="rich_text": vals[n]={"rich_text":[{"type":"text","text":{"content":str(v)}}]}
                    elif k=="date": vals[n]={"date":{"start":str(v)}}
                    elif k=="url": vals[n]={"url":str(v)}
                    elif k=="phone_number": vals[n]={"phone_number":str(v)}
                    elif k=="number":
                        try: vals[n]={"number": float(v)}
                        except: vals[n]={"number": None}
                return vals
            pr = req("POST","https://api.notion.com/v1/pages", data=json.dumps({"parent":{"type":"database_id","database_id":database_id},
                                                                               "properties":prop_values(row, kinds)}))
            if pr.status_code >= 300:
                print(f"[DB] Seed error for {db_name}: {pr.status_code}")
        # DB setup helper page
        setup_title = f"DB Setup: {db_name}"
        if setup_title in db_setup_pages:
            setup_id = db_setup_pages[setup_title]
        else:
            helper = f"Add views (Table, Board by Status) and any page templates for “{db_name}” manually in Notion. Delete this note once complete."
            payload = create_page_payload(setup_title, parent, role="owner", helper_text=helper)
            r = req("POST","https://api.notion.com/v1/pages", data=json.dumps(payload))
            if r.status_code >= 300:
                print(f"[DB] Setup page error for {db_name}")
            else:
                setup_id = r.json()["id"]; db_setup_pages[setup_title]=setup_id
                req("PATCH", f"https://api.notion.com/v1/blocks/{setup_id}/children", data=json.dumps({"children":[{"object":"block","type":"link_to_page","link_to_page":{"type":"database_id","database_id":database_id}}]}))
                print(f"[DB] Setup helper page created for {db_name}")

    state["databases"]=db_ids; state["db_setup_pages"]=db_setup_pages
    save_state(state)

    # Letters index + pages (same as 3.5.3)
    if not state.get("letters_index_db_id"):
        payload = {"parent":{"type":"page_id","page_id":parent},
                   "title":[{"type":"text","text":{"content":"Letters Index"}}],
                   "properties":{"Title":{"title":{}},"Audience":{"select":{"options":[{"name":"Executor"},{"name":"Family"}]}},
                                 "Category":{"select":{"options":[{"name":"Financial"},{"name":"Insurance"},{"name":"Medical"},{"name":"Legal"},{"name":"Employment"},{"name":"Services"},{"name":"Community"},{"name":"Housing"},{"name":"Personal"}]}},
                                 "URL":{"url":{}}}}
        r = req("POST","https://api.notion.com/v1/databases", data=json.dumps(payload))
        if r.status_code >= 300: print("ERROR creating Letters Index DB"); sys.exit(1)
        state["letters_index_db_id"]=r.json()["id"]; print("Created Letters Index DB.")
        save_state(state)

    letters_state = state.get("letters_pages", {})
    for L in merged.get("letters", []):
        title = L.get("Title"); disclaimer=L.get("Disclaimer","Sample letter — adjust for your situation."); body=L.get("Body","")
        if title in letters_state and not args.update:
            pid = letters_state[title]["page_id"]; page_url = letters_state[title]["url"]
            print(f"[LETTER] Exists: {title}")
        else:
            children = [
                {"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"ℹ️"},"rich_text":[{"type":"text","text":{"content":disclaimer}}]}},
                {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":body}}]}},
                {"object":"block","type":"link_to_page","link_to_page":{"type":"database_id","database_id":state["letters_index_db_id"]}}
            ]
            payload = {"parent":{"type":"page_id","page_id":state["letters_parent_id"]},
                       "properties":{"title":{"title":[{"text":{"content":title}}]}},
                       "children": children}
            r = req("POST","https://api.notion.com/v1/pages", data=json.dumps(payload))
            if r.status_code >= 300:
                print(f"[LETTER] ERROR {title}: {r.status_code} {r.text}"); continue
            res = r.json(); pid=res["id"]; page_url=res.get("url","")
            letters_state[title]={"page_id":pid,"url":page_url,"audience":L.get("Audience"),"category":L.get("Category")}
            print(f"[LETTER] Created: {title}")
        # index row append
        props={"Title":{"title":[{"type":"text","text":{"content":title}}]},"Audience":{"select":{"name":L.get("Audience")}},
               "Category":{"select":{"name":L.get("Category")}},"URL":{"url": letters_state[title]["url"]}}
        req("POST","https://api.notion.com/v1/pages", data=json.dumps({"parent":{"type":"database_id","database_id":state["letters_index_db_id"]},"properties":props}))
    state["letters_pages"]=letters_state
    save_state(state)

    # Diagnostics from YAML
    def diagnostics_from_yaml(merged):
        rows=[]
        for p in merged.get("pages", []):
            role=p.get("role"); title=p.get("title")
            if role=="executor" and not p.get("disclaimer"):
                rows.append(("red", title, "Executor page missing disclaimer"))
            if not p.get("cover"): rows.append(("yellow", title, "Cover missing"))
            if not p.get("icon"): rows.append(("yellow", title, "Icon missing"))
        for name, spec in (merged.get("db",{}).get("schemas") or {}).items():
            if not (spec.get("seed_rows") or []):
                rows.append(("yellow", f"(DB) {name}", "Database has no seeded rows"))
        return rows
    for sev, page, msg in diagnostics_from_yaml(merged):
        props={"Page":{"title":[{"type":"text","text":{"content":page}}]},"Severity":{"select":{"name":sev}},
               "Message":{"rich_text":[{"type":"text","text":{"content":msg}}]},"Resolved":{"select":{"name":"No"}}}
        req("POST","https://api.notion.com/v1/pages", data=json.dumps({"parent":{"type":"database_id","database_id":state["diagnostics_db_id"]},"properties":props}))

    # Rollout Summary: link to all pages still containing helper notes;
    # ALSO mark helpers_cleared for pages where helper is no longer present.
    if not state.get("rollout_page_id"):
        payload = create_page_payload("Rollout Summary", parent, role="owner",
                                      description="Links to every page that still has a Setup Helper note.")
        rr = req("POST","https://api.notion.com/v1/pages", data=json.dumps(payload))
        if rr.status_code >= 300: print("ERROR creating Rollout Summary"); sys.exit(1)
        state["rollout_page_id"] = rr.json()["id"]
        save_state(state)

    helper_links = []
    helpers_cleared = state.get("helpers_cleared", {})
    # page helpers
    for p in merged.get("pages", []):
        if p.get("parent"):
            pid = state["pages"].get(p["title"])
            if not pid: continue
            if children_have_helper(pid):
                helper_links.append(("Move under “%s”" % p["parent"], pid, p["title"]))
            else:
                helpers_cleared[pid] = True  # remember that helper was cleared, never re-add
    # db setup helpers
    for title, pid in state.get("db_setup_pages", {}).items():
        if children_have_helper(pid):
            helper_links.append(("DB views/templates", pid, title))
        else:
            helpers_cleared[pid] = True  # mark cleared

    state["helpers_cleared"] = helpers_cleared
    save_state(state)

    # Replace Rollout content
    children = []
    if not ICON_BASE_URL:
        children.append(helper_callout("Host diamond icons and set ICON_BASE_URL in .env. Delete this reminder once icons display correctly."))
    if helper_links:
        children.append({"object":"block","type":"heading_3","heading_3":{"rich_text":[{"type":"text","text":{"content":"Pages needing manual action"}}]}})
        for reason, pid, label in helper_links:
            children.append({"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":f"• {label} — {reason}"}}]}})
            children.append({"object":"block","type":"link_to_page","link_to_page":{"type":"page_id","page_id":pid}})
    else:
        children.append({"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"No Setup Helpers remain. You’re ready to share."}}]}})
    req("PATCH", f"https://api.notion.com/v1/blocks/{state['rollout_page_id']}/children", data=json.dumps({"children":children}))

    print("\nDone. Helper notes, once deleted, will NOT be re-added on future runs. Use --reset-helpers to re-enable if needed.")

if __name__ == "__main__":
    main()
