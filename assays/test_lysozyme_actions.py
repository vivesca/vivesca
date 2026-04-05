from __future__ import annotations

"""Tests for metabolon/enzymes/lysozyme.py — MCP tool wrapper around lysozyme effector.

Covers all three action branches (scrape, search, unknown), argument
forwarding, timeout, and error propagation from run_cli.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.enzymes.lysozyme import BINARY, lysozyme

# ── Module constants ─────────────────────────────────────────────────────────


class TestConstants:
    def test_binary_points_to_lysozyme_effector(self):
        assert str(Path.home() / "germline/effectors/lysozyme") == BINARY

    def test_binary_path_is_absolute(self):
        assert Path(BINARY).is_absolute()


# ── Scrape action ────────────────────────────────────────────────────────────


class TestScrapeAction:
    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_scrape_returns_stdout(self, mock_run):
        mock_run.return_value = "# Hello\nScraped content."
        result = lysozyme(action="scrape", url="https://example.com")
        assert result == "# Hello\nScraped content."

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_scrape_forwards_url_as_single_arg(self, mock_run):
        mock_run.return_value = "ok"
        lysozyme(action="scrape", url="https://example.com/page")
        mock_run.assert_called_once_with(BINARY, ["https://example.com/page"], timeout=60)

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_scrape_uses_60s_timeout(self, mock_run):
        mock_run.return_value = "ok"
        lysozyme(action="scrape", url="https://example.com")
        _args, kwargs = mock_run.call_args
        assert kwargs["timeout"] == 60

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_scrape_empty_url_still_calls(self, mock_run):
        mock_run.return_value = "Done."
        lysozyme(action="scrape", url="")
        mock_run.assert_called_once_with(BINARY, [""], timeout=60)

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_scrape_propagates_value_error(self, mock_run):
        mock_run.side_effect = ValueError("lysozyme error: blocked")
        with pytest.raises(ValueError, match="blocked"):
            lysozyme(action="scrape", url="https://example.com")

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_scrape_propagates_timeout_error(self, mock_run):
        mock_run.side_effect = ValueError("lysozyme timed out")
        with pytest.raises(ValueError, match="timed out"):
            lysozyme(action="scrape", url="https://slow.example.com")

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_scrape_returns_string(self, mock_run):
        mock_run.return_value = "markdown output"
        result = lysozyme(action="scrape", url="https://example.com")
        assert isinstance(result, str)


# ── Search action ────────────────────────────────────────────────────────────


class TestSearchAction:
    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_search_returns_results(self, mock_run):
        mock_run.return_value = "## 1. Result\nContent"
        result = lysozyme(action="search", query="test query")
        assert "Result" in result

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_search_forwards_query_with_search_prefix(self, mock_run):
        mock_run.return_value = "ok"
        lysozyme(action="search", query="my search terms")
        mock_run.assert_called_once_with(BINARY, ["search", "my search terms"], timeout=60)

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_search_uses_60s_timeout(self, mock_run):
        mock_run.return_value = "ok"
        lysozyme(action="search", query="test")
        _args, kwargs = mock_run.call_args
        assert kwargs["timeout"] == 60

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_search_empty_query_still_calls(self, mock_run):
        mock_run.return_value = "Done."
        lysozyme(action="search", query="")
        mock_run.assert_called_once_with(BINARY, ["search", ""], timeout=60)

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_search_propagates_value_error(self, mock_run):
        mock_run.side_effect = ValueError("lysozyme error: rate limited")
        with pytest.raises(ValueError, match="rate limited"):
            lysozyme(action="search", query="test")

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_search_returns_string(self, mock_run):
        mock_run.return_value = "search output"
        result = lysozyme(action="search", query="test")
        assert isinstance(result, str)


# ── Unknown action ───────────────────────────────────────────────────────────


class TestUnknownAction:
    def test_unknown_returns_error_message(self):
        result = lysozyme(action="delete")
        assert isinstance(result, str)
        assert "Error" in result
        assert "delete" in result

    def test_unknown_mentions_valid_actions(self):
        result = lysozyme(action="bogus")
        assert "scrape" in result
        assert "search" in result

    def test_unknown_does_not_call_run_cli(self):
        """Ensure run_cli is never invoked for invalid actions."""
        with patch("metabolon.enzymes.lysozyme.run_cli") as mock_run:
            result = lysozyme(action="invalid")
            mock_run.assert_not_called()
            assert "Error" in result

    def test_empty_action_is_unknown(self):
        result = lysozyme(action="")
        assert "Error" in result

    def test_case_sensitive_action(self):
        """Actions should be case-sensitive — 'Scrape' is not 'scrape'."""
        result = lysozyme(action="Scrape")
        assert "Error" in result

    def test_mixed_case_action(self):
        result = lysozyme(action="SEARCH")
        assert "Error" in result


# ── Default arguments ────────────────────────────────────────────────────────


class TestDefaults:
    def test_url_default_empty(self):
        """Default url should be empty string."""
        import inspect

        sig = inspect.signature(lysozyme)
        assert sig.parameters["url"].default == ""

    def test_query_default_empty(self):
        """Default query should be empty string."""
        import inspect

        sig = inspect.signature(lysozyme)
        assert sig.parameters["query"].default == ""
