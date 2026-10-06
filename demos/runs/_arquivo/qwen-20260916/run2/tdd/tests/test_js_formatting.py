import pytest


def test_formatting_in_js(js):
    assert "maskCep" in js
    assert "maskCpf" in js
    assert "maskData" in js
    assert "maskValor" in js
