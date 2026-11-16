def _folha():
    return {"section": 1, "field": 1}


def test_criar_e_ler_mapeamento_do_candidato(api_admin, novo_edital):
    edict_id = novo_edital["id"]
    resp = api_admin.post(
        f"/edicts/{edict_id}/candidates/mappings/versions/1/",
        json={"nome": _folha()},
    )
    assert resp.status_code == 200, resp.text

    lidos = api_admin.get(f"/edicts/{edict_id}/candidates/mappings")
    assert lidos.status_code == 200, lidos.text
    assert "nome" in lidos.json()


def test_criar_e_ler_mapeamento_do_recomendante(api_admin, novo_edital):
    edict_id = novo_edital["id"]
    resp = api_admin.post(
        f"/edicts/{edict_id}/recommenders/mappings/versions/1/",
        json={"recomendacao": _folha()},
    )
    assert resp.status_code == 200, resp.text

    lidos = api_admin.get(f"/edicts/{edict_id}/recommenders/mappings")
    assert lidos.status_code == 200, lidos.text
    assert "recomendacao" in lidos.json()


def test_atualizar_e_remover_mapeamento_do_candidato(api_admin, novo_edital):
    edict_id = novo_edital["id"]
    api_admin.post(
        f"/edicts/{edict_id}/candidates/mappings/versions/1/",
        json={"nome": _folha()},
    )
    mappings = api_admin.get(f"/edicts/{edict_id}/candidates/mappings").json()

    # Atualiza a folha existente.
    resp = api_admin.put(
        f"/edicts/{edict_id}/candidates/mappings/versions/1/1",
        json={"section": 2, "field": 3},
    )
    assert resp.status_code == 200, resp.text

    resp = api_admin.delete(
        f"/edicts/{edict_id}/candidates/mappings/versions/1/1"
    )
    assert resp.status_code == 200, resp.text
    assert mappings is not None


def test_versoes_nao_mapeadas(api_admin, novo_edital):
    edict_id = novo_edital["id"]
    for path in (
        f"/edicts/{edict_id}/candidates/forms/versions/unmapped",
        f"/edicts/{edict_id}/recommenders/forms/versions/unmapped",
    ):
        resp = api_admin.get(path)
        assert resp.status_code == 200, path
