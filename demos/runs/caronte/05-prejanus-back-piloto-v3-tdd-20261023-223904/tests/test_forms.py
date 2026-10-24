def _forms(client):
    r = client.get("/forms")
    assert r.status_code == 200, r.text
    forms = r.json()
    assert isinstance(forms, list) and forms
    return forms


def _tag(form, key):
    tags = form.get("tags") or {}
    return tags.get(key)


def test_list_forms(api):
    for f in _forms(api):
        for key in ("id", "title", "tags", "phase"):
            assert key in f


def test_forms_filter_by_year(api):
    forms = _forms(api)
    target = next(f for f in forms if _tag(f, "Ano"))
    year = _tag(target, "Ano")
    r = api.get("/forms", params={"year": year})
    assert r.status_code == 200
    ids = [f["id"] for f in r.json()]
    assert target["id"] in ids
    assert all(_tag(f, "Ano") == year for f in r.json())


def test_forms_filter_by_notice(api):
    forms = _forms(api)
    target = next(f for f in forms if _tag(f, "Edital"))
    notice = _tag(target, "Edital")
    r = api.get("/forms", params={"notice": notice})
    assert r.status_code == 200
    ids = [f["id"] for f in r.json()]
    assert target["id"] in ids


def test_forms_filters_combined(api):
    forms = _forms(api)
    target = next(f for f in forms if _tag(f, "Ano") and _tag(f, "Edital"))
    r = api.get(
        "/forms",
        params={"year": _tag(target, "Ano"), "notice": _tag(target, "Edital")},
    )
    assert r.status_code == 200
    assert target["id"] in [f["id"] for f in r.json()]


def test_forms_filter_no_match(api):
    r = api.get("/forms", params={"year": "ano-inexistente-9999"})
    assert r.status_code == 200
    assert r.json() == []


def _section_ids(client, form_id, params=None):
    r = client.get(f"/forms/{form_id}/sections", params=params or {})
    assert r.status_code == 200, r.text
    data = r.json()
    if data and isinstance(data[0], dict):
        return [s["id"] for s in data]
    return list(data)


def _field_ids(client, form_id, section_id):
    r = client.get(f"/forms/{form_id}/sessions/{section_id}/fields")
    assert r.status_code == 200, r.text
    data = r.json()
    if data and isinstance(data[0], dict):
        return [f["id"] for f in data]
    return list(data)


def test_form_full_and_sections(api):
    form_id = _forms(api)[0]["id"]
    r = api.get(f"/forms/{form_id}")
    assert r.status_code == 200

    sections = _section_ids(api, form_id)
    assert sections
    fields = _field_ids(api, form_id, sections[0])
    assert fields


def test_form_version_selection(api):
    form_id = _forms(api)[0]["id"]
    r = api.get(f"/forms/{form_id}", params={"version": 1})
    assert r.status_code == 200
    r = api.get(f"/forms/{form_id}/sections", params={"version": 1})
    assert r.status_code == 200
    assert r.json()
