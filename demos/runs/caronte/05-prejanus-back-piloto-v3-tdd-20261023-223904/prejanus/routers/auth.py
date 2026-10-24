from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prejanus import oauth
from prejanus.auth import get_current_user, read_session, write_session
from prejanus.config import settings
from prejanus.db import get_db
from prejanus.models import User

router = APIRouter(tags=["auth"])


@router.get("/auth/login")
async def login(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "nusp": user.nusp,
        "role": user.role,
    }


@router.post("/auth/login/senhaunica")
async def login_senhaunica(
    request: Request,
    payload: dict = Body(default={}),
    db: AsyncSession = Depends(get_db),
):
    oauth_token = payload.get("oauth_token")
    if not oauth_token:
        try:
            token, secret = oauth.get_request_token()
        except Exception:
            raise HTTPException(500, "failed to obtain request token")
        response = JSONResponse({"redirect_to": oauth.authorize_url(token)})
        session = read_session(request)
        session["oauth_token"] = token
        session["oauth_secret"] = secret
        write_session(response, session)
        return response

    session = read_session(request)
    if session.get("oauth_token") != oauth_token or "oauth_secret" not in session:
        raise HTTPException(401, "missing request token secret in session")
    try:
        access_token, access_secret = oauth.get_access_token(
            oauth_token, session["oauth_secret"], payload.get("oauth_verifier", "")
        )
        info = oauth.get_user_info(access_token, access_secret)
    except Exception:
        raise HTTPException(500, "failed to complete senhaunica login")

    nusp = str(info.get("loginUsuario") or "")
    if nusp not in settings.whitelist:
        raise HTTPException(403, "user is not authorized")

    email = info.get("emailPrincipalUsuario") or ""
    name = info.get("nomeUsuario") or ""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(email=email, name=name, role="teacher", nusp=nusp)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    response = JSONResponse(
        {"message": "ok", "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}}
    )
    write_session(response, {"user_id": user.id})
    return response
