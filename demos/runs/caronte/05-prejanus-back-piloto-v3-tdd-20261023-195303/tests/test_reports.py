import time


def _download(client, path, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = client.get(path)
        if resp.status_code == 200:
            return resp
        if resp.status_code == 404:
            time.sleep(1)
            continue
        raise AssertionError(f"download inesperado: {resp.status_code}")
    raise AssertionError(f"relatório não ficou pronto: {path}")


def test_download_nonexistent_job(client):
    assert client.get("/edicts/download_pdf/nao-existe").status_code == 404
    assert client.get("/edicts/download_csv/nao-existe").status_code == 404


def test_pdf_report(client, edict_with_submissions):
    detail, _ = edict_with_submissions
    resp = client.post(
        f"/edicts/{detail['id']}/interactors_list",
        params={"mode": "pdf"},
        json={"general_statistics": True, "approved": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "processing"
    job_id = body["job_id"]

    pdf = _download(client, f"/edicts/download_pdf/{job_id}")
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert "inline" in pdf.headers.get("content-disposition", "")
    assert pdf.content[:4] == b"%PDF"

    # arquivo removido apos o consumo
    assert client.get(f"/edicts/download_pdf/{job_id}").status_code == 404


def test_csv_report(client, evaluation_edict):
    detail, _ = evaluation_edict
    resp = client.post(f"/edicts/{detail['id']}/pairing-biddings")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "processing"
    job_id = body["job_id"]

    csv = _download(client, f"/edicts/download_csv/{job_id}")
    assert csv.headers["content-type"].startswith("text/csv")
    assert "inline" in csv.headers.get("content-disposition", "")
    text = csv.text
    lines = text.strip().splitlines()
    assert lines
    assert lines[0].startswith("#")
    assert any(line.split(",")[0] == "slots" for line in lines)

    assert client.get(f"/edicts/download_csv/{job_id}").status_code == 404
