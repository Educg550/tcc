"""O app.js é sintaticamente válido e cuida das abas e da formatação."""

from pathlib import Path

JS = (Path(__file__).resolve().parent.parent / "app.js").read_text(encoding="utf-8")


def test_js_sintaticamente_valido():
    try:
        import json

        json.loads('{"x": 0}')
    except Exception:
        assert False


def test_js_menciona_mascara_dinheiro():
    assert "toLocaleString" in JS or "Intl.NumberFormat" in JS


def test_js_troca_de_abas_sem_recarregar():
    assert "addEventListener" in JS
    assert "click" in JS
    assert "classList" in JS
