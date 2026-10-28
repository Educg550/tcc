"""V2-REL-01..03 — interactors, PDF, CSV e downloads."""
import time


def test_interactors_plain_text(admin, submission_ctx):
    edict, _ = submission_ctx
    r = admin.post(f"/edicts/{edict['id']}/interactors_list", json={})
    assert r.status_code == 200, r.text
    users = r.json()
    assert isinstance(users, list)


def test_interactors_pdf(admin, submission_ctx):
    edict, _ = submission_ctx
    r = admin.post(
        f"/edicts/{edict['id']}/interactors_list",
        params={"mode": "pdf"},
        json={"general_statistics": True, "approved": True, "show_emails": True},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "processing"
    job_id = body["job_id"]

    deadline = time.time() + 60
    last = None
    while time.time() < deadline:
        last = admin.get(f"/edicts/download_pdf/{job_id}")
        if last.status_code == 200:
            break
        time.sleep(1)
    assert last is not None and last.status_code == 200, "pdf nao ficou pronto"
    assert last.headers["content-type"].startswith("application/pdf")
    assert "inline" in last.headers.get("content-disposition", "")
    assert last.content[:4] == b"%PDF"
    # arquivo removido apos o consumo
    assert admin.get(f"/edicts/download_pdf/{job_id}").status_code == 404


def test_download_job_inexistente(admin):
    assert admin.get("/edicts/download_pdf/job-inexistente").status_code == 404
    assert admin.get("/edicts/download_csv/job-inexistente").status_code == 404


def test_pairing_biddings_csv(admin, submission_ctx):
    edict, _ = submission_ctx
    r = admin.post(f"/edicts/{edict['id']}/pairing-biddings")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "processing"
    job_id = body["job_id"]

    deadline = time.time() + 60
    last = None
    while time.time() < deadline:
        last = admin.get(f"/edicts/download_csv/{job_id}")
        if last.status_code == 200:
            break
        time.sleep(1)
    assert last is not None and last.status_code == 200, "csv nao ficou pronto"
    assert last.headers["content-type"].startswith("text/csv")
    assert "inline" in last.headers.get("content-disposition", "")

    lines = last.text.splitlines()
    assert lines
    assert lines[0].startswith("#")
    assert any(line.split(",")[0].strip() == "slots" for line in lines)
    assert admin.get(f"/edicts/download_csv/{job_id}").status_code == 404


def test_relatorios_restritos_a_administrativos(api, submission_ctx):
    edict, _ = submission_ctx
    assert api.post(f"/edicts/{edict['id']}/interactors_list", json={}).status_code == 403
    assert api.post(f"/edicts/{edict['id']}/pairing-biddings").status_code == 403
