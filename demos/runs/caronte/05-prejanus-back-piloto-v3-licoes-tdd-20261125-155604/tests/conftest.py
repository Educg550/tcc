import os

import pytest
import httpx


def _client(env_var):
    url = os.environ.get(env_var)
    if not url:
        pytest.skip(f"variável {env_var} não definida")
    return httpx.Client(base_url=url.rstrip("/"), timeout=30)


@pytest.fixture
def api():
    c = _client("CARONTE_API")
    yield c
    c.close()


@pytest.fixture
def admin():
    c = _client("CARONTE_API_ADMIN")
    yield c
    c.close()


@pytest.fixture
def outro():
    c = _client("CARONTE_API_OUTRO")
    yield c
    c.close()


@pytest.fixture
def secretaria():
    c = _client("CARONTE_API_SECRETARIA")
    yield c
    c.close()


@pytest.fixture
def coordenador():
    c = _client("CARONTE_API_COORDENADOR")
    yield c
    c.close()


@pytest.fixture
def estudante():
    c = _client("CARONTE_API_ESTUDANTE")
    yield c
    c.close()


@pytest.fixture
def sem_atalho():
    c = _client("CARONTE_API_SEM_ATALHO")
    yield c
    c.close()


@pytest.fixture
def senhaunica():
    c = _client("CARONTE_API_SENHAUNICA")
    yield c
    c.close()


@pytest.fixture
def smtp_api():
    url = os.environ.get("CARONTE_SMTP_API")
    if not url:
        pytest.skip("variável CARONTE_SMTP_API não definida")
    c = httpx.Client(base_url=url.rstrip("/"), timeout=30)
    yield c
    c.close()


@pytest.fixture
def provedor():
    url = os.environ.get("SENHAUNICA_PROVEDOR")
    if not url:
        pytest.skip("variável SENHAUNICA_PROVEDOR não definida")
    c = httpx.Client(base_url=url.rstrip("/"), timeout=30)
    yield c
    c.close()


def smtp_messages(smtp_api):
    return smtp_api.get("/api/Messages").json()


def smtp_raw(smtp_api, message_id):
    r = smtp_api.get(f"/api/Messages/{message_id}/raw")
    return r.content.decode("utf-8", errors="replace")


def find_form(client, tag_year=None, tag_notice=None):
    """Retorna um formulário do Forms conforme filtros de tags Ano/Edital."""
    params = {}
    if tag_year:
        params["year"] = tag_year
    if tag_notice:
        params["notice"] = tag_notice
    forms = client.get("/forms", params=params).json()
    assert forms, "nenhum formulário encontrado"
    return forms[0]


def create_edict(client, form_id, recommender_form_id, **overrides):
    payload = {
        "title": "Edital de teste",
        "description": "Descrição do edital de teste",
        "year": 2026,
        "semester": 1,
        "edict_type": "mestrado",
        "is_open": True,
        "candidate_forms": form_id,
        "recommenders_forms": recommender_form_id,
        "date_application": "2026-01-01T00:00:00",
        "date_verification": "2026-02-01T00:00:00",
        "date_evaluation": "2026-03-01T00:00:00",
        "date_closed": "2026-04-01T00:00:00",
    }
    payload.update(overrides)
    r = client.post("/edicts", json=payload)
    assert r.status_code == 200, r.text
    return r.json()


def first_submission(client, edict_id):
    r = client.get(f"/edicts/{edict_id}/submissions")
    assert r.status_code == 200, r.text
    subs = r.json()["submissions"]
    assert subs, "nenhuma inscrição no edital"
    return subs[0]


def advance_phase(client, edict_id, phase_name):
    detail = client.get(f"/edicts/{edict_id}").json()
    phase = next(p for p in detail["phases"] if p["phase"] == phase_name)
    r = client.post(f"/edicts/{edict_id}/advance-phase", json={"id": phase["id"]})
    assert r.status_code == 200, r.text
    return r.json()
