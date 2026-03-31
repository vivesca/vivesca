#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/lysis — Firecrawl scrape/search CLI.

Lysis is a script (effectors/lysis), not an importable module.
It is loaded via exec() into isolated namespaces.
"""


import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

LYSIS_PATH = Path(__file__).resolve().parents[1] / "effectors" / "lysis"


# ── Fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def lysis():
    """Load lysis via exec into an isolated namespace dict."""
    ns: dict = {"__name__": "test_lysis", "__doc__": ""}
    source = LYSIS_PATH.read_text(encoding="utf-8")
    exec(source, ns)
    return ns


# ── get_api_key ─────────────────────────────────────────────────────────────


class TestGetApiKey:
    def test_keychain_success(self, lysis, monkeypatch):
        """Should return key from macOS Keychain when available."""
        mock_result = MagicMock(stdout="fc-test-key-123\n")
        with patch.object(subprocess, "run", return_value=mock_result):
            monkeypatch.setenv("USER", "terry")
            key = lysis["get_api_key"]()
        assert key == "fc-test-key-123"

    def test_fallback_to_env_var(self, lysis, monkeypatch):
        """Should fall back to FIRECRAWL_API_KEY env var when keychain fails."""
        monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-env-key")
        with patch.object(
            subprocess, "run", side_effect=subprocess.CalledProcessError(1, "security")
        ):
            key = lysis["get_api_key"]()
        assert key == "fc-env-key"

    def test_no_key_exits(self, lysis, monkeypatch):
        """Should exit with code 1 when no key is available."""
        monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)
        with patch.object(
            subprocess, "run", side_effect=subprocess.CalledProcessError(1, "security")
        ):
            with pytest.raises(SystemExit) as exc_info:
                lysis["get_api_key"]()
        assert exc_info.value.code == 1


# ── scrape ──────────────────────────────────────────────────────────────────


class TestScrape:
    def test_successful_scrape(self, lysis, capsys):
        """Should print markdown from successful scrape response."""
        response_data = {
            "success": True,
            "data": {"markdown": "# Hello World\n\nScraped content here."},
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = response_data
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp):
            lysis["scrape"]("https://example.com", "fc-test-key")

        out = capsys.readouterr().out
        assert "# Hello World" in out
        assert "Scraped content" in out

    def test_scrape_sends_correct_payload(self, lysis):
        """Should send correct URL and formats to the API."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"success": True, "data": {"markdown": "ok"}}
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp) as mock_post:
            lysis["scrape"]("https://example.com", "fc-test-key")

        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["json"]["url"] == "https://example.com"
        assert "markdown" in call_kwargs[1]["json"]["formats"]
        assert "Bearer fc-test-key" in call_kwargs[1]["headers"]["Authorization"]

    def test_scrape_failure_exits(self, lysis):
        """Should exit 1 when API returns success=False."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"success": False, "error": "blocked"}
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp):
            with pytest.raises(SystemExit) as exc_info:
                lysis["scrape"]("https://example.com", "fc-test-key")
        assert exc_info.value.code == 1

    def test_scrape_empty_markdown_exits(self, lysis):
        """Should exit 1 when API returns success but empty markdown."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"success": True, "data": {"markdown": ""}}
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp):
            with pytest.raises(SystemExit) as exc_info:
                lysis["scrape"]("https://example.com", "fc-test-key")
        assert exc_info.value.code == 1


# ── search ──────────────────────────────────────────────────────────────────


class TestSearch:
    def test_successful_search(self, lysis, capsys):
        """Should print formatted search results."""
        response_data = {
            "success": True,
            "data": [
                {
                    "title": "Result 1",
                    "url": "https://example.com/1",
                    "markdown": "Content of result 1.",
                },
                {
                    "title": "Result 2",
                    "url": "https://example.com/2",
                    "markdown": "Content of result 2.",
                },
            ],
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = response_data
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp):
            lysis["search"]("test query", "fc-test-key")

        out = capsys.readouterr().out
        assert "## 1. Result 1" in out
        assert "## 2. Result 2" in out
        assert "**URL:** https://example.com/1" in out
        assert "Content of result 1." in out

    def test_search_sends_correct_payload(self, lysis):
        """Should send correct query and scrapeOptions."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"success": True, "data": []}
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp) as mock_post:
            lysis["search"]("my query", "fc-test-key")

        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["json"]["query"] == "my query"
        assert call_kwargs[1]["json"]["limit"] == 5
        assert call_kwargs[1]["json"]["scrapeOptions"]["formats"] == ["markdown"]

    def test_search_failure_exits(self, lysis):
        """Should exit 1 when search API returns success=False."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"success": False, "error": "rate limited"}
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp):
            with pytest.raises(SystemExit) as exc_info:
                lysis["search"]("test", "fc-test-key")
        assert exc_info.value.code == 1

    def test_search_truncates_long_markdown(self, lysis, capsys):
        """Should truncate markdown to 3000 characters."""
        long_md = "x" * 5000
        response_data = {
            "success": True,
            "data": [
                {"title": "Long", "url": "https://example.com", "markdown": long_md},
            ],
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = response_data
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp):
            lysis["search"]("test", "fc-test-key")

        out = capsys.readouterr().out
        # The markdown should be truncated — the full 5000-char string won't appear
        assert "x" * 4000 not in out

    def test_search_untitled_default(self, lysis, capsys):
        """Should use 'Untitled' when title is missing."""
        response_data = {
            "success": True,
            "data": [
                {"url": "https://example.com", "markdown": "content"},
            ],
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = response_data
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.post", return_value=mock_resp):
            lysis["search"]("test", "fc-test-key")

        out = capsys.readouterr().out
        assert "Untitled" in out


# ── main ────────────────────────────────────────────────────────────────────


class TestMain:
    def test_no_args_shows_usage(self, lysis):
        """Should print usage and exit 0 when no args given (treated as --help)."""
        with patch.object(sys, "argv", ["lysis"]):
            with pytest.raises(SystemExit) as exc_info:
                lysis["main"]()
        assert exc_info.value.code == 0

    def test_scrape_url(self, lysis):
        """Should call scrape when given a URL."""
        mock_scrape = MagicMock()
        lysis["scrape"] = mock_scrape
        lysis["get_api_key"] = lambda: "fc-key"
        with patch.object(sys, "argv", ["lysis", "https://example.com"]):
            lysis["main"]()
        mock_scrape.assert_called_once_with("https://example.com", "fc-key")

    def test_search_command(self, lysis):
        """Should call search when first arg is 'search'."""
        mock_search = MagicMock()
        lysis["search"] = mock_search
        lysis["get_api_key"] = lambda: "fc-key"
        with patch.object(sys, "argv", ["lysis", "search", "hello", "world"]):
            lysis["main"]()
        mock_search.assert_called_once_with("hello world", "fc-key")

    def test_search_without_query_exits(self, lysis):
        """Should exit 1 when 'search' given without query."""
        lysis["get_api_key"] = lambda: "fc-key"
        with patch.object(sys, "argv", ["lysis", "search"]):
            with pytest.raises(SystemExit) as exc_info:
                lysis["main"]()
        assert exc_info.value.code == 1


# ── CLI subprocess ──────────────────────────────────────────────────────────


class TestCLISubprocess:
    def test_no_args_shows_usage(self):
        """Running lysis with no args should exit 0 (prints usage like --help)."""
        r = subprocess.run(
            ["uv", "run", "--script", str(LYSIS_PATH)],
            capture_output=True, text=True, timeout=60,
        )
        assert r.returncode == 0

    def test_help_output(self):
        """Running lysis with no args should show usage in stderr."""
        r = subprocess.run(
            ["uv", "run", "--script", str(LYSIS_PATH)],
            capture_output=True, text=True, timeout=60,
        )
        assert "scrape" in r.stderr.lower() or "search" in r.stderr.lower()
