def _first_form(client):
    forms = client.get("/forms").json()
    assert forms, "nenhum formulario disponivel"
    return forms[0]


def test_forms_list(client):
    r = client.get("/forms")
    assert r.status_code == 200
    forms = r.json()
    assert isinstance(forms, list) and forms
    for f in forms:
        for k in ("id", "title", "tags", "phase"):
            assert k in f, k


def test_forms_filters_year_and_notice(client):
    forms = client.get("/forms").json()
    year = None
    notice = None
    for f in forms:
        tags = f.get("tags") or {}
        if year is None and tags.get("Ano"):
            year = tags["Ano"]
        if notice is None and tags.get("Edital"):
            notice = tags["Edital"]
    if year is not None:
        filtered = client.get("/forms", params={"year": year}).json()
        assert filtered
        assert all((f.get("tags") or {}).get("Ano") == year for f in filtered)
    if year is not None and notice is not None:
        both = client.get("/forms", params={"year": year, "notice": notice}).json()
        for f in both:
            tags = f.get("tags") or {}
            assert tags.get("Ano") == year
            assert tags.get("Edital") == notice


def test_form_full(client):
    fid = _first_form(client)["id"]
    r = client.get(f"/forms/{fid}")
    assert r.status_code == 200
    assert r.json()
    r = client.get(f"/forms/{fid}", params={"version": 1})
    assert r.status_code == 200


def test_form_sections(client):
    fid = _first_form(client)["id"]
    r = client.get(f"/forms/{fid}/sections")
    assert r.status_code == 200
    secs = r.json()
    assert isinstance(secs, list) and secs
    r = client.get(f"/forms/{fid}/sections", params={"version": 1})
    assert r.status_code == 200


def test_form_fields_sessions_segment(client):
    fid = _first_form(client)["id"]
    secs = client.get(f"/forms/{fid}/sections").json()
    sec = secs[0]
    if isinstance(sec, dict):
        sec = sec["id"]
    r = client.get(f"/forms/{fid}/sessions/{sec}/fields")
    assert r.status_code == 200
    fields = r.json()
    assert isinstance(fields, list)
