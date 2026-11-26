import pytest

from conftest import advance, first_edict_with_submissions


@pytest.fixture(scope="module")
def avaliacao(request):
    """Edital com inscrições colocado na fase de avaliação."""
    import httpx
    import os

    url = os.environ.get("CARONTE_API_ADMIN")
    if not url:
        pytest.skip("CARONTE_API_ADMIN não definido")
    with httpx.Client(base_url=url.rstrip("/"), timeout=60) as admin:
        edict_id, subs = first_edict_with_submissions(admin)
        advance(admin, edict_id, "avaliacao")
    return edict_id, subs


def test_comentario_fora_da_fase_avaliacao(admin):
    edict_id, subs = first_edict_with_submissions(admin)
    # garante fase diferente de avaliacao para o teste
    advance(admin, edict_id, "homologacao")
    r = admin.post(
        f"/submissions/{subs[0]['id']}/comments", json={"comment": "fora de fase"}
    )
    assert r.status_code == 400
    advance(admin, edict_id, "avaliacao")


def test_comentarios_criacao_e_listagem(admin, avaliacao):
    edict_id, subs = avaliacao
    sub_id = subs[0]["id"]
    r = admin.post(f"/submissions/{sub_id}/comments", json={"comment": "bom candidato"})
    assert r.status_code == 200, r.text
    comment = r.json()
    for key in ("id", "user", "submission_id", "comment", "created_at"):
        assert key in comment
    assert comment["comment"] == "bom candidato"
    assert comment["created_at"] is not None
    lista = admin.get(f"/submissions/{sub_id}/comments")
    assert lista.status_code == 200
    assert any(c.get("comment") == "bom candidato" for c in lista.json())


def test_comentario_exclusao_por_autor(admin, outro, avaliacao):
    _, subs = avaliacao
    sub_id = subs[0]["id"]
    created = admin.post(
        f"/submissions/{sub_id}/comments", json={"comment": "para excluir"}
    ).json()
    # outro usuário (mesmo admin) não pode excluir
    r403 = outro.delete(f"/submissions/comments/{created['id']}")
    assert r403.status_code == 403
    r = admin.delete(f"/submissions/comments/{created['id']}")
    assert r.status_code == 204
    r404 = admin.delete(f"/submissions/comments/{created['id']}")
    assert r404.status_code == 404
    assert admin.delete("/submissions/comments/99999999").status_code == 404


def test_favoritos(api, outro, avaliacao):
    _, subs = avaliacao
    sub_id = subs[0]["id"]
    r = api.post(f"/submissions/{sub_id}/favorites")
    assert r.status_code == 201
    r2 = api.post(f"/submissions/{sub_id}/favorites")
    assert r2.status_code == 409
    # reflete no detalhe para quem marcou
    detalhe = api.get(f"/submissions/{sub_id}").json()["summary"]
    assert detalhe["is_favorite"] is True
    # outro usuário não vê o favorito alheio
    detalhe_outro = outro.get(f"/submissions/{sub_id}").json()["summary"]
    assert detalhe_outro["is_favorite"] is False
    d = api.delete(f"/submissions/{sub_id}/favorites")
    assert d.status_code == 204
    d404 = api.delete(f"/submissions/{sub_id}/favorites")
    assert d404.status_code == 404


def test_etiquetas_cores_e_catalogo(api, outro, avaliacao):
    _, subs = avaliacao
    sub_id = subs[0]["id"]
    r = api.post(
        f"/submissions/{sub_id}/labels",
        json={"label": "destaque", "color": "#ff0000"},
    )
    assert r.status_code == 200, r.text
    label = r.json()
    for key in ("id", "user", "submission_id", "label"):
        assert key in label
    # atualizar cor em outra inscrição do mesmo autor e rótulo
    if len(subs) > 1:
        outro_sub = subs[1]["id"]
        r2 = api.post(
            f"/submissions/{outro_sub}/labels",
            json={"label": "destaque", "color": "#00ff00"},
        )
        assert r2.status_code == 200
        catalogo = api.get(f"/submissions/{sub_id}/labels").json()["labels"]
        destaque = [l for l in catalogo if l["label"] == "destaque"]
        assert destaque and destaque[0]["color"] == "#00ff00"
    # exclusão: outro autor recebe 403
    r403 = outro.delete(f"/submissions/label/{label['id']}")
    assert r403.status_code == 403
    d = api.delete(f"/submissions/label/{label['id']}")
    assert d.status_code == 204
    assert api.delete(f"/submissions/label/{label['id']}").status_code == 404
    assert api.delete("/submissions/label/99999999").status_code == 404


def test_notas_privadas_isoladas(api, outro, avaliacao):
    _, subs = avaliacao
    sub_id = subs[0]["id"]
    r = api.post(f"/submissions/{sub_id}/private_notes", json={"note": "nota v1"})
    assert r.status_code == 200, r.text
    assert r.json()["note"] == "nota v1"
    r2 = api.post(f"/submissions/{sub_id}/private_notes", json={"note": "nota v2"})
    assert r2.status_code == 200
    assert r2.json()["note"] == "nota v2"
    detalhe = api.get(f"/submissions/{sub_id}").json()["summary"]
    assert detalhe["private_note"] == "nota v2"
    detalhe_outro = outro.get(f"/submissions/{sub_id}").json()["summary"]
    assert detalhe_outro["private_note"] == ""


def test_visualizacoes(api, outro, avaliacao):
    _, subs = avaliacao
    sub_id = subs[0]["id"]
    r = api.post(f"/submissions/{sub_id}/view")
    assert r.status_code == 200
    r2 = api.post(f"/submissions/{sub_id}/view")
    assert r2.status_code == 200
    outro.post(f"/submissions/{sub_id}/view")
    lista = api.get(f"/submissions/{sub_id}/view")
    assert lista.status_code == 200
    views = lista.json()
    assert isinstance(views, list)
    minhas = [v for v in views if v.get("user_id") == 2 or v.get("user", {}).get("id") == 2]
    assert len(minhas) == 1
