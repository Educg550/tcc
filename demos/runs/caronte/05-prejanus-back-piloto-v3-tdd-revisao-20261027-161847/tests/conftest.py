import os
import uuid
from datetime import date, timedelta

import httpx
import pytest


def _client(var):
    url = os.environ.get(var)
    if not url:
        pytest.skip(f"environment variable {var} is not set")
    return httpx.Client(base_url=url.rstrip("/"), timeout=120, verify=False)


@pytest.fixture
def api():
    return _client("CARONTE_API")


@pytest.fixture
def admin():
    return _client("CARONTE_API_ADMIN")


@pytest.fixture
def outro():
    return _client("CARONTE_API_OUTRO")


@pytest.fixture
def secretaria():
    return _client("CARONTE_API_SECRETARIA")


@pytest.fixture
def coordenador():
    return _client("CARONTE_API_COORDENADOR")


@pytest.fixture
def estudante():
    return _client("CARONTE_API_ESTUDANTE")


@pytest.fixture
def senhaunica():
    return _client("CARONTE_API_SENHAUNICA")


@pytest.fixture
def sem_atalho():
    return _client("CARONTE_API_SEM_ATALHO")


@pytest.fixture
def smtp():
    return _client("CARONTE_SMTP_API")


@pytest.fixture
def provedor():
    return _client("SENHAUNICA_PROVEDOR")


def _dates():
    base = date.today()
    fmt = lambda d: f"{d.isoformat()}T12:00:00"
    return {
        "date_application": fmt(base + timedelta(days=1)),
        "date_verification": fmt(base + timedelta(days=2)),
        "date_evaluation": fmt(base + timedelta(days=3)),
        "date_closed": fmt(base + timedelta(days=4)),
    }


@pytest.fixture
def make_edict(admin):
    def _make(**overrides):
        forms = admin.get("/forms").json()
        assert forms, "fixture data must provide forms"
        payload = {
            "title": f"Edital teste {uuid.uuid4().hex[:8]}",
            "description": "Descricao do edital de teste",
            "year": 2027,
            "semester": 1,
            "edict_type": "mestrado",
            "is_open": True,
            "candidate_forms": forms[0]["id"],
            "recommenders_forms": forms[1]["id"] if len(forms) > 1 else forms[0]["id"],
        }
        payload.update(_dates())
        payload.update(overrides)
        r = admin.post("/edicts", json=payload)
        assert r.status_code == 200, r.text
        return r.json()

    return _make


@pytest.fixture
def edict(make_edict):
    return make_edict()


def _phase_id(admin, edict_id, label):
    detail = admin.get(f"/edicts/{edict_id}").json()
    return next(p["id"] for p in detail["phases"] if p["phase"] == label)


@pytest.fixture
def phase_id(admin):
    return lambda edict_id, label: _phase_id(admin, edict_id, label)


@pytest.fixture
def advance_phase(admin):
    def _advance(edict_id, label):
        r = admin.post(f"/edicts/{edict_id}/advance-phase", json={"id": _phase_id(admin, edict_id, label)})
        assert r.status_code == 200, r.text
        return r.json()

    return _advance


def _find_submission(client):
    for e in client.get("/edicts").json():
        r = client.get(f"/edicts/{e['id']}/submissions")
        assert r.status_code == 200, r.text
        subs = r.json()["submissions"]
        if subs:
            return e, subs[0]
    pytest.fail("fixture data must contain at least one submission")


@pytest.fixture
def submission_ctx(admin):
    """Edital e inscricao pre-existentes, com a fase avancada para avaliacao."""
    edict, sub = _find_submission(admin)
    r = admin.post(
        f"/edicts/{edict['id']}/advance-phase",
        json={"id": _phase_id(admin, edict["id"], "avaliacao")},
    )
    assert r.status_code == 200, r.text
    return edict, sub


@pytest.fixture
def smtp_messages(smtp):
    def _messages():
        r = smtp.get("/api/Messages")
        assert r.status_code == 200, r.text
        return r.json()

    return _messages
