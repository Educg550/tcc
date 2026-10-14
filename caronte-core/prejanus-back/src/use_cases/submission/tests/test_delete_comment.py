import pytest
from fastapi import HTTPException
from src.infra.database.models.comment import Comment
from src.use_cases.dtos import UserDTO
from src.use_cases.submission.delete_comment import delete_comment

# Testes para a função delete_comment
@pytest.mark.anyio
async def test_delete_comment_success(session, user_a, submission_a):
    # Cria um comentário para o teste
    comment = Comment(
        user_id=user_a.id,
        submission_id=submission_a.id,
        comment="Este é um comentário de teste."
    )
    session.add(comment)
    await session.commit()
    
    # Verifica se o comentário foi adicionado
    fetched_comment = await session.get(Comment, comment.id)
    assert fetched_comment is not None

    # Deleta o comentário
    await delete_comment(session, comment.id, user=UserDTO(id=user_a.id, name=user_a.name, email=user_a.email, nusp=user_a.nusp))

    # Verifica se o comentário foi deletado
    deleted_comment = await session.get(Comment, comment.id)
    assert deleted_comment is None

@pytest.mark.anyio
async def test_delete_comment_not_found(session):
    # Tenta deletar um comentário que não existe
    with pytest.raises(HTTPException) as exc_info:
        await delete_comment(session, 999, user=UserDTO(id=1, name='MOCK', email='mock@email.com', nusp='123123'))  # ID que não existe

    # Verifica se a exceção levantada tem o status e detalhe corretos
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Comment with id 999 was not found."
