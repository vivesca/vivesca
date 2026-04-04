"""Tests for the chromatin_stats resource module."""

from metabolon.resources.chromatin_stats import BINARY


def test_resource_chromatin_stats_module_structure():
    """Test that the module has the expected structure."""
    # Verify BINARY constant exists and is correct type
    assert isinstance(BINARY, str)
    assert BINARY == "oghma"


def test_resource_chromatin_stats_docstring_content():
    """Test that the module docstring contains expected information."""
    import metabolon.resources.chromatin_stats as module

    docstring = module.__doc__

    assert "Hippocampus" in docstring
    assert "the organism's memory performance" in docstring
    assert "vivesca://histone_store" in docstring
    assert "memory database statistics" in docstring
