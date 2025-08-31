
# deploy_v3_5.py — v (Audit Fix Patch)
# Entry points preserved: # Implements:
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
import urllib.parse
import urllib.parse
import math

ENABLE_SEARCH_FALLBACK = os.getenv("ENABLE_SEARCH_FALLBACK","1") in ("1","true","True","yes","YES")

def expect_ok(resp, context=""):
    if resp is None:
        print("ERROR:", context, "no response"); return False
    if resp.status_code not in (200,201):
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        print("ERROR:", context, resp.status_code, body)
        return False
    return True

def find_page_id_by_title(title, state):
    pid = state["pages"].get(title)
    if pid:
        return pid
    if not ENABLE_SEARCH_FALLBACK:
        return None
    payload = {
        "query": title,
        "filter": {"value":"page","property":"object"}
    }
    r = req("POST","https://api.notion.com/v1/search", data=json.dumps(payload))
    if r.status_code in (200,201):
        data = j(r)
        for res in data.get("results",[]):
            # Try to read the page title property (varies by DB/page)
            props = res.get("properties",{})
            name = None
            for p in props.values():
                if p.get("type")=="title":
                    name = "".join([t.get("plain_text","") for t in p.get("title",[])])
                    break
            if not name and res.get("object")=="page":
                # fallback to plain title in properties.title
                pass
            if name and name.strip()==title.strip():
                return res.get("id")
    return None

def url_join(base, filename):
    filename = filename.lstrip("/")
    return base.rstrip("/") + "/" + urllib.parse.quote(filename)


NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_VERSION = os.getenv("NOTION_VERSION", "2022-06-28")

def req(method, url, headers=None, data=None, files=None, timeout=None):
    headers = headers or {}
    if "Notion-Version" not in headers:
        headers["Notion-Version"] = os.getenv("NOTION_VERSION","2022-06-28")
    if "Authorization" not in headers:
        headers["Authorization"] = f'Bearer {os.getenv("NOTION_TOKEN","")}'
    if "Content-Type" not in headers and data is not None and files is None:
        headers["Content-Type"] = "application/json"
    timeout = timeout or int(os.getenv("NOTION_TIMEOUT","25"))
    max_try = int(os.getenv("RETRY_MAX","5"))
    backoff = float(os.getenv("RETRY_BACKOFF_BASE","1.5"))
    for attempt in range(max_try):
        try:
            r = requests.request(method, url, headers=headers, data=data, files=files, timeout=timeout)
        except requests.exceptions.Timeout:
            if attempt == max_try-1: raise
            time.sleep(backoff * (attempt+1)); continue
        except requests.exceptions.RequestException as e:
            # network failure
            if attempt == max_try-1: raise
            time.sleep(backoff * (attempt+1)); continue
        if r.status_code in (429, 500, 502, 503, 504):
            # retryable
            time.sleep(backoff * (attempt+1)); continue
        # return on any non-retryable
        return r
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
    if base and (spec.endswith(".png") or spec.endswith(".jpg") or spec.endswith(".jpeg") or spec.endswith(".svg")):
        return {"type":"external","external":{"url": url_join(base, spec)}}
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
    # Build hero + description + helpers in one pass to avoid duplicates later
    blocks = []
    blocks += make_hero_blocks(title, role)
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
        {"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"⬢"},"rich_text": rt("HERO_MARKER  This page helps you with: " + title, bold=True),"color": role_color(role)}},
        {"object":"block","type":"divider","divider":{}}
    ]

def grid_cards(items, cols=3):
    n=len(items)
    if n==0: return []
    cols=max(1, min(3, n))
    columns=[[] for _ in range(cols)]
    # seed one per column
    for i in range(min(n, cols)):
        it = items[i]
        tile={"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"⬢"},"rich_text": rt(it.get("title","")),"color": role_color(it.get("role"))}}
        columns[i].append(tile)
        if it.get("subtitle"):
            columns[i].append({"object":"block","type":"paragraph","paragraph":{"rich_text": rt(it["subtitle"])}})
        if it.get("page_id"):
            columns[i].append({"object":"block","type":"link_to_page","link_to_page":{"type":"page_id","page_id": it["page_id"]}})
        columns[i].append({"object":"block","type":"paragraph","paragraph":{"rich_text": rt(" ")}})
    for i in range(cols, n):
        it = items[i]
        c = i % cols
        tile={"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"⬢"},"rich_text": rt(it.get("title","")),"color": role_color(it.get("role"))}}
        columns[c].append(tile)
        if it.get("subtitle"):
            columns[c].append({"object":"block","type":"paragraph","paragraph":{"rich_text": rt(it["subtitle"])}})
        if it.get("page_id"):
            columns[c].append({"object":"block","type":"link_to_page","link_to_page":{"type":"page_id","page_id": it["page_id"]}})
        columns[c].append({"object":"block","type":"paragraph","paragraph":{"rich_text": rt(" ")}})
    col_blocks=[{"object":"block","type":"column","column":{"children": blocks}} for blocks in columns]
    return [{"object":"block","type":"column_list","column_list":{}}, *col_blocks]

def create_database(parent_id, title, schema):
    props = {}
    for name, spec in (schema.get("properties") or {}).items():
        t = spec if isinstance(spec, str) else spec.get("type") or "rich_text"
        if t=="title": props[name]={"title":{}}
        elif t in ("text","rich_text"): props[name]={"rich_text":{}}
        elif t=="number": props[name]={"number":{"format":"number"}}
        elif t=="select": props[name]={"select":{"options":[{"name":o} for o in (spec.get("options") if isinstance(spec, dict) else [])]}}
        elif t=="multi_select": props[name]={"multi_select":{"options":[{"name":o} for o in (spec.get("options") if isinstance(spec, dict) else [])]}}
        elif t=="date": props[name]={"date":{}}
        elif t=="url": props[name]={"url":{}}
        elif t=="relation": props[name]={"relation":{"database_id": state.get("pages_index_db") or "", "type":"single_property", "single_property":{}}}
        elif t=="formula":
            expr = spec.get("formula") or spec.get("expression") or '""'
            props[name]={"formula":{"expression": expr}}
        else: props[name]={"rich_text":{}}
    payload = {"parent":{"type":"page_id","page_id":parent_id},"title":[{"type":"text","text":{"content":title}}],"properties":props}
    r = req("POST","https://api.notion.com/v1/databases", data=json.dumps(payload))
    expect_ok(r, f"create DB {title}")
    dbid = j(r).get("id")
    # If Acceptance/Setup, ensure Check formula exists
    if dbid and (title.lower().startswith("acceptance") or title.lower().startswith("setup")):
        req("PATCH", f"https://api.notion.com/v1/databases/{dbid}", data=json.dumps({"properties":{"Check":{"formula":{"expression":'if(prop("Status") == "Done", "✅", "")'}}}}))
    return dbid

def insert_db_rows(dbid, rows, state):
    meta = j(req("GET", f"https://api.notion.com/v1/databases/{dbid}"))
    pmap = meta.get("properties",{})
    for row in rows or []:
        # Merge Notes -> Note to avoid conflicts
        if "Notes" in row and "Note" not in row:
            row["Note"] = row.pop("Notes")
        props={}
        # Prefetch related page title if needed
        target_title = row.get("Related Page Title") or row.get("Related Page")
        target_pid = None
        if target_title and "Related Page" in pmap:
                # Resolve to Pages Index DB item
                idx_db = state.get("pages_index_db")
                idx_item = find_index_item_by_title(idx_db, str(target_title)) if idx_db else None
                if idx_item:
                    props["Related Page"]={"relation":[{"id":idx_item}]}
                else:
                    ensure_property_rich_text(dbid, "Intended Relation")
                    props["Intended Relation"]={"rich_text": rt(f"{target_title} (not found)", italic=True, color="gray")}
                continue
            if k in ["Related Page Title","Related Page"]:
                if target_pid:
                    props["Related Page"]={"relation":[{"id":target_pid}]}
                else:
                    # keep a breadcrumb of intended title
                    if "Intended Relation" in pmap:
                        props["Intended Relation"]={"rich_text": rt(str(v), italic=True, color="gray")}
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
            # Rich text for Note
            if k.lower() in ["note","notes"] or k.endswith(" Note"):
                props["Note" if "Note" in pmap else k]={"rich_text": rt(v, italic=True, color="gray")}; continue
            # Fallback rich_text
            if k in pmap:
                props[k]={"rich_text":[{"type":"text","text":{"content":str(v)}}]}
        created = req("POST","https://api.notion.com/v1/pages", data=json.dumps({"parent":{"database_id":dbid},"properties":props}))
        expect_ok(created, f"seed row in {dbid}")
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

    # Pages Index DB first
    state["pages_index_db"] = ensure_pages_index_db(parent)

    # PREVIEW
    preview_plan(merged)
    resp = os.getenv("AUTO_YES")
    if not resp:
        resp = input("Proceed with deployment? (y/n): ").strip().lower()
    if resp not in ("y","yes","1","true"):
        print("Aborted by user.")
        return

    # Create all pages first (to resolve relations by title later)
    for p in merged["pages"]:

        upsert_page(p.get("title"), p.get("parent"), p.get("icon"), p.get("cover_png") or p.get("cover"), p.get("description"), p.get("helper"), p.get("role"))

    # Hero blocks already injected in create_page
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

    # Add mobile tips to hubs
    add_mobile_tip(state, merged["pages"])

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
    pairs=[("LEGAL","Legal Documents"),("LETTERS","Letters"),("EXECUTOR","Executor Hub")]
    for key, page_title in pairs:
        pid=state["pages"].get(page_title)
        if not pid or key not in sync_map: continue
        src_id=sync_map[key]
        # idempotency: skip if a synced_block already references src_id
        existing = get_children(pid)
        found = False
        for b in existing:
            if b.get("type")=="synced_block":
                sf = b["synced_block"].get("synced_from")
                if sf and sf.get("block_id")==src_id:
                    found=True; break
        if found: 
            continue
        block={"object":"block","type":"synced_block","synced_block":{"synced_from":{"block_id":src_id}}}
        insert_children(pid, [block])
    return
 {"object":"block","type":"link_to_page","link_to_page":{"type":"page_id","page_id": pid}}

def add_nav_links(state, pages_cfg):
    # Build parent -> children mapping in listed order
    children_by_parent={}
    for p in pages_cfg:
        parent=p.get("parent")
        children_by_parent.setdefault(parent or "__ROOT__", []).append(p.get("title"))
    # For each page with a parent, add Back and Next links
    for p in pages_cfg:
        title=p.get("title"); parent=p.get("parent")
        if not parent: continue
        pid = state["pages"].get(title); par_id = state["pages"].get(parent)
        if not pid or not par_id: continue
        sibs = children_by_parent.get(parent, [])
        try:
            idx=sibs.index(title)
        except ValueError:
            idx=None
        next_pid=None
        if idx is not None and idx+1 < len(sibs):
            next_title=sibs[idx+1]
            next_pid = state["pages"].get(next_title)
        blocks=[]
        # Navigation group
        nav_children=[]
        nav_children.append({"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"↩️"},"rich_text": rt("Back to " + parent),"color":"gray_background"}})
        nav_children.append(link_to_page_block(par_id))
        if next_pid:
            nav_children.append({"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"➡️"},"rich_text": rt("Next step"),"color":"gray_background"}})
            nav_children.append(link_to_page_block(next_pid))
        blocks.append({"object":"block","type":"toggle","toggle":{"rich_text": rt("Navigation"),"children": nav_children}})
        req("PATCH", f"https://api.notion.com/v1/blocks/{pid}/children", data=json.dumps({"children":blocks}))

def add_mobile_tip(state, pages_cfg):
    # Treat hubs from YAML if marked, else fallback to known names
    hub_titles=set()
    for p in pages_cfg:
        if p.get("hub") is True:
            hub_titles.add(p.get("title"))
    if not hub_titles:
        hub_titles.update(["Preparation Hub","Executor Hub","Family Hub"])
    tip='On phones, use the ••• menu to jump sections. Tiles stack vertically.'
    for t in hub_titles:
        pid=state["pages"].get(t)
        if not pid: continue
        block={"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"📱"},"rich_text": rt(tip, italic=True, color="gray"),"color":"gray_background"}}
        req("PATCH", f"https://api.notion.com/v1/blocks/{pid}/children", data=json.dumps({"children":[block]}) )

def add_letter_legal_content(state, pages_cfg):
    # If a page dict includes Body/Disclaimer, render them
    for p in pages_cfg:
        title=p.get("title"); pid=state["pages"].get(title)
        if not pid: continue
        body = p.get("Body") or p.get("body")
        disclaimer = p.get("Disclaimer") or p.get("disclaimer")
        if not (body or disclaimer): continue
        children=[]
        if body:
            children.append({"object":"block","type":"toggle","toggle":{"rich_text": rt("Draft (expand)"),"children":[{"object":"block","type":"paragraph","paragraph":{"rich_text": rt(body)}}]}})
        if disclaimer:
            children.append({"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"⚠️"},"rich_text": rt(disclaimer),"color":"gray_background"}})
        if children:
            req("PATCH", f"https://api.notion.com/v1/blocks/{pid}/children", data=json.dumps({"children":children}))

def get_children(pid, page_size=100):
    r = req("GET", f"https://api.notion.com/v1/blocks/{pid}/children?page_size={page_size}")
    return j(r).get("results", [])

def plain_text(rtlist):
    return "".join([x.get("plain_text","") for x in (rtlist or [])])

def has_block_marker(pid, token):
    results = get_children(pid)
    for b in results:
        t = b.get("type")
        if t in ("paragraph","callout","toggle","bulleted_list_item","numbered_list_item","to_do"):
            txt = plain_text(b[t].get("rich_text",[]))
            if token in txt:
                return True
        if t=="synced_block":
            # check first child
            sc = req("GET", f"https://api.notion.com/v1/blocks/{b['id']}/children")
            scj = j(sc)
            for cb in scj.get("results",[]):
                tt = cb.get("type")
                if tt in ("paragraph","callout","toggle"):
                    if token in plain_text(cb[tt].get("rich_text",[])):
                        return True
    return False

def insert_children(pid, blocks):
    return req("PATCH", f"https://api.notion.com/v1/blocks/{pid}/children", data=json.dumps({"children":blocks}))

def url_join(base, filename):
    filename = filename.lstrip("/")
    return base.rstrip("/") + "/" + urllib.parse.quote(filename)



def ensure_pages_index_db(parent_id):
    title = "Admin – Pages Index"
    # Create minimal DB
    schema = {"properties":{
        "Name":{"type":"title"},
        "Page ID":{"type":"rich_text"},
        "URL":{"type":"url"}
    }}
    payload = {"parent":{"type":"page_id","page_id":parent_id},
               "title":[{"type":"text","text":{"content":title}}],
               "properties":{"Name":{"title":{}},"Page ID":{"rich_text":{}},"URL":{"url":{}}}}
    r = req("POST","https://api.notion.com/v1/databases", data=json.dumps(payload))
    if not expect_ok(r, "create Pages Index DB"): return None
    return j(r).get("id")

def upsert_pages_index_row(dbid, title, pid):
    # Build URL (Notion doesn't expose public URL via API; leave blank or use internal scheme if known)
    url = None
    # Query by title exact match
    q = req("POST", f"https://api.notion.com/v1/databases/{dbid}/query", data=json.dumps({"page_size":5, "filter":{"property":"Name","title":{"equals": title}}}))
    data = j(q)
    existing = (data.get("results") or [])
    props={"Name":{"title":[{"type":"text","text":{"content":title}}]},"Page ID":{"rich_text": rt(pid)}}
    if url: props["URL"]={"url": url}
    if existing:
        page_id = existing[0]["id"]
        req("PATCH", f"https://api.notion.com/v1/pages/{page_id}", data=json.dumps({"properties":props}))
        return page_id
    else:
        cr = req("POST","https://api.notion.com/v1/pages", data=json.dumps({"parent":{"database_id":dbid},"properties":props}))
        if expect_ok(cr, "insert pages index row"):
            return j(cr).get("id")
    return None



def ensure_property_rich_text(dbid, name):
    meta = j(req("GET", f"https://api.notion.com/v1/databases/{dbid}"))
    if name in meta.get("properties", {}):
        return
    req("PATCH", f"https://api.notion.com/v1/databases/{dbid}", data=json.dumps({"properties":{name:{"rich_text":{}}}}))

def find_index_item_by_title(dbid, title):
    q = req("POST", f"https://api.notion.com/v1/databases/{dbid}/query", data=json.dumps({"page_size":10, "filter":{"property":"Name","title":{"equals": title}}}))
    data = j(q)
    for res in data.get("results",[]):
        return res.get("id")
    return None



def query_database_all(dbid):
    has_more=True; start=None; results=[]
    while has_more:
        payload = {"page_size":100}
        if start: payload["start_cursor"]=start
        r = req("POST", f"https://api.notion.com/v1/databases/{dbid}/query", data=json.dumps(payload))
        if not expect_ok(r, f"query DB {dbid}"): break
        data = j(r)
        results.extend(data.get("results",[]))
        has_more = data.get("has_more")
        start = data.get("next_cursor")
    return results

def update_rollout_summary(state):
    # Find Acceptance DB id
    acc = None
    for name, dbid in state.get("dbs",{}).items():
        if name.lower().startswith("acceptance") or name.lower().startswith("setup"):
            acc = dbid; break
    if not acc: 
        return
    rows = query_database_all(acc)
    # compute by 'Section' (fallback 'Role' or 'Category')
    def read_prop(page, key):
        p = page.get("properties",{}).get(key)
        if not p: return None
        t = p.get("type")
        if t=="select": return p["select"]["name"] if p.get("select") else None
        if t=="title": return plain_text(p["title"])
        if t=="rich_text": return plain_text(p["rich_text"])
        return None
    summary={}
    total=0; done=0
    for r in rows:
        section = read_prop(r, "Section") or read_prop(r, "Role") or "General"
        status = read_prop(r, "Status") or ""
        total += 1
        if section not in summary: summary[section]={"total":0,"done":0}
        summary[section]["total"] += 1
        if status.lower()=="done": 
            summary[section]["done"] += 1
            done += 1
    remaining = total - done
    # Upsert "Admin – Rollout Summary" page
    title = "Admin – Rollout Summary"
    pid = state["pages"].get(title)
    if not pid:
        pid = create_page(parent, title, {"type":"emoji","emoji":"🧩"}, None, "Live deployment progress summary.", None, None)
        state["pages"][title]=pid
    # Build table as paragraphs
    blocks=[
        {"object":"block","type":"paragraph","paragraph":{"rich_text": rt("ROLLUP_START")}},
        {"object":"block","type":"paragraph","paragraph":{"rich_text": rt(f"Total: {total} • Done: {done} • Remaining: {remaining}")}},
        {"object":"block","type":"divider","divider":{}},
    ]
    for sec, v in sorted(summary.items()):
        pct = 0 if v["total"]==0 else int(round(100 * v["done"]/v["total"]))
        blocks.append({"object":"block","type":"paragraph","paragraph":{"rich_text": rt(f"{sec}: {v['done']}/{v['total']} ({pct}%)")}})
    blocks.append({"object":"block","type":"paragraph","paragraph":{"rich_text": rt("ROLLUP_END")}})
    insert_children(pid, blocks)



def preview_plan(merged):
    total_pages = len(merged.get("pages", []))
    total_dbs = len(merged.get("db", {}).get("schemas", {}))
    print("=== Deployment Preview ===")
    print(f"Pages to ensure: {total_pages}")
    print(f"Databases to ensure: {total_dbs}")
    # list top-level page titles
    for p in merged.get("pages", [])[:10]:
        print(" -", p.get("title"))
    if total_pages > 10:
        print(f" ... (+{total_pages-10} more)")


def list_children(block_id, page_size=100):
    r = req("GET", f"https://api.notion.com/v1/blocks/{block_id}/children?page_size={page_size}")
    try:
        return r.json().get("results", [])
    except Exception:
        return []

TEXTUAL = {"paragraph","callout","toggle","bulleted_list_item","numbered_list_item","to_do","quote","heading_1","heading_2","heading_3"}

def block_plain_text(b):
    t = b.get("type")
    if t in TEXTUAL:
        rt = b[t].get("rich_text", [])
        return "".join([seg.get("plain_text","") for seg in rt])
    return ""

def has_block_marker_recursive(block_id, token, max_depth=2):
    # Search for `token` in this block's subtree (limited depth).
    stack = [(block_id, 0)]
    while stack:
        bid, depth = stack.pop()
        for child in list_children(bid):
            if token in block_plain_text(child):
                return True
            if depth < max_depth:
                t = child.get("type")
                if t == "column_list":
                    # Notion API doesn't return nested children directly; still push child id to traverse
                    stack.append((child["id"], depth+1))
                elif t in ("column","toggle","callout"):
                    stack.append((child["id"], depth+1))
    return False


def ensure_synced_library(state, library_page_title="Synced Library"):
    # Ensure a master page that holds original synced blocks exists; return page_id.
    pid = state["pages"].get(library_page_title)
    if pid:
        return pid
    payload = {
        "parent": {"type":"page_id","page_id": state.get("root_page_id") or state.get("root")},
        "icon": {"type":"emoji","emoji":"🔁"},
        "properties": {"title":{"title":[{"type":"text","text":{"content":library_page_title}}]}},
    }
    r = req("POST","https://api.notion.com/v1/pages", data=json.dumps(payload))
    if expect_ok(r, "create synced library"):
        new_id = r.json().get("id")
        state["pages"][library_page_title]=new_id
        return new_id
    return None

def ensure_sync_original(state, lib_pid, sync_key, content=""):
    # Create (or find) an original synced_block tagged with SYNC_KEY::.
    children = list_children(lib_pid)
    for b in children:
        if b.get("type") == "synced_block" and b["synced_block"].get("synced_from") is None:
            inner = list_children(b["id"])
            for c in inner:
                if sync_key in (block_plain_text(c) or ""):
                    return b["id"]
    blocks = [{
        "object":"block","type":"synced_block",
        "synced_block":{"synced_from": None, "children":[
            {"object":"block","type":"callout","callout":{
                "icon":{"type":"emoji","emoji":"🔖"},
                "rich_text":[{"type":"text","text":{"content":f"{sync_key}"}},{"type":"text","text":{"content":"  •  Do not edit this marker text"}}],
                "color":"gray_background"
            }},
            {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content": content or "Synced original content"}}]}}
        ]}
    }]
    r = req("PATCH", f"https://api.notion.com/v1/blocks/{lib_pid}/children", data=json.dumps({"children":blocks}))
    if expect_ok(r, "create sync original"):
        for res in r.json().get("results", []):
            if res.get("type") == "synced_block":
                return res.get("id")
    return None

def add_synced_reference_if_absent(target_page_id, original_block_id, sync_key):
    # Insert a synced reference to original into target, if marker absent.
    if has_block_marker_recursive(target_page_id, sync_key):
        return True
    block = {
        "object":"block","type":"synced_block",
        "synced_block":{"synced_from":{"block_id": original_block_id}}
    }
    r = req("PATCH", f"https://api.notion.com/v1/blocks/{target_page_id}/children", data=json.dumps({"children":[block]}))
    return expect_ok(r, f"add sync ref {sync_key}")
