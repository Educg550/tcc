from fastapi import HTTPException, Request, Response
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import text

from .config import settings
from .db import engine

serializer = URLSafeTimedSerializer(settings.secret_key, salt='prejanus-session')
COOKIE = 'session'
MAX_AGE = 28800
STAFF_ROLES = {'administrator', 'secretary', 'coordinator'}


def set_session(response: Response, user_id: int) -> None:
    response.set_cookie(COOKIE, serializer.dumps(user_id), max_age=MAX_AGE,
                        secure=True, samesite='lax', httponly=True)


def _load_user(uid: int) -> dict | None:
    with engine.connect() as conn:
        row = conn.execute(
            text('SELECT id, name, email, nusp, role FROM "user" WHERE id = :uid'),
            {'uid': uid}).mappings().first()
    return dict(row) if row else None


def current_user(request: Request) -> dict:
    uid = None
    raw = request.cookies.get(COOKIE)
    if raw:
        try:
            uid = serializer.loads(raw, max_age=MAX_AGE)
        except Exception:
            uid = None
    if uid is None and settings.is_local and settings.dev_user_id:
        uid = settings.dev_user_id
    if uid is None:
        raise HTTPException(status_code=401, detail='Não autenticado')
    user = _load_user(uid)
    if user is None:
        raise HTTPException(status_code=401, detail='Usuário inválido')
    return user


def require_staff(user: dict) -> dict:
    if user['role'] not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail='Sem permissão')
    return user
