"""A pasta assets/ é servida como estáticos."""

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_usp_logo_servida():
    assert client.get("/assets/usp-logo.png").status_code == 200
