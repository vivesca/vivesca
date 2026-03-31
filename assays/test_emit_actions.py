from __future__ import annotations
"""Tests for emit enzyme helpers and dispatch."""


import re

import pytest


def test_today_iso_format():
    """_today_iso returns YYYY-MM-DD string."""
    from metabolon.enzymes.emit import _today_iso

    result = _today_iso()
    assert re.match(r"\d{4}-\d{2}-\d{2}", result)


def test_append_to_file(tmp_path):
    """_append_to_file creates parent dirs and appends content."""
    from metabolon.enzymes.emit import _append_to_file

    target = str(tmp_path / "subdir" / "test.md")
    _append_to_file(target, "line one\n")
    _append_to_file(target, "line two\n")
    content = open(target).read()
    assert "line one" in content
    assert "line two" in content


def test_emit_tool_exists():
    """Verify the emit tool function is importable and callable."""
    from metabolon.enzymes.emit import emit

    assert callable(emit)


def test_emit_unknown_action():
    """emit handles unknown actions with EffectorResult."""
    from metabolon.enzymes.emit import emit

    result = emit(action="nonexistent_action_xyz")
    assert hasattr(result, "success")
    assert result.success is False
    assert "Unknown action" in result.message
