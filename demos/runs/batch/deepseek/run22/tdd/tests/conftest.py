import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def cliente():
    return TestClient(app)
