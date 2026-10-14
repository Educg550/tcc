from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.infra.database.models.edict import Edict
from src.use_cases.dtos import UserDTO
from src.use_cases.exceptions import InsufficientRole
from src.use_cases.submission.exceptions import EdictNotFound
from src.utils import is_admin_role

async def remove_edict_by_id(session: AsyncSession, edict_id: int, user: UserDTO):
    if not is_admin_role(user.role):
        raise InsufficientRole()
    
    stmt = (
        select(Edict)
        .where(Edict.id == edict_id)
        .options(joinedload(Edict.edict_phases))
    )
    edict = await session.scalar(stmt)

    if edict is None:
        raise EdictNotFound(edict_id)

    await session.delete(edict)
    await session.commit()