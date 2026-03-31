from __future__ import annotations

"""Tests for effector — CLI binary runner."""

from unittest.mock import patch, MagicMock
import subprocess

import pytest


class TestRunCli:
    def test_success(self):
        from metabolon.organelles.effector import run_cli
        with patch("metabolon.organelles.effector.subprocess.run") as mock:
            mock.return_value = MagicMock(stdout="hello world\n", returncode=0)
            result = run_cli("/usr/bin/echo", ["test"])
        assert result == "hello world"

    def test_empty_output_returns_done(self):
        from metabolon.organelles.effector import run_cli
        with patch("metabolon.organelles.effector.subprocess.run") as mock:
            mock.return_value = MagicMock(stdout="", returncode=0)
            assert run_cli("/usr/bin/true", []) == "Done."

    def test_binary_not_found(self):
        from metabolon.organelles.effector import run_cli
        with patch("metabolon.organelles.effector.subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(ValueError, match="not found"):
                run_cli("/nonexistent/binary", [])

    def test_timeout(self):
        from metabolon.organelles.effector import run_cli
        with patch("metabolon.organelles.effector.subprocess.run",
                   side_effect=subprocess.TimeoutExpired("cmd", 30)):
            with pytest.raises(ValueError, match="timed out"):
                run_cli("slowcmd", [], timeout=30)

    def test_nonzero_exit(self):
        from metabolon.organelles.effector import run_cli
        with patch("metabolon.organelles.effector.subprocess.run",
                   side_effect=subprocess.CalledProcessError(1, "cmd", stderr="bad input")):
            with pytest.raises(ValueError, match="error"):
                run_cli("failing", [])
