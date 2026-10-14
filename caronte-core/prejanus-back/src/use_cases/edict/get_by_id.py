from pydantic import BaseModel
from datetime import datetime, date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from src.infra.database.models.edict import Edict
from src.infra.database.models.user_edict_slots import UserEdictSlots
from src.use_cases.dtos import UserDTO
from src.use_cases.submission.exceptions import EdictNotFound


class EdictPhaseResponse(BaseModel):
    id: int
    closed_date: Optional[date] = None
    phase: str
    

class EdictByIdSchema(BaseModel):
    id: int
    title: str
    candidate_form_id: str
    recommender_form_id: str
    description: str
    closed_date: Optional[date] = None
    created_at: Optional[datetime] = None
    year: int
    semester: int
    type: str
    is_open: bool
    updated_at: Optional[datetime] = None
    phase: str
    phases: list[EdictPhaseResponse]
    slots: str


async def get_edict_by_id(session: AsyncSession, edict_id: int, user: UserDTO) -> EdictByIdSchema:
    edict_query = select(Edict).where(Edict.id == edict_id)
    edict_result = await session.execute(edict_query)
    edict = edict_result.scalar_one_or_none()

    if edict is None:
        raise EdictNotFound(edict_id)

    slot_query = (
        select(UserEdictSlots)
        .where(UserEdictSlots.edict_id == edict_id)
        .where((UserEdictSlots.user_id == user.id) | (UserEdictSlots.user_id.is_(None)))
    )
    slot_result = await session.execute(slot_query)
    slot = slot_result.scalar_one_or_none()

    return EdictByIdSchema(
        id=edict.id,
        title=edict.title,
        candidate_form_id=edict.candidate_forms,
        recommender_form_id=edict.recommenders_forms,
        description=edict.description,
        closed_date=edict.closed_date,
        created_at=edict.created_at,
        year=edict.year,
        semester=edict.semester,
        type=edict.type,
        is_open=edict.is_open,
        updated_at=edict.updated_at,
        phase=edict.phase,
        phases=[
            EdictPhaseResponse(
                id=__phase.id,
                closed_date=__phase.closed_date,
                phase=__phase.phase
            ) for __phase in edict.edict_phases
        ],
        slots="0" if slot is None else str(slot.slots)
    )
