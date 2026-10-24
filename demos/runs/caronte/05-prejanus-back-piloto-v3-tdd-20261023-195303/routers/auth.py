from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text

from auth import get_current_user
from config import settings
from database import PrejanusSession
from services import oauth

router = APIRouter(tags=["auth"])


@router.get("/auth/login")
def login(user=Depends(get_current_user)):
    return user


@router.post("/auth/login/senhaunica")
async def login_senhaunica(request: Request):
    form = await request.form()
    oauth_token = form.get("oauth_token")
    oauth_verifier = form.get("oauth_verifier")

    if not oauth_token:
        try:
            token, secret = oauth.fetch_request_token()
        except Exception:
            raise HTTPException(status_code=500, detail="Falha ao obter o request token")
        request.session["oauth_token"] = token
        request.session["oauth_token_secret"] = secret
        return {"redirect_to": oauth.authorize_url(token)}

    token_secret = request.session.get("oauth_token_secret")
    if not token_secret:
        raise HTTPException(status_code=401, detail="Sessão OAuth inexistente")

    try:
        access_token, access_secret = oauth.fetch_access_token(oauth_token, token_secret, oauth_verifier)
        user_data = oauth.fetch_user_data(access_token, access_secret)
    except Exception:
        raise HTTPException(status_code=500, detail="Falha na troca de tokens")

    nusp = str(user_data.get("loginUsuario") or "")
    whitelist = oauth.load_whitelist()
    if nusp not in whitelist:
        raise HTTPException(status_code=401, detail="Usuário não autorizado")

    email = user_data.get("emailPrincipalUsuario")
    name = user_data.get("nomeUsuario") or ""
    with PrejanusSession() as ps:
        row = ps.execute(text('select * from "user" where email=:e'), {"e": email}).mappings().first()
        if row is None:
            ps.execute(
                text(
                    'insert into "user" (email, name, role, nusp, created_at) '
                    "values (:e, :n, 'teacher', :u, now())"
                ),
                {"e": email, "n": name, "u": nusp},
            )
            ps.commit()
            row = ps.execute(text('select * from "user" where email=:e'), {"e": email}).mappings().first()
        request.session["user_id"] = row["id"]
        return {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "nusp": row["nusp"],
            "role": row["role"],
        }
