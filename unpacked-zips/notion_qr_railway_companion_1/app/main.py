import os,glob,datetime
from fastapi import FastAPI
from .companion import router as companion_router
from .db import db_conn

app=FastAPI()
@app.on_event('startup')
def migrate():
    for path in sorted(glob.glob('migrations/*.sql')):
        with open(path) as f: sql=f.read()
        with db_conn() as c: c.execute(sql)
@app.get('/healthz')
def healthz(): return {'ok':True,'time':datetime.datetime.utcnow().isoformat()}
app.include_router(companion_router)
