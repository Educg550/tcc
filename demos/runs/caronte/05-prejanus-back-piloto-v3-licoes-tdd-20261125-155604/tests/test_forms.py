from tests.conftest import find_form


def test_forms_lista(api):
    r = api.get("/forms")
    assert r.status_code == 200
    forms = r.json()
    assert forms
    f = forms[0]
    for key in ("id", "title", "tags", "phase"):
        assert key in f


def test_forms_filtro_ano(api):
    forms = api.get("/forms").json()
    if not forms:
        return
    year = forms[0]["tags"].get("Ano")
    if not year:
        return
    r = api.get("/forms", params={"year": year})
    assert r.status_code == 200
    assert r.json()
    for f in r.json():
        assert f["tags"].get("Ano") == year


def test_forms_filtro_notice(api):
    forms = api.get("/forms").json()
    notice = None
    for f in forms:
        if f["tags"].get("Edital"):
            notice = f["tags"]["Edital"]
            break
    if not notice:
        return
    r = api.get("/forms", params={"notice": notice})
    assert r.status_code == 200
    assert r.json()
    for f in r.json():
        assert f["tags"].get("Edital") == notice


def test_forms_estrutura(api):
    f = find_form(api)
    r = api.get(f"/forms/{f['id']}")
    assert r.status_code == 200
    data = r.json()
    assert data.get("sections") or data.get("fields") or data


def test_forms_sections(api):
    f = find_form(api)
    r = api.get(f"/forms/{f['id']}/sections")
    assert r.status_code == 200
    sections = r.json()
    assert sections
    r2 = api.get(f"/forms/{f['id']}/sections", params={"version": 1})
    assert r2.status_code == 200


def test_forms_campos_secao(api):
    f = find_form(api)
    sections = api.get(f"/forms/{f['id']}/sections").json()
    assert sections
    section_id = sections[0] if isinstance(sections[0], int) else sections[0]["id"]
    r = api.get(f"/forms/{f['id']}/sessions/{section_id}/fields")
    assert r.status_code == 200
    fields = r.json()
    assert isinstance(fields, list)
    if fields:
        assert "id" in fields[0]
