from datetime import datetime, timezone
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database.models.comment import Comment
from src.use_cases.auth.get_or_register_user import UserDTO
from src.utils.get_edict_phase import check_edict_phase_by_submission

class CommentSchema(BaseModel):
    comment: str
    created_at: datetime | None = None  
    updated_at: datetime | None = None  


class UserResponseSchema(BaseModel):
    id: int
    name: str

class CommentResponseSchema(BaseModel):
    id: int
    user: UserResponseSchema
    submission_id: int
    comment: str
    created_at: datetime | None = None  
    updated_at: datetime | None = None  


async def insert_comment(submission_id: int, session: AsyncSession, comment_data: CommentSchema, user: UserDTO) -> CommentSchema:
    await check_edict_phase_by_submission(submission_id, ["avaliacao"], "comment", session)
    
    new_comment = Comment(
        user_id=user.id,
        submission_id=submission_id,
        comment=comment_data.comment,
        created_at=comment_data.created_at or datetime.now(tz=timezone.utc), 
        updated_at=comment_data.updated_at  
    )

    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)

    return CommentResponseSchema(
        id=new_comment.id,
        user=UserResponseSchema(
            id=user.id,
            name=user.name,
        ),
        submission_id=new_comment.submission_id,
        comment=new_comment.comment,
        created_at=new_comment.created_at,
        updated_at=new_comment.updated_at
    )
