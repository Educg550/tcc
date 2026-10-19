"""V2-AUT-02 (início do fluxo) e V2-MAI-02/03: comunicação."""


def test_senhaunica_inicio_do_fluxo(api):
    """Sem oauth_token, responde com redirect_to e guarda o segredo na sessão."""
    resp = api.post("/auth/login/senhaunica")
    assert resp.status_code == 200
    data = resp.json()
    assert "redirect_to" in data
    assert data["redirect_to"]


def test_senhaunica_sem_segredo_401(api):
    """Retorno com oauth_token mas sem o segredo na sessão responde 401."""
    resp = api.post("/auth/login/senhaunica",
                    json={"oauth_token": "token-qualquer",
                          "oauth_verifier": "verifier-qualquer"})
    assert resp.status_code == 401


def test_send_accept_exige_candidatura_aprovada(api, any_submission):
    detail = api.get(f"/submissions/{any_submission['id']}").json()
    if detail["summary"]["stats"] == "approved":
        pytest.skip("candidatura já aprovada")
    resp = api.post(f"/submissions/{any_submission['id']}/send-accept")
    assert resp.status_code == 400


def test_send_letter_exige_candidatura_aprovada(api, any_submission):
    detail = api.get(f"/submissions/{any_submission['id']}").json()
    if detail["summary"]["stats"] == "approved":
        pytest.skip("candidatura já aprovada")
    resp = api.post(f"/submissions/{any_submission['id']}/send-letter")
    assert resp.status_code == 400


def test_send_accept_sem_sessao_401(api_sem_atalho):
    resp = api_sem_atalho.post("/submissions/1/send-accept")
    assert resp.status_code == 401


def test_send_letter_sem_sessao_401(api_sem_atalho):
    resp = api_sem_atalho.post("/submissions/1/send-letter")
    assert resp.status_code == 401
