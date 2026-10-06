import re

import pytest

HEADER = [
    "Universidade de São Paulo",
    "assets/usp-logo.png",
]

def test_html_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "<!doctype html" in r.text.lower()



def test_institutional_header(html):
    for t in HEADER:
        assert t in html, t


def test_no_remote_assets(html, css, js):
    for src, text in [("html", html), ("css", css), ("js", js)]:
        assert "http://" not in text and "https://" not in text, src
