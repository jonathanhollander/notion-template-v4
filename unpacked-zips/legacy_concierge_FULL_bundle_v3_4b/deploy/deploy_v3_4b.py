#!/usr/bin/env python3
# deploy_v3_4b.py — supports link_to_database blocks by database name

import os, sys, json, argparse
from pathlib import Path
import requests, yaml

NOTION_API="https://api.notion.com/v1"
NOTION_VERSION=os.getenv("NOTION_VERSION","2022-06-28")
STATE_FILE=".deploy_state.json"

def load_yaml_files(d:Path):
    names=["meta.yaml","globals.yaml","databases.yaml","pages.yaml","subpages.yaml","diagnostics.yaml","acceptance.yaml","addons.yaml","admin.yaml"]
    data={}
    for n in names:
        p=d/n
        data[n]=yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}
    return data

def resolve_use_global(value, g):
    if isinstance(value,str) and value.startswith("use_global."):
        parts=value.split(".")[1:]
        obj=g
        for part in parts: obj=obj[part]
        return obj
    if isinstance(value,list): return [resolve_use_global(v,g) for v in value]
    if isinstance(value,dict): return {k:resolve_use_global(v,g) for k,v in value.items()}
    return value

def rt(t): return [{"type":"text","text":{"content":str(t)}}]

def blockify(blocks, db_ids_by_name):
    out=[]
    for b in blocks or []:
        if not isinstance(b,dict) or len(b)!=1: continue
        (k,v),=b.items()
        if k in ("h1","h2","h3"):
            t={"h1":"heading_1","h2":"heading_2","h3":"heading_3"}[k]
            out.append({"object":"block","type":t,t:{"rich_text":rt(v)}})
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
        elif k=="linked_db":
            # v is {"name":"owner_progress"}
            name = v.get("name") if isinstance(v, dict) else str(v)
            dbid = db_ids_by_name.get(name)
            if dbid:
                out.append({"object":"block","type":"link_to_database","link_to_database":{"database_id":dbid}})
            else:
                out.append({"object":"block","type":"callout","callout":{"rich_text":rt(f"[Link could not be created automatically: database '{name}' not found.]")}})
        else:
            out.append({"object":"block","type":"paragraph","paragraph":{"rich_text":rt(f'{k}: {v}')}})
    return out

def get_parent_id(d:Path):
    env=os.getenv("NOTION_PARENT_PAGEID")
    if env: return env
    st=d/STATE_FILE
    if st.exists():
        try:
            j=json.loads(st.read_text()); pid=j.get("parent_page_id")
            if pid: return pid
        except: pass
    pid=input("Enter NOTION parent page ID: ").strip()
    st.write_text(json.dumps({"parent_page_id":pid}, indent=2))
    return pid

def headers(token): return {"Authorization":f"Bearer {token}","Notion-Version":NOTION_VERSION,"Content-Type":"application/json"}

def create_db(token, parent_id, name, schema):
    props={}
    for k,t in (schema.get("properties") or {}).items():
        if t=="title": props[k]={"title":{}}
        elif t=="select": props[k]={"select":{"options":[{"name":o} for o in (schema.get("options",{}).get(k,[]) if isinstance(schema.get('options',{}).get(k,[]), list) else [])]}}
        else: props[k]={t:{}}
    payload={"parent":{"type":"page_id","page_id":parent_id},"title":[{"type":"text","text":{"content":name}}],"properties":props}
    r=requests.post(f"{NOTION_API}/databases", headers=headers(token), data=json.dumps(payload)); r.raise_for_status(); return r.json()["id"]

def seed_db_rows(token, dbid, rows):
    if not rows: return 0
    h=headers(token); n=0
    for row in rows:
        props={}
        for k,v in row.items():
            if k=="Page":
                props["Page"]={"title":[{"type":"text","text":{"content":str(v)}}]}
            elif isinstance(v,str):
                props[k]={"rich_text":[{"type":"text","text":{"content":v}}]}
            else:
                props[k]={"rich_text":[{"type":"text","text":{"content":json.dumps(v)}}]}
        payload={"parent":{"database_id":dbid},"properties":props}
        r=requests.post(f"{NOTION_API}/pages", headers=h, data=json.dumps(payload)); r.raise_for_status(); n+=1
    return n

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
    g=(data.get("globals.yaml") or {}).get("globals") or {}
    parent_id=get_parent_id(d)

    plan={"dbs":[], "pages":[]}
    db_defs=(data.get("databases.yaml") or {}).get("db") or {}
    schemas=(db_defs.get("schemas") or {})
    seeds=(db_defs.get("seeds") or {})
    for name, schema in schemas.items():
        plan["dbs"].append({"name":name,"schema":schema,"seed_rows": (schema.get("seed_rows") or []), "seeds": seeds.get(name)})
    for key in ("pages.yaml","subpages.yaml"):
        coll=(data.get(key) or {})
        arr = coll.get("pages") if key=="pages.yaml" else coll.get("subpages")
        for p in (arr or []):
            plan["pages"].append(p)

    print("=== PLAN ===")
    print(f"DBs: {len(plan['dbs'])}")
    print(f"Pages: {len(plan['pages'])}")
    if args.dry_run and not args.deploy:
        print("Dry-run only. Use --deploy to create in Notion.")
        return

    # Create DBs first, collect ids by name
    db_ids_by_name={}
    for db in plan["dbs"]:
        print(f"Creating DB: {db['name']}")
        dbid=create_db(token, parent_id, db["name"], db["schema"])
        db_ids_by_name[db["name"]] = dbid
        # seed built-in rows
        count = seed_db_rows(token, dbid, db.get("seed_rows"))
        if count: print(f"  seeded {count} initial rows")
        # seed standard seeds (if present)
        if db.get("seeds"):
            from requests import post
            h=headers(token)
            for row in db["seeds"]:
                props={"Name":{"title":[{"type":"text","text":{"content":row.get('Title','')}}]}}
                for k,v in row.items():
                    if k=="Title": continue
                    props[k]={"rich_text":[{"type":"text","text":{"content":str(v)}}]}
                payload={"parent":{"database_id":dbid},"properties":props}
                r=post(f"{NOTION_API}/pages", headers=h, data=json.dumps(payload)); r.raise_for_status()

    # Create pages
    icons=(g.get("icons_map") or {})
    covers=(g.get("covers_map") or {})
    slug_to_id={}
    from copy import deepcopy

    # Resolve globals into blocks at runtime (so link_to_database can find db ids)
    def resolve_blocks(p):
        blocks= p.get("blocks") or []
        # resolve use_global first
        def resolve_use_global_value(v):
            if isinstance(v,str) and v.startswith("use_global."):
                obj=g
                for part in v.split(".")[1:]: obj=obj[part]
                return obj
            if isinstance(v,list):
                return [resolve_use_global_value(x) for x in v]
            if isinstance(v,dict):
                return {kk: resolve_use_global_value(vv) for kk,vv in v.items()}
            return v
        resolved=[{k: resolve_use_global_value(v)} for blk in blocks for k,v in blk.items()]
        return blockify(resolved, db_ids_by_name)

    # pages without parent
    for p in [x for x in plan["pages"] if not x.get("parent")]:
        slug=p.get("slug"); title=p["title"]
        icon=icons.get(slug); icon={"type":"emoji","emoji":icon} if icon else None
        cover=covers.get(slug)
        children=resolve_blocks(p)
        print(f"Creating page: {title}")
        pid=create_page(token, parent_id, title, icon, cover, children)
        if slug: slug_to_id[slug]=pid

    # subpages
    for p in [x for x in plan["pages"] if x.get("parent")]:
        parent_slug=p["parent"]; pid=slug_to_id.get(parent_slug)
        if not pid:
            print(f"Warning: parent {parent_slug} not found for {p['title']}"); continue
        slug=p.get("slug"); title=p["title"]
        icon=icons.get(slug); icon={"type":"emoji","emoji":icon} if icon else None
        cover=covers.get(slug)
        children=resolve_blocks(p)
        print(f"Creating subpage: {title} (parent={parent_slug})")
        cid=create_page(token, pid, title, icon, cover, children)
        if slug: slug_to_id[slug]=cid

    print("Deploy complete.")

if __name__=="__main__":
    main()
