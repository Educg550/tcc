import pytest


def test_reesend_requires_admin(client, edict_with_submissions):
    _, subs = edict_with_submissions
    resp = client.post(
        f"/submissions/{subs[0]['id']}/reesend_submission",
        json={"text": "por favor corrija"},
    )
    assert resp.status_code == 403


def test_send_accept_not_found(client):
    resp = client.post("/submissions/99999999/send-accept")
    assert resp.status_code == 404


def test_send_letter_not_found(client):
    resp = client.post("/submissions/99999999/send-letter")
    assert resp.status_code == 404


def test_send_letter_requires_approved(client, edict_with_submissions):
    _, subs = edict_with_submissions
    sub = next((s for s in subs if s["stats"] != "approved"), subs[0])
    if sub["stats"] == "approved":
        detail = client.get(f"/submissions/{sub['id']}").json()
        if detail["summary"].get("letter_sent"):
            pytest.skip("sem candidatura não aprovada disponível")
    resp = client.post(f"/submissions/{sub['id']}/send-letter")
    assert resp.status_code == 400


def test_send_accept_requires_approved(client, edict_with_submissions):
    _, subs = edict_with_submissions
    sub = next((s for s in subs if s["stats"] != "approved"), None)
    if sub is None:
        pytest.skip("sem candidatura não aprovada disponível")
    resp = client.post(f"/submissions/{sub['id']}/send-accept")
    assert resp.status_code in (400, 404)
