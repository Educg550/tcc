import os

import httpx
import pytest

API_URL = os.environ.get("CARONTE_API", "http://localhost:8083")
API_NO_SHORTCUT_URL = os.environ.get("CARONTE_API_SEM_ATALHO")


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=API_URL, timeout=60) as c:
        yield c


@pytest.fixture(scope="session")
def no_shortcut_client():
    if not API_NO_SHORTCUT_URL:
        pytest.skip("CARONTE_API_SEM_ATALHO não configurado")
    with httpx.Client(base_url=API_NO_SHORTCUT_URL, timeout=60) as c:
        yield c


def all_edicts(client):
    resp = client.get("/edicts")
    assert resp.status_code == 200
    return resp.json()


def edict_detail(client, edict_id):
    resp = client.get(f"/edicts/{edict_id}")
    assert resp.status_code == 200
    return resp.json()


def find_edict_with_submissions(client, phase=None):
    """Retorna (edital, submissions) para o primeiro edital com candidaturas,
    opcionalmente na fase indicada."""
    for item in all_edicts(client):
        detail = edict_detail(client, item["id"])
        if phase is not None and detail.get("phase") != phase:
            continue
        resp = client.get(f"/edicts/{item['id']}/submissions")
        assert resp.status_code == 200
        subs = resp.json().get("submissions", [])
        if subs:
            return detail, subs
    return None, []


@pytest.fixture(scope="session")
def edict_with_submissions(client):
    detail, subs = find_edict_with_submissions(client)
    if detail is None:
        pytest.skip("nenhum edital com candidaturas no conjunto de dados")
    return detail, subs


@pytest.fixture(scope="session")
def evaluation_edict(client):
    detail, subs = find_edict_with_submissions(client, phase="avaliacao")
    if detail is None:
        pytest.skip("nenhum edital na fase avaliacao com candidaturas")
    return detail, subs
