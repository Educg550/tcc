def test_root(api):
    r = api.get("/")
    assert r.status_code == 200
    assert r.json() == {"message": "Hello World"}


def test_openapi(api):
    r = api.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    for path in [
        "/edicts",
        "/edicts/{edict_id}/submissions",
        "/submissions/{submission_id}",
        "/submissions/{submission_id}/files/{label}/{filename}",
        "/submissions/{submission_id}/private_notes",
        "/submissions/{submission_id}/reesend_submission",
        "/forms/{form_id}/sessions/{section_id}/fields",
        "/auth/login",
        "/auth/login/senhaunica",
    ]:
        assert path in paths, f"caminho ausente: {path}"


def test_docs(api):
    assert api.get("/docs").status_code == 200
    assert api.get("/redoc").status_code == 200
