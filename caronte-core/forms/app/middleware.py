from app.entities.User import User
from app.exceptions.error_messages import IDENTITY_PERMISSION_DENIED
from flask import current_app, session, abort
from functools import wraps
from app.services.user_service import exist_user
from senhaunicapy.identity import Identity
from app.persistence.db import db

from app.config import load_config
config = load_config()


def require_authorization(role="common"):
    def inner(callback):
        @wraps(callback)
        def decorator(*args, **kwargs):
            # Local dev bypass: skip SenhaUnica when DEV_USER_EMAIL is set in .env
            dev_email = config.get("DEV_USER_EMAIL")
            if dev_email:
                db_user = exist_user(db, User({"email": dev_email}))
                if not db_user.succeeded:
                    abort(401, description=IDENTITY_PERMISSION_DENIED())
                if role == "administrator" and db_user.data["role"] != "administrator":
                    abort(403, description=IDENTITY_PERMISSION_DENIED())
                res_user = {
                    "emailPrincipalUsuario": dev_email,
                    "id": db_user.data["id"],
                    "role": db_user.data["role"],
                }
                return callback(res_user, *args, **kwargs)

            config_senhaunica = current_app.extensions["senhaunicapy"].config

            if "access_token" not in session or "access_secret" not in session:
                abort(401, description=IDENTITY_PERMISSION_DENIED())

            try:
                user = Identity.get_protected_resources(session["access_token"], session["access_secret"], "wsusuario/oauth/usuariousp", "POST", config=config_senhaunica)
            except Exception:
                session.clear()
                abort(401, description=IDENTITY_PERMISSION_DENIED())

            db_user = exist_user(db, User({
                "email": user["emailPrincipalUsuario"]
            }))
            
            if not db_user.succeeded:
                session.clear()
                abort(401, description=IDENTITY_PERMISSION_DENIED())
                
            if role == "administrator" and db_user.data["role"] != "administrator":
                abort(403, description=IDENTITY_PERMISSION_DENIED())

            res_user = dict(user)
            res_user.update({ 
                "id": db_user.data["id"], "role": db_user.data["role"]
            })

            return callback(res_user, *args, **kwargs)
        return decorator
    return inner

def optional_authorization():
    def inner(callback):
        @wraps(callback)
        def decorator(*args, **kwargs):
            # Local dev bypass: skip SenhaUnica when DEV_USER_EMAIL is set in .env
            dev_email = config.get("DEV_USER_EMAIL")
            if dev_email:
                db_user = exist_user(db, User({"email": dev_email}))
                if not db_user.succeeded:
                    return callback(None, *args, **kwargs)
                res_user = {
                    "emailPrincipalUsuario": dev_email,
                    "id": db_user.data["id"],
                    "role": db_user.data["role"],
                }
                return callback(res_user, *args, **kwargs)

            config_senhaunica = current_app.extensions["senhaunicapy"].config

            if "access_token" not in session or "access_secret" not in session:
                return callback(None, *args, **kwargs)

            try:
                user = Identity.get_protected_resources(session["access_token"], session["access_secret"], "wsusuario/oauth/usuariousp", "POST", config=config_senhaunica)
            except Exception:
                session.clear()
                return callback(None, *args, **kwargs)

            db_user = exist_user(db, User({
                "email": user["emailPrincipalUsuario"]
            }))
            
            if not db_user.succeeded:
                session.clear()
                return callback(None, *args, **kwargs)
            
            res_user = dict(user)
            res_user.update({ 
                "id": db_user.data["id"], "role": db_user.data["role"]
            })

            return callback(res_user, *args, **kwargs)
        return decorator
    return inner