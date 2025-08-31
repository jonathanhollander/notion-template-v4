#!/usr/bin/env python3
# deploy_v3_3.py — Notion template deployer (split YAML + centralized strings, undertone copy integrated)
# Usage:
#   python deploy_v3_3.py --dir split_yaml --dry-run
#   python deploy_v3_3.py --dir split_yaml --deploy

import os, sys, json, argparse
from pathlib import Path
import requests, yaml

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = os.getenv("NOTION_VERSION", "2022-06-28")
STATE_FILE = ".deploy_state.json"

def load_yaml_files(directory: Path):
    order = ["meta.yaml","globals.yaml","databases.yaml","pages.yaml","subpages.yaml","diagnostics.yaml","acceptance.yaml","addons.yaml","admin.yaml"]
    data = {}
    for name in order:
        p = directory / name
        if p.exists():
            data[name] = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        else:
            data[name] = {}
    return data

def resolve_use_global(value, globals_obj):
    if isinstance(value, str) and value.startswith("use_global."):
        parts = value.split(".")[1:]
        obj = globals_obj
        for part in parts:
            obj = obj[part]
        return obj
    if isinstance(value, list):
        return [resolve_use_global(v, globals_obj) for v in value]
    if isinstance(value, dict):
        return {k: resolve_use_global(v, globals_obj) for k,v in value.items()}
    return value

def blockify(blocks):
    def rt(txt): return [{"type":"text","text":{"content":str(txt)}}]
    out=[]
    for b in blocks or []:
        if not isinstance(b, dict) or len(b)!=1: continue
        (k,v),=b.items()
        if k in ("h1","h2","h3"):
            t = {"h1":"heading_1","h2":"heading_2","h3":"heading_3"}[k]
            out.append({"object":"block","type":t, t:{"rich_text":rt(v)}})
        elif k=="p":
            out.append({"object":"block","type":"paragraph","paragraph":{"rich_text":rt(v)}})
        elif k=="callout":
            out.append({"object":"block","type":"callout","callout":{"rich_text":rt(v),"icon":{"type":"emoji","emoji":"💡"}}})
        elif k=="bulleted_list":
            for item in (v or []):
                out.append({"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":rt(item)}})
        elif k=="numbered_list":
            for item in (v or []):
                out.append({"object":"block","type":"numbered_list_item","numbered_list_item":{"rich_text":rt(item)}})
        elif k=="divider":
            out.append({"object":"block","type":"divider","divider":{}})
        else:
            out.append({"object":"block","type":"paragraph","paragraph":{"rich_text":rt(f'{k}: {v}')}})
    return out

def get_parent_page_id(d: Path):
    env = os.getenv("NOTION_PARENT_PAGEID")
    if env: return env
    state_path = d / STATE_FILE
    if state_path.exists():
        try:
            st=json.loads(state_path.read_text())
            if st.get("parent_page_id"): return st["parent_page_id"]
        except: pass
    parent = input("Enter NOTION parent page ID: ").strip()
    state_path.write_text(json.dumps({"parent_page_id":parent}, indent=2))
    return parent

def headers(token): 
    return {"Authorization":f"Bearer {token}","Notion-Version":NOTION_VERSION,"Content-Type":"application/json"}

def create_db(token, parent_id, title, schema):
    props = {k:{"type":t, t:{}} for k,t in (schema.get("properties") or {}).items()}
    payload={"parent":{"type":"page_id","page_id":parent_id},"title":[{"type":"text","text":{"content":title}}],"properties":props}
    r=requests.post(f"{NOTION_API}/databases", headers=headers(token), data=json.dumps(payload)); r.raise_for_status(); return r.json()["id"]

def create_page(token, parent_id, title, icon=None, cover=None, children=None):
    payload={"parent":{"type":"page_id","page_id":parent_id},"properties":{"title":{"title":[{"type":"text","text":{"content":title}}]}}}
    if icon: payload["icon"]=icon
    if cover: payload["cover"]={"type":"external","external":{"url":cover}}
    if children: payload["children"]=children
    r=requests.post(f"{NOTION_API}/pages", headers=headers(token), data=json.dumps(payload)); r.raise_for_status(); return r.json()["id"]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--deploy", action="store_true")
    args=ap.parse_args()

    token=os.getenv("NOTION_TOKEN")
    if not token: print("Missing NOTION_TOKEN"); sys.exit(1)

    d=Path(args.dir)
    data=load_yaml_files(d)
    globals_obj=(data.get("globals.yaml") or {}).get("globals") or {}
    addons=data.get("addons.yaml") or {}
    parent_page_id=get_parent_page_id(d)

    # Plan
    plan={"databases":[], "pages":[]}
    db_section=(data.get("databases.yaml") or {}).get("db") or {}
    for name,schema in (db_section.get("schemas") or {}).items():
        plan["databases"].append({"name":name,"schema":schema,"seed":(db_section.get("seeds") or {}).get(name)})
    for name in ("pages.yaml","subpages.yaml"):
        collection=(data.get(name) or {})
        key="pages" if name=="pages.yaml" else "subpages"
        for p in (collection.get(key) or []):
            blocks=resolve_use_global(p.get("blocks"), globals_obj)
            disc = p.get("disclaimer")
            if isinstance(disc,str) and disc.startswith("use_global."):
                disc = resolve_use_global(disc, globals_obj)
            plan["pages"].append({**p, "blocks":blocks, "disclaimer":disc})

    print("=== PLAN ===")
    print(f"DBs: {len(plan['databases'])}")
    print(f"Pages: {len(plan['pages'])}")
    if not args.deploy:
        print("Dry-run only. Use --deploy to create in Notion.")
        return

    # Deploy
    h=headers(token)
    slug_to_id={}
    icons = ((globals_obj.get("icons_map") or {}) | ((addons.get("assets") or {}).get("icons") or {}))
    covers = ((globals_obj.get("covers_map") or {}) | ((addons.get("assets") or {}).get("covers") or {}))

    # DBs
    for db in plan["databases"]:
        print(f"Creating DB: {db['name']}")
        dbid=create_db(token, parent_page_id, db["name"], db["schema"])
        # seed rows best-effort
        seeds=db.get("seed") or []
        for row in seeds:
            props={"Name":{"title":[{"type":"text","text":{"content":row.get('Title','')}}]}}
            for k,v in row.items():
                if k=="Title": continue
                props[k]={"rich_text":[{"type":"text","text":{"content":str(v)}}]}
            payload={"parent":{"database_id":dbid},"properties":props}
            r=requests.post(f"{NOTION_API}/pages", headers=h, data=json.dumps(payload)); r.raise_for_status()
        if seeds: print(f"  seeded {len(seeds)} rows")

    # Pages (create when no parent key first)
    for p in [x for x in plan["pages"] if not x.get("parent")]:
        slug=p.get("slug"); title=p["title"]
        icon = icons.get(slug); icon = {"type":"emoji","emoji":icon} if icon else None
        cover = covers.get(slug)
        children = blockify(p.get("blocks"))
        print(f"Creating page: {title}")
        pid=create_page(token, parent_page_id, title, icon, cover, children)
        if slug: slug_to_id[slug]=pid

    # Subpages
    for p in [x for x in plan["pages"] if x.get("parent")]:
        parent_slug=p["parent"]; parent_id=slug_to_id.get(parent_slug)
        if not parent_id:
            print(f"Warning: parent {parent_slug} not found for {p['title']}"); continue
        slug=p.get("slug"); title=p["title"]
        icon = icons.get(slug); icon = {"type":"emoji","emoji":icon} if icon else None
        cover = covers.get(slug)
        children = blockify(p.get("blocks"))
        print(f"Creating subpage: {title} (parent={parent_slug})")
        pid=create_page(token, parent_id, title, icon, cover, children)
        if slug: slug_to_id[slug]=pid

    print("Deploy complete.")

if __name__=="__main__":
    main()
