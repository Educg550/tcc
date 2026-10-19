import os

import httpx
import pytest

BASE = os.environ.get("CARONTE_API", "http://localhost:8083")
BASE_SEM = os.environ.get("CARONTE_API_SEM_ATALHO")


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE, timeout=60) as c:
        # garante o cookie de sessao do atalho local, se houver
        try:
            c.get("/auth/login")
        except Exception:
            pass
        yield c


@pytest.fixture(scope="session")
def client_noauth():
    if not BASE_SEM:
        pytest.skip("CARONTE_API_SEM_ATALHO nao configurada")
    with httpx.Client(base_url=BASE_SEM, timeout=60) as c:
        yield c


def get_edicts(client):
    r = client.get("/edicts")
    assert r.status_code == 200, r.text
    return r.json()


def edict_detail(client, edict_id):
    r = client.get(f"/edicts/{edict_id}")
    assert r.status_code == 200, r.text
    return r.json()


def submissions_of(client, edict_id, **params):
    r = client.get(f"/edicts/{edict_id}/submissions", params=params)
    assert r.status_code == 200, r.text
    return r.json()["submissions"]


def find_edict(client, phase=None, with_submissions=False):
    for e in get_edicts(client):
        d = edict_detail(client, e["id"])
        if phase is not None and d.get("phase") != phase:
            continue
        if with_submissions and not submissions_of(client, e["id"]):
            continue
        return d
    return None


def items(maybe):
    """Normaliza resposta que pode ser lista ou {'comments': [...]} etc."""
    if isinstance(maybe, list):
        return maybe
    if isinstance(maybe, dict):
        for v in maybe.values():
            if isinstance(v, list):
                return v
    return []
