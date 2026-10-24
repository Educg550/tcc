from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import settings


def _normalize(url: str) -> str:
    if url.startswith("postgresql+psycopg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


prejanus_engine = create_async_engine(_normalize(settings.DB_CONNECTION_STRING))
forms_engine = create_async_engine(_normalize(settings.DB_CONNECTION_STRING_FORMS))

PrejanusSession = async_sessionmaker(prejanus_engine, expire_on_commit=False)
FormsSession = async_sessionmaker(forms_engine, expire_on_commit=False)
