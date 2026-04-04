from __future__ import annotations

"""Tests for constitution resource module."""


from pathlib import Path

from metabolon.resources import constitution


def test_constitution_module_imports():
    """Test that constitution module can be imported."""
    assert constitution is not None


def test_canonical_path_exists():
    """Test that CANONICAL is defined as a Path."""
    assert hasattr(constitution, "CANONICAL")
    assert isinstance(constitution.CANONICAL, Path)
    assert str(constitution.CANONICAL).endswith("genome.md")


def test_constitution_docstring():
    """Test that module has appropriate docstring."""
    assert "Constitution" in constitution.__doc__
    assert "vivesca://constitution" in constitution.__doc__
