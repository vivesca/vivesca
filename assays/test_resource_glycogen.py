"""Tests for the glycogen resource module."""
from metabolon.resources.glycogen import BINARY


def test_module_structure():
    """Test that the module has the expected structure."""
    # Verify BINARY constant exists and is correct type
    assert isinstance(BINARY, str)
    assert BINARY == "respirometry"


def test_docstring_content():
    """Test that the module docstring contains expected information."""
    import metabolon.resources.glycogen as module
    docstring = module.__doc__
    
    assert "Budget resource" in docstring
    assert "current Claude Code token usage" in docstring
    assert "vivesca://budget" in docstring
    assert "current token budget and usage status" in docstring
