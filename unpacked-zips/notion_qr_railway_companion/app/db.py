import os, psycopg
from contextlib import contextmanager
DATABASE_URL = os.environ["DATABASE_URL"]
@contextmanager
def db_conn():
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        yield conn
