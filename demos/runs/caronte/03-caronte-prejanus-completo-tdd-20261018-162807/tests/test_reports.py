import time

import pytest

from conftest import as_list

BASE_OPTIONS = {
    "list_of_advisors": False,
    "relation": False,
    "approved": False,
    "refused": False,
    "underreview": False,
    "general_statistics": False,
    "show_emails": False,
}


def _wait_for(client, path, timeout=90):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = client.get(path)
        if r.status_code == 200:
            return r
        assert r.status_code == 404, r.status_code
        time.sleep(1)
    pytest.fail(f"relatorio nao ficou pronto: {path}")


def test_interactors_plain_text(client, edict_factory):
    eid = edict_factory()
    r = client.post(f"/edicts/{eid}/interactors_list", json=dict(BASE_OPTIONS))
    assert r.status_code == 200, r.text
    as_list(r.json())


def test_pdf_report(client, edict_factory):
    eid = edict_factory()
    r = client.post(f"/edicts/{eid}/interactors_list", json=dict(BASE_OPTIONS, mode="pdf"))
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["status"] == "processing"
    assert "job_id" in j

    pdf = _wait_for(client, f"/edicts/download_pdf/{j['job_id']}")
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert "inline" in pdf.headers.get("content-disposition", "")
    assert pdf.content[:4] == b"%PDF"

    # arquivo removido apos o consumo completo
    assert client.get(f"/edicts/download_pdf/{j['job_id']}").status_code == 404


def test_csv_report(client, edict_factory):
    eid = edict_factory()
    r = client.post(f"/edicts/{eid}/pairing-biddings", json={})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["status"] == "processing"
    assert "job_id" in j

    csv = _wait_for(client, f"/edicts/download_csv/{j['job_id']}")
    assert csv.headers["content-type"].startswith("text/csv")
    assert "inline" in csv.headers.get("content-disposition", "")
    text = csv.content.decode("utf-8", errors="replace")
    lines = text.splitlines()
    assert lines and lines[0].startswith("#")
    assert any(line.startswith("slots") for line in lines)

    assert client.get(f"/edicts/download_csv/{j['job_id']}").status_code == 404


def test_download_unknown_job(client):
    assert client.get("/edicts/download_pdf/job-inexistente-v2").status_code == 404
    assert client.get("/edicts/download_csv/job-inexistente-v2").status_code == 404
