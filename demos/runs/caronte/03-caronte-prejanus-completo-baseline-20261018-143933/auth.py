"""Identidade, sessão e papéis."""
from fastapi import Depends, HTTPException, Request

from config import settings
from db import get_db
from models import User

ADMIN_ROLES = {"administrator", "secretary", "coordinator"}


def current_user(request: Request, db=Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if settings.APP_ENV == "local" and settings.DEV_USER_ID:
        user_id = settings.DEV_USER_ID
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user
