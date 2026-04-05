from __future__ import annotations

"""Tests for metabolon.organelles.browser — headless page fetcher.

Every test mocks async_playwright so no browser is launched.
"""

import json
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metabolon.organelles.browser import fetch

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers to build a mock Playwright stack
# ---------------------------------------------------------------------------


def _make_mock_pw(
    *,
    page_title: str = "Test Page",
    page_url: str = "https://example.com",
    inner_text: str = "hello world",
    status: int = 200,
    element_text: str | None = None,
):
    """Return an async-context-manager that looks like ``async_playwright()``.

    Returns (mock_pw_cm, page, context, browser) so tests can make extra
    assertions on the page/context/browser objects.
    """
    page = AsyncMock()
    page.title = AsyncMock(return_value=page_title)
    page.url = page_url
    page.inner_text = AsyncMock(return_value=inner_text)
    page.goto = AsyncMock(return_value=MagicMock(status=status))
    page.wait_for_timeout = AsyncMock()
    page.screenshot = AsyncMock()
    page.pdf = AsyncMock()

    # query_selector returns an element whose inner_text returns element_text
    if element_text is not None:
        elem = AsyncMock()
        elem.inner_text = AsyncMock(return_value=element_text)
        page.query_selector = AsyncMock(return_value=elem)
    else:
        page.query_selector = AsyncMock(return_value=None)

    context = AsyncMock()
    context.new_page = AsyncMock(return_value=page)
    context.add_cookies = AsyncMock()

    browser = AsyncMock()
    browser.new_context = AsyncMock(return_value=context)
    browser.close = AsyncMock()

    pw = MagicMock()
    pw.chromium.launch = AsyncMock(return_value=browser)

    pw_cm = AsyncMock()
    pw_cm.__aenter__ = AsyncMock(return_value=pw)
    pw_cm.__aexit__ = AsyncMock(return_value=False)

    return pw_cm, page, context, browser


# ---------------------------------------------------------------------------
# Basic fetch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_basic_fetch():
    """fetch returns dict with expected keys and values."""
    pw_cm, _page, _ctx, _br = _make_mock_pw()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        result = await fetch("https://example.com")

    assert result["title"] == "Test Page"
    assert result["url"] == "https://example.com"
    assert result["text"] == "hello world"
    assert result["status"] == 200
    assert result["cookies_loaded"] == 0
    assert result["screenshot_saved"] is False
    assert result["pdf_saved"] is False


# ---------------------------------------------------------------------------
# Cookies
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cookies_loaded(tmp_path: Path):
    """fetch loads cookies from a JSON file and reports count."""
    cookie_file = tmp_path / "cookies.json"
    cookies = [{"name": "sid", "value": "abc", "domain": ".example.com"}]
    cookie_file.write_text(json.dumps(cookies))

    pw_cm, _page, ctx, _br = _make_mock_pw()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        result = await fetch("https://example.com", cookies=str(cookie_file))

    assert result["cookies_loaded"] == 1
    ctx.add_cookies.assert_awaited_once_with(cookies)


@pytest.mark.asyncio
async def test_cookies_file_missing(tmp_path: Path):
    """Missing cookie file results in cookies_loaded == 0, no crash."""
    pw_cm, _page, ctx, _br = _make_mock_pw()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        result = await fetch("https://example.com", cookies=str(tmp_path / "nope.json"))

    assert result["cookies_loaded"] == 0
    ctx.add_cookies.assert_not_awaited()


@pytest.mark.asyncio
async def test_cookies_not_list(tmp_path: Path):
    """Cookie file with non-list JSON does not load cookies."""
    cookie_file = tmp_path / "cookies.json"
    cookie_file.write_text('{"not": "a list"}')

    pw_cm, _page, _ctx, _br = _make_mock_pw()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        result = await fetch("https://example.com", cookies=str(cookie_file))

    assert result["cookies_loaded"] == 0


# ---------------------------------------------------------------------------
# Selector
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_selector_returns_element_text():
    """When selector is given, inner_text of the matched element is returned."""
    pw_cm, page, _ctx, _br = _make_mock_pw(element_text="selected content")
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        result = await fetch("https://example.com", selector="div.main")

    assert result["text"] == "selected content"
    page.query_selector.assert_awaited_once_with("div.main")


@pytest.mark.asyncio
async def test_selector_no_match_returns_empty():
    """When selector matches nothing, text is empty string."""
    pw_cm, page, _ctx, _br = _make_mock_pw()
    page.query_selector = AsyncMock(return_value=None)
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        result = await fetch("https://example.com", selector="div.missing")

    assert result["text"] == ""


# ---------------------------------------------------------------------------
# Screenshot
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_screenshot_saved(tmp_path: Path):
    """When screenshot path is given, screenshot is taken and flag is True."""
    shot_path = str(tmp_path / "out.png")
    pw_cm, page, _ctx, _br = _make_mock_pw()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        result = await fetch("https://example.com", screenshot=shot_path)

    assert result["screenshot_saved"] is True
    page.screenshot.assert_awaited_once_with(path=shot_path)


@pytest.mark.asyncio
async def test_no_screenshot_by_default():
    """screenshot_saved is False when no screenshot path is given."""
    pw_cm, _, _, _ = _make_mock_pw()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        result = await fetch("https://example.com")

    assert result["screenshot_saved"] is False


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pdf_saved(tmp_path: Path):
    """When pdf path is given, pdf is rendered and flag is True."""
    pdf_path = str(tmp_path / "out.pdf")
    pw_cm, page, _ctx, _br = _make_mock_pw()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        result = await fetch("https://example.com", pdf=pdf_path)

    assert result["pdf_saved"] is True
    page.pdf.assert_awaited_once_with(path=pdf_path)


@pytest.mark.asyncio
async def test_no_pdf_by_default():
    """pdf_saved is False when no pdf path is given."""
    pw_cm, _, _, _ = _make_mock_pw()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        result = await fetch("https://example.com")

    assert result["pdf_saved"] is False


# ---------------------------------------------------------------------------
# Wait
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_wait_parameter():
    """wait > 0 triggers page.wait_for_timeout with the given ms."""
    pw_cm, page, _, _ = _make_mock_pw()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        await fetch("https://example.com", wait=500)

    page.wait_for_timeout.assert_awaited_once_with(500)


@pytest.mark.asyncio
async def test_zero_wait_skips_timeout():
    """wait=0 (default) does not call page.wait_for_timeout."""
    pw_cm, page, _, _ = _make_mock_pw()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        await fetch("https://example.com")

    page.wait_for_timeout.assert_not_awaited()


# ---------------------------------------------------------------------------
# Response status edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_null_response_status_zero():
    """When page.goto returns None (e.g. navigation error), status is 0."""
    pw_cm, page, _, _ = _make_mock_pw()
    page.goto = AsyncMock(return_value=None)
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        result = await fetch("https://example.com")

    assert result["status"] == 0


# ---------------------------------------------------------------------------
# Browser lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_browser_closed():
    """browser.close() is always called."""
    pw_cm, _, _, br = _make_mock_pw()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        await fetch("https://example.com")

    br.close.assert_awaited_once()


# ---------------------------------------------------------------------------
# Multiple cookies
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_multiple_cookies(tmp_path: Path):
    """Multiple cookies in the file are all loaded."""
    cookie_file = tmp_path / "cookies.json"
    cookies = [
        {"name": "sid", "value": "abc", "domain": ".example.com"},
        {"name": "theme", "value": "dark", "domain": ".example.com"},
        {"name": "lang", "value": "en", "domain": ".example.com"},
    ]
    cookie_file.write_text(json.dumps(cookies))

    pw_cm, _, _ctx, _ = _make_mock_pw()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        result = await fetch("https://example.com", cookies=str(cookie_file))

    assert result["cookies_loaded"] == 3
