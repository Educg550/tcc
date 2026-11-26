from tests.conftest import find_form, create_edict


def _leaf(client, form_id):
    sections = client.get(f"/forms/{form_id}/sections").json()
    assert sections
    sid = sections[0] if isinstance(sections[0], int) else sections[0]["id"]
    fields = client.get(f"/forms/{form_id}/sessions/{sid}/fields").json()
    assert fields
    fid = fields[0]["id"]
    return {"section": sid, "field": fid}


def _setup(admin):
    forms = admin.get("/forms").json()
    assert forms
    cand = forms[0]["id"]
    rec = forms[1]["id"] if len(forms) > 1 else forms[0]["id"]
    created = create_edict(admin, cand, rec, title="Edital mapeamento")
    return created, cand, rec


def test_criar_e_listar_mapeamento(admin):
    created, cand, rec = _setup(admin)
    leaf = _leaf(admin, cand)
    tree = {"pessoal": {"nome": leaf}, "nao_mapeado": None}
    r = admin.post(
        f"/edicts/{created['id']}/candidates/mappings/versions/1/", json=tree
    )
    assert r.status_code == 200, r.text
    data = r.json()
    for key in ("id", "edict_id", "form_type", "user_id", "form_version", "mapping", "is_active"):
        assert key in data
    assert data["form_version"] == 1
    assert data["is_active"] is True

    lst = admin.get(f"/edicts/{created['id']}/candidates/mappings").json()
    assert any(m["id"] == data["id"] for m in lst)


def test_mapeamento_duplicado_rejeitado(admin):
    created, cand, rec = _setup(admin)
    tree = {"a": _leaf(admin, cand)}
    r1 = admin.post(f"/edicts/{created['id']}/candidates/mappings/versions/1/", json=tree)
    assert r1.status_code == 200
    r2 = admin.post(f"/edicts/{created['id']}/candidates/mappings/versions/1/", json=tree)
    assert r2.status_code in (400, 409, 422)


def test_mapeamento_referencia_invalida_422(admin):
    created, cand, rec = _setup(admin)
    tree = {"a": {"section": 999999, "field": 999999}}
    r = admin.post(f"/edicts/{created['id']}/candidates/mappings/versions/1/", json=tree)
    assert r.status_code == 422


def test_atualizar_e_excluir_mapeamento(admin):
    created, cand, rec = _setup(admin)
    leaf = _leaf(admin, cand)
    tree = {"a": leaf}
    data = admin.post(
        f"/edicts/{created['id']}/candidates/mappings/versions/1/", json=tree
    ).json()

    nova = {"b": leaf}
    r = admin.put(
        f"/edicts/{created['id']}/candidates/mappings/versions/1/{data['id']}",
        json=nova,
    )
    assert r.status_code == 200, r.text
    lst = admin.get(f"/edicts/{created['id']}/candidates/mappings").json()
    m = next(m for m in lst if m["id"] == data["id"])
    assert "b" in m["mapping"]

    # combinação inexistente: 404
    r404 = admin.put(
        f"/edicts/{created['id']}/candidates/mappings/versions/2/{data['id']}",
        json=nova,
    )
    assert r404.status_code == 404

    d = admin.delete(
        f"/edicts/{created['id']}/candidates/mappings/versions/1/{data['id']}"
    )
    assert d.status_code == 200
    assert d.json() == {"message": "Mapping deleted successfully"}
    lst2 = admin.get(f"/edicts/{created['id']}/candidates/mappings").json()
    assert all(m["id"] != data["id"] for m in lst2)


def test_mapeamento_recommenders(admin):
    created, cand, rec = _setup(admin)
    leaf = _leaf(admin, rec)
    r = admin.post(
        f"/edicts/{created['id']}/recommenders/mappings/versions/1/",
        json={"r": leaf},
    )
    assert r.status_code == 200, r.text
    lst = admin.get(f"/edicts/{created['id']}/recommenders/mappings").json()
    assert lst


def test_versoes_sem_mapeamento(admin):
    created, cand, rec = _setup(admin)
    r = admin.get(f"/edicts/{created['id']}/candidates/forms/versions/unmapped")
    assert r.status_code == 200
    before = r.json()
    # criar mapeamento para a versão 1 (se houver inscrições nela) altera a lista
    leaf = _leaf(admin, cand)
    admin.post(f"/edicts/{created['id']}/candidates/mappings/versions/1/", json={"a": leaf})
    after = admin.get(f"/edicts/{created['id']}/candidates/forms/versions/unmapped").json()
    assert 1 not in after
    assert isinstance(before, list)
