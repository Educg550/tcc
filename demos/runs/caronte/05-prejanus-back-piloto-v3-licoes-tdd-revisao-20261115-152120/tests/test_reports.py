import csv
import io

import pytest

from helpers import advance, create_edict, submissions_of, wait_download


@pytest.fixture(scope="module")
def rep(admin, api):
    eid = create_edict(admin, "Edital relatórios")
    advance(admin, eid, "avaliacao")
    subs = submissions_of(api, eid)
    sid = subs[0]["id"]
    api.post(f"/submissions/{sid}/comments", json={"comment": "comentário do relatório"})
    api.post(f"/submissions/{sid}/favorites")
    api.post(f"/edicts/{eid}/slots", json={"amount": "2"})
    api.post(f"/submissions/{sid}/bidding", json={"bidding": "interested"})
    return {"id": eid, "sid": sid, "subs": subs}


def test_interactors_plain_text(admin, api, rep):
    # docente não gera relatório
    assert (
        api.post(f"/edicts/{rep['id']}/interactors_list", json={}).status_code == 403
    )
    r = admin.post(f"/edicts/{rep['id']}/interactors_list", json={})
    assert r.status_code == 200, r.text
    users = r.json()
    assert isinstance(users, list) and users
    ids = [u.get("id") for u in users]
    # o docente interagiu por comentário e favorito
    assert 2 in ids, users


def test_relatorio_pdf(admin, rep):
    r = admin.post(
        f"/edicts/{rep['id']}/interactors_list",
        params={"mode": "pdf"},
        json={"general_statistics": True, "approved": True, "show_emails": True},
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["status"] == "processing"
    assert j["job_id"]

    pdf = wait_download(admin, f"/edicts/download_pdf/{j['job_id']}")
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert "inline" in pdf.headers.get("content-disposition", "")
    assert pdf.content[:4] == b"%PDF"

    # arquivo removido após o consumo
    assert admin.get(f"/edicts/download_pdf/{j['job_id']}").status_code == 404


def test_download_job_inexistente_404(admin):
    assert admin.get("/edicts/download_pdf/job-inexistente").status_code == 404
    assert admin.get("/edicts/download_csv/job-inexistente").status_code == 404


def test_pairing_biddings_csv(admin, api, rep):
    r = admin.post(f"/edicts/{rep['id']}/pairing-biddings")
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["status"] == "processing"
    assert j["job_id"]

    res = wait_download(admin, f"/edicts/download_csv/{j['job_id']}")
    assert res.headers["content-type"].startswith("text/csv")
    assert "inline" in res.headers.get("content-disposition", "")

    rows = list(csv.reader(io.StringIO(res.text)))
    header = rows[0]
    assert header[0] == "#"

    teacher_email = api.get("/auth/login").json()["email"]
    assert teacher_email in header, header
    idx = header.index(teacher_email)

    slots_row = next(row for row in rows if row[0] == "slots")
    assert slots_row[idx] == "2", slots_row

    sub_rows = [row for row in rows if row[0] not in ("#", "slots")]
    assert sub_rows, rows
    assert any(row[idx] == "interested" for row in sub_rows), rows

    # arquivo removido após o consumo
    assert admin.get(f"/edicts/download_csv/{j['job_id']}").status_code == 404
