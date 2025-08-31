#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compact deploy script (v2) — full functionality in a single file.
"""
import os, sys, time, json, datetime, logging, requests, yaml
from notion_client import Client
from notion_client.errors import APIResponseError

LOGFILE="deploy.log"; CONFIG_FILE=".notion_parent_id"
EM={"PLAN":"🟨","INFO":"ℹ️","CREATE":"✅","WARN":"⚠️","RETRY":"🔁","SKIP":"↩︎","ERROR":"❌","TRACK":"🧭"}
def log_setup(): logging.basicConfig(level=logging.INFO, format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(LOGFILE, encoding="utf-8")])
def echo(m): logging.info(m)
def get_parent_id():
    if os.path.exists(CONFIG_FILE): return open(CONFIG_FILE,"r",encoding="utf-8").read().strip()
    pid=input("Enter Notion parent page ID: ").strip(); open(CONFIG_FILE,"w",encoding="utf-8").write(pid); return pid
tok=os.getenv("NOTION_TOKEN"); 
if not tok: print("ERROR: set NOTION_TOKEN"); sys.exit(1)
if len(sys.argv)<2: print("USAGE: python deploy_notion_template.py spec.v2.yml"); sys.exit(1)
SPEC=sys.argv[1]; 
if not os.path.exists(SPEC): print(f"ERROR: Spec file not found: {SPEC}"); sys.exit(1)
cli=Client(auth=tok); V=cli._client.options.get("notion_version") or "2022-06-28"
HDR={"Authorization":f"Bearer {tok}","Notion-Version":V}

def retry(fn,*a,**k):
    for i in range(6):
        try: return fn(*a,**k)
        except APIResponseError as e:
            if e.status in (429,502,503): echo(f"{EM['RETRY']} Retrying ({e.status}) … attempt {i+1}/6"); time.sleep(0.9*(i+1)); continue
            raise

def norm(x): return x.replace("-","") if isinstance(x,str) else x
def nurl(pid): return f"https://www.notion.so/{norm(pid)}"
def upload_file(path, ctype=None):
    fn=os.path.basename(path); payload={"filename":fn}; 
    if ctype: payload["content_type"]=ctype
    r=requests.post("https://api.notion.com/v1/file_uploads", json=payload, headers={**HDR,"Content-Type":"application/json"})
    if r.status_code!=200: raise RuntimeError(f"File create failed: {r.status_code} {r.text}")
    up=r.json(); url=up["upload_url"]
    with open(path,"rb") as fh: r2=requests.post(url, files={"file":(fn, fh, ctype or "application/octet-stream")}, headers={**HDR})
    if r2.status_code not in (200,201,204): raise RuntimeError(f"File send failed: {r2.status_code} {r2.text}")
    return {"type":"file_upload","file_upload":{"id": up["id"]}}

def ptitle(props): t=props.get("title",{}).get("title",[]); return t[0]["plain_text"] if t else ""
def find_page(parent,title):
    res=retry(cli.search, query=title, filter={"value":"page","property":"object"})
    for r in res.get("results",[]): 
        if r["object"]!="page": continue
        par=r.get("parent",{})
        if par.get("type")=="page_id" and norm(par["page_id"])==norm(parent):
            if ptitle(r.get("properties",{})).strip().lower()==title.strip().lower(): return r
    return None
def find_db(parent,title):
    res=retry(cli.search, query=title, filter={"value":"database","property":"object"})
    for r in res.get("results",[]): 
        if r["object"]!="database": continue
        par=r.get("parent",{})
        if par.get("type")=="page_id" and norm(par["page_id"])==norm(parent):
            t=r.get("title",[]); text=t[0]["plain_text"] if t else ""
            if text.strip().lower()==title.strip().lower(): return r
    return None

def rt(t): return [{"type":"text","text":{"content":t}}]
def h2(t): return {"object":"block","type":"heading_2","heading_2":{"rich_text":rt(t)}}
def p(t): return {"object":"block","type":"paragraph","paragraph":{"rich_text":rt(t)}}
def co(t, e="💡"): return {"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":e},"rich_text":rt(t)}}
def td(t, c=False): return {"object":"block","type":"to_do","to_do":{"rich_text":rt(t),"checked":bool(c)}}
def code(t, lang="mermaid"): return {"object":"block","type":"code","code":{"language":lang,"rich_text":rt(t)}}
def div(): return {"object":"block","type":"divider","divider":{}}
def link_db(dbid): return {"object":"block","type":"link_to_page","link_to_page":{"type":"database_id","database_id":dbid}}
def toc(): return {"object":"block","type":"table_of_contents","table_of_contents":{}}

def enc_prop(prop):
    t=prop["type"]
    if t=="title": return {"title":{}}
    if t=="rich_text": return {"rich_text":{}}
    if t=="select": return {"select":{"options":[{"name":o} for o in prop.get("options",[])]}}
    if t=="multi_select": return {"multi_select":{"options":[{"name":o} for o in prop.get("options",[])]}}
    if t=="checkbox": return {"checkbox":{}}
    if t=="date": return {"date":{}}
    if t=="email": return {"email":{}}
    if t=="phone_number": return {"phone_number":{}}
    if t=="url": return {"url":{}}
    if t=="files": return {"files":{}}
    if t=="number": return {"number":{"format":"number"}}
    if t=="last_edited_time": return {"last_edited_time":{}}
    if t=="relation": return {"relation":{"database_id": None}}
    if t=="formula": return {"formula":{"expression": prop.get("expression","")}}
    raise ValueError("Unsupported property type")

def db_title_key(dbid):
    props=retry(cli.databases.retrieve, database_id=dbid)["properties"]
    for k,v in props.items():
        if "title" in v: return k
    return None

def append_blocks(block_id, children, apply_changes):
    if not children: return
    if not apply_changes: echo(f"{EM['PLAN']} PLAN append {len(children)} blocks → {block_id}"); return
    for i in range(0, len(children), 40):
        retry(cli.blocks.children.append, block_id=block_id, children=children[i:i+40])

def ensure_page(parent, title, icon=None, cover=None, children=None, apply=False):
    ex=find_page(parent, title)
    if ex:
        pid=ex["id"]; echo(f"{EM['INFO']} Page exists: {title}")
        if apply:
            payload={}
            if icon: payload["icon"]={"type":"emoji","emoji":icon}
            if cover:
                if isinstance(cover, dict) and "file_upload" in cover:
                    payload["cover"]={"type":"file","file":{"file_upload":cover["file_upload"]}}
                elif isinstance(cover, str): payload["cover"]={"type":"external","external":{"url":cover}}
            if payload: retry(cli.pages.update, page_id=pid, **payload)
        if children: append_blocks(pid, children, apply)
        return pid
    echo(f"{EM['PLAN'] if not apply else EM['CREATE']} {'PLAN create' if not apply else 'Created'} page: {title}")
    if not apply: return f"PLAN_{title}"
    iconp={"type":"emoji","emoji":icon} if icon else None
    cov=None
    if cover:
        if isinstance(cover, dict) and "file_upload" in cover: cov={"type":"file","file":{"file_upload":cover["file_upload"]}}
        elif isinstance(cover, str): cov={"type":"external","external":{"url":cover}}
    pg=retry(cli.pages.create, parent={"type":"page_id","page_id":parent},
             icon=iconp, cover=cov, properties={"title":{"title":[{"type":"text","text":{"content":title}}]}}, children=children or [])
    return pg["id"]

def ensure_db(parent, title, props, icon=None, apply=False):
    ex=find_db(parent, title)
    if ex:
        cur=set(ex["properties"].keys())
        to_add={k:v for k,v in props.items() if k not in cur}
        if to_add:
            echo(f"{EM['PLAN'] if not apply else EM['CREATE']} {'PLAN add props' if not apply else 'Added props'} → db: {title} → {list(to_add.keys())}")
            if apply: retry(cli.databases.update, database_id=ex["id"], properties=to_add)
        else: echo(f"{EM['INFO']} DB exists: {title}")
        return ex["id"]
    echo(f"{EM['PLAN'] if not apply else EM['CREATE']} {'PLAN create' if not apply else 'Created'} db: {title}")
    if not apply: return f"PLAN_DB_{title}"
    iconp={"type":"emoji","emoji":icon} if icon else None
    db=retry(cli.databases.create, parent={"type":"page_id","page_id":parent}, icon=iconp,
             title=[{"type":"text","text":{"content":title}}], properties=props)
    return db["id"]

def build_blocks(spec_blocks, db_ids):
    out=[]
    for b in spec_blocks or []:
        t=b["type"]
        if t=="h2": out.append(h2(b["text"]))
        elif t=="paragraph": out.append(p(b["text"]))
        elif t=="callout": out.append(co(b["text"], b.get("emoji","💡")))
        elif t=="todo": out.append(td(b["text"], b.get("checked", False)))
        elif t=="code": out.append(code(b["text"], b.get("language","mermaid")))
        elif t=="divider": out.append(div())
        elif t=="link_to_database":
            key=b["database"]; 
            if key in db_ids: out.append(link_db(db_ids[key]))
        elif t in ("table_of_contents","toc"):
            out.append(toc())
    return out

INSTR = "[#INSTR"
def scan_instr(page_id):
    total=0; need_layout=False; need_cover=False; need_qr=False
    start=None
    while True:
        res=retry(cli.blocks.children.list, block_id=page_id, start_cursor=start) if start else retry(cli.blocks.children.list, block_id=page_id)
        for blk in res.get("results", []):
            t=blk["type"]
            if "rich_text" in blk.get(t, {}):
                txt="".join([r["plain_text"] for r in blk[t]["rich_text"] if r.get("type")=="text"])
                if INSTR in txt:
                    total+=1
                    if "INSTR:LAYOUT" in txt: need_layout=True
                    if "INSTR:COVER" in txt: need_cover=True
                    if "INSTR:SHARE" in txt: need_qr=True
        if not res.get("has_more"): break
        start=res.get("next_cursor")
    return total, need_layout, need_cover, need_qr

def upsert_tracker(dbid, title, pid, link, openi, gaps, apply=True):
    props={
        "Page Title":{"title":[{"type":"text","text":{"content":title}}]},
        "Page ID":{"rich_text":[{"type":"text","text":{"content":pid}}]},
        "Page Link":{"url": link},
        "Open Instructions":{"number": openi},
        "Status":{"select":{"name": ("Pending" if openi>0 else "Complete")}},
        "Last Checked":{"date":{"start": datetime.date.today().isoformat()}},
        "Missing Cover":{"checkbox": gaps.get("cover", False)},
        "Missing Icon":{"checkbox": gaps.get("icon", False)},
        "Missing Layout":{"checkbox": gaps.get("layout", False)},
        "Missing QR Entry":{"checkbox": gaps.get("qr", False)},
        "Gaps":{"multi_select":[{"name":n} for n,f in gaps.items() if f]}
    }
    try:
        res=retry(cli.databases.query, database_id=dbid, filter={"property":"Page Title","title":{"equals":title}})
        rs=res.get("results", [])
        if rs:
            rid=rs[0]["id"]; retry(cli.pages.update, page_id=rid, properties=props); echo(f"{EM['TRACK']} Tracker updated: {title} → Open={openi}"); return
    except Exception: pass
    retry(cli.pages.create, parent={"database_id": dbid}, properties=props); echo(f"{EM['TRACK']} Tracker created: {title}")

def main():
    log_setup()
    with open(SPEC,"r",encoding="utf-8") as f: spec=yaml.safe_load(f)
    parent=get_parent_id(); echo("=== PLAN: Root, DBs, Pages ===")
    root=spec["root"]; rtitle=root["title"]; ricon=root.get("icon"); rcover=root.get("cover")
    rx=find_page(parent, rtitle)
    if rx: root_id=rx["id"]; echo(f"{EM['INFO']} Root exists: {rtitle} ({root_id})")
    else: echo(f"{EM['PLAN']} PLAN create root: {rtitle}"); root_id=None
    db_spec=spec.get("databases",{}); db_ids={}
    for key,cfg in db_spec.items():
        title=cfg["title"]; ex = find_db(rx["id"] if rx else parent, title) if rx else None
        if ex: echo(f"{EM['INFO']} DB exists: {title}"); db_ids[key]=ex["id"]
        else: echo(f"{EM['PLAN']} PLAN create db: {title}"); db_ids[key]=f"PLAN_DB_{title}"
    for page in spec.get("pages",[]):
        t=page["title"]; ex=find_page(rx["id"] if rx else parent, t) if rx else None
        if ex: echo(f"{EM['INFO']} Page exists: {t}")
        else: echo(f"{EM['PLAN']} PLAN create page: {t}")
    if input("\nProceed with deploy? [y/N]: ").strip().lower()!="y":
        echo("🚫 Aborted (no changes)."); return

    echo("\n=== APPLY: Root ===")
    def coverify(x):
        if not x: return None
        if isinstance(x,str) and os.path.exists(x):
            try: return upload_file(x, "image/jpeg" if x.lower().endswith(".jpg") else None)
            except Exception as e: echo(f\"{EM['WARN']} Cover upload failed: {e}\"); return None
        return x
    if rx: root_id=rx["id"]; ensure_page(parent, rtitle, icon=ricon, cover=coverify(rcover), children=None, apply=True)
    else: root_id=ensure_page(parent, rtitle, icon=ricon, cover=coverify(rcover), children=None, apply=True)

    echo("\n=== APPLY: Databases ===")
    for key,cfg in db_spec.items():
        title=cfg["title"]; icon=cfg.get("icon")
        props={pname: enc_prop(pdef) for pname,pdef in cfg["properties"].items()}
        db_ids[key]=ensure_db(root_id, title, props, icon, apply=True)

    echo("\n=== APPLY: DB Relations ===")
    for key,cfg in db_spec.items():
        title=cfg["title"]; need={}
        for pname,pdef in cfg["properties"].items():
            if pdef["type"]=="relation":
                target_key=pdef["target"]; tid=db_ids.get(target_key)
                if tid: need[pname]={"relation":{"database_id": tid}}; echo(f"{EM['CREATE']} Set relation: {title}.{pname} → {db_spec[target_key]['title']}")
                else: echo(f"{EM['WARN']} Relation target missing: {title}.{pname} → {target_key}")
        if need: retry(cli.databases.update, database_id=db_ids[key], properties=need)

    echo("\n=== APPLY: Pages & Blocks ===")
    page_ids={}
    for pg in spec.get("pages",[]):
        title=pg["title"]; icon=pg.get("icon"); cov=coverify(pg.get("cover"))
        blocks=build_blocks(pg.get("blocks",[]), db_ids)
        if pg.get("insert_toc"): blocks=[toc(), div()] + blocks
        if pg.get("layout_hint"): blocks=[co(f"[#NOTE] {pg['layout_hint']}", "🧩")] + blocks
        for instr in pg.get("instructions",[]): blocks=[co(instr, "🛠️")]+blocks
        pid=ensure_page(root_id, title, icon=icon, cover=cov, children=blocks, apply=True)
        page_ids[title]=pid

    # Template Map
    try:
        mid=page_ids.get("Template Map (All Pages Index)")
        if mid:
            kids=retry(cli.blocks.children.list, block_id=mid).get("results",[])
            if len(kids)<3:
                links=[{"object":"block","type":"link_to_page","link_to_page":{"type":"page_id","page_id": pid}} for t,pid in page_ids.items() if t!="Template Map (All Pages Index)"]
                append_blocks(mid, links, True); echo(f"{EM['CREATE']} Built Template Map with {len(links)} links")
    except Exception as e: echo(f"{EM['WARN']} Could not build Template Map automatically: {e}")

    echo("\n=== APPLY: Seeds ===")
    seeds=spec.get("seed",{})
    for key, rows in seeds.items():
        dbid=db_ids.get(key); 
        if not dbid: continue
        title_prop=db_title_key(dbid); live=retry(cli.databases.retrieve, database_id=dbid)["properties"]
        for row in rows or []:
            tval=row.get(title_prop) if title_prop else "(no-title)"
            exists=None
            if title_prop and tval:
                try:
                    res=retry(cli.databases.query, database_id=dbid, filter={"property":title_prop,"title":{"equals":tval}})
                    R=res.get("results", []); 
                    if R: exists=R[0]["id"]
                except Exception: pass
            if exists: echo(f"{EM['SKIP']} Skipped seed (exists): {key} → \"{tval}\""); continue
            props={}
            for k,v in row.items():
                pd=live.get(k)
                if not pd: continue
                if "title" in pd: props[k]={"title":[{"type":"text","text":{"content":str(v)}}]}
                elif "rich_text" in pd: props[k]={"rich_text":[{"type":"text","text":{"content":str(v)}}]}
                elif "select" in pd: props[k]={"select":{"name": str(v)}}
                elif "multi_select" in pd:
                    vals=v if isinstance(v,list) else [v]; props[k]={"multi_select":[{"name":str(x)} for x in vals]}
                elif "checkbox" in pd: props[k]={"checkbox": bool(v)}
                elif "date" in pd: props[k]={"date":{"start": str(v)}}
                elif "email" in pd: props[k]={"email": str(v)}
                elif "phone_number" in pd: props[k]={"phone_number": str(v)}
                elif "url" in pd: props[k]={"url": str(v)}
                elif "files" in pd: pass
                elif "number" in pd:
                    try: props[k]={"number": float(v)}
                    except: pass
            retry(cli.pages.create, parent={"database_id": dbid}, properties=props)
            echo(f"{EM['CREATE']} Seeded: {key} → \"{tval}\"")

    echo("\n=== APPLY: Build Tracker & Diagnostics ===")
    tracker=db_ids.get("build_tracker")
    if tracker:
        for title,pid in page_ids.items():
            openi, need_layout, need_cover, need_qr = scan_instr(pid)
            gaps={"cover":need_cover, "icon":False, "layout":need_layout, "qr":need_qr}
            upsert_tracker(tracker, title, pid, nurl(pid), openi, gaps, apply=True)
        echo(f"{EM['TRACK']} Build Tracker updated for {len(page_ids)} pages")
    else:
        echo(f"{EM['WARN']} Build Tracker DB not found; skipping diagnostics rows.")

    echo("\n=== Summary ===")
    echo("Pages and databases created/updated. See deploy.log for the full transcript.")
    echo("Open Diagnostics to see what's left, and clear all [#INSTR] on each page.")
if __name__=="__main__": 
    log_setup(); main()
