from tests.conftest import create_edict, advance_phase


def _form_ids(client):
    forms = client.get("/forms").json()
    assert len(forms) >= 1
    cand = forms[0]["id"]
    rec = forms[1]["id"] if len(forms) > 1 else forms[0]["id"]
    return cand, rec


def test_listar_editais(api):
    r = api.get("/edicts")
    assert r.status_code == 200
    edicts = r.json()
    for e in edicts:
        for key in ("id", "title", "year", "semester", "edict_type", "is_open"):
            assert key in e
    # ordem decrescente por data de encerramento via detalhe
    dates = []
    for e in edicts:
        d = api.get(f"/edicts/{e['id']}").json()
        dates.append(d.get("closed_date") or "")
    assert dates == sorted(dates, reverse=True)


def test_filtros_editais(api):
    edicts = api.get("/edicts").json()
    if not edicts:
        return
    t = edicts[0]["edict_type"]
    r = api.get("/edicts", params={"type": t})
    assert all(e["edict_type"] == t for e in r.json())
    r = api.get("/edicts", params={"is_open": True})
    assert all(e["is_open"] for e in r.json())
    r = api.get("/edicts", params={"type": t, "is_open": True})
    assert all(e["edict_type"] == t and e["is_open"] for e in r.json())


def test_criar_e_consultar_edital(admin):
    cand, rec = _form_ids(admin)
    created = create_edict(admin, cand, rec, title="Edital criado no teste")
    assert created["id"]
    assert created["title"] == "Edital criado no teste"

    detail = admin.get(f"/edicts/{created['id']}").json()
    assert detail["candidate_form_id"] == str(cand)
    assert detail["recommender_form_id"] == str(rec)
    assert detail["phase"] == "inscricoes"
    assert detail["is_open"] is True
    assert detail["slots"] == "0"
    labels = [p["phase"] for p in detail["phases"]]
    assert labels == ["inscricoes", "homologacao", "avaliacao", "encerrado"]


def test_criar_edital_docente_403(api):
    cand, rec = _form_ids(api)
    r = api.post(
        "/edicts",
        json={
            "title": "x",
            "description": "x",
            "year": 2026,
            "semester": 1,
            "edict_type": "mestrado",
            "is_open": True,
            "candidate_forms": cand,
            "recommenders_forms": rec,
            "date_application": "2026-01-01T00:00:00",
            "date_verification": "2026-02-01T00:00:00",
            "date_evaluation": "2026-03-01T00:00:00",
            "date_closed": "2026-04-01T00:00:00",
        },
    )
    assert r.status_code == 403


def test_datas_fora_de_ordem_422(admin):
    cand, rec = _form_ids(admin)
    r = admin.post(
        "/edicts",
        json={
            "title": "x",
            "description": "x",
            "year": 2026,
            "semester": 1,
            "edict_type": "mestrado",
            "is_open": True,
            "candidate_forms": cand,
            "recommenders_forms": rec,
            "date_application": "2026-04-01T00:00:00",
            "date_verification": "2026-03-01T00:00:00",
            "date_evaluation": "2026-02-01T00:00:00",
            "date_closed": "2026-01-01T00:00:00",
        },
    )
    assert r.status_code == 422


def test_editar_edital(admin):
    cand, rec = _form_ids(admin)
    created = create_edict(admin, cand, rec)
    r = admin.post(
        f"/edicts/{created['id']}/edit",
        json={
            "title": "Novo título",
            "description": "Nova descrição",
            "year": "2027",
            "semester": "2",
            "edict_type": "doutorado",
            "date_application": "2026-01-01T00:00:00",
            "date_verification": "2026-02-01T00:00:00",
            "date_evaluation": "2026-03-01T00:00:00",
            "date_closed": "2026-04-01T00:00:00",
        },
    )
    assert r.status_code == 200, r.text
    detail = admin.get(f"/edicts/{created['id']}").json()
    assert detail["title"] == "Novo título"
    assert detail["year"] == 2027
    assert detail["semester"] == 2


def test_editar_data_encerramento(admin):
    cand, rec = _form_ids(admin)
    created = create_edict(admin, cand, rec)
    r = admin.post(
        f"/edicts/{created['id']}/edit-date", json={"closed_date": "2026-05-01"}
    )
    assert r.status_code == 200
    assert r.json()["closed_date"] == "2026-05-01"


def test_avancar_fase_propaga_forms(admin):
    cand, rec = _form_ids(admin)
    created = create_edict(admin, cand, rec)
    resp = advance_phase(admin, created["id"], "homologacao")
    assert resp["label"] == "homologacao"
    detail = admin.get(f"/edicts/{created['id']}").json()
    assert detail["phase"] == "homologacao"
    # fase do formulário no Forms deve ser Approval
    form = admin.get(f"/forms/{cand}").json()
    phase = form.get("phase") or form.get("form", {}).get("phase")
    assert phase == "Approval"


def test_encerrar_edital(admin):
    cand, rec = _form_ids(admin)
    created = create_edict(admin, cand, rec)
    r = admin.patch(
        f"/edicts/{created['id']}/close",
        json={"confirmation_deadline": "2026-06-01", "send_approval_letter": False},
    )
    assert r.status_code == 200
    assert admin.get(f"/edicts/{created['id']}").json()["is_open"] is False
    # encerrar de novo: 409
    r2 = admin.patch(
        f"/edicts/{created['id']}/close",
        json={"confirmation_deadline": "2026-06-01", "send_approval_letter": False},
    )
    assert r2.status_code == 409


def test_remover_edital(admin):
    cand, rec = _form_ids(admin)
    created = create_edict(admin, cand, rec, title="Edital a remover")
    r = admin.delete(f"/edicts/{created['id']}/remove")
    assert r.status_code == 200
    assert admin.get(f"/edicts/{created['id']}").status_code == 404
