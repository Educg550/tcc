from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import COOKIE_NAME, SESSION_MAX_AGE, get_current_user, make_session_cookie
from src.db import get_session
from src.oauth import build_redirect, get_request_token, get_user

router = APIRouter(prefix='/auth', tags=['auth'])


def _whitelist() -> set[str]:
    path = Path('data/nusp_whitelist.txt')
    if not path.is_file():
        return set()
    raw = path.read_text()
    return {t.strip() for t in raw.replace(',', ' ').split() if t.strip()}


@router.get('/login')
async def login(user: dict = Depends(get_current_user)):
    return user


@router.post('/login/senhaunica')
async def login_senhaunica(response: Response,
                           oauth_token: str | None = None,
                           oauth_verifier: str | None = None,
                           oauth_token_secret: str | None = None,
                           session: AsyncSession = Depends(get_session)):
    if not oauth_token:
        token = get_request_token()
        return {'redirect_to': build_redirect(token)}
    info = get_user(oauth_token, oauth_verifier, oauth_token_secret)
    nusp = str(info.get('loginUsuario') or '')
    if nusp not in _whitelist():
        raise HTTPException(status_code=403, detail='NUSP not authorized')
    email = info.get('emailPrincipalUsuario')
    name = info.get('nomeUsuario') or email or nusp
    row = (await session.execute(text(
        'SELECT id, name, email, nusp, role FROM "user" '
        'WHERE email = :e OR nusp = :n LIMIT 1'),
        {'e': email, 'n': nusp})).first()
    if row is None:
        row = (await session.execute(text(
            'INSERT INTO "user" (email, name, role, nusp, created_at) '
            "VALUES (:e, :n, 'teacher', :u, now()) "
            'RETURNING id, name, email, nusp, role'),
            {'e': email, 'n': name, 'u': nusp})).first()
        await session.commit()
    user = dict(row._mapping)
    response.set_cookie(COOKIE_NAME, make_session_cookie(user['id']),
                        max_age=SESSION_MAX_AGE, secure=True, samesite='lax',
                        httponly=True)
    return user
