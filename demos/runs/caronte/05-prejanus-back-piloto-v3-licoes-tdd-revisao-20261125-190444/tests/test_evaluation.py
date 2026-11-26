import pytest

from tests.conftest import advance_to, find_submission


@pytest.fixture(scope="module")
def submission_em_avaliacao(api_admin):
    edict_id, submission_id = find_submission(api_admin)
    advance_to(api_admin, edict_id, "avaliacao")
    return edict_id, submission_id


def test_comentarios(api, api_outro, api_admin, submission_em_avaliacao):
    _, submission_id = submission_em_avaliacao
    r = api.post(
        f"/submissions/{submission_id}/comments", json={"comment": "Comentário pytest"}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["comment"] == "Comentário pytest"
    assert body["submission_id"] == submission_id
    assert body["user"]["id"] == 2
    assert body["created_at"]
    comment_id = body["id"]

    # histórico
    rg = api.get(f"/submissions/{submission_id}/comments")
    assert rg.status_code == 200, rg.text
    atividade = rg.json()
    assert any(a["id"] == comment_id for a in atividade)

    # outro autor não exclui
    rd = api_outro.delete(f"/submissions/comments/{comment_id}")
    assert rd.status_code == 403, rd.text

    # autor exclui
    rd2 = api.delete(f"/submissions/comments/{comment_id}")
    assert rd2.status_code == 204, rd2.text

    # id inexistente
    assert api.delete("/submissions/comments/99999999").status_code == 404


def test_comentario_fora_da_fase_avaliacao(api_admin, form_id):
    # edital recém-criado está em inscricoes; sem submissão própria, usa 400
    # apenas se houver submissão em edital fora de avaliação
    edicts = api_admin.get("/edicts", params={"is_open": True}).json()
    alvo = None
    for edict in edicts:
        detail = api_admin.get(f"/edicts/{edict['id']}").json()
        if detail["phase"] != "avaliacao":
            subs = api_admin.get(f"/edicts/{edict['id']}/submissions").json()["submissions"]
            if subs:
                alvo = subs[0]["id"]
                break
    if alvo is None:
        pytest.skip("nenhuma submissão em edital fora de avaliação")
    r = api_admin.post(f"/submissions/{alvo}/comments", json={"comment": "x"})
    assert r.status_code == 400, r.text


def test_favoritos(api, api_outro, submission_em_avaliacao):
    _, submission_id = submission_em_avaliacao
    r = api.post(f"/submissions/{submission_id}/favorites")
    assert r.status_code == 201, r.text
    # repetição
    r2 = api.post(f"/submissions/{submission_id}/favorites")
    assert r2.status_code == 409, r2.text

    # reflete no detalhe para o próprio usuário
    detail = api.get(f"/submissions/{submission_id}").json()
    assert detail["summary"]["is_favorite"] is True

    # outro usuário não vê nem perde o próprio estado
    detail_outro = api_outro.get(f"/submissions/{submission_id}").json()
    assert detail_outro["summary"]["is_favorite"] is False

    rd = api.delete(f"/submissions/{submission_id}/favorites")
    assert rd.status_code == 204, rd.text
    rd2 = api.delete(f"/submissions/{submission_id}/favorites")
    assert rd2.status_code == 404, rd2.text


def test_etiquetas(api, api_outro, submission_em_avaliacao):
    _, submission_id = submission_em_avaliacao
    r = api.post(
        f"/submissions/{submission_id}/labels",
        json={"label": "pytest-tag", "color": "#ff0000"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["label"] == "pytest-tag"
    assert body["submission_id"] == submission_id
    label_id = body["id"]

    # catálogo do usuário
    rg = api.get(f"/submissions/{submission_id}/labels")
    assert rg.status_code == 200, rg.text
    catalogo = rg.json()["labels"]
    assert any(l["id"] == label_id and l["color"] == "#ff0000" for l in catalogo)

    # outro autor não exclui
    assert api_outro.delete(f"/submissions/label/{label_id}").status_code == 403
    # autor exclui
    assert api.delete(f"/submissions/label/{label_id}").status_code == 204
    # inexistente
    assert api.delete("/submissions/label/99999999").status_code == 404


def test_notas_privadas(api, api_outro, submission_em_avaliacao):
    _, submission_id = submission_em_avaliacao
    r = api.post(
        f"/submissions/{submission_id}/private_notes", json={"note": "nota inicial"}
    )
    assert r.status_code == 200, r.text
    assert r.json()["note"] == "nota inicial"

    # atualização não cria outra
    r2 = api.post(
        f"/submissions/{submission_id}/private_notes", json={"note": "nota atualizada"}
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["note"] == "nota atualizada"

    detail = api.get(f"/submissions/{submission_id}").json()
    assert detail["summary"]["private_note"] == "nota atualizada"

    # outro usuário não vê a nota do anterior
    detail_outro = api_outro.get(f"/submissions/{submission_id}").json()
    assert detail_outro["summary"]["private_note"] in ("", None)


def test_visualizacoes(api, api_outro, submission_em_avaliacao):
    _, submission_id = submission_em_avaliacao
    r = api.post(f"/submissions/{submission_id}/view")
    assert r.status_code == 200, r.text
    # repetição no mesmo dia não duplica
    api.post(f"/submissions/{submission_id}/view")
    api_outro.post(f"/submissions/{submission_id}/view")

    rg = api.get(f"/submissions/{submission_id}/view")
    assert rg.status_code == 200, rg.text
    views = rg.json()
    assert isinstance(views, list)
    usuarios = [v["user"]["id"] if isinstance(v.get("user"), dict) else v.get("user_id") for v in views]
    assert 2 in usuarios and 3 in usuarios
    do_usuario = [v for v in views if (v["user"]["id"] if isinstance(v.get("user"), dict) else v.get("user_id")) == 2]
    assert len(do_usuario) == 1
