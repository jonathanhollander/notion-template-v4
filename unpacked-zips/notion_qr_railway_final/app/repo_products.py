from datetime import datetime, timezone
from .db import db_conn

def _active(row: dict) -> bool:
    if not row["enabled"]:
        return False
    now = datetime.now(timezone.utc)
    s, e = row["start_at"], row["end_at"]
    if s and now < s: return False
    if e and now >= e: return False
    return True

def get_active_products(ids=None):
    q = "SELECT id,name,price_id,qr_set,enabled,start_at,end_at FROM products"
    params = ()
    if ids:
        q += " WHERE id = ANY(%s)"
        params = (ids,)
    with db_conn() as c:
        rows = c.execute(q, params).fetchall()
    if not rows: return []
    cols = [d.name for d in rows[0].cursor.description]
    out = [dict(zip(cols, r)) for r in rows]
    return [r for r in out if _active(r)]

def get_product(pid: str):
    with db_conn() as c:
        r = c.execute("SELECT id,name,price_id,qr_set,enabled,start_at,end_at FROM products WHERE id=%s", (pid,)).fetchone()
    if not r: return None
    cols = [d.name for d in r.cursor.description]
    row = dict(zip(cols, r))
    return row if _active(row) else None

def upsert_products(items: list):
    with db_conn() as c:
        for p in items:
            c.execute(
              '''INSERT INTO products (id,name,price_id,qr_set,enabled,start_at,end_at)
                 VALUES (%(id)s,%(name)s,%(price_id)s,%(qr_set)s,%(enabled)s,%(start_at)s,%(end_at)s)
                 ON CONFLICT (id) DO UPDATE SET
                   name=EXCLUDED.name,
                   price_id=EXCLUDED.price_id,
                   qr_set=EXCLUDED.qr_set,
                   enabled=EXCLUDED.enabled,
                   start_at=EXCLUDED.start_at,
                   end_at=EXCLUDED.end_at,
                   updated_at=NOW()''',
              p
            )
