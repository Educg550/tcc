from conftest import advance, first_edict_with_submissions, make_edict


def test_slots(admin):
    edict = make_edict(admin)
    r = admin.post(f"/edicts/{edict['id']}/slots", json={"amount": "3"})
    assert r.status_code == 200, r.text
    assert r.json()["amount"] == "3"
    # repetir atualiza
    r = admin.post(f"/edicts/{edict['id']}/slots", json={"amount": "5"})
    assert r.json()["amount"] == "5"
    # vazio e negativo viram "0"
    assert admin.post(f"/edicts/{edict['id']}/slots", json={"amount": ""}).json()["amount"] == "0"
    assert admin.post(f"/edicts/{edict['id']}/slots", json={"amount": "-2"}).json()["amount"] == "0"
    # texto inválido rejeitado
    r = admin.post(f"/edicts/{edict['id']}/slots", json={"amount": "abc"})
    assert r.status_code == 422


def test_bidding(api, admin):
    edict_id, subs = first_edict_with_submissions(api)
    sub_id = subs[0]["id"]
    for valor in ("decline", "available", "interested", "agreed", "interested_scholarship", ""):
        r = api.post(f"/submissions/{sub_id}/bidding", json={"bidding": valor})
        assert r.status_code == 200, (valor, r.text)
    # docente não pode indicar outro usuário
    r = api.post(
        f"/submissions/{sub_id}/bidding",
        json={"bidding": "interested", "user_id": 3},
    )
    assert r.status_code == 200
    detalhe = api.get(f"/submissions/{sub_id}").json()["summary"]
    # administrador pode indicar outro usuário
    r2 = admin.post(
        f"/submissions/{sub_id}/bidding",
        json={"bidding": "interested", "user_id": 3},
    )
    assert r2.status_code == 200, r2.text


def test_select_aprovar_com_orientador(admin, api):
    edict_id, subs = first_edict_with_submissions(admin)
    advance(admin, edict_id, "avaliacao")
    sub_id = subs[0]["id"]
    r = admin.post(
        f"/submissions/{sub_id}/select",
        json={"stats": "approved", "user_ids": [2]},
    )
    assert r.status_code == 200, r.text
    detalhe = api.get(f"/submissions/{sub_id}").json()["summary"]
    assert detalhe["stats"] == "approved"
    assert detalhe["advisor"] is not None
    assert detalhe["advisor"]["id"] == 2


def test_select_docente_403(api):
    edict_id, subs = first_edict_with_submissions(api)
    r = api.post(
        f"/submissions/{subs[0]['id']}/select",
        json={"stats": "refused", "user_ids": None},
    )
    assert r.status_code == 403


def test_select_inexistente_404(admin):
    r = admin.post(
        "/submissions/99999999/select",
        json={"stats": "refused", "user_ids": None},
    )
    assert r.status_code == 404


def test_select_edital_fechado_409(admin):
    edict_id, subs = first_edict_with_submissions(admin)
    advance(admin, edict_id, "avaliacao")
    sub_id = subs[0]["id"]
    admin.patch(
        f"/edicts/{edict_id}/close",
        json={"confirmation_deadline": "2030-01-01", "send_approval_letter": False},
    )
    r = admin.post(
        f"/submissions/{sub_id}/select",
        json={"stats": "refused", "user_ids": None},
    )
    assert r.status_code == 409


def test_entry_semester_normalizacao(admin):
    edict_id, subs = first_edict_with_submissions(admin)
    sub_id = subs[0]["id"]
    r = admin.post(
        f"/submissions/{sub_id}/entry-semester", json={"semester": "first"}
    )
    assert r.status_code == 200, r.text
    detalhe = admin.get(f"/submissions/{sub_id}").json()["summary"]
    assert detalhe["entry_semester"] == "Primeiro semestre."
    r = admin.post(
        f"/submissions/{sub_id}/entry-semester", json={"semester": "Segundo semestre"}
    )
    assert r.status_code == 200
    detalhe = admin.get(f"/submissions/{sub_id}").json()["summary"]
    assert detalhe["entry_semester"] == "Segundo semestre."
