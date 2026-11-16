import os

import httpx


def test_login_atalho_local_retorna_usuario(api):
    resp = api.get("/auth/login")
    assert resp.status_code == 200, resp.text
    user = resp.json()
    assert user.get("id") == 2
    assert user.get("name") == "teacher"


def test_atalho_admin_e_docente_distintos(api_admin, api):
    admin = api_admin.get("/auth/login").json()
    teacher = api.get("/auth/login").json()
    assert admin["id"] == 1
    assert admin["name"] == "administrator"
    assert teacher["id"] != admin["id"]


def test_sem_sessao_rotas_protegidas_respondem_401(api_sem_atalho):
    resp = api_sem_atalho.get("/edicts")
    assert resp.status_code == 401, resp.text


def test_login_senha_unica_cria_sessao(api_senhaunica):
    provedor = os.environ["SENHAUNICA_PROVEDOR"].rstrip("/")
    client = api_senhaunica

    # Início do fluxo: o backend redireciona ao provedor.
    resp = client.get("/auth/login", follow_redirects=False)
    assert resp.status_code in (200, 302, 303, 307), resp.text

    url = resp.headers.get("location")
    if url:
        # Autorização sem tela no provedor local, com perfil docente.
        sep = "&" if "?" in url else "?"
        authorize = httpx.get(f"{url}{sep}perfil=docente", timeout=30)
        assert authorize.status_code == 200, authorize.text
        callback = authorize.json()
        assert "oauth_token" in callback and "oauth_verifier" in callback

    # Após o fluxo, a sessão deve dar acesso às rotas protegidas.
    protegida = client.get("/edicts")
    assert protegida.status_code == 200, protegida.text


def test_usuario_novo_na_whitelist_e_cadastrado(api_senhaunica):
    provedor = os.environ["SENHAUNICA_PROVEDOR"].rstrip("/")
    client = api_senhaunica
    resp = client.get("/auth/login", follow_redirects=False)
    url = resp.headers.get("location")
    assert url, resp.text
    sep = "&" if "?" in url else "?"
    authorize = httpx.get(f"{url}{sep}perfil=novo", timeout=30)
    assert authorize.status_code == 200, authorize.text
    assert client.get("/edicts").status_code == 200


def test_usuario_fora_da_whitelist_negado(api_senhaunica):
    client = api_senhaunica
    resp = client.get("/auth/login", follow_redirects=False)
    url = resp.headers.get("location")
    assert url, resp.text
    sep = "&" if "?" in url else "?"
    authorize = httpx.get(f"{url}{sep}perfil=negado", timeout=30)
    assert authorize.status_code in (200, 401, 403), authorize.text
    if authorize.status_code == 200:
        assert client.get("/edicts").status_code == 401
