"""V2-MAP-01..03 — mapeamentos por tipo e versao."""
import uuid


def _tree(admin, form_id, version=None):
    params = {"version": version} if version else {}
    sections = admin.get(f"/forms/{form_id}/sections", params=params).json()
    assert sections
    section = sections[0]
    fields = admin.get(f"/forms/{form_id}/sessions/{section['id']}/fields").json()
    assert fields
    return {
        "grupo": {
            "campo": {"section": section["id"], "field": fields[0]["id"]},
            "nao_mapeado": None,
        }
    }


def _form_ids(admin, edict):
    detail = admin.get(f"/edicts/{edict['id']}").json()
    return int(detail["candidate_form_id"]), int(detail["recommender_form_id"])


def test_criar_mapeamento_candidato(admin, edict):
    form_id, _ = _form_ids(admin, edict)
    tree = _tree(admin, form_id, 1)
    r = admin.post(f"/edicts/{edict['id']}/candidates/mappings/versions/1/", json=tree)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"]
    mappings = admin.get(f"/edicts/{edict['id']}/candidates/mappings").json()
    assert any(m["id"] == body["id"] for m in mappings)


def test_criar_mapeamento_recommender(admin, edict):
    _, rec_id = _form_ids(admin, edict)
    tree = _tree(admin, rec_id, 1)
    r = admin.post(f"/edicts/{edict['id']}/recommenders/mappings/versions/1/", json=tree)
    assert r.status_code == 200, r.text
    mappings = admin.get(f"/edicts/{edict['id']}/recommenders/mappings").json()
    assert mappings


def test_mapeamento_referencia_invalida(admin, edict):
    tree = {"grupo": {"campo": {"section": 999999, "field": 999999}}}
    r = admin.post(f"/edicts/{edict['id']}/candidates/mappings/versions/1/", json=tree)
    assert r.status_code == 422


def test_nao_duplica_mapeamento(admin, edict):
    form_id, _ = _form_ids(admin, edict)
    tree = _tree(admin, form_id, 1)
    r1 = admin.post(f"/edicts/{edict['id']}/candidates/mappings/versions/1/", json=tree)
    assert r1.status_code == 200
    r2 = admin.post(f"/edicts/{edict['id']}/candidates/mappings/versions/1/", json=tree)
    assert r2.status_code in (200, 409, 422)
    mappings = admin.get(f"/edicts/{edict['id']}/candidates/mappings").json()
    do_tipo = [m for m in mappings if m.get("form_version") == 1 or m.get("version") == 1]
    assert len(do_tipo) == 1


def test_atualizar_e_excluir_mapeamento(admin, edict):
    form_id, _ = _form_ids(admin, edict)
    tree = _tree(admin, form_id, 1)
    created = admin.post(
        f"/edicts/{edict['id']}/candidates/mappings/versions/1/", json=tree
    ).json()
    mapping_id = created["id"]

    sections = admin.get(f"/forms/{form_id}/sections", params={"version": 1}).json()
    fields = admin.get(f"/forms/{form_id}/sessions/{sections[0]['id']}/fields").json()
    new_tree = {"outro": {"x": {"section": sections[0]["id"], "field": fields[-1]["id"]}}}
    r = admin.put(
        f"/edicts/{edict['id']}/candidates/mappings/versions/1/{mapping_id}",
        json=new_tree,
    )
    assert r.status_code == 200, r.text
    mappings = admin.get(f"/edicts/{edict['id']}/candidates/mappings").json()
    stored = next(m for m in mappings if m["id"] == mapping_id)
    assert stored["mapping"] == new_tree or stored.get("tree") == new_tree

    r = admin.delete(
        f"/edicts/{edict['id']}/candidates/mappings/versions/1/{mapping_id}"
    )
    assert r.status_code == 200
    assert r.json() == {"message": "Mapping deleted successfully"}
    mappings = admin.get(f"/edicts/{edict['id']}/candidates/mappings").json()
    assert all(m["id"] != mapping_id for m in mappings)

    # combinacao inexistente
    r = admin.delete(f"/edicts/{edict['id']}/candidates/mappings/versions/1/{mapping_id}")
    assert r.status_code == 404
    r = admin.put(
        f"/edicts/{edict['id']}/candidates/mappings/versions/7/{mapping_id}",
        json=new_tree,
    )
    assert r.status_code == 404


def test_versoes_sem_mapeamento(admin, submission_ctx):
    edict, _ = submission_ctx
    r = admin.get(f"/edicts/{edict['id']}/candidates/forms/versions/unmapped")
    assert r.status_code == 200
    versions = r.json()
    assert isinstance(versions, list)
    if versions:
        version = versions[0]
        form_id, _ = _form_ids(admin, edict)
        tree = _tree(admin, form_id, version)
        created = admin.post(
            f"/edicts/{edict['id']}/candidates/mappings/versions/{version}/", json=tree
        )
        assert created.status_code == 200, created.text
        depois = admin.get(f"/edicts/{edict['id']}/candidates/forms/versions/unmapped").json()
        assert version not in depois
