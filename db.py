from sqlalchemy import create_engine, text
from contextlib import contextmanager
from config import settings

def make_uri(user, password):
    return f"mysql+pymysql://{user}:{password}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"

engine_default = create_engine(make_uri(settings.MYSQL_USER, settings.MYSQL_PASSWORD), pool_pre_ping=True)
engine_read = create_engine(make_uri(settings.MYSQL_USER_READ, settings.MYSQL_PASSWORD_READ), pool_pre_ping=True)
engine_admin = create_engine(make_uri(settings.MYSQL_USER_ADMIN, settings.MYSQL_PASSWORD_ADMIN), pool_pre_ping=True)

@contextmanager
def get_conn(role=None):
    eng = engine_default
    if role in ("Customer", "Artist"):
        eng = engine_read
    elif role == "Admin":
        eng = engine_admin
    with eng.connect() as conn:
        yield conn

def fetch_all(conn, sql, params=None):
    res = conn.execute(text(sql), params or {})
    return [dict(r._mapping) for r in res]

def fetch_one(conn, sql, params=None):
    res = conn.execute(text(sql), params or {})
    row = res.first()
    return dict(row._mapping) if row else None

def execute(conn, sql, params=None):
    conn.execute(text(sql), params or {})
    conn.commit()
