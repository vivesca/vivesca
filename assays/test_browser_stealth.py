"""Tests for metabolon.organelles.browser_stealth.

All Playwright objects are mocked — no browser launch required.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metabolon.organelles.browser_stealth import (
    CHROME_USER_AGENTS,
    _CHROME_RUNTIME_PATCH_JS,
    _PERMISSIONS_PATCH_JS,
    _PLUGINS_PATCH_JS,
    _WEBDRIVER_PATCH_JS,
    human_delay,
    patch_navigator,
    set_realistic_headers,
    stealth_context,
)


# ── Constants ────────────────────────────────────────────────────────────────


class TestConstants:
    def test_user_agent_list_has_20_entries(self):
        assert len(CHROME_USER_AGENTS) == 20

    def test_all_user_agents_are_chrome(self):
        for ua in CHROME_USER_AGENTS:
            assert "Chrome/" in ua
            assert "AppleWebKit" in ua

    def test_user_agents_cover_multiple_platforms(self):
        platforms = set()
        for ua in CHROME_USER_AGENTS:
            if "Windows NT" in ua:
                platforms.add("windows")
            elif "Macintosh" in ua:
                platforms.add("mac")
            elif "Linux" in ua:
                platforms.add("linux")
        assert platforms == {"windows", "mac", "linux"}

    def test_webdriver_patch_contains_define_property(self):
        assert "Object.defineProperty" in _WEBDRIVER_PATCH_JS
        assert "navigator" in _WEBDRIVER_PATCH_JS
        assert "webdriver" in _WEBDRIVER_PATCH_JS

    def test_chrome_runtime_patch_contains_window_chrome(self):
        assert "window.chrome" in _CHROME_RUNTIME_PATCH_JS

    def test_plugins_patch_contains_plugins(self):
        assert "navigator" in _PLUGINS_PATCH_JS
        assert "plugins" in _PLUGINS_PATCH_JS

    def test_permissions_patch_contains_permissions(self):
        assert "permissions" in _PERMISSIONS_PATCH_JS


# ── patch_navigator ─────────────────────────────────────────────────────────


class TestPatchNavigator:
    @pytest.mark.asyncio
    async def test_calls_add_init_script_four_times(self):
        page = AsyncMock()
        await patch_navigator(page)
        assert page.add_init_script.call_count == 4

    @pytest.mark.asyncio
    async def test_passes_webdriver_js(self):
        page = AsyncMock()
        await patch_navigator(page)
        calls = [c.args[0] for c in page.add_init_script.call_args_list]
        assert _WEBDRIVER_PATCH_JS in calls
        assert _CHROME_RUNTIME_PATCH_JS in calls
        assert _PLUGINS_PATCH_JS in calls
        assert _PERMISSIONS_PATCH_JS in calls


# ── set_realistic_headers ──────────────────────────────────────────────────


class TestSetRealisticHeaders:
    def test_returns_a_user_agent_string(self):
        context = MagicMock()
        ua = set_realistic_headers(context)
        assert isinstance(ua, str)
        assert "Chrome/" in ua

    def test_calls_set_extra_http_headers(self):
        context = MagicMock()
        ua = set_realistic_headers(context)
        context.set_extra_http_headers.assert_called_once()
        headers = context.set_extra_http_headers.call_args[0][0]
        assert "User-Agent" in headers
        assert headers["User-Agent"] == ua

    def test_selected_ua_from_known_list(self):
        context = MagicMock()
        ua = set_realistic_headers(context)
        assert ua in CHROME_USER_AGENTS

    @patch("metabolon.organelles.browser_stealth.random.choice")
    def test_uses_random_choice(self, mock_choice):
        mock_choice.return_value = CHROME_USER_AGENTS[0]
        context = MagicMock()
        result = set_realistic_headers(context)
        mock_choice.assert_called_once_with(CHROME_USER_AGENTS)
        assert result == CHROME_USER_AGENTS[0]


# ── human_delay ─────────────────────────────────────────────────────────────


class TestHumanDelay:
    @pytest.mark.asyncio
    async def test_returns_float(self):
        with patch("metabolon.organelles.browser_stealth.asyncio.sleep", new_callable=AsyncMock):
            result = await human_delay()
            assert isinstance(result, float)

    @pytest.mark.asyncio
    async def test_delay_within_default_range(self):
        with patch("metabolon.organelles.browser_stealth.asyncio.sleep", new_callable=AsyncMock):
            result = await human_delay()
            assert 0.5 <= result <= 2.0

    @pytest.mark.asyncio
    async def test_custom_range(self):
        with patch("metabolon.organelles.browser_stealth.asyncio.sleep", new_callable=AsyncMock):
            result = await human_delay(min_seconds=1.0, max_seconds=3.0)
            assert 1.0 <= result <= 3.0

    @pytest.mark.asyncio
    async def test_actually_sleeps(self):
        with patch("metabolon.organelles.browser_stealth.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await human_delay(0.5, 2.0)
            mock_sleep.assert_awaited_once()
            # The sleep argument should match the returned delay.
            assert mock_sleep.call_args[0][0] == result


# ── stealth_context ─────────────────────────────────────────────────────────


class TestStealthContext:
    @pytest.mark.asyncio
    async def test_returns_same_context(self):
        context = AsyncMock()
        result = await stealth_context(context)
        assert result is context

    @pytest.mark.asyncio
    async def test_sets_headers(self):
        context = AsyncMock()
        await stealth_context(context)
        context.set_extra_http_headers.assert_called_once()

    @pytest.mark.asyncio
    async def test_applies_init_scripts(self):
        context = AsyncMock()
        await stealth_context(context)
        # 4 init scripts: webdriver, chrome runtime, plugins, permissions
        assert context.add_init_script.call_count == 4

    @pytest.mark.asyncio
    async def test_init_scripts_include_webdriver_patch(self):
        context = AsyncMock()
        await stealth_context(context)
        scripts = [c.args[0] for c in context.add_init_script.call_args_list]
        assert _WEBDRIVER_PATCH_JS in scripts
        assert _CHROME_RUNTIME_PATCH_JS in scripts
        assert _PLUGINS_PATCH_JS in scripts
        assert _PERMISSIONS_PATCH_JS in scripts

    @pytest.mark.asyncio
    async def test_chaining_works(self):
        """Returned context should be usable directly."""
        ctx = AsyncMock()
        result = await stealth_context(ctx)
        assert result is ctx
        assert isinstance(result, AsyncMock)
