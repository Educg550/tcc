"""V2-MAI-01..03 — correcao, formulario de aceite e carta."""
import os
import time

import httpx
import pytest


def _smtp_client():
    url = os.environ["CARONTE_SMTP_API"].rstrip("/")
    return httpx.Client(base_url=url, timeout=60, verify=False)


def _all_messages(c):
    r = c.get("/api/Messages")
    data = r.json()
    if isinstance(data, dict):
        for key in ("messages", "items", "results", "data"):
            if isinstance(data.get(key), list):
                return data[key]
        return []
    return data


def _find_message(to_email, contains=None, timeout=30):
    with _smtp_client() as c:
        deadline = time.time() + timeout
        while time.time() < deadline:
            for m in _all_messages(c):
                if not isinstance(m, dict):
                    continue
                if to_email in str(m.get("to", "")):
                    if contains is None:
                        return m
                    raw = c.get(f"/api/Messages/{m['id']}/raw")
                    if contains in raw.text:
                        return m
            time.sleep(1)
    return None


def test_reesend_submission(admin, submission_ctx, phase_id):
    edict, sub = submission_ctx
    admin.post(f"/edicts/{edict['id']}/advance-phase", json={"id": phase_id(edict["id"], "homologacao")})
    detail = admin.get(f"/submissions/{sub['id']}").json()
    email = detail["summary"]["email"]

    r = admin.post(f"/submissions/{sub['id']}/reesend_submission", json={"text": "Corrigir o anexo"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["message"]
    assert body["email_sent"]

    msg = _find_message(email, contains="Corrigir o anexo")
    assert msg, f"mensagem de correcao nao recebida para {email}"
    with _smtp_client() as c:
        raw = c.get(f"/api/Messages/{msg['id']}/raw").text
    assert "/form/" in raw


def test_reesend_restrito_a_administrativos(api, admin, submission_ctx, phase_id):
    edict, sub = submission_ctx
    admin.post(f"/edicts/{edict['id']}/advance-phase", json={"id": phase_id(edict["id"], "homologacao")})
    r = api.post(f"/submissions/{sub['id']}/reesend_submission", json={"text": "x"})
    assert r.status_code == 403


def _approve(admin, sub_id):
    r = admin.post(f"/submissions/{sub_id}/select", json={"stats": "approved", "user_ids": [2]})
    assert r.status_code == 200, r.text


def _edict_com_aceite(admin):
    """Procura um edital cujo formulario de aceite esteja configurado."""
    for e in admin.get("/edicts").json():
        r = admin.get(f"/edicts/{e['id']}/submissions")
        subs = r.json()["submissions"]
        if not subs:
            continue
        sub = subs[0]
        _approve(admin, sub["id"])
        resp = admin.post(f"/submissions/{sub['id']}/send-accept")
        if resp.status_code == 200:
            return e, sub, resp.json()
    pytest.fail("nenhum edital com formulario de aceite configurado")


def test_send_accept(admin):
    _, sub, body = _edict_com_aceite(admin)
    assert body["message"]
    assert body["email_sent"]

    detail = admin.get(f"/submissions/{sub['id']}").json()
    accept = detail["summary"]["accept"]
    assert accept["sent"] in ("sent", "replied")

    # repetir nao cria outro envio
    r = admin.post(f"/submissions/{sub['id']}/send-accept")
    assert r.status_code == 400


def test_send_accept_nao_aprovado(admin, submission_ctx):
    _, sub = submission_ctx
    admin.post(f"/submissions/{sub['id']}/select", json={"stats": "underreview", "user_ids": None})
    r = admin.post(f"/submissions/{sub['id']}/send-accept")
    assert r.status_code in (400, 404)


def test_send_letter(admin, submission_ctx):
    _, sub = submission_ctx
    _approve(admin, sub["id"])
    detail = admin.get(f"/submissions/{sub['id']}").json()
    email = detail["summary"]["email"]
    name = detail["summary"]["name"]

    r = admin.post(f"/submissions/{sub['id']}/send-letter")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["message"]
    assert body["email_sent"]

    msg = _find_message(email, contains=name)
    assert msg, f"carta nao recebida por {email}"

    assert admin.get(f"/submissions/{sub['id']}").json()["summary"]["letter_sent"] is True
    # repetir nao envia outra carta
    assert admin.post(f"/submissions/{sub['id']}/send-letter").status_code == 400


def test_send_letter_nao_aprovado(admin, submission_ctx):
    _, sub = submission_ctx
    admin.post(f"/submissions/{sub['id']}/select", json={"stats": "refused", "user_ids": None})
    r = admin.post(f"/submissions/{sub['id']}/send-letter")
    assert r.status_code == 400
