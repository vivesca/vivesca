"""Tests for metabolon/organelles/browser_stealth.py.

All Playwright objects are mocked — no browser launch required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.browser_stealth import (
    CHROME_USER_AGENTS,
    _STEALTH_INIT_JS,
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
    def test_adds_init_script_with_webdriver_patch(self, mock_context: MagicMock) -> None:
        patch_navigator(mock_context)
        mock_context.add_init_script.assert_called_once_with(_WEBDRIVER_PATCH_JS)

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

    def test_headers_include_required_fields(self, mock_context: MagicMock) -> None:
        set_realistic_headers(mock_context)
        call_args = mock_context.set_extra_http_headers.call_args[0][0]
        required = [
            "Accept",
            "Accept-Encoding",
            "Accept-Language",
            "Sec-Ch-Ua",
            "Sec-Ch-Ua-Mobile",
            "Sec-Ch-Ua-Platform",
            "Sec-Fetch-Dest",
            "Sec-Fetch-Mode",
            "Sec-Fetch-Site",
            "Sec-Fetch-User",
            "Upgrade-Insecure-Requests",
        ]
        for key in required:
            assert key in call_args, f"Missing header: {key}"

    def test_randomness_across_calls(self, mock_context: MagicMock) -> None:
        """With 20 UAs, 50 calls should produce > 1 unique UA."""
        uas = {set_realistic_headers(mock_context) for _ in range(50)}
        assert len(uas) > 1


# ── human_delay ──────────────────────────────────────────────────────────


class TestHumanDelay:
    @patch("metabolon.organelles.browser_stealth.time.sleep")
    def test_returns_float_in_range(self, mock_sleep: MagicMock) -> None:
        mock_sleep.return_value = None
        delay = human_delay(0.5, 2.0)
        assert isinstance(delay, float)
        assert 0.5 <= delay <= 2.0

    @patch("metabolon.organelles.browser_stealth.time.sleep")
    def test_calls_sleep_with_delay(self, mock_sleep: MagicMock) -> None:
        mock_sleep.return_value = None
        human_delay(1.0, 1.0)
        # With min==max, sleep argument should be 1.0 (within float epsilon)
        assert abs(mock_sleep.call_args[0][0] - 1.0) < 1e-6

    @patch("metabolon.organelles.browser_stealth.time.sleep")
    def test_custom_range(self, mock_sleep: MagicMock) -> None:
        mock_sleep.return_value = None
        delay = human_delay(3.0, 5.0)
        assert 3.0 <= delay <= 5.0

    @patch("metabolon.organelles.browser_stealth.time.sleep")
    def test_default_range(self, mock_sleep: MagicMock) -> None:
        mock_sleep.return_value = None
        delay = human_delay()
        assert 0.5 <= delay <= 2.0


# ── stealth_context ──────────────────────────────────────────────────────


class TestStealthContext:
    def test_creates_context_from_browser(
        self, mock_browser: MagicMock, mock_context: MagicMock
    ) -> None:
        ctx = stealth_context(mock_browser)
        mock_browser.new_context.assert_called_once()
        assert ctx is mock_context

    def test_applies_all_patches(
        self, mock_browser: MagicMock, mock_context: MagicMock
    ) -> None:
        stealth_context(mock_browser)
        # patch_navigator calls add_init_script once
        # _STEALTH_INIT_JS calls add_init_script once more
        assert mock_context.add_init_script.call_count == 2
        # set_realistic_headers calls set_extra_http_headers once
        mock_context.set_extra_http_headers.assert_called_once()

    def test_random_ua_when_not_supplied(
        self, mock_browser: MagicMock, mock_context: MagicMock
    ) -> None:
        stealth_context(mock_browser)
        kwargs = mock_browser.new_context.call_args[1]
        assert kwargs["user_agent"] in CHROME_USER_AGENTS

    def test_custom_ua_preserved(
        self, mock_browser: MagicMock, mock_context: MagicMock
    ) -> None:
        custom_ua = "CustomBot/1.0"
        stealth_context(mock_browser, user_agent=custom_ua)
        kwargs = mock_browser.new_context.call_args[1]
        assert kwargs["user_agent"] == custom_ua

    def test_forwarded_kwargs(
        self, mock_browser: MagicMock, mock_context: MagicMock
    ) -> None:
        stealth_context(mock_browser, viewport={"width": 1920, "height": 1080}, locale="en-US")
        kwargs = mock_browser.new_context.call_args[1]
        assert kwargs["viewport"] == {"width": 1920, "height": 1080}
        assert kwargs["locale"] == "en-US"


# ── UA pool integrity ────────────────────────────────────────────────────


class TestUAPool:
    def test_pool_has_20_agents(self) -> None:
        assert len(CHROME_USER_AGENTS) == 20

    def test_all_are_chrome(self) -> None:
        for ua in CHROME_USER_AGENTS:
            assert "Chrome" in ua, f"Non-Chrome UA: {ua}"

    def test_all_unique(self) -> None:
        assert len(CHROME_USER_AGENTS) == len(set(CHROME_USER_AGENTS))

    def test_stealth_init_js_is_nonempty(self) -> None:
        assert len(_STEALTH_INIT_JS.strip()) > 0
        assert "navigator" in _STEALTH_INIT_JS
