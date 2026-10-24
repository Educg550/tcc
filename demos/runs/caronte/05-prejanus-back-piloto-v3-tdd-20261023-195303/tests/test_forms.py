def test_list_forms(client):
    resp = client.get("/forms")
    assert resp.status_code == 200
    forms = resp.json()
    assert isinstance(forms, list) and forms
    for form in forms:
        for key in ("id", "title", "tags", "phase"):
            assert key in form


def test_forms_filters_by_tags(client):
    forms = client.get("/forms").json()
    tagged = next(f for f in forms if f.get("tags"))
    tags = tagged["tags"]
    year = tags.get("Ano")
    notice = tags.get("Edital")
    assert year and notice

    by_year = client.get("/forms", params={"year": year}).json()
    assert by_year
    assert all(f["tags"].get("Ano") == year for f in by_year)

    by_both = client.get("/forms", params={"year": year, "notice": notice}).json()
    assert by_both
    assert all(
        f["tags"].get("Ano") == year and f["tags"].get("Edital") == notice
        for f in by_both
    )


def test_form_full_structure(client):
    form = client.get("/forms").json()[0]
    resp = client.get(f"/forms/{form['id']}")
    assert resp.status_code == 200
    full = resp.json()
    assert full.get("sections")
    section = full["sections"][0]
    assert "fields" in section
    if section["fields"]:
        field = section["fields"][0]
        for key in ("id", "name", "label", "type"):
            assert key in field


def test_form_sections(client):
    form = client.get("/forms").json()[0]
    resp = client.get(f"/forms/{form['id']}/sections")
    assert resp.status_code == 200
    sections = resp.json()
    assert sections
    for section in sections:
        assert "id" in section


def test_form_sections_version_1_accepts_null_version(client):
    form = client.get("/forms").json()[0]
    resp = client.get(f"/forms/{form['id']}/sections", params={"version": 1})
    assert resp.status_code == 200
    assert resp.json()


def test_form_fields_uses_sessions_segment(client):
    form = client.get("/forms").json()[0]
    sections = client.get(f"/forms/{form['id']}/sections").json()
    section_id = sections[0]["id"]
    resp = client.get(f"/forms/{form['id']}/sessions/{section_id}/fields")
    assert resp.status_code == 200
    fields = resp.json()
    assert isinstance(fields, list)
    for field in fields:
        for key in ("id", "name", "type"):
            assert key in field
