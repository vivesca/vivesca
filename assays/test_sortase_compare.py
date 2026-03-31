from __future__ import annotations
"""Tests for sortase compare delta indicators."""


from metabolon.sortase.compare import _delta_str


def test_delta_str_increase():
    result = _delta_str(50.0, 75.0)
    assert "↑" in result
    assert "50%" in result


def test_delta_str_decrease():
    result = _delta_str(100.0, 80.0)
    assert "↓" in result
    assert "20%" in result


def test_delta_str_zero_base():
    assert _delta_str(0, 10) == ""


def test_delta_str_no_change():
    result = _delta_str(42.0, 42.0)
    assert "→" in result
    assert "0%" in result
