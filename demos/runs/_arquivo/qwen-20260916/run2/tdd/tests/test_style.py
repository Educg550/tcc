import re

import pytest


def test_usp_colors(css):
    for color in ["#1094ab", "#64c4d2", "#fcb421"]:
        assert color in css, color


def test_tabs_visual(css):
    m = re.search(r"\.tab\s*\{([^}]+)\}", css)
    assert m, "tab css not found"
    block = m.group(1)
    assert "padding" in block

    m_active = re.search(r"\.tab\.active\s*\{([^}]+)\}", css)
    assert m_active, "tab active css not found"
    active_block = m_active.group(1)
    assert ("font-weight" in active_block or "border" in active_block or "background" in active_block)

    m_inactive = re.search(r"\.tab\s*:\s*not\(\.active\)\s*\{([^}]+)\}", css)
    if m_inactive:
        assert ("opacity" in m_inactive.group(1) or "background" in m_inactive.group(1) or "color" in m_inactive.group(1))


def test_form_layout(css):
    m = re.search(r"\.form\s*\{([^}]+)\}", css)
    assert m
    assert "display" in m.group(1) and "grid" in m.group(1)
    assert re.search(r"grid-template-columns", m.group(1))
    assert re.search(r"gap", m.group(1))


def test_font_family(css):
    m = re.search(r"font-family\s*:\s*([^;]+);", css)
    assert m
    value = m.group(1)
    assert ("Open Sans" in value or re.search(r"-?apple-system", value))
    assert "serif" not in value


def test_no_external(css):
    assert "@import" not in css.lower()


def test_logo_margin(css):
    m = re.search(r"\.logo\s*\{([^}]+)\}", css)
    if not m:
        m = re.search(r"\.header\s*\{([^}]+)\}", css)
    assert m
    block = m.group(1)
    assert "padding" in block or "margin" in block
