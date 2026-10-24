import pytest

from tests.utils import edicts_with_submissions


@pytest.fixture(scope="module")
def base(admin):
    found = edicts_with_submissions(admin)
    assert found
    eid, subs = found[0]
    return eid, subs


def test_slots(admin, base):
    eid, _ = base
    r = admin.post(f"/edicts/{eid}/slots", json={"amount": "3"})
    assert r.status_code == 200, r.text
    assert r.json()["amount"] == "3"

    r = admin.post(f"/edicts/{eid}/slots", json={"amount": "5"})
    assert r.status_code == 200
    assert r.json()["amount"] == "5"

    detail = admin.get(f"/edicts/{eid}").json()
    assert detail["slots"] == "5"

    assert admin.post(f"/edicts/{eid}/slots", json={"amount": ""}).json()["amount"] == "0"
    assert admin.post(f"/edicts/{eid}/slots", json={"amount": "-2"}).json()["amount"] == "0"
    assert admin.post(f"/edicts/{eid}/slots", json={"amount": "abc"}).status_code >= 400


def test_bidding(api, admin, base):
    _eid, subs = base
    sid = subs[0]["id"]

    r = api.post(f"/submissions/{sid}/bidding", json={"bidding": "interested"})
    assert r.status_code == 200, r.text

    listing = api.get(f"/edicts/{_eid}/submissions").json()["submissions"]
    sub = next(s for s in listing if s["id"] == sid)
    data = sub["bidding_users"]["data"]
    interested = data.get("interested", [])
    assert any(u["id"] == 2 for u in interested)

    # administrador indica outro usuario
    r = admin.post(
        f"/submissions/{sid}/bidding", json={"bidding": "decline", "user_id": 3}
    )
    assert r.status_code == 200
    listing = admin.get(f"/edicts/{_eid}/submissions").json()["submissions"]
    sub = next(s for s in listing if s["id"] == sid)
    data = sub["bidding_users"]["data"]
    assert any(u["id"] == 3 for u in data.get("decline", []))

    # nao-administrador nao indica outro usuario
    r = api.post(
        f"/submissions/{sid}/bidding", json={"bidding": "available", "user_id": 3}
    )
    assert r.status_code == 200
    listing = api.get(f"/edicts/{_eid}/submissions").json()["submissions"]
    sub = next(s for s in listing if s["id"] == sid)
    data = sub["bidding_users"]["data"]
    assert any(u["id"] == 2 for u in data.get("available", []))

    assert (
        api.post(f"/submissions/{sid}/bidding", json={"bidding": "banana"}).status_code
        == 422
    )
    assert (
        api.post(f"/submissions/{sid}/bidding", json={"bidding": ""}).status_code == 200
    )


def test_select_requires_admin(api, base):
    _eid, subs = base
    r = api.post(
        f"/submissions/{subs[0]['id']}/select",
        json={"stats": "approved", "user_ids": [2]},
    )
    assert r.status_code == 403


def test_select_not_found(admin):
    r = admin.post(
        "/submissions/99999999/select",
        json={"stats": "approved", "user_ids": [2]},
    )
    assert r.status_code == 404


def test_select_approve_with_advisor(admin, base):
    eid, subs = base
    sid = subs[0]["id"]
    r = admin.post(
        f"/submissions/{sid}/select", json={"stats": "approved", "user_ids": [2]}
    )
    assert r.status_code == 200, r.text

    listing = admin.get(f"/edicts/{eid}/submissions").json()["submissions"]
    sub = next(s for s in listing if s["id"] == sid)
    assert sub["stats"] == "approved"
    assert sub["advisor"] and sub["advisor"]["id"] == 2

    r = admin.post(f"/submissions/{sid}/select", json={"stats": "refused", "user_ids": None})
    assert r.status_code == 200
    listing = admin.get(f"/edicts/{eid}/submissions").json()["submissions"]
    assert next(s for s in listing if s["id"] == sid)["stats"] == "refused"


def test_entry_semester_normalization(admin, base):
    _eid, subs = base
    sid = subs[0]["id"]

    r = admin.post(f"/submissions/{sid}/entry-semester", json={"semester": "first"})
    assert r.status_code == 200, r.text
    summary = admin.get(f"/submissions/{sid}").json()["summary"]
    assert "Primeiro semestre." in str(summary)

    r = admin.post(f"/submissions/{sid}/entry-semester", json={"semester": "second"})
    assert r.status_code == 200
    summary = admin.get(f"/submissions/{sid}").json()["summary"]
    assert "Segundo semestre." in str(summary)

    r = admin.post(
        f"/submissions/{sid}/entry-semester", json={"semester": "Texto livre."}
    )
    assert r.status_code == 200
    summary = admin.get(f"/submissions/{sid}").json()["summary"]
    assert "Texto livre." in str(summary)


def test_select_blocked_on_closed_edict(admin, base):
    eid, subs = base
    sid = subs[-1]["id"]
    r = admin.patch(
        f"/edicts/{eid}/close",
        json={"confirmation_deadline": "2027-12-01", "send_approval_letter": False},
    )
    assert r.status_code == 200
    r = admin.post(
        f"/submissions/{sid}/select", json={"stats": "approved", "user_ids": [2]}
    )
    assert r.status_code == 409
