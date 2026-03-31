#!/usr/bin/env python3
"""Tests for browser effector CLI wrapper.

Uses mocks — no real browser launch required.
"""
from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the effector main + parser directly (it has a .py extension via shebang)
from effectors.browser import main, build_parser

# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

class TestParser:
    def test_fetch_minimum(self):
        args = build_parser().parse_args(["fetch", "https://example.com"])
        assert args.command == "fetch"
        assert args.url == "https://example.com"
        assert args.cookies is None
        assert args.selector is None
        assert args.screenshot is None
        assert args.pdf is None
        assert args.wait == 0
        assert args.json_output is False

    def test_fetch_all_options(self):
        args = build_parser().parse_args([
            "fetch", "https://example.com",
            "--cookies", "/tmp/cookies.json",
            "--selector", "article",
            "--screenshot", "/tmp/shot.png",
            "--pdf", "/tmp/out.pdf",
            "--wait", "2000",
            "--json",
        ])
        assert args.url == "https://example.com"
        assert args.cookies == "/tmp/cookies.json"
        assert args.selector == "article"
        assert args.screenshot == "/tmp/shot.png"
        assert args.pdf == "/tmp/out.pdf"
        assert args.wait == 2000
        assert args.json_output is True

    def test_no_command_exits(self):
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Fetch tests — mock the core browser.fetch function
# ---------------------------------------------------------------------------

SAMPLE_RESULT = {
    "url": "https://example.com",
    "title": "Example Domain",
    "text": "This domain is for use in illustrative examples.",
    "status": 200,
    "screenshot": None,
    "pdf": None,
}


class TestFetchText:
    @patch("effectors.browser.fetch", return_value=SAMPLE_RESULT)
    def test_plain_text_output(self, mock_fetch, capsys):
        main(["fetch", "https://example.com"])
        captured = capsys.readouterr()
        assert "This domain is for use in illustrative examples." in captured.out
        assert "title" not in captured.out  # no JSON keys in plain mode

    @patch("effectors.browser.fetch", return_value=SAMPLE_RESULT)
    def test_json_output(self, mock_fetch, capsys):
        main(["fetch", "https://example.com", "--json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["title"] == "Example Domain"
        assert data["status"] == 200
        assert data["text"] == SAMPLE_RESULT["text"]

    @patch("effectors.browser.fetch", return_value=SAMPLE_RESULT)
    def test_passes_cookies(self, mock_fetch):
        main(["fetch", "https://example.com", "--cookies", "/tmp/c.json"])
        mock_fetch.assert_called_once_with(
            "https://example.com",
            cookies="/tmp/c.json",
            selector=None,
            screenshot=None,
            pdf=None,
            wait=0,
        )

    @patch("effectors.browser.fetch", return_value=SAMPLE_RESULT)
    def test_passes_selector(self, mock_fetch):
        main(["fetch", "https://example.com", "--selector", "main"])
        mock_fetch.assert_called_once()
        assert mock_fetch.call_args.kwargs["selector"] == "main"

    @patch("effectors.browser.fetch", return_value=SAMPLE_RESULT)
    def test_passes_screenshot(self, mock_fetch):
        main(["fetch", "https://example.com", "--screenshot", "/tmp/s.png"])
        assert mock_fetch.call_args.kwargs["screenshot"] == "/tmp/s.png"

    @patch("effectors.browser.fetch", return_value=SAMPLE_RESULT)
    def test_passes_pdf(self, mock_fetch):
        main(["fetch", "https://example.com", "--pdf", "/tmp/out.pdf"])
        assert mock_fetch.call_args.kwargs["pdf"] == "/tmp/out.pdf"

    @patch("effectors.browser.fetch", return_value=SAMPLE_RESULT)
    def test_passes_wait(self, mock_fetch):
        main(["fetch", "https://example.com", "--wait", "3000"])
        assert mock_fetch.call_args.kwargs["wait"] == 3000

    @patch("effectors.browser.fetch", side_effect=FileNotFoundError("Cookie file not found: /tmp/nope"))
    def test_missing_cookies_exits_1(self, mock_fetch, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["fetch", "https://example.com", "--cookies", "/tmp/nope"])
        assert exc_info.value.code == 1
        assert "Cookie file" in capsys.readouterr().err

    @patch("effectors.browser.fetch", side_effect=RuntimeError("timeout"))
    def test_generic_error_exits_1(self, mock_fetch, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["fetch", "https://example.com"])
        assert exc_info.value.code == 1
        assert "timeout" in capsys.readouterr().err

    @patch("effectors.browser.fetch", return_value=SAMPLE_RESULT)
    def test_json_includes_screenshot_path(self, mock_fetch, capsys):
        result = {**SAMPLE_RESULT, "screenshot": "/tmp/shot.png"}
        mock_fetch.return_value = result
        main(["fetch", "https://example.com", "--json"])
        data = json.loads(capsys.readouterr().out)
        assert data["screenshot"] == "/tmp/shot.png"

    @patch("effectors.browser.fetch", return_value=SAMPLE_RESULT)
    def test_json_includes_pdf_path(self, mock_fetch, capsys):
        result = {**SAMPLE_RESULT, "pdf": "/tmp/page.pdf"}
        mock_fetch.return_value = result
        main(["fetch", "https://example.com", "--json"])
        data = json.loads(capsys.readouterr().out)
        assert data["pdf"] == "/tmp/page.pdf"


# ---------------------------------------------------------------------------
# Core module unit tests — mock Playwright itself
# ---------------------------------------------------------------------------

class TestCoreFetch:
    """Test metabolon.organelles.browser.fetch with mocked Playwright."""

    @patch("metabolon.organelles.browser.sync_playwright")
    def test_basic_fetch(self, mock_pw_factory):
        # Build mock chain: sync_playwright() -> __enter__ -> chromium.launch -> ...
        mock_pw = MagicMock()
        mock_pw_factory.return_value.__enter__ = MagicMock(return_value=mock_pw)
        mock_pw_factory.return_value.__exit__ = MagicMock(return_value=False)

        mock_browser = MagicMock()
        mock_pw.chromium.launch.return_value = mock_browser

        mock_page = MagicMock()
        mock_page.title.return_value = "Test Page"
        mock_page.inner_text.return_value = "Hello world"
        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto.return_value = mock_response

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context

        from metabolon.organelles.browser import fetch
        result = fetch("https://example.com")

        assert result["title"] == "Test Page"
        assert result["text"] == "Hello world"
        assert result["status"] == 200
        assert result["screenshot"] is None
        assert result["pdf"] is None
        mock_page.screenshot.assert_not_called()
        mock_page.pdf.assert_not_called()

    @patch("metabolon.organelles.browser.sync_playwright")
    def test_fetch_with_selector(self, mock_pw_factory):
        mock_pw = MagicMock()
        mock_pw_factory.return_value.__enter__ = MagicMock(return_value=mock_pw)
        mock_pw_factory.return_value.__exit__ = MagicMock(return_value=False)

        mock_element = MagicMock()
        mock_element.inner_text.return_value = "Selected content"

        mock_page = MagicMock()
        mock_page.title.return_value = "Page"
        mock_page.query_selector.return_value = mock_element
        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto.return_value = mock_response

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context
        mock_pw.chromium.launch.return_value = mock_browser

        from metabolon.organelles.browser import fetch
        result = fetch("https://example.com", selector="article")

        mock_page.query_selector.assert_called_once_with("article")
        assert result["text"] == "Selected content"

    @patch("metabolon.organelles.browser.sync_playwright")
    def test_fetch_screenshot(self, mock_pw_factory):
        mock_pw = MagicMock()
        mock_pw_factory.return_value.__enter__ = MagicMock(return_value=mock_pw)
        mock_pw_factory.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.title.return_value = "Shot"
        mock_page.inner_text.return_value = "body text"
        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto.return_value = mock_response

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context
        mock_pw.chromium.launch.return_value = mock_browser

        from metabolon.organelles.browser import fetch
        result = fetch("https://example.com", screenshot="/tmp/shot.png")

        mock_page.screenshot.assert_called_once_with(path="/tmp/shot.png", full_page=True)
        assert result["screenshot"] == "/tmp/shot.png"

    @patch("metabolon.organelles.browser.sync_playwright")
    def test_fetch_pdf(self, mock_pw_factory):
        mock_pw = MagicMock()
        mock_pw_factory.return_value.__enter__ = MagicMock(return_value=mock_pw)
        mock_pw_factory.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.title.return_value = "PDF"
        mock_page.inner_text.return_value = "pdf body"
        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto.return_value = mock_response

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context
        mock_pw.chromium.launch.return_value = mock_browser

        from metabolon.organelles.browser import fetch
        result = fetch("https://example.com", pdf="/tmp/out.pdf")

        mock_page.pdf.assert_called_once_with(path="/tmp/out.pdf")
        assert result["pdf"] == "/tmp/out.pdf"

    @patch("metabolon.organelles.browser.sync_playwright")
    def test_fetch_with_wait(self, mock_pw_factory):
        mock_pw = MagicMock()
        mock_pw_factory.return_value.__enter__ = MagicMock(return_value=mock_pw)
        mock_pw_factory.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.title.return_value = "Wait"
        mock_page.inner_text.return_value = "waited"
        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto.return_value = mock_response

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context
        mock_pw.chromium.launch.return_value = mock_browser

        from metabolon.organelles.browser import fetch
        fetch("https://example.com", wait=1500)

        mock_page.wait_for_timeout.assert_called_once_with(1500)

    def test_missing_cookie_file_raises(self):
        from metabolon.organelles.browser import fetch
        with pytest.raises(FileNotFoundError, match="Cookie file not found"):
            fetch("https://example.com", cookies="/nonexistent/path/cookies.json")

    @patch("metabolon.organelles.browser.sync_playwright")
    def test_fetch_text_helper(self, mock_pw_factory):
        mock_pw = MagicMock()
        mock_pw_factory.return_value.__enter__ = MagicMock(return_value=mock_pw)
        mock_pw_factory.return_value.__exit__ = MagicMock(return_value=False)

        mock_page = MagicMock()
        mock_page.title.return_value = "Text"
        mock_page.inner_text.return_value = "just the text"
        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto.return_value = mock_response

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context
        mock_pw.chromium.launch.return_value = mock_browser

        from metabolon.organelles.browser import fetch_text
        assert fetch_text("https://example.com") == "just the text"
