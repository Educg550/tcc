import time

import pytest

from conftest import first_edict_with_submissions


def _wait_download(client, path, timeout=60):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = client.get(path)
        if r.status_code == 200:
            return r
        time.sleep(1)
    return client.get(path)


def test_interactors_plain_text(admin):
    edict_id, _ = first_edict_with_submissions(admin)
    r = admin.post(f"/edicts/{edict_id}/interactors_list", json={})
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body, list)


def test_interactors_pdf(admin):
    edict_id, _ = first_edict_with_submissions(admin)
    r = admin.post(
        f"/edicts/{edict_id}/interactors_list",
        params={"mode": "pdf"},
        json={"general_statistics": True, "approved": True},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "processing"
    job_id = body["job_id"]
    # antes de pronto ou job inexistente: 404
    assert admin.get("/edicts/download_pdf/job-inexistente-xyz").status_code == 404
    pdf = _wait_download(admin, f"/edicts/download_pdf/{job_id}")
    assert pdf.status_code == 200, pdf.text
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert "inline" in pdf.headers.get("content-disposition", "")
    assert pdf.content[:4] == b"%PDF"
    # arquivo removido após consumo
    time.sleep(1)
    assert admin.get(f"/edicts/download_pdf/{job_id}").status_code == 404


def test_pairing_biddings_csv(admin):
    edict_id, _ = first_edict_with_submissions(admin)
    r = admin.post(f"/edicts/{edict_id}/pairing-biddings")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "processing"
    job_id = body["job_id"]
    csv = _wait_download(admin, f"/edicts/download_csv/{job_id}")
    assert csv.status_code == 200, csv.text
    assert csv.headers["content-type"].startswith("text/csv")
    assert "inline" in csv.headers.get("content-disposition", "")
    linhas = csv.text.strip().splitlines()
    assert linhas
    assert linhas[0].startswith("#")
    assert any(l.startswith("slots") for l in linhas)
    time.sleep(1)
    assert admin.get(f"/edicts/download_csv/{job_id}").status_code == 404


def test_relatorios_restritos_a_admin(api):
    edict_id, _ = first_edict_with_submissions(api)
    r = api.post(f"/edicts/{edict_id}/interactors_list", json={})
    assert r.status_code == 403
    r2 = api.post(f"/edicts/{edict_id}/pairing-biddings")
    assert r2.status_code == 403
