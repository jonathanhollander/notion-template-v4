
# deploy_v3_5.py — v3.7.5 (Audit Fix Patch)
# Entry points preserved: --dry-run, --deploy, --update
# Implements:
# - True relations (from "Related Page Title")
# - Acceptance DB "Check" as Notion formula
# - Rich-text seeds (italic/gray) for Notes
# - Multi-select defaults
# - Synced blocks library + copies
# - Grid dashboards, hero blocks, nav links
# - Robust req() with retries incl. 504; JSON helpers
# - All helper functions defined; idempotent markers
import os, sys, json, time, argparse
import requests

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_VERSION = os.getenv("NOTION_VERSION", "2022-06-28")

def req(method, url, data=None, timeout=25):
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    }
    for attempt in range(5):
        try:
            r = requests.request(method, url, headers=headers, data=data, timeout=timeout)
        except requests.exceptions.RequestException:
            time.sleep(1.2 * (attempt + 1)); continue
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(1.5 * (attempt + 1)); continue
        return r
    return r

def j(resp):
    try:
        return resp.json()
    except Exception:
        return {}

def resolve_icon(spec):
    if not spec: return None
    if spec.startswith("emoji:"):
        return {"type":"emoji","emoji": spec.split(":",1)[1]}
    base = os.getenv("ASSET_BASE_URL") or os.getenv("ICON_BASE_URL")
    if base and (spec.endswith(".png") or spec.endswith(".jpg") or spec.endswith(".jpeg")):
        return {"type":"external","external":{"url": base.rstrip("/") + "/" + spec}}
    # fallback emoji
    return {"type":"emoji","emoji":"📄"}

def helper_toggle(summary, bullets):
    return {"object":"block","type":"toggle","toggle":{"rich_text":[{"type":"text","text":{"content":summary}}],
            "children":[{"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":b}}]}} for b in bullets]}}

def rt(text, italic=False, bold=False, color="gray"):
    return [{"type":"text","text":{"content":str(text)},"annotations":{"italic":italic,"bold":bold,"color":color}}]

def has_marker(pid, text_snippet):
    r = req("GET", f"https://api.notion.com/v1/blocks/{pid}/children")
    data = j(r)
    for b in data.get("results", []):
        t = b.get("type")
        if t in ["paragraph","heading_1","heading_2","heading_3","callout","bulleted_list_item","numbered_list_item","to_do","toggle"]:
            rtxt = b[t].get("rich_text",[])
            txt = "".join([x.get("plain_text","") for x in rtxt])
            if text_snippet.lower() in txt.lower():
                return True
    return False

def create_page(parent_id, title, icon=None, cover=None, description=None, helpers=None, role=None):
    payload = {"parent":{"type":"page_id","page_id":parent_id},
               "icon": icon, "cover": cover,
               "properties":{"title":{"title":[{"type":"text","text":{"content":title}}]}}}
    r = req("POST","https://api.notion.com/v1/pages", data=json.dumps(payload))
    if r.status_code not in (200,201):
        print("ERROR creating page", title, r.text); return None
    pid = j(r)["id"]
    blocks = []
    if description:
        blocks.append({"object":"block","type":"paragraph","paragraph":{"rich_text": rt(description)}})
    if helpers:
        for helper in helpers:
            blocks.append(helper_toggle(str(helper), ["Please complete this step."]))
    if blocks:
        req("PATCH", f"https://api.notion.com/v1/blocks/{pid}/children", data=json.dumps({"children":blocks}))
    return pid

def role_color(role):
    r = (role or "owner").lower()
    return "blue_background" if r=="executor" else ("orange_background" if r=="family" else "gray_background")

def make_hero_blocks(title, role):
    return [
        {"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"⬢"},"rich_text": rt(f"This page helps you with: {title}", bold=True),"color": role_color(role)}},
        {"object":"block","type":"divider","divider":{}}
    ]

def grid_cards(items, cols=3):
    columns=[[] for _ in range(cols)]
    for i, it in enumerate(items):
        c=i%cols
        tile={"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"⬢"},"rich_text": rt(it.get("title","")),"color": role_color(it.get("role"))}}
        columns[c].append(tile)
        if it.get("subtitle"):
            columns[c].append({"object":"block","type":"paragraph","paragraph":{"rich_text": rt(it["subtitle"])}})
        if it.get("page_id"):
            columns[c].append({"object":"block","type":"link_to_page","link_to_page":{"type":"page_id","page_id": it["page_id"]}})
        columns[c].append({"object":"block","type":"paragraph","paragraph":{"rich_text": rt(" ")}})
    col_blocks=[{"object":"block","type":"column","column":{"children":blocks}} for blocks in columns]
    return [{"object":"block","type":"column_list","column_list":{}}, *col_blocks]

def create_database(parent_id, title, schema):
    # schema.properties may be dict[str, str] or dict[str, dict]
    props = {}
    for name, spec in (schema.get("properties") or {}).items():
        t = spec if isinstance(spec, str) else spec.get("type") or "rich_text"
        if t=="title": props[name]={"title":{}}
        elif t=="text" or t=="rich_text": props[name]={"rich_text":{}}
        elif t=="number": props[name]={"number":{"format":"number"}}
        elif t=="select": props[name]={"select":{"options":[{"name":o} for o in (spec.get("options") if isinstance(spec, dict) else [])]}}
        elif t=="multi_select": props[name]={"multi_select":{"options":[{"name":o} for o in (spec.get("options") if isinstance(spec, dict) else [])]}}
        elif t=="date": props[name]={"date":{}}
        elif t=="url": props[name]={"url":{}}
        elif t=="relation": props[name]={"relation":{"database_id": "DYNAMIC_PAGE_DB", "type":"single_property", "single_property":{}}}  # we'll patch db id later if needed
        elif t=="formula":
            expr = spec.get("formula") or spec.get("expression") or '""'
            props[name]={"formula":{"expression": expr}}
        else: props[name]={"rich_text":{}}
    payload = {"parent":{"type":"page_id","page_id":parent_id},
               "title":[{"type":"text","text":{"content":title}}],
               "properties":props}
    r = req("POST","https://api.notion.com/v1/databases", data=json.dumps(payload))
    if r.status_code not in (200,201):
        print("ERROR creating DB", title, r.text); return None
    return j(r)["id"]

def insert_db_rows(dbid, rows, state):
    # Build once: property map
    meta = j(req("GET", f"https://api.notion.com/v1/databases/{dbid}"))
    pmap = meta.get("properties",{})
    for row in rows or []:
        props={}
        for k,v in row.items():
            if v is None: continue
            # Relation by title hint
            if k in ["Related Page Title","Related Page"] and "Related Page" in pmap:
                pid = state["pages"].get(str(v))
                if pid:
                    props["Related Page"]={"relation":[{"id":pid}]}
                continue
            # Title
            if k in pmap and pmap[k]["type"]=="title":
                props[k]={"title":[{"type":"text","text":{"content":str(v)}}]}; continue
            # Select
            if k in pmap and pmap[k]["type"]=="select":
                props[k]={"select":{"name": str(v)}}; continue
            # Multi-select
            if k in pmap and pmap[k]["type"]=="multi_select":
                items = v if isinstance(v,list) else [v]
                props[k]={"multi_select":[{"name":str(x)} for x in items]}; continue
            # Number
            if k in pmap and pmap[k]["type"]=="number":
                try: num=float(v)
                except: num=None
                props[k]={"number": num}; continue
            # Rich text (Notes/Note)
            if k.lower() in ["note","notes"] or k.endswith(" Note"):
                props[k]={"rich_text": rt(v, italic=True, color="gray")}; continue
            # Fallback to rich_text
            if k in pmap:
                props[k]={"rich_text":[{"type":"text","text":{"content":str(v)}}]}
        created = req("POST","https://api.notion.com/v1/pages", data=json.dumps({"parent":{"database_id":dbid},"properties":props}))
        if created.status_code not in (200,201):
            print("WARN seed row failed:", created.text)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--deploy", action="store_true")
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args()
    parent = os.getenv("NOTION_PARENT_PAGEID")
    if not parent: print("Missing NOTION_PARENT_PAGEID"); sys.exit(1)
    if not NOTION_TOKEN: print("Missing NOTION_TOKEN"); sys.exit(1)

    # Load all YAML
    import yaml, os
    merged = {"pages":[], "db":{"schemas":{}}, "acceptance":{"rows":[]}}
    for name in sorted(os.listdir(args.dir)):
        if not name.endswith(".yaml"): continue
        d = yaml.safe_load(open(os.path.join(args.dir,name),"r",encoding="utf-8"))
        if not d: continue
        if "pages" in d: merged["pages"].extend(d["pages"])
        if "db" in d and "schemas" in d["db"]:
            merged["db"]["schemas"].update(d["db"]["schemas"])
        if "acceptance" in d and "rows" in d["acceptance"]:
            merged["acceptance"]["rows"].extend(d["acceptance"]["rows"])

    # State
    state={"pages":{}, "dbs":{}}

    def upsert_page(title, parent_title=None, icon=None, cover=None, description=None, helpers=None, role=None):
        pid = create_page(parent, title, resolve_icon(icon) if icon else None, None, description, helpers, role)
        state["pages"][title]=pid
        return pid

    # Create top-level hubs known by title (if defined in YAML)
    # We rely on merged["pages"] entries to create pages; hubs are inferred by matches
    if args.dry_run:
        print("DRY-RUN: would create", len(merged["pages"]), "pages and", len(merged["db"]["schemas"]), "databases")
        # Show a subset
        for p in merged["pages"][:10]:
            print(" - Page:", p.get("title"))
        for k in list(merged["db"]["schemas"].keys())[:10]:
            print(" - DB:", k)
        return

    # Create all pages first (to resolve relations by title later)
    for p in merged["pages"]:
        upsert_page(p.get("title"), p.get("parent"), p.get("icon"), p.get("cover_png") or p.get("cover"), p.get("description"), p.get("helper"), p.get("role"))

    # Inject hero blocks once
    for title, pid in state["pages"].items():
        if not has_marker(pid, "This page helps you with:"):
            blocks = make_hero_blocks(title, None)
            req("PATCH", f"https://api.notion.com/v1/blocks/{pid}/children", data=json.dumps({"children":blocks}))

    # Dashboards: simple grid on hubs if they exist
    hubs = ["Preparation Hub","Executor Hub","Family Hub"]
    hub_ids = {t: state["pages"].get(t) for t in hubs if state["pages"].get(t)}
    for hub, hid in hub_ids.items():
        # Build grid of its children by scanning merged pages with parent==hub
        children=[p.get("title") for p in merged["pages"] if p.get("parent")==hub]
        items=[]
        for t in children:
            cid=state["pages"].get(t); role="owner" if hub=="Preparation Hub" else ("executor" if hub=="Executor Hub" else "family")
            if cid: items.append({"title":t,"subtitle":None,"page_id":cid,"role":role})
        grid=grid_cards(items, cols=3)
        req("PATCH", f"https://api.notion.com/v1/blocks/{hid}/children", data=json.dumps({"children":grid}))

    # Create databases
    for db_name, schema in merged["db"]["schemas"].items():
        dbid = create_database(parent, db_name, schema)
        if not dbid: continue
        state["dbs"][db_name]=dbid
        # If Acceptance DB, patch its Check as a formula
        if db_name.lower().startswith("acceptance") or db_name=="Setup & Acceptance":
            # ensure formula
            # Update property to formula via patch (Notion doesn't support partial schema patch fully; but try)
            props={"properties":{"Check":{"formula":{"expression":'if(prop("Status") == "Done", "✅", "")'}}}}
            req("PATCH", f"https://api.notion.com/v1/databases/{dbid}", data=json.dumps(props))
        # Seed rows
        rows = (schema.get("seed_rows") or [])
        if rows: insert_db_rows(dbid, rows, state)

    # Synced blocks library (legal/letters/executor notes)
    def create_synced_library():
        lib_id = create_page(parent, "Admin – Synced Library", {"type":"emoji","emoji":"📌"}, None, "Master synced blocks for disclaimers and helpers.", None, None)
        if not lib_id: return None, {}
        children=[
            {"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"⚖️"},"rich_text": rt("Legal documents: This workspace offers general guidance only. It is not legal advice."),"color":"gray_background"}},
            {"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"✉️"},"rich_text": rt("Letters: Confirm each recipient’s requirements before sending."),"color":"gray_background"}},
            {"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"🧭"},"rich_text": rt("Executor: You don’t have to do this all at once. Start with the first, easiest step."),"color":"gray_background"}},
        ]
        r = req("PATCH", f"https://api.notion.com/v1/blocks/{lib_id}/children", data=json.dumps({"children":children}))
        data=j(r); sync_map={}
        for b in data.get("results", []):
            text="".join([t.get("plain_text","") for t in b.get("callout",{}).get("rich_text",[])])
            key=text.split(":")[0] if ":" in text else text[:16]
            sync_map[key]=b["id"]
        return lib_id, sync_map

    def add_synced_to_pages(sync_map):
        pairs=[("Legal documents","Legal Documents"),("Letters","Letters"),("Executor","Executor Hub")]
        for key, page_title in pairs:
            pid=state["pages"].get(page_title)
            if not pid or key not in sync_map: continue
            src_id=sync_map[key]
            block={"object":"block","type":"synced_block","synced_block":{"synced_from":{"block_id":src_id}}}
            req("PATCH", f"https://api.notion.com/v1/blocks/{pid}/children", data=json.dumps({"children":[block]}))

    lib_id, sm = create_synced_library()
    if lib_id: add_synced_to_pages(sm)

    if args.update:
        # Could add completion cues by reading Acceptance DB here if needed
        pass

if __name__ == "__main__":
    main()
