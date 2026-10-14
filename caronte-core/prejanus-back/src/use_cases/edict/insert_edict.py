from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database.models.edict import Edict
from src.infra.database.models.edict_phase import EdictPhase
from src.use_cases.dtos import UserDTO
from src.use_cases.exceptions import InsufficientRole
from src.utils import is_admin_role


class InsertEdictSchema(BaseModel):
    title: str
    description: str | None = None
    year: int
    semester: int
    edict_type: str
    is_open: bool

    candidate_forms: int
    recommenders_forms: int

    date_application: datetime
    date_verification: datetime
    date_evaluation: datetime
    date_closed: datetime


class InsertEdictResponse(InsertEdictSchema):
    id: int

    closed_date: datetime


async def insert_edict(session: AsyncSession, edict_data: InsertEdictSchema, user: UserDTO) -> InsertEdictResponse:
    assert edict_data.date_application < edict_data.date_verification < edict_data.date_evaluation < edict_data.date_closed, \
        "Edict phase dates must be in chronological order."

    if not is_admin_role(user.role):
        raise InsufficientRole()

    new_edict = Edict(
        title=edict_data.title,
        user_id=user.id,
        description=edict_data.description,
        year=edict_data.year,
        semester=edict_data.semester,
        type=edict_data.edict_type,
        candidate_forms=edict_data.candidate_forms,
        recommenders_forms=edict_data.recommenders_forms,
        is_open=edict_data.is_open,
        closed_date=edict_data.date_closed,
        edict_phases=[
            EdictPhase(
                closed_date = edict_data.date_application,
                phase = "inscricoes"
            ), EdictPhase(
                closed_date = edict_data.date_evaluation,
                phase = "homologacao"
            ), EdictPhase(
                closed_date = edict_data.date_verification,
                phase = "avaliacao"
            ), EdictPhase(
                closed_date = edict_data.date_closed,
                phase = "encerrado"
            )
        ]
    )
    session.add(new_edict)
    await session.commit()
    await session.refresh(new_edict)
    for phase in new_edict.edict_phases:
        await session.refresh(phase)

    return InsertEdictResponse(
        id=new_edict.id,
        title=new_edict.title,
        description=new_edict.description,
        year=new_edict.year,
        semester=new_edict.semester,
        candidate_forms=new_edict.candidate_forms,
        recommenders_forms=new_edict.recommenders_forms,
        edict_type=new_edict.type,
        is_open=new_edict.is_open,
        closed_date=new_edict.closed_date,

        date_application=edict_data.date_application,
        date_verification=edict_data.date_verification,
        date_evaluation=edict_data.date_evaluation,
        date_closed=edict_data.date_closed
    )
