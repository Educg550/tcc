"""V2-REL-01 a V2-REL-03: relatórios e downloads."""


def test_download_pdf_job_inexistente_404(api):
    resp = api.get("/edicts/download_pdf/job-inexistente-000")
    assert resp.status_code == 404


def test_download_csv_job_inexistente_404(api):
    resp = api.get("/edicts/download_csv/job-inexistente-000")
    assert resp.status_code == 404


def test_download_pdf_publico_sem_sessao(api_sem_atalho):
    """Downloads por job_id são públicos no contrato original."""
    resp = api_sem_atalho.get("/edicts/download_pdf/job-inexistente-000")
    assert resp.status_code == 404


def test_download_csv_publico_sem_sessao(api_sem_atalho):
    resp = api_sem_atalho.get("/edicts/download_csv/job-inexistente-000")
    assert resp.status_code == 404
