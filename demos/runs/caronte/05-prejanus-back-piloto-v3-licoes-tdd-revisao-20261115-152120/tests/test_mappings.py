from helpers import (
    create_edict,
    first_leaf,
    mapping_items,
    mapping_version,
    submissions_of,
)


def _edict_form(admin, eid):
    d = admin.get(f"/edicts/{eid}").json()
    return int(d["candidate_form_id"])


def _mappings(admin, eid, tipo):
    r = admin.get(f"/edicts/{eid}/{tipo}/mappings")
    assert r.status_code == 200, r.text
    return mapping_items(r.json())


def test_ciclo_mapeamento(admin):
    eid = create_edict(admin, "Edital mapeamento", copy=False)
    leaf = first_leaf(admin, _edict_form(admin, eid))
    tree = {"pessoal": {"nome": leaf}}
    r = admin.post(f"/edicts/{eid}/candidates/mappings/versions/1/", json=tree)
    assert r.status_code == 200, r.text
    created = r.json()
    mid = created["id"]
    assert created.get("form_version", created.get("version")) == 1

    items = _mappings(admin, eid, "candidates")
    assert any(m["id"] == mid for m in items)

    # não cria dois mapeamentos para o mesmo edital, tipo e versão
    admin.post(f"/edicts/{eid}/candidates/mappings/versions/1/", json=tree)
    items = _mappings(admin, eid, "candidates")
    same = [m for m in items if mapping_version(m) == 1]
    assert len(same) == 1

    # atualização refletida e preservada
    tree2 = {"pessoal": {"nome": leaf, "extra": None}}
    r2 = admin.put(f"/edicts/{eid}/candidates/mappings/versions/1/{mid}", json=tree2)
    assert r2.status_code == 200, r2.text
    items = _mappings(admin, eid, "candidates")
    assert any(m["id"] == mid for m in items)

    # exclusão
    r3 = admin.delete(f"/edicts/{eid}/candidates/mappings/versions/1/{mid}")
    assert r3.status_code == 200, r3.text
    assert r3.json()["message"] == "Mapping deleted successfully"
    items = _mappings(admin, eid, "candidates")
    assert all(m["id"] != mid for m in items)

    # combinações inexistentes
    assert (
        admin.delete(f"/edicts/{eid}/candidates/mappings/versions/1/{mid}").status_code
        == 404
    )
    assert (
        admin.put(
            f"/edicts/{eid}/candidates/mappings/versions/1/{mid}", json=tree2
        ).status_code
        == 404
    )


def test_mapeamento_recommenders(admin):
    eid = create_edict(admin, "Edital mapeamento recomendador", copy=False)
    d = admin.get(f"/edicts/{eid}").json()
    leaf = first_leaf(admin, int(d["recommender_form_id"]))
    tree = {"recomendador": {"nome": leaf}}
    r = admin.post(f"/edicts/{eid}/recommenders/mappings/versions/1/", json=tree)
    assert r.status_code == 200, r.text
    items = _mappings(admin, eid, "recommenders")
    assert items


def test_mapeamento_referencia_invalida_422(admin):
    eid = create_edict(admin, "Edital mapeamento inválido", copy=False)
    tree = {"x": {"section": 999999, "field": 999999}}
    r = admin.post(f"/edicts/{eid}/candidates/mappings/versions/1/", json=tree)
    assert r.status_code == 422, r.text


def test_versoes_sem_mapeamento(admin):
    eid = create_edict(admin, "Edital unmapped", copy=False)
    # materializa as inscrições do edital
    submissions_of(admin, eid)
    r = admin.get(f"/edicts/{eid}/candidates/forms/versions/unmapped")
    assert r.status_code == 200, r.text
    versions = r.json()
    assert isinstance(versions, list) and versions, versions

    v = versions[0]
    leaf = first_leaf(admin, _edict_form(admin, eid))
    rr = admin.post(
        f"/edicts/{eid}/candidates/mappings/versions/{v}/", json={"a": {"b": leaf}}
    )
    assert rr.status_code == 200, rr.text
    r2 = admin.get(f"/edicts/{eid}/candidates/forms/versions/unmapped")
    assert v not in r2.json()

    # endpoint dos recomendadores responde
    assert (
        admin.get(f"/edicts/{eid}/recommenders/forms/versions/unmapped").status_code
        == 200
    )
