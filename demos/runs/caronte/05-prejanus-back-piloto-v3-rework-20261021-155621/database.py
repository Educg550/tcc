"""Conexões dos bancos PreJanus e Forms."""
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import settings


def _fix_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


engine = create_async_engine(_fix_url(settings.db_connection_string))
forms_engine = create_async_engine(_fix_url(settings.db_connection_string_forms))

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
FormsSessionLocal = async_sessionmaker(forms_engine, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session


async def get_forms_db():
    async with FormsSessionLocal() as session:
        yield session
