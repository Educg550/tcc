import pytest


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
    user = r.json()
    assert user["id"] == 2
    assert user["role"] == "teacher"
    for key in ("id", "name", "email", "nusp", "role"):
        assert key in user


def test_login_admin_role(admin):
    user = admin.get("/auth/login").json()
    assert user["id"] == 1
    assert user["role"] == "administrator"


def test_login_estudante_nao_e_admin(estudante):
    user = estudante.get("/auth/login").json()
    assert user["role"] == "student"
    r = estudante.post("/edicts", json={})
    assert r.status_code == 403


def test_sem_sessao_protegidas_401(sem_atalho):
    r = sem_atalho.get("/edicts")
    assert r.status_code == 401
    r = sem_atalho.get("/forms")
    assert r.status_code == 401


def test_consultas_exigem_autenticacao(sem_atalho):
    r = sem_atalho.get("/edicts/1")
    assert r.status_code == 401
    r = sem_atalho.get("/submissions/1")
    assert r.status_code == 401


@pytest.mark.parametrize("fixture_name", ["secretaria", "coordenador"])
def test_papeis_administrativos_podem_criar_edital(request, fixture_name, make_edict):
    client = request.getfixturevalue(fixture_name)
    user = client.get("/auth/login").json()
    assert user["role"] in ("secretary", "coordinator")
    edict = make_edict()
    r = client.get(f"/edicts/{edict['id']}")
    assert r.status_code == 200


def test_docente_nao_cria_edital(api):
    r = api.post("/edicts", json={
        "title": "x", "description": "x", "year": 2027, "semester": 1,
        "edict_type": "mestrado", "is_open": True,
        "candidate_forms": 1, "recommenders_forms": 1,
        "date_application": "2027-01-01T00:00:00",
        "date_verification": "2027-01-02T00:00:00",
        "date_evaluation": "2027-01-03T00:00:00",
        "date_closed": "2027-01-04T00:00:00",
    })
    assert r.status_code == 403


def test_docente_nao_gerencia_edital(api, edict):
    assert api.post(f"/edicts/{edict['id']}/edit", json={}).status_code == 403
    assert api.post(f"/edicts/{edict['id']}/advance-phase", json={"id": 1}).status_code == 403
    assert api.patch(f"/edicts/{edict['id']}/close", json={
        "confirmation_deadline": "2027-02-01", "send_approval_letter": False,
    }).status_code == 403
    assert api.delete(f"/edicts/{edict['id']}/remove").status_code == 403
