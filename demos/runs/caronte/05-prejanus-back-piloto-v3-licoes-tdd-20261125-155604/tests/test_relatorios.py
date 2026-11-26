import time

import pytest

def _edict_com_inscricoes(api):
    for e in api.get("/edicts").json():
        r = api.get(f"/edicts/{e['id']}/submissions")
        if r.status_code == 200 and r.json()["submissions"]:
            return e["id"]
    pytest.skip("nenhum edital com inscrições")


def _baixar(client, path, tentativas=20):
    for _ in range(tentativas):
        r = client.get(path)
        if r.status_code == 200:
            return r
        time.sleep(0.5)
    return r


def test_interactors_plain_text(admin, api):
    edict_id = _edict_com_inscricoes(api)
    r = admin.post(f"/edicts/{edict_id}/interactors_list", json={})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data  # usuários que interagiram


def test_interactors_pdf(admin, api):
    edict_id = _edict_com_inscricoes(api)
    r = admin.post(
        f"/edicts/{edict_id}/interactors_list",
        params={"mode": "pdf"},
        json={"general_statistics": True, "approved": True},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "processing"
    job_id = data["job_id"]
    assert job_id

    pdf = _baixar(admin, f"/edicts/download_pdf/{job_id}")
    assert pdf.status_code == 200, pdf.text
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert "inline" in pdf.headers.get("content-disposition", "")
    assert pdf.content[:4] == b"%PDF"
    # consumido: nova tentativa 404
    assert admin.get(f"/edicts/download_pdf/{job_id}").status_code == 404


def test_download_inexistente_404(admin):
    assert admin.get("/edicts/download_pdf/job-inexistente").status_code == 404
    assert admin.get("/edicts/download_csv/job-inexistente").status_code == 404


def test_pairing_biddings_csv(admin, api):
    edict_id = _edict_com_inscricoes(api)
    r = admin.post(f"/edicts/{edict_id}/pairing-biddings")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "processing"
    job_id = data["job_id"]

    csv = _baixar(admin, f"/edicts/download_csv/{job_id}")
    assert csv.status_code == 200, csv.text
    assert csv.headers["content-type"].startswith("text/csv")
    texto = csv.text
    linhas = texto.strip().splitlines()
    assert linhas
    primeira = linhas[0].split(",")
    assert primeira[0] == "#"
    # linha de vagas
    assert any(l.startswith("slots") or l.split(",")[0] == "slots" for l in linhas)
    assert admin.get(f"/edicts/download_csv/{job_id}").status_code == 404


def test_relatorios_docente_403(api):
    edict_id = _edict_com_inscricoes(api)
    assert api.post(f"/edicts/{edict_id}/interactors_list", json={}).status_code == 403
    assert api.post(f"/edicts/{edict_id}/pairing-biddings").status_code == 403
