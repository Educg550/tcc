def test_root_message(api):
    resp = api.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Hello World"}


def test_openapi_contract(api):
    resp = api.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    operations = sum(
        len([m for m in methods if m in spec["paths"][p]])
        for p in spec["paths"]
        for methods in [spec["paths"][p]]
    )
    assert operations >= 40


def test_docs_available(api):
    assert api.get("/docs").status_code == 200
    assert api.get("/redoc").status_code == 200


def test_login_dev_user(api):
    resp = api.get("/auth/login")
    assert resp.status_code == 200
    user = resp.json()
    for key in ("id", "name", "email", "nusp", "role"):
        assert key in user
    assert user["role"] == "teacher"


def test_protected_routes_require_session(api_noauth):
    for path in ("/edicts", "/forms", "/submissions/1", "/auth/login"):
        assert api_noauth.get(path).status_code == 401, path


def test_senhaunica_request_token_redirect(api):
    resp = api.post("/auth/login/senhaunica")
    assert resp.status_code == 200
    assert "redirect_to" in resp.json()


def test_senhaunica_callback_without_secret(api):
    # Sem o segredo de request token na sessão, o retorno deve ser 401.
    resp = api.post(
        "/auth/login/senhaunica",
        params={"oauth_token": "token-qualquer", "oauth_verifier": "verifier"},
    )
    assert resp.status_code == 401
