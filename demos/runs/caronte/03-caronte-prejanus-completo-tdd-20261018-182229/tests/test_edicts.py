from conftest import edict_detail, get_edicts

INSERT_PAYLOAD = {
    "title": "Edital de teste",
    "description": "descricao",
    "year": 2027,
    "semester": 1,
    "edict_type": "mestrado",
    "is_open": True,
    "candidate_forms": 1,
    "recommenders_forms": 2,
    "date_application": "2027-01-01T00:00:00",
    "date_evaluation": "2027-02-01T00:00:00",
    "date_verification": "2027-03-01T00:00:00",
    "date_closed": "2027-04-01T00:00:00",
}

EDIT_PAYLOAD = dict(INSERT_PAYLOAD)


def test_edicts_list_keys(client):
    eds = get_edicts(client)
    assert eds
    for e in eds:
        assert {"id", "title", "year", "semester", "edict_type", "is_open"} <= set(e)


def test_edicts_filters(client):
    eds = get_edicts(client)
    t = eds[0]["edict_type"]
    by_type = client.get("/edicts", params={"type": t}).json()
    assert all(e["edict_type"] == t for e in by_type)
    by_open = client.get("/edicts", params={"is_open": True}).json()
    assert all(e["is_open"] is True for e in by_open)
    both = client.get("/edicts", params={"type": t, "is_open": True}).json()
    assert all(e["edict_type"] == t and e["is_open"] is True for e in both)


def test_edict_detail(client):
    eds = get_edicts(client)
    d = edict_detail(client, eds[0]["id"])
    for k in (
        "id",
        "title",
        "candidate_form_id",
        "recommender_form_id",
        "description",
        "year",
        "semester",
        "type",
        "is_open",
        "phase",
        "phases",
        "slots",
    ):
        assert k in d, k
    assert isinstance(d["slots"], str)
    phases = {p["phase"] for p in d["phases"]}
    assert {"inscricoes", "homologacao", "avaliacao", "encerrado"} <= phases


def test_teacher_forbidden_on_admin_operations(client):
    eds = get_edicts(client)
    eid = eds[0]["id"]
    assert client.post("/edicts", json=INSERT_PAYLOAD).status_code == 403
    assert client.post(f"/edicts/{eid}/edit", json=EDIT_PAYLOAD).status_code == 403
    assert (
        client.post(f"/edicts/{eid}/edit-date", json={"closed_date": "2027-05-01"}).status_code
        == 403
    )
    assert (
        client.post(f"/edicts/{eid}/advance-phase", json={"id": 1}).status_code == 403
    )
    assert (
        client.patch(
            f"/edicts/{eid}/close",
            json={"confirmation_deadline": "2027-05-01", "send_approval_letter": False},
        ).status_code
        == 403
    )
    assert client.delete(f"/edicts/{eid}/remove").status_code == 403
    tree = {"p": {"section": 1, "field": 1}}
    for tipo in ("candidates", "recommenders"):
        assert (
            client.post(f"/edicts/{eid}/{tipo}/mappings/versions/1/", json=tree).status_code
            == 403
        )
        assert (
            client.put(f"/edicts/{eid}/{tipo}/mappings/versions/1/1", json=tree).status_code
            == 403
        )
        assert client.delete(f"/edicts/{eid}/{tipo}/mappings/versions/1/1").status_code == 403
    assert client.post(f"/edicts/{eid}/interactors_list", json={}).status_code == 403
    assert client.post(f"/edicts/{eid}/pairing-biddings").status_code == 403


def test_mappings_consultation_allowed(client):
    eds = get_edicts(client)
    eid = eds[0]["id"]
    for tipo in ("candidates", "recommenders"):
        r = client.get(f"/edicts/{eid}/{tipo}/mappings")
        assert r.status_code == 200
    r = client.get(f"/edicts/{eid}/candidates/forms/versions/unmapped")
    assert r.status_code == 200
    r = client.get(f"/edicts/{eid}/recommenders/forms/versions/unmapped")
    assert r.status_code == 200
