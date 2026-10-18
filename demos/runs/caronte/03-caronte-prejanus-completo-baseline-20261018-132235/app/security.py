"""Authentication helpers: session user, dev shortcut and role checks."""
from fastapi import Depends, HTTPException, Request

from .config import settings
from .db import get_db
from .models import User

ADMIN_ROLES = {"administrator", "secretary", "coordinator"}


def _load_dev_user(db) -> User | None:
    """Local development shortcut: use the pre-existent DEV_USER_ID."""
    if settings.is_local and settings.DEV_USER_ID is not None:
        user = db.get(User, settings.DEV_USER_ID)
        if user is None:
            raise HTTPException(
                status_code=500,
                detail="DEV_USER_ID points to a non-existent user",
            )
        return user
    return None


def get_user(request: Request, db=Depends(get_db)) -> User | None:
    dev = _load_dev_user(db)
    if dev is not None:
        return dev
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    return db.get(User, user_id)


def require_user(request: Request, db=Depends(get_db)) -> User:
    user = get_user(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_admin(request: Request, db=Depends(get_db)) -> User:
    user = require_user(request, db)
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user