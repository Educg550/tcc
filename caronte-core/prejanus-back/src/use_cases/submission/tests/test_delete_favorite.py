import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database.models.favorites import Favorites
from src.infra.database.models.submission import Submission
from src.infra.database.models.user import User
from src.use_cases.submission.delete_favorite import delete_favorite
from src.use_cases.submission.exceptions import FavoriteNotFound
from src.use_cases.submission.insert_favorite import insert_favorite

pytestmark = pytest.mark.anyio

@pytest.mark.usefixtures("user_a", "submission_a")
async def test_delete_favorite_success(session: AsyncSession, user_a: User, submission_a: Submission):
    await insert_favorite(session=session, user_id=user_a.id, submission_id=submission_a.id)

    await delete_favorite(session=session, user_id=user_a.id, submission_id=submission_a.id)

    favorite = await session.get(Favorites, (user_a.id, submission_a.id))
    assert favorite is None

@pytest.mark.usefixtures("user_a", "submission_a")
async def test_delete_favorite_not_found(session: AsyncSession, user_a: User, submission_a: Submission):
    with pytest.raises(FavoriteNotFound):
        await delete_favorite(session=session, user_id=user_a.id, submission_id=submission_a.id)