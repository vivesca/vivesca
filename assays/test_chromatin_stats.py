"""Tests for metabolon.resources.chromatin_stats — focused on module contract."""

import types

# ---------------------------------------------------------------------------
# Import & identity
# ---------------------------------------------------------------------------


def test_import_returns_module():
    """Importing chromatin_stats yields a real module object."""
    from metabolon.resources import chromatin_stats

    assert isinstance(chromatin_stats, types.ModuleType)


def test_module_fqn():
    """Module's __name__ matches its fully-qualified package path."""
    from metabolon.resources import chromatin_stats

    assert chromatin_stats.__name__ == "metabolon.resources.chromatin_stats"


# ---------------------------------------------------------------------------
# BINARY constant
# ---------------------------------------------------------------------------


def test_binary_is_lowercase_alpha():
    """BINARY must be a non-empty lowercase alphabetic string."""
    from metabolon.resources.chromatin_stats import BINARY

    assert isinstance(BINARY, str)
    assert len(BINARY) > 0
    assert BINARY.isalpha()
    assert BINARY.lower() == BINARY


def test_binary_value_is_oghma():
    """BINARY constant holds the expected service name."""
    from metabolon.resources.chromatin_stats import BINARY

    assert BINARY == "oghma"


def test_binary_is_module_only_public_name():
    """BINARY is the sole public top-level name (no trailing underscore attrs)."""
    import metabolon.resources.chromatin_stats as mod

    public_names = [n for n in dir(mod) if not n.startswith("_")]
    assert public_names == ["BINARY"]


# ---------------------------------------------------------------------------
# Docstring contract
# ---------------------------------------------------------------------------


def test_docstring_declares_resource_uri():
    """Module docstring must declare the vivesca resource URI."""
    from metabolon.resources import chromatin_stats

    assert chromatin_stats.__doc__ is not None
    assert "vivesca://" in chromatin_stats.__doc__


def test_docstring_describes_hippocampus():
    """Module docstring identifies this as the Hippocampus resource."""
    from metabolon.resources import chromatin_stats

    assert "Hippocampus" in chromatin_stats.__doc__
