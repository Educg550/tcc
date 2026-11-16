import json
import os

import pytest


@pytest.fixture(scope="module")
def openapi_original():
    path = os.path.join(os.path.dirname(__file__), "..", "infra", "openapi-original.json")
    with open(path) as f:
        return json.load(f)


def test_openapi_do_backend_cobre_todas_as_rotas(api, openapi_original):
    resp = api.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    atual = resp.json()

    for caminho, metodos in openapi_original["paths"].items():
        assert caminho in atual["paths"], f"rota ausente: {caminho}"
        for metodo in metodos:
            assert metodo in atual["paths"][caminho], (
                f"método ausente: {metodo.upper()} {caminho}"
            )


def test_root_responde(api):
    resp = api.get("/")
    assert resp.status_code == 200, resp.text
