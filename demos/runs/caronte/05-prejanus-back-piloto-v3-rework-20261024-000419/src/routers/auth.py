"""Rotas de autenticação: atalho local e login pela Senha Única."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import text

from .. import oauth
from ..auth import dev_user, get_current_user, load_user, set_session_cookie
from ..config import settings
from ..db import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def _authorize_url() -> str:
    url = settings.senhaunica_authorize_url
    if not url.startswith("http"):
        url = settings.senhaunica_oauth_host.rstrip("/") + url
    return url


@router.get("/login")
def login(request: Request, response: Response, db=Depends(get_db)):
    user = get_current_user(request, db)
    if user is None:
        user = dev_user(db)
        if user is not None:
            set_session_cookie(response, user["id"])
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.post("/login/senhaunica")
def login_senhaunica(
    request: Request,
    response: Response,
    oauth_token: str | None = Query(default=None),
    oauth_verifier: str | None = Query(default=None),
    db=Depends(get_db),
):
    if not oauth_token or not oauth_verifier:
        token = oauth.start_login()
        url = _authorize_url()
        separator = "&" if "?" in url else "?"
        redirect_to = (
            f"{url}{separator}oauth_token={token}"
            f"&callback_id={settings.senhaunica_callback_id}"
        )
        return {"redirect_to": redirect_to}

    try:
        access_token, access_secret = oauth.exchange(oauth_token, oauth_verifier)
        info = oauth.user_info(access_token, access_secret)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"authentication failed: {exc}")

    nusp = str(info.get("loginUsuario") or "")
    if not oauth.nusp_allowed(nusp):
        raise HTTPException(status_code=403, detail="NUSP not authorized")
    email = str(info.get("emailPrincipalUsuario") or "")
    name = str(info.get("nomeUsuario") or "")

    row = db.execute(
        text('SELECT id FROM "user" WHERE nusp = :n'), {"n": nusp}
    ).first()
    if row is None and email:
        row = db.execute(
            text('SELECT id FROM "user" WHERE email = :e'), {"e": email}
        ).first()
    if row is None:
        db.execute(
            text('INSERT INTO "user" (email, name, role, nusp, created_at) '
                 "VALUES (:e, :n, 'teacher', :u, now())"),
            {"e": email, "n": name, "u": nusp},
        )
        db.commit()
        row = db.execute(
            text('SELECT id FROM "user" WHERE nusp = :n'), {"n": nusp}
        ).first()
    user = load_user(db, row[0])
    set_session_cookie(response, user["id"])
    return user
