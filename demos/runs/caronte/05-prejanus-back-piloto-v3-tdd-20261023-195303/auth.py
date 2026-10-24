from fastapi import Depends, HTTPException, Request

from config import settings
from database import PrejanusSession
from services.common import get_user_row

ADMIN_ROLES = {"administrator", "secretary", "coordinator"}


def _user_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "nusp": row["nusp"],
        "role": row["role"],
    }


def get_current_user(request: Request):
    user = None
    uid = request.session.get("user_id")
    if uid is not None:
        with PrejanusSession() as ps:
            row = get_user_row(ps, uid)
            if row is not None:
                user = _user_dict(row)
    if user is None and settings.app_env == "local" and settings.dev_user_id is not None:
        with PrejanusSession() as ps:
            row = get_user_row(ps, settings.dev_user_id)
            if row is None:
                raise HTTPException(status_code=500, detail="DEV_USER_ID não corresponde a um usuário cadastrado")
            user = _user_dict(row)
    if user is None:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user


def require_admin(user=Depends(get_current_user)):
    if user["role"] not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Operação restrita a papéis administrativos")
    return user
