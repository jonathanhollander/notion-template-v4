from fastapi import APIRouter, Depends, Header, HTTPException
from .db import db_conn
import json, os
router = APIRouter()
def admin_auth(authorization: str = Header("")):
    if authorization != f"Bearer {os.environ.get('ADMIN_TOKEN','')}":
        raise HTTPException(401, "Unauthorized")
@router.post("/admin/messages/workspace-toggle", dependencies=[Depends(admin_auth)])
def workspace_toggle(payload: dict):
    wid = payload.get("wid"); enabled = payload.get("enabled")
    if not wid or enabled is None:
        raise HTTPException(400, "wid and enabled required")
    with db_conn() as c:
        c.execute("UPDATE installs SET companion_enabled=%s WHERE wid=%s", (bool(enabled), wid))
    return {"ok": True}
@router.post("/admin/messages/default", dependencies=[Depends(admin_auth)])
def default_toggle(payload: dict):
    enabled = payload.get("enabled")
    if enabled is None:
        raise HTTPException(400, "enabled required")
    with db_conn() as c:
        c.execute(
          "INSERT INTO app_settings(key,value,updated_at) VALUES ('companion_default', %s, NOW()) ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value, updated_at=NOW()",
          (json.dumps({"enabled": bool(enabled)}),)
        )
    return {"ok": True}
@router.post("/admin/messages/rotation", dependencies=[Depends(admin_auth)])
def rotation_update(payload: dict):
    ids = payload.get("ids"); include = payload.get("include")
    if not ids or include is None:
        raise HTTPException(400, "ids and include required")
    with db_conn() as c:
        c.execute("UPDATE gentle_messages SET include_in_rotation=%s WHERE id = ANY(%s)", (bool(include), ids))
    return {"ok": True}
