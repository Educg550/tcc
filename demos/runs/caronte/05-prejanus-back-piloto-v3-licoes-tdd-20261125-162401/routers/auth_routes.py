import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select

import oauth
from auth import get_current_user
from database import SessionLocal
from models import User

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
    oauth_token: str | None = None,
    oauth_verifier: str | None = None,
):
    if not oauth_token:
        try:
            token, secret = await _in_thread(oauth.get_request_token)
        except oauth.OAuthError as e:
            raise HTTPException(status_code=500, detail=str(e))
        request.session["oauth_request"] = {"token": token, "secret": secret}
        return {"redirect_to": oauth.authorize_redirect(token)}

    stored = request.session.get("oauth_request")
    if not stored or stored.get("token") != oauth_token:
        raise HTTPException(status_code=401, detail="Sessão OAuth inválida")

    try:
        access_token, access_secret = await _in_thread(
            oauth.get_access_token, oauth_token, stored["secret"], oauth_verifier or ""
        )
        info = await _in_thread(oauth.get_user_info, access_token, access_secret)
    except oauth.OAuthError as e:
        raise HTTPException(status_code=500, detail=str(e))

    nusp = str(info.get("loginUsuario") or "")
    if nusp not in oauth.load_whitelist():
        raise HTTPException(status_code=403, detail="NUSP não autorizado")

    email = info.get("emailPrincipalUsuario") or ""
    name = info.get("nomeUsuario") or ""
    async with SessionLocal() as db:
        user = (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if user is None:
            user = User(
                email=email,
                name=name,
                role="teacher",
                nusp=nusp,
                created_at=datetime.now(timezone.utc),
            )
            db.add(user)
            await db.flush()
        elif not user.nusp:
            user.nusp = nusp
        request.session["user_id"] = user.id
        request.session.pop("oauth_request", None)
        await db.commit()
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "nusp": user.nusp,
            "role": user.role,
        }


async def _in_thread(fn, *args):
    return await asyncio.to_thread(fn, *args)
