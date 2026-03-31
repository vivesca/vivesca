#!/usr/bin/env python3
"""Tests for browser effector CLI wrapper and core browser module.

Uses mocks — no real browser launch required.
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Load effector via exec (effectors are scripts, not importable packages)
# Use the module's own __dict__ as exec namespace so patching the module
# attribute is visible to the exec'd functions' globals.
_effector_path = Path(__file__).parent.parent / "effectors" / "browser"
_mod = types.ModuleType("effectors.browser")
_mod.__file__ = str(_effector_path)
_mod.__name__ = "effectors.browser"
sys.modules["effectors.browser"] = _mod
exec(open(_effector_path).read(), _mod.__dict__)  # noqa: S102

main = _mod.__dict__["main"]
build_parser = _mod.__dict__["build_parser"]
format_text = _mod.__dict__["format_text"]
format_json = _mod.__dict__["format_json"]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_RESULT = {
    "title": "Example Domain",
    "url": "https://example.com/",
    "text": "This domain is for use in illustrative examples.",
    "status": 200,
    "cookies_loaded": 0,
    "screenshot_saved": False,
    "pdf_saved": False,
}


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

    def test_no_command_returns_1(self):
        assert main([]) == 1


# ---------------------------------------------------------------------------
# Format helpers
# ---------------------------------------------------------------------------


class TestFormatText:
    def test_includes_body_text(self):
        out = format_text(SAMPLE_RESULT)
        assert "This domain is for use in illustrative examples." in out

    def test_includes_metadata(self):
        out = format_text(SAMPLE_RESULT)
        assert "title: Example Domain" in out
        assert "status: 200" in out

    def test_no_json_keys_in_plain(self):
        out = format_text(SAMPLE_RESULT)
        assert "cookies_loaded" not in out


class TestFormatJson:
    def test_produces_valid_json(self):
        out = format_json(SAMPLE_RESULT)
        data = json.loads(out)
        assert data["title"] == "Example Domain"
        assert data["status"] == 200

    def test_includes_all_keys(self):
        out = format_json(SAMPLE_RESULT)
        data = json.loads(out)
        for key in ("title", "url", "text", "status", "cookies_loaded",
                     "screenshot_saved", "pdf_saved"):
            assert key in data


# ---------------------------------------------------------------------------
# CLI fetch tests — mock the async fetch inside the exec'd namespace
# ---------------------------------------------------------------------------


def _async_return(value):
    """Create a coroutine that returns *value* — for mocking async fetch."""
    async def _coro():
        return value
    return _coro()


class TestFetchCLI:
    @patch("effectors.browser.fetch")
    def test_plain_text_output(self, mock_fetch, capsys):
        mock_fetch.return_value = _async_return(SAMPLE_RESULT)
        rc = main(["fetch", "https://example.com"])
        assert rc == 0
        captured = capsys.readouterr()
        assert "This domain is for use in illustrative examples." in captured.out

    @patch("effectors.browser.fetch")
    def test_json_output(self, mock_fetch, capsys):
        mock_fetch.return_value = _async_return(SAMPLE_RESULT)
        main(["fetch", "https://example.com", "--json"])
        data = json.loads(capsys.readouterr().out)
        assert data["title"] == "Example Domain"
        assert data["status"] == 200
        assert data["text"] == SAMPLE_RESULT["text"]

    @patch("effectors.browser.fetch")
    def test_passes_cookies(self, mock_fetch):
        mock_fetch.return_value = _async_return(SAMPLE_RESULT)
        main(["fetch", "https://example.com", "--cookies", "/tmp/c.json"])
        mock_fetch.assert_called_once_with(
            "https://example.com",
            cookies="/tmp/c.json",
            selector=None,
            screenshot=None,
            pdf=None,
            wait=0,
        )

    @patch("effectors.browser.fetch")
    def test_passes_selector(self, mock_fetch):
        mock_fetch.return_value = _async_return(SAMPLE_RESULT)
        main(["fetch", "https://example.com", "--selector", "main"])
        assert mock_fetch.call_args.kwargs["selector"] == "main"

    @patch("effectors.browser.fetch")
    def test_passes_screenshot(self, mock_fetch):
        mock_fetch.return_value = _async_return(SAMPLE_RESULT)
        main(["fetch", "https://example.com", "--screenshot", "/tmp/s.png"])
        assert mock_fetch.call_args.kwargs["screenshot"] == "/tmp/s.png"

    @patch("effectors.browser.fetch")
    def test_passes_pdf(self, mock_fetch):
        mock_fetch.return_value = _async_return(SAMPLE_RESULT)
        main(["fetch", "https://example.com", "--pdf", "/tmp/out.pdf"])
        assert mock_fetch.call_args.kwargs["pdf"] == "/tmp/out.pdf"

    @patch("effectors.browser.fetch")
    def test_passes_wait(self, mock_fetch):
        mock_fetch.return_value = _async_return(SAMPLE_RESULT)
        main(["fetch", "https://example.com", "--wait", "3000"])
        assert mock_fetch.call_args.kwargs["wait"] == 3000

    @patch("effectors.browser.fetch")
    def test_json_includes_screenshot_flag(self, mock_fetch, capsys):
        result = {**SAMPLE_RESULT, "screenshot_saved": True}
        mock_fetch.return_value = _async_return(result)
        main(["fetch", "https://example.com", "--json"])
        data = json.loads(capsys.readouterr().out)
        assert data["screenshot_saved"] is True

    @patch("effectors.browser.fetch")
    def test_json_includes_pdf_flag(self, mock_fetch, capsys):
        result = {**SAMPLE_RESULT, "pdf_saved": True}
        mock_fetch.return_value = _async_return(result)
        main(["fetch", "https://example.com", "--json"])
        data = json.loads(capsys.readouterr().out)
        assert data["pdf_saved"] is True


# ---------------------------------------------------------------------------
# Core module unit tests — mock async Playwright
# ---------------------------------------------------------------------------


def _mock_async_playwright_chain(mock_pw_factory, page_text="Hello world"):
    """Wire up a mock async Playwright chain."""
    import asyncio

    mock_pw = MagicMock()

    # async context manager: async with async_playwright() as pw
    mock_pw_factory.return_value.__aenter__ = asyncio.coroutine(lambda: mock_pw)()
    mock_pw_factory.return_value.__aexit__ = asyncio.coroutine(lambda *a: None)()

    mock_browser = MagicMock()
    mock_pw.chromium.launch.return_value = asyncio.coroutine(lambda: mock_browser)()

    mock_context = MagicMock()
    mock_browser.new_context.return_value = asyncio.coroutine(lambda: mock_context)()

    mock_page = MagicMock()
    mock_page.title.return_value = asyncio.coroutine(lambda: "Test Page")()
    mock_page.inner_text.return_value = asyncio.coroutine(lambda: page_text)()
    mock_page.url = "https://example.com/"

    mock_response = MagicMock()
    mock_response.status = 200
    mock_page.goto.return_value = asyncio.coroutine(lambda: mock_response)()

    mock_page.wait_for_timeout.return_value = asyncio.coroutine(lambda ms: None)()
    mock_page.screenshot.return_value = asyncio.coroutine(lambda **kw: None)()
    mock_page.pdf.return_value = asyncio.coroutine(lambda **kw: None)()

    mock_element = MagicMock()
    mock_element.inner_text.return_value = asyncio.coroutine(lambda: "Selected content")()
    mock_page.query_selector.return_value = asyncio.coroutine(lambda sel: mock_element)()

    mock_context.new_page.return_value = asyncio.coroutine(lambda: mock_page)()
    mock_browser.close.return_value = asyncio.coroutine(lambda: None)()

    return mock_page, mock_context, mock_browser


class TestCoreFetch:
    @pytest.mark.asyncio
    async def test_basic_fetch(self):
        mock_page = MagicMock()
        mock_page.title.side_effect = lambda: _coro("Test Page")
        mock_page.inner_text.side_effect = lambda _: _coro("Hello world")
        mock_page.url = "https://example.com/"

        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto.return_value = _coro(mock_response)
        mock_page.wait_for_timeout.return_value = _coro(None)
        mock_page.screenshot.return_value = _coro(None)
        mock_page.pdf.return_value = _coro(None)

        mock_context = MagicMock()
        mock_context.new_page.return_value = _coro(mock_page)

        mock_browser = MagicMock()
        mock_browser.new_context.return_value = _coro(mock_context)
        mock_browser.close.return_value = _coro(None)

        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = _coro(mock_browser)

        with patch("metabolon.organelles.browser.async_playwright",
                   return_value=_async_ctx(mock_pw)):
            from metabolon.organelles.browser import fetch
            result = await fetch("https://example.com")

        assert result["title"] == "Test Page"
        assert result["text"] == "Hello world"
        assert result["status"] == 200
        assert result["screenshot_saved"] is False
        assert result["pdf_saved"] is False

    @pytest.mark.asyncio
    async def test_fetch_with_selector(self):
        mock_element = MagicMock()
        mock_element.inner_text.return_value = _coro("Selected content")

        mock_page = MagicMock()
        mock_page.title.return_value = _coro("Page")
        mock_page.inner_text.return_value = _coro("body")
        mock_page.url = "https://example.com/"
        mock_page.query_selector.return_value = _coro(mock_element)

        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto.return_value = _coro(mock_response)
        mock_page.wait_for_timeout.return_value = _coro(None)
        mock_page.screenshot.return_value = _coro(None)
        mock_page.pdf.return_value = _coro(None)

        mock_context = MagicMock()
        mock_context.new_page.return_value = _coro(mock_page)

        mock_browser = MagicMock()
        mock_browser.new_context.return_value = _coro(mock_context)
        mock_browser.close.return_value = _coro(None)

        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = _coro(mock_browser)

        with patch("metabolon.organelles.browser.async_playwright",
                   return_value=_async_ctx(mock_pw)):
            from metabolon.organelles.browser import fetch
            result = await fetch("https://example.com", selector="article")

        mock_page.query_selector.assert_called_once_with("article")
        assert result["text"] == "Selected content"

    @pytest.mark.asyncio
    async def test_fetch_screenshot(self):
        mock_page = MagicMock()
        mock_page.title.return_value = _coro("Shot")
        mock_page.inner_text.return_value = _coro("body text")
        mock_page.url = "https://example.com/"

        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto.return_value = _coro(mock_response)
        mock_page.wait_for_timeout.return_value = _coro(None)
        mock_page.screenshot.return_value = _coro(None)
        mock_page.pdf.return_value = _coro(None)

        mock_context = MagicMock()
        mock_context.new_page.return_value = _coro(mock_page)

        mock_browser = MagicMock()
        mock_browser.new_context.return_value = _coro(mock_context)
        mock_browser.close.return_value = _coro(None)

        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = _coro(mock_browser)

        with patch("metabolon.organelles.browser.async_playwright",
                   return_value=_async_ctx(mock_pw)):
            from metabolon.organelles.browser import fetch
            result = await fetch("https://example.com", screenshot="/tmp/shot.png")

        mock_page.screenshot.assert_called_once_with(path="/tmp/shot.png")
        assert result["screenshot_saved"] is True

    @pytest.mark.asyncio
    async def test_fetch_pdf(self):
        mock_page = MagicMock()
        mock_page.title.return_value = _coro("PDF")
        mock_page.inner_text.return_value = _coro("pdf body")
        mock_page.url = "https://example.com/"

        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto.return_value = _coro(mock_response)
        mock_page.wait_for_timeout.return_value = _coro(None)
        mock_page.screenshot.return_value = _coro(None)
        mock_page.pdf.return_value = _coro(None)

        mock_context = MagicMock()
        mock_context.new_page.return_value = _coro(mock_page)

        mock_browser = MagicMock()
        mock_browser.new_context.return_value = _coro(mock_context)
        mock_browser.close.return_value = _coro(None)

        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = _coro(mock_browser)

        with patch("metabolon.organelles.browser.async_playwright",
                   return_value=_async_ctx(mock_pw)):
            from metabolon.organelles.browser import fetch
            result = await fetch("https://example.com", pdf="/tmp/out.pdf")

        mock_page.pdf.assert_called_once_with(path="/tmp/out.pdf")
        assert result["pdf_saved"] is True

    @pytest.mark.asyncio
    async def test_fetch_with_wait(self):
        mock_page = MagicMock()
        mock_page.title.return_value = _coro("Wait")
        mock_page.inner_text.return_value = _coro("waited")
        mock_page.url = "https://example.com/"

        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto.return_value = _coro(mock_response)
        mock_page.wait_for_timeout.return_value = _coro(None)
        mock_page.screenshot.return_value = _coro(None)
        mock_page.pdf.return_value = _coro(None)

        mock_context = MagicMock()
        mock_context.new_page.return_value = _coro(mock_page)

        mock_browser = MagicMock()
        mock_browser.new_context.return_value = _coro(mock_context)
        mock_browser.close.return_value = _coro(None)

        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = _coro(mock_browser)

        with patch("metabolon.organelles.browser.async_playwright",
                   return_value=_async_ctx(mock_pw)):
            from metabolon.organelles.browser import fetch
            await fetch("https://example.com", wait=1500)

        mock_page.wait_for_timeout.assert_called_once_with(1500)

    @pytest.mark.asyncio
    async def test_cookies_loaded(self):
        mock_page = MagicMock()
        mock_page.title.return_value = _coro("Cookied")
        mock_page.inner_text.return_value = _coro("secret")
        mock_page.url = "https://example.com/"

        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto.return_value = _coro(mock_response)
        mock_page.wait_for_timeout.return_value = _coro(None)
        mock_page.screenshot.return_value = _coro(None)
        mock_page.pdf.return_value = _coro(None)

        mock_context = MagicMock()
        mock_context.new_page.return_value = _coro(mock_page)
        mock_context.add_cookies.return_value = _coro(None)

        mock_browser = MagicMock()
        mock_browser.new_context.return_value = _coro(mock_context)
        mock_browser.close.return_value = _coro(None)

        mock_pw = MagicMock()
        mock_pw.chromium.launch.return_value = _coro(mock_browser)

        import tempfile, os
        cookie_data = [{"name": "session", "value": "abc", "domain": ".example.com"}]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(cookie_data, f)
            cookie_path = f.name

        try:
            with patch("metabolon.organelles.browser.async_playwright",
                       return_value=_async_ctx(mock_pw)):
                from metabolon.organelles.browser import fetch
                result = await fetch("https://example.com", cookies=cookie_path)

            assert result["cookies_loaded"] == 1
            mock_context.add_cookies.assert_called_once_with(cookie_data)
        finally:
            os.unlink(cookie_path)


# ---------------------------------------------------------------------------
# Helpers for async mocking
# ---------------------------------------------------------------------------

def _coro(value):
    """Return a coroutine that yields *value*."""
    async def _c():
        return value
    return _c()


class _AsyncCtx:
    """Shim so `async with <instance>` yields *obj*."""
    def __init__(self, obj):
        self._obj = obj

    async def __aenter__(self):
        return self._obj

    async def __aexit__(self, *args):
        pass


def _async_ctx(obj):
    return _AsyncCtx(obj)
