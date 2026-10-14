import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from app import create_app, csrf
import flask_seasurf

def disable_csrf(app):
    print("Desabilitando CSRF nos testes...")
    csrf._disable = True
    for ext in app.extensions.values():
        if isinstance(ext, flask_seasurf.SeaSurf):
            ext._disable = True
            print("CSRF desabilitado!")
            break
    return app

@pytest.fixture()
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    disable_csrf(app)

    return app

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()

def pytest_addoption(parser):
    parser.addoption(
        "--login",
        action="store"
    )
    parser.addoption(
        "--password",
        action="store"
    )

@pytest.fixture
def login(request):
    return request.config.getoption("--login")

@pytest.fixture
def password(request):
    return request.config.getoption("--password")