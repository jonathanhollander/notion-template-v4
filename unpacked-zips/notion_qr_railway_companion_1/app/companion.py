import os, uuid, random, datetime, json
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .db import db_conn

env=Environment(loader=FileSystemLoader('app/templates'),autoescape=select_autoescape())
router=APIRouter()

FAMILY_DEFAULT=["Would you like to add a gentle memory today?"]
EXECUTOR_DEFAULT=["Small step: review the Subscriptions list."]

def get_default_enabled():
    with db_conn() as c:
        row=c.execute("SELECT value FROM app_settings WHERE key='companion_default'").fetchone()
    if not row: return True
    try:
        return json.loads(row[0]).get('enabled',True)
    except: return True

@router.get('/widget/companion',response_class=HTMLResponse)
def widget(request:Request,audience:str='family'):
    wid=request.cookies.get('wid')
    if not wid:
        wid=str(uuid.uuid4())
        with db_conn() as c:
            c.execute("INSERT INTO installs(wid) VALUES(%s) ON CONFLICT (wid) DO NOTHING",(wid,))
    with db_conn() as c:
        row=c.execute("SELECT companion_enabled FROM installs WHERE wid=%s",(wid,)).fetchone()
    enabled=get_default_enabled() if (row is None or row[0] is None) else bool(row[0])
    if not enabled:
        return HTMLResponse(env.get_template('widget_quiet.html').render())
    msg=random.choice(EXECUTOR_DEFAULT if audience=='executor' else FAMILY_DEFAULT)
    return HTMLResponse(env.get_template('widget_companion.html').render(text=msg,updated=datetime.datetime.utcnow().isoformat()))
