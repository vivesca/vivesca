"""Tests for ultradian pinocytosis module."""

from __future__ import annotations

import pytest


def test_ultradian_module_imports():
    """Test that ultradian module can be imported."""
    from metabolon.pinocytosis import ultradian
    assert ultradian is not None


def test_ultradian_intake_exists():
    """Test that intake function exists and has expected signature."""
    from metabolon.pinocytosis import ultradian
    assert hasattr(ultradian, "intake")
    # It currently raises NotImplementedError which is expected
    with pytest.raises(NotImplementedError, match="ultradian gather not yet implemented"):
        ultradian.intake()


def test_ultradian_main_exists():
    """Test that main function exists."""
    from metabolon.pinocytosis import ultradian
    assert hasattr(ultradian, "main")


def test_ultradian_docstring():
    """Test that module has appropriate docstring."""
    from metabolon.pinocytosis import ultradian
    assert "Ultradian" in ultradian.__doc__
    assert "situational snapshot" in ultradian.__doc__
