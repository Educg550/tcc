from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import get_settings


def _engine(url: str):
    if url.startswith('postgresql://'):
        url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
    return create_async_engine(url)


settings = get_settings()
engine = _engine(settings.db_connection_string)
forms_engine = _engine(settings.db_connection_string_forms)

Session = async_sessionmaker(engine, expire_on_commit=False)
FormsSession = async_sessionmaker(forms_engine, expire_on_commit=False)


async def get_session():
    async with Session() as session:
        yield session


async def get_forms_session():
    async with FormsSession() as session:
        yield session
