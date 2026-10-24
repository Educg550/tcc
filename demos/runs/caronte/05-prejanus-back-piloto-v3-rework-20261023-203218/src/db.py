from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import settings


def _url(connection_string: str) -> str:
    if connection_string.startswith("postgresql+"):
        return connection_string
    return connection_string.replace("postgresql://", "postgresql+psycopg://", 1)


engine = create_async_engine(_url(settings.DB_CONNECTION_STRING))
forms_engine = create_async_engine(_url(settings.DB_CONNECTION_STRING_FORMS))

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
FormsSessionLocal = async_sessionmaker(forms_engine, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session


async def get_forms_db():
    async with FormsSessionLocal() as session:
        yield session
