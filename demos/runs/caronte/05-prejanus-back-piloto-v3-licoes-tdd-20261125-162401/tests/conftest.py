import os
import time
import uuid

import httpx
import pytest


def _client(var):
    url = os.environ.get(var)
    if not url:
        pytest.skip(f"variável de ambiente {var} não definida")
    return httpx.Client(base_url=url.rstrip("/"), timeout=60)


def release(client):
    client.close()


@pytest.fixture
def api():
    c = _client("CARONTE_API")
    yield c
    release(c)


@pytest.fixture
def admin():
    c = _client("CARONTE_API_ADMIN")
    yield c
    release(c)


@pytest.fixture
def outro():
    c = _client("CARONTE_API_OUTRO")
    yield c
    release(c)


@pytest.fixture
def secretaria():
    c = _client("CARONTE_API_SECRETARIA")
    yield c
    release(c)


@pytest.fixture
def coordenador():
    c = _client("CARONTE_API_COORDENADOR")
    yield c
    release(c)


@pytest.fixture
def estudante():
    c = _client("CARONTE_API_ESTUDANTE")
    yield c
    release(c)


@pytest.fixture
def sem_atalho():
    c = _client("CARONTE_API_SEM_ATALHO")
    yield c
    release(c)


@pytest.fixture
def smtp_api():
    c = _client("CARONTE_SMTP_API")
    yield c
    release(c)


def unique_title(prefix="Edital"):
    return f"{prefix} {uuid.uuid4().hex[:10]}"


def make_edict(client, **overrides):
    """Cria um edital válido com datas em ordem cronológica estrita."""
    payload = {
        "title": unique_title(),
        "description": "Edital de teste",
        "year": 2027,
        "semester": 1,
        "edict_type": "mestrado",
        "is_open": True,
        "candidate_forms": 1,
        "recommenders_forms": 2,
        "date_application": "2027-01-01T00:00:00",
        "date_verification": "2027-02-01T00:00:00",
        "date_evaluation": "2027-03-01T00:00:00",
        "date_closed": "2027-04-01T00:00:00",
    }
    payload.update(overrides)
    r = client.post("/edicts", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def get_edict(client, edict_id):
    r = client.get(f"/edicts/{edict_id}")
    assert r.status_code == 200, r.text
    return r.json()


def phase_id(edict, name):
    for p in edict["phases"]:
        if p["phase"] == name:
            return p["id"]
    raise AssertionError(f"fase {name} não encontrada: {edict['phases']}")


def advance(client, edict_id, phase_name):
    edict = get_edict(client, edict_id)
    r = client.post(
        f"/edicts/{edict_id}/advance-phase", json={"id": phase_id(edict, phase_name)}
    )
    assert r.status_code == 200, r.text
    return r.json()


def first_edict_with_submissions(client):
    for e in client.get("/edicts").json():
        r = client.get(f"/edicts/{e['id']}/submissions")
        assert r.status_code == 200, r.text
        if r.json()["submissions"]:
            return e["id"], r.json()["submissions"]
    pytest.skip("nenhum edital com inscrições no conjunto de dados")


def smtp_messages(smtp):
    r = smtp.get("/api/Messages")
    assert r.status_code == 200, r.text
    return r.json()


def wait_for_email(smtp, predicate, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for m in smtp_messages(smtp):
            if predicate(m):
                return m
        time.sleep(1)
    raise AssertionError("e-mail esperado não recebido no SMTP")
