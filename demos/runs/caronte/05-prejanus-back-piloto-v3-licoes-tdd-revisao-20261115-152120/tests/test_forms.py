import pytest


def _forms(api):
    r = api.get("/forms")
    assert r.status_code == 200, r.text
    forms = r.json()
    assert isinstance(forms, list) and forms, "nenhum formulário listado"
    return forms


def test_listar_formularios(api):
    f = _forms(api)[0]
    for key in ("id", "title", "tags", "phase"):
        assert key in f, f


def test_filtros_year_notice(api):
    forms = _forms(api)
    tagged = [f for f in forms if (f.get("tags") or {}).get("Ano")]
    if not tagged:
        pytest.skip("nenhum formulário com tag Ano")
    f = tagged[0]
    year = f["tags"]["Ano"]
    r = api.get("/forms", params={"year": year})
    assert r.status_code == 200
    assert f["id"] in [x["id"] for x in r.json()]
    notice = (f.get("tags") or {}).get("Edital")
    if notice:
        r2 = api.get("/forms", params={"year": year, "notice": notice})
        assert r2.status_code == 200
        assert f["id"] in [x["id"] for x in r2.json()]


def test_form_completo(api):
    fid = _forms(api)[0]["id"]
    r = api.get(f"/forms/{fid}")
    assert r.status_code == 200, r.text
    full = r.json()
    sections = full if isinstance(full, list) else full.get("sections")
    assert sections, full


def test_secoes_e_campos(api):
    fid = _forms(api)[0]["id"]
    r = api.get(f"/forms/{fid}/sections")
    assert r.status_code == 200, r.text
    secs = r.json()
    ids = [s["id"] if isinstance(s, dict) else s for s in secs]
    assert ids
    # segmento literal "sessions"
    r2 = api.get(f"/forms/{fid}/sessions/{ids[0]}/fields")
    assert r2.status_code == 200, r2.text
    fields = r2.json()
    assert isinstance(fields, list) and fields
    f = fields[0]
    assert "id" in f


def test_versao_do_formulario(api):
    fid = _forms(api)[0]["id"]
    r = api.get(f"/forms/{fid}", params={"version": 1})
    assert r.status_code == 200, r.text
    r2 = api.get(f"/forms/{fid}/sections", params={"version": 1})
    assert r2.status_code == 200, r2.text
