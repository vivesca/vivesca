from __future__ import annotations

"""Tests for metabolon.organelles.porta — cookie bridge from Chrome to agent-browser."""

from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.porta import _ab, inject


# ── _ab helper tests ────────────────────────────────────────────────


class TestAb:
    """Tests for the _ab() subprocess wrapper."""

    @patch("metabolon.organelles.porta.subprocess.run")
    @patch("os.popen")
    def test_success_returns_true_plus_stdout(self, mock_popen, mock_run):
        mock_popen.return_value.read.return_value = "/usr/local/bin/agent-browser\n"
        mock_run.return_value = MagicMock(returncode=0, stdout="ok output\n")
        ok, out = _ab(["open", "https://example.com"])
        assert ok is True
        assert out == "ok output"
        mock_run.assert_called_once_with(
            ["/usr/local/bin/agent-browser", "open", "https://example.com"],
            capture_output=True,
            text=True,
            timeout=15,
        )

    @patch("metabolon.organelles.porta.subprocess.run")
    @patch("os.popen")
    def test_failure_returns_false_plus_stderr(self, mock_popen, mock_run):
        mock_popen.return_value.read.return_value = "agent-browser\n"
        mock_run.return_value = MagicMock(returncode=1, stderr="bad\n")
        ok, out = _ab(["eval", "bad"])
        assert ok is False
        assert out == "bad"

    @patch("metabolon.organelles.porta.subprocess.run")
    @patch("os.popen")
    def test_timeout_returns_false_timeout(self, mock_popen, mock_run):
        import subprocess

        mock_popen.return_value.read.return_value = "agent-browser\n"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="agent-browser", timeout=15)
        ok, out = _ab(["open", "url"], timeout=15)
        assert ok is False
        assert out == "timeout"

    @patch("metabolon.organelles.porta.subprocess.run")
    @patch("os.popen")
    def test_file_not_found(self, mock_popen, mock_run):
        mock_popen.return_value.read.return_value = "agent-browser\n"
        mock_run.side_effect = FileNotFoundError
        ok, out = _ab(["cookies", "list"])
        assert ok is False
        assert out == "agent-browser not found"

    @patch("metabolon.organelles.porta.subprocess.run")
    @patch("os.popen")
    def test_called_process_error(self, mock_popen, mock_run):
        import subprocess

        mock_popen.return_value.read.return_value = "agent-browser\n"
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "agent-browser", stderr="kaboom"
        )
        ok, out = _ab(["eval", "x"])
        assert ok is False
        assert out == "kaboom"

    @patch("metabolon.organelles.porta.subprocess.run")
    @patch("os.popen")
    def test_custom_timeout(self, mock_popen, mock_run):
        mock_popen.return_value.read.return_value = "agent-browser\n"
        mock_run.return_value = MagicMock(returncode=0, stdout="done")
        _ab(["cmd"], timeout=5)
        _, kwargs = mock_run.call_args
        assert kwargs["timeout"] == 5

    @patch("metabolon.organelles.porta.subprocess.run")
    @patch("os.popen")
    def test_falls_back_when_which_empty(self, mock_popen, mock_run):
        mock_popen.return_value.read.return_value = ""
        mock_run.return_value = MagicMock(returncode=0, stdout="ok")
        ok, out = _ab(["test"])
        assert ok is True
        mock_run.assert_called_once_with(
            ["agent-browser", "test"],
            capture_output=True,
            text=True,
            timeout=15,
        )


# ── inject() tests ──────────────────────────────────────────────────


class TestInject:
    """Tests for the inject() function."""

    def test_pycookiecheat_missing(self):
        with patch.dict("sys.modules", {"pycookiecheat": None}):
            # Force ImportError when chrome_cookies is accessed
            with patch(
                "metabolon.organelles.porta.chrome_cookies",
                side_effect=ImportError,
                create=True,
            ):
                # Simulate the import path inside inject
                with patch(
                    "metabolon.organelles.porta.inject.__globals__",
                    {"__builtins__": __builtins__},
                ):
                    result = inject("example.com")
        # The function handles ImportError internally
        assert result["success"] is False
        assert "pycookiecheat" in result["message"]
        assert result["count"] == 0

    @patch("metabolon.organelles.porta._ab")
    @patch("metabolon.organelles.porta.chrome_cookies")
    def test_pycookiecheat_import_error_branch(self, mock_cc, mock_ab):
        """When pycookiecheat import fails inside inject, returns failure."""
        mock_cc.side_effect = ImportError("no module")
        # We need to patch the import site inside inject
        with patch.dict("sys.modules", {"pycookiecheat": None}):
            result = inject("example.com")
        assert result["success"] is False
        assert result["count"] == 0

    @patch("metabolon.organelles.porta._ab")
    @patch("metabolon.organelles.porta.chrome_cookies")
    def test_cookie_extraction_exception(self, mock_cc, mock_ab):
        """When chrome_cookies raises, returns failure with message."""
        mock_cc.side_effect = RuntimeError("keychain locked")
        result = inject("bigmodel.cn")
        assert result["success"] is False
        assert "Chrome cookie extraction failed" in result["message"]
        assert "keychain locked" in result["message"]
        assert result["count"] == 0

    @patch("metabolon.organelles.porta._ab")
    @patch("metabolon.organelles.porta.chrome_cookies")
    def test_no_cookies_found(self, mock_cc, mock_ab):
        """When chrome_cookies returns empty dict, returns failure."""
        mock_cc.return_value = {}
        result = inject("example.com")
        assert result["success"] is False
        assert "No cookies found" in result["message"]
        assert result["count"] == 0

    @patch("metabolon.organelles.porta._ab")
    @patch("metabolon.organelles.porta.chrome_cookies")
    def test_strips_https_prefix(self, mock_cc, mock_ab):
        """Domain normalization strips https:// prefix."""
        mock_cc.return_value = {"sid": "abc123"}
        mock_ab.return_value = (True, "ok")
        result = inject("https://example.com")
        # chrome_cookies should be called with https://example.com
        mock_cc.assert_called_with("https://example.com")

    @patch("metabolon.organelles.porta._ab")
    @patch("metabolon.organelles.porta.chrome_cookies")
    def test_strips_http_prefix(self, mock_cc, mock_ab):
        """Domain normalization strips http:// prefix."""
        mock_cc.return_value = {"sid": "abc123"}
        mock_ab.return_value = (True, "ok")
        result = inject("http://example.com")
        mock_cc.assert_called_with("https://example.com")

    @patch("metabolon.organelles.porta._ab")
    @patch("metabolon.organelles.porta.chrome_cookies")
    def test_strips_trailing_slash(self, mock_cc, mock_ab):
        """Domain normalization strips trailing slash."""
        mock_cc.return_value = {"sid": "abc123"}
        mock_ab.return_value = (True, "ok")
        result = inject("example.com/")
        mock_cc.assert_called_with("https://example.com")

    @patch("metabolon.organelles.porta._ab")
    @patch("metabolon.organelles.porta.chrome_cookies")
    def test_navigation_open_succeeds(self, mock_cc, mock_ab):
        """When agent-browser open succeeds, cookies are injected."""
        mock_cc.return_value = {"sid": "val1", "token": "val2"}
        mock_ab.return_value = (True, "ok")
        result = inject("example.com")
        assert result["success"] is True
        assert result["count"] == 2
        # First call is open, then two cookie set calls
        assert mock_ab.call_count == 3

    @patch("metabolon.organelles.porta._ab")
    @patch("metabolon.organelles.porta.chrome_cookies")
    def test_navigation_open_fails_eval_succeeds(self, mock_cc, mock_ab):
        """When open fails, falls back to eval-based navigation."""
        mock_cc.return_value = {"sid": "val1"}
        # First call (open) fails, second (eval) succeeds, third (cookie set) succeeds
        mock_ab.side_effect = [
            (False, "open failed"),
            (True, "ok"),
            (True, "ok"),
        ]
        result = inject("example.com")
        assert result["success"] is True
        assert result["count"] == 1
        # Check that eval was called with window.location.href
        second_call = mock_ab.call_args_list[1]
        assert "window.location.href" in second_call[0][0][1]

    @patch("metabolon.organelles.porta._ab")
    @patch("metabolon.organelles.porta.chrome_cookies")
    def test_navigation_both_fail(self, mock_cc, mock_ab):
        """When both open and eval navigation fail, returns failure."""
        mock_cc.return_value = {"sid": "val1"}
        mock_ab.side_effect = [
            (False, "open failed"),
            (False, "eval failed"),
        ]
        result = inject("example.com")
        assert result["success"] is False
        assert "Failed to navigate" in result["message"]
        assert result["count"] == 0

    @patch("metabolon.organelles.porta._ab")
    @patch("metabolon.organelles.porta.chrome_cookies")
    def test_partial_injection_success(self, mock_cc, mock_ab):
        """Some cookies succeed, some fail — partial result."""
        mock_cc.return_value = {"a": "1", "b": "2", "c": "3"}
        mock_ab.side_effect = [
            (True, "ok"),       # open
            (True, "ok"),       # cookie a
            (False, "err"),     # cookie b fails
            (True, "ok"),       # cookie c
        ]
        result = inject("example.com")
        assert result["success"] is True
        assert result["count"] == 2
        assert "failed: b" in result["message"]

    @patch("metabolon.organelles.porta._ab")
    @patch("metabolon.organelles.porta.chrome_cookies")
    def test_all_cookies_fail_injection(self, mock_cc, mock_ab):
        """All cookie set calls fail — returns failure."""
        mock_cc.return_value = {"a": "1", "b": "2"}
        mock_ab.side_effect = [
            (True, "ok"),       # open succeeds
            (False, "err"),     # cookie a
            (False, "err"),     # cookie b
        ]
        result = inject("example.com")
        assert result["success"] is False
        assert "Cookie injection failed for all 2 cookies" in result["message"]
        assert result["count"] == 0

    @patch("metabolon.organelles.porta._ab")
    @patch("metabolon.organelles.porta.chrome_cookies")
    def test_many_failures_truncates_in_message(self, mock_cc, mock_ab):
        """More than 5 failed cookies get truncated in message."""
        cookies = {f"cookie_{i}": f"val_{i}" for i in range(8)}
        mock_cc.return_value = cookies
        # open succeeds, then all cookie sets fail except first two
        mock_ab.side_effect = [
            (True, "ok"),
            (True, "ok"),       # cookie_0
            (True, "ok"),       # cookie_1
            (False, "err"),     # cookie_2
            (False, "err"),     # cookie_3
            (False, "err"),     # cookie_4
            (False, "err"),     # cookie_5
            (False, "err"),     # cookie_6
            (False, "err"),     # cookie_7
        ]
        result = inject("example.com")
        assert result["success"] is True
        assert result["count"] == 2
        assert "..." in result["message"]

    @patch("metabolon.organelles.porta._ab")
    @patch("metabolon.organelles.porta.chrome_cookies")
    def test_cookie_value_sanitization(self, mock_cc, mock_ab):
        """Newlines in cookie names/values are stripped."""
        mock_cc.return_value = {"good\nname": "val\r\nue"}
        mock_ab.return_value = (True, "ok")
        result = inject("example.com")
        assert result["success"] is True
        assert result["count"] == 1
        # Check the cookie set command used sanitized values
        # Second call is the cookie set (first was open)
        cookie_call = mock_ab.call_args_list[1]
        cmd = cookie_call[0][0]
        assert "goodname" in cmd
        assert "value" in cmd

    @patch("metabolon.organelles.porta._ab")
    @patch("metabolon.organelles.porta.chrome_cookies")
    def test_domain_passed_to_cookie_set(self, mock_cc, mock_ab):
        """Cookie set command includes --domain with dot prefix."""
        mock_cc.return_value = {"sid": "abc"}
        mock_ab.return_value = (True, "ok")
        result = inject("bigmodel.cn")
        cookie_call = mock_ab.call_args_list[1]
        cmd = cookie_call[0][0]
        assert "--domain" in cmd
        idx = cmd.index("--domain")
        assert cmd[idx + 1] == ".bigmodel.cn"

    @patch("metabolon.organelles.porta._ab")
    @patch("metabolon.organelles.porta.chrome_cookies")
    def test_cookie_flags_set(self, mock_cc, mock_ab):
        """Cookie set includes --httpOnly --secure --path /."""
        mock_cc.return_value = {"sid": "abc"}
        mock_ab.return_value = (True, "ok")
        result = inject("example.com")
        cookie_call = mock_ab.call_args_list[1]
        cmd = cookie_call[0][0]
        assert "--httpOnly" in cmd
        assert "--secure" in cmd
        assert "--path" in cmd
        path_idx = cmd.index("--path")
        assert cmd[path_idx + 1] == "/"
