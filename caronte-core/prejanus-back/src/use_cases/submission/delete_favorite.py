from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.infra.database.models.favorites import Favorites
from src.use_cases.submission.exceptions import FavoriteNotFound

async def delete_favorite(session: AsyncSession, user_id: int, submission_id: int):
    query = select(Favorites).where(
        Favorites.user_id == user_id,
        Favorites.submission_id == submission_id
    )
    result = await session.execute(query)
    favorite = result.scalar()

    if not favorite:
        raise FavoriteNotFound(user_id=user_id, submission_id=submission_id)

    await session.delete(favorite)
    await session.commit()
