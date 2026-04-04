"""Tests for the consolidation resource module."""


def test_resource_consolidation_module_structure():
    """Test that the module has the expected structure."""
    # BINARY is not defined in consolidation.py, check we can import
    import metabolon.resources.consolidation

    assert metabolon.resources.consolidation is not None


def test_resource_consolidation_docstring_content():
    """Test that the module docstring contains expected information."""
    import metabolon.resources.consolidation as module

    docstring = module.__doc__

    assert "Consolidation resource" in docstring
    assert "memory metabolism report" in docstring
    assert "vivesca://consolidation" in docstring
    assert "latest memory consolidation analysis" in docstring
