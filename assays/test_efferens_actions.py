"""Tests for efferens action-dispatch consolidation."""
from unittest.mock import patch
import pytest

def test_unknown_action():
    from metabolon.enzymes.efferens import efferens
    result = efferens(action="nonexistent")
    assert isinstance(result, str)
    assert "unknown" in result.lower() or "nonexistent" in result.lower()

@patch("metabolon.enzymes.efferens.run_cli")
def test_list_action(mock_run):
    from metabolon.enzymes.efferens import efferens
    mock_run.return_value = "list result"
    result = efferens(action="list")
    assert isinstance(result, str)

@patch("metabolon.enzymes.efferens.run_cli")
def test_post_action(mock_run):
    from metabolon.enzymes.efferens import efferens
    mock_run.return_value = "post result"
    result = efferens(action="post", subject="test", message="test")
    assert isinstance(result, str)

@patch("metabolon.enzymes.efferens.run_cli")
def test_count_action(mock_run):
    from metabolon.enzymes.efferens import efferens
    mock_run.return_value = "count result"
    result = efferens(action="count")
    assert isinstance(result, str)
