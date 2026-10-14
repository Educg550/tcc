from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database.models.edict import Edict


class EdictSchema(BaseModel):
    id: int
    title: str
    year: int
    semester: int
    edict_type: str
    is_open: bool

async def get_all_edicts(session: AsyncSession, type: str | None = None, is_open: bool | None = None) -> list[EdictSchema]:
    query = select(Edict).order_by(Edict.closed_date.desc())

    if type is not None:
        query = query.where(Edict.type == type)
    if is_open is not None:
        query = query.where(Edict.is_open == is_open)

    query_result = await session.execute(query)
    edicts = query_result.scalars().all()

    return [EdictSchema(id=edict.id, title=edict.title, year=edict.year, semester=edict.semester, edict_type=edict.type, is_open=edict.is_open) for edict in edicts]