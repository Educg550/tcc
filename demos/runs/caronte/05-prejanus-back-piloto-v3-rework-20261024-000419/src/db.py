"""Conexões dos dois bancos: PreJanus e Forms."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings


def _url(conn: str) -> str:
    if not conn:
        return conn
    if conn.startswith("postgresql+"):
        return conn
    if conn.startswith("postgres://"):
        conn = "postgresql://" + conn[len("postgres://"):]
    return conn.replace("postgresql://", "postgresql+psycopg://", 1)


engine = create_engine(_url(settings.db_connection_string), pool_pre_ping=True)
engine_forms = create_engine(_url(settings.db_connection_string_forms), pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine)
SessionForms = sessionmaker(bind=engine_forms)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_forms_db():
    db = SessionForms()
    try:
        yield db
    finally:
        db.close()
