import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _estatico(nome):
    return (RAIZ / nome).read_text(encoding="utf-8")


def test_frontend_escrito_a_mao():
    for nome in ("index.html", "style.css", "app.js"):
        assert (RAIZ / nome).is_file(), f"faltando: {nome}"


def test_sem_recurso_externo():
    for nome in ("index.html", "style.css", "app.js"):
        texto = _estatico(nome).lower()
        assert "http://" not in texto, f"{nome} referencia http://"
        assert "https://" not in texto, f"{nome} referencia https://"
        assert "//cdn" not in texto, f"{nome} referencia CDN"


def test_html_contem_elementos_da_interface():
    html = _estatico("index.html")
    assert "index.html" not in html.replace('href="index.html"', "")
    assert 'src="app.js"' in html
    assert 'src="style.css"' in html or "style.css" in html
    assert "usp-logo.png" in html
    assert "Universidade de São Paulo" in html
    assert "alunos" in html.lower() and "docentes" in html.lower()
    assert "ENVIAR SOLICITAÇÃO" in html.upper()
