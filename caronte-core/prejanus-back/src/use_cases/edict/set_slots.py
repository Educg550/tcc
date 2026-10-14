from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database.models.user_edict_slots import UserEdictSlots
from src.use_cases.auth.get_or_register_user import UserDTO
from src.use_cases.edict.exceptions import SlotsTyping

class SlotsSchema(BaseModel):
    amount: str

class SlotsResponseSchema(BaseModel):
    amount: str


async def set_slots(edict_id: int, session: AsyncSession, slots_data: SlotsSchema, user: UserDTO) -> SlotsResponseSchema:
    value = 0
    if slots_data.amount != "":
        try:
            value = int(slots_data.amount)
            if value < 0:
                value = 0
        except ValueError:
            raise SlotsTyping()

    stmt = insert(UserEdictSlots).values(
        user_id=user.id,
        edict_id=edict_id,
        slots=value
    )

    stmt = stmt.on_conflict_do_update(
        index_elements=['user_id', 'edict_id'],
        set_={'slots': stmt.excluded.slots}
    )

    await session.execute(stmt)
    await session.commit()

    return SlotsResponseSchema(
        amount=str(value)
    )