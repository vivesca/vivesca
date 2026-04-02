from __future__ import annotations

"""Tests for metabolon.organelles.browser_stealth.

Complementary to test_organelles_browser_stealth.py — focuses on
UA pool diversity, JS patch structural checks, and edge-case behaviour.
"""

import re
from unittest.mock import MagicMock, patch

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


# ── UA pool diversity ────────────────────────────────────────────────────


class TestUADiversity:
    def test_pool_covers_windows(self) -> None:
        assert any("Windows" in ua for ua in CHROME_USER_AGENTS)

    def test_pool_covers_mac(self) -> None:
        assert any("Macintosh" in ua for ua in CHROME_USER_AGENTS)

    def test_pool_covers_linux(self) -> None:
        assert any("Linux" in ua for ua in CHROME_USER_AGENTS)

    def test_all_uas_contain_applewebkit(self) -> None:
        for ua in CHROME_USER_AGENTS:
            assert "AppleWebKit" in ua, f"Missing AppleWebKit: {ua}"

    def test_chrome_versions_in_expected_range(self) -> None:
        """All UAs should reference Chrome 120-131."""
        for ua in CHROME_USER_AGENTS:
            m = re.search(r"Chrome/(\d+)", ua)
            assert m is not None, f"No Chrome version in: {ua}"
            version = int(m.group(1))
            assert 120 <= version <= 131, f"Version {version} out of range"


# ── JS patch structural checks ───────────────────────────────────────────


class TestJSPatchStructure:
    def test_webdriver_patch_uses_define_property(self) -> None:
        assert "Object.defineProperty" in _WEBDRIVER_PATCH_JS

    def test_chrome_runtime_defines_load_times(self) -> None:
        assert "loadTimes" in _CHROME_RUNTIME_PATCH_JS
        assert "csi" in _CHROME_RUNTIME_PATCH_JS

    def test_plugins_patch_overrides_both_plugins_and_mimetypes(self) -> None:
        assert "'plugins'" in _PLUGINS_PATCH_JS
        assert "'mimeTypes'" in _PLUGINS_PATCH_JS

    def test_permissions_patch_checks_notifications(self) -> None:
        assert "notifications" in _PERMISSIONS_PATCH_JS
        assert "Promise.resolve" in _PERMISSIONS_PATCH_JS

    def test_all_patches_are_non_empty_strings(self) -> None:
        for script in (
            _WEBDRIVER_PATCH_JS,
            _CHROME_RUNTIME_PATCH_JS,
            _PLUGINS_PATCH_JS,
            _PERMISSIONS_PATCH_JS,
        ):
            assert isinstance(script, str)
            assert len(script.strip()) > 0


# ── human_delay edge cases ───────────────────────────────────────────────


class TestHumanDelayEdgeCases:
    @pytest.mark.asyncio
    @patch("metabolon.organelles.browser_stealth.asyncio.sleep")
    async def test_zero_range_returns_fixed_value(self, mock_sleep: MagicMock) -> None:
        mock_sleep.return_value = None
        delay = await human_delay(1.0, 1.0)
        assert delay == 1.0

    @pytest.mark.asyncio
    @patch("metabolon.organelles.browser_stealth.asyncio.sleep")
    async def test_very_small_range(self, mock_sleep: MagicMock) -> None:
        mock_sleep.return_value = None
        delay = await human_delay(0.001, 0.002)
        assert 0.001 <= delay <= 0.002

    @pytest.mark.asyncio
    @patch("metabolon.organelles.browser_stealth.asyncio.sleep")
    async def test_returned_delay_matches_sleep_arg(self, mock_sleep: MagicMock) -> None:
        """The value returned by human_delay should be exactly what was passed to sleep."""
        mock_sleep.return_value = None
        delay = await human_delay(0.5, 2.0)
        slept_arg = mock_sleep.call_args[0][0]
        assert delay == slept_arg


# ── stealth_context integration ──────────────────────────────────────────


class TestStealthContextIntegration:
    @pytest.mark.asyncio
    async def test_init_scripts_applied_before_first_page(self) -> None:
        """stealth_context applies init scripts on the context itself, not a page."""
        ctx = MagicMock()

        async def noop(*a, **kw):
            pass

        ctx.add_init_script = MagicMock(side_effect=noop)
        ctx.set_extra_http_headers = MagicMock()

        result = await stealth_context(ctx)
        # add_init_script called exactly 4 times (4 patch scripts)
        assert ctx.add_init_script.call_count == 4
        assert result is ctx

    @pytest.mark.asyncio
    @patch("metabolon.organelles.browser_stealth.random.choice")
    async def test_ua_rotation_is_deterministic_with_mock(
        self, mock_choice: MagicMock
    ) -> None:
        mock_choice.return_value = CHROME_USER_AGENTS[0]
        ctx = MagicMock()

        async def noop(*a, **kw):
            pass

        ctx.add_init_script = MagicMock(side_effect=noop)
        ctx.set_extra_http_headers = MagicMock()

        await stealth_context(ctx)
        header_arg = ctx.set_extra_http_headers.call_args[0][0]
        assert header_arg["User-Agent"] == CHROME_USER_AGENTS[0]
