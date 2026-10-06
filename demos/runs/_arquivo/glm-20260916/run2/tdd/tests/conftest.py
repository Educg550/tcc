import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="session")
def buscar(client):
    def _buscar(caminho):
        for pasta in ("", "/static"):
            resposta = client.get(pasta + caminho)
            if resposta.status_code == 200:
                return resposta
        return None

    return _buscar
