from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text

from auth import (
    authorize_redirect,
    fetch_user,
    get_current_user,
    load_whitelist,
    oauth_access_token,
    oauth_request_token,
    oauth_user_data,
)
from database import SessionLocal

router = APIRouter(tags=["auth"])


@router.get("/auth/login")
async def login(user: dict = Depends(get_current_user)):
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "nusp": user["nusp"],
        "role": user["role"],
    }


@router.post("/auth/login/senhaunica")
async def login_senhaunica(
    request: Request,
    oauth_token: str | None = None,
    oauth_verifier: str | None = None,
):
    if not oauth_token:
        token, secret = oauth_request_token()
        secrets = request.session.get("oauth_secrets", {})
        secrets[token] = secret
        request.session["oauth_secrets"] = secrets
        return {"redirect_to": authorize_redirect(token)}

    secrets = request.session.get("oauth_secrets", {})
    secret = secrets.get(oauth_token)
    if not secret:
        raise HTTPException(status_code=401, detail="Sessão sem segredo de retorno")

    access_token, access_secret = oauth_access_token(oauth_token, secret, oauth_verifier or "")
    secrets.pop(oauth_token, None)
    request.session["oauth_secrets"] = secrets

    data = oauth_user_data(access_token, access_secret)
    nusp = str(data.get("loginUsuario") or "")
    name = data.get("nomeUsuario") or ""
    email = data.get("emailPrincipalUsuario") or ""

    whitelist = load_whitelist()
    if whitelist and nusp not in whitelist:
        raise HTTPException(status_code=403, detail="NUSP não autorizado")

    async with SessionLocal() as session:
        rows = await session.execute(
            text('select * from "user" where email = :email'), {"email": email}
        )
        existing = rows.fetchone()
        if existing:
            user_id = existing.id
            role = existing.role
        else:
            rows = await session.execute(
                text(
                    'insert into "user" (email, name, role, nusp, created_at)'
                    " values (:email, :name, 'teacher', :nusp, now()) returning id, role"
                ),
                {"email": email, "name": name, "nusp": nusp},
            )
            await session.commit()
            row = rows.fetchone()
            user_id = row.id
            role = row.role
    request.session["user_id"] = user_id
    user = await fetch_user(user_id)
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "nusp": user["nusp"],
        "role": role,
    }
