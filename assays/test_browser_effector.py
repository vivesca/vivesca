#!/usr/bin/env python3
"""Tests for browser effector CLI wrapper and core browser module.

Uses mocks — no real browser launch required.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

# Load effector via exec (no .py extension, per coaching notes)
_effector_path = Path(__file__).parent.parent / "effectors" / "browser"
_ns: dict = {"__name__": "browser_effector"}
exec(open(_effector_path).read(), _ns)

main = _ns["main"]
build_parser = _ns["build_parser"]
run_fetch = _ns["run_fetch"]

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
# CLI fetch tests — mock _async_fetch in the exec'd namespace
# ---------------------------------------------------------------------------

SAMPLE_RESULT = {
    "url": "https://example.com",
    "title": "Example Domain",
    "text": "This domain is for use in illustrative examples.",
    "status": 200,
    "cookies_loaded": 0,
    "screenshot_saved": False,
    "pdf_saved": False,
}


class TestCLIFetch:
    def test_plain_text_output(self, capsys):
        _ns["_async_fetch"] = AsyncMock(return_value=SAMPLE_RESULT)
        main(["fetch", "https://example.com"])
        captured = capsys.readouterr()
        assert "This domain is for use in illustrative examples." in captured.out
        assert "title" not in captured.out

    def test_json_output(self, capsys):
        _ns["_async_fetch"] = AsyncMock(return_value=SAMPLE_RESULT)
        main(["fetch", "https://example.com", "--json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["title"] == "Example Domain"
        assert data["status"] == 200
        assert data["text"] == SAMPLE_RESULT["text"]

    def test_passes_all_options(self):
        mock_fetch = AsyncMock(return_value=SAMPLE_RESULT)
        _ns["_async_fetch"] = mock_fetch
        main([
            "fetch", "https://example.com",
            "--cookies", "/tmp/c.json",
            "--selector", "article",
            "--screenshot", "/tmp/s.png",
            "--pdf", "/tmp/out.pdf",
            "--wait", "3000",
        ])
        mock_fetch.assert_called_once_with(
            "https://example.com",
            cookies="/tmp/c.json",
            selector="article",
            screenshot="/tmp/s.png",
            pdf="/tmp/out.pdf",
            wait=3000,
        )

    def test_error_exits_1(self, capsys):
        _ns["_async_fetch"] = AsyncMock(side_effect=RuntimeError("timeout"))
        with pytest.raises(SystemExit) as exc_info:
            main(["fetch", "https://example.com"])
        assert exc_info.value.code == 1
        assert "timeout" in capsys.readouterr().err

    def test_json_includes_screenshot_and_pdf(self, capsys):
        result = {**SAMPLE_RESULT, "screenshot_saved": True, "pdf_saved": True}
        _ns["_async_fetch"] = AsyncMock(return_value=result)
        main(["fetch", "https://example.com", "--json"])
        data = json.loads(capsys.readouterr().out)
        assert data["screenshot_saved"] is True
        assert data["pdf_saved"] is True


# ---------------------------------------------------------------------------
# Core module unit tests — mock Playwright
# ---------------------------------------------------------------------------


def _make_mock_pw():
    """Build a mock async Playwright context chain."""
    mock_pw = AsyncMock()
    mock_browser = AsyncMock()
    mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

    mock_context = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)

    mock_page = AsyncMock()
    mock_page.title = AsyncMock(return_value="Test Page")
    mock_page.inner_text = AsyncMock(return_value="Hello world")
    mock_page.url = "https://example.com"
    mock_response = MagicMock()
    mock_response.status = 200
    mock_page.goto = AsyncMock(return_value=mock_response)

    mock_context.new_page = AsyncMock(return_value=mock_page)

    return mock_pw, mock_browser, mock_context, mock_page


class TestCoreFetch:
    def test_basic_fetch(self):
        mock_pw, mock_browser, mock_context, mock_page = _make_mock_pw()

        with patch("metabolon.organelles.browser.async_playwright", return_value=mock_pw):
            from metabolon.organelles.browser import fetch
            result = asyncio.run(fetch("https://example.com"))

        assert result["title"] == "Test Page"
        assert result["text"] == "Hello world"
        assert result["status"] == 200
        assert result["cookies_loaded"] == 0
        assert result["screenshot_saved"] is False
        assert result["pdf_saved"] is False

    def test_fetch_with_selector(self):
        mock_pw, _, _, mock_page = _make_mock_pw()
        mock_element = AsyncMock()
        mock_element.inner_text = AsyncMock(return_value="Selected content")
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        with patch("metabolon.organelles.browser.async_playwright", return_value=mock_pw):
            from metabolon.organelles.browser import fetch
            result = asyncio.run(fetch("https://example.com", selector="article"))

        assert result["text"] == "Selected content"

    def test_fetch_screenshot(self):
        mock_pw, _, _, mock_page = _make_mock_pw()
        mock_page.screenshot = AsyncMock()

        with patch("metabolon.organelles.browser.async_playwright", return_value=mock_pw):
            from metabolon.organelles.browser import fetch
            result = asyncio.run(fetch("https://example.com", screenshot="/tmp/shot.png"))

        mock_page.screenshot.assert_called_once_with(path="/tmp/shot.png")
        assert result["screenshot_saved"] is True

    def test_fetch_pdf(self):
        mock_pw, _, _, mock_page = _make_mock_pw()
        mock_page.pdf = AsyncMock()

        with patch("metabolon.organelles.browser.async_playwright", return_value=mock_pw):
            from metabolon.organelles.browser import fetch
            result = asyncio.run(fetch("https://example.com", pdf="/tmp/out.pdf"))

        mock_page.pdf.assert_called_once_with(path="/tmp/out.pdf")
        assert result["pdf_saved"] is True

    def test_fetch_with_wait(self):
        mock_pw, _, _, mock_page = _make_mock_pw()
        mock_page.wait_for_timeout = AsyncMock()

        with patch("metabolon.organelles.browser.async_playwright", return_value=mock_pw):
            from metabolon.organelles.browser import fetch
            asyncio.run(fetch("https://example.com", wait=1500))

        mock_page.wait_for_timeout.assert_called_once_with(1500)

    def test_fetch_with_cookies(self):
        import tempfile
        mock_pw, _, mock_context, _ = _make_mock_pw()
        mock_context.add_cookies = AsyncMock()

        cookies = [{"name": "session", "value": "abc", "domain": ".example.com"}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(cookies, f)
            cookie_path = f.name

        try:
            with patch("metabolon.organelles.browser.async_playwright", return_value=mock_pw):
                from metabolon.organelles.browser import fetch
                result = asyncio.run(fetch("https://example.com", cookies=cookie_path))
            mock_context.add_cookies.assert_called_once_with(cookies)
            assert result["cookies_loaded"] == 1
        finally:
            Path(cookie_path).unlink()

    def test_missing_cookie_file_loads_zero(self):
        mock_pw, _, _, _ = _make_mock_pw()

        with patch("metabolon.organelles.browser.async_playwright", return_value=mock_pw):
            from metabolon.organelles.browser import fetch
            result = asyncio.run(fetch("https://example.com", cookies="/nonexistent/cookies.json"))

        assert result["cookies_loaded"] == 0
