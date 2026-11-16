from collections.abc import AsyncIterator

from fastapi import Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import FormsSessionLocal, SessionLocal
from models import User

ADMIN_ROLES = {"administrator", "secretary", "coordinator"}

# A carga inicial de dados pode inserir ids explícitos sem avançar as
# sequências, o que faria as inserções da aplicação falharem com chave
# duplicada. Como a carga pode ocorrer depois da inicialização do processo,
# alinhamos cada sequência de coluna `id` com o maior id presente na tabela
# no início de cada requisição, na própria transação da sessão.
_SEQUENCE_SYNC = text(
    """
do $$
declare
  r record;
begin
  for r in
    select quote_ident(seq.relname) as seqname,
           quote_ident(tab.relname) as tablename
    from pg_class seq
    join pg_depend dep on dep.objid = seq.oid
      and dep.refclassid = 'pg_class'::regclass and dep.deptype in ('a', 'i')
    join pg_class tab on tab.oid = dep.refobjid
    join pg_namespace ns on ns.oid = tab.relnamespace
    join pg_attribute att on att.attrelid = tab.oid
      and att.attnum = dep.refobjsubid
    where seq.relkind = 'S' and ns.nspname = 'public' and att.attname = 'id'
  loop
    execute format(
      'select setval(%L, coalesce((select max(id) from %I), 0) + 1, false)',
      r.seqname, r.tablename);
  end loop;
end $$;
"""
)


async def _sync_sequences(session: AsyncSession) -> None:
    try:
        await session.execute(_SEQUENCE_SYNC)
    except Exception:
        # Sem permissão ou catálogo indisponível: não derruba a requisição.
        await session.rollback()


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        await _sync_sequences(session)
        yield session


async def get_forms_db() -> AsyncIterator[AsyncSession]:
    async with FormsSessionLocal() as session:
        await _sync_sequences(session)
        yield session


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    from config import settings

    if settings.is_local and settings.dev_user_id is not None:
        user = await db.get(User, settings.dev_user_id)
        if user is None:
            raise HTTPException(
                status_code=500,
                detail="DEV_USER_ID aponta para um usuário inexistente",
            )
        return user

    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação administrativa")
    return user
