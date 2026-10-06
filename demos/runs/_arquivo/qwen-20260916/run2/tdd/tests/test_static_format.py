import re

import pytest


def test_format_functions_in_app_js(js):
    for fn in ["formatValor", "formatCpf", "formatCep", "formatData"]:
        assert re.search(r"function\s+" + fn, js), fn
    assert re.search(r"function\s+validateCPF", js)
    assert re.search(r"function\s+validateDate", js)


def test_listeners_registered_in_app_js(js):
    for evt in ["blur", "input"]:
        assert re.search(r"addEventListener\s*\(\s*['\"]" + evt, js), evt


def test_ajax_submit_in_app_js(js):
    assert re.search(r"fetch\s*\(\s*['\"]", js)
    assert re.search(r"\.preventDefault\s*\(\s*\)", js)
