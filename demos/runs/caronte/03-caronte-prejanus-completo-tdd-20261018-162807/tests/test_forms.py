from conftest import as_list


def test_forms_list(client):
    forms = as_list(client.get("/forms").json())
    assert forms, "nenhum formulario retornado"
    f = forms[0]
    assert "id" in f and "title" in f


def test_forms_filters(client):
    assert client.get("/forms", params={"year": "2026"}).status_code == 200
    assert client.get("/forms", params={"notice": "1"}).status_code == 200
    assert client.get("/forms", params={"year": "2026", "notice": "1"}).status_code == 200


def test_form_structure_and_versions(client):
    forms = as_list(client.get("/forms").json())
    fid = forms[0]["id"]
    assert client.get(f"/forms/{fid}").status_code == 200
    assert client.get(f"/forms/{fid}", params={"version": 1}).status_code == 200
    sections = as_list(client.get(f"/forms/{fid}/sections").json())
    assert sections, "formulario sem secoes"
    sid = sections[0]["id"] if isinstance(sections[0], dict) else sections[0]
    fields = as_list(client.get(f"/forms/{fid}/sessions/{sid}/fields").json())
    assert isinstance(fields, list)
