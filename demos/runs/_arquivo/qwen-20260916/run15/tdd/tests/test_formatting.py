import re

import pytest


@pytest.mark.parametrize(
    "regex, sample",
    [
        (r"1\s*\)\s*;?\s*\}\s*return\s*'\$\s*'\s*\+", None),
        (r"3\s*\)\s*;?\s*\}\s*return\s*\1", None),
    ],
)
def test_cep_pattern_present(js, regex):
    assert re.search(regex, js) is not None


def test_cpf_cep_date_money_logic(js):
    assert re.search(r"3\s*\)\s*;?\s*\}\s*return\s*", js) is not None
    assert re.search(r"\d\s*\)\s*;?\s*\}\s*return", js) is not None
    assert re.search(r"\.\*\)\s*;?\s*return", js) is not None
    assert re.search(r"2\s*\)\s*;?\s*return\s*", js) is not None
    assert "R$" in js


def test_blur_handler(js):
    assert re.search(r"blur|focusout|change", js, re.I) is not None
