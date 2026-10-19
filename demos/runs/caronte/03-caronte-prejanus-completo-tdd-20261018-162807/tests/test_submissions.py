import json
from urllib.parse import quote

import pytest

from conftest import as_list


def test_submissions_list_stable(client, submission_ctx):
    e, sub = submission_ctx
    if not sub:
        pytest.skip("sem candidaturas no ambiente")
    r = client.get(f"/edicts/{e['id']}/submissions")
    assert r.status_code == 200
    subs = r.json()["submissions"]
    assert isinstance(subs, list) and subs
    ids = [s["id"] for s in subs]
    assert len(ids) == len(set(ids))
    # leituras repetidas nao duplicam inscricoes
    r2 = client.get(f"/edicts/{e['id']}/submissions")
    assert [s["id"] for s in r2.json()["submissions"]] == ids


def test_submissions_filters(client, submission_ctx):
    e, sub = submission_ctx
    if not sub:
        pytest.skip("sem candidaturas no ambiente")
    assert client.get(
        f"/edicts/{e['id']}/submissions", params={"only_favorites": "true"}
    ).status_code == 200
    assert client.get(
        f"/edicts/{e['id']}/submissions", params={"stats": "approved"}
    ).status_code == 200


def test_submission_detail(client, submission_ctx):
    e, sub = submission_ctx
    if not sub:
        pytest.skip("sem candidaturas no ambiente")
    r = client.get(f"/submissions/{sub['id']}")
    assert r.status_code == 200
    d = r.json()
    assert "summary" in d and "submission_form" in d
    assert client.get(
        f"/submissions/{sub['id']}", params={"include_comments": "true"}
    ).status_code == 200
    assert client.get("/submissions/999999999").status_code == 404


def test_submission_file_not_served_for_unknown_label(client, submission_ctx):
    e, sub = submission_ctx
    if not sub:
        pytest.skip("sem candidaturas no ambiente")
    r = client.get(f"/submissions/{sub['id']}/files/qualquer/arquivo.pdf")
    assert r.status_code == 404


def test_submission_file_download(client, submission_ctx):
    e, sub = submission_ctx
    if not sub:
        pytest.skip("sem candidaturas no ambiente")
    d = client.get(f"/submissions/{sub['id']}").json()
    found = None

    def walk(node):
        nonlocal found
        if found is not None:
            return
        if isinstance(node, dict):
            val = node.get("value")
            name = node.get("name") or node.get("label")
            if (isinstance(val, str) and val.lower().endswith(".pdf")
                    and isinstance(name, str) and name):
                found = (name, val)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(d.get("submission_form"))
    if found is None:
        pytest.skip("candidatura sem anexo pdf")
    label, filename = found
    url = f"/submissions/{sub['id']}/files/{quote(label)}/{quote(filename)}"
    r = client.get(url)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/pdf")
    assert "attachment" in r.headers.get("content-disposition", "")
    assert r.content[:4] == b"%PDF"
