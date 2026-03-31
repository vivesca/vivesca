#!/usr/bin/env python3
"""Tests for browser effector CLI wrapper and core browser module.

Uses mocks — no real browser launch required.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Load effector via exec (no .py extension)
_effector_path = Path(__file__).parent.parent / "effectors" / "browser"
_ns: dict = {"__name__": "browser_effector"}
exec(open(_effector_path).read(), _ns)

main = _ns["main"]
build_parser = _ns["build_parser"]

# Patch target inside the exec'd namespace
_FETCH_TARGET = "browser_effector.fetch"

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
# CLI fetch tests — mock browser.fetch inside the exec'd namespace
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
    @patch(_FETCH_TARGET, return_value=SAMPLE_RESULT)
    def test_plain_text_output(self, mock_fetch, capsys):
        main(["fetch", "https://example.com"])
        captured = capsys.readouterr()
        assert "This domain is for use in illustrative examples." in captured.out
        assert "title" not in captured.out

    @patch(_FETCH_TARGET, return_value=SAMPLE_RESULT)
    def test_json_output(self, mock_fetch, capsys):
        main(["fetch", "https://example.com", "--json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["title"] == "Example Domain"
        assert data["status"] == 200
        assert data["text"] == SAMPLE_RESULT["text"]

    @patch(_FETCH_TARGET, return_value=SAMPLE_RESULT)
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

    @patch(_FETCH_TARGET, return_value=SAMPLE_RESULT)
    def test_passes_selector(self, mock_fetch):
        main(["fetch", "https://example.com", "--selector", "main"])
        assert mock_fetch.call_args.kwargs["selector"] == "main"

    @patch(_FETCH_TARGET, return_value=SAMPLE_RESULT)
    def test_passes_screenshot(self, mock_fetch):
        main(["fetch", "https://example.com", "--screenshot", "/tmp/s.png"])
        assert mock_fetch.call_args.kwargs["screenshot"] == "/tmp/s.png"

    @patch(_FETCH_TARGET, return_value=SAMPLE_RESULT)
    def test_passes_pdf(self, mock_fetch):
        main(["fetch", "https://example.com", "--pdf", "/tmp/out.pdf"])
        assert mock_fetch.call_args.kwargs["pdf"] == "/tmp/out.pdf"

    @patch(_FETCH_TARGET, return_value=SAMPLE_RESULT)
    def test_passes_wait(self, mock_fetch):
        main(["fetch", "https://example.com", "--wait", "3000"])
        assert mock_fetch.call_args.kwargs["wait"] == 3000

    @patch(_FETCH_TARGET, side_effect=FileNotFoundError("Cookie file not found: /tmp/nope"))
    def test_missing_cookies_exits_1(self, mock_fetch, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["fetch", "https://example.com", "--cookies", "/tmp/nope"])
        assert exc_info.value.code == 1
        assert "Cookie file" in capsys.readouterr().err

    @patch(_FETCH_TARGET, side_effect=RuntimeError("timeout"))
    def test_generic_error_exits_1(self, mock_fetch, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["fetch", "https://example.com"])
        assert exc_info.value.code == 1
        assert "timeout" in capsys.readouterr().err

    @patch(_FETCH_TARGET)
    def test_json_includes_screenshot_path(self, mock_fetch, capsys):
        mock_fetch.return_value = {**SAMPLE_RESULT, "screenshot": "/tmp/shot.png"}
        main(["fetch", "https://example.com", "--json"])
        data = json.loads(capsys.readouterr().out)
        assert data["screenshot"] == "/tmp/shot.png"

    @patch(_FETCH_TARGET)
    def test_json_includes_pdf_path(self, mock_fetch, capsys):
        mock_fetch.return_value = {**SAMPLE_RESULT, "pdf": "/tmp/page.pdf"}
        main(["fetch", "https://example.com", "--json"])
        data = json.loads(capsys.readouterr().out)
        assert data["pdf"] == "/tmp/page.pdf"


# ---------------------------------------------------------------------------
# Core module unit tests — mock Playwright itself
# ---------------------------------------------------------------------------


def _mock_playwright_chain(mock_pw_factory, page_return_value=None):
    """Wire up a mock Playwright chain for sync_playwright()."""
    mock_pw = MagicMock()
    mock_pw_factory.return_value.__enter__ = MagicMock(return_value=mock_pw)
    mock_pw_factory.return_value.__exit__ = MagicMock(return_value=False)

    mock_page = MagicMock()
    mock_page.title.return_value = "Test Page"
    mock_page.inner_text.return_value = page_return_value or "Hello world"
    mock_response = MagicMock()
    mock_response.status = 200
    mock_page.goto.return_value = mock_response

    mock_context = MagicMock()
    mock_context.new_page.return_value = mock_page
    mock_browser = MagicMock()
    mock_browser.new_context.return_value = mock_context
    mock_pw.chromium.launch.return_value = mock_browser

    return mock_page, mock_context, mock_browser


class TestCoreFetch:
    @patch("metabolon.organelles.browser.sync_playwright")
    def test_basic_fetch(self, mock_pw_factory):
        mock_page, _, _ = _mock_playwright_chain(mock_pw_factory)

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
        mock_page, _, _ = _mock_playwright_chain(mock_pw_factory)
        mock_element = MagicMock()
        mock_element.inner_text.return_value = "Selected content"
        mock_page.query_selector.return_value = mock_element

        from metabolon.organelles.browser import fetch
        result = fetch("https://example.com", selector="article")

        mock_page.query_selector.assert_called_once_with("article")
        assert result["text"] == "Selected content"

    @patch("metabolon.organelles.browser.sync_playwright")
    def test_fetch_screenshot(self, mock_pw_factory):
        mock_page, _, _ = _mock_playwright_chain(mock_pw_factory)

        from metabolon.organelles.browser import fetch
        result = fetch("https://example.com", screenshot="/tmp/shot.png")

        mock_page.screenshot.assert_called_once_with(path="/tmp/shot.png", full_page=True)
        assert result["screenshot"] == "/tmp/shot.png"

    @patch("metabolon.organelles.browser.sync_playwright")
    def test_fetch_pdf(self, mock_pw_factory):
        mock_page, _, _ = _mock_playwright_chain(mock_pw_factory)

        from metabolon.organelles.browser import fetch
        result = fetch("https://example.com", pdf="/tmp/out.pdf")

        mock_page.pdf.assert_called_once_with(path="/tmp/out.pdf")
        assert result["pdf"] == "/tmp/out.pdf"

    @patch("metabolon.organelles.browser.sync_playwright")
    def test_fetch_with_wait(self, mock_pw_factory):
        mock_page, _, _ = _mock_playwright_chain(mock_pw_factory)

        from metabolon.organelles.browser import fetch
        fetch("https://example.com", wait=1500)

        mock_page.wait_for_timeout.assert_called_once_with(1500)

    def test_missing_cookie_file_raises(self):
        from metabolon.organelles.browser import fetch
        with pytest.raises(FileNotFoundError, match="Cookie file not found"):
            fetch("https://example.com", cookies="/nonexistent/path/cookies.json")

    @patch("metabolon.organelles.browser.sync_playwright")
    def test_fetch_text_helper(self, mock_pw_factory):
        _mock_playwright_chain(mock_pw_factory, page_return_value="just the text")

        from metabolon.organelles.browser import fetch_text
        assert fetch_text("https://example.com") == "just the text"
