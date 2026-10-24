import time

from tests.utils import edicts_with_submissions


def _edict(admin):
    found = edicts_with_submissions(admin)
    assert found
    return found[0][0]


def _wait_for(admin, path, tries=60):
    for _ in range(tries):
        r = admin.get(path)
        if r.status_code == 200:
            return r
        assert r.status_code == 404
        time.sleep(1)
    raise AssertionError(f"relatorio nao ficou disponivel: {path}")


def test_interactors_list_plain_text(admin):
    eid = _edict(admin)
    r = admin.post(f"/edicts/{eid}/interactors_list", json={})
    assert r.status_code == 200, r.text
    assert r.json() is not None


def test_interactors_list_pdf(admin):
    eid = _edict(admin)
    r = admin.post(
        f"/edicts/{eid}/interactors_list", params={"mode": "pdf"}, json={}
    )
    assert r.status_code == 200, r.text
    job = r.json()
    assert job["status"] == "processing"
    job_id = job["job_id"]

    d = _wait_for(admin, f"/edicts/download_pdf/{job_id}")
    assert d.headers["content-type"].startswith("application/pdf")
    assert "inline" in d.headers.get("content-disposition", "")
    assert d.content[:4] == b"%PDF"

    # arquivo consumido e removido
    assert admin.get(f"/edicts/download_pdf/{job_id}").status_code == 404


def test_pairing_biddings_csv(admin):
    eid = _edict(admin)
    r = admin.post(f"/edicts/{eid}/pairing-biddings")
    assert r.status_code == 200, r.text
    job = r.json()
    assert job["status"] == "processing"
    job_id = job["job_id"]

    d = _wait_for(admin, f"/edicts/download_csv/{job_id}")
    assert d.headers["content-type"].startswith("text/csv")
    assert "inline" in d.headers.get("content-disposition", "")
    text = d.content.decode("utf-8")
    lines = text.splitlines()
    assert lines
    assert lines[0].startswith("#")
    assert any(line.split(",")[0].strip() == "slots" for line in lines)

    assert admin.get(f"/edicts/download_csv/{job_id}").status_code == 404


def test_download_jobs_are_distinct(admin):
    eid = _edict(admin)
    pdf = admin.post(f"/edicts/{eid}/interactors_list", params={"mode": "pdf"}, json={})
    csv = admin.post(f"/edicts/{eid}/pairing-biddings")
    assert pdf.json()["job_id"] != csv.json()["job_id"]


def test_download_unknown_job(admin):
    assert admin.get("/edicts/download_pdf/job-inexistente").status_code == 404
    assert admin.get("/edicts/download_csv/job-inexistente").status_code == 404
