def _arvore(api, form_id):
    """Monta uma árvore de mapeamento válida a partir da estrutura do formulário."""
    sections = api.get(f"/forms/{form_id}/sections").json()
    assert sections
    section = sections[0]
    fields = api.get(f"/forms/{form_id}/sessions/{section['id']}/fields").json()
    assert fields, "seção sem campos"
    return {
        "grupo": {
            "propriedade": {"section": section["id"], "field": fields[0]["id"]},
            "nao_mapeada": None,
        }
    }


def test_criar_e_consultar_mapeamento(api_admin, edict_id, form_id):
    arvore = _arvore(api_admin, form_id)
    r = api_admin.post(
        f"/edicts/{edict_id}/candidates/mappings/versions/1/", json=arvore
    )
    assert r.status_code == 200, r.text
    body = r.json()
    for key in ("id", "edict_id", "form_type", "user_id", "form_version", "mapping", "is_active"):
        assert key in body, f"chave ausente: {key}"
    assert body["is_active"] is True
    assert body["form_version"] == 1

    # não criar duplicado
    r2 = api_admin.post(
        f"/edicts/{edict_id}/candidates/mappings/versions/1/", json=arvore
    )
    assert r2.status_code in (400, 409, 422), r2.text

    # listagem
    rl = api_admin.get(f"/edicts/{edict_id}/candidates/mappings")
    assert rl.status_code == 200, rl.text
    mappings = rl.json()
    assert any(m["id"] == body["id"] for m in mappings)


def test_criar_mapeamento_recommenders(api_admin, edict_id, form_id):
    arvore = _arvore(api_admin, form_id)
    r = api_admin.post(
        f"/edicts/{edict_id}/recommenders/mappings/versions/1/", json=arvore
    )
    assert r.status_code == 200, r.text
    rl = api_admin.get(f"/edicts/{edict_id}/recommenders/mappings")
    assert rl.status_code == 200
    assert rl.json()


def test_mapeamento_referencia_invalida(api_admin, edict_id):
    arvore = {"grupo": {"propriedade": {"section": 999999, "field": 999999}}}
    r = api_admin.post(
        f"/edicts/{edict_id}/candidates/mappings/versions/1/", json=arvore
    )
    assert r.status_code == 422, r.text


def test_atualizar_e_excluir_mapeamento(api_admin, edict_id, form_id):
    arvore = _arvore(api_admin, form_id)
    r = api_admin.post(
        f"/edicts/{edict_id}/candidates/mappings/versions/2/", json=arvore
    )
    assert r.status_code == 200, r.text
    mapping_id = r.json()["id"]

    nova = {"outro": {"prop": None}}
    ru = api_admin.put(
        f"/edicts/{edict_id}/candidates/mappings/versions/2/{mapping_id}",
        json=nova,
    )
    assert ru.status_code == 200, ru.text

    rl = api_admin.get(f"/edicts/{edict_id}/candidates/mappings")
    m = next(m for m in rl.json() if m["id"] == mapping_id)
    assert m["mapping"] == nova

    rd = api_admin.delete(
        f"/edicts/{edict_id}/candidates/mappings/versions/2/{mapping_id}"
    )
    assert rd.status_code == 200, rd.text
    assert rd.json() == {"message": "Mapping deleted successfully"}

    rl = api_admin.get(f"/edicts/{edict_id}/candidates/mappings")
    assert all(m["id"] != mapping_id for m in rl.json())

    # combinação inexistente
    rd2 = api_admin.delete(
        f"/edicts/{edict_id}/candidates/mappings/versions/2/{mapping_id}"
    )
    assert rd2.status_code == 404, rd2.text


def test_versoes_sem_mapeamento(api_admin, edict_id):
    for tipo in ("candidates", "recommenders"):
        r = api_admin.get(f"/edicts/{edict_id}/{tipo}/forms/versions/unmapped")
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)
