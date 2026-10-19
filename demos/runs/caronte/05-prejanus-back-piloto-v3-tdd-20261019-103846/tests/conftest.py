import os

import pytest
import httpx


def _base_url(var):
    url = os.environ.get(var)
    if not url:
        pytest.skip(f"variável de ambiente {var} não definida")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def api():
    """Instância local (APP_ENV=local, DEV_USER_ID=2, docente)."""
    with httpx.Client(base_url=_base_url("CARONTE_API"), timeout=60) as client:
        yield client


@pytest.fixture(scope="session")
def api_sem_atalho():
    """Instância fora do ambiente local, sem sessão."""
    with httpx.Client(base_url=_base_url("CARONTE_API_SEM_ATALHO"), timeout=60) as client:
        yield client


@pytest.fixture(scope="session")
def current_user(api):
    resp = api.get("/auth/login")
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture(scope="session")
def any_edict(api):
    resp = api.get("/edicts")
    assert resp.status_code == 200, resp.text
    edicts = resp.json()
    assert edicts, "nenhum edital cadastrado"
    return edicts[0]


@pytest.fixture(scope="session")
def edict_with_submissions(api):
    resp = api.get("/edicts")
    assert resp.status_code == 200, resp.text
    for edict in resp.json():
        sub = api.get(f"/edicts/{edict['id']}/submissions")
        assert sub.status_code == 200, sub.text
        if sub.json().get("submissions"):
            return edict
    pytest.skip("nenhum edital com inscrições")


@pytest.fixture(scope="session")
def any_submission(api, edict_with_submissions):
    resp = api.get(f"/edicts/{edict_with_submissions['id']}/submissions")
    return resp.json()["submissions"][0]
