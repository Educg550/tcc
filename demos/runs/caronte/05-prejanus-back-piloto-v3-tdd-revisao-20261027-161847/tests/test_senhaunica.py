"""V2-AUT-02 — fluxo completo da Senha Unnica contra o provedor local."""
from urllib.parse import parse_qs, urlparse

import pytest


def _start(client):
    r = client.post("/auth/login/senhaunica")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "redirect_to" in body
    return body["redirect_to"]


def _authorize(provedor, redirect_to, perfil):
    qs = parse_qs(urlparse(redirect_to).query)
    token = qs["oauth_token"][0]
    r = provedor.get(
        "/wsusuario/oauth/authorize",
        params={"oauth_token": token, "perfil": perfil},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _callback(client, oauth_token, oauth_verifier):
    r = client.post(
        "/auth/login/senhaunica",
        data={"oauth_token": oauth_token, "oauth_verifier": oauth_verifier},
    )
    if r.status_code == 422:
        r = client.post(
            "/auth/login/senhaunica",
            json={"oauth_token": oauth_token, "oauth_verifier": oauth_verifier},
        )
    return r


def test_fluxo_docente(senhaunica, provedor):
    redirect_to = _start(senhaunica)
    auth = _authorize(provedor, redirect_to, "docente")
    r = _callback(senhaunica, auth["oauth_token"], auth["oauth_verifier"])
    assert r.status_code == 200, r.text
    user = r.json()
    assert user["role"] == "teacher"
    for key in ("id", "name", "email", "nusp", "role"):
        assert key in user
    # sessao valida em requisicoes seguintes
    assert senhaunica.get("/edicts").status_code == 200


def test_novo_usuario_whitelist_cadastra_docente(senhaunica, provedor):
    redirect_to = _start(senhaunica)
    auth = _authorize(provedor, redirect_to, "novo")
    r = _callback(senhaunica, auth["oauth_token"], auth["oauth_verifier"])
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "teacher"


def test_fora_da_whitelist_negado(senhaunica, provedor):
    redirect_to = _start(senhaunica)
    auth = _authorize(provedor, redirect_to, "negado")
    r = _callback(senhaunica, auth["oauth_token"], auth["oauth_verifier"])
    assert r.status_code in (401, 403)


def test_callback_sem_segredo_de_sessao(senhaunica, provedor):
    redirect_to = _start(senhaunica)
    auth = _authorize(provedor, redirect_to, "docente")
    # outra sessao, sem o segredo do request token
    import httpx
    url = senhaunica.base_url
    with httpx.Client(base_url=url, timeout=60, verify=False) as outra:
        r = _callback(outra, auth["oauth_token"], auth["oauth_verifier"])
    assert r.status_code == 401


def test_cookie_de_sessao(senhaunica):
    r = senhaunica.post("/auth/login/senhaunica")
    assert r.status_code == 200
    cookie = r.headers.get("set-cookie", "")
    assert "samesite=lax" in cookie.lower()
    assert "secure" in cookie.lower()
