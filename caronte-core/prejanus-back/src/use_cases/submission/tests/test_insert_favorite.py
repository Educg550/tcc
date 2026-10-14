import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database.models.favorites import Favorites
from src.infra.database.models.user import User
from src.infra.database.models.submission import Submission
from src.use_cases.submission.insert_favorite import insert_favorite
from src.use_cases.submission.exceptions import UserNotFound, SubmissionNotFound, FavoriteAlreadyExists
pytestmark = pytest.mark.anyio

@pytest.mark.usefixtures("user_a", "submission_a")
async def test_insert_favorite_user_not_found(session: AsyncSession, submission_a: Submission):
    
    with pytest.raises(UserNotFound):
        await insert_favorite(session=session, user_id=999, submission_id=submission_a.id)


@pytest.mark.usefixtures("user_a", "submission_a")
async def test_insert_favorite_submission_not_found(session: AsyncSession, user_a: User):
    
    with pytest.raises(SubmissionNotFound):
        await insert_favorite(session=session, user_id=user_a.id, submission_id=999)


@pytest.mark.usefixtures("user_a", "submission_a")
async def test_insert_favorite_already_exists(session: AsyncSession, user_a: User, submission_a: Submission):
    await insert_favorite(session=session, user_id=user_a.id, submission_id=submission_a.id)

    with pytest.raises(FavoriteAlreadyExists):
        await insert_favorite(session=session, user_id=user_a.id, submission_id=submission_a.id)


@pytest.mark.usefixtures("user_a", "submission_a")
async def test_insert_favorite_success(session: AsyncSession, user_a: User, submission_a: Submission):
    await insert_favorite(session=session, user_id=user_a.id, submission_id=submission_a.id)

    favorite = await session.get(Favorites, (user_a.id, submission_a.id))
    assert favorite is not None
    assert favorite.user_id == user_a.id
    assert favorite.submission_id == submission_a.id