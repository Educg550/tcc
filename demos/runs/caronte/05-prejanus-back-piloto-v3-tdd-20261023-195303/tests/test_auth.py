def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Hello World"}


def test_openapi_contract(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    paths = spec["paths"]
    # 50 operações de aplicação, incluindo a raiz
    operations = [
        op for path in paths.values() for op in path if op in ("get", "post", "put", "patch", "delete")
    ]
    assert len(operations) == 50
    # caminhos literais preservados
    assert "/edicts/{edict_id}/submissions" in paths
    assert "/submissions/{submission_id}/private_notes" in paths
    assert "/submissions/{submission_id}/reesend_submission" in paths
    assert "/forms/{form_id}/sessions/{section_id}/fields" in paths
    assert "/edicts/{edict_id}/candidates/mappings/versions/{version}/" in paths


def test_docs_available(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_login_dev_user(client):
    resp = client.get("/auth/login")
    assert resp.status_code == 200
    user = resp.json()
    for key in ("id", "name", "email", "nusp", "role"):
        assert key in user
    # DEV_USER_ID=2: docente já cadastrado
    assert user["id"] == 2
    assert user["role"] == "teacher"


def test_protected_routes_require_session(no_shortcut_client):
    for path in ("/auth/login", "/edicts", "/forms", "/edicts/1"):
        resp = no_shortcut_client.get(path)
        if path == "/auth/login":
            assert resp.status_code == 401
        else:
            assert resp.status_code == 401, path
