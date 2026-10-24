import psycopg
from psycopg.types import string
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from prejanus.config import settings


class _StrDumperUnknown(string.StrDumper):
    """Envia str como unknown (OID 0), como o psycopg2 fazia.

    O psycopg3 envia str como text, o que quebra comparacoes/escritas em
    colunas enum, json e uuid ("operator does not exist").
    """

    oid = 0


psycopg.adapters.register_dumper(str, _StrDumperUnknown)


def _async_url(url: str) -> str:
    if "+" in url.split("://", 1)[0]:
        return url
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url.replace("postgresql://", "postgresql+psycopg://", 1)


engine = create_async_engine(_async_url(settings.db_connection_string), pool_pre_ping=True)
forms_engine = create_async_engine(_async_url(settings.db_connection_string_forms), pool_pre_ping=True)


def _register_str_dumper(dbapi_conn, _record):
    dbapi_conn.adapters.register_dumper(str, _StrDumperUnknown)


event.listens_for(engine.sync_engine, "connect")(_register_str_dumper)
event.listens_for(forms_engine.sync_engine, "connect")(_register_str_dumper)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session
