from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import settings


def _async_url(url: str) -> str:
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    if url.startswith("postgresql+"):
        return url
    return "postgresql+psycopg://" + url


engine = create_async_engine(_async_url(settings.db_connection_string))
forms_engine = create_async_engine(_async_url(settings.db_connection_string_forms))

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
FormsSessionLocal = async_sessionmaker(forms_engine, expire_on_commit=False)
