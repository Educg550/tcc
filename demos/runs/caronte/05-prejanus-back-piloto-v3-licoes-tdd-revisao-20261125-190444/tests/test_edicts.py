import pytest


def test_listar_editais(api):
    r = api.get("/edicts")
    assert r.status_code == 200, r.text
    edicts = r.json()
    assert isinstance(edicts, list)
    assert edicts, "nenhum edital cadastrado"
    for key in ("id", "title", "year", "semester", "edict_type", "is_open"):
        assert key in edicts[0], f"chave ausente: {key}"


def test_listar_filtros(api):
    todos = api.get("/edicts").json()
    if not todos:
        pytest.skip("sem editais")
    tipo = todos[0]["edict_type"]
    r = api.get("/edicts", params={"type": tipo})
    assert r.status_code == 200
    assert all(e["edict_type"] == tipo for e in r.json())
    r = api.get("/edicts", params={"is_open": True})
    assert r.status_code == 200
    assert all(e["is_open"] for e in r.json())
    r = api.get("/edicts", params={"type": tipo, "is_open": True})
    assert r.status_code == 200
    assert all(e["edict_type"] == tipo and e["is_open"] for e in r.json())


def test_criar_edital(api_admin, form_id):
    payload = {
        "title": "Edital criação pytest",
        "description": "desc",
        "year": 2032,
        "semester": 2,
        "edict_type": "doutorado",
        "is_open": True,
        "candidate_forms": form_id,
        "recommenders_forms": form_id,
        "date_application": "2032-01-01T00:00:00",
        "date_verification": "2032-02-01T00:00:00",
        "date_evaluation": "2032-03-01T00:00:00",
        "date_closed": "2032-04-01T00:00:00",
    }
    r = api_admin.post("/edicts", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"]
    assert body["title"] == payload["title"]
    assert body["candidate_forms"] == form_id

    # fases iniciais
    rd = api_admin.get(f"/edicts/{body['id']}")
    detail = rd.json()
    assert detail["phase"] == "inscricoes"
    fases = sorted(p["phase"] for p in detail["phases"])
    assert fases == ["avaliacao", "encerrado", "homologacao", "inscricoes"]
    assert detail["slots"] == "0"
    for key in ("candidate_form_id", "recommender_form_id", "description"):
        assert key in detail


def test_criar_edital_datas_fora_de_ordem(api_admin, form_id):
    payload = {
        "title": "Edital datas inválidas",
        "description": None,
        "year": 2032,
        "semester": 1,
        "edict_type": "mestrado",
        "is_open": True,
        "candidate_forms": form_id,
        "recommenders_forms": form_id,
        "date_application": "2032-04-01T00:00:00",
        "date_verification": "2032-03-01T00:00:00",
        "date_evaluation": "2032-02-01T00:00:00",
        "date_closed": "2032-01-01T00:00:00",
    }
    r = api_admin.post("/edicts", json=payload)
    assert r.status_code in (400, 422), r.text


def test_editar_edital(api_admin, edict_id):
    payload = {
        "title": "Edital editado",
        "description": "nova descrição",
        "year": "2033",
        "semester": "2",
        "edict_type": "mestrado",
        "date_application": "2033-01-01T00:00:00",
        "date_verification": "2033-02-01T00:00:00",
        "date_evaluation": "2033-03-01T00:00:00",
        "date_closed": "2033-04-01T00:00:00",
    }
    r = api_admin.post(f"/edicts/{edict_id}/edit", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["title"] == "Edital editado"
    assert body["year"] == "2033"
    assert body["semester"] == "2"

    rd = api_admin.get(f"/edicts/{edict_id}")
    assert rd.json()["title"] == "Edital editado"


def test_editar_data(api_admin, edict_id):
    r = api_admin.post(
        f"/edicts/{edict_id}/edit-date",
        json={"closed_date": "2034-05-01"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["closed_date"] == "2034-05-01"


def test_avancar_fase_propaga_forms(api_admin, edict_id):
    detail = api_admin.get(f"/edicts/{edict_id}").json()
    candidate_form_id = int(detail["candidate_form_id"])
    homologacao = next(p["id"] for p in detail["phases"] if p["phase"] == "homologacao")
    r = api_admin.post(f"/edicts/{edict_id}/advance-phase", json={"id": homologacao})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == homologacao
    assert body["label"] == "homologacao"

    # fase do formulário de candidatura no Forms
    forms = api_admin.get("/forms").json()
    form = next(f for f in forms if f["id"] == candidate_form_id)
    assert form["phase"] == "Approval", form

    # voltar para inscricoes restaura Registration
    detail = api_admin.get(f"/edicts/{edict_id}").json()
    inscricoes = next(p["id"] for p in detail["phases"] if p["phase"] == "inscricoes")
    api_admin.post(f"/edicts/{edict_id}/advance-phase", json={"id": inscricoes})
    forms = api_admin.get("/forms").json()
    form = next(f for f in forms if f["id"] == candidate_form_id)
    assert form["phase"] == "Registration", form


def test_encerrar_edital(api_admin, form_id):
    payload = {
        "title": "Edital encerramento",
        "description": "desc",
        "year": 2035,
        "semester": 1,
        "edict_type": "mestrado",
        "is_open": True,
        "candidate_forms": form_id,
        "recommenders_forms": form_id,
        "date_application": "2035-01-01T00:00:00",
        "date_verification": "2035-02-01T00:00:00",
        "date_evaluation": "2035-03-01T00:00:00",
        "date_closed": "2035-04-01T00:00:00",
    }
    edict_id = api_admin.post("/edicts", json=payload).json()["id"]
    r = api_admin.patch(
        f"/edicts/{edict_id}/close",
        json={"confirmation_deadline": "2035-05-01", "send_approval_letter": False},
    )
    assert r.status_code == 200, r.text
    assert api_admin.get(f"/edicts/{edict_id}").json()["is_open"] is False
    # encerrar de novo
    r2 = api_admin.patch(
        f"/edicts/{edict_id}/close",
        json={"confirmation_deadline": "2035-05-01", "send_approval_letter": False},
    )
    assert r2.status_code == 409, r2.text


def test_remover_edital(api_admin, form_id):
    payload = {
        "title": "Edital remoção",
        "description": "desc",
        "year": 2036,
        "semester": 1,
        "edict_type": "mestrado",
        "is_open": True,
        "candidate_forms": form_id,
        "recommenders_forms": form_id,
        "date_application": "2036-01-01T00:00:00",
        "date_verification": "2036-02-01T00:00:00",
        "date_evaluation": "2036-03-01T00:00:00",
        "date_closed": "2036-04-01T00:00:00",
    }
    edict_id = api_admin.post("/edicts", json=payload).json()["id"]
    r = api_admin.delete(f"/edicts/{edict_id}/remove")
    assert r.status_code == 200, r.text
    ids = [e["id"] for e in api_admin.get("/edicts").json()]
    assert edict_id not in ids


def test_papeis_edital(api, api_estudante, form_id):
    payload = {
        "title": "Edital permissões",
        "description": "desc",
        "year": 2037,
        "semester": 1,
        "edict_type": "mestrado",
        "is_open": True,
        "candidate_forms": form_id,
        "recommenders_forms": form_id,
        "date_application": "2037-01-01T00:00:00",
        "date_verification": "2037-02-01T00:00:00",
        "date_evaluation": "2037-03-01T00:00:00",
        "date_closed": "2037-04-01T00:00:00",
    }
    for client in (api, api_estudante):
        r = client.post("/edicts", json=payload)
        assert r.status_code == 403, r.text
