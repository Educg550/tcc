import secrets

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from backend.db import SessionLocal
from backend.models import Session as SessionModel, User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_from_request(request: Request, db: OrmSession) -> User | None:
    token = request.cookies.get("session")
    if not token:
        return None
    sess = db.execute(
        select(SessionModel).where(SessionModel.token == token)
    ).scalar_one_or_none()
    if not sess:
        return None
    return db.get(User, sess.user_id)


def get_optional_user(
    request: Request, db: OrmSession = Depends(get_db)
) -> User | None:
    return get_user_from_request(request, db)


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Sessão necessária")
    return user


def new_session_token() -> str:
    return secrets.token_urlsafe(32)
