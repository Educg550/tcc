import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app as app_module  # noqa: E402


def client():
    return TestClient(app_module.app)


def texto_de_app_js():
    return (ROOT / "app.js").read_text(encoding="utf-8")


def texto_de_style_css():
    return (ROOT / "style.css").read_text(encoding="utf-8")


def html_da_pagina():
    resposta = client().get("/")
    assert resposta.status_code == 200
    return resposta.text
