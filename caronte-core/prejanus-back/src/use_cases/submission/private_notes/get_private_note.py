from src.infra.database.models.private_note import PrivateNote
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def get_private_note(
    session: AsyncSession,
    user_id: int,
    submission_id: int,
) -> PrivateNote: 
    stmt = select(PrivateNote).where(
        PrivateNote.user_id == user_id,
        PrivateNote.submission_id == submission_id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()