"""Tests for tool: data_fetch."""


def test_data_fetch_exists():
    """Verify data_fetch can be imported."""
    from myapp.enzymes.data import data_fetch
    assert callable(data_fetch)