"""Tests for hemostasis enzyme."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_unknown_action():
    """Unknown action returns error with 'Unknown action' in message."""
    from metabolon.enzymes.hemostasis import hemostasis

    result = hemostasis(action="nonexistent")
    assert not result.success
    assert "Unknown action" in result.message


def test_ps_action():
    """ps action returns ProcessListResult with matches list."""
    from metabolon.enzymes.hemostasis import hemostasis

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="123 python\n456 node\n", returncode=0
        )
        result = hemostasis(action="ps", pattern="python")
        assert result.count >= 0
        assert isinstance(result.matches, list)


def test_ps_timeout():
    """ps action handles TimeoutExpired gracefully."""
    from metabolon.enzymes.hemostasis import hemostasis

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pgrep", timeout=5)
        result = hemostasis(action="ps", pattern="test")
        assert result.count == 0


def test_kill_invalid_signal():
    """kill action with invalid signal returns error."""
    from metabolon.enzymes.hemostasis import hemostasis

    result = hemostasis(action="kill", pattern="test", signal="INVALID")
    assert not result.success
    assert "Invalid signal" in result.message


def test_kill_success():
    """kill action with valid signal returns success."""
    from metabolon.enzymes.hemostasis import hemostasis

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = hemostasis(action="kill", pattern="zombie-proc", signal="TERM")
        assert result.success
        assert "TERM" in result.message


def test_kill_no_match():
    """kill action when pkill finds no processes."""
    from metabolon.enzymes.hemostasis import hemostasis

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="")
        result = hemostasis(action="kill", pattern="nonexistent")
        assert not result.success
        assert "No processes" in result.message


def test_launchagent_invalid_action():
    """launchagent with unsupported action returns error."""
    from metabolon.enzymes.hemostasis import hemostasis

    result = hemostasis(action="launchagent", launchagent_action="restart")
    assert not result.success


def test_launchagent_missing_plist():
    """launchagent with nonexistent plist returns error."""
    from metabolon.enzymes.hemostasis import hemostasis

    result = hemostasis(action="launchagent", plist_path="/nonexistent.plist")
    assert not result.success
    assert "not found" in result.message.lower()


def test_launchagent_unload_success():
    """launchagent unload with valid plist returns success."""
    from metabolon.enzymes.hemostasis import hemostasis

    with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as f:
        f.write(b"<plist></plist>")
        plist = f.name
    try:
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = hemostasis(
                action="launchagent",
                plist_path=plist,
                launchagent_action="unload",
            )
            assert result.success
            assert "Unloaded" in result.message
    finally:
        os.unlink(plist)


def test_handoff_writes_file(tmp_path):
    """handoff action writes a markdown file with correct content."""
    from metabolon.enzymes.hemostasis import hemostasis

    with patch("metabolon.enzymes.hemostasis._HANDOFF_DIR", tmp_path):
        result = hemostasis(
            action="handoff",
            what_stopped="killed rogue cron",
            known_gaps="cron not restarted",
            next_steps="investigate root cause",
        )
        assert result.success
        files = list(tmp_path.glob("hemostasis-*.md"))
        assert len(files) == 1
        content = files[0].read_text()
        assert "killed rogue cron" in content
        assert "investigate root cause" in content
