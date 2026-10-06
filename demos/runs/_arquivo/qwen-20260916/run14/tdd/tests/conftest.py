import sys
from pathlib import Path

from fastapi.testclient import TestClient
from app import app

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _client():
    return TestClient(app)


client = _client()
