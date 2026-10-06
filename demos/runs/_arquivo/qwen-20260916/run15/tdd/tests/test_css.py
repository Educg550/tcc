import re

import pytest


@pytest.mark.parametrize("color", ["#1094ab", "#64c4d2", "#fcb421"])
def test_color_defined(css, color):
    assert color.lower() in css.lower()


def test_font_family(css):
    assert re.search(r"Open\s+Sans|sans-serif", css, re.I) is not None


def test_oficio_preserves_lines(css):
    assert "white-space" in css.lower()
    assert re.search(r"pre-wrap|pre-line", css, re.I) is not None


def test_no_remote_css(css):
    assert "@import" not in css.lower()
    assert "http://" not in css.lower()
    assert "https://" not in css.lower()
