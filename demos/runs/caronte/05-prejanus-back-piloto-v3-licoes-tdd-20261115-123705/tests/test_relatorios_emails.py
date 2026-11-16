def _extrair_job_id(body):
    if isinstance(body, dict):
        for key in ("job_id", "job", "id", "task_id"):
            if key in body:
                return body[key]
    return None


def test_lista_de_interatores_do_edital(api, edital_com_submissao):
    edict, _ = edital_com_submissao
    resp = api.post(
        f"/edicts/{edict['id']}/interactors_list",
        params={"mode": "plain_text"},
        json={},
    )
    assert resp.status_code == 200, resp.text
    job_id = _extrair_job_id(resp.json())
    if job_id:
        pdf = api.get(f"/edicts/download_pdf/{job_id}")
        assert pdf.status_code == 200, pdf.text
        csv = api.get(f"/edicts/download_csv/{job_id}")
        assert csv.status_code == 200, csv.text


def test_enviar_formulario_de_aceite(api, edital_com_submissao, smtp_api):
    _, submission = edital_com_submissao
    resp = api.post(f"/submissions/{submission['id']}/send-accept")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "message" in body and "email_sent" in body


def test_enviar_carta_de_aceite(api, edital_com_submissao):
    _, submission = edital_com_submissao
    resp = api.post(f"/submissions/{submission['id']}/send-letter")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "message" in body and "email_sent" in body


def test_pedir_reenvio_da_submissao(api, edital_com_submissao, smtp_api):
    _, submission = edital_com_submissao
    resp = api.post(
        f"/submissions/{submission['id']}/reesend_submission",
        json={"text": "Por favor, reenvie sua inscrição."},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "message" in body and "email_sent" in body

    mensagens = smtp_api.get("/api/Messages").json()
    if isinstance(mensagens, dict):
        mensagens = mensagens.get("messages", [])
    assert mensagens


def test_pareamento_de_biddings(api, edital_com_submissao):
    edict, _ = edital_com_submissao
    resp = api.post(f"/edicts/{edict['id']}/pairing-biddings")
    assert resp.status_code == 200, resp.text
