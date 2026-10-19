"""V2-FOR-01 e V2-FOR-02: formulários, estrutura e versões."""


def test_forms_lista_metadados(api):
    resp = api.get("/forms")
    assert resp.status_code == 200
    forms = resp.json()
    assert isinstance(forms, list) and forms
    form = forms[0]
    for key in ("id", "title", "tags", "phase"):
        assert key in form


def test_forms_filtro_por_ano_e_edital(api):
    resp = api.get("/forms")
    assert resp.status_code == 200
    forms = resp.json()
    with_year = [f for f in forms if f.get("tags", {}).get("Ano")]
    if not with_year:
        pytest.skip("nenhum formulário com tag Ano")
    year = with_year[0]["tags"]["Ano"]
    filtered = api.get("/forms", params={"year": year}).json()
    assert all(f["tags"].get("Ano") == year for f in filtered)
    assert filtered
    # combinação de filtros não pode misturar outros anos
    both = api.get("/forms", params={"year": year, "notice": "inexistente-xyz"}).json()
    assert both == []


def test_form_full_estrutura(api):
    forms = api.get("/forms").json()
    form = forms[0]
    resp = api.get(f"/forms/{form['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert "sections" in data
    sections = data["sections"]
    assert sections
    positions = [s.get("position") for s in sections]
    assert positions == sorted(positions)
    for section in sections:
        for field in section.get("fields", []):
            for key in ("id", "name", "label", "type"):
                assert key in field


def test_form_sections_ids(api):
    forms = api.get("/forms").json()
    form = forms[0]
    resp = api.get(f"/forms/{form['id']}/sections")
    assert resp.status_code == 200
    sections = resp.json()
    assert sections
    assert all("id" in s for s in sections)


def test_form_sections_por_versao(api):
    forms = api.get("/forms").json()
    form = forms[0]
    resp = api.get(f"/forms/{form['id']}/sections", params={"version": 1})
    assert resp.status_code == 200
    assert resp.json()


def test_form_fields_do_segmento_sessions(api):
    forms = api.get("/forms").json()
    form = forms[0]
    sections = api.get(f"/forms/{form['id']}/sections").json()
    section_id = sections[0]["id"]
    resp = api.get(f"/forms/{form['id']}/sessions/{section_id}/fields")
    assert resp.status_code == 200
    fields = resp.json()
    assert isinstance(fields, list)
    positions = [f.get("position") for f in fields]
    assert positions == sorted(positions)
