# deploy_v3_5.py — v3.6.0
# - Creates pages (with icons, covers, descriptions, disclaimers)
# - Adds collapsed "⚠️ Setup Helper" toggles where manual steps are needed
# - Creates unified "Setup & Acceptance" DB; seeds Acceptance rows from YAML; tracks Helpers
# - Creates content databases from YAML (schemas + seed_rows)
# - Creates Letters subpages from YAML
# - Creates "Release Notes" page from YAML content
# - Rollout Summary shows live totals from unified DB
#
# Usage:
#   python deploy/deploy_v3_5.py --dir split_yaml --dry-run
#   python deploy/deploy_v3_5.py --dir split_yaml --deploy
#   python deploy/deploy_v3_5.py --dir split_yaml --update

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


def load_copy_registry(dir_path):
    import yaml, os
    reg = {}
    fp = os.path.join(dir_path, "00_copy_registry.yaml")
    if os.path.exists(fp):
        d = yaml.safe_load(open(fp, "r", encoding="utf-8")) or {}
        reg = d.get("copy_registry") or {}
    return reg

def load_split_yaml(dir_path):
    import yaml, os
    merged = {"pages":[], "letters":[], "db":{"schemas":{}}, "acceptance":{"rows":[]}, "release_notes":""}
    for name in sorted(os.listdir(dir_path)):
        if not name.endswith(".yaml"): continue
        with open(os.path.join(dir_path, name), "r", encoding="utf-8") as f:
            y = yaml.safe_load(f) or {}
        for k,v in y.items():
            if k == "pages":
                merged["pages"].extend(v or [])
            elif k == "letters":
                merged["letters"].extend(v or [])
            elif k == "db":
                merged["db"]["schemas"].update((v or {}).get("schemas") or {})
            elif k == "acceptance":
                merged["acceptance"]["rows"].extend((v or {}).get("rows") or [])
            elif k == "release_notes":
                merged["release_notes"] = v or merged["release_notes"]
    return merged

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

def page_url(page_id):
    r = req("GET", f"https://api.notion.com/v1/pages/{page_id}")
    if r.status_code in (200,201):
        return r.json().get("url")
    return None

def children_have_helper(page_id):
    r = req("GET", f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100")
    if r.status_code not in (200,201): return False
    for b in r.json().get("results", []):
        if "toggle" in b:
            rich = b["toggle"].get("rich_text", [])
            txt = "".join([t.get("text",{}).get("content","") for t in rich if t.get("type")=="text"])
            if HELPER_TEXT in txt: return True
        if "paragraph" in b:
            rich = b["paragraph"].get("rich_text", [])
            txt = "".join([t.get("text",{}).get("content","") for t in rich if t.get("type")=="text"])
            if HELPER_TEXT in txt: return True
    return False

# Unified DB
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
    dbid = r.json()["id"]
    state["setup_db_id"] = dbid
    return dbid

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

# Page & DB creation
def resolve_icon(spec, filename=None):
    # Emoji fallback
    if isinstance(spec, str) and spec.startswith("emoji:"):
        return {"type":"emoji","emoji": spec.replace("emoji:","",1)}
    # Hosted filename takes precedence if provided and ICON_BASE_URL is set
    if filename and ICON_BASE_URL:
        return {"type":"external","external":{"url": ICON_BASE_URL.rstrip('/') + '/' + filename}}
    # Direct http url
    if isinstance(spec, str) and spec.startswith("http"):
        return {"type":"external","external":{"url": spec}}
    # If spec is a bare filename and host exists
    if isinstance(spec, str) and ICON_BASE_URL and (spec.endswith(".png") or spec.endswith(".svg") or spec.endswith(".jpg")):
        return {"type":"external","external":{"url": ICON_BASE_URL.rstrip('/') + '/' + spec}}
    # Fallback: None
    return None
    if isinstance(spec, str) and spec.startswith("emoji:"):
        return {"type":"emoji","emoji": spec.replace("emoji:","",1)}
    if isinstance(spec, str) and spec.startswith("http"):
        return {"type":"external","external":{"url": spec}}
    if isinstance(spec, str) and ICON_BASE_URL:
        return {"type":"external","external":{"url": ICON_BASE_URL.rstrip('/') + '/' + spec}}
    return None

def create_page(parent_id, title, icon=None, cover=None, description=None, disclaimer=None, helper=None, icon_file=None, cover_file=None):
    props = {"title":{"title":[{"type":"text","text":{"content":title}}]}}
    payload = {"parent":{"type":"page_id","page_id":parent_id},"properties":props}
    if icon_file:
        icon = resolve_icon(icon, filename=icon_file)
    if icon: payload["icon"]=icon
    if cover_file:
        c_url = resolve_cover(cover_file)
        if c_url:
            payload["cover"]={"type":"external","external":{"url": c_url}}
    elif cover:
        payload["cover"]={"type":"external","external":{"url": cover}}
    r = req("POST","https://api.notion.com/v1/pages", data=json.dumps(payload))
    if r.status_code not in (200,201):
        print("ERROR creating page", title, r.text); return None
    pid = r.json()["id"]
    blocks = []
    if description:
        blocks.append({"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":description}}]}})
    if disclaimer:
        blocks.append({"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"ℹ️"},"rich_text":[{"type":"text","text":{"content":disclaimer}}]}})
    if helper:
        if isinstance(helper, dict):
            if helper.get("type")=="nesting" and helper.get("parent"):
                blocks.append(build_nesting_helper(helper["parent"]))
            elif helper.get("type")=="db_setup" and helper.get("db"):
                blocks.append(build_db_setup_helper(helper["db"]))
            elif helper.get("type")=="icons":
                blocks.append(build_icon_hosting_helper())
        else:
            blocks.append(helper_toggle(str(helper), ["Please complete this step."]))
    if blocks:
        req("PATCH", f"https://api.notion.com/v1/blocks/{pid}/children", data=json.dumps({"children":blocks}))
    return pid

def create_database(parent_id, title, schema):
    props = {}
    # Minimal type mapping
    for name, t in (schema.get("properties") or {}).items():
        if t=="title": props[name]={"title":{}}
        elif t=="text": props[name]={"rich_text":{}}
        elif t=="number": props[name]={"number":{"format":"number"}}
        elif t=="select": props[name]={"select":{"options":[{"name":"Pending"},{"name":"Done"}]}}
        elif t=="multi_select": props[name]={"multi_select":{"options":[]}}
        elif t=="date": props[name]={"date":{}}
        elif t=="url": props[name]={"url":{}}
        else: props[name]={"rich_text":{}}
    payload = {"parent":{"type":"page_id","page_id":parent_id},"title":[{"type":"text","text":{"content":title}}],"properties":props}
    r = req("POST","https://api.notion.com/v1/databases", data=json.dumps(payload))
    if r.status_code not in (200,201):
        print("ERROR creating DB", title, r.text); return None
    return r.json()["id"]

def insert_db_rows(dbid, rows):
    for row in rows or []:
        props={}
        for k,v in row.items():
            if isinstance(v,(int,float)):
                props[k]={"number": float(v)}
            elif isinstance(v,str) and v.startswith("http"):
                props[k]={"url": v}
            elif isinstance(v,str):
                props[k]={"rich_text":[{"type":"text","text":{"content":v}}]}
            elif isinstance(v,dict) and v.get("_select"):
                props[k]={"select":{"name": v["_select"]}}
            else:
                props[k]={"rich_text":[{"type":"text","text":{"content":str(v)}}]}
        req("POST","https://api.notion.com/v1/pages", data=json.dumps({"parent":{"type":"database_id","database_id":dbid},"properties":props}))

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="split_yaml")
    ap.add_argument("--deploy", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--update", action="store_true")
    args = ap.parse_args()

    merged = load_split_yaml(args.dir)

    copy_registry = load_copy_registry(args.dir)

    parent = os.getenv("NOTION_PARENT_PAGEID")
    print("Preflight:")
    print(f"  NOTION_TOKEN: {'set' if bool(NOTION_TOKEN) else 'MISSING'}")
    print(f"  Parent page ID: {parent[:6] + '...' if parent else 'ASKING'}")
    print(f"  ICON_BASE_URL: {ICON_BASE_URL if ICON_BASE_URL else '(emoji fallback)'}")
    if not NOTION_TOKEN:
        print("ERROR: NOTION_TOKEN missing"); sys.exit(1)
    if not parent:
        parent = input("Enter top-level Notion page ID to deploy under: ").strip()

    state={"pages":{}, "setup_rows":[]}
    setup_db_id = ensure_setup_db(state, parent)

    # Create pages
    change_plan = []
    for p in merged.get("pages", []):
        title = p.get("title"); icon = resolve_icon(p.get("icon")); cover=p.get("cover")
        desc=p.get("description"); disc=p.get("disclaimer"); slug=p.get("slug")
        if slug and slug in copy_registry:
            override = copy_registry[slug]
            desc = override.get("description", desc)
            disc = override.get("disclaimer", disc)
        parent_title = p.get("parent")
        helper = {"type":"nesting","parent": parent_title} if parent_title else None
        change_plan.append(f"PAGE: {title} (parent: {parent_title or 'Top Level'})")
        if args.dry_run: continue
        pid = create_page(parent, title, icon, cover, desc, disc, helper, p.get("icon_file"), p.get("cover_file"))
        if pid: state["pages"][title]=pid
    # Add legal sample content where applicable
    if pid and title and ("Sample" in title or "Advance Directive" in title):
        sample_blocks=[
            {"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"⚖️"},"rich_text":[{"type":"text","text":{"content":"Sample text for planning conversations — not a valid legal document."}}]}},
            {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"Purpose"}}]}},
            {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"This sample outlines common sections you may discuss with your attorney. Adapt thoughtfully."}}]}},
            {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"Key Sections"}}]}},
            {"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":"Identification and intent"}}]}},
            {"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":"Health care preferences (comfort, interventions, pain management)"}}]}},
            {"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":"Agents/decision-makers and alternates"}}]}},
            {"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":"Signatures, witnesses, and notarization as required"}}]}},
            {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"AI Prompt"}}]}},
            {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"Draft a more detailed sample using the sections above. Keep language clear and compassionate. Mark clearly as 'Sample, not legal advice'."}}]}},
        ]
        req("PATCH", f"https://api.notion.com/v1/blocks/{pid}/children", data=json.dumps({"children":sample_blocks}))


    # Create content databases
    for db_name, schema in (merged.get("db") or {}).get("schemas", {}).items():
        change_plan.append(f"DB: {db_name}")
        if args.dry_run: continue
        dbid = create_database(parent, db_name, schema)
        if dbid:
            pass


    # --- Build Start Here, Welcome, Hub dashboards, and Back/Next navigation ---
    # Gather hub IDs and children
    hubs = ["Preparation Hub","Executor Hub","Family Hub"]
    hub_ids = {t: state["pages"].get(t) for t in hubs if state["pages"].get(t)}
    # Create Start Here after hubs exist
    start_pid = create_page(parent, "Start Here", resolve_icon("emoji:🌟"), None,
                            "Begin here. Choose the path that fits what you need right now.", None, None)
    if start_pid:
        # Three hub tiles (link_to_page)
        blocks=[
            {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"Choose a path"}}]}},
        ]
        for hub in hubs:
            hid = hub_ids.get(hub)
            if not hid: continue
            blocks.append({"object":"block","type":"link_to_page","link_to_page":{"type":"page_id","page_id":hid}})
        req("PATCH", f"https://api.notion.com/v1/blocks/{start_pid}/children", data=json.dumps({"children":blocks}))

    # Welcome page
    welcome_pid = create_page(parent, "Welcome", resolve_icon("emoji:🤝"), None,
                              "You’re in the right place. This workspace helps you prepare, guide your executor, and support family.", None, None)
    if welcome_pid and start_pid:
        welcome_blocks=[
            {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"Take it one section at a time. There’s no rush."}}]}},
            {"object":"block","type":"heading_3","heading_3":{"rich_text":[{"type":"text","text":{"content":"First 3 Steps"}}]}},
            {"object":"block","type":"numbered_list_item","numbered_list_item":{"rich_text":[{"type":"text","text":{"content":"Open the Preparation Hub."}}]}},
            {"object":"block","type":"numbered_list_item","numbered_list_item":{"rich_text":[{"type":"text","text":{"content":"Review a few Executor steps so you know what they’ll need."}}]}},
            {"object":"block","type":"numbered_list_item","numbered_list_item":{"rich_text":[{"type":"text","text":{"content":"When ready, share the Family QR pack."}}]}},
            {"object":"block","type":"link_to_page","link_to_page":{"type":"page_id","page_id":start_pid}},
            helper_toggle("Delete this Welcome page when it’s served its purpose.", ["Open the ••• menu → Delete.", "This page is optional."])
        ]
        req("PATCH", f"https://api.notion.com/v1/blocks/{welcome_pid}/children", data=json.dumps({"children":welcome_blocks}))

    # Hub dashboards: add intro + child links
    # Map each hub to its children (from YAML)
    pages_by_parent = {}
    for p in merged.get("pages", []):
        pr = p.get("parent")
        if pr:
            pages_by_parent.setdefault(pr, []).append(p.get("title"))
    for hub, hid in hub_ids.items():
        children_titles = pages_by_parent.get(hub, [])
        hub_blocks=[
            {"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"ℹ️"},"rich_text":[{"type":"text","text":{"content":f"This hub focuses on {hub.lower()} tasks. Move at your pace."}}],"color":"gray_background"}},
            {"object":"block","type":"heading_3","heading_3":{"rich_text":[{"type":"text","text":{"content":"Sections"}}]}},
        ]
        for t in children_titles[:20]:  # avoid too-large payloads
            pid = state["pages"].get(t)
            if not pid: continue
            hub_blocks.append({"object":"block","type":"link_to_page","link_to_page":{"type":"page_id","page_id":pid}})
        # Add Start Here backlink
        if start_pid:
            hub_blocks.append({"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":" "}}]}})
            hub_blocks.append({"object":"block","type":"link_to_page","link_to_page":{"type":"page_id","page_id":start_pid}})
        req("PATCH", f"https://api.notion.com/v1/blocks/{hid}/children", data=json.dumps({"children":hub_blocks}))

    # Back to Hub + Next Step on each child page
    # Build per-parent order
    order_by_parent = {}
    for p in merged.get("pages", []):
        if p.get("parent"):
            order_by_parent.setdefault(p["parent"], []).append(p["title"])
    for parent_title, titles in order_by_parent.items():
        ids=[state["pages"].get(tt) for tt in titles if state["pages"].get(tt)]
        for idx, tt in enumerate(titles):
            pid = state["pages"].get(tt)
            if not pid: continue
            children=[]
            # Back to hub
            hub_id = state["pages"].get(parent_title)
            if hub_id:
                children.append({"object":"block","type":"link_to_page","link_to_page":{"type":"page_id","page_id":hub_id}})
            # Next step
            if idx+1 < len(titles):
                next_pid = state["pages"].get(titles[idx+1])
                if next_pid:
                    children.append({"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"Next step →"}}]}})
                    children.append({"object":"block","type":"link_to_page","link_to_page":{"type":"page_id","page_id":next_pid}})
            if children:
                req("PATCH", f"https://api.notion.com/v1/blocks/{pid}/children", data=json.dumps({"children":children}))

    # Letters as subpages
    for L in merged.get("letters", []):
        title = f"Letter — {L.get('Title','Untitled')}"
        body = L.get("Body","")
        desc = "This draft letter is provided to help you start; personalize details before sending."
        parent_title = "Letters"
        change_plan.append(f"LETTER: {title} (parent: {parent_title})")
        if args.dry_run: continue
        pid = create_page(parent, title, resolve_icon("emoji:✉️"), None, desc, None, {"type":"nesting","parent":parent_title})
        if pid and body:
            blocks=[
                {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":body}}]}},
                {"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"ℹ️"},"rich_text":[{"type":"text","text":{"content":"This is a suggested draft, not legal advice. Confirm requirements for the recipient."}}]}},
                {"object":"block","type":"heading_3","heading_3":{"rich_text":[{"type":"text","text":{"content":"AI Prompt"}}]}},
                {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"Please refine the letter above using the facts from this page. Keep the tone respectful, factual, and concise."}}]}}
            ]
            req("PATCH", f"https://api.notion.com/v1/blocks/{pid}/children", data=json.dumps({"children":blocks}))

    # Release Notes page
    rn = merged.get("release_notes")
    if rn:
        change_plan.append("PAGE: Release Notes (Admin)")
        if not args.dry_run:
            pid = create_page(parent, "Admin – Release Notes", resolve_icon("emoji:🗒️"), None, None, None, None)
            # Add content paragraphs
            blocks=[]
            for line in rn.splitlines():
                blocks.append({"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":line}}]}})
            if pid: req("PATCH", f"https://api.notion.com/v1/blocks/{pid}/children", data=json.dumps({"children":blocks}))

    
    # --- Unified Setup & Acceptance population (upsert) ---
    def upsert_helper_row(title, intended_parent, pid):
        section = intended_parent or "Top Level"
        url = page_url(pid)
        check_text = f"Move under “{intended_parent}”" if intended_parent else "Complete manual step"
        existing = setup_row_find(setup_db_id, title, "Helper", check_text)
        has_helper = children_have_helper(pid)
        status = "Pending" if has_helper else "Done"
        props = {"Status":{"select":{"name": status}}, "Section":{"select":{"name": section}}}
        if url: props["PageURL"] = {"url": url}
        if existing:
            for row in existing: patch_setup_row(row["id"], props)
        else:
            setup_db_add_row(setup_db_id, title, "owner", "Helper", check_text, status, est_minutes=5, section=section, page_url_val=url, page_id=pid, state=state)

    def upsert_acceptance_row(title, role, check, status, section, pid, est):
        url = page_url(pid) if pid else None
        existing = setup_row_find(setup_db_id, title, "Acceptance", check)
        props = {"Status":{"select":{"name": status}}, "Section":{"select":{"name": section or 'Top Level'}}}
        if url: props["PageURL"] = {"url": url}
        if existing:
            for row in existing: patch_setup_row(row["id"], props)
        else:
            setup_db_add_row(setup_db_id, title, role, "Acceptance", check, status, est_minutes=est, section=section, page_url_val=url, page_id=pid, state=state)

    # Helpers (one per page that has nesting intent)
    for p in merged.get("pages", []):
        intended_parent = p.get("parent")
        title = p.get("title")
        pid = state["pages"].get(title)
        if intended_parent and pid:
            upsert_helper_row(title, intended_parent, pid)

    # Acceptance rows from YAML
    acc_rows = (merged.get("acceptance") or {}).get("rows") or []
    for r in acc_rows:
        title=r.get("Page"); role=r.get("Role","owner"); check=r.get("Check","Finalize this page")
        status=r.get("Status","Pending"); section=r.get("Section") or r.get("Parent") or "Top Level"
        est=r.get("Est. Time (min)") or None
        pid=state["pages"].get(title)
        upsert_acceptance_row(title, role, check, status, section, pid, est)

    # Build Rollout Summary from live DB (Pending only)
    pendings = db_query(setup_db_id, {"property":"Status","select":{"equals":"Pending"}})
    section_counts={}
    for row in pendings:
        props=row.get("properties",{})
        sec=(props.get("Section",{}).get("select",{}) or {}).get("name") or "(Unassigned)"
        minutes=props.get("Est. Time",{}).get("number") or 5
        section_counts.setdefault(sec,{"pending":0,"minutes":0})
        section_counts[sec]["pending"]+=1
        section_counts[sec]["minutes"]+=float(minutes)
    total_pending=sum(v["pending"] for v in section_counts.values())
    total_minutes=sum(v["minutes"] for v in section_counts.values())
# Write rollout summary onto parent page (top-level)
    rollout_blocks=[build_icon_hosting_helper()]
    if section_counts:
        rollout_blocks.append({"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"Section Subtotals"}}]}})
        for sec,vals in section_counts.items():
            hrs=int(vals["minutes"]//60); mins=int(vals["minutes"]%60)
            line=f"{sec}: {vals['pending']} Pending — ~{hrs}h {mins}m remaining"
            rollout_blocks.append({"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":line}}]}})
        hrs=int(total_minutes//60); mins=int(total_minutes%60)
        rollout_blocks.append({"object":"block","type":"heading_3","heading_3":{"rich_text":[{"type":"text","text":{"content":f'Total Remaining: {total_pending} Pending — ~{hrs}h {mins}m'}}]}})
    req("PATCH", f"https://api.notion.com/v1/blocks/{parent}/children", data=json.dumps({"children":rollout_blocks}))
    # --- Admin branch pages: Cockpit and Diagnostics ---
    # Cockpit: instructions + link to Setup & Acceptance
    cock_pid = create_page(parent, "Admin – Rollout Cockpit", resolve_icon("emoji:🧭"), None,
                           "Quick access to rollout. Filter by Section, Status=Pending. Group by Type or Role for focus.", None, None)
    if cock_pid:
        cock_blocks=[
            {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"Use the database below to track progress. Create views in the UI: Pending Only, Quick Wins (<=15m), By Type (Helper vs Acceptance)."}}]}},
            {"object":"block","type":"heading_3","heading_3":{"rich_text":[{"type":"text","text":{"content":"Setup & Acceptance Database"}}]}},
            {"object":"block","type":"link_to_page","link_to_page":{"type":"database_id","database_id": setup_db_id}}
        ]
        req("PATCH", f"https://api.notion.com/v1/blocks/{cock_pid}/children", data=json.dumps({"children":cock_blocks}))

    # Diagnostics: missing icons/covers + pages still carrying helpers
    diag_pid = create_page(parent, "Admin – Diagnostics", resolve_icon("emoji:🔍"), None,
                           "Automatic checks to help you finish setup.", None, None)
    if diag_pid:
        issues=[]
        # Check icons/covers: from YAML
        for p in merged.get("pages", []):
            ttl=p.get("title"); ic=p.get("icon"); cov=p.get("cover")
            if not ic: issues.append(f"Icon missing — {ttl}")
            if not cov: issues.append(f"Cover missing — {ttl}")
        # Pages still with helpers
        for ttl, pid in state["pages"].items():
            if children_have_helper(pid):
                issues.append(f"Helper present — {ttl}")
        if not issues:
            diag_blocks=[{"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":"No issues detected."}}]}}]
        else:
            diag_blocks=[{"object":"block","type":"heading_3","heading_3":{"rich_text":[{"type":"text","text":{"content":"Items to review"}}]}}]
            for it in issues:
                diag_blocks.append({"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":it}}]}})
        req("PATCH", f"https://api.notion.com/v1/blocks/{diag_pid}/children", data=json.dumps({"children":diag_blocks}))


    # Hub saved-views helper toggles (API can't create views)
    hub_titles = set([p.get("parent") for p in merged.get("pages", []) if p.get("parent")])
    hub_page_ids = {t: state["pages"].get(t) for t in hub_titles if state["pages"].get(t)}
    hub_helper = helper_toggle(
        "Create linked views for this section (one-time)",
        [
            "Add a linked view of the ‘Setup & Acceptance’ database on this page.",
            "Filter: Section equals this hub’s name.",
            "Add a ‘Pending Only’ view: filter Status = Pending.",
            "Add a ‘Quick Wins’ view: filter Est. Time <= 15.",
            "Add a ‘By Type’ view: group by Helper vs Acceptance.",
            "Optional: Add a ‘Timeline’ view if you assign due dates."
        ]
    )
    for hub_title, hub_id in hub_page_ids.items():
        req("PATCH", f"https://api.notion.com/v1/blocks/{hub_id}/children", data=json.dumps({"children":[hub_helper]}))

    # Print plan
    print("Change plan:")
    for line in change_plan:
        print(" -", line)
    print(f"Acceptance rows added/updated: {added}")

if __name__ == "__main__":
    main()

def resolve_cover(filename):
    # Notion requires a public URL for covers; use ICON_BASE_URL as generic ASSET_BASE_URL if set
    base = os.getenv("ASSET_BASE_URL") or ICON_BASE_URL
    if filename and base:
        return base.rstrip('/') + '/' + filename
    return None
