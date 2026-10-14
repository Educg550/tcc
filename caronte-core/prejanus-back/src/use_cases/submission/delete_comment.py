from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database.models.comment import Comment
from src.use_cases.dtos import UserDTO
from src.use_cases.submission.exceptions import CommentFromAnotherUser, CommentNotFound


async def delete_comment(session: AsyncSession, comment_id: int, user: UserDTO) -> None:
    comment = await session.get(Comment, comment_id)
    
    if comment is None:
        raise CommentNotFound(comment_id)
    
    if user.id != comment.user_id:
        raise CommentFromAnotherUser(comment_id)
    
    await session.delete(comment)
    await session.commit()
    