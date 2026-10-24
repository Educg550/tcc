from urllib.parse import urlparse, parse_qs

import httpx

from tests.utils import Client
import os


def test_root(api):
    r = api.get("/")
    assert r.status_code == 200
    assert r.json() == {"message": "Hello World"}


def test_openapi_documentation(api):
    assert api.get("/docs").status_code == 200
    spec = api.get("/openapi.json")
    assert spec.status_code == 200
    assert spec.json()["openapi"].startswith("3.")


def test_login_dev_user(api):
    r = api.get("/auth/login")
    assert r.status_code == 200
    user = r.json()
    for key in ("id", "name", "email", "nusp", "role"):
        assert key in user
    assert user["id"] == 2
    assert user["role"] == "teacher"


def test_login_admin_user(admin):
    user = admin.get("/auth/login").json()
    assert user["id"] == 1
    assert user["role"] == "administrator"


def test_protected_routes_require_session(sem_atalho):
    for path in ("/edicts", "/forms", "/submissions/1", "/edicts/1/submissions"):
        r = sem_atalho.get(path)
        assert r.status_code == 401, path


def _authorize(provedor, oauth_token, perfil):
    r = httpx.get(
        f"{provedor}/wsusuario/oauth/authorize",
        params={"oauth_token": oauth_token, "perfil": perfil},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_senhaunica_full_flow(senhaunica, provedor):
    r = senhaunica.post("/auth/login/senhaunica", json={})
    assert r.status_code == 200
    redirect_to = r.json()["redirect_to"]
    assert redirect_to
    token = parse_qs(urlparse(redirect_to).query)["oauth_token"][0]

    auth = _authorize(provedor, token, "docente")
    r2 = senhaunica.post(
        "/auth/login/senhaunica",
        json={"oauth_token": auth["oauth_token"], "oauth_verifier": auth["oauth_verifier"]},
    )
    assert r2.status_code == 200, r2.text

    me = senhaunica.get("/auth/login")
    assert me.status_code == 200
    assert me.json()["role"] == "teacher"


def test_senhaunica_registers_new_whitelisted_user(provedor):
    c = Client(os.environ["CARONTE_API_SENHAUNICA"].rstrip("/"))
    try:
        token = parse_qs(
            urlparse(c.post("/auth/login/senhaunica", json={}).json()["redirect_to"]).query
        )["oauth_token"][0]
        auth = _authorize(provedor, token, "novo")
        r = c.post(
            "/auth/login/senhaunica",
            json={"oauth_token": auth["oauth_token"], "oauth_verifier": auth["oauth_verifier"]},
        )
        assert r.status_code == 200, r.text
        me = c.get("/auth/login").json()
        assert me["role"] == "teacher"
        assert me["nusp"]
    finally:
        c.close()


def test_senhaunica_rejects_outside_whitelist(provedor):
    c = Client(os.environ["CARONTE_API_SENHAUNICA"].rstrip("/"))
    try:
        token = parse_qs(
            urlparse(c.post("/auth/login/senhaunica", json={}).json()["redirect_to"]).query
        )["oauth_token"][0]
        auth = _authorize(provedor, token, "negado")
        r = c.post(
            "/auth/login/senhaunica",
            json={"oauth_token": auth["oauth_token"], "oauth_verifier": auth["oauth_verifier"]},
        )
        assert r.status_code in (401, 403)
        assert c.get("/edicts").status_code == 401
    finally:
        c.close()


def test_senhaunica_callback_requires_request_secret(provedor):
    a = Client(os.environ["CARONTE_API_SENHAUNICA"].rstrip("/"))
    b = Client(os.environ["CARONTE_API_SENHAUNICA"].rstrip("/"))
    try:
        token = parse_qs(
            urlparse(a.post("/auth/login/senhaunica", json={}).json()["redirect_to"]).query
        )["oauth_token"][0]
        auth = _authorize(provedor, token, "docente")
        r = b.post(
            "/auth/login/senhaunica",
            json={"oauth_token": auth["oauth_token"], "oauth_verifier": auth["oauth_verifier"]},
        )
        assert r.status_code == 401
    finally:
        a.close()
        b.close()
