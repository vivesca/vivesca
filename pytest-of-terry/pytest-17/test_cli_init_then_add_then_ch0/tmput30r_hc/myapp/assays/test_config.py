"""Tests for resource: config."""


def test_config_exists():
    """Verify config can be imported."""
    from myapp.resources.config import config
    assert callable(config)