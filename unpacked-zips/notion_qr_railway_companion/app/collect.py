from fastapi import APIRouter, Request, HTTPException
from .db import db_conn
router = APIRouter()
@router.post("/collect/session-start")
async def session_start(req: Request):
    data = await req.json()
    wid = data.get("wid"); session_id = data.get("session_id")
    if not wid or not session_id:
        raise HTTPException(400, "wid and session_id required")
    with db_conn() as c:
        c.execute("INSERT INTO installs (wid, notion_workspace_id) VALUES (%s, %s) ON CONFLICT (wid) DO NOTHING", (wid, None))
        c.execute('''UPDATE installs SET
               language_pref = %s, timezone = %s, device_type = %s, browser = %s, os = %s,
               screen_w = %s, screen_h = %s, dpr = %s, a11y_reduced_motion = %s, a11y_contrast = %s,
               net_downlink = %s, net_effective_type = %s, net_save_data = %s, last_seen_at = NOW()
             WHERE wid = %s''',
          (data.get("language_pref"), data.get("timezone"), data.get("device_type"), data.get("browser"), data.get("os"),
           data.get("screen_w"), data.get("screen_h"), data.get("dpr"),
           data.get("a11y_reduced_motion"), data.get("a11y_contrast"),
           data.get("net_downlink"), data.get("net_effective_type"), data.get("net_save_data"),
           wid)
        )
        c.execute('''INSERT INTO sessions (id, wid, referer_url, section_hint, render_ms)
             VALUES (%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING''',
          (session_id, wid, data.get("referer_url"), data.get("section_hint"), data.get("render_ms"))
        )
    return {"ok": True}
@router.post("/collect/session-end")
async def session_end(req: Request):
    data = await req.json()
    wid = data.get("wid"); session_id = data.get("session_id")
    if not wid or not session_id:
        raise HTTPException(400, "wid and session_id required")
    with db_conn() as c:
        c.execute("UPDATE sessions SET unload_ts = NOW() WHERE id=%s", (session_id,))
    return {"ok": True}
@router.post("/collect/event")
async def collect_event(req: Request):
    data = await req.json()
    with db_conn() as c:
        c.execute('INSERT INTO events (wid, session_id, type, name, value, extra) VALUES (%s,%s,%s,%s,%s,%s)',
                  (data.get("wid"), data.get("session_id"), data.get("type"),
                   data.get("name"), data.get("value"), data.get("extra") or {}))
    return {"ok": True}
