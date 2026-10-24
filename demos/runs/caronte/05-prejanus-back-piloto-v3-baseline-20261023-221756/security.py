from fastapi import Depends, HTTPException, Request
from sqlalchemy import text

from config import settings
from db import PrejanusSession

ADMIN_ROLES = {"administrator", "secretary", "coordinator"}

USER_COLS = 'id, name, email, role, nusp'


async def fetch_user(user_id: int):
    async with PrejanusSession() as s:
        return (
            await s.execute(text(f'select {USER_COLS} from "user" where id = :i'), {"i": user_id})
        ).mappings().first()


async def get_current_user(request: Request):
    """Resolve the authenticated user, or raise 401/500."""
    if settings.APP_ENV == "local" and settings.DEV_USER_ID is not None:
        user_id = settings.DEV_USER_ID
        missing_is_config_error = True
    else:
        user_id = request.session.get("user_id")
        missing_is_config_error = False
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = await fetch_user(user_id)
    if user is None:
        if missing_is_config_error:
            raise HTTPException(status_code=500, detail="DEV_USER_ID does not exist")
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def require_admin(user=Depends(get_current_user)):
    if user["role"] not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Administrative role required")
    return user
