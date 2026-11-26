import time

import pytest

from tests.conftest import find_submission


def _aguardar_download(client, path, timeout=60):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = client.get(path)
        if r.status_code == 200:
            return r
        assert r.status_code == 404, r.text
        time.sleep(1)
    pytest.fail(f"relatório não ficou disponível: {path}")


def test_interactors_plain_text(api_admin):
    edict_id, _ = find_submission(api_admin)
    r = api_admin.post(f"/edicts/{edict_id}/interactors_list", json={})
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body, list)
    for user in body:
        assert "id" in user or "email" in user or "name" in user, user


def test_interactors_pdf(api_admin):
    edict_id, _ = find_submission(api_admin)
    r = api_admin.post(
        f"/edicts/{edict_id}/interactors_list",
        params={"mode": "pdf"},
        json={"general_statistics": True, "approved": True, "show_emails": True},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "processing"
    job_id = body["job_id"]
    assert job_id

    rd = _aguardar_download(api_admin, f"/edicts/download_pdf/{job_id}")
    assert rd.headers["content-type"].startswith("application/pdf")
    assert "inline" in rd.headers.get("content-disposition", "")
    conteudo = rd.content
    assert conteudo[:5] == b"%PDF-"

    # consumido: nova tentativa 404
    r2 = api_admin.get(f"/edicts/download_pdf/{job_id}")
    assert r2.status_code == 404, r2.text


def test_pairing_biddings_csv(api_admin):
    edict_id, _ = find_submission(api_admin)
    r = api_admin.post(f"/edicts/{edict_id}/pairing-biddings")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "processing"
    job_id = body["job_id"]

    rd = _aguardar_download(api_admin, f"/edicts/download_csv/{job_id}")
    assert rd.headers["content-type"].startswith("text/csv")
    assert "inline" in rd.headers.get("content-disposition", "")
    linhas = rd.text.strip().splitlines()
    assert linhas, "CSV vazio"
    assert linhas[0].startswith("#")
    if len(linhas) > 1:
        assert linhas[1].startswith("slots") or "slots" in linhas[1]

    assert api_admin.get(f"/edicts/download_csv/{job_id}").status_code == 404


def test_download_job_inexistente(api_admin):
    assert api_admin.get("/edicts/download_pdf/job-inexistente").status_code == 404
    assert api_admin.get("/edicts/download_csv/job-inexistente").status_code == 404
