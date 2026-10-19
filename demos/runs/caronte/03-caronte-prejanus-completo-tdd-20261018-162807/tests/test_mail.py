import json

import pytest

from conftest import as_list


def _all_submissions(client):
    out = []
    for ed in as_list(client.get("/edicts").json()):
        r = client.get(f"/edicts/{ed['id']}/submissions")
        if r.status_code == 200:
            out.extend(r.json().get("submissions") or [])
    return out


def test_reesend_submission(client, submission_ctx, is_admin):
    e, sub = submission_ctx
    if not sub:
        pytest.skip("sem candidaturas no ambiente")
    if not is_admin:
        r = client.post(f"/submissions/{sub['id']}/reesend_submission", json={"text": "x"})
        assert r.status_code == 403
        return
    r = client.post(
        f"/submissions/{sub['id']}/reesend_submission",
        json={"text": "Solicito a correcao da candidatura para o teste v2."},
    )
    if r.status_code == 400:
        pytest.skip("fase atual nao e homologacao")
    assert r.status_code == 200, r.text
    j = r.json()
    assert "message" in j and "email_sent" in j


def test_send_accept(client):
    subs = _all_submissions(client)
    approved = next((s for s in subs if "approved" in json.dumps(s)), None)
    if approved is None:
        pytest.skip("sem candidatura aprovada no ambiente")
    r = client.post(f"/submissions/{approved['id']}/send-accept", json={})
    if r.status_code in (400, 404):
        pytest.skip("formulario de aceite nao configurado ou aceite ja criado")
    assert r.status_code == 200, r.text
    j = r.json()
    assert "message" in j and "email_sent" in j


def test_send_letter(client):
    subs = _all_submissions(client)
    approved = next((s for s in subs if "approved" in json.dumps(s)), None)
    if approved is None:
        pytest.skip("sem candidatura aprovada no ambiente")
    r = client.post(f"/submissions/{approved['id']}/send-letter", json={})
    if r.status_code == 400:
        pytest.skip("candidatura nao aprovada ou carta ja enviada")
    assert r.status_code == 200, r.text
    j = r.json()
    assert "message" in j and "email_sent" in j
    d = client.get(f"/submissions/{approved['id']}").json()
    assert '"letter_sent": true' in json.dumps(d["summary"])


def test_send_letter_requires_approval(client):
    subs = _all_submissions(client)
    not_approved = next((s for s in subs if "approved" not in json.dumps(s)), None)
    if not_approved is None:
        pytest.skip("sem candidatura nao aprovada no ambiente")
    r = client.post(f"/submissions/{not_approved['id']}/send-letter", json={})
    assert r.status_code == 400
