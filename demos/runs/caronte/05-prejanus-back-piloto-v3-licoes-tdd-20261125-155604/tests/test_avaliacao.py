import pytest

from tests.conftest import first_submission, advance_phase


@pytest.fixture(scope="module")
def cenário(admin, api):
    edicts = api.get("/edicts").json()
    for e in edicts:
        r = api.get(f"/edicts/{e['id']}/submissions")
        if r.status_code == 200 and r.json()["submissions"]:
            edict_id = e["id"]
            break
    else:
        pytest.skip("nenhum edital com inscrições")
    detail = admin.get(f"/edicts/{edict_id}").json()
    if detail["phase"] != "avaliacao":
        advance_phase(admin, edict_id, "avaliacao")
    sub = first_submission(api, edict_id)
    return {"edict_id": edict_id, "sub": sub}


def test_comentario_criar_e_listar(api, cenário):
    sid = cenário["sub"]["id"]
    r = api.post(f"/submissions/{sid}/comments", json={"comment": "Comentário de teste"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["comment"] == "Comentário de teste"
    assert data["user"]["id"] == 2
    assert data["submission_id"] == sid
    assert data["created_at"]

    lst = api.get(f"/submissions/{sid}/comments").json()
    assert any(c.get("comment") == "Comentário de teste" for c in lst)
    # ler não registra evento novo
    lst2 = api.get(f"/submissions/{sid}/comments").json()
    assert len(lst2) == len(lst)


def test_comentario_fase_errada_400(admin, api):
    # cria edital novo (fase inscricoes) sem inscrições: usa inscrição existente em outro contexto
    # usa uma inscrição de edital em fase diferente, se houver
    edicts = api.get("/edicts").json()
    for e in edicts:
        detail = api.get(f"/edicts/{e['id']}").json()
        if detail["phase"] != "avaliacao":
            r = api.get(f"/edicts/{e['id']}/submissions")
            if r.status_code == 200 and r.json()["submissions"]:
                sid = r.json()["submissions"][0]["id"]
                rr = admin.post(
                    f"/submissions/{sid}/comments", json={"comment": "fora de fase"}
                )
                assert rr.status_code == 400
                return
    pytest.skip("sem edital fora da fase avaliação com inscrições")


def test_comentario_autoria(api, outro, admin, cenário):
    sid = cenário["sub"]["id"]
    r = api.post(f"/submissions/{sid}/comments", json={"comment": "comentário do docente"})
    cid = r.json()["id"]
    # outro usuário não pode excluir
    assert outro.delete(f"/submissions/comments/{cid}").status_code == 403
    assert admin.delete(f"/submissions/comments/{cid}").status_code == 403
    # autor exclui com 204
    assert api.delete(f"/submissions/comments/{cid}").status_code == 204
    # id inexistente
    assert api.delete(f"/submissions/comments/{cid}").status_code == 404


def test_favoritos(api, outro, cenário):
    sid = cenário["sub"]["id"]
    r = api.post(f"/submissions/{sid}/favorites")
    assert r.status_code == 201
    # repetição: 409
    assert api.post(f"/submissions/{sid}/favorites").status_code == 409
    # reflete no detalhe do próprio usuário
    detail = api.get(f"/submissions/{sid}").json()
    assert detail["summary"]["is_favorite"] is True
    # outro usuário não vê o favorito
    detail_outro = outro.get(f"/submissions/{sid}").json()
    assert detail_outro["summary"]["is_favorite"] is False
    # remoção
    assert api.delete(f"/submissions/{sid}/favorites").status_code == 204
    assert api.delete(f"/submissions/{sid}/favorites").status_code == 404


def test_etiquetas(api, outro, cenário):
    sid = cenário["sub"]["id"]
    r = api.post(
        f"/submissions/{sid}/labels", json={"label": "destaque", "color": "#ff0000"}
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["label"] == "destaque"
    assert data["submission_id"] == sid

    # catálogo do usuário
    cat = api.get(f"/submissions/{sid}/labels").json()
    assert any(l["label"] == "destaque" for l in cat["labels"])
    label_id = next(l["id"] for l in cat["labels"] if l["label"] == "destaque")

    # outro autor não exclui
    assert outro.delete(f"/submissions/label/{label_id}").status_code == 403
    # autor exclui
    assert api.delete(f"/submissions/label/{label_id}").status_code == 204
    assert api.delete(f"/submissions/label/{label_id}").status_code == 404


def test_nota_privada(api, outro, cenário):
    sid = cenário["sub"]["id"]
    r = api.post(f"/submissions/{sid}/private_notes", json={"note": "nota secreta"})
    assert r.status_code == 200
    assert r.json()["note"] == "nota secreta"
    # atualização não duplica
    r2 = api.post(f"/submissions/{sid}/private_notes", json={"note": "nota revisada"})
    assert r2.json()["note"] == "nota revisada"
    detail = api.get(f"/submissions/{sid}").json()
    assert detail["summary"]["private_note"] == "nota revisada"
    # outro usuário não vê a nota
    detail_outro = outro.get(f"/submissions/{sid}").json()
    assert detail_outro["summary"]["private_note"] in ("", None)


def test_visualizacoes(api, outro, cenário):
    sid = cenário["sub"]["id"]
    assert api.post(f"/submissions/{sid}/view").status_code == 200
    # repetição no mesmo dia não cria outra linha
    api.post(f"/submissions/{sid}/view")
    outro.post(f"/submissions/{sid}/view")
    views = api.get(f"/submissions/{sid}/view").json()
    users = [v["user"]["id"] if isinstance(v.get("user"), dict) else v.get("user_id") for v in views]
    assert 2 in users and 3 in users
    assert users.count(2) == 1
