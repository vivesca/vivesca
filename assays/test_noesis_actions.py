"""Tests for noesis action-dispatch consolidation."""
from unittest.mock import patch
import pytest

def test_unknown_action():
    from metabolon.enzymes.noesis import noesis
    result = noesis(action="nonexistent")
    assert isinstance(result, str)
    assert "unknown" in result.lower() or "nonexistent" in result.lower()

@patch("metabolon.enzymes.noesis.run_cli")
def test_search_action(mock_run):
    from metabolon.enzymes.noesis import noesis
    mock_run.return_value = "search result"
    result = noesis(action="search", query="test")
    assert isinstance(result, str)

@patch("metabolon.enzymes.noesis.run_cli")
def test_ask_action(mock_run):
    from metabolon.enzymes.noesis import noesis
    mock_run.return_value = "ask result"
    result = noesis(action="ask", query="test")
    assert isinstance(result, str)

@patch("metabolon.enzymes.noesis.run_cli")
def test_research_action(mock_run):
    from metabolon.enzymes.noesis import noesis
    mock_run.return_value = "research result"
    result = noesis(action="research", query="test")
    assert isinstance(result, str)
