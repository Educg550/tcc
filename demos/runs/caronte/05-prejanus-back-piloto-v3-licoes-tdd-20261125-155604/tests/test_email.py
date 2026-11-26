import time

import pytest

from tests.conftest import advance_phase, first_submission, smtp_messages, smtp_raw


def _edict_com_inscricoes(api):
    for e in api.get("/edicts").json():
        r = api.get(f"/edicts/{e['id']}/submissions")
        if r.status_code == 200 and r.json()["submissions"]:
            return e["id"]
    pytest.skip("nenhum edital com inscrições")


def _aguardar_email(smtp_api, pred, tentativas=20):
    for _ in range(tentativas):
        for m in smtp_messages(smtp_api):
            raw = smtp_raw(smtp_api, m["id"])
            if pred(m, raw):
                return m, raw
        time.sleep(0.5)
    return None, None


def test_reesend_submission(admin, api, smtp_api):
    edict_id = _edict_com_inscricoes(api)
    detail = admin.get(f"/edicts/{edict_id}").json()
    if detail["phase"] != "homologacao":
        advance_phase(admin, edict_id, "homologacao")
    sub = first_submission(api, edict_id)
    r = admin.post(
        f"/submissions/{sub['id']}/reesend_submission",
        json={"text": "Corrija o documento de identidade."},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "message" in data and "email_sent" in data

    m, raw = _aguardar_email(
        smtp_api, lambda m, raw: sub["email"] in raw and "Corrija o documento" in raw
    )
    assert m is not None, "e-mail de correção não recebido"
    assert "/form/" in raw


def test_reesend_docente_403(api):
    edict_id = _edict_com_inscricoes(api)
    sub = first_submission(api, edict_id)
    r = api.post(
        f"/submissions/{sub['id']}/reesend_submission", json={"text": "x"}
    )
    assert r.status_code == 403


def _aprovada(admin, api):
    for e in api.get("/edicts").json():
        r = api.get(f"/edicts/{e['id']}/submissions")
        if r.status_code != 200:
            continue
        for s in r.json()["submissions"]:
            if s["stats"] == "approved":
                return s
    pytest.skip("nenhuma candidatura aprovada")


def test_send_accept(admin, api, smtp_api):
    sub = _aprovada(admin, api)
    r = admin.post(f"/submissions/{sub['id']}/send-accept")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "message" in data and "email_sent" in data

    m, raw = _aguardar_email(smtp_api, lambda m, raw: sub["email"] in raw and "/form/" in raw)
    assert m is not None, "e-mail de aceite não recebido"

    # repetir não cria outro envio
    msgs_antes = len(smtp_messages(smtp_api))
    r2 = admin.post(f"/submissions/{sub['id']}/send-accept")
    assert r2.status_code == 400
    time.sleep(1)
    assert len(smtp_messages(smtp_api)) == msgs_antes


def test_send_letter(admin, api, smtp_api):
    sub = _aprovada(admin, api)
    r = admin.post(f"/submissions/{sub['id']}/send-letter")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "message" in data and "email_sent" in data

    m, raw = _aguardar_email(smtp_api, lambda m, raw: sub["email"] in raw)
    assert m is not None, "carta de aceite não recebida"
    assert sub["name"] in raw

    # persistido
    detail = api.get(f"/submissions/{sub['id']}").json()
    assert detail["summary"]["letter_sent"] is True

    # repetir: 400 e sem novo e-mail
    msgs_antes = len(smtp_messages(smtp_api))
    assert admin.post(f"/submissions/{sub['id']}/send-letter").status_code == 400
    time.sleep(1)
    assert len(smtp_messages(smtp_api)) == msgs_antes
