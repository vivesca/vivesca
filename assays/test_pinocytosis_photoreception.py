"""Tests for photoreception pinocytosis module."""

from __future__ import annotations

import pytest


def test_photoreception_module_imports():
    """Test that photoreception module can be imported."""
    from metabolon.pinocytosis import photoreception
    assert photoreception is not None


def test_photoreception_intake_exists():
    """Test that intake function exists and has expected signature."""
    from metabolon.pinocytosis import photoreception
    assert hasattr(photoreception, "intake")
    # It currently raises NotImplementedError which is expected
    with pytest.raises(NotImplementedError, match="photoreception gather not yet implemented"):
        photoreception.intake()


def test_photoreception_main_exists():
    """Test that main function exists."""
    from metabolon.pinocytosis import photoreception
    assert hasattr(photoreception, "main")


def test_photoreception_docstring():
    """Test that module has appropriate docstring."""
    from metabolon.pinocytosis import photoreception
    assert "Photoreception" in photoreception.__doc__
    assert "morning brief" in photoreception.__doc__
