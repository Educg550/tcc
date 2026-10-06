from fastapi.testclient import TestClient
from app import app


def pytest_collection_modifyitems(items):
    client = TestClient(app)
    for item in items:
        item.client = client
