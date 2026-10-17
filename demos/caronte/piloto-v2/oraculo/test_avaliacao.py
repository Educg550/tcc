from datetime import datetime, timedelta, timezone

import pytest

from conftest import banco, sql


def fora_da_avaliacao(fase="homologacao"):
    sql(f"UPDATE edict SET phase='{fase}' WHERE id=1")


def atividade(c, submission_id=1):
    r = c.get(f"submissions/{submission_id}/comments")
    assert r.status_code == 200
    return r.json()


@pytest.mark.req("V2-AVA-01", "V2-BD-01")
@pytest.mark.integracao("INT-PREJANUS-DB")
def test_cria_comentario_com_autor_e_data(api):
    antes = datetime.now(timezone.utc) - timedelta(minutes=1)
    r = api.post("submissions/1/comments", json={"comment": "Bom histórico"})
    assert r.status_code == 200
    c = r.json()
    assert (c["user"]["id"], c["submission_id"], c["comment"]) == (2, 1, "Bom histórico")
    assert datetime.fromisoformat(c["created_at"]) >= antes
    assert banco(f"SELECT user_id, submission_id, comment FROM comment WHERE id={c['id']}") == [
        {"user_id": 2, "submission_id": 1, "comment": "Bom histórico"}]


@pytest.mark.req("V2-AVA-01")
def test_comentario_respeita_data_informada(api):
    r = api.post("submissions/1/comments", json={"comment": "Retroativo", "created_at": "2026-09-01T10:00:00+00:00"})
    assert datetime.fromisoformat(r.json()["created_at"]) == datetime(2026, 9, 1, 10, tzinfo=timezone.utc)


@pytest.mark.req("V2-AVA-01")
@pytest.mark.parametrize("fase", ["inscricoes", "homologacao", "encerrado"])
def test_comentario_fora_da_avaliacao_responde_400(api, fase):
    fora_da_avaliacao(fase)
    assert api.post("submissions/1/comments", json={"comment": "Fora"}).status_code == 400
    assert banco("SELECT id FROM comment") == []


@pytest.mark.req("V2-AVA-01")
@pytest.mark.integracao("INT-FORMS-DB")
def test_atividade_reune_comentarios_candidatura_e_recomendacoes(clientes):
    clientes("docente").get("edicts/1/submissions")
    clientes("docente").post("submissions/1/comments", json={"comment": "Primeiro", "created_at": "2026-10-18T10:00:00+00:00"})
    clientes("outro").post("submissions/1/comments", json={"comment": "Segundo", "created_at": "2026-10-19T10:00:00+00:00"})
    eventos = atividade(clientes("docente"))
    comentarios = [(e["user"]["name"], e["comment"]) for e in eventos if e["type"] == "comment"]
    assert comentarios == [("Docente Piloto", "Primeiro"), ("Outra Docente", "Segundo")]
    autores = {e["user"]["name"] for e in eventos if e["type"] != "comment"}
    assert {"Ana Piloto Caronte", "Paula Recomendadora Um", "Pedro Recomendador Dois"} <= autores
    datas = [datetime.fromisoformat(e["created_at"]).replace(tzinfo=None) for e in eventos]
    assert datas == sorted(datas)


@pytest.mark.req("V2-AVA-01")
def test_ler_a_atividade_nao_cria_eventos(api):
    api.post("submissions/1/comments", json={"comment": "Único"})
    assert atividade(api) == atividade(api)
    assert len(banco("SELECT id FROM comment")) == 1


@pytest.mark.req("V2-AVA-01")
def test_exclui_somente_o_proprio_comentario(clientes):
    id = clientes("docente").post("submissions/1/comments", json={"comment": "Meu"}).json()["id"]
    assert clientes("admin").delete(f"submissions/comments/{id}").status_code == 403
    assert clientes("docente").delete(f"submissions/comments/{id}").status_code == 204
    assert clientes("docente").delete(f"submissions/comments/{id}").status_code == 404
    assert "Meu" not in [e["comment"] for e in atividade(clientes("docente"))]


@pytest.mark.req("V2-AVA-02", "V2-BD-01")
@pytest.mark.integracao("INT-PREJANUS-DB")
def test_favorito_por_usuario(clientes):
    assert clientes("docente").post("submissions/1/favorites").status_code == 201
    assert clientes("docente").post("submissions/1/favorites").status_code == 409
    assert clientes("docente").get("submissions/1").json()["summary"]["is_favorite"] is True
    assert clientes("outro").get("submissions/1").json()["summary"]["is_favorite"] is False
    assert clientes("outro").delete("submissions/1/favorites").status_code == 404
    assert banco("SELECT user_id FROM favorites WHERE submission_id=1") == [{"user_id": 2}]
    assert clientes("docente").delete("submissions/1/favorites").status_code == 204
    assert banco("SELECT user_id FROM favorites") == []


@pytest.mark.req("V2-AVA-02")
def test_favorito_fora_da_avaliacao_responde_400(api):
    fora_da_avaliacao()
    assert api.post("submissions/1/favorites").status_code == 400


@pytest.mark.req("V2-AVA-03", "V2-BD-01")
@pytest.mark.integracao("INT-PREJANUS-DB")
def test_etiqueta_com_autor_e_contexto_de_candidato(api):
    r = api.post("submissions/1/labels", json={"label": "forte", "color": "#00ff00"})
    assert r.status_code == 200
    e = r.json()
    assert (e["user"]["id"], e["submission_id"], e["label"]) == (2, 1, "forte")
    assert banco(f"SELECT color, context_type FROM labels WHERE id={e['id']}") == [
        {"color": "#00ff00", "context_type": "candidate"}]
    assert [(l["label"], l["color"]) for l in api.get("submissions/1").json()["summary"]["labels"]] == [("forte", "#00ff00")]


@pytest.mark.req("V2-AVA-03")
def test_cor_propaga_ao_mesmo_rotulo_do_mesmo_autor(clientes):
    docente, outro = clientes("docente"), clientes("outro")
    docente.post("submissions/1/labels", json={"label": "forte", "color": "#111111"})
    outro.post("submissions/1/labels", json={"label": "forte", "color": "#222222"})
    docente.post("submissions/2/bidding", json={"bidding": "interested"})
    docente.post("submissions/2/labels", json={"label": "forte", "color": "#333333"})
    assert banco("SELECT user_id, submission_id, color FROM labels WHERE context_type='candidate' ORDER BY id") == [
        {"user_id": 2, "submission_id": 1, "color": "#333333"},
        {"user_id": 3, "submission_id": 1, "color": "#222222"},
        {"user_id": 2, "submission_id": 2, "color": "#333333"}]
    assert banco("SELECT label FROM labels WHERE context_type='bidding'") == [{"label": "interested"}]


@pytest.mark.req("V2-AVA-03")
def test_catalogo_de_etiquetas_do_usuario(clientes):
    clientes("docente").post("submissions/1/labels", json={"label": "forte", "color": "#111111"})
    clientes("docente").post("submissions/2/labels", json={"label": "forte", "color": "#111111"})
    clientes("docente").post("submissions/2/labels", json={"label": "rever", "color": "#999999"})
    clientes("outro").post("submissions/1/labels", json={"label": "alheia", "color": "#000000"})
    r = clientes("docente").get("submissions/4/labels")
    assert r.status_code == 200
    assert sorted((l["label"], l["color"]) for l in r.json()["labels"]) == [("forte", "#111111"), ("rever", "#999999")]
    assert [l["label"] for l in clientes("docente").get("submissions/1").json()["summary"]["labels"]] == ["forte"]


@pytest.mark.req("V2-AVA-03")
def test_exclui_somente_a_propria_etiqueta(clientes):
    id = clientes("docente").post("submissions/1/labels", json={"label": "minha", "color": "#123456"}).json()["id"]
    assert clientes("admin").delete(f"submissions/label/{id}").status_code == 403
    assert clientes("docente").delete(f"submissions/label/{id}").status_code == 204
    assert clientes("docente").delete(f"submissions/label/{id}").status_code == 404


@pytest.mark.req("V2-AVA-03")
def test_etiqueta_fora_da_avaliacao_responde_400(api):
    fora_da_avaliacao()
    assert api.post("submissions/1/labels", json={"label": "x", "color": "#000000"}).status_code == 400


@pytest.mark.req("V2-AVA-04", "V2-BD-01")
@pytest.mark.integracao("INT-PREJANUS-DB")
def test_nota_privada_cria_e_atualiza_uma_unica_nota(api):
    assert api.post("submissions/1/private_notes", json={"note": "Primeira"}).json()["note"] == "Primeira"
    assert api.post("submissions/1/private_notes", json={"note": "Revisada"}).json()["note"] == "Revisada"
    assert banco("SELECT user_id, note FROM private_note") == [{"user_id": 2, "note": "Revisada"}]
    assert api.get("submissions/1").json()["summary"]["private_note"] == "Revisada"


@pytest.mark.req("V2-AVA-04")
def test_nota_privada_nao_aparece_para_outro_usuario(clientes):
    clientes("docente").post("submissions/1/private_notes", json={"note": "Segredo da docente"})
    assert clientes("outro").get("submissions/1").json()["summary"]["private_note"] == ""
    assert clientes("admin").get("submissions/1").json()["summary"]["private_note"] == ""


@pytest.mark.req("V2-AVA-04")
def test_nota_fora_da_avaliacao_responde_400(api):
    fora_da_avaliacao()
    assert api.post("submissions/1/private_notes", json={"note": "x"}).status_code == 400


@pytest.mark.req("V2-AVA-05", "V2-BD-01")
@pytest.mark.integracao("INT-PREJANUS-DB")
def test_visualizacao_uma_por_usuario_e_dia(clientes):
    for _ in range(3):
        assert clientes("docente").post("submissions/1/view").status_code == 200
    clientes("outro").post("submissions/1/view")
    vistas = clientes("docente").get("submissions/1/view").json()
    assert sorted(v["user"]["id"] for v in vistas) == [2, 3]
    assert all("created_at" in v for v in vistas)


@pytest.mark.req("V2-AVA-05")
def test_visualizacao_de_outro_dia_cria_nova_linha(api):
    sql("INSERT INTO submission_view(user_id, submission_id, created_at, updated_at) "
        "VALUES (2, 1, now() - interval '2 days', now() - interval '2 days')")
    api.post("submissions/1/view")
    assert len(api.get("submissions/1/view").json()) == 2


@pytest.mark.req("V2-AVA-05")
def test_dia_e_o_de_sao_paulo(api):
    # 23h de ontem em São Paulo já é hoje em UTC.
    sql("INSERT INTO submission_view(user_id, submission_id, created_at, updated_at) "
        "VALUES (2, 1, date_trunc('day', now() AT TIME ZONE 'America/Sao_Paulo') AT TIME ZONE 'America/Sao_Paulo' "
        "- interval '1 hour', now())")
    api.post("submissions/1/view")
    assert len(api.get("submissions/1/view").json()) == 2
