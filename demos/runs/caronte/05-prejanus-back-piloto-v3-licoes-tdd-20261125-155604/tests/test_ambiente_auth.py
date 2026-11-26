def test_root(api):
    r = api.get("/")
    assert r.status_code == 200
    assert r.json() == {"message": "Hello World"}


def test_openapi_disponivel(api):
    r = api.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    assert "/edicts" in paths
    assert "/auth/login" in paths
    assert "/forms" in paths


def test_login_dev_user(api):
    r = api.get("/auth/login")
    assert r.status_code == 200
    data = r.json()
    for key in ("id", "name", "email", "nusp", "role"):
        assert key in data
    assert data["role"] == "teacher"
    assert data["id"] == 2


def test_login_admin_role(admin):
    data = admin.get("/auth/login").json()
    assert data["role"] == "administrator"


def test_sem_sessao_protegidas_401(sem_atalho):
    assert sem_atalho.get("/edicts").status_code == 401
    assert sem_atalho.get("/forms").status_code == 401
    assert sem_atalho.get("/edicts/1/submissions").status_code == 401


def test_senhaunica_fluxo_completo(senhaunica, provedor):
    # passo 1: request token
    r = senhaunica.post("/auth/login/senhaunica")
    assert r.status_code == 200, r.text
    redirect = r.json()["redirect_to"]
    assert redirect
    # extrai oauth_token do redirect
    token = None
    for part in redirect.split("?")[1].split("&"):
        if part.startswith("oauth_token="):
            token = part.split("=", 1)[1]
    assert token

    # autorização no provedor local
    ra = provedor.get(
        "/wsusuario/oauth/authorize", params={"oauth_token": token, "perfil": "docente"}
    )
    assert ra.status_code == 200, ra.text
    auth = ra.json()
    assert "oauth_verifier" in auth

    # retorno com token e verifier
    r2 = senhaunica.post(
        "/auth/login/senhaunica",
        params={"oauth_token": token, "oauth_verifier": auth["oauth_verifier"]},
    )
    assert r2.status_code == 200, r2.text

    # sessão estabelecida
    me = senhaunica.get("/auth/login")
    assert me.status_code == 200
    assert me.json()["role"] == "teacher"


def test_senhaunica_sem_segredo_401(senhaunica, provedor):
    r = senhaunica.post("/auth/login/senhaunica")
    assert r.status_code == 200
    redirect = r.json()["redirect_to"]
    token = redirect.split("oauth_token=")[1].split("&")[0]
    ra = provedor.get(
        "/wsusuario/oauth/authorize", params={"oauth_token": token, "perfil": "docente"}
    )
    verifier = ra.json()["oauth_verifier"]
    # nova sessão sem o segredo do request token
    import httpx
    import os

    base = os.environ["CARONTE_API_SENHAUNICA"].rstrip("/")
    with httpx.Client(base_url=base, timeout=30) as c2:
        r2 = c2.post(
            "/auth/login/senhaunica",
            params={"oauth_token": token, "oauth_verifier": verifier},
        )
        assert r2.status_code == 401


def test_senhaunica_novo_usuario_whitelist(senhaunica, provedor):
    r = senhaunica.post("/auth/login/senhaunica")
    token = r.json()["redirect_to"].split("oauth_token=")[1].split("&")[0]
    ra = provedor.get(
        "/wsusuario/oauth/authorize", params={"oauth_token": token, "perfil": "novo"}
    )
    r2 = senhaunica.post(
        "/auth/login/senhaunica",
        params={
            "oauth_token": token,
            "oauth_verifier": ra.json()["oauth_verifier"],
        },
    )
    assert r2.status_code == 200, r2.text
    me = senhaunica.get("/auth/login").json()
    assert me["role"] == "teacher"
    assert me["nusp"]


def test_senhaunica_fora_whitelist(senhaunica, provedor):
    r = senhaunica.post("/auth/login/senhaunica")
    token = r.json()["redirect_to"].split("oauth_token=")[1].split("&")[0]
    ra = provedor.get(
        "/wsusuario/oauth/authorize", params={"oauth_token": token, "perfil": "negado"}
    )
    r2 = senhaunica.post(
        "/auth/login/senhaunica",
        params={
            "oauth_token": token,
            "oauth_verifier": ra.json()["oauth_verifier"],
        },
    )
    assert r2.status_code in (401, 403)
