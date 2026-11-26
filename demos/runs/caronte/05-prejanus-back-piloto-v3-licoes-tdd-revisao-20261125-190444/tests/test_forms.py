def test_forms_list(api):
    r = api.get("/forms")
    assert r.status_code == 200, r.text
    forms = r.json()
    assert isinstance(forms, list) and forms
    for key in ("id", "title", "tags", "phase"):
        assert key in forms[0], f"chave ausente: {key}"


def test_forms_filtros(api):
    todos = api.get("/forms").json()
    algum = todos[0]
    year = algum["tags"].get("Ano")
    notice = algum["tags"].get("Edital")
    if year:
        r = api.get("/forms", params={"year": year})
        assert r.status_code == 200
        assert r.json(), "filtro por ano não retornou formulários"
    if notice:
        r = api.get("/forms", params={"notice": notice})
        assert r.status_code == 200
        assert r.json(), "filtro por edital não retornou formulários"
    if year and notice:
        r = api.get("/forms", params={"year": year, "notice": notice})
        assert r.status_code == 200
        assert r.json(), "filtros combinados não retornaram formulários"


def test_forms_full(api, form_id):
    r = api.get(f"/forms/{form_id}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "sections" in body or isinstance(body, list), body


def test_forms_sections(api, form_id):
    r = api.get(f"/forms/{form_id}/sections")
    assert r.status_code == 200, r.text
    sections = r.json()
    assert isinstance(sections, list) and sections


def test_forms_sections_version_1(api, form_id):
    r = api.get(f"/forms/{form_id}/sections", params={"version": 1})
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_forms_fields_segmento_sessions(api, form_id):
    rs = api.get(f"/forms/{form_id}/sections")
    section_id = rs.json()[0]["id"]
    r = api.get(f"/forms/{form_id}/sessions/{section_id}/fields")
    assert r.status_code == 200, r.text
    fields = r.json()
    assert isinstance(fields, list)
    if fields:
        for key in ("id", "name", "label", "type"):
            assert key in fields[0], f"chave ausente: {key}"
