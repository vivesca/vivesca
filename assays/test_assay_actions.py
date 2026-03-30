"""Tests for assay action-dispatch consolidation."""
from unittest.mock import patch
import pytest

def test_unknown_action():
    from metabolon.enzymes.assay import assay
    result = assay(action="nonexistent")
    assert isinstance(result, str)
    assert "unknown" in result.lower() or "nonexistent" in result.lower()

@patch("metabolon.enzymes.assay.run_cli")
def test_list_action(mock_run):
    from metabolon.enzymes.assay import assay
    mock_run.return_value = "list result"
    result = assay(action="list")
    assert isinstance(result, str)

@patch("metabolon.enzymes.assay.run_cli")
def test_check_action(mock_run):
    from metabolon.enzymes.assay import assay
    mock_run.return_value = "check result"
    result = assay(action="check", name="test")
    assert isinstance(result, str)

@patch("metabolon.enzymes.assay.run_cli")
def test_close_action(mock_run):
    from metabolon.enzymes.assay import assay
    mock_run.return_value = "close result"
    result = assay(action="close", name="test")
    assert isinstance(result, str)
