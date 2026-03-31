"""Tests for metabolon/organelles/browser_stealth.py.

All Playwright objects are mocked — no browser launch required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.browser_stealth import (
    CHROME_USER_AGENTS,
    _WEBDRIVER_PATCH_JS,
    human_delay,
    patch_navigator,
    set_realistic_headers,
    stealth_context,
)


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def mock_context() -> MagicMock:
    """Playwright BrowserContext mock."""
    ctx = MagicMock()
    ctx.add_init_script = MagicMock()
    ctx.set_extra_http_headers = MagicMock()
    return ctx


@pytest.fixture
def mock_browser(mock_context: MagicMock) -> MagicMock:
    """Playwright Browser mock that returns mock_context."""
    browser = MagicMock()
    browser.new_context = MagicMock(return_value=mock_context)
    return browser


# ── patch_navigator ──────────────────────────────────────────────────────


class TestPatchNavigator:
    @pytest.mark.asyncio
    async def test_adds_init_script_with_webdriver_patch(self, mock_context: MagicMock) -> None:
        await patch_navigator(mock_context)
        # Should be called 4 times: webdriver, chrome runtime, plugins, permissions
        assert mock_context.add_init_script.call_count == 4

    def test_script_sets_undefined(self) -> None:
        """The injected JS must override navigator.webdriver."""
        assert "navigator" in _WEBDRIVER_PATCH_JS
        assert "webdriver" in _WEBDRIVER_PATCH_JS
        assert "undefined" in _WEBDRIVER_PATCH_JS


# ── set_realistic_headers ────────────────────────────────────────────────


class TestSetRealisticHeaders:
    def test_returns_ua_from_pool(self, mock_context: MagicMock) -> None:
        ua = set_realistic_headers(mock_context)
        assert ua in CHROME_USER_AGENTS

    def test_calls_set_extra_http_headers(self, mock_context: MagicMock) -> None:
        set_realistic_headers(mock_context)
        mock_context.set_extra_http_headers.assert_called_once()

    def test_headers_include_user_agent(self, mock_context: MagicMock) -> None:
        set_realistic_headers(mock_context)
        call_args = mock_context.set_extra_http_headers.call_args[0][0]
        assert "User-Agent" in call_args

    def test_randomness_across_calls(self, mock_context: MagicMock) -> None:
        """With 20 UAs, 50 calls should produce > 1 unique UA."""
        uas = {set_realistic_headers(mock_context) for _ in range(50)}
        assert len(uas) > 1


# ── human_delay ──────────────────────────────────────────────────────────


class TestHumanDelay:
    @pytest.mark.asyncio
    @patch("metabolon.organelles.browser_stealth.asyncio.sleep")
    async def test_returns_float_in_range(self, mock_sleep: MagicMock) -> None:
        mock_sleep.return_value = None
        delay = await human_delay(0.5, 2.0)
        assert isinstance(delay, float)
        assert 0.5 <= delay <= 2.0

    @pytest.mark.asyncio
    @patch("metabolon.organelles.browser_stealth.asyncio.sleep")
    async def test_calls_sleep_with_delay(self, mock_sleep: MagicMock) -> None:
        mock_sleep.return_value = None
        await human_delay(1.0, 1.0)
        # With min==max, sleep argument should be 1.0 (within float epsilon)
        assert abs(mock_sleep.call_args[0][0] - 1.0) < 1e-6

    @pytest.mark.asyncio
    @patch("metabolon.organelles.browser_stealth.asyncio.sleep")
    async def test_custom_range(self, mock_sleep: MagicMock) -> None:
        mock_sleep.return_value = None
        delay = await human_delay(3.0, 5.0)
        assert 3.0 <= delay <= 5.0

    @pytest.mark.asyncio
    @patch("metabolon.organelles.browser_stealth.asyncio.sleep")
    async def test_default_range(self, mock_sleep: MagicMock) -> None:
        mock_sleep.return_value = None
        delay = await human_delay()
        assert 0.5 <= delay <= 2.0


# ── stealth_context ──────────────────────────────────────────────────────


class TestStealthContext:
    @pytest.mark.asyncio
    async def test_returns_same_context(self, mock_context: MagicMock) -> None:
        ctx = await stealth_context(mock_context)
        assert ctx is mock_context

    @pytest.mark.asyncio
    async def test_applies_all_patches(self, mock_context: MagicMock) -> None:
        await stealth_context(mock_context)
        # 4 init scripts for patches: webdriver, chrome runtime, plugins, permissions
        assert mock_context.add_init_script.call_count == 4
        # set_realistic_headers calls set_extra_http_headers once
        mock_context.set_extra_http_headers.assert_called_once()

    @pytest.mark.asyncio
    async def test_sets_random_ua(self, mock_context: MagicMock) -> None:
        await stealth_context(mock_context)
        call_args = mock_context.set_extra_http_headers.call_args[0][0]
        assert "User-Agent" in call_args
        assert call_args["User-Agent"] in CHROME_USER_AGENTS


# ── UA pool integrity ────────────────────────────────────────────────────


class TestUAPool:
    def test_pool_has_20_agents(self) -> None:
        assert len(CHROME_USER_AGENTS) == 20

    def test_all_are_chrome(self) -> None:
        for ua in CHROME_USER_AGENTS:
            assert "Chrome" in ua, f"Non-Chrome UA: {ua}"

    def test_all_unique(self) -> None:
        assert len(CHROME_USER_AGENTS) == len(set(CHROME_USER_AGENTS))
