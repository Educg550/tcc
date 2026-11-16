import os
from urllib.parse import parse_qs, urlparse

import httpx

from helpers import client


def test_root(api):
    r = api.get("/")
    assert r.status_code == 200, r.text
    assert r.json() == {"message": "Hello World"}


def test_openapi_documentado(api):
    r = api.get("/openapi.json")
    assert r.status_code == 200, r.text
    paths = r.json()["paths"]
    for path in ("/edicts", "/forms", "/auth/login", "/submissions/{submission_id}"):
        assert path in paths


def test_login_dev_user_teacher(api):
    r = api.get("/auth/login")
    assert r.status_code == 200, r.text
    u = r.json()
    for key in ("id", "name", "email", "nusp", "role"):
        assert key in u, u
    assert u["role"] == "teacher"


def test_login_dev_user_admin(admin):
    u = admin.get("/auth/login").json()
    assert u["role"] == "administrator"


def test_sem_atalho_protegidas_401(sem_atalho):
    assert sem_atalho.get("/edicts").status_code == 401
    assert sem_atalho.get("/auth/login").status_code == 401


def _senhaunica_login(perfil):
    c = client("CARONTE_API_SENHAUNICA")
    with c:
        r = c.post("/auth/login/senhaunica", json={})
        assert r.status_code == 200, r.text
        redirect = r.json()["redirect_to"]
        query = parse_qs(urlparse(redirect).query)
        assert "oauth_token" in query, redirect
        token = query["oauth_token"][0]
        prov = os.environ["SENHAUNICA_PROVEDOR"].rstrip("/")
        auth = httpx.get(
            f"{prov}/wsusuario/oauth/authorize",
            params={"oauth_token": token, "perfil": perfil},
            timeout=60,
        )
        assert auth.status_code == 200, auth.text
        verifier = auth.json()["oauth_verifier"]
        r2 = c.post(
            "/auth/login/senhaunica",
            json={"oauth_token": token, "oauth_verifier": verifier},
        )
        return c, r2


def test_senhaunica_fluxo_docente():
    c, r2 = _senhaunica_login("docente")
    assert r2.status_code == 200, r2.text
    u = c.get("/auth/login").json()
    assert u["role"] == "teacher"
    assert u["nusp"]


def test_senhaunica_novo_usuario_vira_teacher():
    c, r2 = _senhaunica_login("novo")
    assert r2.status_code == 200, r2.text
    u = c.get("/auth/login").json()
    assert u["role"] == "teacher"
    assert u["nusp"]


def test_senhaunica_fora_da_whitelist():
    _, r2 = _senhaunica_login("negado")
    assert r2.status_code in (401, 403), r2.text


def test_senhaunica_callback_sem_segredo():
    c = client("CARONTE_API_SENHAUNICA")
    with c:
        r = c.post(
            "/auth/login/senhaunica",
            json={"oauth_token": "token-qualquer", "oauth_verifier": "verifier"},
        )
        assert r.status_code == 401, r.text
