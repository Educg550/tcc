from fastapi.testclient import TestClient


def _cliente():
    from app import app
    return TestClient(app)
