from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from prejanus.config import settings


def _normalize(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


engine = create_async_engine(_normalize(settings.db_connection_string), pool_pre_ping=True)
forms_engine = create_async_engine(_normalize(settings.db_connection_string_forms), pool_pre_ping=True)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
FormsSessionLocal = async_sessionmaker(forms_engine, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session


async def get_forms_db():
    async with FormsSessionLocal() as session:
        yield session
