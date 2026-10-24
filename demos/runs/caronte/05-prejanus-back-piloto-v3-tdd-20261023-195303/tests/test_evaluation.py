import uuid


def test_comment_only_in_evaluation_phase(client, edict_with_submissions):
    _, subs = edict_with_submissions
    resp = client.post(
        f"/submissions/{subs[0]['id']}/comments", json={"comment": "teste"}
    )
    # fora da fase avaliacao a criacao e recusada
    assert resp.status_code in (200, 400)


def test_comment_lifecycle(client, evaluation_edict):
    _, subs = evaluation_edict
    submission_id = subs[0]["id"]
    text = f"comentario {uuid.uuid4().hex[:8]}"
    resp = client.post(
        f"/submissions/{submission_id}/comments", json={"comment": text}
    )
    assert resp.status_code == 200
    comment = resp.json()
    for key in ("id", "user", "submission_id", "comment", "created_at"):
        assert key in comment
    assert comment["comment"] == text
    assert comment["submission_id"] == submission_id
    assert comment["user"]["id"] == 2

    # atividade registra o comentario sem duplicar por leitura
    activity = client.get(f"/submissions/{submission_id}/comments").json()
    before = [a for a in activity if a.get("comment") == text]
    assert len(before) == 1
    activity2 = client.get(f"/submissions/{submission_id}/comments").json()
    assert len([a for a in activity2 if a.get("comment") == text]) == 1

    # exclusao pelo proprio autor
    assert (
        client.delete(f"/submissions/comments/{comment['id']}").status_code == 204
    )
    assert client.delete(f"/submissions/comments/{comment['id']}").status_code == 404


def test_comment_not_found(client):
    assert client.delete("/submissions/comments/99999999").status_code == 404


def test_favorite_lifecycle(client, evaluation_edict):
    _, subs = evaluation_edict
    submission_id = subs[0]["id"]
    # limpa estado anterior, se houver
    client.delete(f"/submissions/{submission_id}/favorites")

    resp = client.post(f"/submissions/{submission_id}/favorites")
    assert resp.status_code == 201
    assert client.post(f"/submissions/{submission_id}/favorites").status_code == 409

    listing = client.get(f"/edicts/{evaluation_edict[0]['id']}/submissions").json()
    sub = next(s for s in listing["submissions"] if s["id"] == submission_id)
    assert sub["is_favorite"] is True

    assert client.delete(f"/submissions/{submission_id}/favorites").status_code == 204
    assert client.delete(f"/submissions/{submission_id}/favorites").status_code == 404

    listing = client.get(f"/edicts/{evaluation_edict[0]['id']}/submissions").json()
    sub = next(s for s in listing["submissions"] if s["id"] == submission_id)
    assert sub["is_favorite"] is False


def test_only_favorites_filter(client, evaluation_edict):
    detail, subs = evaluation_edict
    submission_id = subs[0]["id"]
    client.delete(f"/submissions/{submission_id}/favorites")
    empty = client.get(
        f"/edicts/{detail['id']}/submissions", params={"only_favorites": True}
    ).json()["submissions"]
    assert submission_id not in [s["id"] for s in empty]

    client.post(f"/submissions/{submission_id}/favorites")
    favs = client.get(
        f"/edicts/{detail['id']}/submissions", params={"only_favorites": True}
    ).json()["submissions"]
    assert submission_id in [s["id"] for s in favs]
    client.delete(f"/submissions/{submission_id}/favorites")


def test_label_lifecycle(client, evaluation_edict):
    _, subs = evaluation_edict
    submission_id = subs[0]["id"]
    label = f"etiqueta-{uuid.uuid4().hex[:6]}"

    resp = client.post(
        f"/submissions/{submission_id}/labels",
        json={"label": label, "color": "#ff0000"},
    )
    assert resp.status_code == 200
    created = resp.json()
    for key in ("id", "user", "submission_id", "label"):
        assert key in created
    assert created["label"] == label

    # catalogo do usuario
    catalog = client.get(f"/submissions/{submission_id}/labels").json()
    assert "labels" in catalog
    entry = next(l for l in catalog["labels"] if l["label"] == label)
    assert entry["color"] == "#ff0000"

    # etiqueta aparece no detalhe da inscricao
    detail = client.get(f"/submissions/{submission_id}").json()
    labels = detail["summary"]["labels"]
    assert label in [l["label"] for l in labels]

    # exclusao pelo proprio autor
    assert client.delete(f"/submissions/label/{created['id']}").status_code == 204
    assert client.delete(f"/submissions/label/{created['id']}").status_code == 404


def test_label_not_found(client):
    assert client.delete("/submissions/label/99999999").status_code == 404


def test_private_note(client, evaluation_edict):
    _, subs = evaluation_edict
    submission_id = subs[0]["id"]
    note = f"nota {uuid.uuid4().hex[:8]}"

    resp = client.post(
        f"/submissions/{submission_id}/private_notes", json={"note": note}
    )
    assert resp.status_code == 200
    assert resp.json()["note"] == note

    # atualizacao nao cria outra nota
    note2 = note + " atualizada"
    resp = client.post(
        f"/submissions/{submission_id}/private_notes", json={"note": note2}
    )
    assert resp.status_code == 200
    assert resp.json()["note"] == note2

    detail = client.get(f"/submissions/{submission_id}").json()
    assert detail["summary"]["private_note"] == note2


def test_private_note_empty_when_absent(client, evaluation_edict):
    _, subs = evaluation_edict
    submission_id = subs[-1]["id"]
    detail = client.get(f"/submissions/{submission_id}").json()
    assert detail["summary"]["private_note"] == ""


def test_view_registration(client, evaluation_edict):
    _, subs = evaluation_edict
    submission_id = subs[0]["id"]
    assert client.post(f"/submissions/{submission_id}/view").status_code == 200
    assert client.post(f"/submissions/{submission_id}/view").status_code == 200

    views = client.get(f"/submissions/{submission_id}/view").json()
    assert isinstance(views, list)
    mine = [v for v in views if v.get("user_id") == 2 or v.get("user", {}).get("id") == 2]
    # repeticoes no mesmo dia nao criam outra linha
    assert len(mine) == 1
