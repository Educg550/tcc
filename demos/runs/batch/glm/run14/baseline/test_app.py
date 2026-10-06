import re
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import FILES_MANIFEST, ZIP_PATH, app

client = TestClient(app)


def test_healthz() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_files_manifest() -> None:
    response = client.get("/files")
    assert response.status_code == 200
    entries = response.json()["entries"]
    assert [entry["path"] for entry in entries] == FILES_MANIFEST
    assert {entry["type"] if "type" in entry else "file" for entry in entries} == {"file"}


def test_read_known_file() -> None:
    response = client.get("/files/qc_core/codecs/rle.py")
    assert response.status_code == 200
    text = response.text
    assert "def " in text


def test_read_unknown_file() -> None:
    response = client.get("/files/qc_core/does_not_exist.py")
    assert response.status_code == 404


def test_index_served() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Quantum Codecs" in response.text


def test_zip_download() -> None:
    response = client.get("/deploy/zip")
    assert response.status_code == 200
    with zipfile.ZipFile(__import__("io").BytesIO(response.content)) as archive:
        names = set(archive.namelist())
    assert set(FILES_MANIFEST).issubset(names)


def test_tarball_download() -> None:
    response = client.get("/deploy/tarball")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/")


def test_bundle_structure() -> None:
    response = client.get("/deploy/bundle")
    assert response.status_code == 200
    data = response.json()
    assert data["root"].endswith("bundle")
    assert "qc.service" in data["files"] or "[Unit]" in data["service"]


def test_stylesheet_present() -> None:
    response = client.get("/style.css")
    assert response.status_code == 200
    assert "#1094ab" in response.text
