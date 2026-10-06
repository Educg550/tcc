import re
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def html():
    path = ROOT / "index.html"
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def css():
    path = ROOT / "style.css"
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def js():
    path = ROOT / "app.js"
    return path.read_text(encoding="utf-8")


def _extract_labels(html_text):
    matches = []
    for tag_match in re.finditer(r"<label\b[^>]*>(.*?)</label>", html_text, re.S | re.I):
        inner = tag_match.group(1)
        inner = re.sub(r"<[^>]+>", " ", inner)
        text = " ".join(inner.split())
        matches.append(text)
    return matches


@pytest.fixture(scope="session")
def labels(html):
    return _extract_labels(html)
