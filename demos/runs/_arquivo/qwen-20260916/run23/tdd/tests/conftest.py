import sys
import pathlib
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


@pytest.fixture
def client():
    from app import app

    return TestClient(app)
