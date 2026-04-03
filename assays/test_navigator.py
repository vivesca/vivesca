from __future__ import annotations

"""Tests for metabolon/enzymes/navigator.py — browser automation."""


from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fn():
    """Return the raw function behind the @tool decorator."""
    from metabolon.enzymes import navigator as mod

    return mod.navigator


def _result_class():
    from metabolon.enzymes.navigator import NavigatorResult

    return NavigatorResult


# ---------------------------------------------------------------------------
# _run_ab unit tests
# ---------------------------------------------------------------------------

class TestRunAb:
    """Tests for _run_ab helper."""

    def test_success_returns_true_and_stdout(self):
        from metabolon.enzymes.navigator import _run_ab

        mock_proc = MagicMock()
        mock_proc.stdout = "  page content  \n"
        with (
            patch("metabolon.enzymes.navigator.os.popen") as mock_popen,
            patch("metabolon.enzymes.navigator.subprocess.run", return_value=mock_proc),
        ):
            mock_popen.return_value.read.return_value = "/usr/local/bin/agent-browser\n"
            ok, out = _run_ab(["open", "https://example.com"])

        assert ok is True
        assert out == "page content"

    def test_failure_returns_false_and_stderr(self):
        from metabolon.enzymes.navigator import _run_ab

        with (
            patch("metabolon.enzymes.navigator.os.popen") as mock_popen,
            patch("metabolon.enzymes.navigator.subprocess.run") as mock_run,
        ):
            import subprocess

            mock_run.side_effect = subprocess.CalledProcessError(
                1, "agent-browser", stderr=" connection refused "
            )
            mock_popen.return_value.read.return_value = "agent-browser\n"
            ok, out = _run_ab(["open", "https://bad.url"])

        assert ok is False
        assert out == "connection refused"

    def test_failure_returns_stdout_if_no_stderr(self):
        from metabolon.enzymes.navigator import _run_ab

        with (
            patch("metabolon.enzymes.navigator.os.popen") as mock_popen,
            patch("metabolon.enzymes.navigator.subprocess.run") as mock_run,
        ):
            import subprocess

            err = subprocess.CalledProcessError(1, "agent-browser")
            err.stderr = ""
            err.stdout = " some stdout error "
            mock_run.side_effect = err
            mock_popen.return_value.read.return_value = "agent-browser\n"
            ok, out = _run_ab(["open", "https://bad.url"])

        assert ok is False
        assert out == "some stdout error"


# ---------------------------------------------------------------------------
# navigator — extract action
# ---------------------------------------------------------------------------

class TestExtract:
    """Tests for the extract action."""

    def test_missing_url_returns_error(self):
        result = _fn()(action="extract")
        assert result.success is False
        assert "url" in result.error

    def test_navigation_failure(self):
        with patch("metabolon.enzymes.navigator._run_ab", return_value=(False, "timeout")):
            result = _fn()(action="extract", url="https://fail.com")
        assert result.success is False
        assert "Navigation failed" in result.error

    def test_successful_extract(self):
        call_count = 0
        responses = {
            ("open", "https://example.com"): (True, "ok"),
            ("get", "title"): (True, "Example Page"),
            ("get", "text"): (True, "Hello world"),
            ("get", "url"): (True, "https://example.com/"),
        }

        def mock_run_ab(args):
            key = tuple(args)
            return responses.get(key, (True, ""))

        with (
            patch("metabolon.enzymes.navigator._run_ab", side_effect=mock_run_ab),
            patch("metabolon.enzymes.navigator.time.sleep"),
        ):
            result = _fn()(action="extract", url="https://example.com")

        assert result.success is True
        assert result.data["title"] == "Example Page"
        assert result.data["text"] == "Hello world"
        assert result.data["url"] == "https://example.com/"

    def test_extract_graceful_on_get_failure(self):
        """If get-title/text/url fail, still returns success with defaults."""

        def mock_run_ab(args):
            if args[0] == "open":
                return (True, "ok")
            return (False, "not available")

        with (
            patch("metabolon.enzymes.navigator._run_ab", side_effect=mock_run_ab),
            patch("metabolon.enzymes.navigator.time.sleep"),
        ):
            result = _fn()(action="extract", url="https://example.com")

        assert result.success is True
        assert result.data["title"] == ""
        assert result.data["text"] == ""
        assert result.data["url"] == "https://example.com"

    def test_zero_wait_skips_sleep(self):
        with (
            patch("metabolon.enzymes.navigator._run_ab", return_value=(True, "ok")),
            patch("metabolon.enzymes.navigator.time.sleep") as mock_sleep,
        ):
            _fn()(action="extract", url="https://x.com", wait_ms=0)

        # sleep should not be called (open succeeds, then get-title etc succeed)
        # Actually sleep IS called in extract only if wait_ms > 0
        # With wait_ms=0, no sleep calls for the wait
        assert all(
            call.args[0] != 0 for call in mock_sleep.call_args_list
        )


# ---------------------------------------------------------------------------
# navigator — screenshot action
# ---------------------------------------------------------------------------

class TestScreenshot:
    """Tests for the screenshot action."""

    def test_missing_url_returns_error(self):
        result = _fn()(action="screenshot")
        assert result.success is False
        assert "url" in result.error

    def test_navigation_failure(self):
        with (
            patch("metabolon.enzymes.navigator._run_ab", return_value=(False, "err")),
            patch("metabolon.enzymes.navigator.subprocess.run"),
        ):
            result = _fn()(action="screenshot", url="https://fail.com")
        assert result.success is False
        assert "Navigation failed" in result.error

    def test_screenshot_failure(self):
        def mock_run_ab(args):
            if args[0] == "open":
                return (True, "ok")
            return (False, "disk full")

        with (
            patch("metabolon.enzymes.navigator._run_ab", side_effect=mock_run_ab),
            patch("metabolon.enzymes.navigator.subprocess.run"),
            patch("metabolon.enzymes.navigator.time.sleep"),
        ):
            result = _fn()(action="screenshot", url="https://example.com", output_path="/tmp/x.png")

        assert result.success is False
        assert "Screenshot failed" in result.error

    def test_successful_screenshot_with_output_path(self):
        def mock_run_ab(args):
            if args[0] == "open":
                return (True, "ok")
            return (True, "saved")

        with (
            patch("metabolon.enzymes.navigator._run_ab", side_effect=mock_run_ab),
            patch("metabolon.enzymes.navigator.subprocess.run"),
            patch("metabolon.enzymes.navigator.time.sleep"),
        ):
            result = _fn()(
                action="screenshot",
                url="https://example.com",
                output_path="/tmp/test_screenshot.png",
            )

        assert result.success is True
        assert result.data["output_path"] == "/tmp/test_screenshot.png"
        assert result.data["url"] == "https://example.com"

    def test_auto_temp_path_when_no_output_path(self):
        def mock_run_ab(args):
            if args[0] == "open":
                return (True, "ok")
            return (True, "saved")

        with (
            patch("metabolon.enzymes.navigator._run_ab", side_effect=mock_run_ab),
            patch("metabolon.enzymes.navigator.subprocess.run"),
            patch("metabolon.enzymes.navigator.time.sleep"),
        ):
            result = _fn()(action="screenshot", url="https://example.com")

        assert result.success is True
        assert "screenshot_" in result.data["output_path"]
        assert result.data["output_path"].endswith(".png")

    @patch("metabolon.enzymes.navigator.sys")
    @patch("metabolon.enzymes.navigator._run_ab", return_value=(True, "ok"))
    @patch("metabolon.enzymes.navigator.subprocess.run")
    @patch("metabolon.enzymes.navigator.time.sleep")
    def test_caffeinate_called(self, mock_sleep, mock_run, mock_ab, mock_sys):
        mock_sys.platform = "darwin"
        _fn()(action="screenshot", url="https://example.com", output_path="/tmp/x.png")

        # First call should be caffeinate
        caffeinate_call = mock_run.call_args_list[0]
        assert caffeinate_call[0][0][0] == "caffeinate"


# ---------------------------------------------------------------------------
# navigator — check_auth action
# ---------------------------------------------------------------------------

class TestCheckAuth:
    """Tests for the check_auth action."""

    def test_missing_domain_returns_error(self):
        result = _fn()(action="check_auth")
        assert result.success is False
        assert "domain" in result.error

    def test_navigation_failure(self):
        with patch("metabolon.enzymes.navigator._run_ab", return_value=(False, "err")):
            result = _fn()(action="check_auth", domain="fail.com")
        assert result.success is False
        assert "Navigation failed" in result.error

    def test_authenticated_no_login_redirect(self):
        def mock_run_ab(args):
            if args[0] == "open":
                return (True, "ok")
            if args[0] == "get":
                return (True, "https://example.com/dashboard")
            return (True, "")

        with (
            patch("metabolon.enzymes.navigator._run_ab", side_effect=mock_run_ab),
            patch("metabolon.enzymes.navigator.time.sleep"),
        ):
            result = _fn()(action="check_auth", domain="example.com")

        assert result.success is True
        assert result.data["is_authenticated"] is True
        assert "guidance" not in result.data
        assert result.data["domain"] == "example.com"

    def test_not_authenticated_login_redirect(self):
        def mock_run_ab(args):
            if args[0] == "open":
                return (True, "ok")
            if args[0] == "get":
                return (True, "https://example.com/login?next=/dashboard")
            return (True, "")

        with (
            patch("metabolon.enzymes.navigator._run_ab", side_effect=mock_run_ab),
            patch("metabolon.enzymes.navigator.time.sleep"),
        ):
            result = _fn()(action="check_auth", domain="example.com")

        assert result.success is True
        assert result.data["is_authenticated"] is False
        assert "guidance" in result.data
        assert "porta inject" in result.data["guidance"]

    def test_not_authenticated_signin_redirect(self):
        def mock_run_ab(args):
            if args[0] == "open":
                return (True, "ok")
            if args[0] == "get":
                return (True, "https://example.com/SignIn")
            return (True, "")

        with (
            patch("metabolon.enzymes.navigator._run_ab", side_effect=mock_run_ab),
            patch("metabolon.enzymes.navigator.time.sleep"),
        ):
            result = _fn()(action="check_auth", domain="example.com")

        assert result.data["is_authenticated"] is False

    def test_not_authenticated_auth_in_url(self):
        def mock_run_ab(args):
            if args[0] == "open":
                return (True, "ok")
            if args[0] == "get":
                return (True, "https://example.com/authorize?step=2")
            return (True, "")

        with (
            patch("metabolon.enzymes.navigator._run_ab", side_effect=mock_run_ab),
            patch("metabolon.enzymes.navigator.time.sleep"),
        ):
            result = _fn()(action="check_auth", domain="example.com")

        assert result.data["is_authenticated"] is False

    def test_domain_without_scheme_gets_https(self):
        """domain without http prefix gets https:// prepended."""

        def mock_run_ab(args):
            assert args == ["open", "https://bare.com"]
            return (True, "ok")

        with (
            patch("metabolon.enzymes.navigator._run_ab", side_effect=mock_run_ab) as mock,
            patch("metabolon.enzymes.navigator.time.sleep"),
        ):
            # The mock only handles the first call; need full mock for subsequent calls
            call_idx = 0

            def side_effect(args):
                nonlocal call_idx
                call_idx += 1
                if call_idx == 1:
                    assert args == ["open", "https://bare.com"]
                return (True, "https://bare.com/dashboard")

            mock.side_effect = side_effect
            result = _fn()(action="check_auth", domain="bare.com")

        assert result.success is True

    def test_domain_with_scheme_unchanged(self):
        call_idx = 0

        def side_effect(args):
            nonlocal call_idx
            call_idx += 1
            if call_idx == 1:
                assert args == ["open", "http://already.http"]
            return (True, "http://already.http/page")

        with (
            patch("metabolon.enzymes.navigator._run_ab", side_effect=side_effect),
            patch("metabolon.enzymes.navigator.time.sleep"),
        ):
            _fn()(action="check_auth", domain="http://already.http")

    def test_get_url_failure_uses_empty(self):
        def mock_run_ab(args):
            if args[0] == "open":
                return (True, "ok")
            return (False, "unavailable")

        with (
            patch("metabolon.enzymes.navigator._run_ab", side_effect=mock_run_ab),
            patch("metabolon.enzymes.navigator.time.sleep"),
        ):
            result = _fn()(action="check_auth", domain="example.com")

        # Empty current_url means no login/signin/auth keywords → authenticated
        assert result.data["is_authenticated"] is True
        assert result.data["current_url"] == ""


# ---------------------------------------------------------------------------
# navigator — unknown action
# ---------------------------------------------------------------------------

class TestUnknownAction:
    """Tests for invalid actions."""

    def test_unknown_action_returns_error(self):
        result = _fn()(action="delete")
        assert result.success is False
        assert "Unknown action" in result.error
        assert "delete" in result.error

    def test_action_case_insensitive(self):
        """Action is lowercased and stripped."""
        with (
            patch("metabolon.enzymes.navigator._run_ab", return_value=(True, "ok")),
            patch("metabolon.enzymes.navigator.time.sleep"),
        ):
            result = _fn()(action="  EXTRACT  ", url="https://x.com")
        assert result.success is True


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

class TestResultType:
    """Tests for NavigatorResult."""

    def test_is_secretion_subclass(self):
        from metabolon.morphology import Secretion

        assert issubclass(_result_class(), Secretion)

    def test_default_error_is_none(self):
        r = _result_class()(success=True, data={"k": "v"})
        assert r.error is None


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

class TestCleanup:
    """Tests for temp screenshot cleanup."""

    def test_cleanup_unlinks_pending(self, tmp_path):
        from metabolon.enzymes.navigator import _cleanup_temp_screenshots, _pending_screenshots

        f = tmp_path / "disposable.png"
        f.write_text("fake")
        assert f.exists()

        _pending_screenshots.append(str(f))
        _cleanup_temp_screenshots()

        assert not f.exists()
        # Clean up list state
        if str(f) in _pending_screenshots:
            _pending_screenshots.remove(str(f))


# ---------------------------------------------------------------------------
# navigator — navigate action (primary name for extract)
# ---------------------------------------------------------------------------

class TestNavigate:
    """Tests for the navigate action (extract is an alias)."""

    def test_navigate_is_primary_name(self):
        """navigate action works identically to extract."""
        def mock_run_ab(args):
            if args[0] == "open":
                return (True, "ok")
            if args == ["get", "title"]:
                return (True, "Nav Page")
            if args == ["get", "text"]:
                return (True, "nav content")
            if args == ["get", "url"]:
                return (True, "https://nav.co")
            return (True, "")

        with (
            patch("metabolon.enzymes.navigator._run_ab", side_effect=mock_run_ab),
            patch("metabolon.enzymes.navigator.time.sleep"),
        ):
            result = _fn()(action="navigate", url="https://nav.co")

        assert result.success is True
        assert result.data["title"] == "Nav Page"
        assert result.data["text"] == "nav content"

    def test_navigate_missing_url(self):
        result = _fn()(action="navigate")
        assert result.success is False
        assert "url" in result.error

    def test_extract_still_works_as_alias(self):
        """extract action is an alias for navigate — backward compat."""
        def mock_run_ab(args):
            if args[0] == "open":
                return (True, "ok")
            if args == ["get", "title"]:
                return (True, "Alias")
            if args == ["get", "text"]:
                return (True, "alias content")
            if args == ["get", "url"]:
                return (True, "https://alias.co")
            return (True, "")

        with (
            patch("metabolon.enzymes.navigator._run_ab", side_effect=mock_run_ab),
            patch("metabolon.enzymes.navigator.time.sleep"),
        ):
            result = _fn()(action="extract", url="https://alias.co")

        assert result.success is True
        assert result.data["title"] == "Alias"


# ---------------------------------------------------------------------------
# helper functions — _set_viewport, _set_device
# ---------------------------------------------------------------------------

class TestHelpers:
    """Tests for _set_viewport and _set_device helpers."""

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(True, "ok"))
    def test_set_viewport_basic(self, mock_run):
        from metabolon.enzymes.navigator import _set_viewport
        ok, out = _set_viewport(1920, 1080)
        assert ok is True
        assert out == "ok"
        mock_run.assert_called_once_with(["set", "viewport", "1920", "1080"])

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(True, "ok"))
    def test_set_viewport_with_scale(self, mock_run):
        from metabolon.enzymes.navigator import _set_viewport
        ok, out = _set_viewport(1280, 720, scale=2.0)
        assert ok is True
        mock_run.assert_called_once_with(
            ["set", "viewport", "1280", "720", "--scale", "2.0"]
        )

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(True, "ok"))
    def test_set_viewport_scale_zero_omits_flag(self, mock_run):
        from metabolon.enzymes.navigator import _set_viewport
        _set_viewport(800, 600, scale=0)
        call_args = mock_run.call_args[0][0]
        assert "--scale" not in call_args

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(True, "ok"))
    def test_set_device(self, mock_run):
        from metabolon.enzymes.navigator import _set_device
        ok, out = _set_device("iPhone 14")
        assert ok is True
        mock_run.assert_called_once_with(["set", "device", "iPhone 14"])

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(False, "no such device"))
    def test_set_device_failure(self, mock_run):
        from metabolon.enzymes.navigator import _set_device
        ok, out = _set_device("FakeDevice")
        assert ok is False
        assert "no such device" in out


# ---------------------------------------------------------------------------
# navigator — screenshot with viewport/device params
# ---------------------------------------------------------------------------

class TestScreenshotViewportDevice:
    """Tests for screenshot action with viewport and device parameters."""

    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    @patch("metabolon.enzymes.navigator.subprocess.run")
    def test_screenshot_with_viewport(self, mock_sp, mock_run, mock_sleep):
        mock_run.side_effect = [
            (True, "ok"),  # set viewport
            (True, "ok"),  # open
            (True, "ok"),  # screenshot
        ]
        mock_sp.return_value = MagicMock(stdout="", stderr="", returncode=0)
        result = _fn()(
            action="screenshot",
            url="https://x.co",
            width=1920,
            height=1080,
            output_path="/tmp/vp.png",
            wait_ms=0,
        )
        assert result.success is True
        assert result.data["output_path"] == "/tmp/vp.png"
        # First _run_ab call should be set viewport
        first_call = mock_run.call_args_list[0][0][0]
        assert first_call == ["set", "viewport", "1920", "1080"]

    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    @patch("metabolon.enzymes.navigator.subprocess.run")
    def test_screenshot_with_viewport_and_scale(self, mock_sp, mock_run, mock_sleep):
        mock_run.side_effect = [
            (True, "ok"),  # set viewport
            (True, "ok"),  # open
            (True, "ok"),  # screenshot
        ]
        mock_sp.return_value = MagicMock(stdout="", stderr="", returncode=0)
        result = _fn()(
            action="screenshot",
            url="https://x.co",
            width=1280,
            height=720,
            scale=2.0,
            output_path="/tmp/vp2.png",
            wait_ms=0,
        )
        assert result.success is True
        first_call = mock_run.call_args_list[0][0][0]
        assert first_call == ["set", "viewport", "1280", "720", "--scale", "2.0"]

    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    @patch("metabolon.enzymes.navigator.subprocess.run")
    def test_screenshot_with_device(self, mock_sp, mock_run, mock_sleep):
        mock_run.side_effect = [
            (True, "ok"),  # set device
            (True, "ok"),  # open
            (True, "ok"),  # screenshot
        ]
        mock_sp.return_value = MagicMock(stdout="", stderr="", returncode=0)
        result = _fn()(
            action="screenshot",
            url="https://x.co",
            device="iPhone 14",
            output_path="/tmp/dev.png",
            wait_ms=0,
        )
        assert result.success is True
        first_call = mock_run.call_args_list[0][0][0]
        assert first_call == ["set", "device", "iPhone 14"]

    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    @patch("metabolon.enzymes.navigator.subprocess.run")
    def test_screenshot_device_and_viewport(self, mock_sp, mock_run, mock_sleep):
        """Both device and viewport can be set — device first, then viewport."""
        mock_run.side_effect = [
            (True, "ok"),  # set device
            (True, "ok"),  # set viewport
            (True, "ok"),  # open
            (True, "ok"),  # screenshot
        ]
        mock_sp.return_value = MagicMock(stdout="", stderr="", returncode=0)
        result = _fn()(
            action="screenshot",
            url="https://x.co",
            device="Pixel 7",
            width=800,
            height=600,
            output_path="/tmp/both.png",
            wait_ms=0,
        )
        assert result.success is True
        calls = [c[0][0] for c in mock_run.call_args_list]
        assert calls[0] == ["set", "device", "Pixel 7"]
        assert calls[1] == ["set", "viewport", "800", "600"]

    @patch("metabolon.enzymes.navigator._run_ab")
    def test_screenshot_device_failure_aborts(self, mock_run):
        mock_run.return_value = (False, "unknown device")
        result = _fn()(
            action="screenshot",
            url="https://x.co",
            device="NoPhone",
            output_path="/tmp/x.png",
        )
        assert result.success is False
        assert "Set device failed" in result.error

    @patch("metabolon.enzymes.navigator._run_ab")
    def test_screenshot_viewport_failure_aborts(self, mock_run):
        mock_run.side_effect = [
            (False, "viewport error"),  # set viewport
        ]
        result = _fn()(
            action="screenshot",
            url="https://x.co",
            width=99999,
            height=99999,
            output_path="/tmp/x.png",
        )
        assert result.success is False
        assert "Set viewport failed" in result.error

    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    @patch("metabolon.enzymes.navigator.subprocess.run")
    def test_screenshot_no_viewport_when_zero(self, mock_sp, mock_run, mock_sleep):
        """width=0, height=0 should NOT call set viewport."""
        mock_run.side_effect = [
            (True, "ok"),  # open
            (True, "ok"),  # screenshot
        ]
        mock_sp.return_value = MagicMock(stdout="", stderr="", returncode=0)
        result = _fn()(
            action="screenshot",
            url="https://x.co",
            width=0,
            height=0,
            output_path="/tmp/novp.png",
            wait_ms=0,
        )
        assert result.success is True
        # Only 2 calls: open + screenshot (no set viewport)
        assert mock_run.call_count == 2


# ---------------------------------------------------------------------------
# navigator — click action
# ---------------------------------------------------------------------------

class TestClick:
    """Tests for the click action."""

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(True, "clicked"))
    def test_click_success(self, mock_run):
        result = _fn()(action="click", css_selector="#submit-btn")
        assert result.success is True
        assert result.data["css_selector"] == "#submit-btn"
        assert result.data["result"] == "clicked"
        mock_run.assert_called_once_with(["click", "#submit-btn"])

    def test_click_missing_selector(self):
        result = _fn()(action="click")
        assert result.success is False
        assert "css_selector" in result.error

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(False, "element not found"))
    def test_click_failure(self, mock_run):
        result = _fn()(action="click", css_selector=".missing")
        assert result.success is False
        assert "Click failed" in result.error
        assert "element not found" in result.error

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(True, "ok"))
    def test_click_complex_selector(self, mock_run):
        result = _fn()(action="click", css_selector="div.card > button.primary")
        assert result.success is True
        mock_run.assert_called_once_with(["click", "div.card > button.primary"])


# ---------------------------------------------------------------------------
# navigator — fill action
# ---------------------------------------------------------------------------

class TestFill:
    """Tests for the fill action."""

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(True, "filled"))
    def test_fill_success(self, mock_run):
        result = _fn()(action="fill", css_selector="#email", value="user@example.com")
        assert result.success is True
        assert result.data["css_selector"] == "#email"
        assert result.data["value"] == "user@example.com"
        assert result.data["result"] == "filled"
        mock_run.assert_called_once_with(["fill", "#email", "user@example.com"])

    def test_fill_missing_selector(self):
        result = _fn()(action="fill", value="hello")
        assert result.success is False
        assert "css_selector" in result.error

    def test_fill_missing_value(self):
        result = _fn()(action="fill", css_selector="#input")
        assert result.success is False
        assert "value" in result.error

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(False, "not interactable"))
    def test_fill_failure(self, mock_run):
        result = _fn()(action="fill", css_selector="#locked", value="test")
        assert result.success is False
        assert "Fill failed" in result.error
        assert "not interactable" in result.error

    def test_fill_empty_string_value_rejected(self):
        """Empty string value is treated as missing."""
        result = _fn()(action="fill", css_selector="#input", value="")
        assert result.success is False
        assert "value" in result.error


# ---------------------------------------------------------------------------
# navigator — eval action
# ---------------------------------------------------------------------------

class TestEval:
    """Tests for the eval action."""

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(True, "42"))
    def test_eval_success(self, mock_run):
        result = _fn()(action="eval", js="document.title")
        assert result.success is True
        assert result.data["js"] == "document.title"
        assert result.data["result"] == "42"
        mock_run.assert_called_once_with(["eval", "document.title"])

    def test_eval_missing_js(self):
        result = _fn()(action="eval")
        assert result.success is False
        assert "js" in result.error

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(False, "SyntaxError"))
    def test_eval_failure(self, mock_run):
        result = _fn()(action="eval", js="invalid{{")
        assert result.success is False
        assert "Eval failed" in result.error
        assert "SyntaxError" in result.error

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(True, '{"key":"value"}'))
    def test_eval_returns_complex_output(self, mock_run):
        result = _fn()(action="eval", js="JSON.stringify({key:'value'})")
        assert result.success is True
        assert result.data["result"] == '{"key":"value"}'


# ---------------------------------------------------------------------------
# navigator — resize action
# ---------------------------------------------------------------------------

class TestResize:
    """Tests for the resize action."""

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(True, "ok"))
    def test_resize_success(self, mock_run):
        result = _fn()(action="resize", width=1920, height=1080)
        assert result.success is True
        assert result.data["width"] == 1920
        assert result.data["height"] == 1080
        assert "scale" not in result.data
        mock_run.assert_called_once_with(["set", "viewport", "1920", "1080"])

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(True, "ok"))
    def test_resize_with_scale(self, mock_run):
        result = _fn()(action="resize", width=1280, height=720, scale=2.0)
        assert result.success is True
        assert result.data["scale"] == 2.0
        mock_run.assert_called_once_with(
            ["set", "viewport", "1280", "720", "--scale", "2.0"]
        )

    def test_resize_missing_width(self):
        result = _fn()(action="resize", height=1080)
        assert result.success is False
        assert "width" in result.error

    def test_resize_missing_height(self):
        result = _fn()(action="resize", width=1920)
        assert result.success is False
        assert "height" in result.error

    def test_resize_zero_dimensions(self):
        result = _fn()(action="resize", width=0, height=0)
        assert result.success is False

    def test_resize_negative_dimensions(self):
        result = _fn()(action="resize", width=-100, height=200)
        assert result.success is False

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(False, "unsupported size"))
    def test_resize_failure(self, mock_run):
        result = _fn()(action="resize", width=50000, height=50000)
        assert result.success is False
        assert "Resize failed" in result.error

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(True, "ok"))
    def test_resize_scale_zero_not_in_data(self, mock_run):
        """scale=0 should be omitted from result data."""
        result = _fn()(action="resize", width=800, height=600, scale=0)
        assert result.success is True
        assert "scale" not in result.data


# ---------------------------------------------------------------------------
# navigator — snapshot action
# ---------------------------------------------------------------------------

class TestSnapshot:
    """Tests for the snapshot action."""

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(True, "<accessibility tree>"))
    def test_snapshot_success(self, mock_run):
        result = _fn()(action="snapshot")
        assert result.success is True
        assert result.data["snapshot"] == "<accessibility tree>"
        mock_run.assert_called_once_with(["snapshot"])

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(False, "no page"))
    def test_snapshot_failure(self, mock_run):
        result = _fn()(action="snapshot")
        assert result.success is False
        assert "Snapshot failed" in result.error
        assert "no page" in result.error

    @patch("metabolon.enzymes.navigator._run_ab", return_value=(True, ""))
    def test_snapshot_empty_page(self, mock_run):
        result = _fn()(action="snapshot")
        assert result.success is True
        assert result.data["snapshot"] == ""


# ---------------------------------------------------------------------------
# navigator — updated unknown action message
# ---------------------------------------------------------------------------

class TestUpdatedUnknownAction:
    """Tests that unknown action error includes all valid actions."""

    def test_unknown_lists_all_actions(self):
        result = _fn()(action="foobar")
        assert result.success is False
        assert "Unknown action" in result.error
        assert "foobar" in result.error
        for act in ["navigate", "extract", "screenshot", "click", "fill", "eval", "resize", "snapshot", "check_auth"]:
            assert act in result.error
