from typing import Optional
from pydantic import BaseModel

from src.use_cases.dtos import UserDTO
from sqlalchemy import select
from src.infra.database.models.labels import Labels
from sqlalchemy.ext.asyncio import AsyncSession
from src.use_cases.submission.schemas import BiddingEnum
from src.utils import is_admin_role



class BiddingSchema(BaseModel):
    bidding: BiddingEnum
    user_id: Optional[int] = None


async def change_bidding_by_submission(
    auth_user: UserDTO,
    submission_id: int,
    bidding: BiddingSchema, 
    session: AsyncSession
):
    if not is_admin_role(auth_user.role) or bidding.user_id is None:
        bidding.user_id = auth_user.id

    labels_query = (
        select(Labels)
        .where(Labels.user_id == bidding.user_id)
        .where(Labels.submission_id == submission_id)
        .where(Labels.context_type == 'bidding')
        .distinct(Labels.label)
    )
    labels_result = await session.execute(labels_query)
    label: Labels = labels_result.scalars().one_or_none()

    if label is None:
        new_label = Labels(
            user_id=bidding.user_id,
            submission_id=submission_id,
            label=bidding.bidding.value,
            color='',
            context_type='bidding'
        )

        session.add(new_label)
    else:
        label.label = bidding.bidding.value
    await session.commit()