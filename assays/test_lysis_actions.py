"""Tests for lysis action-dispatch consolidation."""
from unittest.mock import patch
import pytest

def test_unknown_action():
    from metabolon.enzymes.lysis import lysis
    result = lysis(action="nonexistent")
    assert isinstance(result, str)
    assert "unknown" in result.lower() or "nonexistent" in result.lower()

@patch("metabolon.enzymes.lysis.run_cli")
def test_scrape_action(mock_run):
    from metabolon.enzymes.lysis import lysis
    mock_run.return_value = "scrape result"
    result = lysis(action="scrape", url="http://example.com")
    assert isinstance(result, str)

@patch("metabolon.enzymes.lysis.run_cli")
def test_search_action(mock_run):
    from metabolon.enzymes.lysis import lysis
    mock_run.return_value = "search result"
    result = lysis(action="search", query="test")
    assert isinstance(result, str)
