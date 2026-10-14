import pytest
from datetime import datetime
from sqlalchemy.future import select
from src.infra.database.models.comment import Comment
from src.use_cases.dtos import UserDTO
from src.use_cases.submission.insert_comment import CommentSchema, insert_comment  # Supondo que o CommentSchema está neste módulo

@pytest.mark.anyio
async def test_insert_comment(submission_a, session, user_a):
    # Dados de entrada para o teste
    comment_data = CommentSchema(
        comment="Este é um comentário de teste"
    )

    # Insere o comentário
    result = await insert_comment(submission_a.id, session, comment_data, user=UserDTO(id=user_a.id, name=user_a.name, email=user_a.email, nusp=user_a.nusp))

    # Verifica se resultado retornado corresponde ao que foi inserido
    assert result.user.id == user_a.id
    assert result.submission_id == submission_a.id
    assert result.comment == comment_data.comment

    # Verifica se `created_at` foi gerado corretamente
    assert isinstance(result.created_at, datetime)
    #assert result.created_at.tzinfo == timezone.utc

    # Verifica se o comentário foi realmente inserido no banco de dados
    inserted_comment = await session.execute(select(Comment).where(Comment.id == result.id))
    inserted_comment = inserted_comment.scalars().first()

    assert inserted_comment is not None
    assert inserted_comment.comment == comment_data.comment
