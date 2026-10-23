"""Rotas de autenticação."""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import text

from auth import oauth
from auth.session import CurrentUser, get_current_user, set_session_cookie
from config import WHITELIST_PATH
from database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def _whitelist() -> set[str]:
    try:
        raw = Path(WHITELIST_PATH).read_text(encoding="utf-8")
    except OSError:
        return set()
    return {part.strip() for line in raw.splitlines() for part in line.split(",") if part.strip()}


@router.get("/login")
async def login(user: CurrentUser = Depends(get_current_user)):
    return user.as_dict()


@router.post("/login/senhaunica")
async def login_senhaunica(
    response: Response,
    oauth_token: str | None = None,
    oauth_verifier: str | None = None,
    db=Depends(get_db),
):
    if not oauth_token or not oauth_verifier:
        token, secret = oauth.get_request_token()
        oauth.REQUEST_SECRETS[token] = secret
        return {"redirect_to": oauth.authorize_redirect_url(token)}

    secret = oauth.REQUEST_SECRETS.pop(oauth_token, None)
    if secret is None:
        raise HTTPException(status_code=500, detail="oauth_token desconhecido")
    try:
        access_token, access_secret = oauth.get_access_token(oauth_token, secret, oauth_verifier)
        info = oauth.get_user_info(access_token, access_secret)
    except Exception as exc:  # provedor recusou o verifier/token
        raise HTTPException(status_code=500, detail=f"Falha no OAuth: {exc}")

    nusp = str(info.get("loginUsuario") or "")
    if nusp not in _whitelist():
        raise HTTPException(status_code=403, detail="NUSP não autorizado")

    email = info.get("emailPrincipalUsuario")
    name = info.get("nomeUsuario") or email
    row = (
        await db.execute(
            text('SELECT id, name, email, nusp, role FROM "user" WHERE email = :e'),
            {"e": email},
        )
    ).first()
    if row is None:
        row = (
            await db.execute(
                text(
                    'INSERT INTO "user"(email, name, role, nusp, created_at) '
                    "VALUES (:e, :n, 'teacher', :u, now()) "
                    "RETURNING id, name, email, nusp, role"
                ),
                {"e": email, "n": name, "u": nusp},
            )
        ).first()
        await db.commit()
    user = CurrentUser(*row)
    set_session_cookie(response, user.id)
    return user.as_dict()
