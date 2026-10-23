from tests.conftest import all_edicts, edict_detail


def test_list_edicts_shape(api):
    edicts = all_edicts(api)
    assert isinstance(edicts, list)
    for edict in edicts:
        for key in ("id", "title", "year", "semester", "edict_type", "is_open"):
            assert key in edict


def test_list_edicts_ordered_by_closed_date_desc(api):
    edicts = all_edicts(api)
    dates = []
    for edict in edicts:
        detail = edict_detail(api, edict["id"])
        dates.append(detail.get("closed_date"))
    known = [d for d in dates if d]
    assert known == sorted(known, reverse=True)


def test_edict_filters(api):
    edicts = all_edicts(api)
    if not edicts:
        return
    edict = edicts[0]
    by_type = api.get("/edicts", params={"type": edict["edict_type"]}).json()
    assert all(e["edict_type"] == edict["edict_type"] for e in by_type)
    by_open = api.get("/edicts", params={"is_open": edict["is_open"]}).json()
    assert all(e["is_open"] == edict["is_open"] for e in by_open)
    both = api.get(
        "/edicts",
        params={"type": edict["edict_type"], "is_open": edict["is_open"]},
    ).json()
    assert all(
        e["edict_type"] == edict["edict_type"] and e["is_open"] == edict["is_open"]
        for e in both
    )


def test_edict_detail_shape(api):
    edicts = all_edicts(api)
    assert edicts, "nenhum edital disponível"
    detail = edict_detail(api, edicts[0]["id"])
    for key in (
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
        assert key in detail
    assert isinstance(detail["slots"], str)
    assert {p["phase"] for p in detail["phases"]} >= {
        "inscricoes",
        "homologacao",
        "avaliacao",
        "encerrado",
    }


def test_teacher_cannot_create_edict(api):
    payload = {
        "title": "Edital de teste",
        "description": "desc",
        "year": 2026,
        "semester": 1,
        "edict_type": "mestrado",
        "is_open": True,
        "candidate_forms": 1,
        "recommenders_forms": 1,
        "date_application": "2026-01-01T00:00:00",
        "date_verification": "2026-02-01T00:00:00",
        "date_evaluation": "2026-03-01T00:00:00",
        "date_closed": "2026-04-01T00:00:00",
    }
    assert api.post("/edicts", json=payload).status_code == 403


def test_teacher_cannot_admin_edict_routes(api):
    edicts = all_edicts(api)
    if not edicts:
        return
    edict_id = edicts[0]["id"]
    body = {
        "title": "x",
        "description": "x",
        "year": "2026",
        "semester": "1",
        "edict_type": "mestrado",
        "date_application": "2026-01-01T00:00:00",
        "date_verification": "2026-02-01T00:00:00",
        "date_evaluation": "2026-03-01T00:00:00",
        "date_closed": "2026-04-01T00:00:00",
    }
    assert api.post(f"/edicts/{edict_id}/edit", json=body).status_code == 403
    assert (
        api.post(
            f"/edicts/{edict_id}/edit-date", json={"closed_date": "2026-05-01"}
        ).status_code
        == 403
    )
    assert (
        api.post(f"/edicts/{edict_id}/advance-phase", json={"id": 1}).status_code == 403
    )
    assert (
        api.patch(
            f"/edicts/{edict_id}/close",
            json={"confirmation_deadline": "2026-05-01", "send_approval_letter": False},
        ).status_code
        == 403
    )
    assert api.delete(f"/edicts/{edict_id}/remove").status_code == 403
    assert (
        api.post(
            f"/edicts/{edict_id}/candidates/mappings/versions/1/",
            json={"nome": {"section": 1, "field": 1}},
        ).status_code
        == 403
    )
    assert (
        api.post(
            f"/edicts/{edict_id}/recommenders/mappings/versions/1/",
            json={"nome": {"section": 1, "field": 1}},
        ).status_code
        == 403
    )


def test_mappings_listing(api):
    edicts = all_edicts(api)
    if not edicts:
        return
    edict_id = edicts[0]["id"]
    for tipo in ("candidates", "recommenders"):
        resp = api.get(f"/edicts/{edict_id}/{tipo}/mappings")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        resp = api.get(f"/edicts/{edict_id}/{tipo}/forms/versions/unmapped")
        assert resp.status_code == 200


def test_nonexistent_edict_detail(api):
    assert api.get("/edicts/999999").status_code == 404
