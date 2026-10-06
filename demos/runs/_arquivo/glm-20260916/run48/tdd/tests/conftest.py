import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import app  # noqa: E402


@pytest.fixture()
def cliente():
    with TestClient(app) as cliente_teste:
        yield cliente_teste
