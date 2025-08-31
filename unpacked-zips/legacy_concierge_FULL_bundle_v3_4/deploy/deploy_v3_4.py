#!/usr/bin/env python3
# deploy_v3_4.py — Notion template deployer (split YAML + centralized undertone strings, 17 letters seeded)
# Usage:
#   python deploy_v3_4.py --dir split_yaml --dry-run
#   python deploy_v3_4.py --dir split_yaml --deploy
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

def blockify(blocks):
    def rt(t): return [{"type":"text","text":{"content":str(t)}}]
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
            for item in v: out.append({"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":rt(item)}})
        elif k=="numbered_list":
            for item in v: out.append({"object":"block","type":"numbered_list_item","numbered_list_item":{"rich_text":rt(item)}})
        elif k=="divider":
            out.append({"object":"block","type":"divider","divider":{}})
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
    st.write_text(json.dumps({"parent_page_id":pid},indent=2))
    return pid

def headers(token): return {"Authorization":f"Bearer {token}","Notion-Version":NOTION_VERSION,"Content-Type":"application/json"}

def create_db(token, parent_id, name, schema):
    props={k:{"type":t,t:{}} for k,t in (schema.get("properties") or {}).items()}
    payload={"parent":{"type":"page_id","page_id":parent_id},"title":[{"type":"text","text":{"content":name}}],"properties":props}
    r=requests.post(f"{NOTION_API}/databases", headers=headers(token), data=json.dumps(payload)); r.raise_for_status(); return r.json()["id"]

def create_page(token, parent_id, title, icon=None, cover=None, children=None):
    payload={"parent":{"type":"page_id","page_id":parent_id},"properties":{"title":{"title":[{"type":"text","text":{"content":title}}]}}}
    if icon: payload["icon"]=icon
    if cover: payload["cover"]={"type":"external","external":{"url":cover}}
    if children: payload["children"]=children
    r=requests.post(f"{NOTION_API}/pages", headers=headers(token), data=json.dumps(payload)); r.raise_for_status(); return r.json()["id"]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dir",required=True)
    ap.add_argument("--dry-run",action="store_true")
    ap.add_argument("--deploy",action="store_true")
    args=ap.parse_args()

    token=os.getenv("NOTION_TOKEN")
    if not token: print("Missing NOTION_TOKEN"); sys.exit(1)

    d=Path(args.dir)
    data=load_yaml_files(d)
    g=(data.get("globals.yaml") or {}).get("globals") or {}
    parent_id=get_parent_id(d)

    # plan
    plan={"dbs":[],"pages":[]}
    dbs=(data.get("databases.yaml") or {}).get("db") or {}
    for name, schema in (dbs.get("schemas") or {}).items():
        plan["dbs"].append({"name":name,"schema":schema,"seeds":(dbs.get("seeds") or {}).get(name)})
    for key in ("pages.yaml","subpages.yaml"):
        coll=(data.get(key) or {})
        arr = coll.get("pages") if key=="pages.yaml" else coll.get("subpages")
        for p in (arr or []):
            blocks=resolve_use_global(p.get("blocks"), g)
            disc=p.get("disclaimer")
            if isinstance(disc,str) and disc.startswith("use_global."): disc=resolve_use_global(disc,g)
            plan["pages"].append({**p,"blocks":blocks,"disclaimer":disc})

    print("=== PLAN ===")
    print(f"DBs: {len(plan['dbs'])}")
    print(f"Pages: {len(plan['pages'])}")
    if args.dry_run and not args.deploy:
        print("Dry-run only. Use --deploy to create in Notion.")
        return

    h=headers(token)
    icons=((g.get("icons_map") or {}))
    covers=((g.get("covers_map") or {}))

    # DBs
    for db in plan["dbs"]:
        print(f"Creating DB: {db['name']}")
        dbid=create_db(token, parent_id, db["name"], db["schema"])
        # seed rows
        seeds=db.get("seeds") or []
        for row in seeds:
            props={"Name":{"title":[{"type":"text","text":{"content":row.get('Title','')}}]}}
            for k,v in row.items():
                if k=="Title": continue
                props[k]={"rich_text":[{"type":"text","text":{"content":str(v)}}]}
            payload={"parent":{"database_id":dbid},"properties":props}
            r=requests.post(f"{NOTION_API}/pages", headers=h, data=json.dumps(payload)); r.raise_for_status()
        if seeds: print(f"  seeded {len(seeds)} rows")

    # Pages without parent
    slug_to_id={}
    for p in [x for x in plan["pages"] if not x.get("parent")]:
        slug=p.get("slug"); title=p["title"]
        icon = icons.get(slug); icon={"type":"emoji","emoji":icon} if icon else None
        cover = covers.get(slug)
        children=blockify(p.get("blocks"))
        print(f"Creating page: {title}")
        pid=create_page(token, parent_id, title, icon, cover, children)
        if slug: slug_to_id[slug]=pid

    # Subpages with parent
    for p in [x for x in plan["pages"] if x.get("parent")]:
        parent_slug=p["parent"]; pid=slug_to_id.get(parent_slug)
        if not pid: print(f"Warning: missing parent {parent_slug} for {p['title']}"); continue
        slug=p.get("slug"); title=p["title"]
        icon = icons.get(slug); icon={"type":"emoji","emoji":icon} if icon else None
        cover = covers.get(slug)
        children=blockify(p.get("blocks"))
        print(f"Creating subpage: {title} (parent={parent_slug})")
        cid=create_page(token, pid, title, icon, cover, children)
        if slug: slug_to_id[slug]=cid

    print("Deploy complete.")

if __name__=="__main__":
    main()
