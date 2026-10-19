import json

import pytest

from conftest import as_list


def test_comments(client, submission_ctx):
    e, sub = submission_ctx
    if not sub:
        pytest.skip("sem candidaturas no ambiente")
    sid = sub["id"]
    r = client.post(f"/submissions/{sid}/comments", json={"comment": "comentario de teste v2"})
    if r.status_code == 400:
        pytest.skip("fase atual nao e avaliacao")
    assert r.status_code in (200, 201), r.text
    c = r.json()
    assert "id" in c

    lst = as_list(client.get(f"/submissions/{sid}/comments").json())
    assert any(i.get("id") == c["id"] for i in lst)

    assert client.delete(f"/submissions/comments/{c['id']}").status_code == 204
    assert client.delete(f"/submissions/comments/{c['id']}").status_code == 404
    assert client.delete("/submissions/comments/999999999").status_code == 404


def test_favorites(client, submission_ctx):
    e, sub = submission_ctx
    if not sub:
        pytest.skip("sem candidaturas no ambiente")
    sid = sub["id"]
    r = client.post(f"/submissions/{sid}/favorites", json={})
    if r.status_code == 400:
        pytest.skip("fase atual nao e avaliacao")
    assert r.status_code == 201, r.text
    assert client.post(f"/submissions/{sid}/favorites", json={}).status_code == 409
    assert client.delete(f"/submissions/{sid}/favorites").status_code == 204
    assert client.delete(f"/submissions/{sid}/favorites").status_code == 404


def test_labels(client, submission_ctx):
    e, sub = submission_ctx
    if not sub:
        pytest.skip("sem candidaturas no ambiente")
    sid = sub["id"]
    r = client.post(f"/submissions/{sid}/labels", json={"label": "etiqueta-teste-v2", "color": "#ff0000"})
    if r.status_code == 400:
        pytest.skip("fase atual nao e avaliacao")
    assert r.status_code in (200, 201), r.text
    m = r.json()
    assert "id" in m

    cat = as_list(client.get(f"/submissions/{sid}/labels").json())
    match = [l for l in cat if l.get("label") == "etiqueta-teste-v2"]
    assert match and match[0].get("color") == "#ff0000"

    lid = m["id"]
    assert client.delete(f"/submissions/label/{lid}").status_code == 204
    assert client.delete(f"/submissions/label/{lid}").status_code == 404
    assert client.delete("/submissions/label/999999999").status_code == 404


def test_private_notes(client, submission_ctx):
    e, sub = submission_ctx
    if not sub:
        pytest.skip("sem candidaturas no ambiente")
    sid = sub["id"]
    r = client.post(f"/submissions/{sid}/private_notes", json={"note": "nota secreta v2"})
    if r.status_code == 400:
        pytest.skip("fase atual nao e avaliacao")
    assert r.status_code == 200, r.text
    assert "nota secreta v2" in r.text

    # atualizar nao cria outra nota
    r2 = client.post(f"/submissions/{sid}/private_notes", json={"note": "nota alterada v2"})
    assert r2.status_code == 200
    assert "nota alterada v2" in r2.text

    d = client.get(f"/submissions/{sid}").json()
    assert "nota alterada v2" in json.dumps(d["summary"])


def test_view(client, submission_ctx):
    e, sub = submission_ctx
    if not sub:
        pytest.skip("sem candidaturas no ambiente")
    sid = sub["id"]
    assert client.post(f"/submissions/{sid}/view", json={}).status_code == 200
    lst = as_list(client.get(f"/submissions/{sid}/view").json())
    assert lst, "visualizacao do usuario nao registrada"
