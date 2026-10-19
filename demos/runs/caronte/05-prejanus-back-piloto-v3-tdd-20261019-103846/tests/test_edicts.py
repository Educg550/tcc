"""V2-EDI-01 a V2-EDI-04: listagem, consulta e ciclo de vida dos editais."""


def test_edicts_listagem_campos(api):
    resp = api.get("/edicts")
    assert resp.status_code == 200
    edicts = resp.json()
    assert edicts
    for edict in edicts:
        for key in ("id", "title", "year", "semester", "edict_type", "is_open"):
            assert key in edict


def test_edicts_ordenacao_decrescente_por_encerramento(api):
    resp = api.get("/edicts")
    assert resp.status_code == 200
    edicts = resp.json()
    if len(edicts) < 2:
        pytest.skip("menos de dois editais")
    dates = [e.get("closed_date") for e in edicts if e.get("closed_date")]
    assert dates == sorted(dates, reverse=True)


def test_edicts_filtros(api):
    resp = api.get("/edicts")
    edicts = resp.json()
    open_edicts = [e for e in edicts if e["is_open"]]
    if not open_edicts:
        pytest.skip("nenhum edital aberto")
    filtered = api.get("/edicts", params={"is_open": True}).json()
    assert all(e["is_open"] for e in filtered)
    assert {e["id"] for e in filtered} == {e["id"] for e in open_edicts}


def test_edict_por_id_configuracao_completa(api, any_edict):
    resp = api.get(f"/edicts/{any_edict['id']}")
    assert resp.status_code == 200
    data = resp.json()
    for key in (
        "id", "title", "candidate_form_id", "recommender_form_id",
        "description", "year", "semester", "type", "is_open",
        "phase", "phases", "slots",
    ):
        assert key in data, f"campo ausente: {key}"
    assert isinstance(data["phases"], list) and data["phases"]
    assert isinstance(data["slots"], str)


def test_edict_inexistente_404(api):
    assert api.get("/edicts/999999").status_code == 404


def test_criacao_e_edicao_restritas_a_administradores(api):
    """V2-AUT-03: docente recebe 403 nas operações administrativas."""
    payload = {
        "title": "Edital de teste",
        "description": "descrição",
        "year": 2027,
        "semester": 1,
        "edict_type": "mestrado",
        "is_open": True,
        "candidate_forms": 1,
        "recommenders_forms": 1,
        "date_application": "2027-01-01T00:00:00",
        "date_verification": "2027-02-01T00:00:00",
        "date_evaluation": "2027-03-01T00:00:00",
        "date_closed": "2027-04-01T00:00:00",
    }
    assert api.post("/edicts", json=payload).status_code == 403

    edicts = api.get("/edicts").json()
    edict_id = edicts[0]["id"]
    assert api.post(f"/edicts/{edict_id}/edit", json={
        "title": "x", "description": "x", "year": "2027", "semester": "1",
        "edict_type": "mestrado",
        "date_application": "2027-01-01T00:00:00",
        "date_verification": "2027-02-01T00:00:00",
        "date_evaluation": "2027-03-01T00:00:00",
        "date_closed": "2027-04-01T00:00:00",
    }).status_code == 403
    assert api.post(f"/edicts/{edict_id}/edit-date",
                    json={"closed_date": "2027-05-01"}).status_code == 403
    assert api.post(f"/edicts/{edict_id}/advance-phase",
                    json={"id": 1}).status_code == 403
    assert api.patch(f"/edicts/{edict_id}/close", json={
        "confirmation_deadline": "2027-05-01",
        "send_approval_letter": False,
    }).status_code == 403
    assert api.delete(f"/edicts/{edict_id}/remove").status_code == 403
    assert api.post(f"/edicts/{edict_id}/interactors_list", json={}).status_code == 403
    assert api.post(f"/edicts/{edict_id}/pairing-biddings").status_code == 403


def test_mapeamentos_restritos_a_administradores(api, any_edict):
    tree = {"pessoal": {"nome": {"section": 1, "field": 1}}}
    edict_id = any_edict["id"]
    assert api.post(
        f"/edicts/{edict_id}/candidates/mappings/versions/1/", json=tree
    ).status_code == 403
    assert api.post(
        f"/edicts/{edict_id}/recommenders/mappings/versions/1/", json=tree
    ).status_code == 403


def test_consulta_mapeamentos_autenticada(api, any_edict):
    edict_id = any_edict["id"]
    for tipo in ("candidates", "recommenders"):
        resp = api.get(f"/edicts/{edict_id}/{tipo}/mappings")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        resp = api.get(f"/edicts/{edict_id}/{tipo}/forms/versions/unmapped")
        assert resp.status_code == 200
