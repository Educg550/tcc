"""Os três arquivos estáticos existem na raiz do projeto."""

from pathlib import Path


def _raiz():
    return Path(__file__).resolve().parent.parent


def test_index_html_existe():
    assert (_raiz() / "index.html").is_file()


def test_style_css_existe():
    assert (_raiz() / "style.css").is_file()


def test_app_js_existe():
    assert (_raiz() / "app.js").is_file()
