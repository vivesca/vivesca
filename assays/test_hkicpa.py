#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/hkicpa — HKICPA LMS auto-login script."""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

HKICPA_PATH = Path(__file__).resolve().parents[1] / "effectors" / "hkicpa"


# ── File structure tests ──────────────────────────────────────────────────────


class TestHkicpaBasics:
    def test_file_exists(self):
        """Test that hkicpa effector file exists."""

        assert HKICPA_PATH.exists()
        assert HKICPA_PATH.is_file()

    def test_is_executable_script(self):
        """Test that hkicpa has proper shebang."""
        first_line = HKICPA_PATH.read_text().split("\n")[0]
        assert first_line.startswith("#!/usr/bin/env")

    def test_has_docstring(self):
        """Test that hkicpa has docstring."""
        content = HKICPA_PATH.read_text()
        assert '"""' in content or "'''" in content

    def test_has_main_function(self):
        """Test that hkicpa defines main function."""
        content = HKICPA_PATH.read_text()
        assert "def main" in content


# ── Load script via exec ───────────────────────────────────────────────────────


@pytest.fixture()
def hkicpa_module():
    """Load hkicpa via exec, returning namespace with functions."""
    ns: dict = {"__name__": "test_hkicpa", "__file__": str(HKICPA_PATH)}
    source = HKICPA_PATH.read_text(encoding="utf-8")
    exec(source, ns)
    return ns


# ── Constants tests ────────────────────────────────────────────────────────────


class TestConstants:
    def test_home_url_defined(self, hkicpa_module):
        """Test HOME_URL is defined."""
        assert "HOME_URL" in hkicpa_module
        assert hkicpa_module["HOME_URL"].startswith("https://")

    def test_login_url_defined(self, hkicpa_module):
        """Test LOGIN_URL is defined."""
        assert "LOGIN_URL" in hkicpa_module
        assert hkicpa_module["LOGIN_URL"].startswith("https://")

    def test_urls_are_hkicpa_domain(self, hkicpa_module):
        """Test URLs point to HKICPA domain."""
        assert "hkicpa.org.hk" in hkicpa_module["HOME_URL"]
        assert "hkicpa.org.hk" in hkicpa_module["LOGIN_URL"]


# ── Helper function tests ──────────────────────────────────────────────────────


class TestHelperFunctions:
    def test_run_function_exists(self, hkicpa_module):
        """Test run helper function exists."""
        assert "run" in hkicpa_module
        assert callable(hkicpa_module["run"])

    def test_ab_function_exists(self, hkicpa_module):
        """Test ab (agent-browser) helper function exists."""
        assert "ab" in hkicpa_module
        assert callable(hkicpa_module["ab"])

    def test_get_password_function_exists(self, hkicpa_module):
        """Test get_password function exists."""
        assert "get_password" in hkicpa_module
        assert callable(hkicpa_module["get_password"])


# ── get_password tests ─────────────────────────────────────────────────────────


class TestGetPassword:
    def test_get_password_exits_on_missing(self, hkicpa_module):
        """Test get_password exits when keychain has no password."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="")
            with patch.dict("os.environ", {"USER": "testuser"}):
                with pytest.raises(SystemExit):
                    hkicpa_module["get_password"]()

    def test_get_password_returns_password(self, hkicpa_module):
        """Test get_password returns password from keychain."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="mysecretpassword\n", stderr="")
            with patch.dict("os.environ", {"USER": "testuser"}):
                result = hkicpa_module["get_password"]()
                assert result == "mysecretpassword"

    def test_get_password_uses_security_command(self, hkicpa_module):
        """Test get_password uses macOS security command."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="password\n", stderr="")
            with patch.dict("os.environ", {"USER": "testuser"}):
                hkicpa_module["get_password"]()
                # Check the command contains security find-generic-password
                call_args = mock_run.call_args[0][0]
                assert "security" in call_args
                assert "find-generic-password" in call_args
                assert "-s hkicpa" in call_args


# ── run helper tests ───────────────────────────────────────────────────────────


class TestRunHelper:
    def test_run_uses_subprocess(self, hkicpa_module):
        """Test run helper uses subprocess.run with shell=True."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="output\n", stderr="")
            result = hkicpa_module["run"]("echo test")
            mock_run.assert_called_once()
            assert result == "output"

    def test_run_strips_output(self, hkicpa_module):
        """Test run strips whitespace from output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="  output  \n", stderr="")
            result = hkicpa_module["run"]("echo test")
            assert result == "output"


# ── ab helper tests ────────────────────────────────────────────────────────────


class TestAbHelper:
    def test_ab_calls_agent_browser(self, hkicpa_module):
        """Test ab calls agent-browser with args."""
        with patch("subprocess.run") as mock_run:
            hkicpa_module["ab"]("open", "https://example.com")
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "agent-browser"

    def test_ab_passes_args_correctly(self, hkicpa_module):
        """Test ab passes all args to agent-browser."""
        with patch("subprocess.run") as mock_run:
            hkicpa_module["ab"]("--headed", "open", "url")
            call_args = mock_run.call_args[0][0]
            assert "--headed" in call_args
            assert "open" in call_args
            assert "url" in call_args


# ── main function tests ────────────────────────────────────────────────────────


class TestMain:
    def test_main_exits_on_missing_password(self, hkicpa_module):
        """Test main exits when password not found."""
        with patch("subprocess.run") as mock_run:
            # First call for get_password returns empty
            mock_run.return_value = MagicMock(stdout="", stderr="")
            with patch.dict("os.environ", {"USER": "testuser"}):
                with pytest.raises(SystemExit):
                    hkicpa_module["main"]()

    def test_main_uses_default_home_url(self, hkicpa_module):
        """Test main uses HOME_URL when no argument."""
        with patch("subprocess.run") as mock_run:
            # Mock responses: security, close, open, fill, press, get url
            mock_run.side_effect = [
                MagicMock(stdout="password\n", stderr=""),  # security
                MagicMock(stdout="", stderr=""),  # close
                MagicMock(stdout="", stderr=""),  # --headed open
                MagicMock(stdout="", stderr=""),  # fill
                MagicMock(stdout="", stderr=""),  # press
                MagicMock(stdout="https://lms.hkicpa.org.hk/session/out", stderr=""),  # get url - login failed
            ]
            with patch.dict("os.environ", {"USER": "testuser"}):
                with patch("time.sleep"):
                    with patch.object(hkicpa_module["sys"], "argv", ["hkicpa"]):
                        with pytest.raises(SystemExit) as exc_info:
                            hkicpa_module["main"]()
                        assert exc_info.value.code == 1

    def test_main_accepts_course_url_argument(self, hkicpa_module):
        """Test main accepts course URL as argument."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout="password\n", stderr=""),  # security
                MagicMock(stdout="", stderr=""),  # close
                MagicMock(stdout="", stderr=""),  # --headed open
                MagicMock(stdout="", stderr=""),  # fill
                MagicMock(stdout="", stderr=""),  # press
                MagicMock(stdout="https://lms.hkicpa.org.hk/session/out", stderr=""),  # get url - login failed
            ]
            with patch.dict("os.environ", {"USER": "testuser"}):
                with patch("time.sleep"):
                    with patch.object(
                        hkicpa_module["sys"], "argv", ["hkicpa", "https://course.url"]
                    ):
                        with pytest.raises(SystemExit) as exc_info:
                            hkicpa_module["main"]()
                        assert exc_info.value.code == 1


# ── Login flow tests ───────────────────────────────────────────────────────────


class TestLoginFlow:
    def test_main_closes_browser_first(self, hkicpa_module):
        """Test main closes browser before starting."""
        calls = []

        def track_run(*args, **kwargs):
            cmd = args[0] if args else ""
            calls.append(cmd)
            if "security" in str(cmd):
                return MagicMock(stdout="password\n", stderr="")
            elif "get url" in str(cmd):
                return MagicMock(stdout="https://lms.hkicpa.org.hk/dashboard", stderr="")
            return MagicMock(stdout="", stderr="")

        with patch("subprocess.run", side_effect=track_run):
            with patch.dict("os.environ", {"USER": "testuser"}):
                with patch("time.sleep"):
                    with patch.object(hkicpa_module["sys"], "argv", ["hkicpa"]):
                        # main should complete successfully with valid URL
                        hkicpa_module["main"]()

        # Verify that close was called
        assert any("close" in str(c) for c in calls)

    def test_main_detects_login_failure(self, hkicpa_module):
        """Test main detects when login fails."""
        with patch("subprocess.run") as mock_run:
            # Password retrieval succeeds
            # URL check shows login page
            mock_run.side_effect = [
                MagicMock(stdout="password\n", stderr=""),  # security
                MagicMock(stdout="", stderr=""),  # close
                MagicMock(stdout="", stderr=""),  # --headed open
                MagicMock(stdout="", stderr=""),  # fill
                MagicMock(stdout="", stderr=""),  # press
                MagicMock(
                    stdout="https://lms.hkicpa.org.hk/session/out", stderr=""
                ),  # get url
            ]
            with patch.dict("os.environ", {"USER": "testuser"}):
                with patch("time.sleep"):
                    with patch.object(hkicpa_module["sys"], "argv", ["hkicpa"]):
                        with pytest.raises(SystemExit) as exc_info:
                            hkicpa_module["main"]()
                        assert exc_info.value.code == 1
