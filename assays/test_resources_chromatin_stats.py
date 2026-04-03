"""Tests for metabolon.resources.chromatin_stats — memory statistics resource."""
from pathlib import Path
import pytest
import importlib


def test_module_import_succeeds():
    """Test that the chromatin_stats module can be imported successfully."""
    from metabolon.resources import chromatin_stats
    assert chromatin_stats is not None
    assert chromatin_stats.__doc__ is not None


def test_module_docstring_contains_expected_metadata():
    """Test that the module docstring contains the expected resource declaration."""
    from metabolon.resources import chromatin_stats
    doc = chromatin_stats.__doc__

    assert "Hippocampus" in doc
    assert "the organism's memory performance" in doc
    assert "vivesca://histone_store" in doc
    assert "memory database statistics" in doc


def test_chromatin_stats_module_is_in_package():
    """Test that chromatin_stats module is properly in the metabolon.resources package."""
    import metabolon.resources
    package_path = Path(metabolon.resources.__file__).parent
    module_path = package_path / "chromatin_stats.py"

    assert module_path.exists()
    assert module_path.is_file()
    assert module_path.stat().st_size > 0


def test_import_module_via_importlib():
    """Test module import via importlib for robustness."""
    spec = importlib.util.find_spec("metabolon.resources.chromatin_stats")
    assert spec is not None
    assert spec.origin is not None
    assert "metabolon/resources/chromatin_stats.py" in spec.origin

    module = importlib.util.module_from_spec(spec)
    assert module is not None


def test_binary_constant_exists_and_is_correct():
    """Test that BINARY constant exists and has the correct value."""
    from metabolon.resources.chromatin_stats import BINARY
    assert isinstance(BINARY, str)
    assert BINARY == "oghma"
