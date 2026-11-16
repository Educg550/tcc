def test_listar_submissoes_do_edital(api, edital_com_submissao):
    edict, _ = edital_com_submissao
    resp = api.get(f"/edicts/{edict['id']}/submissions")
    assert resp.status_code == 200, resp.text
    submissions = resp.json()["submissions"]
    assert submissions
    for s in submissions:
        for field in (
            "id", "name", "email", "stats", "is_favorite",
            "bidding_users", "labels", "accept",
        ):
            assert field in s


def test_detalhes_da_submissao(api, edital_com_submissao):
    _, submission = edital_com_submissao
    resp = api.get(f"/submissions/{submission['id']}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == submission["id"]


def test_comentarios_da_submissao(api, edital_com_submissao):
    _, submission = edital_com_submissao
    texto = "Comentário de teste"
    resp = api.post(
        f"/submissions/{submission['id']}/comments", json={"comment": texto}
    )
    assert resp.status_code == 200, resp.text
    comment = resp.json()
    assert comment["comment"] == texto
    assert comment["submission_id"] == submission["id"]

    lista = api.get(f"/submissions/{submission['id']}/comments").json()
    assert any(c["id"] == comment["id"] for c in lista)

    assert api.delete(f"/submissions/comments/{comment['id']}").status_code == 200
    lista = api.get(f"/submissions/{submission['id']}/comments").json()
    assert not any(c["id"] == comment["id"] for c in lista)


def test_rotulo_da_submissao(api, edital_com_submissao):
    _, submission = edital_com_submissao
    resp = api.post(
        f"/submissions/{submission['id']}/labels",
        json={"label": "destaque", "color": "#ff0000"},
    )
    assert resp.status_code == 200, resp.text
    label = resp.json()
    assert label["label"] == "destaque"
    assert label["color"] == "#ff0000"

    do_usuario = api.get(f"/submissions/{submission['id']}/labels").json()
    assert any(l["id"] == label["id"] for l in do_usuario["labels"])

    assert api.delete(f"/submissions/label/{label['id']}").status_code == 200
    do_usuario = api.get(f"/submissions/{submission['id']}/labels").json()
    assert not any(l["id"] == label["id"] for l in do_usuario["labels"])


def test_nota_privada_por_usuario(api, edital_com_submissao):
    _, submission = edital_com_submissao
    resp = api.post(
        f"/submissions/{submission['id']}/private_notes",
        json={"note": "nota privada"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["note"] == "nota privada"

    # Atualização sobrescreve a nota do mesmo usuário.
    resp = api.post(
        f"/submissions/{submission['id']}/private_notes",
        json={"note": "nota revisada"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["note"] == "nota revisada"


def test_favorito_da_submissao(api, edital_com_submissao):
    edict, submission = edital_com_submissao
    resp = api.post(f"/submissions/{submission['id']}/favorites")
    assert resp.status_code == 200, resp.text

    lista = api.get(
        f"/edicts/{edict['id']}/submissions", params={"only_favorites": True}
    ).json()["submissions"]
    assert any(s["id"] == submission["id"] for s in lista)

    assert api.delete(f"/submissions/{submission['id']}/favorites").status_code == 200
    lista = api.get(
        f"/edicts/{edict['id']}/submissions", params={"only_favorites": True}
    ).json()["submissions"]
    assert not any(s["id"] == submission["id"] for s in lista)


def test_status_da_submissao(api, edital_com_submissao):
    _, submission = edital_com_submissao
    resp = api.post(
        f"/submissions/{submission['id']}/select",
        json={"user_ids": [], "stats": "underreview"},
    )
    assert resp.status_code == 200, resp.text
    detalhe = api.get(f"/submissions/{submission['id']}").json()
    assert detalhe["stats"] == "underreview"


def test_bidding_da_submissao(api, edital_com_submissao):
    _, submission = edital_com_submissao
    resp = api.post(
        f"/submissions/{submission['id']}/bidding", json={"bidding": "interested"}
    )
    assert resp.status_code == 200, resp.text
    detalhe = api.get(f"/submissions/{submission['id']}").json()
    assert "2" in detalhe["bidding_users"]["data"]


def test_semestre_de_entrada_da_submissao(api, edital_com_submissao):
    _, submission = edital_com_submissao
    resp = api.post(
        f"/submissions/{submission['id']}/entry-semester",
        json={"semester": "2026S1"},
    )
    assert resp.status_code == 200, resp.text


def test_registro_e_consulta_de_visualizacao(api, edital_com_submissao):
    _, submission = edital_com_submissao
    assert api.post(f"/submissions/{submission['id']}/view").status_code == 200
    resp = api.get(f"/submissions/{submission['id']}/view")
    assert resp.status_code == 200, resp.text
    assert resp.json()
