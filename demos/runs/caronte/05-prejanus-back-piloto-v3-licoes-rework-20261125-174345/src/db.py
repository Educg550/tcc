from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from .config import settings


def _normalize(url: str) -> str:
    for prefix in ("postgresql+asyncpg://", "postgresql+psycopg://", "postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


prejanus_engine = create_async_engine(_normalize(settings.DB_CONNECTION_STRING), pool_pre_ping=True)
forms_engine = create_async_engine(_normalize(settings.DB_CONNECTION_STRING_FORMS), pool_pre_ping=True)


async def fetch(eng, sql: str, params: dict | None = None) -> list[dict]:
    async with eng.connect() as conn:
        result = await conn.execute(text(sql), params or {})
        return [dict(row) for row in result.mappings()]


async def fetch_one(eng, sql: str, params: dict | None = None) -> dict | None:
    rows = await fetch(eng, sql, params)
    return rows[0] if rows else None


async def run(eng, sql: str, params: dict | None = None) -> list[dict]:
    """Executa em transação; devolve linhas quando a consulta retorna."""
    async with eng.begin() as conn:
        result = await conn.execute(text(sql), params or {})
        if result.returns_rows:
            return [dict(row) for row in result.mappings()]
        return []
