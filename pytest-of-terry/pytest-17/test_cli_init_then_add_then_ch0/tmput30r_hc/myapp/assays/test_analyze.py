"""Tests for prompt: analyze."""


def test_analyze_exists():
    """Verify analyze can be imported."""
    from myapp.codons.analyze import analyze
    assert callable(analyze)