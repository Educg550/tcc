import pytest

from conftest import get_edict, make_edict


def _leaf(api, form_id):
    """Extrai uma folha válida (section, field) da estrutura do formulário."""
    sections = api.get(f"/forms/{form_id}/sections").json()
    for sec in sections:
        sid = sec["id"] if isinstance(sec, dict) else sec
        fields = api.get(f"/forms/{form_id}/sessions/{sid}/fields").json()
        if fields:
            fid = fields[0]["id"] if isinstance(fields[0], dict) else fields[0]
            return {"section": sid, "field": fid}
    pytest.skip("formulário sem campos")


def _tree(api, form_id):
    leaf = _leaf(api, form_id)
    return {"pessoal": {"nome": leaf}, "formacao": None}


def test_criar_e_listar_mapeamento(admin, api):
    edict = make_edict(admin)
    detalhe = get_edict(admin, edict["id"])
    tree = _tree(api, detalhe["candidate_form_id"])
    r = admin.post(
        f"/edicts/{edict['id']}/candidates/mappings/versions/1/", json=tree
    )
    assert r.status_code == 200, r.text
    mapping = r.json()
    for key in ("id", "edict_id", "form_type", "user_id", "form_version", "mapping"):
        assert key in mapping
    assert mapping["mapping"] == tree
    lista = admin.get(f"/edicts/{edict['id']}/candidates/mappings").json()
    assert any(m["id"] == mapping["id"] for m in lista)


def test_mapeamento_duplicado_rejeitado(admin, api):
    edict = make_edict(admin)
    detalhe = get_edict(admin, edict["id"])
    tree = _tree(api, detalhe["candidate_form_id"])
    r1 = admin.post(
        f"/edicts/{edict['id']}/candidates/mappings/versions/1/", json=tree
    )
    assert r1.status_code == 200
    r2 = admin.post(
        f"/edicts/{edict['id']}/candidates/mappings/versions/1/", json=tree
    )
    assert r2.status_code in (400, 409, 422)
    lista = admin.get(f"/edicts/{edict['id']}/candidates/mappings").json()
    assert len([m for m in lista if m["form_version"] == 1]) == 1


def test_mapeamento_referencia_invalida_422(admin):
    edict = make_edict(admin)
    tree = {"x": {"y": {"section": 999999, "field": 999999}}}
    r = admin.post(
        f"/edicts/{edict['id']}/candidates/mappings/versions/1/", json=tree
    )
    assert r.status_code == 422


def test_atualizar_e_excluir_mapeamento(admin, api):
    edict = make_edict(admin)
    detalhe = get_edict(admin, edict["id"])
    tree = _tree(api, detalhe["candidate_form_id"])
    created = admin.post(
        f"/edicts/{edict['id']}/candidates/mappings/versions/1/", json=tree
    ).json()
    nova_tree = {"outro": tree["pessoal"]}
    r = admin.put(
        f"/edicts/{edict['id']}/candidates/mappings/versions/1/{created['id']}",
        json=nova_tree,
    )
    assert r.status_code == 200, r.text
    lista = admin.get(f"/edicts/{edict['id']}/candidates/mappings").json()
    alvo = [m for m in lista if m["id"] == created["id"]][0]
    assert alvo["mapping"] == nova_tree
    d = admin.delete(
        f"/edicts/{edict['id']}/candidates/mappings/versions/1/{created['id']}"
    )
    assert d.status_code == 200
    assert d.json() == {"message": "Mapping deleted successfully"}
    lista = admin.get(f"/edicts/{edict['id']}/candidates/mappings").json()
    assert all(m["id"] != created["id"] for m in lista)
    # combinação inexistente
    d2 = admin.delete(
        f"/edicts/{edict['id']}/candidates/mappings/versions/1/{created['id']}"
    )
    assert d2.status_code == 404


def test_mapeamento_recommenders(admin, api):
    edict = make_edict(admin)
    detalhe = get_edict(admin, edict["id"])
    tree = _tree(api, detalhe["recommender_form_id"])
    r = admin.post(
        f"/edicts/{edict['id']}/recommenders/mappings/versions/1/", json=tree
    )
    assert r.status_code == 200, r.text
    lista = admin.get(f"/edicts/{edict['id']}/recommenders/mappings").json()
    assert lista


def test_versoes_sem_mapeamento(admin, api):
    edict_id, _ = None, None
    for e in admin.get("/edicts").json():
        subs = admin.get(f"/edicts/{e['id']}/submissions").json()["submissions"]
        if subs:
            edict_id = e["id"]
            break
    if edict_id is None:
        pytest.skip("nenhum edital com inscrições")
    r = admin.get(f"/edicts/{edict_id}/candidates/forms/versions/unmapped")
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)
    r2 = admin.get(f"/edicts/{edict_id}/recommenders/forms/versions/unmapped")
    assert r2.status_code == 200
