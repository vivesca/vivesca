"""Tests for metabolon.resources.consolidation — memory consolidation resource."""

import importlib
from pathlib import Path


def test_module_import_succeeds():
    """Test that the consolidation module can be imported successfully."""
    from metabolon.resources import consolidation

    assert consolidation is not None
    assert consolidation.__doc__ is not None


def test_module_docstring_contains_expected_metadata():
    """Test that the module docstring contains the expected resource declaration."""
    from metabolon.resources import consolidation

    doc = consolidation.__doc__

    assert "Consolidation resource" in doc
    assert "memory metabolism report" in doc
    assert "vivesca://consolidation" in doc
    assert "latest memory consolidation analysis" in doc


def test_consolidation_module_is_in_package():
    """Test that consolidation module is properly in the metabolon.resources package."""
    import metabolon.resources

    package_path = Path(metabolon.resources.__file__).parent
    module_path = package_path / "consolidation.py"

    assert module_path.exists()
    assert module_path.is_file()
    assert module_path.stat().st_size > 0


def test_import_module_via_importlib():
    """Test module import via importlib for robustness."""
    spec = importlib.util.find_spec("metabolon.resources.consolidation")
    assert spec is not None
    assert spec.origin is not None
    assert "metabolon/resources/consolidation.py" in spec.origin

    module = importlib.util.module_from_spec(spec)
    assert module is not None
