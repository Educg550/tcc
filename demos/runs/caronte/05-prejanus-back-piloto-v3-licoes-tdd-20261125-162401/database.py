from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import settings


def _url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


engine = create_async_engine(_url(settings.db_connection_string), pool_pre_ping=True)
forms_engine = create_async_engine(
    _url(settings.db_connection_string_forms), pool_pre_ping=True
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
FormsSessionLocal = async_sessionmaker(forms_engine, expire_on_commit=False)
