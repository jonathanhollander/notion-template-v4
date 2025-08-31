import hashlib
from fastapi import Request
from .db import db_conn

def _hash(val: str) -> str:
    return hashlib.sha256(val.encode()).hexdigest()

def log_visit(request: Request, page: str, promo_id: str = None, product_id: str = None, extra: dict = None):
    xf = request.headers.get("x-forwarded-for","")
    ip = (xf.split(",")[0] or (request.client.host if request.client else "")).split(":")[0]
    ua = request.headers.get("user-agent","")
    ip_hash = _hash(ip) if ip else None
    ua_hash = _hash(ua) if ua else None
    with db_conn() as c:
        c.execute(
            'INSERT INTO visits (page,promo_id,product_id,ip_hash,ua_hash,referer_host,extra) VALUES (%s,%s,%s,%s,%s,%s,%s)',
            (page, promo_id, product_id, ip_hash, ua_hash, None, extra or {})
        )
