from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database.models.user import RolesEnum, User
from src.use_cases.dtos import UserDTO


class SenhaunicaUserSchema(BaseModel):
    email: str
    name: str
    nusp: str


async def get_or_register_user(senhaunica_user: SenhaunicaUserSchema, session: AsyncSession) -> UserDTO:
    query = select(User).filter_by(email=senhaunica_user.email)
    result = await session.execute(query)
    user = result.scalars().one_or_none()

    if user:
        return UserDTO(
            id=user.id,
            email=user.email,
            name=user.name,
            nusp=user.nusp,
            role=user.role
        )

    user = User(
        email=senhaunica_user.email,
        name=senhaunica_user.name,
        role=RolesEnum.TEACHER,
        nusp=senhaunica_user.nusp
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user
