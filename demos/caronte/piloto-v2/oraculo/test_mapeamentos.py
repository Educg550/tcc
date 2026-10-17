import pytest

from conftest import banco, sql

ARVORE_V2 = {"name": {"section": 102, "field": 1002}, "email": None,
             "graduation": {"course": {"section": 103, "field": 1021}, "country": None}}
TIPOS = [("candidates", "candidate"), ("recommenders", "recommender")]


def mapeamentos(edict_id, tipo):
    return banco(f"SELECT id, form_version, mapping FROM edict_form_mappings "
                 f"WHERE edict_id={edict_id} AND form_type='{tipo}' ORDER BY id")


@pytest.mark.req("V2-MAP-01", "V2-BD-01")
@pytest.mark.integracao("INT-PREJANUS-DB", "INT-FORMS-DB")
def test_cria_mapeamento_de_candidatura_para_nova_versao(clientes):
    sql_antes = mapeamentos(2, "candidate")
    r = clientes("coordenador").post("edicts/2/candidates/mappings/versions/2/",
                                     json={"name": {"section": 13, "field": 51}, "email": None})
    assert r.status_code == 200
    m = r.json()
    assert {k: m[k] for k in ("edict_id", "form_type", "user_id", "is_active", "mapping")} == {
        "edict_id": 2, "form_type": "candidate", "user_id": 5, "is_active": True,
        "mapping": {"name": {"section": 13, "field": 51}, "email": None}}
    assert str(m["version"]) == "2"
    assert len(mapeamentos(2, "candidate")) == len(sql_antes) + 1


@pytest.mark.req("V2-MAP-01")
def test_cria_mapeamento_de_recomendacao(admin):
    arvore = {"fullname": {"section": 9, "field": 44}, "rating": {"section": 10, "field": 48}}
    r = admin.post("edicts/2/recommenders/mappings/versions/1/", json=arvore)
    assert r.status_code == 200
    assert (r.json()["form_type"], r.json()["mapping"]) == ("recommender", arvore)
    assert [m["mapping"] for m in admin.get("edicts/2/recommenders/mappings").json()] == [arvore]


@pytest.mark.req("V2-MAP-01")
@pytest.mark.parametrize("versao,arvore", [
    (1, {"name": {"section": 2, "field": 999}}),
    (2, {"name": {"section": 2, "field": 2}}),
    (1, {"grupo": {"name": {"section": 3, "field": 2}}}),
])
def test_referencia_invalida_na_versao_responde_422(admin, versao, arvore):
    sql("DELETE FROM edict_form_mappings WHERE edict_id=1 AND form_type='candidate'")
    r = admin.post(f"edicts/1/candidates/mappings/versions/{versao}/", json=arvore)
    assert r.status_code == 422
    assert mapeamentos(1, "candidate") == []


@pytest.mark.req("V2-MAP-01")
def test_versao_sem_campos_usa_todos_os_campos_do_formulario(admin):
    r = admin.post("edicts/1/candidates/mappings/versions/9/", json={"name": {"section": 2, "field": 2}})
    assert r.status_code == 200


@pytest.mark.req("V2-MAP-01")
def test_nao_duplica_mapeamento_do_mesmo_tipo_e_versao(admin):
    antes = mapeamentos(1, "candidate")
    r = admin.post("edicts/1/candidates/mappings/versions/2/", json=ARVORE_V2)
    assert r.status_code >= 400
    assert mapeamentos(1, "candidate") == antes


@pytest.mark.req("V2-MAP-02")
@pytest.mark.parametrize("rota,tipo", TIPOS)
def test_lista_mapeamentos_por_tipo(api, rota, tipo):
    r = api.get(f"edicts/1/{rota}/mappings")
    assert r.status_code == 200
    assert sorted((m["id"], int(m["form_version"])) for m in r.json()) == [
        (l["id"], l["form_version"]) for l in mapeamentos(1, tipo)]
    assert all(m["form_type"] == tipo and m["edict_id"] == 1 for m in r.json())


@pytest.mark.req("V2-MAP-02")
def test_atualiza_a_arvore_preservando_outras_versoes(admin):
    v1 = mapeamentos(1, "candidate")[0]
    v2 = next(m for m in mapeamentos(1, "candidate") if m["form_version"] == 2)
    r = admin.put(f"edicts/1/candidates/mappings/versions/2/{v2['id']}", json=ARVORE_V2)
    assert r.status_code == 200
    por_id = {m["id"]: m for m in admin.get("edicts/1/candidates/mappings").json()}
    assert por_id[v2["id"]]["mapping"] == ARVORE_V2
    assert por_id[v1["id"]]["mapping"] == v1["mapping"]


@pytest.mark.req("V2-MAP-02")
def test_atualiza_mapeamento_de_recomendacao(admin):
    rec = mapeamentos(1, "recommender")[0]
    arvore = {"fullname": {"section": 9, "field": 44}}
    assert admin.put(f"edicts/1/recommenders/mappings/versions/1/{rec['id']}", json=arvore).status_code == 200
    assert mapeamentos(1, "recommender")[0]["mapping"] == arvore


@pytest.mark.req("V2-MAP-02")
@pytest.mark.parametrize("rota,tipo", TIPOS)
def test_exclui_mapeamento(admin, rota, tipo):
    alvo = mapeamentos(1, tipo)[0]
    r = admin.delete(f"edicts/1/{rota}/mappings/versions/{alvo['form_version']}/{alvo['id']}")
    assert (r.status_code, r.json()) == (200, {"message": "Mapping deleted successfully"})
    assert alvo["id"] not in [m["id"] for m in admin.get(f"edicts/1/{rota}/mappings").json()]


@pytest.mark.req("V2-MAP-02")
@pytest.mark.parametrize("metodo", ["PUT", "DELETE"])
@pytest.mark.parametrize("caminho", [
    "edicts/1/candidates/mappings/versions/2/1",
    "edicts/2/candidates/mappings/versions/1/1",
    "edicts/1/recommenders/mappings/versions/1/1",
    "edicts/1/candidates/mappings/versions/1/999",
])
def test_combinacao_inexistente_responde_404(admin, metodo, caminho):
    antes = banco("SELECT id, mapping FROM edict_form_mappings ORDER BY id")
    r = admin.request(metodo, caminho, json=ARVORE_V2 if metodo == "PUT" else None)
    assert r.status_code == 404
    assert banco("SELECT id, mapping FROM edict_form_mappings ORDER BY id") == antes


@pytest.mark.req("V2-MAP-03")
@pytest.mark.parametrize("edict_id,rota,esperado", [
    (1, "candidates", []), (1, "recommenders", []), (2, "candidates", []), (2, "recommenders", [1]),
])
def test_versoes_sem_mapeamento(api, edict_id, rota, esperado):
    r = api.get(f"edicts/{edict_id}/{rota}/forms/versions/unmapped")
    assert (r.status_code, sorted(r.json())) == (200, esperado)


@pytest.mark.req("V2-MAP-03")
def test_remover_e_recriar_mapeamento_altera_versoes_sem_mapeamento(admin):
    v2 = next(m for m in mapeamentos(1, "candidate") if m["form_version"] == 2)
    admin.delete(f"edicts/1/candidates/mappings/versions/2/{v2['id']}")
    assert admin.get("edicts/1/candidates/forms/versions/unmapped").json() == [2]
    admin.post("edicts/1/candidates/mappings/versions/2/", json=ARVORE_V2)
    assert admin.get("edicts/1/candidates/forms/versions/unmapped").json() == []


@pytest.mark.req("V2-MAP-03")
def test_versao_sem_inscricoes_nao_aparece(admin):
    sql("DELETE FROM edict_form_mappings WHERE edict_id=1 AND form_type='candidate'; DELETE FROM submission WHERE id=1")
    assert admin.get("edicts/1/candidates/forms/versions/unmapped").json() == [2]
