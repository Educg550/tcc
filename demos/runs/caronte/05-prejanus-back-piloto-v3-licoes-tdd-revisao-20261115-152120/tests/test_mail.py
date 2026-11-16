import pytest

from helpers import (
    advance,
    create_edict,
    smtp_find,
    smtp_raw_messages,
    submissions_of,
)


def test_solicitar_correcao(admin, api):
    eid = create_edict(admin, "Edital correção")
    subs = submissions_of(admin, eid)
    sid = subs[0]["id"]
    email = subs[0]["email"]

    # fora da fase homologacao
    r0 = admin.post(f"/submissions/{sid}/reesend_submission", json={"text": "corrija"})
    assert r0.status_code == 400, r0.text

    advance(admin, eid, "homologacao")

    # docente não solicita correção
    assert (
        api.post(f"/submissions/{sid}/reesend_submission", json={"text": "corrija"}).status_code
        == 403
    )

    snap = smtp_raw_messages()
    r = admin.post(
        f"/submissions/{sid}/reesend_submission",
        json={"text": "Precisa corrigir o anexo enviado"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "message" in body and "email_sent" in body

    m = smtp_find(to=email, contains="/form/", since=snap)
    assert m, f"e-mail de correção não recebido por {email}"
    assert "Precisa corrigir o anexo enviado" in m["raw"]


def _accept_sent(d):
    accept = d["summary"].get("accept") or {}
    return accept.get("sent")


@pytest.fixture(scope="module")
def accepted(admin):
    """Aprova uma candidatura e envia o formulário de aceite com sucesso."""
    r = admin.get("/edicts", params={"is_open": True})
    assert r.status_code == 200, r.text
    for e in r.json():
        subs = submissions_of(admin, e["id"])
        for s in subs:
            if s["accept"]["sent"] != "not_sent":
                continue
            if s["stats"] not in ("approved", "underreview", "waitlist"):
                continue
            if s["stats"] != "approved":
                rs = admin.post(
                    f"/submissions/{s['id']}/select",
                    json={"stats": "approved", "user_ids": [2]},
                )
                if rs.status_code != 200:
                    continue
            snap = smtp_raw_messages()
            ra = admin.post(f"/submissions/{s['id']}/send-accept")
            if ra.status_code == 200:
                return s, snap
    pytest.fail("nenhum envio de formulário de aceite foi possível")


def test_enviar_formulario_aceite(admin, accepted):
    s, snap = accepted
    ra = admin.post(f"/submissions/{s['id']}/send-accept")
    assert ra.status_code == 200, ra.text
    body = ra.json()
    assert "message" in body and "email_sent" in body

    m = smtp_find(to=s["email"], contains="/form/", since=snap)
    assert m, f"e-mail de aceite não recebido por {s['email']}"

    d = admin.get(f"/submissions/{s['id']}").json()
    assert _accept_sent(d) == "sent"


def test_enviar_carta_aceite(admin, accepted):
    s, _ = accepted
    snap = smtp_raw_messages()
    r = admin.post(f"/submissions/{s['id']}/send-letter")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "message" in body and "email_sent" in body

    m = smtp_find(to=s["email"], since=snap)
    assert m, f"carta de aceite não recebida por {s['email']}"

    d = admin.get(f"/submissions/{s['id']}").json()
    assert d["summary"].get("letter_sent") is True

    # repetir não envia outra carta
    assert admin.post(f"/submissions/{s['id']}/send-letter").status_code == 400


def test_carta_candidato_nao_aprovado_400(admin):
    r = admin.get("/edicts", params={"is_open": True})
    for e in r.json():
        for s in submissions_of(admin, e["id"]):
            if s["stats"] != "approved":
                assert (
                    admin.post(f"/submissions/{s['id']}/send-letter").status_code == 400
                )
                return
    pytest.skip("nenhuma candidatura não aprovada disponível")
