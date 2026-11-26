import httpx


def test_login_dev_user(api):
    r = api.get("/auth/login")
    assert r.status_code == 200, r.text
    user = r.json()
    for key in ("id", "name", "email", "nusp", "role"):
        assert key in user, f"chave ausente: {key}"
    assert user["role"] == "teacher"
    assert user["id"] == 2


def test_login_admin_role(api_admin):
    user = api_admin.get("/auth/login").json()
    assert user["role"] == "administrator"
    assert user["id"] == 1


def test_sem_atalho_protegidas_401(api_sem_atalho):
    for method, path in [
        ("get", "/edicts"),
        ("get", "/forms"),
        ("get", "/auth/login"),
    ]:
        r = getattr(api_sem_atalho, method)(path)
        assert r.status_code == 401, f"{path} -> {r.status_code}"


def test_senhaunica_fluxo_docente(api_senhaunica, provedor):
    # passo 1: request token
    r = api_senhaunica.post("/auth/login/senhaunica")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "redirect_to" in body
    redirect = body["redirect_to"]
    assert "oauth_token" in redirect

    token = dict(
        part.split("=", 1)
        for part in redirect.split("?", 1)[1].split("&")
    )["oauth_token"]

    # passo 2: autorização no provedor local
    ra = provedor.get(
        "/wsusuario/oauth/authorize",
        params={"oauth_token": token, "perfil": "docente"},
    )
    assert ra.status_code == 200, ra.text
    auth = ra.json()
    assert "oauth_verifier" in auth

    # passo 3: retorno com token e verifier na mesma sessão
    rr = api_senhaunica.post(
        "/auth/login/senhaunica",
        params={
            "oauth_token": auth["oauth_token"],
            "oauth_verifier": auth["oauth_verifier"],
        },
    )
    assert rr.status_code == 200, rr.text

    # passo 4: sessão autenticada
    rl = api_senhaunica.get("/auth/login")
    assert rl.status_code == 200, rl.text
    user = rl.json()
    assert user["role"] == "teacher"
    assert user["nusp"]


def test_senhaunica_sem_segredo_401(api_senhaunica, provedor):
    r = api_senhaunica.post("/auth/login/senhaunica")
    assert r.status_code == 200, r.text
    redirect = r.json()["redirect_to"]
    token = dict(
        part.split("=", 1)
        for part in redirect.split("?", 1)[1].split("&")
    )["oauth_token"]
    ra = provedor.get(
        "/wsusuario/oauth/authorize",
        params={"oauth_token": token, "perfil": "docente"},
    )
    auth = ra.json()
    # nova sessão, sem o segredo do request token
    with httpx.Client(base_url=api_senhaunica.base_url, timeout=30) as other:
        rr = other.post(
            "/auth/login/senhaunica",
            params={
                "oauth_token": auth["oauth_token"],
                "oauth_verifier": auth["oauth_verifier"],
            },
        )
        assert rr.status_code == 401, rr.text


def test_senhaunica_novo_usuario_whitelist(api_senhaunica, provedor):
    r = api_senhaunica.post("/auth/login/senhaunica")
    redirect = r.json()["redirect_to"]
    token = dict(
        part.split("=", 1)
        for part in redirect.split("?", 1)[1].split("&")
    )["oauth_token"]
    ra = provedor.get(
        "/wsusuario/oauth/authorize",
        params={"oauth_token": token, "perfil": "novo"},
    )
    assert ra.status_code == 200, ra.text
    auth = ra.json()
    rr = api_senhaunica.post(
        "/auth/login/senhaunica",
        params={
            "oauth_token": auth["oauth_token"],
            "oauth_verifier": auth["oauth_verifier"],
        },
    )
    assert rr.status_code == 200, rr.text
    user = api_senhaunica.get("/auth/login").json()
    assert user["role"] == "teacher"
    assert user["id"]


def test_senhaunica_fora_whitelist(api_senhaunica, provedor):
    r = api_senhaunica.post("/auth/login/senhaunica")
    redirect = r.json()["redirect_to"]
    token = dict(
        part.split("=", 1)
        for part in redirect.split("?", 1)[1].split("&")
    )["oauth_token"]
    ra = provedor.get(
        "/wsusuario/oauth/authorize",
        params={"oauth_token": token, "perfil": "negado"},
    )
    auth = ra.json()
    rr = api_senhaunica.post(
        "/auth/login/senhaunica",
        params={
            "oauth_token": auth["oauth_token"],
            "oauth_verifier": auth["oauth_verifier"],
        },
    )
    assert rr.status_code in (401, 403), rr.text
