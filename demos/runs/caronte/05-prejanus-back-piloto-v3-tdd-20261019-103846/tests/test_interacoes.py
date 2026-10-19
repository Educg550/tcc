"""V2-AVA-01 a V2-AVA-05 e V2-SEL-01: interações do docente com inscrições."""
import uuid


def _edict_phase(api, edict_id):
    return api.get(f"/edicts/{edict_id}").json()["phase"]


def test_comentarios_fora_da_fase_avaliacao_400(api, edict_with_submissions):
    edict_id = edict_with_submissions["id"]
    if _edict_phase(api, edict_id) == "avaliacao":
        pytest.skip("edital em fase de avaliação")
    subs = api.get(f"/edicts/{edict_id}/submissions").json()["submissions"]
    resp = api.post(f"/submissions/{subs[0]['id']}/comments",
                    json={"comment": "comentário de teste"})
    assert resp.status_code == 400


def test_comentarios_leitura_nao_registra_evento(api, any_submission):
    before = api.get(f"/submissions/{any_submission['id']}/comments").json()
    api.get(f"/submissions/{any_submission['id']}/comments")
    after = api.get(f"/submissions/{any_submission['id']}/comments").json()
    assert before == after


def test_favorito_ciclo_do_proprio_usuario(api, any_submission):
    sid = any_submission["id"]
    api.delete(f"/submissions/{sid}/favorites")
    resp = api.post(f"/submissions/{sid}/favorites")
    assert resp.status_code == 201
    # repetição
    assert api.post(f"/submissions/{sid}/favorites").status_code == 409
    detail = api.get(f"/submissions/{sid}").json()
    assert detail["summary"]["is_favorite"] is True
    # remoção
    assert api.delete(f"/submissions/{sid}/favorites").status_code == 204
    assert api.delete(f"/submissions/{sid}/favorites").status_code == 404
    detail = api.get(f"/submissions/{sid}").json()
    assert detail["summary"]["is_favorite"] is False


def test_etiquetas_ciclo(api, any_submission):
    sid = any_submission["id"]
    label = f"etiqueta-{uuid.uuid4().hex[:8]}"
    resp = api.post(f"/submissions/{sid}/labels",
                   json={"label": label, "color": "#ff0000"})
    assert resp.status_code == 200
    created = resp.json()
    for key in ("id", "user", "submission_id", "label"):
        assert key in created
    label_id = created["id"]

    catalog = api.get(f"/submissions/{sid}/labels").json()
    assert "labels" in catalog
    mine = [l for l in catalog["labels"] if l["id"] == label_id]
    assert mine and mine[0]["label"] == label and mine[0]["color"] == "#ff0000"

    detail = api.get(f"/submissions/{sid}").json()
    assert any(l["id"] == label_id for l in detail["summary"]["labels"])

    # exclusão por outro autor é 403; pelo próprio autor, 204
    assert api.delete(f"/submissions/label/{label_id}").status_code == 204
    assert api.delete(f"/submissions/label/{label_id}").status_code == 404
    assert api.delete("/submissions/label/99999999").status_code == 404


def test_nota_privada_atualiza_sem_duplicar(api, any_submission):
    sid = any_submission["id"]
    resp = api.post(f"/submissions/{sid}/private_notes",
                   json={"note": "primeira nota"})
    assert resp.status_code == 200
    assert resp.json()["note"] == "primeira nota"
    resp = api.post(f"/submissions/{sid}/private_notes",
                    json={"note": "nota revisada"})
    assert resp.status_code == 200
    assert resp.json()["note"] == "nota revisada"
    detail = api.get(f"/submissions/{sid}").json()
    summary = detail["summary"]
    note = summary.get("private_note", summary.get("note"))
    assert note == "nota revisada"


def test_visualizacoes_por_usuario_e_dia(api, any_submission):
    sid = any_submission["id"]
    assert api.post(f"/submissions/{sid}/view").status_code == 200
    before = api.get(f"/submissions/{sid}/view").json()
    assert isinstance(before, list) and before
    api.post(f"/submissions/{sid}/view")
    after = api.get(f"/submissions/{sid}/view").json()
    assert len(after) == len(before), "visualização repetida no mesmo dia criou outra linha"


def test_vagas_do_proprio_usuario(api, any_edict):
    edict_id = any_edict["id"]
    resp = api.post(f"/edicts/{edict_id}/slots", json={"amount": "3"})
    assert resp.status_code == 200
    assert resp.json()["amount"] == "3"
    # valor vazio vira "0"
    resp = api.post(f"/edicts/{edict_id}/slots", json={"amount": ""})
    assert resp.status_code == 200
    assert resp.json()["amount"] == "0"
    # negativo vira "0"
    resp = api.post(f"/edicts/{edict_id}/slots", json={"amount": "-2"})
    assert resp.status_code == 200
    assert resp.json()["amount"] == "0"
    # texto inválido é rejeitado
    assert api.post(f"/edicts/{edict_id}/slots",
                    json={"amount": "abc"}).status_code == 422
    # refletido na consulta do edital
    data = api.get(f"/edicts/{edict_id}").json()
    assert data["slots"] == "0"


def test_manifestacao_de_interesse(api, any_submission):
    sid = any_submission["id"]
    resp = api.post(f"/submissions/{sid}/bidding", json={"bidding": "interested"})
    assert resp.status_code == 200
    detail = api.get(f"/submissions/{sid}").json()
    assert "interested" in str(detail["summary"])
    # valor vazio limpa o interesse
    resp = api.post(f"/submissions/{sid}/bidding", json={"bidding": ""})
    assert resp.status_code == 200


def test_selecao_restrita_a_administradores(api, any_submission):
    resp = api.post(f"/submissions/{any_submission['id']}/select",
                    json={"stats": "approved", "user_ids": None})
    assert resp.status_code == 403


def test_solicitacao_correcao_restrita(api, any_submission):
    resp = api.post(f"/submissions/{any_submission['id']}/reesend_submission",
                    json={"text": "corrija por favor"})
    assert resp.status_code == 403
