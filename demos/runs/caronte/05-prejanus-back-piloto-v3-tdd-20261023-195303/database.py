from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings


def _normalize(url: str) -> str:
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


prejanus_engine = create_engine(_normalize(settings.db_connection_string), pool_pre_ping=True)
forms_engine = create_engine(_normalize(settings.db_connection_string_forms), pool_pre_ping=True)

PrejanusSession = sessionmaker(bind=prejanus_engine, expire_on_commit=False)
FormsSession = sessionmaker(bind=forms_engine, expire_on_commit=False)
