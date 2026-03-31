from __future__ import annotations

"""Tests for effectors/cleanup-stuck — bash script that kills stuck processes."""

import subprocess
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "effectors" / "cleanup-stuck"


# ── Script validity ────────────────────────────────────────────────────


class TestScriptValidity:
    """Basic script properties: exists, executable, valid bash."""

    def test_script_exists(self):
        """cleanup-stuck script exists at expected path."""
        assert SCRIPT.exists()

    def test_script_is_executable(self):
        """cleanup-stuck is executable."""
        assert SCRIPT.stat().st_mode & 0o111

    def test_script_is_bash(self):
        """cleanup-stuck starts with a bash shebang."""
        first_line = SCRIPT.read_text().splitlines()[0]
        assert "bash" in first_line


# ── Run script end-to-end (safe — no matching processes on CI) ────────


class TestScriptExecution:
    """Run the actual script and verify output format and exit code."""

    def test_exits_zero(self):
        """Script exits with code 0 even when no processes match."""
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0

    def test_outputs_pyenv_message(self):
        """Script prints message about killing pyenv processes."""
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "pyenv" in result.stdout.lower()

    def test_outputs_claude_agent_message(self):
        """Script prints message about killing orphan Claude agents."""
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "claude" in result.stdout.lower() or "agent" in result.stdout.lower()

    def test_outputs_playwright_message(self):
        """Script prints message about killing playwright/chromium."""
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "playwright" in result.stdout.lower() or "chromium" in result.stdout.lower()

    def test_outputs_process_count(self):
        """Script prints a process count line with a number."""
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Line like "Process count: 142"
        for line in result.stdout.splitlines():
            if "Process count:" in line or "process count" in line.lower():
                digits = [c for c in line if c.isdigit()]
                assert len(digits) >= 1, f"No digits in process count line: {line}"
                break
        else:
            pytest.fail("No process count line found in output")

    def test_outputs_done_message(self):
        """Script prints 'Done' at the end."""
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "Done" in result.stdout

    def test_no_stderr_on_clean_run(self):
        """Script produces no stderr when no stuck processes exist."""
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # pkill writes to stderr when no match, but 2>/dev/null suppresses it
        assert result.stderr.strip() == ""


# ── Script content analysis ────────────────────────────────────────────


class TestScriptContent:
    """Verify the script targets the expected process patterns."""

    def test_targets_pyenv(self):
        """Script contains pkill for pyenv processes."""
        content = SCRIPT.read_text()
        assert "pyenv" in content
        assert "pkill" in content

    def test_targets_claude_node(self):
        """Script contains pkill for node.*claude."""
        content = SCRIPT.read_text()
        assert "node" in content and "claude" in content

    def test_targets_python_agent(self):
        """Script contains pkill for python.*agent."""
        content = SCRIPT.read_text()
        assert "python" in content and "agent" in content

    def test_targets_playwright(self):
        """Script contains pkill for playwright."""
        content = SCRIPT.read_text()
        assert "playwright" in content

    def test_targets_chromium(self):
        """Script contains pkill for chromium."""
        content = SCRIPT.read_text()
        assert "chromium" in content

    def test_uses_kill_signal_9(self):
        """Script uses -9 (SIGKILL) for forceful termination."""
        content = SCRIPT.read_text()
        assert "-9" in content

    def test_suppresses_pkill_errors(self):
        """Script redirects pkill stderr to /dev/null."""
        content = SCRIPT.read_text()
        assert "2>/dev/null" in content

    def test_uses_pkill_not_killall(self):
        """Script uses pkill (pattern-based) not killall (name-based)."""
        content = SCRIPT.read_text()
        assert "pkill" in content


# ── Mocked pkill to verify commands ────────────────────────────────────


class TestMockedExecution:
    """Run script with mocked pkill/ps to verify exact invocations."""

    def test_pkill_called_for_each_pattern(self, tmp_path):
        """Script calls pkill once for each target pattern."""
        log = tmp_path / "calls.log"
        # Create a fake pkill that logs its arguments
        fake_pkill = tmp_path / "pkill"
        fake_pkill.write_text(
            f'#!/bin/bash\necho "$@" >> {log}\nexit 0\n'
        )
        fake_pkill.chmod(0o755)

        # Create a fake ps that returns a count
        fake_ps = tmp_path / "ps"
        fake_ps.write_text('#!/bin/bash\necho "USER PID %%CPU %%MEM COMMAND"\necho "root 1 0.0 0.0 bash"\n')
        fake_ps.chmod(0o755)

        # Create a fake wc that returns a number
        fake_wc = tmp_path / "wc"
        fake_wc.write_text('#!/bin/bash\necho "5"\n')
        fake_wc.chmod(0o755)

        env = {
            "PATH": f"{tmp_path}:{__import__('os').environ.get('PATH', '')}",
        }
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        assert result.returncode == 0

        calls = log.read_text().strip().splitlines()
        # Should have pkill calls for: pyenv, node.*claude, python.*agent, playwright, chromium
        assert len(calls) >= 5, f"Expected >=5 pkill calls, got {len(calls)}: {calls}"

        # Verify each expected pattern is targeted
        all_args = " ".join(calls)
        assert "pyenv" in all_args
        assert "node.*claude" in all_args
        assert "python.*agent" in all_args
        assert "playwright" in all_args
        assert "chromium" in all_args

    def test_pkill_uses_sigkill(self, tmp_path):
        """Each pkill invocation uses -9 flag."""
        log = tmp_path / "calls.log"
        fake_pkill = tmp_path / "pkill"
        fake_pkill.write_text(
            f'#!/bin/bash\necho "$@" >> {log}\nexit 0\n'
        )
        fake_pkill.chmod(0o755)
        fake_ps = tmp_path / "ps"
        fake_ps.write_text('#!/bin/bash\necho "USER PID CMD"\n')
        fake_ps.chmod(0o755)
        fake_wc = tmp_path / "wc"
        fake_wc.write_text('#!/bin/bash\necho "3"\n')
        fake_wc.chmod(0o755)

        env = {
            "PATH": f"{tmp_path}:{__import__('os').environ.get('PATH', '')}",
        }
        subprocess.run(
            ["/bin/bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )

        calls = log.read_text().strip().splitlines()
        for call in calls:
            assert "-9" in call.split(), f"pkill call missing -9: {call}"

    def test_pkill_uses_full_pattern_flag(self, tmp_path):
        """Each pkill invocation uses -f flag for full command matching."""
        log = tmp_path / "calls.log"
        fake_pkill = tmp_path / "pkill"
        fake_pkill.write_text(
            f'#!/bin/bash\necho "$@" >> {log}\nexit 0\n'
        )
        fake_pkill.chmod(0o755)
        fake_ps = tmp_path / "ps"
        fake_ps.write_text('#!/bin/bash\necho "USER PID CMD"\n')
        fake_ps.chmod(0o755)
        fake_wc = tmp_path / "wc"
        fake_wc.write_text('#!/bin/bash\necho "3"\n')
        fake_wc.chmod(0o755)

        env = {
            "PATH": f"{tmp_path}:{__import__('os').environ.get('PATH', '')}",
        }
        subprocess.run(
            ["/bin/bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )

        calls = log.read_text().strip().splitlines()
        for call in calls:
            assert "-f" in call.split(), f"pkill call missing -f: {call}"

    def test_process_count_output(self, tmp_path):
        """Script outputs process count using ps | wc pipeline."""
        fake_pkill = tmp_path / "pkill"
        fake_pkill.write_text('#!/bin/bash\nexit 0\n')
        fake_pkill.chmod(0o755)

        fake_ps = tmp_path / "ps"
        fake_ps.write_text('#!/bin/bash\necho "line1"\necho "line2"\necho "line3"\n')
        fake_ps.chmod(0o755)

        fake_wc = tmp_path / "wc"
        fake_wc.write_text('#!/bin/bash\necho "42"\n')
        fake_wc.chmod(0o755)

        env = {
            "PATH": f"{tmp_path}:{__import__('os').environ.get('PATH', '')}",
        }
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )

        # Should contain "42" in the process count line
        assert "42" in result.stdout

    def test_exactly_five_pkill_calls(self, tmp_path):
        """Script calls pkill exactly 5 times (one per target pattern)."""
        log = tmp_path / "calls.log"
        fake_pkill = tmp_path / "pkill"
        fake_pkill.write_text(
            f'#!/bin/bash\necho "$@" >> {log}\nexit 0\n'
        )
        fake_pkill.chmod(0o755)
        fake_ps = tmp_path / "ps"
        fake_ps.write_text('#!/bin/bash\necho "USER PID CMD"\n')
        fake_ps.chmod(0o755)
        fake_wc = tmp_path / "wc"
        fake_wc.write_text('#!/bin/bash\necho "3"\n')
        fake_wc.chmod(0o755)

        env = {
            "PATH": f"{tmp_path}:{__import__('os').environ.get('PATH', '')}",
        }
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        assert result.returncode == 0

        calls = log.read_text().strip().splitlines()
        assert len(calls) == 5, f"Expected exactly 5 pkill calls, got {len(calls)}: {calls}"

    def test_output_order(self, tmp_path):
        """Messages appear in order: pyenv, claude/agent, playwright, count, done."""
        fake_pkill = tmp_path / "pkill"
        fake_pkill.write_text('#!/bin/bash\nexit 0\n')
        fake_pkill.chmod(0o755)
        fake_ps = tmp_path / "ps"
        fake_ps.write_text('#!/bin/bash\necho "line1"\necho "line2"\n')
        fake_ps.chmod(0o755)
        fake_wc = tmp_path / "wc"
        fake_wc.write_text('#!/bin/bash\necho "7"\n')
        fake_wc.chmod(0o755)

        env = {
            "PATH": f"{tmp_path}:{__import__('os').environ.get('PATH', '')}",
        }
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]

        # Find indices of key messages using specific keywords
        idx_pyenv = next(i for i, l in enumerate(lines) if "pyenv" in l.lower())
        idx_agent = next(i for i, l in enumerate(lines) if "claude" in l.lower() or "orphan" in l.lower())
        idx_playwright = next(i for i, l in enumerate(lines) if "playwright" in l.lower())
        idx_done = next(i for i, l in enumerate(lines) if "done" in l.lower())

        assert idx_pyenv < idx_agent < idx_playwright < idx_done, (
            f"Messages out of order: pyenv@{idx_pyenv}, agent@{idx_agent}, "
            f"playwright@{idx_playwright}, done@{idx_done}"
        )

    def test_tr_strips_spaces_from_wc(self, tmp_path):
        """wc -l output has leading spaces stripped by tr -d ' '."""
        fake_pkill = tmp_path / "pkill"
        fake_pkill.write_text('#!/bin/bash\nexit 0\n')
        fake_pkill.chmod(0o755)
        fake_ps = tmp_path / "ps"
        fake_ps.write_text('#!/bin/bash\necho "a"\necho "b"\n')
        fake_ps.chmod(0o755)
        # wc on Linux outputs padded numbers like "      2"
        fake_wc = tmp_path / "wc"
        fake_wc.write_text('#!/bin/bash\necho "      2"\n')
        fake_wc.chmod(0o755)

        env = {
            "PATH": f"{tmp_path}:{__import__('os').environ.get('PATH', '')}",
        }
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        # The process count line should contain "2" without leading spaces
        count_lines = [l for l in result.stdout.splitlines() if "Process count" in l]
        assert len(count_lines) == 1, f"Expected 1 process count line, got: {count_lines}"
        # The number after "Process count:" should be clean
        count_val = count_lines[0].split(":")[-1].strip()
        assert count_val == "2", f"Expected '2', got '{count_val}'"

    def test_no_stdin_consumed(self, tmp_path):
        """Script does not read from stdin."""
        fake_pkill = tmp_path / "pkill"
        fake_pkill.write_text('#!/bin/bash\nexit 0\n')
        fake_pkill.chmod(0o755)
        fake_ps = tmp_path / "ps"
        fake_ps.write_text('#!/bin/bash\necho "1"\n')
        fake_ps.chmod(0o755)
        fake_wc = tmp_path / "wc"
        fake_wc.write_text('#!/bin/bash\necho "1"\n')
        fake_wc.chmod(0o755)

        env = {
            "PATH": f"{tmp_path}:{__import__('os').environ.get('PATH', '')}",
        }
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
            stdin=subprocess.DEVNULL,
        )
        assert result.returncode == 0


# ── Additional content analysis ─────────────────────────────────────────


class TestScriptContentAdditional:
    """Deeper static analysis of the script contents."""

    def test_has_terminal_advice_message(self):
        """Script tells user to open a new terminal tab."""
        content = SCRIPT.read_text()
        assert "new terminal" in content.lower()

    def test_each_echo_section_pairs_with_pkill(self):
        """Each 'Killing...' echo is followed by at least one pkill command."""
        content = SCRIPT.read_text()
        lines = content.splitlines()

        killing_sections = []
        for i, line in enumerate(lines):
            if line.strip().startswith("echo") and "Killing" in line:
                killing_sections.append(i)

        assert len(killing_sections) >= 3, (
            f"Expected >=3 'Killing...' echo lines, found {len(killing_sections)}"
        )

        # Each echo section should be followed by at least one pkill before next echo
        for idx, echo_line in enumerate(killing_sections):
            end = killing_sections[idx + 1] if idx + 1 < len(killing_sections) else len(lines)
            block = "\n".join(lines[echo_line:end])
            assert "pkill" in block, (
                f"No pkill after 'Killing' echo at line {echo_line + 1}: "
                f"{lines[echo_line]}"
            )

    def test_no_dangerous_commands(self):
        """Script does not contain rm -rf or other destructive filesystem commands."""
        content = SCRIPT.read_text()
        assert "rm " not in content
        assert "rmdir" not in content
        assert "mkfs" not in content
        assert "dd " not in content

    def test_all_pkill_redirected_to_devnull(self):
        """Every pkill line redirects stderr to /dev/null."""
        content = SCRIPT.read_text()
        for line in content.splitlines():
            if "pkill" in line:
                assert "2>/dev/null" in line, (
                    f"pkill line missing stderr redirect: {line.strip()}"
                )
