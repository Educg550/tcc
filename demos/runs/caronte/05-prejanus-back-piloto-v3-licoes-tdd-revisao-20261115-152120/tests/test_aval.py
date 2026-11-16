import pytest

from helpers import advance, create_edict, submissions_of


@pytest.fixture(scope="module")
def aval(admin):
    eid = create_edict(admin, "Edital avaliação")
    advance(admin, eid, "avaliacao")
    subs = submissions_of(admin, eid)
    assert len(subs) >= 2, "edital de avaliação precisa de ao menos duas inscrições"
    return {"id": eid, "subs": subs}


@pytest.fixture(scope="module")
def insc(admin):
    eid = create_edict(admin, "Edital fase inscrição")
    subs = submissions_of(admin, eid)
    return {"id": eid, "subs": subs}


def _comments(cl, sid):
    r = cl.get(f"/submissions/{sid}/comments")
    assert r.status_code == 200, r.text
    data = r.json()
    return data if isinstance(data, list) else data.get("comments", data.get("activity", []))


def test_comentario_criacao_e_consulta(api, aval):
    sid = aval["subs"][0]["id"]
    r = api.post(f"/submissions/{sid}/comments", json={"comment": "bom candidato"})
    assert r.status_code == 200, r.text
    c = r.json()
    assert c["comment"] == "bom candidato"
    assert c["submission_id"] == sid
    assert c["user"]["id"] == 2
    assert c["id"]
    assert any(
        x.get("comment", x.get("text")) == "bom candidato" for x in _comments(api, sid)
    )
    # leitura não registra novo evento
    n = len(_comments(api, sid))
    _comments(api, sid)
    assert len(_comments(api, sid)) == n


def test_comentario_fase_errada_400(admin, insc):
    sid = insc["subs"][0]["id"]
    r = admin.post(f"/submissions/{sid}/comments", json={"comment": "fora de fase"})
    assert r.status_code == 400, r.text


def test_comentario_exclusao_por_autor(api, admin, outro, aval):
    sid = aval["subs"][0]["id"]
    r = api.post(f"/submissions/{sid}/comments", json={"comment": "para excluir"})
    cid = r.json()["id"]
    # outro usuário, mesmo administrador, não exclui
    assert outro.delete(f"/submissions/comments/{cid}").status_code == 403
    assert admin.delete(f"/submissions/comments/{cid}").status_code == 403
    # autor exclui
    assert api.delete(f"/submissions/comments/{cid}").status_code == 204
    assert api.delete(f"/submissions/comments/{cid}").status_code == 404
    assert api.delete("/submissions/comments/99999999").status_code == 404


def _favorite(d):
    summ = d["summary"]
    return summ.get("favorite", summ.get("is_favorite"))


def test_favoritos(api, outro, aval):
    sid = aval["subs"][0]["id"]
    assert api.post(f"/submissions/{sid}/favorites").status_code == 201
    assert api.post(f"/submissions/{sid}/favorites").status_code == 409
    assert _favorite(api.get(f"/submissions/{sid}").json()) is True
    # não altera favoritos de outro usuário
    assert _favorite(outro.get(f"/submissions/{sid}").json()) is False
    assert api.delete(f"/submissions/{sid}/favorites").status_code == 204
    assert api.delete(f"/submissions/{sid}/favorites").status_code == 404
    assert _favorite(api.get(f"/submissions/{sid}").json()) is False


def _labels(cl, sid):
    r = cl.get(f"/submissions/{sid}/labels")
    assert r.status_code == 200, r.text
    data = r.json()
    return data["labels"] if isinstance(data, dict) else data


def test_etiquetas(api, outro, aval):
    sid, sid2 = aval["subs"][0]["id"], aval["subs"][1]["id"]
    r = api.post(
        f"/submissions/{sid}/labels", json={"label": "destaque", "color": "#ff0000"}
    )
    assert r.status_code == 200, r.text
    lab = r.json()
    assert lab["label"] == "destaque"
    assert lab["submission_id"] == sid

    labels = _labels(api, sid)
    assert any(
        l["label"] == "destaque" and l["color"] == "#ff0000" for l in labels
    ), labels

    # mesma etiqueta em outra inscrição atualiza a cor do mesmo autor
    api.post(
        f"/submissions/{sid2}/labels", json={"label": "destaque", "color": "#00ff00"}
    )
    labels = _labels(api, sid)
    destaque = [l for l in labels if l["label"] == "destaque"]
    assert destaque and all(l["color"] == "#00ff00" for l in destaque), labels

    # catálogo é por usuário
    assert not any(l["label"] == "destaque" for l in _labels(outro, sid))

    # exclusão só pelo autor
    lid = destaque[0]["id"]
    assert outro.delete(f"/submissions/label/{lid}").status_code == 403
    assert api.delete(f"/submissions/label/{lid}").status_code == 204
    assert api.delete(f"/submissions/label/{lid}").status_code == 404
    assert api.delete("/submissions/label/99999999").status_code == 404


def _note(d):
    return d["summary"].get("private_note", "")


def test_notas_privadas(api, outro, aval):
    sid = aval["subs"][0]["id"]
    r = api.post(f"/submissions/{sid}/private_notes", json={"note": "nota um"})
    assert r.status_code == 200, r.text
    assert r.json()["note"] == "nota um"
    # atualização não cria outra nota
    r2 = api.post(f"/submissions/{sid}/private_notes", json={"note": "nota dois"})
    assert r2.status_code == 200, r2.text
    assert r2.json()["note"] == "nota dois"
    assert _note(api.get(f"/submissions/{sid}").json()) == "nota dois"
    # outro usuário não vê a nota
    assert _note(outro.get(f"/submissions/{sid}").json()) == ""


def _views(cl, sid):
    r = cl.get(f"/submissions/{sid}/view")
    assert r.status_code == 200, r.text
    data = r.json()
    return data if isinstance(data, list) else data.get("views", [])


def _view_user(v):
    if isinstance(v.get("user"), dict):
        return v["user"].get("id")
    return v.get("user_id")


def test_visualizacoes(api, outro, aval):
    sid = aval["subs"][0]["id"]
    assert api.post(f"/submissions/{sid}/view").status_code == 200
    views = _views(api, sid)
    mine = [v for v in views if _view_user(v) == 2]
    assert len(mine) == 1
    # repetição no mesmo dia não cria outra linha
    api.post(f"/submissions/{sid}/view")
    views = _views(api, sid)
    assert len([v for v in views if _view_user(v) == 2]) == 1
    # outro usuário cria a sua
    outro.post(f"/submissions/{sid}/view")
    views = _views(api, sid)
    assert any(_view_user(v) == 3 for v in views)
