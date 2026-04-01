from __future__ import annotations

"""Tests for metabolon/enzymes/navigator.py.

Covers: extract (success + failures), screenshot (temp path + custom path +
navigation failure), check_auth (authenticated + unauthenticated + no domain),
unknown action, _run_ab error paths, and atexit cleanup.
"""


import os
import time
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.navigator import (
    NavigatorResult,
    _pending_screenshots,
    navigator,
)


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_pending():
    """Clear global pending-screenshots list between tests."""
    _pending_screenshots.clear()
    yield
    _pending_screenshots.clear()


def _subprocess_ok(stdout: str = ""):
    """Return a mock subprocess.CompletedProcess representing success."""
    return MagicMock(stdout=stdout, stderr="", returncode=0)


def _subprocess_fail(stderr: str = "fail"):
    """Return a mock raising CalledProcessError."""
    import subprocess

    return subprocess.CalledProcessError(1, "agent-browser", stderr=stderr, stdout="")


# ── extract action ───────────────────────────────────────────────────────


class TestExtract:
    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    def test_extract_success(self, mock_run, mock_sleep):
        mock_run.side_effect = [
            (True, "ok"),          # open
            (True, "My Page"),     # get title
            (True, "page text"),   # get text
            (True, "https://x.co"),  # get url
        ]
        res = navigator(action="extract", url="https://example.com", wait_ms=100)
        assert res.success is True
        assert res.data["title"] == "My Page"
        assert res.data["text"] == "page text"
        assert res.data["url"] == "https://x.co"
        assert res.error is None
        mock_sleep.assert_called_once_with(0.1)

    @patch("metabolon.enzymes.navigator._run_ab")
    def test_extract_missing_url(self, mock_run):
        res = navigator(action="extract", url="")
        assert res.success is False
        assert "url" in res.error
        mock_run.assert_not_called()

    @patch("metabolon.enzymes.navigator._run_ab")
    def test_extract_nav_failure(self, mock_run):
        mock_run.return_value = (False, "connection refused")
        res = navigator(action="extract", url="https://bad.site")
        assert res.success is False
        assert "Navigation failed" in res.error
        assert "connection refused" in res.error

    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    def test_extract_partial_get_failure(self, mock_run, mock_sleep):
        """If some `get` calls fail, graceful degradation with defaults."""
        mock_run.side_effect = [
            (True, "ok"),        # open
            (False, "err"),      # get title
            (False, "err"),      # get text
            (False, "err"),      # get url
        ]
        res = navigator(action="extract", url="https://x.co", wait_ms=0)
        assert res.success is True
        assert res.data["title"] == ""
        assert res.data["text"] == ""
        assert res.data["url"] == "https://x.co"
        mock_sleep.assert_not_called()

    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    def test_extract_zero_wait(self, mock_run, mock_sleep):
        mock_run.side_effect = [
            (True, "ok"),
            (True, "t"), (True, "txt"), (True, "u"),
        ]
        navigator(action="extract", url="https://x.co", wait_ms=0)
        mock_sleep.assert_not_called()


# ── screenshot action ────────────────────────────────────────────────────


class TestScreenshot:
    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    @patch("metabolon.enzymes.navigator.subprocess.run")
    def test_screenshot_default_path(self, mock_sp, mock_run, mock_sleep):
        mock_run.side_effect = [
            (True, "ok"),  # open
            (True, "ok"),  # screenshot
        ]
        mock_sp.return_value = _subprocess_ok()
        res = navigator(action="screenshot", url="https://x.co", wait_ms=0)
        assert res.success is True
        assert "output_path" in res.data
        assert res.data["output_path"].endswith(".png")
        # Temp screenshot registered for cleanup
        assert res.data["output_path"] in _pending_screenshots

    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    @patch("metabolon.enzymes.navigator.subprocess.run")
    def test_screenshot_custom_path(self, mock_sp, mock_run, mock_sleep):
        mock_run.side_effect = [
            (True, "ok"),
            (True, "ok"),
        ]
        mock_sp.return_value = _subprocess_ok()
        res = navigator(
            action="screenshot",
            url="https://x.co",
            output_path="/tmp/custom.png",
            wait_ms=0,
        )
        assert res.success is True
        assert res.data["output_path"] == "/tmp/custom.png"
        # Custom path should NOT be added to pending screenshots
        assert "/tmp/custom.png" not in _pending_screenshots

    @patch("metabolon.enzymes.navigator._run_ab")
    def test_screenshot_missing_url(self, mock_run):
        res = navigator(action="screenshot", url="")
        assert res.success is False
        assert "url" in res.error

    @patch("metabolon.enzymes.navigator._run_ab")
    @patch("metabolon.enzymes.navigator.subprocess.run")
    def test_screenshot_nav_failure(self, mock_sp, mock_run):
        mock_run.return_value = (False, "timeout")
        mock_sp.return_value = _subprocess_ok()
        res = navigator(action="screenshot", url="https://bad.site")
        assert res.success is False
        assert "Navigation failed" in res.error

    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    @patch("metabolon.enzymes.navigator.subprocess.run")
    def test_screenshot_capture_failure(self, mock_sp, mock_run, mock_sleep):
        mock_run.side_effect = [
            (True, "ok"),           # open succeeds
            (False, "disk full"),   # screenshot fails
        ]
        mock_sp.return_value = _subprocess_ok()
        res = navigator(action="screenshot", url="https://x.co", wait_ms=0)
        assert res.success is False
        assert "Screenshot failed" in res.error

    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    @patch("metabolon.enzymes.navigator.subprocess.run")
    def test_screenshot_caffeinate_called(self, mock_sp, mock_run, mock_sleep):
        """Verify caffeinate is invoked to wake display."""
        mock_run.side_effect = [(True, "ok"), (True, "ok")]
        mock_sp.return_value = _subprocess_ok()
        navigator(action="screenshot", url="https://x.co", wait_ms=0)
        mock_sp.assert_called_once_with(
            ["caffeinate", "-u", "-t", "2"], capture_output=True, timeout=300
        )


# ── check_auth action ────────────────────────────────────────────────────


class TestCheckAuth:
    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    def test_check_auth_authenticated(self, mock_run, mock_sleep):
        mock_run.side_effect = [
            (True, "ok"),                      # open
            (True, "https://app.example.com/dashboard"),  # get url
        ]
        res = navigator(action="check_auth", domain="example.com")
        assert res.success is True
        assert res.data["is_authenticated"] is True
        assert res.data["domain"] == "example.com"
        assert "guidance" not in res.data

    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    def test_check_auth_redirected_to_login(self, mock_run, mock_sleep):
        mock_run.side_effect = [
            (True, "ok"),
            (True, "https://example.com/login?next=/dashboard"),
        ]
        res = navigator(action="check_auth", domain="example.com")
        assert res.success is True
        assert res.data["is_authenticated"] is False
        assert "guidance" in res.data
        assert "porta inject" in res.data["guidance"]

    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    def test_check_auth_signin_redirect(self, mock_run, mock_sleep):
        mock_run.side_effect = [
            (True, "ok"),
            (True, "https://accounts.x.com/SignIn"),
        ]
        res = navigator(action="check_auth", domain="x.com")
        assert res.data["is_authenticated"] is False

    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    def test_check_auth_auth_keyword(self, mock_run, mock_sleep):
        mock_run.side_effect = [
            (True, "ok"),
            (True, "https://id.example.com/auth?redirect=/"),
        ]
        res = navigator(action="check_auth", domain="example.com")
        assert res.data["is_authenticated"] is False

    @patch("metabolon.enzymes.navigator._run_ab")
    def test_check_auth_missing_domain(self, mock_run):
        res = navigator(action="check_auth", domain="")
        assert res.success is False
        assert "domain" in res.error
        mock_run.assert_not_called()

    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    def test_check_auth_nav_failure(self, mock_run, mock_sleep):
        mock_run.return_value = (False, "refused")
        res = navigator(action="check_auth", domain="bad.site")
        assert res.success is False
        assert "Navigation failed" in res.error

    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    def test_check_auth_prepends_https(self, mock_run, mock_sleep):
        """Bare domain should get https:// prepended."""
        mock_run.side_effect = [
            (True, "ok"),
            (True, "https://my.site/home"),
        ]
        navigator(action="check_auth", domain="my.site")
        call_args = mock_run.call_args_list[0][0][0]
        assert call_args[0] == "open"
        assert call_args[1] == "https://my.site"

    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    def test_check_auth_keeps_full_url(self, mock_run, mock_sleep):
        """Already-absolute URL should be used as-is."""
        mock_run.side_effect = [
            (True, "ok"),
            (True, "http://my.site/home"),
        ]
        navigator(action="check_auth", domain="http://my.site")
        call_args = mock_run.call_args_list[0][0][0]
        assert call_args[1] == "http://my.site"

    @patch("metabolon.enzymes.navigator.time.sleep")
    @patch("metabolon.enzymes.navigator._run_ab")
    def test_check_auth_get_url_fails(self, mock_run, mock_sleep):
        """If get-url fails, current_url defaults to empty and user is 'authenticated'."""
        mock_run.side_effect = [
            (True, "ok"),     # open
            (False, "error"), # get url
        ]
        res = navigator(action="check_auth", domain="example.com")
        assert res.success is True
        assert res.data["current_url"] == ""
        assert res.data["is_authenticated"] is True


# ── unknown action ───────────────────────────────────────────────────────


class TestUnknownAction:
    def test_unknown_action(self):
        res = navigator(action="fly")
        assert res.success is False
        assert "Unknown action" in res.error
        assert "fly" in res.error

    def test_action_case_insensitive(self):
        """Action is lowercased and stripped."""
        res = navigator(action="  EXTRACT ", url="")
        # Should get "extract requires: url", not "Unknown action"
        assert "url" in res.error
        assert "Unknown" not in res.error


# ── _run_ab unit tests ───────────────────────────────────────────────────


class TestRunAb:
    @patch("metabolon.enzymes.navigator.subprocess.run")
    @patch("metabolon.enzymes.navigator.os.popen")
    def test_run_ab_success(self, mock_popen, mock_sp):
        mock_popen.return_value = MagicMock(read=MagicMock(return_value="/usr/local/bin/agent-browser\n"))
        mock_sp.return_value = _subprocess_ok("result text")
        from metabolon.enzymes.navigator import _run_ab
        ok, out = _run_ab(["open", "https://x.co"])
        assert ok is True
        assert out == "result text"

    @patch("metabolon.enzymes.navigator.subprocess.run")
    @patch("metabolon.enzymes.navigator.os.popen")
    def test_run_ab_failure_returns_stderr(self, mock_popen, mock_sp):
        import subprocess
        mock_popen.return_value = MagicMock(read=MagicMock(return_value="agent-browser\n"))
        mock_sp.side_effect = subprocess.CalledProcessError(
            1, "agent-browser", stderr="bad",
        )
        from metabolon.enzymes.navigator import _run_ab
        ok, out = _run_ab(["fail"])
        assert ok is False
        assert out == "bad"

    @patch("metabolon.enzymes.navigator.subprocess.run")
    @patch("metabolon.enzymes.navigator.os.popen")
    def test_run_ab_failure_falls_back_to_stdout(self, mock_popen, mock_sp):
        import subprocess
        mock_popen.return_value = MagicMock(read=MagicMock(return_value="agent-browser\n"))
        mock_sp.side_effect = subprocess.CalledProcessError(
            1, "agent-browser", output="std output", stderr="",
        )
        from metabolon.enzymes.navigator import _run_ab
        ok, out = _run_ab(["fail"])
        assert ok is False
        assert out == "std output"

    @patch("metabolon.enzymes.navigator.subprocess.run")
    @patch("metabolon.enzymes.navigator.os.popen")
    def test_run_ab_empty_which_uses_default(self, mock_popen, mock_sp):
        mock_popen.return_value = MagicMock(read=MagicMock(return_value="\n"))
        mock_sp.return_value = _subprocess_ok("ok")
        from metabolon.enzymes.navigator import _run_ab
        _run_ab(["version"])
        called_path = mock_sp.call_args[0][0][0]
        assert called_path == "agent-browser"


# ── atexit cleanup ───────────────────────────────────────────────────────


class TestCleanup:
    def test_cleanup_unlinks_pending(self, tmp_path):
        from metabolon.enzymes.navigator import _cleanup_temp_screenshots
        f = tmp_path / "screenshot_test.png"
        f.write_text("img")
        _pending_screenshots.append(str(f))
        _cleanup_temp_screenshots()
        assert not f.exists()

    def test_cleanup_missing_ok(self):
        """No error if file already gone."""
        from metabolon.enzymes.navigator import _cleanup_temp_screenshots
        _pending_screenshots.append("/nonexistent/path/file.png")
        _cleanup_temp_screenshots()  # should not raise
