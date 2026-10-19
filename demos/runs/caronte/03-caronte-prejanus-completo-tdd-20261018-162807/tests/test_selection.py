import json

import pytest


def test_slots(client, edict_factory):
    eid = edict_factory()
    r = client.post(f"/edicts/{eid}/slots", json={"amount": "3"})
    assert r.status_code == 200, r.text
    assert client.get(f"/edicts/{eid}").json()["slots"] == "3"

    client.post(f"/edicts/{eid}/slots", json={"amount": ""})
    assert client.get(f"/edicts/{eid}").json()["slots"] == "0"

    client.post(f"/edicts/{eid}/slots", json={"amount": "-1"})
    assert client.get(f"/edicts/{eid}").json()["slots"] == "0"

    r = client.post(f"/edicts/{eid}/slots", json={"amount": "tres"})
    assert r.status_code >= 400


def test_bidding(client, submission_ctx):
    e, sub = submission_ctx
    if not sub:
        pytest.skip("sem candidaturas no ambiente")
    sid = sub["id"]
    r = client.post(f"/submissions/{sid}/bidding", json={"bidding": "interested"})
    assert r.status_code == 200, r.text
    d = client.get(f"/submissions/{sid}").json()
    assert "interested" in json.dumps(d)

    assert client.post(f"/submissions/{sid}/bidding", json={"bidding": ""}).status_code == 200
    r = client.post(f"/submissions/{sid}/bidding", json={"bidding": "valor-invalido"})
    assert r.status_code >= 400


def test_select_missing_submission(client):
    r = client.post("/submissions/999999999/select", json={"stats": "approved", "user_ids": None})
    assert r.status_code == 404


def test_select_role(client, submission_ctx, is_admin):
    e, sub = submission_ctx
    if not sub:
        pytest.skip("sem candidaturas no ambiente")
    r = client.post(f"/submissions/{sub['id']}/select", json={"stats": "underreview", "user_ids": None})
    if not is_admin:
        assert r.status_code == 403
        return
    if r.status_code == 409:
        pytest.skip("edital fechado")
    assert r.status_code == 200, r.text


def test_entry_semester_normalization(client, submission_ctx):
    e, sub = submission_ctx
    if not sub:
        pytest.skip("sem candidaturas no ambiente")
    sid = sub["id"]
    r = client.post(f"/submissions/{sid}/entry-semester", json={"semester": "first"})
    assert r.status_code == 200, r.text
    d = client.get(f"/submissions/{sid}").json()
    assert "Primeiro semestre." in json.dumps(d)

    client.post(f"/submissions/{sid}/entry-semester", json={"semester": "second"})
    d = client.get(f"/submissions/{sid}").json()
    assert "Segundo semestre." in json.dumps(d)
