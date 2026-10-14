from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database.models.labels import Labels
from src.use_cases.auth.get_or_register_user import UserDTO
from sqlalchemy import update
from src.utils.get_edict_phase import check_edict_phase_by_submission

class LabelSchema(BaseModel):
    label: str
    color: str

class UserResponseSchema(BaseModel):
    id: int
    name: str

class LabelResponseSchema(BaseModel):
    id: int
    user: UserResponseSchema
    submission_id: int
    label: str


async def insert_label(submission_id: int, session: AsyncSession, label_data: LabelSchema, user: UserDTO) -> LabelResponseSchema:
    await check_edict_phase_by_submission(submission_id, ["avaliacao"], "label", session)
    
    new_label = Labels(
        user_id=user.id,
        submission_id=submission_id,
        label=label_data.label,
        color=label_data.color,
        context_type='candidate'
    )

    session.add(new_label)
    await session.commit()
    await session.refresh(new_label)

    stmt = (
        update(Labels)
        .where(Labels.user_id == user.id)
        .where(Labels.label == label_data.label)
        .where(Labels.context_type == 'candidate')
        .values(color=label_data.color)
    )

    await session.execute(stmt)
    await session.commit()
    await session.refresh(new_label)

    return LabelResponseSchema(
        id=new_label.id,
        user=UserResponseSchema(
            id=user.id,
            name=user.name,
        ),
        submission_id=new_label.submission_id,
        label=new_label.label
    )
