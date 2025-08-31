import os, uuid, random, datetime, json
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .db import db_conn

env = Environment(loader=FileSystemLoader("app/templates"), autoescape=select_autoescape())
router = APIRouter()
ALLOW_ANON = os.getenv("ALLOW_ANON_WID","true").lower() == "true"
APP_BASE = os.getenv("APP_BASE_URL","")

FALLBACK_FAMILY = [
  "A tiny step is enough—would adding one loving note feel okay today?",
  "Is there a photo that quietly brings comfort—would you like to place it here?",
  "Would a single-kind sentence to someone help today? Only a few words are needed."
]
FALLBACK_EXECUTOR = [
  "One simple action: open the Subscriptions list—checking one item helps.",
  "A small win: add the insurer’s contact—this prevents delays later.",
  "Glance at the First 72 Hours card—one check today keeps momentum."
]

def get_default_enabled():
    with db_conn() as c:
        row = c.execute("SELECT value FROM app_settings WHERE key='companion_default'").fetchone()
    if not row:
        return True
    try:
        return bool(row[0].get("enabled", True)) if isinstance(row[0], dict) else bool(json.loads(row[0]).get("enabled", True))
    except Exception:
        return True

def pick_from_db(audience: str):
    with db_conn() as c:
        rows = c.execute(
            "SELECT text FROM gentle_messages WHERE audience=%s AND enabled=true AND include_in_rotation=true",
            (audience,)
        ).fetchall()
    if not rows:
        return None
    return random.choice([r[0] for r in rows])

def resolve_text(audience: str) -> str:
    t = pick_from_db(audience)
    if t: return t
    return random.choice(FALLBACK_EXECUTOR if audience == "executor" else FALLBACK_FAMILY)

@router.get("/widget/companion", response_class=HTMLResponse)
def widget_companion(request: Request, audience: str="family"):
    wid = request.cookies.get("wid")
    if not wid:
        if ALLOW_ANON:
            wid = str(uuid.uuid4())
            with db_conn() as c:
                c.execute("INSERT INTO installs (wid, notion_workspace_id) VALUES (%s, %s) ON CONFLICT (wid) DO NOTHING", (wid, None))
            response = HTMLResponse(env.get_template("widget_companion.html").render(
                text=resolve_text(audience),
                updated=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")+"Z",
                wid=wid
            ))
            response.set_cookie("wid", wid, secure=True, httponly=False, samesite="none", max_age=31536000)
            return response
        oauth_start_url = f"{APP_BASE}/widget/oauth/start?audience={audience}" if APP_BASE else "/widget/oauth/start"
        return HTMLResponse(env.get_template("widget_pair.html").render(oauth_start_url=oauth_start_url))

    with db_conn() as c:
        row = c.execute("SELECT companion_enabled FROM installs WHERE wid=%s", (wid,)).fetchone()
    enabled = get_default_enabled() if (row is None or row[0] is None) else bool(row[0])

    if not enabled:
        html = env.get_template("widget_quiet.html").render()
        return HTMLResponse(html)

    return HTMLResponse(env.get_template("widget_companion.html").render(
        text=resolve_text(audience),
        updated=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")+"Z",
        wid=wid
    ))

@router.get("/widget/oauth/start")
def widget_oauth_start(audience: str="family"):
    cid = os.getenv("NOTION_CLIENT_ID"); redir = os.getenv("NOTION_REDIRECT_URI")
    if not cid or not redir:
        return HTMLResponse("<small>Developer: set NOTION_CLIENT_ID/SECRET/REDIRECT_URI. Anonymous pairing is enabled.</small>")
    url = f"https://api.notion.com/v1/oauth/authorize?owner=user&client_id={cid}&redirect_uri={redir}&response_type=code&state={audience}"
    return HTMLResponse(f"<script>location.href='{url}'</script>")

@router.get("/widget/oauth/callback")
def widget_oauth_callback(code: str, state: str="family"):
    return HTMLResponse("<small>OAuth callback received. Implement token exchange if you need workspace-level actions.</small>")
