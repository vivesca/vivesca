"""Tests for metabolon/enzymes/lysis.py"""

from __future__ import annotations

from unittest.mock import patch

import pytest


class TestLysis:
    """Tests for the lysis tool."""

    def test_scrape_action_calls_run_cli_with_url(self):
        """Scrape action should pass URL to run_cli."""
        from metabolon.enzymes.lysis import lysis

        with patch("metabolon.enzymes.lysis.run_cli") as mock_run:
            mock_run.return_value = "# Page Title\n\nContent here."
            result = lysis(action="scrape", url="https://example.com")

            mock_run.assert_called_once_with(
                "/home/terry/germline/effectors/lysis",
                ["https://example.com"],
                timeout=60,
            )
            assert result == "# Page Title\n\nContent here."

    def test_search_action_calls_run_cli_with_search_prefix(self):
        """Search action should pass 'search' prefix and query to run_cli."""
        from metabolon.enzymes.lysis import lysis

        with patch("metabolon.enzymes.lysis.run_cli") as mock_run:
            mock_run.return_value = "Search results..."
            result = lysis(action="search", query="python testing")

            mock_run.assert_called_once_with(
                "/home/terry/germline/effectors/lysis",
                ["search", "python testing"],
                timeout=60,
            )
            assert result == "Search results..."

    def test_unknown_action_returns_error(self):
        """Unknown action should return an error message."""
        from metabolon.enzymes.lysis import lysis

        with patch("metabolon.enzymes.lysis.run_cli") as mock_run:
            result = lysis(action="invalid", url="https://example.com")

            mock_run.assert_not_called()
            assert result == "Error: unknown action 'invalid'. Use 'scrape' or 'search'."

    def test_scrape_propagates_run_cli_error(self):
        """Scrape should propagate ValueError from run_cli."""
        from metabolon.enzymes.lysis import lysis

        with patch("metabolon.enzymes.lysis.run_cli") as mock_run:
            mock_run.side_effect = ValueError("lysis error: API key missing")

            with pytest.raises(ValueError, match="lysis error: API key missing"):
                lysis(action="scrape", url="https://example.com")

    def test_search_propagates_run_cli_error(self):
        """Search should propagate ValueError from run_cli."""
        from metabolon.enzymes.lysis import lysis

        with patch("metabolon.enzymes.lysis.run_cli") as mock_run:
            mock_run.side_effect = ValueError("lysis timed out \\(60s\\)")

            with pytest.raises(ValueError, match="lysis timed out"):
                lysis(action="search", query="test query")

    def test_default_parameters(self):
        """Test that url and query have default empty strings."""
        from metabolon.enzymes.lysis import lysis

        with patch("metabolon.enzymes.lysis.run_cli") as mock_run:
            mock_run.return_value = "Done."
            # Calling with just action uses defaults
            result = lysis(action="scrape")

            mock_run.assert_called_once_with(
                "/home/terry/germline/effectors/lysis",
                [""],
                timeout=60,
            )
            assert result == "Done."
