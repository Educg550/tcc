import pytest


def test_slots(api, edict_id):
    r = api.post(f"/edicts/{edict_id}/slots", json={"amount": "3"})
    assert r.status_code == 200, r.text
    assert r.json()["amount"] == "3"

    detail = api.get(f"/edicts/{edict_id}").json()
    assert detail["slots"] == "3"

    # repetir atualiza
    r = api.post(f"/edicts/{edict_id}/slots", json={"amount": "5"})
    assert r.status_code == 200
    assert api.get(f"/edicts/{edict_id}").json()["slots"] == "5"

    # vazio e negativo viram "0"
    assert api.post(f"/edicts/{edict_id}/slots", json={"amount": ""}).json()["amount"] == "0"
    assert api.post(f"/edicts/{edict_id}/slots", json={"amount": "-2"}).json()["amount"] == "0"

    # texto inválido é rejeitado
    r = api.post(f"/edicts/{edict_id}/slots", json={"amount": "abc"})
    assert r.status_code in (400, 422), r.text


def test_bidding(api, api_admin, submission_em_avaliacao_module):
    _, submission_id = submission_em_avaliacao_module
    for valor in ("decline", "available", "interested", "agreed", "interested_scholarship", ""):
        r = api.post(f"/submissions/{submission_id}/bidding", json={"bidding": valor})
        assert r.status_code == 200, (valor, r.text)

    # docente não indica outro usuário: o interesse fica no próprio id
    r = api.post(
        f"/submissions/{submission_id}/bidding",
        json={"bidding": "interested", "user_id": 3},
    )
    assert r.status_code == 200, r.text
    detail = api.get(f"/submissions/{submission_id}").json()
    texto = str(detail)
    assert "interested" in texto

    # administrador pode indicar outro usuário
    r = api_admin.post(
        f"/submissions/{submission_id}/bidding",
        json={"bidding": "interested", "user_id": 3},
    )
    assert r.status_code == 200, r.text


def test_select(api, api_admin, submission_em_avaliacao_module):
    _, submission_id = submission_em_avaliacao_module
    # docente não altera decisão
    r = api.post(
        f"/submissions/{submission_id}/select",
        json={"stats": "refused", "user_ids": None},
    )
    assert r.status_code == 403, r.text

    # aprovação com orientador existente
    r = api_admin.post(
        f"/submissions/{submission_id}/select",
        json={"stats": "approved", "user_ids": [2]},
    )
    assert r.status_code == 200, r.text
    detail = api_admin.get(f"/submissions/{submission_id}").json()
    assert detail["summary"]["stats"] == "approved"
    advisor = detail["summary"].get("advisor")
    assert advisor and advisor["id"] == 2

    # inscrição inexistente
    r = api_admin.post(
        "/submissions/99999999/select",
        json={"stats": "refused", "user_ids": None},
    )
    assert r.status_code == 404, r.text


def test_entry_semester(api_admin, submission_em_avaliacao_module):
    _, submission_id = submission_em_avaliacao_module
    r = api_admin.post(
        f"/submissions/{submission_id}/entry-semester", json={"semester": "first"}
    )
    assert r.status_code == 200, r.text
    detail = api_admin.get(f"/submissions/{submission_id}").json()
    assert detail["summary"]["entry_semester"] == "Primeiro semestre."

    r = api_admin.post(
        f"/submissions/{submission_id}/entry-semester", json={"semester": "Segundo semestre."}
    )
    assert r.status_code == 200
    detail = api_admin.get(f"/submissions/{submission_id}").json()
    assert detail["summary"]["entry_semester"] == "Segundo semestre."


def test_edital_fechado_bloqueia_decisao(api_admin, form_id):
    """Um edital fechado impede alterações de decisão (409)."""
    edicts = api_admin.get("/edicts", params={"is_open": False}).json()
    alvo = None
    for edict in edicts:
        subs = api_admin.get(f"/edicts/{edict['id']}/submissions").json()["submissions"]
        if subs:
            alvo = subs[0]["id"]
            break
    if alvo is None:
        pytest.skip("nenhuma submissão em edital fechado")
    r = api_admin.post(
        f"/submissions/{alvo}/select",
        json={"stats": "refused", "user_ids": None},
    )
    assert r.status_code == 409, r.text
