"""V2-AMB-01 e V2-AUT-01: raiz, documentação, contrato e login local."""


def test_root_message(api):
    resp = api.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Hello World"}


def test_docs_disponiveis(api):
    assert api.get("/docs").status_code == 200
    assert api.get("/redoc").status_code == 200


def test_openapi_possui_as_50_operacoes(api):
    resp = api.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    paths = spec["paths"]
    # raiz + interfaces auxiliares não contam; checamos operações de aplicação conhecidas
    esperadas = [
        "/edicts",
        "/edicts/{edict_id}",
        "/edicts/{edict_id}/edit",
        "/edicts/{edict_id}/edit-date",
        "/edicts/{edict_id}/advance-phase",
        "/edicts/{edict_id}/remove",
        "/edicts/{edict_id}/close",
        "/edicts/{edict_id}/slots",
        "/edicts/{edict_id}/submissions",
        "/edicts/{edict_id}/interactors_list",
        "/edicts/{edict_id}/pairing-biddings",
        "/edicts/download_pdf/{job_id}",
        "/edicts/download_csv/{job_id}",
        "/edicts/{edict_id}/candidates/mappings",
        "/edicts/{edict_id}/recommenders/mappings",
        "/edicts/{edict_id}/candidates/mappings/versions/{version}/",
        "/edicts/{edict_id}/recommenders/mappings/versions/{version}/",
        "/edicts/{edict_id}/candidates/mappings/versions/{version}/{mapping_id}",
        "/edicts/{edict_id}/recommenders/mappings/versions/{version}/{mapping_id}",
        "/edicts/{edict_id}/candidates/forms/versions/unmapped",
        "/edicts/{edict_id}/recommenders/forms/versions/unmapped",
        "/submissions/{submission_id}",
        "/submissions/{submission_id}/send-accept",
        "/submissions/{submission_id}/send-letter",
        "/submissions/{submission_id}/comments",
        "/submissions/comments/{comment_id}",
        "/submissions/{submission_id}/labels",
        "/submissions/label/{label_id}",
        "/submissions/{submission_id}/private_notes",
        "/submissions/{submission_id}/reesend_submission",
        "/submissions/{submission_id}/favorites",
        "/submissions/{submission_id}/select",
        "/submissions/{submission_id}/bidding",
        "/submissions/{submission_id}/entry-semester",
        "/submissions/{submission_id}/files/{label}/{filename}",
        "/submissions/{submission_id}/view",
        "/auth/login",
        "/auth/login/senhaunica",
        "/forms",
        "/forms/{form_id}",
        "/forms/{form_id}/sections",
        "/forms/{form_id}/sessions/{section_id}/fields",
    ]
    for path in esperadas:
        assert path in paths, f"caminho ausente no OpenAPI: {path}"


def test_login_dev_user(api):
    resp = api.get("/auth/login")
    assert resp.status_code == 200
    user = resp.json()
    for key in ("id", "name", "email", "nusp", "role"):
        assert key in user
    # DEV_USER_ID=2: docente já cadastrado
    assert user["id"] == 2
    assert user["role"] == "teacher"


def test_sem_sessao_protegidas_401(api_sem_atalho):
    for path in ("/auth/login", "/edicts", "/forms", "/edicts/1/submissions"):
        resp = api_sem_atalho.get(path)
        assert resp.status_code == 401, f"{path} -> {resp.status_code}"
