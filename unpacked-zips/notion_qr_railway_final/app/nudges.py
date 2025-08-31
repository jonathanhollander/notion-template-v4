import os, uuid, random, datetime
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .db import db_conn

env = Environment(loader=FileSystemLoader("app/templates"), autoescape=select_autoescape())
router = APIRouter()
ALLOW_ANON = os.getenv("ALLOW_ANON_WID","true").lower() == "true"
APP_BASE = os.getenv("APP_BASE_URL","")

FALLBACK_FAMILY = [
  "Would you like to add a small memory today—just a sentence is enough?",
  "Is there a photo that brings a smile—adding it here could feel nice?",
  "Would you like to write a kind note to someone—even a few words matter?"
]
FALLBACK_EXECUTOR = [
  "Next small step: open the Subscriptions list—checking one item helps.",
  "A simple win: add the insurer’s contact—this prevents delays later.",
  "Review the First 72 Hours card—one check today keeps momentum."
]

def pick_from_db(audience: str) -> str|None:
    with db_conn() as c:
        rows = c.execute("SELECT text FROM nudges WHERE audience=%s AND enabled=true", (audience,)).fetchall()
    if not rows:
        return None
    return random.choice([r[0] for r in rows])

def pick(audience: str) -> str:
    t = pick_from_db(audience)
    if t: return t
    return random.choice(FALLBACK_EXECUTOR if audience == "executor" else FALLBACK_FAMILY)

@router.get("/widget/nudge", response_class=HTMLResponse)
def widget_nudge(request: Request, audience: str="family"):
    wid_cookie = request.cookies.get("wid")
    if not wid_cookie:
        if ALLOW_ANON:
            wid = str(uuid.uuid4())
            with db_conn() as c:
                c.execute("INSERT INTO installs (wid, notion_workspace_id) VALUES (%s, %s) ON CONFLICT (wid) DO NOTHING", (wid, None))
            html = env.get_template("widget_nudge.html").render(
                text=pick(audience), updated=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")+"Z", wid=wid
            )
            response = HTMLResponse(html)
            response.set_cookie("wid", wid, secure=True, httponly=False, samesite="none", max_age=31536000)
            return response
        oauth_start_url = f"{APP_BASE}/widget/oauth/start?audience={audience}" if APP_BASE else "/widget/oauth/start"
        return HTMLResponse(env.get_template("widget_pair.html").render(oauth_start_url=oauth_start_url))
    return HTMLResponse(env.get_template("widget_nudge.html").render(
        text=pick(audience), updated=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")+"Z", wid=wid_cookie
    ))

@router.get("/widget/oauth/start")
def widget_oauth_start(audience: str="family"):
    cid = os.getenv("NOTION_CLIENT_ID"); redir = os.getenv("NOTION_REDIRECT_URI")
    if not cid or not redir:
        return HTMLResponse("<small>Developer: set NOTION_CLIENT_ID/SECRET/REDIRECT_URI. Anon pairing is enabled.</small>")
    url = f"https://api.notion.com/v1/oauth/authorize?owner=user&client_id={cid}&redirect_uri={redir}&response_type=code&state={audience}"
    return HTMLResponse(f"<script>location.href='{url}'</script>")

@router.get("/widget/oauth/callback")
def widget_oauth_callback(code: str, state: str="family"):
    return HTMLResponse("<small>OAuth callback received. Implement token exchange if you need workspace-level actions.</small>")
