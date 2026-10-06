"""O CSS define a identidade visual da Universidade."""

from pathlib import Path

CSS = (Path(__file__).resolve().parent.parent / "style.css").read_text(encoding="utf-8")


def test_cores_da_universidade():
    for cor in ("#1094ab", "#64c4d2", "#fcb421"):
        assert cor in CSS


def test_fonte_open_sans():
    assert "Open Sans" in CSS


def test_sem_fonte_remota():
    assert "@import" not in CSS
    assert "http://" not in CSS and "https://" not in CSS


def test_aba_ativa_distinguivel():
    assert ".tab.active" in CSS
