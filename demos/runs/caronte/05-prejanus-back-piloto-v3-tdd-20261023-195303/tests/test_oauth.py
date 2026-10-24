import os
import uuid
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from oauthlib.oauth1 import Client as OAuth1Client

from conftest import API_URL

OAUTH_HOST = os.environ.get("SENHAUNICA_OAUTH_HOST")
REQUEST_TOKEN_RESOURCE = os.environ.get("SENHAUNICA_REQUEST_TOKEN_RESOURCE")
AUTHORIZE_URL = os.environ.get("SENHAUNICA_AUTHORIZE_URL")
ACCESS_TOKEN_RESOURCE = os.environ.get("SENHAUNICA_ACCESS_TOKEN_RESOURCE")
CALLBACK_ID = os.environ.get("SENHAUNICA_CALLBACK_ID")
CONSUMER_KEY = os.environ.get("SENHAUNICA_CONSUMER_KEY")
CONSUMER_SECRET = os.environ.get("SENHAUNICA_CONSUMER_SECRET")

pytestmark = pytest.mark.skipif(
    not all(
        [
            OAUTH_HOST,
            REQUEST_TOKEN_RESOURCE,
            AUTHORIZE_URL,
            ACCESS_TOKEN_RESOURCE,
            CALLBACK_ID,
            CONSUMER_KEY,
            CONSUMER_SECRET,
        ]
    ),
    reason="provedor OAuth local não configurado no ambiente de teste",
)


def _signed_post(url, oauth_client):
    uri, headers, body = oauth_client.sign(url, http_method="POST")
    return httpx.post(uri, headers=headers, content=body, timeout=30)


def _oauth_flow():
    """Executa o fluxo OAuth 1.0a contra o provedor local e devolve
    (oauth_token, oauth_verifier)."""
    consumer = OAuth1Client(
        client_key=CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        callback_uri="oob",
        nonce=uuid.uuid4().hex,
    )
    resp = _signed_post(OAUTH_HOST.rstrip("/") + REQUEST_TOKEN_RESOURCE, consumer)
    assert resp.status_code == 200, resp.text
    data = parse_qs(resp.text)
    request_token = data["oauth_token"][0]
    request_secret = data["oauth_token_secret"][0]

    # autorizacao: o provedor local devolve token e verifier
    auth_url = f"{OAUTH_HOST.rstrip('/')}{AUTHORIZE_URL}"
    resp = httpx.get(
        auth_url,
        params={"oauth_token": request_token, "callback_id": CALLBACK_ID},
        timeout=30,
    )
    assert resp.status_code == 200, resp.text
    verifier = _extract_verifier(resp)
    return request_token, verifier


def _extract_verifier(resp):
    # pode vir no corpo (form-urlencoded/json) ou na URL de retorno
    for candidate in (resp.text, str(resp.url)):
        if "oauth_verifier" in candidate:
            parsed = parse_qs(urlparse(candidate).query)
            if "oauth_verifier" in parsed:
                return parsed["oauth_verifier"][0]
    try:
        body = resp.json()
        if isinstance(body, dict) and "oauth_verifier" in body:
            return body["oauth_verifier"]
    except Exception:
        pass
    parsed = parse_qs(resp.text)
    assert "oauth_verifier" in parsed, resp.text
    return parsed["oauth_verifier"][0]


def test_senhaunica_login_flow():
    with httpx.Client(base_url=API_URL, timeout=60) as c:
        # passo 1: sem oauth_token, backend obtem request token e guarda o segredo
        resp = c.post("/auth/login/senhaunica")
        assert resp.status_code == 200
        body = resp.json()
        assert "redirect_to" in body
        assert "oauth_token" in body["redirect_to"]

        # passo 2: retorno com token e verifier da mesma sessao
        request_token, verifier = _oauth_flow()
        resp = c.post(
            "/auth/login/senhaunica",
            data={"oauth_token": request_token, "oauth_verifier": verifier},
        )
        assert resp.status_code == 200, resp.text
        user = resp.json()
        for key in ("id", "name", "email", "nusp", "role"):
            assert key in user

        # sessao autentica acessos seguintes
        assert c.get("/edicts").status_code == 200


def test_senhaunica_without_session_secret():
    # retorno sem o segredo guardado na sessao responde 401
    with httpx.Client(base_url=API_URL, timeout=60) as c:
        resp = c.post(
            "/auth/login/senhaunica",
            data={"oauth_token": "token-invalido", "oauth_verifier": "verifier"},
        )
        assert resp.status_code == 401
