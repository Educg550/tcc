import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest


@pytest.fixture()
def cliente():
    from fastapi.testclient import TestClient

    from app import app

    return TestClient(app)
