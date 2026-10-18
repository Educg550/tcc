"""Authentication routes: dev shortcut login and Senha Única OAuth."""
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urljoin

import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from oauthlib.oauth1 import Client

from ..config import settings
from ..db import get_db
from ..models import User
from ..security import get_user

router = APIRouter(tags=["auth"])


def _load_whitelist() -> set[str]:
    path = Path(settings.WHITELIST_FILE)
    if not path.exists():
        return set()
    values: set[str] = set()
    for line in path.read_text().splitlines():
        for part in line.split(","):
            part = part.strip()
            if part:
                values.add(part)
    return values


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "nusp": user.nusp,
        "role": user.role,
    }


@router.get("/auth/login")
def login(request: Request, db=Depends(get_db)):
    user = get_user(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _user_payload(user)


def _oauth_client(**kwargs) -> Client:
    return Client(
        settings.SENHAUNICA_CONSUMER_KEY,
        client_secret=settings.SENHAUNICA_CONSUMER_SECRET,
        **kwargs,
    )


def _resource_url(resource: str) -> str:
    if resource.startswith("http://") or resource.startswith("https://"):
        return resource
    return urljoin(settings.SENHAUNICA_OAUTH_HOST.rstrip("/") + "/", resource.lstrip("/"))


@router.post("/auth/login/senhaunica")
def login_senhaunica(request: Request, db=Depends(get_db)):
    params = request.query_params
    oauth_token = params.get("oauth_token")
    oauth_verifier = params.get("oauth_verifier")

    if not oauth_token:
        # First step: obtain a request token and redirect to the provider.
        callback = (
            f"{settings.BASE_URL.rstrip('/')}/auth/login/senhaunica"
            if not settings.SENHAUNICA_CALLBACK_ID
            else settings.SENHAUNICA_CALLBACK_ID
        )
        client = _oauth_client(callback_uri=callback)
        uri, headers, body = client.sign(
            _resource_url(settings.SENHAUNICA_REQUEST_TOKEN_RESOURCE),
            http_method="POST",
        )
        try:
            resp = requests.post(uri, headers=headers, data=body, timeout=30)
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="OAuth request failed")
        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="OAuth request failed")
        data = parse_qs(resp.text)
        try:
            token = data["oauth_token"][0]
            secret = data["oauth_token_secret"][0]
        except (KeyError, IndexError):
            raise HTTPException(status_code=500, detail="OAuth request failed")
        request.session["oauth_token"] = token
        request.session["oauth_secret"] = secret
        authorize = _resource_url(settings.SENHAUNICA_AUTHORIZE_URL)
        return {"redirect_to": f"{authorize}?oauth_token={token}"}

    # Callback: exchange the request token for the access token.
    secret = request.session.get("oauth_secret")
    if (
        not secret
        or request.session.get("oauth_token") != oauth_token
        or not oauth_verifier
    ):
        raise HTTPException(status_code=401, detail="Invalid OAuth callback")

    client = _oauth_client(
        resource_owner_key=oauth_token,
        resource_owner_secret=secret,
        verifier=oauth_verifier,
    )
    uri, headers, body = client.sign(
        _resource_url(settings.SENHAUNICA_ACCESS_TOKEN_RESOURCE),
        http_method="POST",
    )
    try:
        resp = requests.post(uri, headers=headers, data=body, timeout=30)
    except requests.RequestException:
        raise HTTPException(status_code=500, detail="OAuth token exchange failed")
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="OAuth token exchange failed")
    data = {k: v[0] for k, v in parse_qs(resp.text).items() if v}

    nome = (
        data.get("nome")
        or data.get("nomeUsuario")
        or data.get("nome_usuario")
        or data.get("name")
        or ""
    )
    email = (
        data.get("email")
        or data.get("emailUsuario")
        or data.get("email_usuario")
        or ""
    )
    nusp = (
        data.get("nusp")
        or data.get("codpes")
        or data.get("login")
        or data.get("username")
        or ""
    )

    whitelist = _load_whitelist()
    if whitelist and nusp not in whitelist:
        raise HTTPException(status_code=403, detail="NUSP not authorized")

    user = None
    if email:
        user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            name=nome or email or nusp,
            email=email or None,
            nusp=nusp or None,
            role="teacher",
            created_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
    request.session["user_id"] = user.id
    request.session.pop("oauth_secret", None)
    request.session.pop("oauth_token", None)
    return _user_payload(user)