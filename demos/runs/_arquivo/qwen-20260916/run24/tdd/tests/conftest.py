import os
import sys

import pytest

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from fastapi.testclient import TestClient
from app import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)
