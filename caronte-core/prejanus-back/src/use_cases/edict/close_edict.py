from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database.models.edict import Edict
from src.use_cases.dtos import UserDTO
from src.use_cases.edict.exceptions import AlreadyClosedEdict
from src.use_cases.exceptions import InsufficientRole
from src.use_cases.submission.exceptions import EdictNotFound
from datetime import date

from src.utils import is_admin_role

class CloseEdictSchema(BaseModel):
    confirmation_deadline: date
    send_approval_letter: bool


async def close_edict_by_id(session: AsyncSession, edict_id: int, user: UserDTO):
    if not is_admin_role(user.role):
        raise InsufficientRole()
    
    edict_query = select(Edict).where(Edict.id == edict_id)
    query_result = await session.execute(edict_query)
    edict = query_result.scalars().one_or_none()

    if edict is None:
        raise EdictNotFound(edict_id)

    if not edict.is_open:
        raise AlreadyClosedEdict()

    edict.is_open = False

    await session.commit()

    await session.refresh(edict)