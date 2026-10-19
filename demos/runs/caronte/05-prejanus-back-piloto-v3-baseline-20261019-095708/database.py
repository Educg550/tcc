from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import settings


def _normalize(url: str) -> str:
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


engine = create_async_engine(_normalize(settings.db_connection_string), pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

forms_engine = create_async_engine(_normalize(settings.db_connection_string_forms), pool_pre_ping=True)
FormsSessionLocal = async_sessionmaker(forms_engine, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session
