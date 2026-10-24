"""Sessão assinada por cookie e controle de acesso por papel."""
from fastapi import Depends, HTTPException, Request
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import text

from .config import settings
from .db import get_db

COOKIE_NAME = "session"
SESSION_MAX_AGE = 28800
ADMIN_ROLES = {"administrator", "secretary", "coordinator"}


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.secret_key)


def sign_session(user_id: int) -> str:
    return _serializer().dumps(user_id)


def set_session_cookie(response, user_id: int) -> None:
    response.set_cookie(
        COOKIE_NAME,
        sign_session(user_id),
        max_age=SESSION_MAX_AGE,
        secure=True,
        samesite="lax",
        httponly=True,
    )


def load_user(db, user_id):
    row = db.execute(
        text('SELECT id, name, email, nusp, role FROM "user" WHERE id = :i'),
        {"i": user_id},
    ).mappings().first()
    return dict(row) if row else None


def get_current_user(request: Request, db):
    value = request.cookies.get(COOKIE_NAME)
    if not value:
        return None
    try:
        user_id = _serializer().loads(value, max_age=SESSION_MAX_AGE)
    except Exception:
        return None
    if user_id is None:
        return None
    return load_user(db, user_id)


def dev_user(db):
    if settings.app_env == "local" and settings.dev_user_id:
        return load_user(db, settings.dev_user_id)
    return None


def require_user(request: Request, db=Depends(get_db)):
    user = get_current_user(request, db) or dev_user(db)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_admin(user=Depends(require_user)):
    if user["role"] not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user
