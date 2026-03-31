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

# Load effector via exec (effectors are scripts, not importable packages).
# Use the module's own __dict__ as exec namespace so @patch modifies the
# same dict that the exec'd functions reference as their globals.
_effector_path = Path(__file__).parent.parent / "effectors" / "browser"
_mod = types.ModuleType("effectors.browser")
_mod.__file__ = str(_effector_path)
_mod.__name__ = "effectors.browser"
sys.modules["effectors.browser"] = _mod
exec(open(_effector_path).read(), _mod.__dict__)  # noqa: S102

main = _mod.__dict__["main"]
build_parser = _mod.__dict__["build_parser"]

# The effector imports fetch as _async_fetch — that's the patch target.
_FETCH_TARGET = "effectors.browser._async_fetch"


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

    def test_no_command_exits(self):
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# CLI fetch tests — mock the async fetch inside the exec'd namespace
# ---------------------------------------------------------------------------


class TestFetchCLI:
    @patch(_FETCH_TARGET)
    def test_plain_text_output(self, mock_fetch, capsys):
        mock_fetch.return_value = SAMPLE_RESULT
        main(["fetch", "https://example.com"])
        captured = capsys.readouterr()
        assert "This domain is for use in illustrative examples." in captured.out

    @patch(_FETCH_TARGET)
    def test_json_output(self, mock_fetch, capsys):
        mock_fetch.return_value = SAMPLE_RESULT
        main(["fetch", "https://example.com", "--json"])
        data = json.loads(capsys.readouterr().out)
        assert data["title"] == "Example Domain"
        assert data["status"] == 200
        assert data["text"] == SAMPLE_RESULT["text"]

    @patch(_FETCH_TARGET)
    def test_passes_cookies(self, mock_fetch):
        mock_fetch.return_value = SAMPLE_RESULT
        main(["fetch", "https://example.com", "--cookies", "/tmp/c.json"])
        mock_fetch.assert_called_once_with(
            "https://example.com",
            cookies="/tmp/c.json",
            selector=None,
            screenshot=None,
            pdf=None,
            wait=0,
        )

    @patch(_FETCH_TARGET)
    def test_passes_selector(self, mock_fetch):
        mock_fetch.return_value = SAMPLE_RESULT
        main(["fetch", "https://example.com", "--selector", "main"])
        assert mock_fetch.call_args.kwargs["selector"] == "main"

    @patch(_FETCH_TARGET)
    def test_passes_screenshot(self, mock_fetch):
        mock_fetch.return_value = SAMPLE_RESULT
        main(["fetch", "https://example.com", "--screenshot", "/tmp/s.png"])
        assert mock_fetch.call_args.kwargs["screenshot"] == "/tmp/s.png"

    @patch(_FETCH_TARGET)
    def test_passes_pdf(self, mock_fetch):
        mock_fetch.return_value = SAMPLE_RESULT
        main(["fetch", "https://example.com", "--pdf", "/tmp/out.pdf"])
        assert mock_fetch.call_args.kwargs["pdf"] == "/tmp/out.pdf"

    @patch(_FETCH_TARGET)
    def test_passes_wait(self, mock_fetch):
        mock_fetch.return_value = SAMPLE_RESULT
        main(["fetch", "https://example.com", "--wait", "3000"])
        assert mock_fetch.call_args.kwargs["wait"] == 3000

    @patch(_FETCH_TARGET, side_effect=RuntimeError("timeout"))
    def test_generic_error_exits_1(self, mock_fetch, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["fetch", "https://example.com"])
        assert exc_info.value.code == 1
        assert "timeout" in capsys.readouterr().err

    @patch(_FETCH_TARGET)
    def test_json_includes_screenshot_flag(self, mock_fetch, capsys):
        mock_fetch.return_value = {**SAMPLE_RESULT, "screenshot_saved": True}
        main(["fetch", "https://example.com", "--json"])
        data = json.loads(capsys.readouterr().out)
        assert data["screenshot_saved"] is True

    @patch(_FETCH_TARGET)
    def test_json_includes_pdf_flag(self, mock_fetch, capsys):
        mock_fetch.return_value = {**SAMPLE_RESULT, "pdf_saved": True}
        main(["fetch", "https://example.com", "--json"])
        data = json.loads(capsys.readouterr().out)
        assert data["pdf_saved"] is True


# ---------------------------------------------------------------------------
# Core module unit tests — mock async Playwright
# ---------------------------------------------------------------------------


def _coro(value):
    """Return a coroutine that resolves to *value*."""
    async def _c():
        return value
    return _c()


class _AsyncCtx:
    """Shim so ``async with <instance>`` yields *obj*."""
    def __init__(self, obj):
        self._obj = obj

    async def __aenter__(self):
        return self._obj

    async def __aexit__(self, *args):
        pass


class TestCoreFetch:
    @pytest.mark.asyncio
    async def test_basic_fetch(self):
        mock_page = MagicMock()
        mock_page.title.return_value = _coro("Test Page")
        mock_page.inner_text.return_value = _coro("Hello world")
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
                   return_value=_AsyncCtx(mock_pw)):
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
                   return_value=_AsyncCtx(mock_pw)):
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
                   return_value=_AsyncCtx(mock_pw)):
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
                   return_value=_AsyncCtx(mock_pw)):
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
                   return_value=_AsyncCtx(mock_pw)):
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
                       return_value=_AsyncCtx(mock_pw)):
                from metabolon.organelles.browser import fetch
                result = await fetch("https://example.com", cookies=cookie_path)

            assert result["cookies_loaded"] == 1
            mock_context.add_cookies.assert_called_once_with(cookie_data)
        finally:
            os.unlink(cookie_path)
