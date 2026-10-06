import sys
from pathlib import Path

import pytest

# A raiz do projeto precisa estar no sys.path para importar a aplicação (app:app).
RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from fastapi.testclient import TestClient

from app import app


@pytest.fixture()
def client():
    return TestClient(app)
