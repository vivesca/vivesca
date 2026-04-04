from __future__ import annotations

"""Tests for metabolon.organelles.effector — run_cli."""

import subprocess
from unittest.mock import patch

import pytest

from metabolon.organelles.effector import run_cli

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ok(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess:
    """Build a successful CompletedProcess."""
    return subprocess.CompletedProcess(
        args=["/usr/bin/true"],
        returncode=returncode,
        stdout=stdout,
        stderr="",
    )


# ---------------------------------------------------------------------------
# Success cases
# ---------------------------------------------------------------------------


class TestRunCliSuccess:
    @patch("metabolon.organelles.effector.subprocess.run")
    def test_returns_stdout_stripped(self, mock_run):
        mock_run.return_value = _ok(stdout="  hello world\n")
        assert run_cli("/usr/bin/echo", ["hello", "world"]) == "hello world"

    @patch("metabolon.organelles.effector.subprocess.run")
    def test_empty_stdout_returns_done(self, mock_run):
        mock_run.return_value = _ok(stdout="")
        assert run_cli("/usr/bin/true", []) == "Done."

    @patch("metabolon.organelles.effector.subprocess.run")
    def test_whitespace_only_stdout_returns_done(self, mock_run):
        mock_run.return_value = _ok(stdout="   \n  \n")
        assert run_cli("/usr/bin/true", []) == "Done."

    @patch("metabolon.organelles.effector.subprocess.run")
    def test_passes_args(self, mock_run):
        mock_run.return_value = _ok(stdout="ok")
        run_cli("/bin/cmd", ["--flag", "val"])
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["/bin/cmd", "--flag", "val"]

    @patch("metabolon.organelles.effector.subprocess.run")
    def test_passes_timeout(self, mock_run):
        mock_run.return_value = _ok(stdout="ok")
        run_cli("/bin/cmd", [], timeout=99)
        assert mock_run.call_args[1]["timeout"] == 99

    @patch("metabolon.organelles.effector.subprocess.run")
    def test_passes_stdin_text(self, mock_run):
        mock_run.return_value = _ok(stdout="ok")
        run_cli("/bin/cmd", [], stdin_text="input data")
        assert mock_run.call_args[1]["input"] == "input data"

    @patch("metabolon.organelles.effector.subprocess.run")
    def test_stdin_text_default_none(self, mock_run):
        mock_run.return_value = _ok(stdout="ok")
        run_cli("/bin/cmd", [])
        assert mock_run.call_args[1]["input"] is None

    @patch("metabolon.organelles.effector.subprocess.run")
    def test_default_timeout_30(self, mock_run):
        mock_run.return_value = _ok(stdout="ok")
        run_cli("/bin/cmd", [])
        assert mock_run.call_args[1]["timeout"] == 30

    @patch("metabolon.organelles.effector.os.path.expanduser")
    @patch("metabolon.organelles.effector.subprocess.run")
    def test_expanduser_called(self, mock_run, mock_expand):
        mock_expand.return_value = str(Path.home() / "bin/foo")
        mock_run.return_value = _ok(stdout="expanded")
        result = run_cli("~/bin/foo", [])
        mock_expand.assert_called_once_with("~/bin/foo")
        assert result == "expanded"


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


class TestRunCliErrors:
    @patch("metabolon.organelles.effector.subprocess.run")
    def test_file_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError
        with pytest.raises(ValueError, match="Binary not found"):
            run_cli("/no/such/binary", [])

    @patch("metabolon.organelles.effector.subprocess.run")
    def test_timeout_expired(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="slow", timeout=5)
        with pytest.raises(ValueError, match=r"timed out \(5s\)"):
            run_cli("/usr/bin/slow", [], timeout=5)

    @patch("metabolon.organelles.effector.subprocess.run")
    def test_called_process_error_with_stderr(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd="git", stderr="fatal: not a repo\n"
        )
        with pytest.raises(ValueError, match="git error: fatal: not a repo"):
            run_cli("/usr/bin/git", ["status"])

    @patch("metabolon.organelles.effector.subprocess.run")
    def test_called_process_error_no_stderr(self, mock_run):
        err = subprocess.CalledProcessError(returncode=2, cmd="fail", stderr=None)
        mock_run.side_effect = err
        with pytest.raises(ValueError, match="fail error:"):
            run_cli("/usr/bin/fail", [])

    @patch("metabolon.organelles.effector.subprocess.run")
    def test_called_process_error_empty_stderr(self, mock_run):
        err = subprocess.CalledProcessError(returncode=1, cmd="cmd", stderr="")
        mock_run.side_effect = err
        with pytest.raises(ValueError, match="cmd error:"):
            run_cli("/usr/bin/cmd", [])

    @patch("metabolon.organelles.effector.subprocess.run")
    def test_uses_basename_in_error_messages(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="x", timeout=10)
        with pytest.raises(ValueError, match="sleeper timed out"):
            run_cli("/usr/local/bin/sleeper", [], timeout=10)
