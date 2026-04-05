"""Tests for metabolon/enzymes/lysozyme.py"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


class TestLysis:
    """Tests for the lysozyme tool."""

    def test_scrape_action_calls_run_cli_with_url(self):
        """Scrape action should pass URL to run_cli."""
        from metabolon.enzymes.lysozyme import lysozyme

        with patch("metabolon.enzymes.lysozyme.run_cli") as mock_run:
            mock_run.return_value = "# Page Title\n\nContent here."
            result = lysozyme(action="scrape", url="https://example.com")

            mock_run.assert_called_once_with(
                str(Path.home() / "germline/effectors/lysozyme"),
                ["https://example.com"],
                timeout=60,
            )
            assert result == "# Page Title\n\nContent here."

    def test_search_action_calls_run_cli_with_search_prefix(self):
        """Search action should pass 'search' prefix and query to run_cli."""
        from metabolon.enzymes.lysozyme import lysozyme

        with patch("metabolon.enzymes.lysozyme.run_cli") as mock_run:
            mock_run.return_value = "Search results..."
            result = lysozyme(action="search", query="python testing")

            mock_run.assert_called_once_with(
                str(Path.home() / "germline/effectors/lysozyme"),
                ["search", "python testing"],
                timeout=60,
            )
            assert result == "Search results..."

    def test_unknown_action_returns_error(self):
        """Unknown action should return an error message."""
        from metabolon.enzymes.lysozyme import lysozyme

        with patch("metabolon.enzymes.lysozyme.run_cli") as mock_run:
            result = lysozyme(action="invalid", url="https://example.com")

            mock_run.assert_not_called()
            assert result == "Error: unknown action 'invalid'. Use 'scrape' or 'search'."

    def test_scrape_propagates_run_cli_error(self):
        """Scrape should propagate ValueError from run_cli."""
        from metabolon.enzymes.lysozyme import lysozyme

        with patch("metabolon.enzymes.lysozyme.run_cli") as mock_run:
            mock_run.side_effect = ValueError("lysozyme error: API key missing")

            with pytest.raises(ValueError, match="lysozyme error: API key missing"):
                lysozyme(action="scrape", url="https://example.com")

    def test_search_propagates_run_cli_error(self):
        """Search should propagate ValueError from run_cli."""
        from metabolon.enzymes.lysozyme import lysozyme

        with patch("metabolon.enzymes.lysozyme.run_cli") as mock_run:
            mock_run.side_effect = ValueError("lysozyme timed out \\(60s\\)")

            with pytest.raises(ValueError, match="lysozyme timed out"):
                lysozyme(action="search", query="test query")

    def test_default_parameters(self):
        """Test that url and query have default empty strings."""
        from metabolon.enzymes.lysozyme import lysozyme

        with patch("metabolon.enzymes.lysozyme.run_cli") as mock_run:
            mock_run.return_value = "Done."
            # Calling with just action uses defaults
            result = lysozyme(action="scrape")

            mock_run.assert_called_once_with(
                str(Path.home() / "germline/effectors/lysozyme"),
                [""],
                timeout=60,
            )
            assert result == "Done."
