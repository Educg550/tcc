import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def test_app_js_existe():
    p = RAIZ / "app.js"
    assert p.exists(), "app.js deve existir na raiz do projeto (frontend estático)"


def test_style_css_existe():
    p = RAIZ / "style.css"
    assert p.exists(), "style.css deve existir na raiz do projeto (frontend estático)"


def test_index_html_existe():
    p = RAIZ / "index.html"
    assert p.exists(), "index.html deve existir na raiz do projeto (frontend estático)"


def test_js_sem_cdn_ou_fonte_remota():
    for nome in ("app.js", "index.html", "style.css"):
        conteudo = (RAIZ / nome).read_text(encoding="utf-8")
        assert "https://" not in conteudo, f"{nome} não deve referenciar recursos externos"


def test_js_contem_formatadores_esperados():
    conteudo = (RAIZ / "app.js").read_text(encoding="utf-8")
    # formatacao de moeda brasileira
    assert ("R$" in conteudo) or ("toLocaleString" in conteudo) or ("Intl.NumberFormat" in conteudo)
    # formatacao de cpf, cep e data
    for trecho in ("CPF", "CEP", "nascimento"):
        assert trecho.lower() in conteudo.lower()
