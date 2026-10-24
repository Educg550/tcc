from conftest import all_edicts, edict_detail


def test_list_edicts_fields(client):
    edicts = all_edicts(client)
    assert edicts
    for edict in edicts:
        for key in ("id", "title", "year", "semester", "edict_type", "is_open"):
            assert key in edict


def test_list_edicts_ordered_by_closed_date_desc(client):
    edicts = all_edicts(client)
    dates = [edict_detail(client, e["id"]).get("closed_date") for e in edicts]
    dates = [d for d in dates if d]
    assert dates == sorted(dates, reverse=True)


def test_edicts_filters(client):
    edicts = all_edicts(client)
    sample = edicts[0]
    by_type = client.get("/edicts", params={"type": sample["edict_type"]}).json()
    assert by_type
    assert all(e["edict_type"] == sample["edict_type"] for e in by_type)

    by_open = client.get("/edicts", params={"is_open": sample["is_open"]}).json()
    assert all(e["is_open"] == sample["is_open"] for e in by_open)

    combined = client.get(
        "/edicts",
        params={"type": sample["edict_type"], "is_open": sample["is_open"]},
    ).json()
    assert all(
        e["edict_type"] == sample["edict_type"] and e["is_open"] == sample["is_open"]
        for e in combined
    )


def test_edict_detail(client):
    edicts = all_edicts(client)
    detail = edict_detail(client, edicts[0]["id"])
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
    labels = [p["phase"] for p in detail["phases"]]
    assert labels == ["inscricoes", "homologacao", "avaliacao", "encerrado"]


def test_edict_slots_default_zero(client):
    edicts = all_edicts(client)
    detail = edict_detail(client, edicts[0]["id"])
    # usuário docente sem configuração de vagas
    assert detail["slots"] in ("0", "0.0")


def test_teacher_forbidden_on_admin_operations(client, edict_with_submissions):
    detail, _ = edict_with_submissions
    edict_id = detail["id"]
    payload = {
        "title": "x",
        "description": "x",
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
    assert client.post("/edicts", json=payload).status_code == 403
    assert (
        client.post(f"/edicts/{edict_id}/edit", json=payload).status_code == 403
    )
    assert (
        client.post(
            f"/edicts/{edict_id}/edit-date", json={"closed_date": "2026-05-01"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/edicts/{edict_id}/advance-phase", json={"id": detail["phases"][0]["id"]}
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"/edicts/{edict_id}/close",
            json={"confirmation_deadline": "2026-05-01", "send_approval_letter": False},
        ).status_code
        == 403
    )
    assert client.delete(f"/edicts/{edict_id}/remove").status_code == 403
    assert (
        client.post(
            f"/edicts/{edict_id}/candidates/mappings/versions/1/", json={}
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/edicts/{edict_id}/interactors_list", json={}
        ).status_code
        == 403
    )
    assert (
        client.post(f"/edicts/{edict_id}/pairing-biddings").status_code == 403
    )
