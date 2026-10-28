from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings


def _url(u):
    if not u:
        u = "postgresql+psycopg://localhost/prejanus"
    if u.startswith("postgresql://"):
        return u.replace("postgresql://", "postgresql+psycopg://", 1)
    if u.startswith("postgres://"):
        return u.replace("postgres://", "postgresql+psycopg://", 1)
    if u.startswith("postgresql+psycopg"):
        return u
    return u


engine = create_engine(_url(settings.db_url), pool_pre_ping=True)
forms_engine = create_engine(_url(settings.db_forms_url), pool_pre_ping=True)
Session = sessionmaker(engine, expire_on_commit=False)
FormsSession = sessionmaker(forms_engine, expire_on_commit=False)
