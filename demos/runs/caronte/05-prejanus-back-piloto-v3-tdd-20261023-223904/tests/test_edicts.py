import uuid

from tests.utils import edicts

DATES = {
    "date_application": "2027-01-01T00:00:00",
    "date_evaluation": "2027-02-01T00:00:00",
    "date_verification": "2027-03-01T00:00:00",
    "date_closed": "2027-04-01T00:00:00",
}


def _form_ids(admin):
    forms = admin.get("/forms").json()
    ids = [f["id"] for f in forms]
    assert len(ids) >= 1
    return ids[0], (ids[1] if len(ids) > 1 else ids[0])


def _payload(admin, **over):
    cf, rf = _form_ids(admin)
    payload = {
        "title": "Edital de teste " + uuid.uuid4().hex[:8],
        "description": "Descricao do edital de teste",
        "year": 2027,
        "semester": 1,
        "edict_type": "mestrado",
        "is_open": True,
        "candidate_forms": cf,
        "recommenders_forms": rf,
    }
    payload.update(DATES)
    payload.update(over)
    return payload


def test_create_and_get_edict(admin):
    payload = _payload(admin)
    r = admin.post("/edicts", json=payload)
    assert r.status_code == 200, r.text
    created = r.json()
    eid = created["id"]
    assert created["title"] == payload["title"]
    assert created["candidate_forms"] == payload["candidate_forms"]
    assert created["recommenders_forms"] == payload["recommenders_forms"]

    d = admin.get(f"/edicts/{eid}")
    assert d.status_code == 200
    detail = d.json()
    assert detail["title"] == payload["title"]
    assert detail["phase"] == "inscricoes"
    assert detail["is_open"] is True
    assert detail["year"] == 2027
    assert detail["semester"] == 1
    assert detail["candidate_form_id"]
    assert detail["recommender_form_id"]
    assert detail["slots"] == "0"
    assert {p["phase"] for p in detail["phases"]} == {
        "inscricoes",
        "homologacao",
        "avaliacao",
        "encerrado",
    }

    admin.delete(f"/edicts/{eid}/remove")


def test_create_edict_rejects_unordered_dates(admin):
    payload = _payload(
        admin,
        date_closed="2026-01-01T00:00:00",
        date_application="2027-01-01T00:00:00",
    )
    r = admin.post("/edicts", json=payload)
    assert r.status_code >= 400


def test_edicts_list_and_filters(admin):
    payload = _payload(admin)
    eid = admin.post("/edicts", json=payload).json()["id"]
    try:
        listed = edicts(admin)
        mine = [e for e in listed if e["id"] == eid]
        assert mine
        item = mine[0]
        for key in ("id", "title", "year", "semester", "edict_type", "is_open"):
            assert key in item

        r = admin.get("/edicts", params={"type": payload["edict_type"]})
        assert eid in [e["id"] for e in r.json()]

        r = admin.get("/edicts", params={"is_open": True})
        assert eid in [e["id"] for e in r.json()]

        r = admin.get(
            "/edicts",
            params={"type": payload["edict_type"], "is_open": True},
        )
        assert eid in [e["id"] for e in r.json()]

        r = admin.get("/edicts", params={"type": "tipo-inexistente"})
        assert eid not in [e["id"] for e in r.json()]
    finally:
        admin.delete(f"/edicts/{eid}/remove")


def test_edit_edict(admin):
    payload = _payload(admin)
    eid = admin.post("/edicts", json=payload).json()["id"]
    try:
        edit = {
            "title": "Titulo editado",
            "description": "Nova descricao",
            "year": "2028",
            "semester": "2",
            "edict_type": "doutorado",
            "date_application": "2027-05-01T00:00:00",
            "date_evaluation": "2027-06-01T00:00:00",
            "date_verification": "2027-07-01T00:00:00",
            "date_closed": "2027-08-01T00:00:00",
        }
        r = admin.post(f"/edicts/{eid}/edit", json=edit)
        assert r.status_code == 200, r.text
        detail = admin.get(f"/edicts/{eid}").json()
        assert detail["title"] == "Titulo editado"
        assert detail["year"] == 2028
        assert detail["semester"] == 2
    finally:
        admin.delete(f"/edicts/{eid}/remove")


def test_edit_edict_date_only(admin):
    payload = _payload(admin)
    eid = admin.post("/edicts", json=payload).json()["id"]
    try:
        r = admin.post(
            f"/edicts/{eid}/edit-date",
            json={"closed_date": "2027-09-01"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["closed_date"] == "2027-09-01"
        detail = admin.get(f"/edicts/{eid}").json()
        assert str(detail["closed_date"]).startswith("2027-09-01")
    finally:
        admin.delete(f"/edicts/{eid}/remove")


def test_advance_phase_propagates_to_forms(admin):
    payload = _payload(admin)
    eid = admin.post("/edicts", json=payload).json()["id"]
    try:
        phases = admin.get(f"/edicts/{eid}").json()["phases"]
        homologacao = next(p for p in phases if p["phase"] == "homologacao")
        r = admin.post(f"/edicts/{eid}/advance-phase", json={"id": homologacao["id"]})
        assert r.status_code == 200, r.text
        assert r.json()["id"] == homologacao["id"]
        assert r.json()["label"] == "homologacao"
        assert admin.get(f"/edicts/{eid}").json()["phase"] == "homologacao"

        cf = payload["candidate_forms"]
        forms = admin.get("/forms").json()
        form = next(f for f in forms if f["id"] == cf)
        assert form["phase"] == "Approval"

        avaliacao = next(p for p in phases if p["phase"] == "avaliacao")
        admin.post(f"/edicts/{eid}/advance-phase", json={"id": avaliacao["id"]})
        form = next(f for f in admin.get("/forms").json() if f["id"] == cf)
        assert form["phase"] == "Completed"
    finally:
        admin.delete(f"/edicts/{eid}/remove")


def test_close_and_remove_edict(admin):
    payload = _payload(admin)
    eid = admin.post("/edicts", json=payload).json()["id"]

    r = admin.patch(
        f"/edicts/{eid}/close",
        json={"confirmation_deadline": "2027-05-01", "send_approval_letter": False},
    )
    assert r.status_code == 200
    assert admin.get(f"/edicts/{eid}").json()["is_open"] is False

    r = admin.patch(
        f"/edicts/{eid}/close",
        json={"confirmation_deadline": "2027-05-01", "send_approval_letter": False},
    )
    assert r.status_code == 409

    r = admin.delete(f"/edicts/{eid}/remove")
    assert r.status_code == 200
    assert admin.get(f"/edicts/{eid}").status_code == 404


def test_edict_management_requires_admin_role(api, estudante, secretaria, coordenador):
    payload = _payload(api)
    assert api.post("/edicts", json=payload).status_code == 403
    assert estudante.post("/edicts", json=payload).status_code == 403

    for client in (secretaria, coordenador):
        r = client.post("/edicts", json=payload)
        assert r.status_code == 200, r.text
        client.delete(f"/edicts/{r.json()['id']}/remove")
