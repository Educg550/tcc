import os

import httpx
import pytest


def _base(varname):
    url = os.environ.get(varname)
    if not url:
        pytest.fail(f"variável de ambiente {varname} não definida")
    return url.rstrip("/")


def _client(varname):
    return httpx.Client(base_url=_base(varname), timeout=30)


@pytest.fixture
def api():
    c = _client("CARONTE_API")
    yield c
    c.close()


@pytest.fixture
def api_admin():
    c = _client("CARONTE_API_ADMIN")
    yield c
    c.close()


@pytest.fixture
def api_outro():
    c = _client("CARONTE_API_OUTRO")
    yield c
    c.close()


@pytest.fixture
def api_secretaria():
    c = _client("CARONTE_API_SECRETARIA")
    yield c
    c.close()


@pytest.fixture
def api_coordenador():
    c = _client("CARONTE_API_COORDENADOR")
    yield c
    c.close()


@pytest.fixture
def api_estudante():
    c = _client("CARONTE_API_ESTUDANTE")
    yield c
    c.close()


@pytest.fixture
def api_sem_atalho():
    c = _client("CARONTE_API_SEM_ATALHO")
    yield c
    c.close()


@pytest.fixture
def api_senhaunica():
    c = _client("CARONTE_API_SENHAUNICA")
    yield c
    c.close()


@pytest.fixture
def smtp_api():
    c = _client("CARONTE_SMTP_API")
    yield c
    c.close()


def _form_ids(client):
    data = client.get("/forms").json()
    if isinstance(data, dict):
        for key in ("forms", "data", "items"):
            if key in data:
                data = data[key]
                break
        else:
            data = list(data.values())[0]
    return [f["id"] for f in data]


def _create_edict(client, title="Edital de teste"):
    ids = _form_ids(client)
    payload = {
        "title": title,
        "description": "Descrição do edital de teste",
        "year": 2026,
        "semester": 1,
        "edict_type": "mestrado",
        "is_open": True,
        "candidate_forms": ids[0],
        "recommenders_forms": ids[-1],
        "date_application": "2026-01-01T00:00:00",
        "date_verification": "2026-02-01T00:00:00",
        "date_evaluation": "2026-03-01T00:00:00",
        "date_closed": "2026-04-01T00:00:00",
    }
    resp = client.post("/edicts", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture
def novo_edital(api_admin):
    edict = _create_edict(api_admin)
    yield edict
    api_admin.delete(f"/edicts/{edict['id']}/remove")


@pytest.fixture
def edital_com_submissao(api):
    """Edital existente na base que já possui submissões, e a primeira delas."""
    for edict in api.get("/edicts").json():
        resp = api.get(f"/edicts/{edict['id']}/submissions")
        if resp.status_code != 200:
            continue
        submissions = resp.json().get("submissions", [])
        if submissions:
            return edict, submissions[0]
    pytest.fail("a base de dados não possui editais com submissões")
