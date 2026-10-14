from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.settings import get_settings


settings = get_settings()

engine_main = create_async_engine(settings.DB_CONNECTION_STRING, future=True, echo=False)
engine_forms = create_async_engine(settings.DB_CONNECTION_STRING_FORMS, future=True, echo=False)

SessionMain = async_sessionmaker(engine_main, expire_on_commit=False, class_=AsyncSession)
SessionForms = async_sessionmaker(engine_forms, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionMain() as session:
        yield session


async def get_session_forms() -> AsyncIterator[AsyncSession]:
    async with SessionForms() as session:
        yield session