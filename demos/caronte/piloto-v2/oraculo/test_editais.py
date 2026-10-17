import pytest

from conftest import banco, sql

NOVO = {"title": "Piloto v2 - Mestrado 2027", "description": "Criado pelo oráculo", "year": 2027, "semester": 1,
        "edict_type": "mestrado", "is_open": True, "candidate_forms": "1", "recommenders_forms": "2",
        "date_application": "2031-01-10", "date_verification": "2031-02-10",
        "date_evaluation": "2031-03-10", "date_closed": "2031-04-10"}
EDICAO = {"title": "Mestrado editado", "description": "Nova descrição", "year": "2027", "semester": "2",
          "edict_type": "doutorado", "date_application": "2030-01-05", "date_verification": "2030-02-05",
          "date_evaluation": "2030-03-05", "date_closed": "2030-04-05"}


def fases(edict_id):
    return {l["phase"]: l for l in banco(f"SELECT id, phase, closed_date::text AS data FROM edict_phase WHERE edict_id={edict_id}")}


@pytest.mark.req("V2-EDI-01")
def test_lista_editais_com_os_campos_do_contrato(api):
    r = api.get("edicts")
    assert r.status_code == 200
    assert {e["id"]: e for e in r.json()}[2] == {"id": 2, "title": "Piloto v2 - Doutorado", "year": 2026,
                                                 "semester": 2, "edict_type": "doutorado", "is_open": True}


@pytest.mark.req("V2-EDI-01")
def test_lista_por_encerramento_decrescente(admin):
    novo = admin.post("edicts", json=NOVO).json()["id"]
    admin.post("edicts/2/edit-date", json={"closed_date": "2020-01-01"})
    assert [e["id"] for e in admin.get("edicts").json()][0] == novo
    assert [e["id"] for e in admin.get("edicts").json()][-1] == 2


@pytest.mark.req("V2-EDI-01")
@pytest.mark.parametrize("filtros,esperado", [
    ({"type": "doutorado"}, {2}), ({"type": "mestrado"}, {1, 3}), ({"is_open": "true"}, {2, 3}),
    ({"is_open": "false"}, {1}), ({"type": "mestrado", "is_open": "true"}, {3}),
    ({"type": "doutorado", "is_open": "false"}, set()),
])
def test_filtra_por_tipo_e_situacao(admin, filtros, esperado):
    assert admin.patch("edicts/1/close", json={"confirmation_deadline": "2030-05-01",
                                               "send_approval_letter": False}).status_code == 200
    assert {e["id"] for e in admin.get("edicts", params=filtros).json()} == esperado


@pytest.mark.req("V2-EDI-01")
def test_consulta_configuracao_completa(api):
    r = api.get("edicts/2")
    assert r.status_code == 200
    e = r.json()
    assert {k: e[k] for k in ("id", "candidate_form_id", "recommender_form_id", "description", "type", "phase",
                              "year", "semester", "is_open", "slots")} == {
        "id": 2, "candidate_form_id": "3", "recommender_form_id": "2", "description": "Edital doutorado",
        "type": "doutorado", "phase": "avaliacao", "year": 2026, "semester": 2, "is_open": True, "slots": "0"}
    assert {(p["id"], p["phase"]) for p in e["phases"]} == {(5, "inscricoes"), (6, "homologacao"),
                                                            (7, "avaliacao"), (8, "encerrado")}


@pytest.mark.req("V2-EDI-01")
def test_vagas_sao_do_usuario_autenticado(clientes):
    assert clientes("docente").post("edicts/1/slots", json={"amount": "3"}).status_code == 200
    assert clientes("docente").get("edicts/1").json()["slots"] == "3"
    assert clientes("outro").get("edicts/1").json()["slots"] == "0"


@pytest.mark.req("V2-EDI-01")
def test_edital_inexistente_e_recusado(api):
    assert api.get("edicts/999").status_code in (400, 404)


@pytest.mark.req("V2-EDI-02", "V2-BD-01")
@pytest.mark.integracao("INT-PREJANUS-DB")
def test_cria_edital_com_quatro_fases(clientes):
    r = clientes("secretaria").post("edicts", json=NOVO)
    assert r.status_code == 200
    criado = r.json()
    assert {k: criado[k] for k in ("title", "year", "semester", "edict_type", "is_open")} == {
        "title": NOVO["title"], "year": 2027, "semester": 1, "edict_type": "mestrado", "is_open": True}
    assert banco(f"SELECT user_id, phase, candidate_forms, recommenders_forms, closed_date::text AS fim "
                 f"FROM edict WHERE id={criado['id']}") == [
        {"user_id": 4, "phase": "inscricoes", "candidate_forms": "1", "recommenders_forms": "2", "fim": "2031-04-10"}]
    assert {f: v["data"] for f, v in fases(criado["id"]).items()} == {
        "inscricoes": "2031-01-10", "homologacao": "2031-03-10", "avaliacao": "2031-02-10", "encerrado": "2031-04-10"}
    assert criado["id"] in [e["id"] for e in clientes("docente").get("edicts").json()]


@pytest.mark.req("V2-EDI-02")
@pytest.mark.parametrize("rota", ["edicts", "edicts/1/edit"])
def test_datas_fora_de_ordem_sao_recusadas(admin, rota):
    corpo = dict(NOVO if rota == "edicts" else EDICAO, date_verification="2029-01-01")
    antes = banco("SELECT count(*) AS n, max(title) AS t FROM edict"), fases(1)
    assert admin.post(rota, json=corpo).status_code >= 400
    assert (banco("SELECT count(*) AS n, max(title) AS t FROM edict"), fases(1)) == antes


@pytest.mark.req("V2-EDI-02")
def test_edicao_completa_altera_dados_e_datas(admin):
    r = admin.post("edicts/1/edit", json=EDICAO)
    assert r.status_code == 200
    e = admin.get("edicts/1").json()
    assert (e["title"], e["description"], e["year"], e["semester"], e["type"], e["closed_date"]) == (
        "Mestrado editado", "Nova descrição", 2027, 2, "doutorado", "2030-04-05")
    assert {f: v["data"] for f, v in fases(1).items()} == {
        "inscricoes": "2030-01-05", "homologacao": "2030-03-05", "avaliacao": "2030-02-05", "encerrado": "2030-04-05"}


@pytest.mark.req("V2-EDI-02")
def test_edicao_da_data_de_encerramento(admin):
    r = admin.post("edicts/2/edit-date", json={"closed_date": "2031-07-01"})
    assert (r.status_code, r.json()) == (200, {"closed_date": "2031-07-01"})
    assert admin.get("edicts/2").json()["closed_date"] == "2031-07-01"


@pytest.mark.req("V2-EDI-03")
@pytest.mark.integracao("INT-FORMS-DB")
@pytest.mark.parametrize("fase,forms", [("inscricoes", "Registration"), ("homologacao", "Approval"),
                                        ("avaliacao", "Completed"), ("encerrado", "Completed")])
def test_mudanca_de_fase_propaga_ao_forms(admin, fase, forms):
    sql("UPDATE form SET phase='Registration' WHERE id=3", "forms")
    sql("UPDATE edict SET phase='inscricoes' WHERE id=2")
    fase_id = fases(2)[fase]["id"]
    r = admin.post("edicts/2/advance-phase", json={"id": fase_id})
    assert (r.status_code, r.json()) == (200, {"id": fase_id, "label": fase})
    assert admin.get("edicts/2").json()["phase"] == fase
    assert banco("SELECT phase::text FROM form WHERE id=3", "forms") == [{"phase": forms}]
    assert banco("SELECT phase::text FROM form WHERE id=1", "forms") == [{"phase": "Registration"}]


@pytest.mark.req("V2-EDI-04")
def test_encerra_uma_unica_vez(admin):
    corpo = {"confirmation_deadline": "2030-05-01", "send_approval_letter": True}
    assert admin.patch("edicts/2/close", json=corpo).status_code == 200
    assert admin.get("edicts/2").json()["is_open"] is False
    assert admin.patch("edicts/2/close", json=corpo).status_code == 409


@pytest.mark.req("V2-EDI-04", "V2-BD-01")
@pytest.mark.integracao("INT-PREJANUS-DB", "INT-FORMS-DB")
def test_remove_edital_e_dependentes_preservando_o_forms(admin):
    admin.post("submissions/3/comments", json={"comment": "Some com o edital"})
    admin.post("submissions/3/favorites")
    admin.post("edicts/2/slots", json={"amount": "2"})
    forms_antes = banco("SELECT count(*) AS n FROM form_response", "forms")
    assert admin.delete("edicts/2/remove").status_code == 200
    assert admin.get("edicts/2").status_code in (400, 404)
    assert 2 not in [e["id"] for e in admin.get("edicts").json()]
    for tabela, coluna in (("edict_phase", "edict_id"), ("submission", "edict_id"),
                           ("edict_form_mappings", "edict_id"), ("user_edict_slots", "edict_id")):
        assert banco(f"SELECT 1 FROM {tabela} WHERE {coluna}=2") == [], tabela
    assert banco("SELECT 1 FROM comment WHERE submission_id=3") == []
    assert banco("SELECT 1 FROM favorites WHERE submission_id=3") == []
    assert banco("SELECT count(*) AS n FROM form_response", "forms") == forms_antes
    assert admin.get("edicts/1/submissions").status_code == 200
