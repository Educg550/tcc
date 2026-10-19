from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import settings


def _normalize(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


prejanus_engine = create_async_engine(
    _normalize(settings.db_connection_string), pool_pre_ping=True
)
forms_engine = create_async_engine(
    _normalize(settings.db_connection_string_forms), pool_pre_ping=True
)

PrejanusSession = async_sessionmaker(prejanus_engine, expire_on_commit=False)
FormsSession = async_sessionmaker(forms_engine, expire_on_commit=False)


async def get_db():
    async with PrejanusSession() as session:
        yield session


async def get_forms_db():
    async with FormsSession() as session:
        yield session
