from fastapi import Depends, HTTPException, Request
from itsdangerous import BadSignature, URLSafeSerializer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db import get_session

COOKIE_NAME = 'session'
SESSION_MAX_AGE = 28800
ADMIN_ROLES = {'admin', 'administrator', 'secretary', 'secretaria',
               'coordinator', 'coordenador'}


def _serializer() -> URLSafeSerializer:
    return URLSafeSerializer(get_settings().secret_key)


def make_session_cookie(user_id: int) -> str:
    return _serializer().dump(user_id)


async def get_current_user(request: Request,
                           session: AsyncSession = Depends(get_session)) -> dict:
    settings = get_settings()
    user_id = None
    cookie = request.cookies.get(COOKIE_NAME)
    if cookie:
        try:
            user_id = _serializer().load(cookie)
        except BadSignature:
            user_id = None
    if user_id is None and settings.app_env == 'local' and settings.dev_user_id:
        user_id = settings.dev_user_id
    if user_id is None:
        raise HTTPException(status_code=401, detail='Not authenticated')
    row = (await session.execute(
        text('SELECT id, name, email, nusp, role FROM "user" WHERE id = :i'),
        {'i': user_id})).first()
    if row is None:
        raise HTTPException(status_code=401, detail='Not authenticated')
    return dict(row._mapping)


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user['role'] not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail='Administrative role required')
    return user
