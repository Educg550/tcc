from fastapi import Depends, HTTPException, Request
from sqlalchemy import text

from config import settings
from database import Session

ADMIN_ROLES = {"administrator", "secretary", "coordinator"}


def get_user_row(user_id):
    with Session() as s:
        row = s.execute(
            text('select id, name, email, nusp, role from "user" where id = :i'),
            {"i": user_id},
        ).mappings().first()
        return dict(row) if row else None


def current_user(request: Request):
    if settings.is_local and settings.dev_user_id:
        user = get_user_row(int(settings.dev_user_id))
        if user is None:
            raise HTTPException(status_code=500, detail="DEV_USER_ID does not exist")
        return user
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = get_user_row(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_admin(user=Depends(current_user)):
    if user["role"] not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Administrator role required")
    return user
