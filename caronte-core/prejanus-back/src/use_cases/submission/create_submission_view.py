from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from src.infra.database.models.submission_view import SubmissionView
from src.use_cases.auth.get_or_register_user import UserDTO


# TODO Adicionar restrição no banco de dados
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo # Disponível a partir do Python 3.9

# TODO Adicionar restrição no banco de dados
async def create_submission_view(
    submission_id: int,
    session: AsyncSession,
    auth_user: UserDTO
) -> SubmissionView | None:

    tz = ZoneInfo("America/Sao_Paulo")
    now = datetime.now(tz)
    start_of_day = datetime(now.year, now.month, now.day, tzinfo=tz)
    end_of_day = start_of_day + timedelta(days=1)

    query = (
        select(func.count())
        .select_from(SubmissionView)
        .where(SubmissionView.user_id == auth_user.id)
        .where(SubmissionView.submission_id == submission_id)
        .where(SubmissionView.created_at >= start_of_day)
        .where(SubmissionView.created_at < end_of_day)
    )

    result = await session.execute(query)
    count = result.scalar_one()

    if count > 0:
        return None

    new_submission_view = SubmissionView(
        user_id=auth_user.id,
        submission_id=submission_id
    )

    session.add(new_submission_view)
    await session.commit()

    return new_submission_view
