import os

import httpx
import pytest


def test_root(api):
    r = api.get("/")
    assert r.status_code == 200
    assert r.json() == {"message": "Hello World"}


def test_openapi_docs_disponiveis(api):
    assert api.get("/openapi.json").status_code == 200
    assert api.get("/docs").status_code == 200


def test_login_dev_user(api):
    r = api.get("/auth/login")
    assert r.status_code == 200, r.text
    user = r.json()
    for key in ("id", "name", "email", "nusp", "role"):
        assert key in user
    assert user["role"] == "teacher"


def test_login_admin(admin):
    user = admin.get("/auth/login").json()
    assert user["role"] == "administrator"


def test_login_estudante(estudante):
    user = estudante.get("/auth/login").json()
    assert user["role"] == "student"


def test_sem_sessao_protegidas_401(sem_atalho):
    for method, path in [
        ("get", "/edicts"),
        ("get", "/auth/login"),
        ("get", "/forms"),
        ("get", "/submissions/1"),
    ]:
        r = getattr(sem_atalho, method)(path)
        assert r.status_code == 401, (path, r.status_code)


def test_senhaunica_fluxo_completo():
    base = os.environ.get("CARONTE_API_SENHAUNICA")
    provedor = os.environ.get("SENHAUNICA_PROVEDOR")
    if not base or not provedor:
        pytest.skip("CARONTE_API_SENHAUNICA/SENHAUNICA_PROVEDOR não definidos")
    with httpx.Client(base_url=base.rstrip("/"), timeout=60) as client:
        # passo 1: request token
        r = client.post("/auth/login/senhaunica")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "redirect_to" in body
        # passo 2: autorização no provedor local
        token = body["redirect_to"].split("oauth_token=")[1].split("&")[0]
        with httpx.Client(base_url=provedor.rstrip("/"), timeout=60) as prov:
            auth = prov.get(
                "/wsusuario/oauth/authorize",
                params={"oauth_token": token, "perfil": "docente"},
            )
            assert auth.status_code == 200, auth.text
            verifier = auth.json()["oauth_verifier"]
        # passo 3: retorno com token e verifier na mesma sessão
        r2 = client.post(
            "/auth/login/senhaunica",
            params={"oauth_token": token, "oauth_verifier": verifier},
        )
        assert r2.status_code == 200, r2.text
        # passo 4: sessão autenticada
        login = client.get("/auth/login")
        assert login.status_code == 200, login.text
        assert login.json()["role"] == "teacher"


def test_senhaunica_sem_segredo_401():
    base = os.environ.get("CARONTE_API_SENHAUNICA")
    if not base:
        pytest.skip("CARONTE_API_SENHAUNICA não definido")
    with httpx.Client(base_url=base.rstrip("/"), timeout=60) as client:
        r = client.post(
            "/auth/login/senhaunica",
            params={"oauth_token": "token-invalido", "oauth_verifier": "v"},
        )
        assert r.status_code == 401


def test_senhaunica_novo_usuario_whitelist():
    base = os.environ.get("CARONTE_API_SENHAUNICA")
    provedor = os.environ.get("SENHAUNICA_PROVEDOR")
    if not base or not provedor:
        pytest.skip("CARONTE_API_SENHAUNICA/SENHAUNICA_PROVEDOR não definidos")
    with httpx.Client(base_url=base.rstrip("/"), timeout=60) as client:
        r = client.post("/auth/login/senhaunica")
        assert r.status_code == 200, r.text
        token = r.json()["redirect_to"].split("oauth_token=")[1].split("&")[0]
        with httpx.Client(base_url=provedor.rstrip("/"), timeout=60) as prov:
            auth = prov.get(
                "/wsusuario/oauth/authorize",
                params={"oauth_token": token, "perfil": "novo"},
            )
            verifier = auth.json()["oauth_verifier"]
        r2 = client.post(
            "/auth/login/senhaunica",
            params={"oauth_token": token, "oauth_verifier": verifier},
        )
        assert r2.status_code == 200, r2.text
        login = client.get("/auth/login")
        assert login.status_code == 200
        assert login.json()["role"] == "teacher"


def test_senhaunica_fora_whitelist():
    base = os.environ.get("CARONTE_API_SENHAUNICA")
    provedor = os.environ.get("SENHAUNICA_PROVEDOR")
    if not base or not provedor:
        pytest.skip("CARONTE_API_SENHAUNICA/SENHAUNICA_PROVEDOR não definidos")
    with httpx.Client(base_url=base.rstrip("/"), timeout=60) as client:
        r = client.post("/auth/login/senhaunica")
        token = r.json()["redirect_to"].split("oauth_token=")[1].split("&")[0]
        with httpx.Client(base_url=provedor.rstrip("/"), timeout=60) as prov:
            auth = prov.get(
                "/wsusuario/oauth/authorize",
                params={"oauth_token": token, "perfil": "negado"},
            )
            verifier = auth.json()["oauth_verifier"]
        r2 = client.post(
            "/auth/login/senhaunica",
            params={"oauth_token": token, "oauth_verifier": verifier},
        )
        assert r2.status_code in (401, 403)
