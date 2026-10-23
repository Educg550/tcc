import os

import httpx
import pytest


@pytest.fixture(scope="session")
def api():
    base = os.environ["CARONTE_API"]
    with httpx.Client(base_url=base, timeout=60) as client:
        yield client


@pytest.fixture(scope="session")
def api_noauth():
    base = os.environ.get("CARONTE_API_SEM_ATALHO")
    if not base:
        pytest.skip("CARONTE_API_SEM_ATALHO não definido")
    with httpx.Client(base_url=base, timeout=60) as client:
        yield client


def all_edicts(api):
    resp = api.get("/edicts")
    assert resp.status_code == 200
    return resp.json()


def edict_detail(api, edict_id):
    resp = api.get(f"/edicts/{edict_id}")
    assert resp.status_code == 200
    return resp.json()


def submissions_of(api, edict_id):
    resp = api.get(f"/edicts/{edict_id}/submissions")
    assert resp.status_code == 200
    return resp.json()["submissions"]


def any_submission(api):
    """Retorna (edict, submission) de qualquer edital com inscrições."""
    for edict in all_edicts(api):
        subs = submissions_of(api, edict["id"])
        if subs:
            return edict_detail(api, edict["id"]), subs[0]
    return None, None


def submission_in_phase(api, phase):
    for edict in all_edicts(api):
        detail = edict_detail(api, edict["id"])
        if detail.get("phase") != phase:
            continue
        subs = submissions_of(api, edict["id"])
        if subs:
            return detail, subs[0]
    return None, None


def walk_file_fields(node):
    """Percorre o submission_form e devolve (label, filename) de campos File."""
    if isinstance(node, dict):
        if node.get("type") == "File":
            value = node.get("value")
            if isinstance(value, str) and value:
                label = node.get("name") or node.get("label")
                if label:
                    yield label, value
        for child in node.values():
            yield from walk_file_fields(child)
    elif isinstance(node, list):
        for child in node:
            yield from walk_file_fields(child)
