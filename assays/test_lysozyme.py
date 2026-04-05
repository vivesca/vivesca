from __future__ import annotations

"""Tests for metabolon/enzymes/lysozyme.py."""

from unittest.mock import patch

import pytest


class TestLysisScrape:
    """Tests for lysozyme scrape action."""

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_scrape_calls_run_cli_with_url(self, mock_run_cli):
        """Test scrape action calls run_cli with URL."""
        from metabolon.enzymes.lysozyme import lysozyme

        mock_run_cli.return_value = "# Page Title\n\nContent here."

        result = lysozyme(action="scrape", url="https://example.com")

        assert result == "# Page Title\n\nContent here."
        mock_run_cli.assert_called_once()
        args = mock_run_cli.call_args
        assert "lysozyme" in args[0][0]  # binary path contains 'lysozyme'
        assert args[0][1] == ["https://example.com"]  # args list
        assert args[1]["timeout"] == 60

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_scrape_empty_url(self, mock_run_cli):
        """Test scrape with empty URL still calls run_cli."""
        from metabolon.enzymes.lysozyme import lysozyme

        mock_run_cli.return_value = "Error: No URL provided"

        lysozyme(action="scrape", url="")

        mock_run_cli.assert_called_once()

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_scrape_returns_markdown(self, mock_run_cli):
        """Test scrape returns markdown content."""
        from metabolon.enzymes.lysozyme import lysozyme

        mock_run_cli.return_value = "# Title\n\nParagraph\n- item1\n- item2"

        result = lysozyme(action="scrape", url="https://test.org/page")

        assert "# Title" in result
        assert "- item1" in result

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_scrape_propagates_value_error(self, mock_run_cli):
        """Test scrape propagates ValueError from run_cli."""
        from metabolon.enzymes.lysozyme import lysozyme

        mock_run_cli.side_effect = ValueError("lysozyme error: timeout")

        with pytest.raises(ValueError, match="lysozyme error"):
            lysozyme(action="scrape", url="https://example.com")


class TestLysisSearch:
    """Tests for lysozyme search action."""

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_search_calls_run_cli_with_query(self, mock_run_cli):
        """Test search action calls run_cli with search prefix."""
        from metabolon.enzymes.lysozyme import lysozyme

        mock_run_cli.return_value = "# Search Results\n\n1. Result one\n2. Result two"

        result = lysozyme(action="search", query="python testing")

        assert "# Search Results" in result
        mock_run_cli.assert_called_once()
        args = mock_run_cli.call_args
        assert args[0][1] == ["search", "python testing"]
        assert args[1]["timeout"] == 60

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_search_empty_query(self, mock_run_cli):
        """Test search with empty query still calls run_cli."""
        from metabolon.enzymes.lysozyme import lysozyme

        mock_run_cli.return_value = "No results"

        lysozyme(action="search", query="")

        mock_run_cli.assert_called_once()
        args = mock_run_cli.call_args
        assert args[0][1] == ["search", ""]

    @patch("metabolon.enzymes.lysozyme.run_cli")
    def test_search_propagates_value_error(self, mock_run_cli):
        """Test search propagates ValueError from run_cli."""
        from metabolon.enzymes.lysozyme import lysozyme

        mock_run_cli.side_effect = ValueError("lysozyme error: API rate limit")

        with pytest.raises(ValueError, match="API rate limit"):
            lysozyme(action="search", query="test query")


class TestLysisInvalidAction:
    """Tests for invalid action handling."""

    def test_invalid_action_returns_error(self):
        """Test unknown action returns error message."""
        from metabolon.enzymes.lysozyme import lysozyme

        result = lysozyme(action="invalid")

        assert "Error" in result
        assert "unknown action" in result
        assert "'invalid'" in result

    def test_invalid_action_suggests_valid_actions(self):
        """Test error message suggests valid actions."""
        from metabolon.enzymes.lysozyme import lysozyme

        result = lysozyme(action="delete")

        assert "scrape" in result or "search" in result

    def test_case_sensitive_action(self):
        """Test action is case sensitive."""
        from metabolon.enzymes.lysozyme import lysozyme

        result = lysozyme(action="SCRAPE")

        assert "Error" in result
        assert "unknown action" in result


class TestLysisBinary:
    """Tests for binary path configuration."""

    def test_binary_path_uses_home(self):
        """Test binary path uses home directory."""
        from pathlib import Path

        from metabolon.enzymes.lysozyme import BINARY

        assert str(Path.home()) in BINARY
        assert "germline" in BINARY
        assert "effectors" in BINARY
        assert "lysozyme" in BINARY
