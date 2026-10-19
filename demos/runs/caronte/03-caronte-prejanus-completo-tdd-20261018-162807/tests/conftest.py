import os

import httpx
import pytest

BASE_URL = (
    os.environ.get("PREJANUS_BASE_URL")
    or os.environ.get("BACKEND_URL")
    or "http://127.0.0.1:8000"
)

ADMIN_ROLES = {"administrator", "secretary", "coordinator"}


def as_list(data):
    """Extrai uma lista de respostas que podem ser lista ou dict com lista dentro."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                return v
    return []


def contains_value(obj, val):
    if isinstance(obj, dict):
        return any(contains_value(v, val) for v in obj.values())
    if isinstance(obj, list):
        return any(contains_value(v, val) for v in obj)
    return obj == val


def build_payload(client, **over):
    forms = as_list(client.get("/forms").json())
    form_id = forms[0]["id"] if forms else None
    existing = as_list(client.get("/edicts").json())
    edict_type = existing[0].get("edict_type", "mestrado") if existing else "mestrado"
    payload = {
        "title": "Edital Piloto v2",
        "description": "Descricao do edital de teste",
        "year": 2027,
        "semester": 1,
        "edict_type": edict_type,
        "is_open": True,
        "candidate_forms": [form_id] if form_id is not None else [],
        "recommenders_forms": [form_id] if form_id is not None else [],
        "date_application": "2027-01-01",
        "date_evaluation": "2027-02-01",
        "date_verification": "2027-03-01",
        "date_closed": "2027-04-01",
    }
    payload.update(over)
    return payload


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=120) as c:
        r = c.get("/auth/login")
        assert r.status_code == 200, r.text
        yield c


@pytest.fixture()
def anon():
    with httpx.Client(base_url=BASE_URL, timeout=30) as c:
        yield c


@pytest.fixture(scope="session")
def is_admin(client):
    return client.get("/auth/login").json().get("role") in ADMIN_ROLES


@pytest.fixture()
def edict_factory(client):
    created = []

    def make(**over):
        payload = build_payload(client, **over)
        r = client.post("/edicts", json=payload)
        assert r.status_code in (200, 201), r.text
        eid = r.json()["id"]
        created.append(eid)
        return eid

    yield make
    for eid in created:
        try:
            client.delete(f"/edicts/{eid}/remove")
        except httpx.HTTPError:
            pass


@pytest.fixture(scope="session")
def submission_ctx(client):
    """Um par (edital, candidatura) com dados existentes no ambiente."""
    for e in as_list(client.get("/edicts").json()):
        r = client.get(f"/edicts/{e['id']}/submissions")
        if r.status_code != 200:
            continue
        subs = r.json().get("submissions") or []
        if subs:
            return e, subs[0]
    return None, None
