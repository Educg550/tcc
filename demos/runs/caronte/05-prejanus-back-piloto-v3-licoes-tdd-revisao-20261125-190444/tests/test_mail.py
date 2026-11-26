import time

import pytest

from tests.conftest import advance_to, find_submission


def _mensagens(smtp):
    r = smtp.get("/api/Messages")
    assert r.status_code == 200, r.text
    body = r.json()
    if isinstance(body, list):
        return body
    assert isinstance(body, dict), f"formato inesperado: {body!r}"
    for value in body.values():
        if isinstance(value, list):
            return value
    raise AssertionError(f"nenhuma lista de mensagens em /api/Messages: {list(body)}")


def _ultima_mensagem(smtp):
    msgs = _mensagens(smtp)
    assert msgs, "nenhuma mensagem recebida no SMTP"
    return msgs[-1]


def _raw(smtp, message_id):
    r = smtp.get(f"/api/Messages/{message_id}/raw")
    assert r.status_code == 200, r.text
    # o endpoint raw não declara charset; decodificar como UTF-8 evita mojibake
    return r.content.decode("utf-8")


def test_reesend_submission(api_admin, smtp, submission_homologacao):
    _, submission_id = submission_homologacao
    detail = api_admin.get(f"/submissions/{submission_id}").json()
    email = detail["summary"]["email"]

    antes = len(_mensagens(smtp))
    r = api_admin.post(
        f"/submissions/{submission_id}/reesend_submission",
        json={"text": "Corrigir o histórico escolar"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "message" in body and "email_sent" in body

    # mensagem entregue ao candidato
    deadline = time.time() + 30
    while time.time() < deadline:
        msgs = _mensagens(smtp)
        if len(msgs) > antes:
            break
        time.sleep(1)
    msgs = _mensagens(smtp)
    assert len(msgs) > antes, "e-mail de correção não recebido"
    ultima = msgs[-1]
    assert email in str(ultima.get("toAddresses", "")) or email in str(ultima)
    raw = _raw(smtp, ultima["id"])
    assert "Corrigir o histórico escolar" in raw
    assert "/form/" in raw


def test_reesend_restrito(api, submission_homologacao):
    _, submission_id = submission_homologacao
    r = api.post(
        f"/submissions/{submission_id}/reesend_submission",
        json={"text": "x"},
    )
    assert r.status_code == 403, r.text


def test_send_accept(api_admin, smtp, submission_aprovada):
    _, submission_id = submission_aprovada
    r = api_admin.post(f"/submissions/{submission_id}/send-accept")
    if r.status_code == 404:
        pytest.skip("formulário de aceite não configurado no edital")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "message" in body and "email_sent" in body

    # repetir não cria outro envio
    antes = len(_mensagens(smtp))
    r2 = api_admin.post(f"/submissions/{submission_id}/send-accept")
    assert r2.status_code == 400, r2.text
    time.sleep(2)
    assert len(_mensagens(smtp)) == antes, "aceite repetido enviou outro e-mail"

    # estado no detalhe: convite enviado
    detail = api_admin.get(f"/submissions/{submission_id}").json()
    accept = detail["summary"]["accept"]
    assert accept["sent"] in ("sent", "replied"), accept


def test_send_letter(api_admin, smtp, submission_aprovada):
    _, submission_id = submission_aprovada
    detail = api_admin.get(f"/submissions/{submission_id}").json()
    email = detail["summary"]["email"]

    antes = len(_mensagens(smtp))
    r = api_admin.post(f"/submissions/{submission_id}/send-letter")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "message" in body and "email_sent" in body

    deadline = time.time() + 30
    while time.time() < deadline:
        if len(_mensagens(smtp)) > antes:
            break
        time.sleep(1)
    msgs = _mensagens(smtp)
    assert len(msgs) > antes, "carta de aceite não recebida"
    raw = _raw(smtp, msgs[-1]["id"])
    assert email in raw or email in str(msgs[-1])

    # persistido
    detail = api_admin.get(f"/submissions/{submission_id}").json()
    assert detail["summary"]["letter_sent"] is True

    # repetir não envia outra carta
    antes2 = len(_mensagens(smtp))
    r2 = api_admin.post(f"/submissions/{submission_id}/send-letter")
    assert r2.status_code == 400, r2.text
    time.sleep(2)
    assert len(_mensagens(smtp)) == antes2


@pytest.fixture(scope="module")
def submission_homologacao(api_admin):
    edict_id, submission_id = find_submission(api_admin)
    advance_to(api_admin, edict_id, "homologacao")
    return edict_id, submission_id


@pytest.fixture(scope="module")
def submission_aprovada(api_admin, submission_homologacao):
    edict_id, submission_id = submission_homologacao
    advance_to(api_admin, edict_id, "avaliacao")
    r = api_admin.post(
        f"/submissions/{submission_id}/select",
        json={"stats": "approved", "user_ids": [2]},
    )
    assert r.status_code == 200, r.text
    return edict_id, submission_id
