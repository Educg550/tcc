import re

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_js_sem_fonte_externa():
    js = client.get("/app.js").text
    assert "http://" not in js
    assert "https://" not in js


def test_css_sem_fonte_externa():
    css = client.get("/style.css").text
    assert "@import" not in css
    assert re.search(r"#1094ab", css, re.IGNORECASE)
    assert re.search(r"#64c4d2", css, re.IGNORECASE)
    assert re.search(r"#fcb421", css, re.IGNORECASE)
    assert "font-family" in css
