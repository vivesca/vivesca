from __future__ import annotations
"""Tests for metabolon.enzymes.hemostasis — emergency process stabilization."""


import datetime
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.hemostasis import hemostasis, ProcessListResult
from metabolon.morphology import EffectorResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_completed(
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
) -> MagicMock:
    proc = MagicMock(spec=subprocess.CompletedProcess)
    proc.stdout = stdout
    proc.stderr = stderr
    proc.returncode = returncode
    return proc


# ===========================================================================
# ps action
# ===========================================================================

class TestPsAction:
    @patch("metabolon.enzymes.hemostasis.subprocess.run")
    def test_ps_returns_matching_processes(self, mock_run):
        mock_run.return_value = _make_completed(
            stdout="1234 python app.py\n5678 node server.js\n"
        )
        result = hemostasis(action="ps", pattern="python")

        assert isinstance(result, ProcessListResult)
        assert result.count == 2
        assert result.matches == ["1234 python app.py", "5678 node server.js"]
        assert "2 found" in result.summary
        mock_run.assert_called_once_with(
            ["pgrep", "-l", "-a", "-f", "python"],
            capture_output=True,
            text=True,
            timeout=5,
        )

    @patch("metabolon.enzymes.hemostasis.subprocess.run")
    def test_ps_no_matches(self, mock_run):
        mock_run.return_value = _make_completed(stdout="")
        result = hemostasis(action="ps", pattern="nonexistent_xyz")

        assert isinstance(result, ProcessListResult)
        assert result.count == 0
        assert result.matches == []
        assert "(none)" in result.summary

    @patch("metabolon.enzymes.hemostasis.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="pgrep", timeout=5))
    def test_ps_timeout_returns_empty(self, mock_run):
        result = hemostasis(action="ps", pattern="slow")

        assert isinstance(result, ProcessListResult)
        assert result.count == 0
        assert result.matches == []

    @patch("metabolon.enzymes.hemostasis.subprocess.run")
    def test_ps_strips_blank_lines(self, mock_run):
        mock_run.return_value = _make_completed(stdout="\n999 proc1\n\n\n")
        result = hemostasis(action="ps", pattern="proc")

        assert result.count == 1
        assert result.matches == ["999 proc1"]


# ===========================================================================
# kill action
# ===========================================================================

class TestKillAction:
    @patch("metabolon.enzymes.hemostasis.subprocess.run")
    def test_kill_success(self, mock_run):
        mock_run.return_value = _make_completed(returncode=0)
        result = hemostasis(action="kill", pattern="rogue_proc")

        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert "TERM" in result.message
        assert result.data["signal"] == "TERM"
        mock_run.assert_called_once_with(
            ["pkill", "-TERM", "-f", "rogue_proc"],
            capture_output=True,
            text=True,
            timeout=10,
        )

    @patch("metabolon.enzymes.hemostasis.subprocess.run")
    def test_kill_no_match(self, mock_run):
        mock_run.return_value = _make_completed(returncode=1)
        result = hemostasis(action="kill", pattern="nothing")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "No processes found" in result.message

    @patch("metabolon.enzymes.hemostasis.subprocess.run")
    def test_kill_error_exit(self, mock_run):
        mock_run.return_value = _make_completed(returncode=2, stderr="permission denied")
        result = hemostasis(action="kill", pattern="foo")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "pkill error" in result.message
        assert "permission denied" in result.message

    @patch("metabolon.enzymes.hemostasis.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="pkill", timeout=10))
    def test_kill_timeout(self, mock_run):
        result = hemostasis(action="kill", pattern="hung")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "timed out" in result.message

    def test_kill_invalid_signal(self):
        result = hemostasis(action="kill", pattern="x", signal="BOGUS")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "Invalid signal" in result.message

    @patch("metabolon.enzymes.hemostasis.subprocess.run")
    def test_kill_custom_signal(self, mock_run):
        mock_run.return_value = _make_completed(returncode=0)
        result = hemostasis(action="kill", pattern="x", signal="KILL")

        assert result.success is True
        assert result.data["signal"] == "KILL"
        mock_run.assert_called_once_with(
            ["pkill", "-KILL", "-f", "x"],
            capture_output=True,
            text=True,
            timeout=10,
        )


# ===========================================================================
# launchagent action
# ===========================================================================

class TestLaunchAgentAction:
    @patch("metabolon.enzymes.hemostasis.subprocess.run")
    def test_unload_success(self, mock_run, tmp_path):
        plist = tmp_path / "com.example.agent.plist"
        plist.write_text("<plist/>")

        mock_run.return_value = _make_completed(returncode=0)
        result = hemostasis(
            action="launchagent",
            plist_path=str(plist),
            launchagent_action="unload",
        )

        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert "Unloaded" in result.message
        mock_run.assert_called_once_with(
            ["launchctl", "unload", str(plist)],
            capture_output=True,
            text=True,
            timeout=15,
        )

    @patch("metabolon.enzymes.hemostasis.subprocess.run")
    def test_load_success(self, mock_run, tmp_path):
        plist = tmp_path / "com.example.agent.plist"
        plist.write_text("<plist/>")

        mock_run.return_value = _make_completed(returncode=0)
        result = hemostasis(
            action="launchagent",
            plist_path=str(plist),
            launchagent_action="load",
        )

        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert "Loaded" in result.message

    def test_launchagent_invalid_action(self, tmp_path):
        plist = tmp_path / "x.plist"
        plist.write_text("x")
        result = hemostasis(
            action="launchagent",
            plist_path=str(plist),
            launchagent_action="restart",
        )

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "Invalid action" in result.message

    def test_launchagent_missing_plist(self):
        result = hemostasis(
            action="launchagent",
            plist_path="/nonexistent/path.plist",
            launchagent_action="unload",
        )

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "Plist not found" in result.message

    @patch("metabolon.enzymes.hemostasis.subprocess.run")
    def test_launchctl_failure(self, mock_run, tmp_path):
        plist = tmp_path / "com.example.agent.plist"
        plist.write_text("<plist/>")

        mock_run.return_value = _make_completed(returncode=1, stderr="operation failed")
        result = hemostasis(
            action="launchagent",
            plist_path=str(plist),
            launchagent_action="unload",
        )

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "launchctl unload failed" in result.message

    @patch("metabolon.enzymes.hemostasis.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="launchctl", timeout=15))
    def test_launchagent_timeout(self, mock_run, tmp_path):
        plist = tmp_path / "com.example.agent.plist"
        plist.write_text("<plist/>")

        result = hemostasis(
            action="launchagent",
            plist_path=str(plist),
            launchagent_action="unload",
        )

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "timed out" in result.message


# ===========================================================================
# handoff action
# ===========================================================================

class TestHandoffAction:
    @patch("metabolon.enzymes.hemostasis._HANDOFF_DIR", new_callable=lambda: lambda: Path("/tmp/hemostasis_test_handoff"))
    def test_handoff_writes_note(self, tmp_path_factory):
        # Use a real temp dir via patching
        import tempfile
        handoff_dir = Path(tempfile.mkdtemp())
        with patch("metabolon.enzymes.hemostasis._HANDOFF_DIR", handoff_dir):
            result = hemostasis(
                action="handoff",
                what_stopped="nginx, sidekiq",
                known_gaps="redis not responding",
                next_steps="restart redis, check sidekiq logs",
            )

        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert "Handoff note written" in result.message

        written_path = Path(result.data["path"])
        assert written_path.exists()
        content = written_path.read_text()
        assert "nginx, sidekiq" in content
        assert "redis not responding" in content
        assert "restart redis" in content
        assert "hemostasis-handoff" in content

    def test_handoff_creates_directory(self):
        import tempfile
        handoff_dir = Path(tempfile.mkdtemp()) / "sub" / "dir"
        with patch("metabolon.enzymes.hemostasis._HANDOFF_DIR", handoff_dir):
            result = hemostasis(
                action="handoff",
                what_stopped="foo",
                known_gaps="bar",
                next_steps="baz",
            )

        assert result.success is True
        assert handoff_dir.exists()


# ===========================================================================
# Unknown action
# ===========================================================================

class TestUnknownAction:
    def test_unknown_action_returns_error(self):
        result = hemostasis(action="explode")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "Unknown action" in result.message

    def test_action_case_insensitive(self):
        """Action matching should be case-insensitive."""
        with patch("metabolon.enzymes.hemostasis.subprocess.run") as mock_run:
            mock_run.return_value = _make_completed(stdout="")
            result = hemostasis(action="PS", pattern="test")

        assert isinstance(result, ProcessListResult)
