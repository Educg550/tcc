import pytest


def test_listar_forms(api):
    r = api.get("/forms")
    assert r.status_code == 200, r.text
    forms = r.json()
    assert isinstance(forms, list) and forms
    for f in forms:
        for key in ("id", "title", "tags", "phase"):
            assert key in f


def test_filtros_year_notice(api):
    forms = api.get("/forms").json()
    com_ano = [f for f in forms if f["tags"].get("Ano")]
    if not com_ano:
        pytest.skip("sem formulários com tag Ano")
    ano = com_ano[0]["tags"]["Ano"]
    r = api.get("/forms", params={"year": ano})
    assert r.status_code == 200
    assert r.json()
    assert all(f["tags"].get("Ano") == ano for f in r.json())
    com_edital = [f for f in forms if f["tags"].get("Edital")]
    if com_edital:
        edital = com_edital[0]["tags"]["Edital"]
        r = api.get("/forms", params={"year": ano, "notice": edital})
        assert r.status_code == 200
        for f in r.json():
            assert f["tags"].get("Ano") == ano
            assert f["tags"].get("Edital") == edital


def _form_id(api):
    forms = api.get("/forms").json()
    if not forms:
        pytest.skip("sem formulários")
    return forms[0]["id"]


def test_estrutura_completa(api):
    form_id = _form_id(api)
    r = api.get(f"/forms/{form_id}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "sections" in body
    assert body["sections"]


def test_secoes(api):
    form_id = _form_id(api)
    r = api.get(f"/forms/{form_id}/sections")
    assert r.status_code == 200, r.text
    sections = r.json()
    assert sections
    r2 = api.get(f"/forms/{form_id}/sections", params={"version": 1})
    assert r2.status_code == 200, r2.text


def test_campos_por_secao(api):
    form_id = _form_id(api)
    sections = api.get(f"/forms/{form_id}/sections").json()
    section_id = sections[0]["id"] if isinstance(sections[0], dict) else sections[0]
    r = api.get(f"/forms/{form_id}/sessions/{section_id}/fields")
    assert r.status_code == 200, r.text
    fields = r.json()
    assert isinstance(fields, list)
