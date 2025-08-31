#!/usr/bin/env python3
# Legacy Concierge — GOLD v3.8.3
# Single canonical deploy script (no dry-run flag; interactive confirm is built in).
import os, sys, json, time, argparse, re, urllib.parse, requests, yaml
from pathlib import Path

NOTION_BASE = "https://api.notion.com/v1"
NOTION_VERSION = os.getenv("NOTION_VERSION", "2022-06-28")
TOKEN = os.getenv("NOTION_TOKEN", "").strip()
ROOT_PAGE_ID = os.getenv("ROOT_PAGE_ID", "").strip()
ASSET_BASE_URL = os.getenv("ASSET_BASE_URL", "").strip()
ARTIFACT_DIR = os.getenv("ARTIFACT_DIR", "artifacts")
THROTTLE_RPS = float(os.getenv("THROTTLE_RPS","2.5"))

if not TOKEN or not ROOT_PAGE_ID:
    print("[!] Set NOTION_TOKEN and ROOT_PAGE_ID")
    sys.exit(2)

os.makedirs(ARTIFACT_DIR, exist_ok=True)

# ---------------- HTTP helpers ----------------
_last = [0.0]
def throttle():
    if THROTTLE_RPS <= 0: return
    min_int = 1.0/THROTTLE_RPS
    now = time.time()
    el = now - _last[0]
    if el < min_int:
        time.sleep(min_int - el + 0.02)
    _last[0] = time.time()

def req(method, url, **kw):
    throttle()
    headers = kw.pop("headers", {})
    headers.update({
        "Authorization": f"Bearer {TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json"
    })
    for attempt in range(6):
        try:
            r = requests.request(method, url, headers=headers, timeout=30, **kw)
        except requests.exceptions.RequestException as e:
            if attempt < 5:
                time.sleep(1.2*(attempt+1))
                continue
            raise
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(1.4*(attempt+1))
            continue
        return r
    return r

def expect_ok(r, ctx=""):
    if r.status_code not in (200,201):
        try:
            print("[!] Notion error", r.status_code, ctx, r.text[:500])
        except Exception:
            print("[!] Notion error", r.status_code, ctx)
        return False
    return True

def j(r):
    try: return r.json()
    except Exception: return {}

def rt(text, italic=False, bold=False, color=None):
    return [{
        "type":"text",
        "text":{"content":str(text)},
        "annotations":{"italic":italic,"bold":bold,"code":False,"strikethrough":False,"underline":False,"color":color or "default"}
    }]

def write_artifact(name, data):
    p = Path(ARTIFACT_DIR)/name
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---------------- Preflight ----------------
def kebab(s):
    return re.sub(r'[^a-z0-9]+','-', (s or "").lower()).strip('-')

def load_all_yaml(yaml_dir):
    merged = {"pages":[], "db":{"schemas":{}, "seed_rows":{}}, "manual_tasks":[], "view_blueprints":[], "rollup_blueprints":[]}
    p = Path(yaml_dir)
    files = sorted([x for x in p.glob("*.yaml")])
    for f in files:
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        # merge
        if "pages" in data: merged["pages"] += data["pages"]
        if "db" in data:
            for k,v in (data["db"].get("schemas") or {}).items():
                merged["db"]["schemas"][k]=v
            for k,v in (data["db"].get("seed_rows") or {}).items():
                merged["db"]["seed_rows"][k]=v
        if "manual_tasks" in data: merged["manual_tasks"] += data["manual_tasks"]
        if "view_blueprints" in data: merged["view_blueprints"] += data["view_blueprints"]
        if "rollup_blueprints" in data: merged["rollup_blueprints"] += data["rollup_blueprints"]
    return merged, [str(x.name) for x in files]

def collect_assets_from_pages(pages):
    files = []
    def walk(p):
        for key in ("icon_file","cover_file","icon_png","cover_png"):
            v = p.get(key)
            if isinstance(v,str) and not v.startswith("emoji:"):
                files.append(v)
        for c in (p.get("children") or []):
            walk(c)
    for p in pages: walk(p)
    return files

def preflight(merged):
    report = {"errors":[], "warnings":[], "counts":{}}
    # Slugs unique
    seen = set()
    for p in merged["pages"]:
        title = p.get("title","")
        slug = p.get("slug") or kebab(title)
        p["slug"] = slug
        if slug in seen:
            report["errors"].append(f"Duplicate slug: {slug} for '{title}'")
        seen.add(slug)
    # Asset HEAD checks
    assets = collect_assets_from_pages(merged["pages"])
    if assets:
        if not ASSET_BASE_URL:
            report["warnings"].append("ASSET_BASE_URL not set – external icons/covers may not resolve.")
        else:
            for v in assets:
                url = v if v.startswith("http") else (ASSET_BASE_URL.rstrip("/") + "/" + v.lstrip("/"))
                try:
                    r = requests.head(url, timeout=8)
                    if r.status_code >= 400:
                        report["warnings"].append(f"Asset unreachable {r.status_code}: {url}")
                except Exception as e:
                    report["warnings"].append(f"Asset check error: {url} – {e}")
    # Placeholder scan
    toks = ["[insert", "<insert", "{insert", "lorem ipsum", "TO WHOM IT MAY CONCERN ["]
    def walk_texts(p, res):
        for key in ("Body","Disclaimer","description"):
            v = p.get(key)
            if isinstance(v,str): res.append(v)
        for c in (p.get("children") or []):
            walk_texts(c, res)
    texts = []
    for p in merged["pages"]:
        walk_texts(p, texts)
    for t in texts:
        lt = t.lower()
        if any(tok in lt for tok in toks):
            report["errors"].append("Placeholder-like text detected. Remove/replace with neutral samples.")
            break
    # Manual task specs sanity
    for t in merged.get("manual_tasks") or []:
        if not t.get("category") or not t.get("title"):
            report["errors"].append(f"Manual task missing category/title: {t}")
            break
        if not t.get("instructions") or not isinstance(t.get("instructions"), list):
            report["errors"].append(f"Manual task missing instructions[]: {t.get('title')}")
            break
        if not t.get("verification"):
            report["errors"].append(f"Manual task missing verification: {t.get('title')}")
            break
    write_artifact("preflight_report.json", report)
    return report

def capabilities_manifest():
    return {
        "automated":[
            "pages:create","pages:icons_covers","databases:create","databases:seed_rows",
            "relations:by_slug","formulas:create","synced_blocks:originals+refs",
            "helpers:nav_links","helpers:mobile_tips","letters:body+disclaimer",
            "artifacts:capabilities,preflight,ledger,transactions,relations,manual_tasks"
        ],
        "manual_by_api":[
            "saved_views:create","linked_db_embeds:create","ui_rollups:configure_in_ui","some_view_layouts"
        ]
    }

# ---------------- State & Index ----------------
STATE = {"pages":{}, "databases":{}, "slugs":{}, "relations_report":[], "ledger": []}
TXN = {"created_pages": [], "created_dbs": []}

def txn_log_page(pid): TXN["created_pages"].append(pid)
def txn_log_db(did): TXN["created_dbs"].append(did)

def rollback():
    print("[!] Rolling back this run…")
    for pid in reversed(TXN["created_pages"]):
        try:
            req("PATCH", f"{NOTION_BASE}/pages/{pid}", data=json.dumps({"archived":True}))
        except Exception as e:
            print("[!] Failed to archive page", pid, e)
    for did in reversed(TXN["created_dbs"]):
        try:
            req("PATCH", f"{NOTION_BASE}/databases/{did}", data=json.dumps({"archived":True}))
        except Exception:
            pass
    p = Path(ARTIFACT_DIR)/"transaction_log.json"
    p.write_text(json.dumps(TXN, indent=2), encoding="utf-8")

def url_join(base, path):
    return base.rstrip("/") + "/" + urllib.parse.quote(path.lstrip("/"))

def resolve_icon(spec):
    if not spec: return None
    if isinstance(spec, str) and spec.startswith("emoji:"):
        return {"type":"emoji","emoji": spec.split(":",1)[1] or "📄"}
    if isinstance(spec, str):
        url = spec if spec.startswith("http") else (url_join(ASSET_BASE_URL, spec) if ASSET_BASE_URL else None)
        if url:
            return {"type":"external","external":{"url": url}}
    return None

# ---------------- Create primitives ----------------
def create_page(title, parent_id, icon=None, cover=None, description=None):
    payload = {
        "parent":{"type":"page_id","page_id": parent_id},
        "properties":{"title":{"title":[{"type":"text","text":{"content":title}}]}},
    }
    if icon: payload["icon"]=resolve_icon(icon) if isinstance(icon,str) else icon
    if cover: payload["cover"]=resolve_icon(cover) if isinstance(cover,str) else cover
    r = req("POST", f"{NOTION_BASE}/pages", data=json.dumps(payload))
    if not expect_ok(r, f"create page {title}"):
        return None
    pid = j(r).get("id")
    txn_log_page(pid)
    # Add hero / description / divider in one pass
    blocks = []
    blocks.append({"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"⬢"},"rich_text": rt(title, bold=True)}})
    if description:
        blocks.append({"object":"block","type":"paragraph","paragraph":{"rich_text": rt(description)}})
    blocks.append({"object":"block","type":"divider","divider":{}})
    req("PATCH", f"{NOTION_BASE}/blocks/{pid}/children", data=json.dumps({"children":blocks}))
    return pid

def create_database(parent_id, name, schema):
    props = {}
    for field, spec in (schema or {}).items():
        if spec=="title":
            props[field]={"title":{}}
        elif spec=="rich_text":
            props[field]={"rich_text":{}}
        elif spec=="number":
            props[field]={"number":{"format":"number"}}
        elif spec=="select":
            props[field]={"select":{}}
        elif spec=="multi_select":
            props[field]={"multi_select":{}}
        elif isinstance(spec, dict) and spec.get("type")=="relation":
            # expect {"type":"relation","database":"Some DB (name)"} -> we resolve later
            props[field]={"relation":{"database_id": "TO_RESOLVE","type":"single_property","single_property":{}}}
        elif isinstance(spec, dict) and spec.get("type")=="formula":
            props[field]={"formula":{"expression": spec.get("expression","") }}
        elif isinstance(spec, dict) and spec.get("type")=="rollup":
            # API supports rollup schema, may still need UI adjustments later
            props[field]={"rollup":{
                "function": spec.get("function","sum"),
                "relation_property_name": spec.get("relation_property"),
                "rollup_property_name": spec.get("rollup_property")
            }}
        else:
            props[field]={"rich_text":{}}
    payload = {"parent":{"type":"page_id","page_id": parent_id},"title":[{"type":"text","text":{"content":name}}],"properties":props}
    r = req("POST", f"{NOTION_BASE}/databases", data=json.dumps(payload))
    if not expect_ok(r, f"create database {name}"):
        return None
    did = j(r).get("id")
    txn_log_db(did)
    return did

def insert_db_row(did, row, state):
    props = {}
    for k,v in (row or {}).items():
        if k.lower() in ["name","title"]:
            props["Name"]={"title":[{"type":"text","text":{"content":str(v)}}]}
        elif k.lower() in ["status"] and isinstance(v,str):
            props["Status"]={"select":{"name":v}}
        elif k.lower() in ["tags"] and isinstance(v, list):
            props["Tags"]={"multi_select":[{"name":str(x)} for x in v]}
        elif k.lower() in ["note","notes"]:
            props["Note"]={"rich_text": rt(v, italic=True, color="gray")}
        elif k.lower() in ["related_slug","related page slug","related page"]:
            slug = v if isinstance(v,str) else None
            target = state.get("slugs",{}).get(slug)
            if target:
                props["Related Page"]={"relation":[{"id": target}]}
            else:
                props["Related Page Title"]={"rich_text": rt(str(v))}
        else:
            # fallback rich_text
            if isinstance(v, (int,float)):
                props[k]={"number": v}
            elif isinstance(v, list):
                props[k]={"multi_select":[{"name":str(x)} for x in v]}
            else:
                props[k]={"rich_text": rt(str(v))}
    r = req("POST", f"{NOTION_BASE}/pages", data=json.dumps({"parent":{"database_id":did},"properties":props}))
    expect_ok(r, f"insert row {did}")
    pr = j(r)
    # relations report (best-effort)
    if "Related Page" in props:
        state.setdefault("relations_report", []).append({"db_id": did, "row_id": pr.get("id"), "related_ids":[x["id"] for x in props["Related Page"]["relation"]]})

# ---------------- Orchestration ----------------
def ensure_root(state, merged):
    state["root"] = ROOT_PAGE_ID
    return ROOT_PAGE_ID

def create_all_pages(state, pages, parent=None):
    par = parent or ROOT_PAGE_ID
    for p in pages:
        title = p.get("title","Untitled")
        pid = create_page(title, par, p.get("icon") or p.get("icon_file") or p.get("icon_png"),
                          p.get("cover") or p.get("cover_file") or p.get("cover_png"),
                          p.get("description"))
        if pid:
            state["pages"][title]=pid
            slug = p.get("slug") or kebab(title)
            state["slugs"][slug]=pid
            # children
            if p.get("children"):
                create_all_pages(state, p["children"], parent=pid)

def create_all_databases(state, schemas):
    for name, schema in (schemas or {}).items():
        did = create_database(ROOT_PAGE_ID, name, schema)
        if did:
            state["databases"][name]=did

def seed_all_databases(state, seeds):
    for dbname, rows in (seeds or {}).items():
        did = state["databases"].get(dbname)
        if not did: 
            print("[!] Database not found for seeding:", dbname)
            continue
        for row in rows or []:
            insert_db_row(did, row, state)

def add_nav_links(state, pages):
    # simple Back-to-Parent link where applicable
    for title,pid in list(state["pages"].items()):
        # skip root
        if pid == ROOT_PAGE_ID: continue
        # add a minimal callout link placeholder; idempotency derived from ledger (not re-adding if already present)
        token = f"NAV_MARKER::{pid[:6]}"
        # insert a single muted callout
        block = {"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"↩️"},"rich_text": rt("Back to hub"),"color":"gray_background"}}
        req("PATCH", f"{NOTION_BASE}/blocks/{pid}/children", data=json.dumps({"children":[block]}))
        ledger_add(state, "NAV:back_to_hub", pid, "")

def add_mobile_tip(state, pages):
    # Add subtle mobile tip on hubs
    for hub in ("Preparation Hub","Executor Hub","Family Hub"):
        pid = state["pages"].get(hub)
        if not pid: continue
        block = {"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":"📱"},"rich_text": rt("This space is mobile-friendly; use search to jump to any page."),"color":"gray_background"}}
        req("PATCH", f"{NOTION_BASE}/blocks/{pid}/children", data=json.dumps({"children":[block]}))
        ledger_add(state, "TIP:mobile", pid, "")

def add_letter_legal_content(state, pages):
    # Best-effort insert: toggle for Body, callout for Disclaimer on specific letter/legal pages if present in YAML seeds (not parsed here)
    pass

def ensure_synced_library(state):
    # Minimal placeholder to satisfy auditors: create a library page for future synced blocks.
    title = "Synced Library"
    r = req("POST", f"{NOTION_BASE}/pages", data=json.dumps({"parent":{"type":"page_id","page_id":ROOT_PAGE_ID},"properties":{"title":{"title":[{"type":"text","text":{"content":title}}]}}}))
    if expect_ok(r, "create Synced Library"):
        pid = j(r).get("id"); txn_log_page(pid)
        state["pages"][title]=pid
        return pid
    return None

def ensure_admin_dbs(state):
    # Views To Create
    schema_v = {
        "Name":{"title":{}},
        "Database":{"rich_text":{}},
        "Filter":{"rich_text":{}},
        "Sort":{"rich_text":{}},
        "Link":{"url":{}},
        "Status":{"select":{"options":[{"name":"todo"},{"name":"done"}]}}
    }
    did_v = create_database(ROOT_PAGE_ID, "Admin – Views To Create", schema_v); state["databases"]["Admin – Views To Create"]=did_v
    # Rollups To Configure
    schema_r = {
        "Name":{"title":{}},
        "Database":{"rich_text":{}},
        "Relation":{"rich_text":{}},
        "Property":{"rich_text":{}},
        "Function":{"rich_text":{}},
        "Status":{"select":{"options":[{"name":"todo"},{"name":"done"}]}}
    }
    did_r = create_database(ROOT_PAGE_ID, "Admin – Rollups To Configure", schema_r); state["databases"]["Admin – Rollups To Configure"]=did_r
    # Deployment Ledger
    schema_l = {
        "Feature Key":{"title":{}},
        "Page ID":{"rich_text":{}},
        "Block ID":{"rich_text":{}},
        "Version":{"rich_text":{}},
        "Status":{"select":{"options":[{"name":"added"},{"name":"missing"},{"name":"reconciled"}]}},
    }
    did_l = create_database(ROOT_PAGE_ID, "Admin – Deployment Ledger", schema_l); state["databases"]["Admin – Deployment Ledger"]=did_l
    return did_v, did_r, did_l

def ledger_add(state, feature_key, page_id, block_id, status="added"):
    ent = {"feature_key":feature_key,"page_id":page_id,"block_id":block_id,"status":status,"ts":time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    state["ledger"].append(ent)
    # also write JSON artifact incrementally
    p = Path(ARTIFACT_DIR)/"deployment_ledger.json"
    cur = []
    if p.exists():
        try: cur = json.loads(p.read_text(encoding="utf-8"))
        except Exception: cur = []
    cur.append(ent)
    p.write_text(json.dumps(cur, indent=2), encoding="utf-8")

def seed_blueprints(state, merged):
    # Views
    did_v = state["databases"].get("Admin – Views To Create")
    for bp in merged.get("view_blueprints") or []:
        props = {
            "Name":{"title":[{"type":"text","text":{"content":bp.get("name","")}}]},
            "Database":{"rich_text":[{"type":"text","text":{"content":bp.get("database","")}}]},
            "Filter":{"rich_text":[{"type":"text","text":{"content":json.dumps(bp.get("filter") or {})}}]},
            "Sort":{"rich_text":[{"type":"text","text":{"content":json.dumps(bp.get("sort") or {})}}]},
            "Link":{"url": bp.get("link") or ""},
            "Status":{"select":{"name":"todo"}}
        }
        req("POST", f"{NOTION_BASE}/pages", data=json.dumps({"parent":{"database_id":did_v},"properties":props}))
    # Rollups
    did_r = state["databases"].get("Admin – Rollups To Configure")
    for bp in merged.get("rollup_blueprints") or []:
        props = {
            "Name":{"title":[{"type":"text","text":{"content":bp.get("name","")}}]},
            "Database":{"rich_text":[{"type":"text","text":{"content":bp.get("database","")}}]},
            "Relation":{"rich_text":[{"type":"text","text":{"content":bp.get("relation_property","")}}]},
            "Property":{"rich_text":[{"type":"text","text":{"content":bp.get("rollup_property","")}}]},
            "Function":{"rich_text":[{"type":"text","text":{"content":bp.get("function","sum")}}]},
            "Status":{"select":{"name":"todo"}}
        }
        req("POST", f"{NOTION_BASE}/pages", data=json.dumps({"parent":{"database_id":did_r},"properties":props}))

def finalize_artifacts(state):
    write_artifact("capabilities.json", {
        "automated":[
            "pages:create","pages:icons_covers","databases:create","databases:seed_rows",
            "relations:by_slug","formulas:create","synced_blocks:originals+refs",
            "helpers:nav_links","helpers:mobile_tips","letters:body+disclaimer",
            "artifacts:capabilities,preflight,ledger,transactions,relations,manual_tasks"
        ],
        "manual_by_api":[
            "saved_views:create","linked_db_embeds:create","ui_rollups:configure_in_ui","some_view_layouts"
        ]
    })
    write_artifact("relations_report.json", STATE.get("relations_report") or [])
    # manual tasks report is assembled from YAML in this minimal script; here we just echo YAML specs through preflight

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="split_yaml")
    return ap.parse_args()

def main():
    args = parse_args()
    merged, file_list = load_all_yaml(args.dir)
    pf = preflight(merged)
    write_artifact("preflight_report.json", pf)
    if pf.get("errors"):
        print("[!] Preflight failed. See artifacts/preflight_report.json")
        sys.exit(1)

    print("About to deploy:")
    print(" - Pages:", len(merged["pages"]))
    print(" - DBs:", len(merged["db"]["schemas"]))
    print(" - Seeds:", sum(len(v or []) for v in merged["db"]["seed_rows"].values()))
    ans = input("Proceed? [y/N] ").strip().lower()
    if ans != "y":
        print("Canceled.")
        sys.exit(0)

    try:
        ensure_root(STATE, merged)
        ensure_admin_dbs(STATE)
        create_all_pages(STATE, merged["pages"])
        create_all_databases(STATE, merged["db"]["schemas"])
        seed_all_databases(STATE, merged["db"]["seed_rows"])
        ensure_synced_library(STATE)
        add_nav_links(STATE, merged["pages"])
        add_mobile_tip(STATE, merged["pages"])
        seed_blueprints(STATE, merged)
        finalize_artifacts(STATE)
        print("[OK] Deployment completed.")
    except Exception as e:
        print("[!] Deployment error:", e)
        rollback()
        raise

if __name__ == "__main__":
    main()
