"""Tests for browserforge fingerprint integration in stealth-browser.

Covers:
  - generate_fingerprint returns a valid fingerprint dict
  - _fingerprint_injection_js produces executable JS
  - apply_fingerprint calls context methods correctly
  - CLI parser accepts --fingerprint-mode with all three choices
  - CLI _async_fetch composes generated+cookies modes correctly
  - Headless mode with generated fingerprint (integration with bot.sannysoft.com)

Network tests (marked @pytest.mark.network) are excluded from default runs.
Run explicitly: pytest -m network assays/test_stealth_browser_fingerprint.py -v
"""

from __future__ import annotations

import json
import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from playwright.async_api import async_playwright

from metabolon.organelles.browser_stealth import (
    _fingerprint_injection_js,
    apply_fingerprint,
    generate_fingerprint,
    stealth_context,
)
from metabolon.organelles.browser_stealth_cli import (
    _async_fetch,
    build_parser,
    format_output,
    main,
)

# ── generate_fingerprint ─────────────────────────────────────────────────


class TestGenerateFingerprint:
    def test_returns_dict_with_expected_keys(self) -> None:
        fp = generate_fingerprint()
        assert isinstance(fp, dict)
        assert "navigator" in fp
        assert "screen" in fp
        assert "headers" in fp

    def test_navigator_has_user_agent(self) -> None:
        fp = generate_fingerprint()
        assert "userAgent" in fp["navigator"]

    def test_js_key_present(self) -> None:
        fp = generate_fingerprint()
        assert "js" in fp
        assert isinstance(fp["js"], str)
        assert len(fp["js"]) > 100

    def test_fingerprints_differ_across_calls(self) -> None:
        seen: set[str] = set()
        for _ in range(10):
            fp = generate_fingerprint()
            seen.add(fp["navigator"]["userAgent"])
        assert len(seen) > 1


# ── _fingerprint_injection_js ────────────────────────────────────────────


class TestFingerprintInjectionJS:
    def test_produces_non_empty_string(self) -> None:
        fp = generate_fingerprint()
        js = _fingerprint_injection_js(fp)
        assert isinstance(js, str)
        assert len(js.strip()) > 0

    def test_contains_navigator_overrides(self) -> None:
        fp = generate_fingerprint()
        js = _fingerprint_injection_js(fp)
        assert "navigator" in js
        assert "userAgent" in js

    def test_contains_webgl_override_when_video_card(self) -> None:
        fp = generate_fingerprint()
        js = _fingerprint_injection_js(fp)
        assert "WEBGL_debug_renderer_info" in js

    def test_valid_js_structure(self) -> None:
        fp = generate_fingerprint()
        js = _fingerprint_injection_js(fp)
        assert js.strip().startswith("(function()")
        assert js.strip().endswith("})();")

    def test_empty_fingerprint_no_crash(self) -> None:
        js = _fingerprint_injection_js({})
        assert isinstance(js, str)
        assert len(js.strip()) > 0


# ── apply_fingerprint ────────────────────────────────────────────────────


class TestApplyFingerprint:
    @pytest.mark.asyncio
    async def test_sets_extra_headers(self) -> None:
        ctx = MagicMock()
        ctx.set_extra_http_headers = AsyncMock()
        ctx.add_init_script = AsyncMock()

        fp = generate_fingerprint()
        result = await apply_fingerprint(ctx, fp)

        assert result is ctx
        ctx.set_extra_http_headers.assert_called_once()
        ctx.add_init_script.assert_called_once()

    @pytest.mark.asyncio
    async def test_filters_sec_fetch_headers(self) -> None:
        ctx = MagicMock()
        ctx.set_extra_http_headers = AsyncMock()
        ctx.add_init_script = AsyncMock()

        fp = generate_fingerprint()
        await apply_fingerprint(ctx, fp)

        call_args = ctx.set_extra_http_headers.call_args[0][0]
        for key in call_args:
            assert not key.lower().startswith("sec-fetch")

    @pytest.mark.asyncio
    async def test_init_script_contains_fingerprint_data(self) -> None:
        ctx = MagicMock()
        ctx.set_extra_http_headers = AsyncMock()
        ctx.add_init_script = AsyncMock()

        fp = generate_fingerprint()
        ua = fp["navigator"]["userAgent"]
        await apply_fingerprint(ctx, fp)

        js_arg = ctx.add_init_script.call_args[0][0]
        assert ua in js_arg


# ── CLI parser ───────────────────────────────────────────────────────────


class TestCLIParser:
    def test_default_fingerprint_mode_is_cookies(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["https://example.com"])
        assert args.fingerprint_mode == "cookies"

    def test_accepts_generated_mode(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--fingerprint-mode", "generated", "https://example.com"])
        assert args.fingerprint_mode == "generated"

    def test_accepts_both_mode(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--fingerprint-mode", "both", "https://example.com"])
        assert args.fingerprint_mode == "both"

    def test_headless_default_true(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["https://example.com"])
        assert args.headless == "true"

    def test_headless_false(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--headless", "false", "https://example.com"])
        assert args.headless == "false"

    def test_json_flag(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--json", "https://example.com"])
        assert args.json_output is True

    def test_cookies_path(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["--cookies", "/tmp/cookies.json", "https://example.com"])
        assert args.cookies == "/tmp/cookies.json"


# ── format_output ────────────────────────────────────────────────────────


class TestFormatOutput:
    def test_text_mode(self) -> None:
        result = {"text": "Hello world", "status": 200}
        assert format_output(result) == "Hello world"

    def test_json_mode(self) -> None:
        result = {"text": "Hello", "fingerprint_mode": "generated"}
        output = format_output(result, as_json=True)
        parsed = json.loads(output)
        assert parsed["fingerprint_mode"] == "generated"


# ── _async_fetch composition ─────────────────────────────────────────────


class TestAsyncFetchComposition:
    @pytest.mark.asyncio
    async def test_generated_mode_applies_fingerprint(self) -> None:
        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_response = MagicMock()

        mock_response.status = 200
        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_page.inner_text = AsyncMock(return_value="Page body")
        mock_page.title = AsyncMock(return_value="Test")
        mock_page.url = "https://example.com"
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_pw.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_pw.__aexit__ = AsyncMock(return_value=False)

        mock_context.set_extra_http_headers = AsyncMock()
        mock_context.add_init_script = AsyncMock()
        mock_context.add_cookies = AsyncMock()

        with patch(
            "metabolon.organelles.browser_stealth_cli.async_playwright",
            return_value=mock_pw,
            create=True,
        ):
            result = await _async_fetch(
                "https://example.com",
                fingerprint_mode="generated",
                headless=True,
            )

        assert result["fingerprint_mode"] == "generated"
        assert result["headless"] is True
        assert result["status"] == 200
        mock_context.add_init_script.assert_called()

    @pytest.mark.asyncio
    async def test_cookies_mode_applies_stealth_context(self) -> None:
        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_response = MagicMock()

        mock_response.status = 200
        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_page.inner_text = AsyncMock(return_value="Page body")
        mock_page.title = AsyncMock(return_value="Test")
        mock_page.url = "https://example.com"
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_pw.__aenter__ = AsyncMock(return_value=mock_pw)
        mock_pw.__aexit__ = AsyncMock(return_value=False)

        mock_context.set_extra_http_headers = AsyncMock()
        mock_context.add_init_script = AsyncMock()

        with (
            patch(
                "metabolon.organelles.browser_stealth_cli.async_playwright", return_value=mock_pw
            ),
            patch(
                "metabolon.organelles.browser_stealth_cli.stealth_context", new_callable=AsyncMock
            ) as mock_stealth,
        ):
            mock_stealth.return_value = mock_context
            result = await _async_fetch(
                "https://example.com",
                fingerprint_mode="cookies",
                headless=False,
            )

        assert result["fingerprint_mode"] == "cookies"
        mock_stealth.assert_called_once_with(mock_context)


# ── main CLI entry point ─────────────────────────────────────────────────


class TestMainCLI:
    def test_no_args_returns_1(self, capsys) -> None:
        code = main([])
        assert code == 1

    def test_fetch_error_returns_1(self, capsys) -> None:
        with patch(
            "metabolon.organelles.browser_stealth_cli._async_fetch",
            new_callable=AsyncMock,
            side_effect=RuntimeError("boom"),
        ):
            code = main(["https://example.com"])
        assert code == 1

    def test_fetch_success_returns_0(self, capsys) -> None:
        fake_result = {
            "text": "Hello",
            "title": "Test",
            "url": "https://example.com",
            "status": 200,
            "fingerprint_mode": "generated",
            "headless": True,
            "cookies_loaded": 0,
            "screenshot_saved": False,
            "pdf_saved": False,
        }
        with patch(
            "metabolon.organelles.browser_stealth_cli._async_fetch",
            new_callable=AsyncMock,
            return_value=fake_result,
        ):
            code = main(["--fingerprint-mode", "generated", "https://example.com"])
        assert code == 0


# ── Live integration tests against bot.sannysoft.com ─────────────────────
# These require internet access and a local Chromium install (playwright install).
# Run: pytest -m network assays/test_stealth_browser_fingerprint.py -v


SANNYSOFT_URL = "https://bot.sannysoft.com/"


def _parse_sannysoft_results(page_text: str) -> tuple[int, int]:
    """Parse bot.sannysoft.com summary table, return (passed, total) counts.

    The page renders a table where each row has a test name and a result cell.
    Result cells use CSS classes: 'passed' (green) or 'failed' (red).
    We count occurrences of each.
    """
    passed = len(re.findall(r'class="[^"]*passed[^"]*"', page_text))
    failed = len(re.findall(r'class="[^"]*failed[^"]*"', page_text))
    total = passed + failed
    return passed, total


async def _score_sannysoft_with_generated() -> tuple[int, int]:
    """Navigate bot.sannysoft.com with browserforge generated fingerprint, return score."""
    fp = generate_fingerprint()
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        scr = fp.get("screen", {})
        viewport = {
            "width": int(scr.get("width") or scr.get("innerWidth") or 1920),
            "height": int(scr.get("height") or scr.get("innerHeight") or 1080),
        }
        context = await browser.new_context(viewport=viewport)
        await apply_fingerprint(context, fp)
        page = await context.new_page()
        await page.goto(SANNYSOFT_URL, wait_until="networkidle", timeout=30000)
        # Give the page a moment for any late JS updates
        await page.wait_for_timeout(2000)
        html = await page.content()
        await browser.close()
    return _parse_sannysoft_results(html)


async def _score_sannysoft_with_cookies() -> tuple[int, int]:
    """Navigate bot.sannysoft.com with cookies-mode stealth context, return score."""
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()
        await stealth_context(context)
        page = await context.new_page()
        await page.goto(SANNYSOFT_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        html = await page.content()
        await browser.close()
    return _parse_sannysoft_results(html)


class TestSannysoftIntegration:
    @pytest.mark.network
    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_generated_fingerprint_sannysoft(self) -> None:
        """Verify browserforge generated fingerprint passes >=20/22 checks on bot.sannysoft.com.

        Up to 2 failures are tolerated — known Chromium-headless leaks (SwiftShader
        renderer, 16x16 broken image canvas) are inherent to headless mode and don't
        reflect on the fingerprint quality itself.
        """
        passed, total = await _score_sannysoft_with_generated()
        print(f"\n[generated mode] sannysoft score: {passed}/{total}")
        assert total >= 20, f"Expected at least 20 checks, found {total}"
        assert passed >= 20, (
            f"Generated fingerprint passed {passed}/{total} checks — expected >=20. "
            f"See reviewer notes in spec for filing a finding if this fails."
        )

    @pytest.mark.network
    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_cookies_fingerprint_sannysoft(self) -> None:
        """Regression baseline: cookies-mode (default) score on bot.sannysoft.com.

        Cookies mode applies init-script patches (webdriver, chrome runtime, plugins,
        permissions) and rotates the User-Agent but does not inject browserforge data.
        It is expected to score lower than generated mode. This test records the
        observed baseline so regressions are caught.
        """
        passed, total = await _score_sannysoft_with_cookies()
        print(f"\n[cookies mode] sannysoft score: {passed}/{total}")
        assert total >= 20, f"Expected at least 20 checks, found {total}"
        assert passed >= 10, (
            f"Cookies mode passed {passed}/{total} — expected >=10 baseline. "
            f"This is a regression check; cookies mode is not expected to match generated."
        )
