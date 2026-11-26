import pytest

from conftest import (
    advance,
    get_edict,
    make_edict,
    unique_title,
)


def test_listar_editais(admin):
    r = admin.get("/edicts")
    assert r.status_code == 200
    edicts = r.json()
    assert isinstance(edicts, list) and edicts
    for e in edicts:
        for key in ("id", "title", "year", "semester", "edict_type", "is_open"):
            assert key in e


def test_filtros_type_e_is_open(admin):
    todos = admin.get("/edicts").json()
    if not todos:
        pytest.skip("sem editais")
    alvo = todos[0]
    r = admin.get("/edicts", params={"type": alvo["edict_type"]})
    assert r.status_code == 200
    assert all(e["edict_type"] == alvo["edict_type"] for e in r.json())
    r = admin.get("/edicts", params={"is_open": alvo["is_open"]})
    assert all(e["is_open"] == alvo["is_open"] for e in r.json())
    r = admin.get(
        "/edicts", params={"type": alvo["edict_type"], "is_open": alvo["is_open"]}
    )
    assert all(
        e["edict_type"] == alvo["edict_type"] and e["is_open"] == alvo["is_open"]
        for e in r.json()
    )


def test_criar_edital(admin):
    edict = make_edict(admin)
    assert edict["id"] > 0
    detalhe = get_edict(admin, edict["id"])
    assert detalhe["phase"] == "inscricoes"
    assert detalhe["is_open"] is True
    assert detalhe["slots"] == "0"
    fases = sorted(p["phase"] for p in detalhe["phases"])
    assert fases == ["avaliacao", "encerrado", "homologacao", "inscricoes"]
    for key in ("candidate_form_id", "recommender_form_id", "description", "phases"):
        assert key in detalhe


def test_criar_edital_docente_403(api):
    r = api.post(
        "/edicts",
        json={
            "title": unique_title(),
            "description": "x",
            "year": 2027,
            "semester": 1,
            "edict_type": "mestrado",
            "is_open": True,
            "candidate_forms": 1,
            "recommenders_forms": 2,
            "date_application": "2027-01-01T00:00:00",
            "date_verification": "2027-02-01T00:00:00",
            "date_evaluation": "2027-03-01T00:00:00",
            "date_closed": "2027-04-01T00:00:00",
        },
    )
    assert r.status_code == 403


def test_criar_edital_datas_fora_de_ordem(admin):
    r = admin.post(
        "/edicts",
        json={
            "title": unique_title(),
            "description": "x",
            "year": 2027,
            "semester": 1,
            "edict_type": "mestrado",
            "is_open": True,
            "candidate_forms": 1,
            "recommenders_forms": 2,
            "date_application": "2027-03-01T00:00:00",
            "date_verification": "2027-02-01T00:00:00",
            "date_evaluation": "2027-04-01T00:00:00",
            "date_closed": "2027-05-01T00:00:00",
        },
    )
    assert r.status_code == 422


def test_editar_edital(admin):
    edict = make_edict(admin)
    novo_titulo = unique_title("Editado")
    r = admin.post(
        f"/edicts/{edict['id']}/edit",
        json={
            "title": novo_titulo,
            "description": "nova descrição",
            "year": "2028",
            "semester": "2",
            "edict_type": "doutorado",
            "date_application": "2028-01-01T00:00:00",
            "date_verification": "2028-02-01T00:00:00",
            "date_evaluation": "2028-03-01T00:00:00",
            "date_closed": "2028-04-01T00:00:00",
        },
    )
    assert r.status_code == 200, r.text
    detalhe = get_edict(admin, edict["id"])
    assert detalhe["title"] == novo_titulo
    assert detalhe["year"] == 2028
    assert detalhe["semester"] == 2


def test_editar_apenas_data(admin):
    edict = make_edict(admin)
    r = admin.post(
        f"/edicts/{edict['id']}/edit-date", json={"closed_date": "2027-06-01"}
    )
    assert r.status_code == 200, r.text
    assert r.json()["closed_date"] == "2027-06-01"


def test_avancar_fase_propaga_forms(admin):
    edict = make_edict(admin)
    resp = advance(admin, edict["id"], "homologacao")
    assert resp["label"] == "homologacao"
    assert get_edict(admin, edict["id"])["phase"] == "homologacao"
    forms = admin.get("/forms").json()
    alvo = [f for f in forms if str(f["id"]) == str(edict["candidate_form_id"])]
    assert alvo, "formulário de candidatura não encontrado em /forms"
    assert alvo[0]["phase"] == "Approval"
    advance(admin, edict["id"], "avaliacao")
    forms = admin.get("/forms").json()
    alvo = [f for f in forms if str(f["id"]) == str(edict["candidate_form_id"])]
    assert alvo[0]["phase"] == "Completed"


def test_encerrar_edital(admin):
    edict = make_edict(admin)
    r = admin.patch(
        f"/edicts/{edict['id']}/close",
        json={"confirmation_deadline": "2027-05-01", "send_approval_letter": False},
    )
    assert r.status_code == 200
    assert get_edict(admin, edict["id"])["is_open"] is False
    r2 = admin.patch(
        f"/edicts/{edict['id']}/close",
        json={"confirmation_deadline": "2027-05-01", "send_approval_letter": False},
    )
    assert r2.status_code == 409


def test_remover_edital(admin):
    edict = make_edict(admin)
    r = admin.delete(f"/edicts/{edict['id']}/remove")
    assert r.status_code == 200
    ids = [e["id"] for e in admin.get("/edicts").json()]
    assert edict["id"] not in ids


def test_papeis_administrativos_podem_criar(secretaria, coordenador):
    for client in (secretaria, coordenador):
        edict = make_edict(client)
        assert edict["id"] > 0
