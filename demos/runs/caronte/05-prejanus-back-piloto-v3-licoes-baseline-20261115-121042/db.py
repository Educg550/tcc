from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import settings


def _normalize(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


engine = create_async_engine(_normalize(settings.db_connection_string))
forms_engine = create_async_engine(_normalize(settings.db_connection_string_forms))

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
FormsSessionLocal = async_sessionmaker(forms_engine, expire_on_commit=False)
