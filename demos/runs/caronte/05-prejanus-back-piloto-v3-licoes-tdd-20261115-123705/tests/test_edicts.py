def test_listar_editais(api):
    resp = api.get("/edicts")
    assert resp.status_code == 200, resp.text
    edicts = resp.json()
    assert isinstance(edicts, list) and edicts
    for e in edicts:
        for field in ("id", "title", "year", "semester", "edict_type", "is_open"):
            assert field in e


def test_filtro_is_open(api):
    resp = api.get("/edicts", params={"is_open": True})
    assert resp.status_code == 200, resp.text
    assert all(e["is_open"] for e in resp.json())


def test_filtro_por_tipo(api):
    resp = api.get("/edicts", params={"type": "mestrado"})
    assert resp.status_code == 200, resp.text
    assert all(e["edict_type"] == "mestrado" for e in resp.json())


def test_criar_e_consultar_edital(api_admin, novo_edital):
    resp = api_admin.get(f"/edicts/{novo_edital['id']}")
    assert resp.status_code == 200, resp.text
    edict = resp.json()
    assert edict["title"] == "Edital de teste"
    assert edict["is_open"] is True
    assert edict["phase"]
    assert isinstance(edict["phases"], list)


def test_editar_data_edital(api_admin, novo_edital):
    resp = api_admin.post(
        f"/edicts/{novo_edital['id']}/edit-date",
        json={"closed_date": "2026-05-01"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["closed_date"] == "2026-05-01"


def test_editar_edital_completo(api_admin, novo_edital):
    payload = {
        "title": "Edital alterado",
        "description": "Nova descrição",
        "year": "2026",
        "semester": "2",
        "edict_type": "doutorado",
        "date_application": "2026-06-01T00:00:00",
        "date_verification": "2026-07-01T00:00:00",
        "date_evaluation": "2026-08-01T00:00:00",
        "date_closed": "2026-09-01T00:00:00",
    }
    resp = api_admin.post(f"/edicts/{novo_edital['id']}/edit", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["title"] == "Edital alterado"
    assert body["edict_type"] == "doutorado"


def test_avancar_fase_do_edital(api_admin, novo_edital):
    resp = api_admin.post(
        f"/edicts/{novo_edital['id']}/advance-phase",
        json={"id": novo_edital["id"]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == novo_edital["id"]
    assert body["label"]


def test_remover_edital(api_admin):
    from conftest import _create_edict

    edict = _create_edict(api_admin, title="Edital para remover")
    resp = api_admin.delete(f"/edicts/{edict['id']}/remove")
    assert resp.status_code == 200, resp.text
    assert api_admin.get(f"/edicts/{edict['id']}").status_code == 404


def test_fechar_edital(api_admin):
    from conftest import _create_edict

    edict = _create_edict(api_admin, title="Edital para fechar")
    resp = api_admin.patch(
        f"/edicts/{edict['id']}/close",
        json={"confirmation_deadline": "2026-10-01", "send_approval_letter": False},
    )
    assert resp.status_code == 200, resp.text
    detalhe = api_admin.get(f"/edicts/{edict['id']}").json()
    assert detalhe["is_open"] is False
    api_admin.delete(f"/edicts/{edict['id']}/remove")


def test_definir_vagas_por_orientador(api_admin, novo_edital):
    resp = api_admin.post(
        f"/edicts/{novo_edital['id']}/slots", json={"amount": "3"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["amount"] == "3"


def test_edital_inexistente_retorna_404(api):
    assert api.get("/edicts/999999").status_code == 404
