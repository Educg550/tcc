from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import settings


def _psycopg_url(url: str) -> str:
    if url.startswith("postgresql+psycopg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


engine = create_async_engine(_psycopg_url(settings.db_connection_string), pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

forms_engine = create_async_engine(
    _psycopg_url(settings.db_connection_string_forms), pool_pre_ping=True
)
FormsSessionLocal = async_sessionmaker(forms_engine, expire_on_commit=False)
