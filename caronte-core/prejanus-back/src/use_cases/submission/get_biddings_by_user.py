
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from src.infra.database.models.labels import Labels
from sqlalchemy.ext.asyncio import AsyncSession


async def get_biddings_by_user(
    submission_id: int,
    user_id: int,
    session: AsyncSession
) -> Labels | None:
    bidding_query = (
        select(Labels)
        .where(Labels.submission_id == submission_id)
        .where(Labels.user_id == user_id)
        .where(Labels.context_type == 'bidding')
        .options(selectinload(Labels.user))
    )
    bidding_result = await session.execute(bidding_query)
    return bidding_result.scalars().one_or_none()