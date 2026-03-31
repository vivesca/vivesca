"""Tests for ecdysis pinocytosis module."""

from __future__ import annotations

import pytest


def test_ecdysis_module_imports():
    """Test that ecdysis module can be imported."""
    from metabolon.pinocytosis import ecdysis
    assert ecdysis is not None


def test_ecdysis_intake_exists():
    """Test that intake function exists and has expected signature."""
    from metabolon.pinocytosis import ecdysis
    assert hasattr(ecdysis, "intake")
    # It currently raises NotImplementedError which is expected
    with pytest.raises(NotImplementedError, match="ecdysis gather not yet implemented"):
        ecdysis.intake()


def test_ecdysis_main_exists():
    """Test that main function exists."""
    from metabolon.pinocytosis import ecdysis
    assert hasattr(ecdysis, "main")


def test_ecdysis_docstring():
    """Test that module has appropriate docstring."""
    from metabolon.pinocytosis import ecdysis
    assert "Ecdysis" in ecdysis.__doc__
    assert "weekly review" in ecdysis.__doc__
