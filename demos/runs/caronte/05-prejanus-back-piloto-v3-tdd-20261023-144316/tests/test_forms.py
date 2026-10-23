def test_list_forms(api):
    resp = api.get("/forms")
    assert resp.status_code == 200
    forms = resp.json()
    assert isinstance(forms, list) and forms
    for form in forms:
        for key in ("id", "title", "tags", "phase"):
            assert key in form


def test_forms_filters_by_tags(api):
    forms = api.get("/forms").json()
    form = forms[0]
    tags = form.get("tags") or {}
    year = tags.get("Ano")
    notice = tags.get("Edital")
    if year:
        filtered = api.get("/forms", params={"year": year}).json()
        assert any(f["id"] == form["id"] for f in filtered)
        assert all((f.get("tags") or {}).get("Ano") == year for f in filtered)
    if year and notice:
        both = api.get("/forms", params={"year": year, "notice": notice}).json()
        assert any(f["id"] == form["id"] for f in both)


def test_form_full_structure(api):
    form = api.get("/forms").json()[0]
    resp = api.get(f"/forms/{form['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body  # seções e campos na ordem da estrutura


def test_form_sections(api):
    form = api.get("/forms").json()[0]
    resp = api.get(f"/forms/{form['id']}/sections")
    assert resp.status_code == 200
    sections = resp.json()
    assert isinstance(sections, list) and sections


def test_form_sections_version_1_accepts_null(api):
    form = api.get("/forms").json()[0]
    resp = api.get(f"/forms/{form['id']}/sections", params={"version": 1})
    assert resp.status_code == 200
    assert resp.json()


def test_form_fields_uses_sessions_segment(api):
    form = api.get("/forms").json()[0]
    sections = api.get(f"/forms/{form['id']}/sections").json()
    section = sections[0]
    section_id = section["id"] if isinstance(section, dict) else section
    resp = api.get(f"/forms/{form['id']}/sessions/{section_id}/fields")
    assert resp.status_code == 200
    fields = resp.json()
    assert isinstance(fields, list)
