from __future__ import annotations

"""Tests for metabolon.enzymes.rheotaxis — the MCP tool wrapper.

All engine calls are mocked; no network access.
"""

from unittest.mock import patch, AsyncMock

from metabolon.enzymes.rheotaxis import rheotaxis


@patch("metabolon.enzymes._parallel_search._report", return_value="formatted")
@patch("metabolon.enzymes._parallel_search._run_all", new_callable=AsyncMock, return_value=[])
def test_default_mode_calls_parallel_pipeline(mock_run_all, mock_report):
    result = rheotaxis("test query")
    mock_run_all.assert_called_once_with("test query")
    mock_report.assert_called_once()
    assert result == "formatted"


@patch("metabolon.enzymes.rheotaxis.rheotaxis_engine")
def test_research_mode_calls_perplexity_deep(mock_engine):
    mock_engine.perplexity_deep.return_value = "deep results"
    result = rheotaxis("test query", mode="research")
    mock_engine.perplexity_deep.assert_called_once_with("test query")
    assert result == "deep results"
