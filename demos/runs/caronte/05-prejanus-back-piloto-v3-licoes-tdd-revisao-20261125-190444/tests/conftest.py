import os

import httpx
import pytest


def _client(var: str) -> httpx.Client:
    url = os.environ.get(var)
    if not url:
        pytest.skip(f"variável {var} não definida")
    return httpx.Client(base_url=url.rstrip("/"), timeout=60)


def _make_fixture(var: str):
    @pytest.fixture(scope="session")
    def fixture():
        client = _client(var)
        yield client
        client.close()

    return fixture


api = _make_fixture("CARONTE_API")
api_admin = _make_fixture("CARONTE_API_ADMIN")
api_outro = _make_fixture("CARONTE_API_OUTRO")
api_secretaria = _make_fixture("CARONTE_API_SECRETARIA")
api_coordenador = _make_fixture("CARONTE_API_COORDENADOR")
api_estudante = _make_fixture("CARONTE_API_ESTUDANTE")
api_senhaunica = _make_fixture("CARONTE_API_SENHAUNICA")
api_sem_atalho = _make_fixture("CARONTE_API_SEM_ATALHO")
smtp_api = _make_fixture("CARONTE_SMTP_API")
smtp = _make_fixture("CARONTE_SMTP_API")
provedor = _make_fixture("SENHAUNICA_PROVEDOR")


@pytest.fixture(scope="session")
def form_id(api_admin):
    r = api_admin.get("/forms")
    assert r.status_code == 200, r.text
    forms = r.json()
    assert isinstance(forms, list) and forms, "nenhum formulário disponível"
    return forms[0]["id"]


@pytest.fixture(scope="session")
def edict_id(api_admin, form_id):
    """Cria um edital próprio dos testes, com datas em ordem cronológica."""
    payload = {
        "title": "Edital de teste pytest",
        "description": "Descrição do edital de teste",
        "year": 2031,
        "semester": 1,
        "edict_type": "mestrado",
        "is_open": True,
        "candidate_forms": form_id,
        "recommenders_forms": form_id,
        "date_application": "2031-01-01T00:00:00",
        "date_verification": "2031-02-01T00:00:00",
        "date_evaluation": "2031-03-01T00:00:00",
        "date_closed": "2031-04-01T00:00:00",
    }
    r = api_admin.post("/edicts", json=payload)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def find_submission(client):
    """Localiza qualquer inscrição existente no sistema."""
    r = client.get("/edicts")
    assert r.status_code == 200, r.text
    for edict in r.json():
        rs = client.get(f"/edicts/{edict['id']}/submissions")
        assert rs.status_code == 200, rs.text
        subs = rs.json()["submissions"]
        if subs:
            return edict["id"], subs[0]["id"]
    pytest.skip("nenhuma inscrição disponível nos dados preparados")


@pytest.fixture(scope="module")
def submission_em_avaliacao_module(api_admin):
    edict_id, submission_id = find_submission(api_admin)
    advance_to(api_admin, edict_id, "avaliacao")
    return edict_id, submission_id


def advance_to(api_admin_client, edict_id, phase_name):
    """Avança o edital até a fase indicada, usando os ids de fase do detalhe."""
    r = api_admin_client.get(f"/edicts/{edict_id}")
    assert r.status_code == 200, r.text
    detail = r.json()
    target = None
    for ph in detail["phases"]:
        if ph["phase"] == phase_name:
            target = ph["id"]
    assert target is not None, f"fase {phase_name} não encontrada"
    ra = api_admin_client.post(
        f"/edicts/{edict_id}/advance-phase", json={"id": target}
    )
    assert ra.status_code == 200, ra.text
    return ra.json()
