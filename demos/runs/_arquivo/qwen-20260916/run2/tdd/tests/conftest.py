import json
import os
import re
from typing import Iterator

import pytest

from fastapi.testclient import TestClient

from app import app


ASSET_FILES = {
    "assets/usp-logo.png": (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4" +
        b"\x89\x00\x00\x00\nIDATx\x9ccb\xfa\xff\xff\x7f\x00\x05\xfe\x02\xfe\xdc\xa7\xc9\x81\x00\x00\x00\x00IEND\xaeB`\x82"
    ),
}


@pytest.fixture(scope="session")
def project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    for path, content in ASSET_FILES.items():
        full = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        if not os.path.exists(full):
            with open(full, "wb") as f:
                f.write(content)
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def html(client: TestClient) -> str:
    return client.get("/").text


@pytest.fixture(scope="session")
def css(client: TestClient) -> str:
    return client.get("/static/style.css").text


@pytest.fixture(scope="session")
def js(client: TestClient) -> str:
    return client.get("/static/app.js").text


ID_RE = re.compile(r"\bid\s*=\s*[\"']([^\"']+)[\"']")


def find_tag(html: str, tag: str, attr: str, value: str) -> str:
    for m in re.finditer(r"<" + tag + r"\b[^>]*>", html, flags=re.I):
        text = m.group(0)
        if re.search(r"\b" + attr + r"\s*=\s*[\"']" + re.escape(value) + r"[\"']", text, flags=re.I):
            return text
    raise AssertionError(f"<{tag}> with {attr}={value!r} not found in HTML")


def field_id(html: str, label_text: str) -> str:
    pattern = (
        r"<label\b[^>]*>\s*" + re.escape(label_text) + r"\s*<\/label>\s*" +
        r"(?:<!--[^>]*-->\s*)?<[^>]*\bid\s*=\s*[\"']([^\"']+)[\"']"
    )
    m = re.search(pattern, html, flags=re.I)
    if not m:
        m = re.search(r"<input[^>]*placeholder\s*=\s*[\"']" + re.escape(label_text) + r"[\"']", html, flags=re.I)
        if not m:
            raise AssertionError(f"input for label {label_text!r} not found")
        return ID_RE.search(m.group(0)).group(1)
    return m.group(1)


def label_for(html: str, field_id: str) -> str:
    pattern = r"<label\b[^>]*for\s*=\s*[\"']" + re.escape(field_id) + r"[\"'][^>]*>([^<]*)"
    m = re.search(pattern, html, flags=re.I)
    if not m:
        raise AssertionError(f"label for field {field_id!r} not found")
    return m.group(1).strip()


def _find_form_by_class(html: str, cls: str) -> str:
    start = None
    for m in re.finditer(r"<form\b[^>]*>", html, flags=re.I):
        if re.search(r"class\s*=\s*[\"'][^\"']*" + re.escape(cls) + r"[^\"']*[\"']", m.group(0), flags=re.I):
            start = m.start()
            break
    if start is None:
        raise AssertionError(f"form with class {cls!r} not found")
    i = start
    depth = 0
    tag_re = re.compile(r"</?form\b", flags=re.I)
    for m in tag_re.finditer(html, start):
        if m.group(0).lower().startswith("</"):
            depth -= 1
            if depth == 0:
                return html[start:m.end()]
        else:
            depth += 1
    raise AssertionError(f"form with class {cls!r} not properly closed")


def form_block(html: str, cls: str) -> str:
    return _find_form_by_class(html, cls)


def has_field_in_form(html: str, cls: str, label_text: str) -> bool:
    block = form_block(html, cls)
    pattern = (
        r"<label\b[^>]*>\s*" + re.escape(label_text) + r"\s*<\/label>|" +
        r"<label\b[^>]*for\s*=\s*[\"'][^\"']+[\"'][^>]*>\s*" + re.escape(label_text)
    )
    return bool(re.search(pattern, block, flags=re.I))


def select_options(html: str, label_text: str) -> list[str]:
    fid = field_id(html, label_text)
    m = re.search(
        r"<select[^>]*\bid\s*=\s*[\"']" + re.escape(fid) + r"[\"'][^>]*>(.*?)</select>",
        html,
        flags=re.I | re.S,
    )
    if not m:
        raise AssertionError(f"select {fid!r} not found")
    return [x.strip() for x in re.findall(r"<option[^>]*>([^<]*)</option>", m.group(1), flags=re.I)]
