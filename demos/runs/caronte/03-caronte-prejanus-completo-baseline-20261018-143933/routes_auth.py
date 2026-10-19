"""Autenticação: dev local e fluxo Senha Única (OAuth 1.0a)."""
import os
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from oauthlib.oauth1 import Client as OAuth1Client

from auth import current_user
from config import settings
from db import get_db
from models import User

router = APIRouter()


def _su(path):
    return settings.SENHA_UNICA_URL.rstrip("/") + path


def _signed_post(url, client):
    body = ""
    uri, headers, _ = client.sign(
        url, http_method="POST", body=body or None,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return requests.post(uri, headers=headers, data=body, timeout=30)


def _signed_get(url, client):
    uri, headers, _ = client.sign(url, http_method="GET")
    return requests.get(uri, headers=headers, timeout=30)


def _parse_token_response(resp):
    data = {}
    for part in resp.text.split("&"):
        if "=" in part:
            k, _, v = part.partition("=")
            data[k] = v
    return data


def _whitelisted(nusp):
    path = settings.NUSP_WHITELIST_FILE
    if not os.path.exists(path):
        return True
    with open(path) as f:
        allowed = {line.strip() for line in f if line.strip()}
    return str(nusp) in allowed


def _user_payload(user):
    return {"id": user.id, "name": user.name, "email": user.email, "nusp": user.nusp, "role": user.role}


@router.get("/auth/login")
def login(user: User = Depends(current_user)):
    return _user_payload(user)


@router.post("/auth/login/senhaunica")
def senhaunica(request: Request, body: dict = Body(default=None), db=Depends(get_db)):
    body = body or {}
    oauth_token = body.get("oauth_token")
    oauth_verifier = body.get("oauth_verifier")

    if not oauth_token:
        # passo 1: request token
        callback = f"{settings.BASE_URL.rstrip('/')}/auth/login/senhaunica"
        client = OAuth1Client(
            settings.OAUTH_CONSUMER_KEY,
            client_secret=settings.OAUTH_CONSUMER_SECRET,
            callback_uri=callback,
        )
        try:
            resp = _signed_post(_su("/request_token"), client)
            data = _parse_token_response(resp)
            token = data["oauth_token"]
            secret = data["oauth_token_secret"]
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to obtain request token")
        request.session["oauth_secret"] = secret
        request.session["oauth_token"] = token
        redirect_to = _su(f"/authorize?{urlencode({'oauth_token': token})}")
        return {"redirect_to": redirect_to}

    # passo 2: troca pelo access token
    secret = request.session.get("oauth_secret")
    if not secret:
        raise HTTPException(status_code=401, detail="Missing request token secret")
    client = OAuth1Client(
        settings.OAUTH_CONSUMER_KEY,
        client_secret=settings.OAUTH_CONSUMER_SECRET,
        resource_owner_key=oauth_token,
        resource_owner_secret=secret,
        verifier=oauth_verifier,
    )
    try:
        resp = _signed_post(_su("/access_token"), client)
        data = _parse_token_response(resp)
        access_token = data["oauth_token"]
        access_secret = data["oauth_token_secret"]
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to exchange access token")

    client = OAuth1Client(
        settings.OAUTH_CONSUMER_KEY,
        client_secret=settings.OAUTH_CONSUMER_SECRET,
        resource_owner_key=access_token,
        resource_owner_secret=access_secret,
    )
    try:
        resp = _signed_get(_su("/usuario"), client)
        info = resp.json()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch user info")
    if isinstance(info, list):
        info = info[0] if info else {}

    nusp = info.get("nusp") or info.get("login") or info.get("vinculo", {}).get("nusp", "") if isinstance(info.get("vinculo"), dict) else info.get("nusp") or info.get("login") or ""
    name = info.get("nome") or info.get("nomeUsuario") or info.get("name") or ""
    email = info.get("email") or info.get("emailPrincipal") or ""

    if not _whitelisted(nusp):
        raise HTTPException(status_code=401, detail="NUSP not authorized")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(name=name, email=email, nusp=str(nusp), role="teacher")
        db.add(user)
        db.commit()
    request.session["user_id"] = user.id
    request.session.pop("oauth_secret", None)
    request.session.pop("oauth_token", None)
    return _user_payload(user)
