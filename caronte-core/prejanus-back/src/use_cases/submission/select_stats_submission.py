from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from src.infra.database.models.submission import StatsEnum, Submission
from src.infra.database.models.user import User
from src.infra.database.models.edict import Edict
from src.use_cases.dtos import UserDTO
from src.use_cases.exceptions import InsufficientRole
from src.use_cases.submission.exceptions import MultiplesAdvisors, UserNotFound
from src.use_cases.submission.exceptions import SubmissionNotFound, SubmissionNoInterest, EdictNotFound, EdictClosed
from src.utils import is_admin_role

class StatsSchema(BaseModel):
    user_ids: Optional[List[int]]
    stats: StatsEnum


async def select_stats_submission(
        submission_id: int, 
        user_ids: List[int], 
        stats: StatsEnum, 
        session: AsyncSession,
        user: UserDTO
    ):
    if not is_admin_role(user.role):
        raise InsufficientRole()
    
    submission_query = (
        select(Submission)
        .where(Submission.id == submission_id)
    )
    query_result = await session.execute(submission_query)
    submission = query_result.scalars().one_or_none()

    if submission is None:
        raise SubmissionNotFound(submission_id)
    
    edict_query = (
        select(Edict)
        .where(Edict.id == submission.edict_id)
    )
    edict_query_result = await session.execute(edict_query)
    edict = edict_query_result.scalars().one_or_none()
    
    if edict is None:
        raise EdictNotFound(submission.edict_id)
    
    if edict.is_open:
        if stats == StatsEnum.APPROVED:
            if user_ids is None:
                raise SubmissionNoInterest(submission_id)
            else:
                if len(user_ids) == 1:
                    if user_ids[0] is not None:
                        user_query = select(User).where(User.id == user_ids[0])
                        query_result = await session.execute(user_query)
                        advisor = query_result.scalars().one_or_none()

                        if advisor is None:
                            raise UserNotFound(user_ids[0])
                        
                        submission.advisor_id = advisor.id
                else:
                    return MultiplesAdvisors(submission_id)
        submission.stats = stats.value.lower()
        await session.commit()
        await session.refresh(submission)
    else:
        raise EdictClosed(submission.edict_id)