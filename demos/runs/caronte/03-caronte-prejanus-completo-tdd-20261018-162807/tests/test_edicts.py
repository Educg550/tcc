import pytest

from conftest import as_list, build_payload, contains_value


def test_create_and_get(client, edict_factory):
    eid = edict_factory()
    r = client.get(f"/edicts/{eid}")
    assert r.status_code == 200
    d = r.json()
    for key in ("id", "title", "year", "semester", "edict_type", "is_open",
                "candidate_form_id", "recommender_form_id", "phases", "slots"):
        assert key in d
    assert d["is_open"] is True
    assert d["slots"] == "0"
    labels = [p.get("label") for p in d["phases"]]
    for phase in ("inscricoes", "homologacao", "avaliacao", "encerrado"):
        assert phase in labels


def test_create_requires_admin(client, is_admin):
    r = client.post("/edicts", json=build_payload(client, title="Edital papel v2"))
    if is_admin:
        assert r.status_code in (200, 201)
        client.delete(f"/edicts/{r.json()['id']}/remove")
    else:
        assert r.status_code == 403


def test_list_and_filters(client, edict_factory):
    eid = edict_factory(title="Edital filtro v2")
    items = as_list(client.get("/edicts").json())
    ids = [i["id"] for i in items]
    assert eid in ids
    et = next(i["edict_type"] for i in items if i["id"] == eid)
    assert eid in [i["id"] for i in as_list(client.get("/edicts", params={"type": et}).json())]
    assert eid in [i["id"] for i in as_list(client.get("/edicts", params={"is_open": "true"}).json())]
    both = as_list(client.get("/edicts", params={"type": et, "is_open": "true"}).json())
    assert eid in [i["id"] for i in both]


def test_create_rejects_unordered_dates(client):
    payload = build_payload(
        client,
        date_application="2027-04-01",
        date_evaluation="2027-03-01",
        date_verification="2027-02-01",
        date_closed="2027-01-01",
    )
    r = client.post("/edicts", json=payload)
    assert r.status_code in (400, 422)


def test_edit(client, edict_factory):
    eid = edict_factory()
    d0 = client.get(f"/edicts/{eid}").json()
    r = client.post(f"/edicts/{eid}/edit", json={
        "title": "Titulo editado v2",
        "description": "Nova descricao",
        "year": "2028",
        "semester": "2",
        "edict_type": d0["edict_type"],
        "date_application": "2028-01-01",
        "date_evaluation": "2028-02-01",
        "date_verification": "2028-03-01",
        "date_closed": "2028-04-01",
    })
    assert r.status_code == 200, r.text
    assert client.get(f"/edicts/{eid}").json()["title"] == "Titulo editado v2"


def test_edit_date(client, edict_factory):
    eid = edict_factory()
    r = client.post(f"/edicts/{eid}/edit-date", json={"closed_date": "2027-06-01"})
    assert r.status_code == 200, r.text
    assert "2027-06-01" in r.text


def test_advance_phase_propagates_to_forms(client, edict_factory):
    eid = edict_factory()
    d = client.get(f"/edicts/{eid}").json()
    target = next(p for p in d["phases"] if p["label"] == "homologacao")
    r = client.post(f"/edicts/{eid}/advance-phase", json={"id": target["id"]})
    assert r.status_code == 200, r.text
    assert r.json()["id"] == target["id"]
    assert r.json()["label"] == "homologacao"
    form_id = d.get("candidate_form_id")
    if form_id:
        form = client.get(f"/forms/{form_id}").json()
        assert contains_value(form, "Approval"), "fase do formulario no Forms nao foi propagada"


def test_close_conflict(client, edict_factory):
    eid = edict_factory()
    body = {"confirmation_deadline": "2027-05-01", "send_approval_letter": False}
    r = client.patch(f"/edicts/{eid}/close", json=body)
    assert r.status_code == 200, r.text
    assert client.get(f"/edicts/{eid}").json()["is_open"] is False
    assert client.patch(f"/edicts/{eid}/close", json=body).status_code == 409


def test_remove(client, edict_factory):
    eid = edict_factory()
    assert client.delete(f"/edicts/{eid}/remove").status_code == 200
    assert client.get(f"/edicts/{eid}").status_code == 404
