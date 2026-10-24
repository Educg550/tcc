def test_slots_update(client, edict_with_submissions):
    detail, _ = edict_with_submissions
    edict_id = detail["id"]

    resp = client.post(f"/edicts/{edict_id}/slots", json={"amount": "3"})
    assert resp.status_code == 200
    assert resp.json()["amount"] == "3"

    # repetir atualiza o registro
    resp = client.post(f"/edicts/{edict_id}/slots", json={"amount": "5"})
    assert resp.status_code == 200
    assert resp.json()["amount"] == "5"

    assert edict_detail_slots(client, edict_id) == "5"


def edict_detail_slots(client, edict_id):
    resp = client.get(f"/edicts/{edict_id}")
    assert resp.status_code == 200
    return resp.json()["slots"]


def test_slots_invalid_values(client, edict_with_submissions):
    detail, _ = edict_with_submissions
    edict_id = detail["id"]

    resp = client.post(f"/edicts/{edict_id}/slots", json={"amount": ""})
    assert resp.status_code == 200
    assert resp.json()["amount"] == "0"

    resp = client.post(f"/edicts/{edict_id}/slots", json={"amount": "-2"})
    assert resp.status_code == 200
    assert resp.json()["amount"] == "0"

    assert client.post(
        f"/edicts/{edict_id}/slots", json={"amount": "abc"}
    ).status_code == 422


def test_bidding(client, evaluation_edict):
    detail, subs = evaluation_edict
    submission_id = subs[0]["id"]

    resp = client.post(
        f"/submissions/{submission_id}/bidding", json={"bidding": "interested"}
    )
    assert resp.status_code == 200

    listing = client.get(f"/edicts/{detail['id']}/submissions").json()
    sub = next(s for s in listing["submissions"] if s["id"] == submission_id)
    bidders = sub["bidding_users"]["data"]
    assert 2 in [u["id"] for u in bidders]

    # alteracao mantem um unico interesse corrente
    resp = client.post(
        f"/submissions/{submission_id}/bidding", json={"bidding": "decline"}
    )
    assert resp.status_code == 200
    listing = client.get(f"/edicts/{detail['id']}/submissions").json()
    sub = next(s for s in listing["submissions"] if s["id"] == submission_id)
    bidders = sub["bidding_users"]["data"]
    mine = [u for u in bidders if u["id"] == 2]
    assert len(mine) == 1


def test_bidding_invalid_value(client, evaluation_edict):
    _, subs = evaluation_edict
    resp = client.post(
        f"/submissions/{subs[0]['id']}/bidding", json={"bidding": "invalido"}
    )
    assert resp.status_code == 422


def test_select_requires_admin(client, evaluation_edict):
    _, subs = evaluation_edict
    resp = client.post(
        f"/submissions/{subs[0]['id']}/select",
        json={"stats": "approved", "user_ids": [2]},
    )
    assert resp.status_code == 403


def test_select_submission_not_found(client):
    resp = client.post(
        "/submissions/99999999/select",
        json={"stats": "underreview", "user_ids": None},
    )
    assert resp.status_code == 404


def test_entry_semester_normalization(client, evaluation_edict):
    _, subs = evaluation_edict
    submission_id = subs[0]["id"]

    resp = client.post(
        f"/submissions/{submission_id}/entry-semester", json={"semester": "first"}
    )
    assert resp.status_code == 200

    detail = client.get(f"/submissions/{submission_id}").json()
    assert detail["summary"]["entry_semester"] == "Primeiro semestre."

    resp = client.post(
        f"/submissions/{submission_id}/entry-semester", json={"semester": "second"}
    )
    assert resp.status_code == 200
    detail = client.get(f"/submissions/{submission_id}").json()
    assert detail["summary"]["entry_semester"] == "Segundo semestre."

    resp = client.post(
        f"/submissions/{submission_id}/entry-semester",
        json={"semester": "Outro texto"},
    )
    assert resp.status_code == 200
    detail = client.get(f"/submissions/{submission_id}").json()
    assert detail["summary"]["entry_semester"] == "Outro texto"
