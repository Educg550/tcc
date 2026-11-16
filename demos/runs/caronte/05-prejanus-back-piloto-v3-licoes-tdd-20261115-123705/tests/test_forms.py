def test_listar_formularios(api):
    resp = api.get("/forms")
    assert resp.status_code == 200, resp.text
    forms = resp.json()
    if isinstance(forms, dict):
        forms = forms.get("forms") or forms.get("data")
    assert forms


def test_formulario_completo(api):
    forms = api.get("/forms").json()
    if isinstance(forms, dict):
        forms = forms.get("forms") or forms.get("data")
    form_id = forms[0]["id"]

    resp = api.get(f"/forms/{form_id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body


def test_secoes_do_formulario(api):
    forms = api.get("/forms").json()
    if isinstance(forms, dict):
        forms = forms.get("forms") or forms.get("data")
    form_id = forms[0]["id"]

    resp = api.get(f"/forms/{form_id}/sections")
    assert resp.status_code == 200, resp.text
    sections = resp.json()
    if isinstance(sections, dict):
        sections = sections.get("sections") or sections.get("data")
    assert sections


def test_campos_da_secao(api):
    forms = api.get("/forms").json()
    if isinstance(forms, dict):
        forms = forms.get("forms") or forms.get("data")
    form_id = forms[0]["id"]

    sections = api.get(f"/forms/{form_id}/sections").json()
    if isinstance(sections, dict):
        sections = sections.get("sections") or sections.get("data")
    section_id = sections[0]["id"]

    resp = api.get(f"/forms/{form_id}/sessions/{section_id}/fields")
    assert resp.status_code == 200, resp.text
    assert resp.json()


def test_filtro_por_ano_e_tipo(api):
    resp = api.get("/forms", params={"year": "2026", "notice": "mestrado"})
    assert resp.status_code == 200, resp.text
