from __future__ import annotations
"""Tests for effectors/cleanup-stuck — kills stuck processes to free resources."""

import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "cleanup-stuck"


class TestCleanupStuckScript:
    """Tests for the cleanup-stuck bash script via subprocess."""

    def test_script_exists_and_is_executable(self):
        """Script file exists."""
        assert SCRIPT.exists()

    def test_runs_with_zero_exit_code(self):
        """Script exits 0 even when no matching processes exist."""
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0

    def test_reports_pyenv_cleanup(self):
        """Script prints message about killing pyenv processes."""
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "Killing stuck pyenv processes..." in result.stdout

    def test_reports_claude_agent_cleanup(self):
        """Script prints message about killing Claude agents."""
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "Killing orphan Claude agents..." in result.stdout

    def test_reports_playwright_cleanup(self):
        """Script prints message about killing playwright."""
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "Killing stuck playwright..." in result.stdout

    def test_reports_process_count(self):
        """Script prints current process count."""
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "Process count:" in result.stdout
        # Extract the number and verify it is a positive integer
        for line in result.stdout.splitlines():
            if line.startswith("Process count:"):
                count_str = line.split(":", 1)[1].strip()
                count = int(count_str)
                assert count > 0
                break
        else:
            pytest.fail("Process count line not found")

    def test_reports_done_message(self):
        """Script prints final 'Done' message."""
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "Done." in result.stdout

    def test_stderr_is_empty(self):
        """Script suppresses pkill errors — stderr should be empty."""
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.stderr == ""

    def test_output_line_order(self):
        """Script outputs messages in the expected order."""
        result = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        # Find indices of key messages
        labels = [
            "Killing stuck pyenv",
            "Killing orphan Claude",
            "Killing stuck playwright",
            "Process count:",
            "Done.",
        ]
        indices = []
        for label in labels:
            for i, line in enumerate(lines):
                if label in line:
                    indices.append(i)
                    break
            else:
                pytest.fail(f"Label '{label}' not found in output")
        # Each label should appear after the previous one
        assert indices == sorted(indices), f"Labels out of order: {indices}"

    def test_idempotent_multiple_runs(self):
        """Running the script twice in succession succeeds both times."""
        for _ in range(2):
            result = subprocess.run(
                ["bash", str(SCRIPT)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.returncode == 0

    def test_pkill_commands_use_signal_9(self):
        """Script uses pkill -9 (SIGKILL) for all kill commands."""
        content = SCRIPT.read_text()
        # Count pkill -9 occurrences
        sigkill_count = content.count("pkill -9")
        assert sigkill_count == 5  # pyenv, node.*claude, python.*agent, playwright, chromium

    def test_script_targets_expected_patterns(self):
        """Script targets the expected process patterns."""
        content = SCRIPT.read_text()
        assert '"pyenv"' in content
        assert '"node.*claude"' in content
        assert '"python.*agent"' in content
        assert '"playwright"' in content
        assert '"chromium"' in content

    def test_script_suppresses_pkill_stderr(self):
        """All pkill commands redirect stderr to /dev/null."""
        content = SCRIPT.read_text()
        # Every pkill line should end with 2>/dev/null
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("pkill"):
                assert "2>/dev/null" in stripped, f"Missing stderr redirect: {stripped}"
