from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings


def _sync_url(raw: str) -> str:
    raw = raw or ''
    if raw.startswith('postgresql+asyncpg://'):
        raw = raw.replace('postgresql+asyncpg://', 'postgresql+psycopg://', 1)
    elif raw.startswith('postgresql://'):
        raw = raw.replace('postgresql://', 'postgresql+psycopg://', 1)
    return raw


engine = create_engine(_sync_url(settings.db_connection_string), pool_pre_ping=True)
engine_forms = create_engine(_sync_url(settings.db_connection_string_forms), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
SessionLocalForms = sessionmaker(bind=engine_forms)
