def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"message": "Hello World"}


def test_openapi_contract(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    esperados = [
        "/edicts",
        "/forms",
        "/auth/login",
        "/auth/login/senhaunica",
        "/submissions/{submission_id}",
        "/submissions/{submission_id}/comments",
        "/submissions/{submission_id}/favorites",
        "/submissions/{submission_id}/labels",
        "/submissions/{submission_id}/private_notes",
        "/submissions/{submission_id}/view",
        "/submissions/{submission_id}/bidding",
        "/submissions/{submission_id}/select",
        "/submissions/{submission_id}/entry-semester",
        "/submissions/{submission_id}/send-accept",
        "/submissions/{submission_id}/send-letter",
        "/submissions/{submission_id}/reesend_submission",
        "/submissions/{submission_id}/files/{label}/{filename}",
        "/edicts/{edict_id}/candidates/mappings/versions/{version}/",
        "/edicts/{edict_id}/recommenders/mappings/versions/{version}/",
        "/edicts/{edict_id}/candidates/forms/versions/unmapped",
        "/edicts/{edict_id}/recommenders/forms/versions/unmapped",
        "/edicts/download_pdf/{job_id}",
        "/edicts/download_csv/{job_id}",
        "/forms/{form_id}/sessions/{section_id}/fields",
    ]
    for p in esperados:
        assert p in paths, p


def test_docs(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_login_dev_user(client):
    r = client.get("/auth/login")
    assert r.status_code == 200
    data = r.json()
    for k in ("id", "name", "email", "nusp", "role"):
        assert k in data, k
    assert data["id"] == 2
    assert data["role"] == "teacher"


def test_protected_routes_401_without_session(client_noauth):
    assert client_noauth.get("/auth/login").status_code == 401
    assert client_noauth.get("/edicts").status_code == 401
    assert client_noauth.get("/forms").status_code == 401
    assert client_noauth.get("/submissions/1").status_code == 401
    assert client_noauth.post("/submissions/1/favorites").status_code == 401
    assert client_noauth.post("/edicts/1/slots", json={"amount": "1"}).status_code == 401


def test_senhaunica_request_token_step(client):
    r = client.post("/auth/login/senhaunica")
    assert r.status_code == 200
    assert "redirect_to" in r.json()


def test_senhaunica_callback_without_secret(client):
    r = client.post(
        "/auth/login/senhaunica",
        params={"oauth_token": "invalido", "oauth_verifier": "invalido"},
    )
    assert r.status_code == 401


def test_session_cookie_attributes(client):
    r = client.post("/auth/login/senhaunica")
    sc = r.headers.get("set-cookie", "")
    if sc:
        assert "samesite=lax" in sc.lower()
        assert "secure" in sc.lower()
