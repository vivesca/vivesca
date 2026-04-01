from __future__ import annotations

"""Tests for navigator enzyme."""


import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest


def test_navigator_actions_unknown_action():
    """Unknown action returns error with 'Unknown action' in message."""
    from metabolon.enzymes.navigator import navigator

    result = navigator(action="nonexistent")
    assert result.success is False
    assert "Unknown action" in result.error


def test_extract_requires_url():
    """extract action without url returns error."""
    from metabolon.enzymes.navigator import navigator

    result = navigator(action="extract")
    assert result.success is False
    assert "url" in result.error.lower()


def test_extract_success():
    """extract action with mocked _run_ab returns page data."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch("time.sleep"):
        mock_ab.side_effect = [
            (True, "navigated"),  # open
            (True, "Page Title"),  # get title
            (True, "Page content"),  # get text
            (True, "https://x.com"),  # get url
        ]
        result = navigator(action="extract", url="https://x.com", wait_ms=0)
        assert result.success is True
        assert result.data["title"] == "Page Title"
        assert result.data["text"] == "Page content"


def test_extract_navigation_failure():
    """extract action when open fails returns error."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab:
        mock_ab.return_value = (False, "Connection refused")
        result = navigator(action="extract", url="https://x.com")
        assert result.success is False
        assert "failed" in result.error.lower()


def test_screenshot_requires_url():
    """screenshot action without url returns error."""
    from metabolon.enzymes.navigator import navigator

    result = navigator(action="screenshot")
    assert result.success is False
    assert "url" in result.error.lower()


def test_screenshot_success():
    """screenshot action with mocked _run_ab returns output_path."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch(
        "subprocess.run"
    ), patch("time.sleep"):
        mock_ab.side_effect = [
            (True, "navigated"),  # open
            (True, "captured"),  # screenshot
        ]
        result = navigator(
            action="screenshot",
            url="https://x.com",
            output_path="/tmp/test.png",
            wait_ms=0,
        )
        assert result.success is True
        assert result.data["output_path"] == "/tmp/test.png"


def test_check_auth_requires_domain():
    """check_auth action without domain returns error."""
    from metabolon.enzymes.navigator import navigator

    result = navigator(action="check_auth")
    assert result.success is False
    assert "domain" in result.error.lower()


def test_check_auth_authenticated():
    """check_auth when redirected to dashboard → authenticated."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch("time.sleep"):
        mock_ab.side_effect = [
            (True, "navigated"),  # open
            (True, "https://app.example.com/dashboard"),  # get url
        ]
        result = navigator(action="check_auth", domain="example.com")
        assert result.success is True
        assert result.data["is_authenticated"] is True


def test_check_auth_not_authenticated():
    """check_auth when redirected to login → not authenticated, guidance mentions porta."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch("time.sleep"):
        mock_ab.side_effect = [
            (True, "navigated"),
            (True, "https://example.com/login?redirect=dashboard"),
        ]
        result = navigator(action="check_auth", domain="example.com")
        assert result.success is True
        assert result.data["is_authenticated"] is False
        assert "porta" in result.data.get("guidance", "").lower()


# ── _run_ab unit tests ──────────────────────────────────────────────


def test_run_ab_success():
    """_run_ab returns (True, stdout) on success."""
    from metabolon.enzymes.navigator import _run_ab

    with patch("os.popen") as mock_popen, patch("subprocess.run") as mock_run:
        mock_popen.return_value.read.return_value = "/usr/bin/agent-browser\n"
        mock_run.return_value = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="page data"
        )
        ok, out = _run_ab(["open", "https://x.com"])
        assert ok is True
        assert out == "page data"


def test_run_ab_failure():
    """_run_ab returns (False, stderr) on CalledProcessError."""
    from metabolon.enzymes.navigator import _run_ab

    with patch("os.popen") as mock_popen, patch("subprocess.run") as mock_run:
        mock_popen.return_value.read.return_value = ""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "agent-browser", stderr="connection refused"
        )
        ok, out = _run_ab(["open", "https://x.com"])
        assert ok is False
        assert "connection refused" in out


# ── extract edge cases ──────────────────────────────────────────────


def test_extract_with_wait_ms():
    """extract calls time.sleep with correct duration."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch(
        "metabolon.enzymes.navigator.time.sleep"
    ) as mock_sleep:
        mock_ab.side_effect = [
            (True, "ok"),
            (True, "Title"),
            (True, "Text"),
            (True, "https://x.com"),
        ]
        result = navigator(action="extract", url="https://x.com", wait_ms=2000)
        assert result.success is True
        mock_sleep.assert_called_once_with(2.0)


def test_extract_partial_title_failure():
    """extract with title failure falls back to empty string."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch("time.sleep"):
        mock_ab.side_effect = [
            (True, "ok"),
            (False, "error"),  # title fails
            (True, "Text"),
            (True, "https://x.com"),
        ]
        result = navigator(action="extract", url="https://x.com", wait_ms=0)
        assert result.success is True
        assert result.data["title"] == ""
        assert result.data["text"] == "Text"


def test_extract_partial_url_failure():
    """extract with url-get failure falls back to original url."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch("time.sleep"):
        mock_ab.side_effect = [
            (True, "ok"),
            (True, "Title"),
            (True, "Text"),
            (False, "error"),  # url fails
        ]
        result = navigator(action="extract", url="https://x.com", wait_ms=0)
        assert result.success is True
        assert result.data["url"] == "https://x.com"


def test_navigator_actions_action_case_insensitive():
    """Action is case-insensitive."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch("time.sleep"):
        mock_ab.side_effect = [
            (True, "ok"),
            (True, "Title"),
            (True, "Text"),
            (True, "https://x.com"),
        ]
        result = navigator(action="EXTRACT", url="https://x.com", wait_ms=0)
        assert result.success is True


# ── screenshot edge cases ───────────────────────────────────────────


def test_screenshot_auto_temp_path():
    """screenshot without output_path generates a temp path and registers it."""
    from metabolon.enzymes.navigator import navigator, _pending_screenshots

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch(
        "subprocess.run"
    ), patch("time.sleep"):
        mock_ab.side_effect = [
            (True, "navigated"),
            (True, "captured"),
        ]
        result = navigator(
            action="screenshot", url="https://x.com", wait_ms=0
        )
        assert result.success is True
        assert "output_path" in result.data
        assert result.data["output_path"].endswith(".png")
        assert result.data["output_path"] in _pending_screenshots
        _pending_screenshots.remove(result.data["output_path"])


def test_screenshot_navigation_failure():
    """screenshot when open fails returns error."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch(
        "subprocess.run"
    ), patch("time.sleep"):
        mock_ab.return_value = (False, "timeout")
        result = navigator(action="screenshot", url="https://x.com")
        assert result.success is False
        assert "failed" in result.error.lower()


def test_screenshot_capture_failure():
    """screenshot when screenshot command fails returns error."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch(
        "subprocess.run"
    ), patch("time.sleep"):
        mock_ab.side_effect = [
            (True, "navigated"),
            (False, "capture failed"),
        ]
        result = navigator(
            action="screenshot", url="https://x.com", output_path="/tmp/out.png"
        )
        assert result.success is False
        assert "capture failed" in result.error


# ── check_auth edge cases ───────────────────────────────────────────


def test_check_auth_domain_with_http_prefix():
    """check_auth with http-prefixed domain uses it directly."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch("time.sleep"):
        mock_ab.side_effect = [
            (True, "navigated"),
            (True, "https://app.example.com/home"),
        ]
        result = navigator(action="check_auth", domain="https://example.com")
        assert result.success is True
        assert result.data["is_authenticated"] is True
        # Verify it didn't prepend https:// again
        call_args = mock_ab.call_args_list[0][0][0]
        assert call_args == ["open", "https://example.com"]


def test_check_auth_signin_redirect():
    """check_auth when URL contains 'signin' → not authenticated."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch("time.sleep"):
        mock_ab.side_effect = [
            (True, "navigated"),
            (True, "https://example.com/signin"),
        ]
        result = navigator(action="check_auth", domain="example.com")
        assert result.success is True
        assert result.data["is_authenticated"] is False


def test_check_auth_auth_redirect():
    """check_auth when URL contains 'auth' → not authenticated."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch("time.sleep"):
        mock_ab.side_effect = [
            (True, "navigated"),
            (True, "https://example.com/authorize"),
        ]
        result = navigator(action="check_auth", domain="example.com")
        assert result.success is True
        assert result.data["is_authenticated"] is False


def test_check_auth_navigation_failure():
    """check_auth when open fails returns error."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch("time.sleep"):
        mock_ab.return_value = (False, "Connection refused")
        result = navigator(action="check_auth", domain="example.com")
        assert result.success is False
        assert "failed" in result.error.lower()


def test_check_auth_get_url_failure():
    """check_auth when get-url fails uses empty string."""
    from metabolon.enzymes.navigator import navigator

    with patch("metabolon.enzymes.navigator._run_ab") as mock_ab, patch("time.sleep"):
        mock_ab.side_effect = [
            (True, "navigated"),
            (False, "error"),
        ]
        result = navigator(action="check_auth", domain="example.com")
        assert result.success is True
        assert result.data["current_url"] == ""
        # No login/signin/auth in empty string → considered authenticated
        assert result.data["is_authenticated"] is True


# ── NavigatorResult model ───────────────────────────────────────────


def test_navigator_result_model():
    """NavigatorResult stores fields correctly."""
    from metabolon.enzymes.navigator import NavigatorResult

    r = NavigatorResult(success=True, data={"k": "v"})
    assert r.success is True
    assert r.data == {"k": "v"}
    assert r.error is None

    r2 = NavigatorResult(success=False, data={}, error="boom")
    assert r2.error == "boom"


# ── _cleanup_temp_screenshots ───────────────────────────────────────


def test_cleanup_temp_screenshots():
    """_cleanup_temp_screenshots removes registered files."""
    import tempfile
    from metabolon.enzymes.navigator import _cleanup_temp_screenshots, _pending_screenshots

    tmp = os.path.join(tempfile.gettempdir(), "navigator_test_cleanup.png")
    Path(tmp).write_text("x")
    _pending_screenshots.append(tmp)
    assert Path(tmp).exists()

    _cleanup_temp_screenshots()
    assert not Path(tmp).exists()
    # Cleanup list state
    if tmp in _pending_screenshots:
        _pending_screenshots.remove(tmp)
