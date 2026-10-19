import json

from conftest import as_list


def _section_id(s):
    return s["id"] if isinstance(s, dict) else s


def _first_field(client, form_id):
    sections = as_list(client.get(f"/forms/{form_id}/sections").json())
    assert sections, "formulario sem secoes"
    sid = _section_id(sections[0])
    fields = as_list(client.get(f"/forms/{form_id}/sessions/{sid}/fields").json())
    assert fields, "secao sem campos"
    return sid, fields[0]["id"]


def test_mapping_lifecycle(client, edict_factory):
    eid = edict_factory()
    d = client.get(f"/edicts/{eid}").json()
    form_id = d["candidate_form_id"]
    assert form_id, "edital sem formulario de candidatura"
    sid, fid = _first_field(client, form_id)

    tree = {"nome": {"section": sid, "field": fid}, "nao_mapeado": None}
    url = f"/edicts/{eid}/candidates/mappings/versions/1/"
    r = client.post(url, json=tree)
    assert r.status_code in (200, 201), r.text
    m = r.json()
    assert "id" in m

    # nao cria dois mapeamentos para o mesmo edital, tipo e versao
    assert client.post(url, json=tree).status_code in (400, 409, 422)

    lst = as_list(client.get(f"/edicts/{eid}/candidates/mappings").json())
    assert m["id"] in [x["id"] for x in lst]

    tree2 = {"nome": {"section": sid, "field": fid}, "extra": None}
    r = client.put(f"/edicts/{eid}/candidates/mappings/versions/1/{m['id']}", json=tree2)
    assert r.status_code == 200, r.text
    lst2 = as_list(client.get(f"/edicts/{eid}/candidates/mappings").json())
    got = next(x for x in lst2 if x["id"] == m["id"])
    assert got.get("tree") == tree2 or "extra" in json.dumps(got)

    r = client.delete(f"/edicts/{eid}/candidates/mappings/versions/1/{m['id']}")
    assert r.status_code == 200
    assert r.json() == {"message": "Mapping deleted successfully"}
    lst3 = as_list(client.get(f"/edicts/{eid}/candidates/mappings").json())
    assert m["id"] not in [x["id"] for x in lst3]

    # combinacoes inexistentes respondem 404
    assert client.put(
        f"/edicts/{eid}/candidates/mappings/versions/1/{m['id']}", json=tree2
    ).status_code == 404
    assert client.delete(
        f"/edicts/{eid}/candidates/mappings/versions/1/{m['id']}"
    ).status_code == 404


def test_mapping_invalid_reference(client, edict_factory):
    eid = edict_factory()
    r = client.post(
        f"/edicts/{eid}/recommenders/mappings/versions/1/",
        json={"x": {"section": 99999999, "field": 99999999}},
    )
    assert r.status_code == 422


def test_unmapped_versions_empty_for_new_edict(client, edict_factory):
    eid = edict_factory()
    r = client.get(f"/edicts/{eid}/candidates/forms/versions/unmapped")
    assert r.status_code == 200
    assert as_list(r.json()) == []
