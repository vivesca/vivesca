"""Tests for metabolon/enzymes/navigator.py — browser automation."""

from __future__ import annotations

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

    def test_caffeinate_called(self):
        with (
            patch("metabolon.enzymes.navigator._run_ab", return_value=(True, "ok")),
            patch("metabolon.enzymes.navigator.subprocess.run") as mock_run,
            patch("metabolon.enzymes.navigator.time.sleep"),
        ):
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
        result = _fn()(action="  EXTRACT  ", url="https://x.com")
        # Should not hit unknown action — will try extract flow
        # Will fail on navigation since _run_ab isn't mocked, but let's mock it
        with patch("metabolon.enzymes.navigator._run_ab", return_value=(True, "ok")):
            with patch("metabolon.enzymes.navigator.time.sleep"):
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
