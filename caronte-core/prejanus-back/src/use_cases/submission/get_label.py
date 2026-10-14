from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database.models.labels import Labels
from sqlalchemy.orm import selectinload


class UserResponseSchema(BaseModel):
    id: int
    name: str

class LabelSchema(BaseModel):
    id: int
    label: str
    color: str

class UserLabelResponseSchema(BaseModel):
    labels: list[LabelSchema]


async def get_label_by_userid(submission_id: int, user_id: int, session: AsyncSession) -> UserLabelResponseSchema:
    labels_query = (
        select(Labels)
        .where(Labels.user_id == user_id)
        .where(Labels.context_type == 'candidate')
        .options(selectinload(Labels.user))
        .distinct(Labels.label)
    )
    labels_result = await session.execute(labels_query)
    labels = labels_result.scalars().all()

    return UserLabelResponseSchema( 
        labels=[ { "label": label.label, "color": label.color, "id": label.id } for label in labels ] 
    )
