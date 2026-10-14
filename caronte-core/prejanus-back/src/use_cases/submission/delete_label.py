from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database.models.labels import Labels
from src.use_cases.dtos import UserDTO
from src.use_cases.submission.exceptions import CommentFromAnotherUser, CommentNotFound


async def delete_label(session: AsyncSession, label_id: int, user: UserDTO) -> None:
    label = await session.get(Labels, label_id)
    
    if label is None:
        raise CommentNotFound(label_id)
    
    if user.id != label.user_id:
        raise CommentFromAnotherUser(label_id)
    
    await session.delete(label)
    await session.commit()
    