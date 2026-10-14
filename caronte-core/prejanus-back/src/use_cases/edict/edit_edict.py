from datetime import date, datetime
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database.models.edict import Edict
from src.use_cases.dtos import UserDTO
from src.use_cases.exceptions import InsufficientRole
from src.utils import is_admin_role


class EditEdictDateSchema(BaseModel):
    closed_date: date


class EditEdictDateResponse(EditEdictDateSchema):
    pass


class EditEdictSchema(BaseModel):
    title: str
    description: str
    year: str
    semester: str
    edict_type: str

    date_application: datetime
    date_verification: datetime
    date_evaluation: datetime
    date_closed: datetime

class EditEdictResponse(EditEdictSchema):
    pass


async def edit_edict_by_id(session: AsyncSession, edict_id: int, edict_data: EditEdictSchema, user: UserDTO) -> EditEdictResponse:
    if not is_admin_role(user.role):
        raise InsufficientRole()
    
    edict_to_update: Edict = await session.get(Edict, edict_id)

    assert edict_data.date_application < edict_data.date_verification < edict_data.date_evaluation < edict_data.date_closed, \
        "Edict phase dates must be in chronological order."

    edict_to_update.title=edict_data.title
    edict_to_update.description=edict_data.description
    edict_to_update.year=edict_data.year
    edict_to_update.semester=edict_data.semester
    edict_to_update.type=edict_data.edict_type
    edict_to_update.closed_date=edict_data.date_closed

    edict_phases = { edict_phase.phase: edict_phase for edict_phase in edict_to_update.edict_phases }
    edict_phases["inscricoes"].closed_date=edict_data.date_application

    edict_phases["homologacao"].closed_date=edict_data.date_evaluation

    edict_phases["avaliacao"].closed_date=edict_data.date_verification

    edict_phases["encerrado"].closed_date=edict_data.date_closed

    await session.commit()
    await session.refresh(edict_to_update)

    return edict_data


async def edit_date_edict_by_id(session: AsyncSession, edict_id: int, edict_data: EditEdictDateSchema, user: UserDTO) -> EditEdictDateResponse:
    if not is_admin_role(user.role):
        raise InsufficientRole()
    
    edict_to_update = await session.get(Edict, edict_id)
    edict_to_update.closed_date = edict_data.closed_date
    await session.commit()
    await session.refresh(edict_to_update)

    return EditEdictDateResponse(
        closed_date=edict_to_update.closed_date
    )
