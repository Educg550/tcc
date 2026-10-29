import os

import httpx
import pytest

def pytest_configure(config):

    config.addinivalue_line("markers", "req(*ids): requisitos de requisitos.md verificados pelo teste")


@pytest.fixture(scope="session")
def api():
    with httpx.Client(base_url=os.environ.get("CARONTE_API", "http://localhost:8093"), timeout=30) as c:
        yield c


@pytest.fixture(scope="session")
def api_sem_atalho():
    with httpx.Client(base_url=os.environ.get("CARONTE_API_SEM_ATALHO", "http://localhost:8094"), timeout=30) as c:
        yield c
