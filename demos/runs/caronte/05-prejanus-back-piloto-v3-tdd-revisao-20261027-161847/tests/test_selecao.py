"""V2-SEL-01 / V2-SEL-02 — vagas, interesses, decisao e semestre."""


def test_slots_atualiza(admin, edict):
    r = admin.post(f"/edicts/{edict['id']}/slots", json={"amount": "3"})
    assert r.status_code == 200
    assert r.json()["amount"] == "3"
    detail = admin.get(f"/edicts/{edict['id']}").json()
    assert detail["slots"] == "3"

    r = admin.post(f"/edicts/{edict['id']}/slots", json={"amount": "5"})
    assert r.status_code == 200
    assert admin.get(f"/edicts/{edict['id']}").json()["slots"] == "5"


def test_slots_vazio_e_negativo(admin, edict):
    assert admin.post(f"/edicts/{edict['id']}/slots", json={"amount": ""}).json()["amount"] == "0"
    assert admin.post(f"/edicts/{edict['id']}/slots", json={"amount": "-2"}).json()["amount"] == "0"
    assert admin.get(f"/edicts/{edict['id']}").json()["slots"] == "0"


def test_slots_texto_invalido(admin, edict):
    r = admin.post(f"/edicts/{edict['id']}/slots", json={"amount": "abc"})
    assert r.status_code == 422


def test_bidding_proprio_usuario(api, submission_ctx):
    _, sub = submission_ctx
    r = api.post(f"/submissions/{sub['id']}/bidding", json={"bidding": "interested"})
    assert r.status_code == 200, r.text
    detail = api.get(f"/submissions/{sub['id']}").json()
    users = detail["bidding_users"]["data"] if "bidding_users" in detail else detail["summary"]["bidding_users"]["data"]
    assert any(u["id"] == 2 for users_list in users.values() for u in users_list)


def test_bidding_admin_indica_outro_usuario(admin, submission_ctx):
    _, sub = submission_ctx
    r = admin.post(f"/submissions/{sub['id']}/bidding", json={"bidding": "decline", "user_id": 3})
    assert r.status_code == 200, r.text
    detail = admin.get(f"/submissions/{sub['id']}").json()
    users = detail["bidding_users"]["data"] if "bidding_users" in detail else detail["summary"]["bidding_users"]["data"]
    assert any(u["id"] == 3 for users_list in users.values() for u in users_list)


def test_bidding_valor_invalido(api, submission_ctx):
    _, sub = submission_ctx
    r = api.post(f"/submissions/{sub['id']}/bidding", json={"bidding": "talvez"})
    assert r.status_code == 422


def test_bidding_vazio(api, submission_ctx):
    _, sub = submission_ctx
    r = api.post(f"/submissions/{sub['id']}/bidding", json={"bidding": ""})
    assert r.status_code == 200


def test_select_aprovado_com_orientador(admin, submission_ctx):
    _, sub = submission_ctx
    r = admin.post(f"/submissions/{sub['id']}/select", json={"stats": "approved", "user_ids": [2]})
    assert r.status_code == 200, r.text
    detail = admin.get(f"/submissions/{sub['id']}").json()
    summary = detail["summary"]
    assert summary["stats"] == "approved"
    assert summary["advisor"]["id"] == 2


def test_select_recusado(admin, submission_ctx):
    _, sub = submission_ctx
    r = admin.post(f"/submissions/{sub['id']}/select", json={"stats": "refused", "user_ids": None})
    assert r.status_code == 200
    assert admin.get(f"/submissions/{sub['id']}").json()["summary"]["stats"] == "refused"


def test_select_docente_403(api, submission_ctx):
    _, sub = submission_ctx
    r = api.post(f"/submissions/{sub['id']}/select", json={"stats": "approved", "user_ids": [2]})
    assert r.status_code == 403


def test_select_inexistente(admin):
    r = admin.post("/submissions/99999999/select", json={"stats": "refused", "user_ids": None})
    assert r.status_code == 404


def test_select_edital_fechado_409(admin, submission_ctx):
    edict, sub = submission_ctx
    admin.patch(f"/edicts/{edict['id']}/close", json={
        "confirmation_deadline": "2027-03-01", "send_approval_letter": False,
    })
    r = admin.post(f"/submissions/{sub['id']}/select", json={"stats": "approved", "user_ids": [2]})
    assert r.status_code == 409


def test_entry_semester_normalizacao(admin, submission_ctx):
    _, sub = submission_ctx
    r = admin.post(f"/submissions/{sub['id']}/entry-semester", json={"semester": "first"})
    assert r.status_code == 200, r.text
    assert admin.get(f"/submissions/{sub['id']}").json()["summary"]["entry_semester"] == "Primeiro semestre."

    admin.post(f"/submissions/{sub['id']}/entry-semester", json={"semester": "Segundo semestre."})
    assert admin.get(f"/submissions/{sub['id']}").json()["summary"]["entry_semester"] == "Segundo semestre."

    admin.post(f"/submissions/{sub['id']}/entry-semester", json={"semester": "Texto livre"})
    assert admin.get(f"/submissions/{sub['id']}").json()["summary"]["entry_semester"] == "Texto livre"
