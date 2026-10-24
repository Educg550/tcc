import os

import pytest

from tests.utils import Client


def _client(var):
    url = os.environ[var].rstrip("/")
    return Client(url)


@pytest.fixture(scope="session")
def api():
    c = _client("CARONTE_API")
    yield c
    c.close()


@pytest.fixture(scope="session")
def admin():
    c = _client("CARONTE_API_ADMIN")
    yield c
    c.close()


@pytest.fixture(scope="session")
def outro():
    c = _client("CARONTE_API_OUTRO")
    yield c
    c.close()


@pytest.fixture(scope="session")
def secretaria():
    c = _client("CARONTE_API_SECRETARIA")
    yield c
    c.close()


@pytest.fixture(scope="session")
def coordenador():
    c = _client("CARONTE_API_COORDENADOR")
    yield c
    c.close()


@pytest.fixture(scope="session")
def estudante():
    c = _client("CARONTE_API_ESTUDANTE")
    yield c
    c.close()


@pytest.fixture(scope="session")
def senhaunica():
    c = _client("CARONTE_API_SENHAUNICA")
    yield c
    c.close()


@pytest.fixture(scope="session")
def sem_atalho():
    c = _client("CARONTE_API_SEM_ATALHO")
    yield c
    c.close()


@pytest.fixture(scope="session")
def smtp():
    return os.environ["CARONTE_SMTP_API"].rstrip("/")


@pytest.fixture(scope="session")
def provedor():
    return os.environ["SENHAUNICA_PROVEDOR"].rstrip("/")
