import time

import pytest

from conftest import (
    advance,
    first_edict_with_submissions,
    get_edict,
    wait_for_email,
)


def _aprovada_com_orientador(admin, edict_id, subs):
    sub = subs[0]
    admin.post(f"/submissions/{sub['id']}/select", json={"stats": "approved", "user_ids": [2]})
    return sub


def test_reesend_submission(admin, smtp_api):
    edict_id, subs = first_edict_with_submissions(admin)
    advance(admin, edict_id, "homologacao")
    sub = subs[0]
    detalhe = admin.get(f"/submissions/{sub['id']}").json()
    email = detalhe["summary"]["email"]
    r = admin.post(
        f"/submissions/{sub['id']}/reesend_submission",
        json={"text": "Falta o diploma."},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "message" in body and "email_sent" in body
    msg = wait_for_email(smtp_api, lambda m: email in str(m.get("toAddresses", "")))
    raw = smtp_api.get(f"/api/Messages/{msg['id']}/raw").text
    assert "Falta o diploma." in raw
    advance(admin, edict_id, "avaliacao")


def test_reesend_restrito_a_admin(api):
    edict_id, subs = first_edict_with_submissions(api)
    r = api.post(
        f"/submissions/{subs[0]['id']}/reesend_submission",
        json={"text": "x"},
    )
    assert r.status_code == 403


def test_send_accept(admin, smtp_api):
    edict_id, subs = first_edict_with_submissions(admin)
    advance(admin, edict_id, "avaliacao")
    sub = _aprovada_com_orientador(admin, edict_id, subs)
    detalhe_edital = get_edict(admin, edict_id)
    if not detalhe_edital.get("accept_form_id"):
        pytest.skip("edital sem formulário de aceite configurado")
    email = admin.get(f"/submissions/{sub['id']}").json()["summary"]["email"]
    r = admin.post(f"/submissions/{sub['id']}/send-accept")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "message" in body and "email_sent" in body
    wait_for_email(smtp_api, lambda m: email in str(m.get("toAddresses", "")))
    # repetir não cria outro envio
    antes = len(smtp_api.get("/api/Messages").json())
    r2 = admin.post(f"/submissions/{sub['id']}/send-accept")
    assert r2.status_code == 400
    time.sleep(2)
    assert len(smtp_api.get("/api/Messages").json()) == antes
    # estado do aceite no detalhe
    summary = admin.get(f"/submissions/{sub['id']}").json()["summary"]
    assert summary["accept"]["sent"] in ("sent", "replied")


def test_send_accept_nao_aprovado_400(admin):
    edict_id, subs = first_edict_with_submissions(admin)
    advance(admin, edict_id, "avaliacao")
    sub = subs[0]
    admin.post(f"/submissions/{sub['id']}/select", json={"stats": "refused", "user_ids": None})
    r = admin.post(f"/submissions/{sub['id']}/send-accept")
    assert r.status_code == 400


def test_send_letter(admin, smtp_api):
    edict_id, subs = first_edict_with_submissions(admin)
    advance(admin, edict_id, "avaliacao")
    sub = _aprovada_com_orientador(admin, edict_id, subs)
    admin.post(f"/submissions/{sub['id']}/entry-semester", json={"semester": "first"})
    email = admin.get(f"/submissions/{sub['id']}").json()["summary"]["email"]
    r = admin.post(f"/submissions/{sub['id']}/send-letter")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "message" in body and "email_sent" in body
    msg = wait_for_email(smtp_api, lambda m: email in str(m.get("toAddresses", "")))
    raw = smtp_api.get(f"/api/Messages/{msg['id']}/raw").text
    assert "html" in raw.lower() or "<" in raw
    summary = admin.get(f"/submissions/{sub['id']}").json()["summary"]
    assert summary["letter_sent"] is True
    # repetir não envia outra carta
    r2 = admin.post(f"/submissions/{sub['id']}/send-letter")
    assert r2.status_code == 400


def test_send_letter_nao_aprovado_400(admin):
    edict_id, subs = first_edict_with_submissions(admin)
    advance(admin, edict_id, "avaliacao")
    sub = subs[0]
    admin.post(f"/submissions/{sub['id']}/select", json={"stats": "refused", "user_ids": None})
    r = admin.post(f"/submissions/{sub['id']}/send-letter")
    assert r.status_code == 400
