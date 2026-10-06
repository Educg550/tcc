import re

import pytest


def test_fetch_to_backend(js):
    assert re.search(r"fetch\s*\(\s*['\"`]/solicitacao", js) is not None


def test_display_oficio_error_js(js):
    assert "oficio" in js.lower()
    assert "erro" in js.lower()


def test_tab_switching_js(js):
    assert re.search(r"ALUNOS", js) is not None
    assert re.search(r"DOCENTES", js) is not None
