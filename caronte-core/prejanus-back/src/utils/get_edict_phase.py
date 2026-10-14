from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.infra.database.models.edict import Edict
from src.infra.database.models.submission import Submission
from src.use_cases.submission.exceptions import IncorrectActionInPphase

async def get_edict_phase_by_submission(submission_id: int, session: AsyncSession) -> str:
    edict_query = (
    select(Edict)
        .join(Submission, Submission.edict_id == Edict.id)
        .where(Submission.id == submission_id)
    )
    result = await session.execute(edict_query)
    edict: Edict = result.scalars().first()

    return edict.phase

async def check_edict_phase_by_submission(submission_id: int, phases: list[str], description: str, session: AsyncSession,):
    edict_phase = await get_edict_phase_by_submission(submission_id, session)
    if edict_phase not in phases:
        raise IncorrectActionInPphase(
            description,
            edict_phase
        )