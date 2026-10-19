import pytest

from conftest import find_edict, items, submissions_of


@pytest.fixture(scope="module")
def eval_edict(client):
    ed = find_edict(client, phase="avaliacao", with_submissions=True)
    if ed is None:
        pytest.skip("nenhum edital em avaliacao com inscricoes")
    return ed


@pytest.fixture(scope="module")
def eval_submission(client, eval_edict):
    return submissions_of(client, eval_edict["id"])[0]["id"]


def test_favorites_lifecycle(client, eval_edict, eval_submission):
    sid = eval_submission
    # garante estado inicial limpo
    client.delete(f"/submissions/{sid}/favorites")
    assert client.post(f"/submissions/{sid}/favorites").status_code == 201
    assert client.post(f"/submissions/{sid}/favorites").status_code == 409
    favs = submissions_of(client, eval_edict["id"], only_favorites=True)
    assert sid in [s["id"] for s in favs]
    assert client.delete(f"/submissions/{sid}/favorites").status_code == 204
    assert client.delete(f"/submissions/{sid}/favorites").status_code == 404
    favs = submissions_of(client, eval_edict["id"], only_favorites=True)
    assert sid not in [s["id"] for s in favs]


def test_labels_lifecycle(client, eval_submission):
    sid = eval_submission
    r = client.post(
        f"/submissions/{sid}/labels",
        json={"label": "etiqueta-teste", "color": "#123456"},
    )
    assert r.status_code == 200, r.text
    lab = r.json()
    for k in ("id", "user", "submission_id", "label"):
        assert k in lab, k
    cat = client.get(f"/submissions/{sid}/labels").json()
    assert "labels" in cat
    assert any(l["label"] == "etiqueta-teste" for l in cat["labels"])
    lid = lab["id"]
    assert client.delete(f"/submissions/label/{lid}").status_code == 204
    assert client.delete(f"/submissions/label/{lid}").status_code == 404
    assert client.delete("/submissions/label/99999999").status_code == 404


def test_private_notes(client, eval_submission):
    sid = eval_submission
    r = client.post(f"/submissions/{sid}/private_notes", json={"note": "nota um"})
    assert r.status_code == 200
    assert r.json()["note"] == "nota um"
    r = client.post(f"/submissions/{sid}/private_notes", json={"note": "nota dois"})
    assert r.status_code == 200
    assert r.json()["note"] == "nota dois"


def test_views(client, eval_submission):
    sid = eval_submission
    assert client.post(f"/submissions/{sid}/view").status_code == 200
    assert client.post(f"/submissions/{sid}/view").status_code == 200
    r = client.get(f"/submissions/{sid}/view")
    assert r.status_code == 200
    views = items(r.json())
    mine = [
        v
        for v in views
        if v.get("user_id") == 2 or (v.get("user") or {}).get("id") == 2
    ]
    # repeticoes no mesmo dia nao criam outra linha
    assert len(mine) <= 1


def test_comments_lifecycle(client, eval_submission):
    sid = eval_submission
    r = client.post(
        f"/submissions/{sid}/comments", json={"comment": "comentario de teste"}
    )
    assert r.status_code == 200, r.text
    c = r.json()
    for k in ("id", "user", "submission_id", "comment"):
        assert k in c, k
    after = items(client.get(f"/submissions/{sid}/comments").json())
    assert any(
        (x.get("comment") == "comentario de teste") or (x.get("text") == "comentario de teste")
        for x in after
    )
    # ler nao registra novo evento
    again = items(client.get(f"/submissions/{sid}/comments").json())
    assert len(again) == len(after)
    cid = c["id"]
    assert client.delete(f"/submissions/comments/{cid}").status_code == 204
    assert client.delete(f"/submissions/comments/{cid}").status_code == 404
    assert client.delete("/submissions/comments/99999999").status_code == 404


def test_comment_outside_avaliacao_is_400(client):
    ed = find_edict(client, with_submissions=True)
    if ed is None or ed.get("phase") == "avaliacao":
        ed = None
        for e in client.get("/edicts").json():
            d = client.get(f"/edicts/{e['id']}").json()
            if d.get("phase") != "avaliacao" and submissions_of(client, e["id"]):
                ed = d
                break
    if ed is None:
        pytest.skip("nenhum edital fora de avaliacao com inscricoes")
    sid = submissions_of(client, ed["id"])[0]["id"]
    r = client.post(f"/submissions/{sid}/comments", json={"comment": "fora de fase"})
    assert r.status_code == 400
