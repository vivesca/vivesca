"""Tests for metabolon.organelles.browser — additional scenarios.

Complements test_organelles_browser.py with edge-case and integration-style
coverage. All tests mock async_playwright so no real browser is launched.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metabolon.organelles.browser import fetch


def _mock_pw_stack(
    *,
    title: str = "Page",
    url: str = "https://example.com",
    body_text: str = "body text",
    status: int = 200,
):
    """Build a mock async_playwright context-manager stack."""
    page = AsyncMock()
    page.title = AsyncMock(return_value=title)
    page.url = url
    page.inner_text = AsyncMock(return_value=body_text)
    page.goto = AsyncMock(return_value=MagicMock(status=status))
    page.wait_for_timeout = AsyncMock()
    page.screenshot = AsyncMock()
    page.pdf = AsyncMock()
    page.query_selector = AsyncMock(return_value=None)

    context = AsyncMock()
    context.new_page = AsyncMock(return_value=page)
    context.add_cookies = AsyncMock()

    browser = AsyncMock()
    browser.new_context = AsyncMock(return_value=context)
    browser.close = AsyncMock()

    pw = MagicMock()
    pw.chromium.launch = AsyncMock(return_value=browser)

    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=pw)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm, page, context, browser


# 1. Return dict has exactly the expected keys
@pytest.mark.asyncio
async def test_return_keys():
    pw_cm, *_ = _mock_pw_stack()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        result = await fetch("https://example.com")

    expected_keys = {
        "title", "url", "text", "status",
        "cookies_loaded", "screenshot_saved", "pdf_saved",
    }
    assert set(result.keys()) == expected_keys


# 2. page.goto is called with the exact URL passed to fetch
@pytest.mark.asyncio
async def test_goto_receives_url():
    pw_cm, page, *_ = _mock_pw_stack()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        await fetch("https://httpbin.org/get")

    page.goto.assert_awaited_once_with(
        "https://httpbin.org/get", wait_until="domcontentloaded",
    )


# 3. chromium.launch is called with headless=True
@pytest.mark.asyncio
async def test_launch_headless():
    pw_cm, _, _, _ = _mock_pw_stack()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm) as mock_pw_factory:
        await fetch("https://example.com")

    # The CM was returned by the factory; the pw inside has chromium.launch
    pw_cm.__aenter__.return_value.chromium.launch.assert_awaited_once_with(headless=True)


# 4. Malformed JSON cookie file does not crash — cookies_loaded stays 0
@pytest.mark.asyncio
async def test_malformed_cookie_file(tmp_path: Path):
    cookie_file = tmp_path / "bad.json"
    cookie_file.write_text("this is not json at all")

    pw_cm, _, ctx, _ = _mock_pw_stack()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        # json.loads will raise — but the source doesn't catch it, so we
        # expect the exception to propagate. Verify the exception type.
        with pytest.raises(json.JSONDecodeError):
            await fetch("https://example.com", cookies=str(cookie_file))


# 5. All optional features combined (cookies + selector + screenshot + pdf + wait)
@pytest.mark.asyncio
async def test_all_options_combined(tmp_path: Path):
    # cookies
    cookie_file = tmp_path / "ck.json"
    cookie_data = [
        {"name": "a", "value": "1", "domain": ".x.com"},
        {"name": "b", "value": "2", "domain": ".x.com"},
    ]
    cookie_file.write_text(json.dumps(cookie_data))

    # selector element
    elem = AsyncMock()
    elem.inner_text = AsyncMock(return_value="selected")

    pw_cm, page, ctx, br = _mock_pw_stack()
    page.query_selector = AsyncMock(return_value=elem)

    shot = str(tmp_path / "s.png")
    pdf = str(tmp_path / "p.pdf")

    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        result = await fetch(
            "https://example.com",
            cookies=str(cookie_file),
            selector="h1",
            screenshot=shot,
            pdf=pdf,
            wait=300,
        )

    assert result["cookies_loaded"] == 2
    assert result["text"] == "selected"
    assert result["screenshot_saved"] is True
    assert result["pdf_saved"] is True
    page.wait_for_timeout.assert_awaited_once_with(300)
    page.screenshot.assert_awaited_once_with(path=shot)
    page.pdf.assert_awaited_once_with(path=pdf)
    ctx.add_cookies.assert_awaited_once_with(cookie_data)


# 6. Empty cookie list still sets cookies_loaded to 0
@pytest.mark.asyncio
async def test_empty_cookie_list(tmp_path: Path):
    cookie_file = tmp_path / "empty.json"
    cookie_file.write_text("[]")

    pw_cm, _, ctx, _ = _mock_pw_stack()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        result = await fetch("https://example.com", cookies=str(cookie_file))

    assert result["cookies_loaded"] == 0
    # Empty list is still a list — add_cookies IS called with []
    ctx.add_cookies.assert_awaited_once_with([])


# 7. cookies=None does not attempt to load any file
@pytest.mark.asyncio
async def test_no_cookies_param():
    pw_cm, _, ctx, _ = _mock_pw_stack()
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        result = await fetch("https://example.com")

    assert result["cookies_loaded"] == 0
    ctx.add_cookies.assert_not_awaited()


# 8. Non-200 HTTP status is reported faithfully
@pytest.mark.asyncio
async def test_non_200_status():
    pw_cm, *_ = _mock_pw_stack(status=404)
    with patch("metabolon.organelles.browser.async_playwright", return_value=pw_cm):
        result = await fetch("https://example.com/notfound")

    assert result["status"] == 404
