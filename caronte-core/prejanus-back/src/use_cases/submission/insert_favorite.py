from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from src.infra.database.models.favorites import Favorites
from src.infra.database.models.user import User
from src.infra.database.models.submission import Submission
from src.use_cases.submission.exceptions import UserNotFound, SubmissionNotFound, FavoriteAlreadyExists
from src.utils.get_edict_phase import check_edict_phase_by_submission

async def insert_favorite(session: AsyncSession, user_id: int, submission_id: int):
    user_exists = await session.execute(select(User).where(User.id == user_id))
    if not user_exists.scalar():
        raise UserNotFound(user_id=user_id)

    submission_exists = await session.execute(select(Submission).where(Submission.id == submission_id))
    if not submission_exists.scalar():
        raise SubmissionNotFound(submission_id=submission_id)
    
    await check_edict_phase_by_submission(submission_id, ["avaliacao"], "favorite", session)

    new_favorite = Favorites(
        user_id=user_id,
        submission_id=submission_id,
        created_at=datetime.now(tz=timezone.utc)
    )

    session.add(new_favorite)
    
    try:
        await session.commit()
    except IntegrityError:
        raise FavoriteAlreadyExists(user_id=user_id, submission_id=submission_id)
