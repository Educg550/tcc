import pytest

from conftest import edict_detail, find_edict, get_edicts, submissions_of


def test_slots(client):
    eid = get_edicts(client)[0]["id"]
    r = client.post(f"/edicts/{eid}/slots", json={"amount": "3"})
    assert r.status_code == 200
    assert r.json()["amount"] == "3"
    assert edict_detail(client, eid)["slots"] == "3"
    assert client.post(f"/edicts/{eid}/slots", json={"amount": ""}).json()["amount"] == "0"
    assert client.post(f"/edicts/{eid}/slots", json={"amount": "-2"}).json()["amount"] == "0"
    assert client.post(f"/edicts/{eid}/slots", json={"amount": "abc"}).status_code == 422


def test_bidding(client):
    ed = find_edict(client, with_submissions=True)
    if ed is None:
        pytest.skip("nenhum edital com inscricoes")
    sid = submissions_of(client, ed["id"])[0]["id"]
    r = client.post(f"/submissions/{sid}/bidding", json={"bidding": "interested"})
    assert r.status_code == 200
    r = client.post(f"/submissions/{sid}/bidding", json={"bidding": ""})
    assert r.status_code == 200
    r = client.post(f"/submissions/{sid}/bidding", json={"bidding": "banana"})
    assert r.status_code == 422


def test_select_forbidden_for_teacher(client):
    ed = find_edict(client, with_submissions=True)
    if ed is None:
        pytest.skip("nenhum edital com inscricoes")
    sid = submissions_of(client, ed["id"])[0]["id"]
    r = client.post(
        f"/submissions/{sid}/select", json={"stats": "approved", "user_ids": None}
    )
    assert r.status_code == 403


def test_reesend_submission_forbidden_for_teacher(client):
    ed = find_edict(client, with_submissions=True)
    if ed is None:
        pytest.skip("nenhum edital com inscricoes")
    sid = submissions_of(client, ed["id"])[0]["id"]
    r = client.post(f"/submissions/{sid}/reesend_submission", json={"text": "motivo"})
    assert r.status_code == 403


def test_download_missing_job_404(client):
    assert client.get("/edicts/download_pdf/job-inexistente").status_code == 404
    assert client.get("/edicts/download_csv/job-inexistente").status_code == 404
