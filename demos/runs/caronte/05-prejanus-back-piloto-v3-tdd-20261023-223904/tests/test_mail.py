import pytest

from tests.utils import edicts_with_submissions, smtp_find


def _approved_submission(admin):
    for eid, subs in edicts_with_submissions(admin):
        for s in subs:
            if s["stats"] == "approved":
                return eid, s
    eid, subs = edicts_with_submissions(admin)[0]
    r = admin.post(
        f"/submissions/{subs[0]['id']}/select",
        json={"stats": "approved", "user_ids": [2]},
    )
    assert r.status_code == 200, r.text
    return eid, subs[0]


def _avaliacao(admin):
    found = edicts_with_submissions(admin)
    assert found
    eid, subs = found[0]
    detail = admin.get(f"/edicts/{eid}").json()
    if detail["phase"] != "avaliacao":
        phase = next(p for p in detail["phases"] if p["phase"] == "avaliacao")
        r = admin.post(f"/edicts/{eid}/advance-phase", json={"id": phase["id"]})
        assert r.status_code == 200, r.text
    return eid, subs


def test_reesend_submission(api, admin, smtp):
    eid, subs = _avaliacao(admin)
    detail = admin.get(f"/edicts/{eid}").json()
    if detail["phase"] != "homologacao":
        phase = next(p for p in detail["phases"] if p["phase"] == "homologacao")
        r = admin.post(f"/edicts/{eid}/advance-phase", json={"id": phase["id"]})
        assert r.status_code == 200, r.text

    sid = subs[0]["id"]
    r = api.post(f"/submissions/{sid}/reesend_submission", json={"text": "corrija"})
    assert r.status_code == 403

    r = admin.post(
        f"/submissions/{sid}/reesend_submission",
        json={"text": "Por favor corrija o documento."},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["message"]
    assert body["email_sent"]

    found = smtp_find(
        smtp,
        lambda m, raw: subs[0]["email"] in (m.get("toAddress") or "")
        and "/form/" in raw,
    )
    assert found, "e-mail de correcao nao recebido no SMTP"


def test_send_accept(admin, smtp):
    eid, sub = _approved_submission(admin)
    sid = sub["id"]
    r = admin.post(f"/submissions/{sid}/send-accept")
    assert r.status_code in (200, 400), r.text

    summary = admin.get(f"/submissions/{sid}").json()["summary"]
    accept = None
    for value in (summary.get("accept"), summary):
        if isinstance(value, dict) and "sent" in value:
            accept = value
    if r.status_code == 200:
        body = r.json()
        assert body["message"] and body["email_sent"]
        assert accept and accept["sent"] in ("sent", "replied")
        found = smtp_find(
            smtp,
            lambda m, raw: sub["email"] in (m.get("toAddress") or "")
            and "/form/" in raw,
        )
        assert found, "convite de aceite nao recebido no SMTP"
        # repetir nao cria outro envio
        r2 = admin.post(f"/submissions/{sid}/send-accept")
        assert r2.status_code == 400
    else:
        assert accept and accept["sent"] in ("sent", "replied")


def test_send_letter(admin, smtp):
    _eid, sub = _approved_submission(admin)
    sid = sub["id"]
    r = admin.post(f"/submissions/{sid}/send-letter")
    assert r.status_code in (200, 400), r.text

    if r.status_code == 200:
        body = r.json()
        assert body["message"] and body["email_sent"]
        found = smtp_find(
            smtp,
            lambda m, raw: sub["email"] in (m.get("toAddress") or "")
            and sub["name"].split()[0] in raw,
        )
        assert found, "carta de aceite nao recebida no SMTP"
        assert admin.post(f"/submissions/{sid}/send-letter").status_code == 400
    summary = admin.get(f"/submissions/{sid}").json()["summary"]
    assert "letter_sent" in str(summary)
