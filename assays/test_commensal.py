from __future__ import annotations

"""Tests for effectors/commensal — route coding tasks to free models.

Commensal is a script — loaded via exec(), never imported.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

COMMENSAL_PATH = Path(__file__).resolve().parents[1] / "effectors" / "commensal"
GERMLINE_ROOT = Path(__file__).resolve().parents[1]


# ── Fixture ────────────────────────────────────────────────────────────────


@pytest.fixture()
def cm(tmp_path):
    """Load commensal via exec, redirecting paths to tmp_path."""
    ns: dict = {
        "__name__": "test_commensal",
        "__file__": str(COMMENSAL_PATH),
    }
    source = COMMENSAL_PATH.read_text(encoding="utf-8")
    exec(source, ns)

    # Redirect HOME to tmp_path for output file tests
    ns["HOME"] = tmp_path
    return ns


# ── File basics ────────────────────────────────────────────────────────────


class TestBasics:
    def test_file_exists(self):
        assert COMMENSAL_PATH.exists()

    def test_shebang(self):
        first = COMMENSAL_PATH.read_text().split("\n")[0]
        assert first.startswith("#!/usr/bin/env python")

    def test_has_docstring(self):
        content = COMMENSAL_PATH.read_text()
        assert '"""' in content
        assert "route" in content.lower() or "delegate" in content.lower()


# ── Constants ──────────────────────────────────────────────────────────────


class TestConstants:
    def test_backends_defined(self, cm):
        assert "BACKENDS" in cm
        assert "opencode" in cm["BACKENDS"]
        assert "gemini" in cm["BACKENDS"]
        assert "codex" in cm["BACKENDS"]

    def test_pty_backends_subset(self, cm):
        assert "PTY_BACKENDS" in cm
        for backend in cm["PTY_BACKENDS"]:
            assert backend in cm["BACKENDS"]

    def test_timeout_floor_defined(self, cm):
        assert "TIMEOUT_FLOOR" in cm
        assert cm["TIMEOUT_FLOOR"]["opencode"] >= 60
        assert cm["TIMEOUT_FLOOR"]["gemini"] >= 60
        assert cm["TIMEOUT_FLOOR"]["codex"] >= 60

    def test_regex_patterns_compiled(self, cm):
        assert "_ANSI_RE" in cm
        assert "_CTRL_RE" in cm
        assert "_TUI_RE" in cm
        # Should be compiled patterns
        assert hasattr(cm["_ANSI_RE"], "search")
        assert hasattr(cm["_CTRL_RE"], "search")
        assert hasattr(cm["_TUI_RE"], "search")


# ── Regex cleaning ──────────────────────────────────────────────────────────


class TestRegexCleaning:
    def test_ansi_re_strips_codes(self, cm):
        text = "\x1b[32mgreen\x1b[0m text"
        clean = cm["_ANSI_RE"].sub("", text)
        assert "\x1b" not in clean
        assert "green" in clean

    def test_ctrl_re_strips_control(self, cm):
        text = "hello\x00world\x07test"
        clean = cm["_CTRL_RE"].sub("", text)
        assert "\x00" not in clean
        assert "\x07" not in clean

    def test_tui_re_strips_tui_chars(self, cm):
        text = "loading█▀▄done"
        clean = cm["_TUI_RE"].sub(" ", text)
        assert "█" not in clean
        assert "▀" not in clean


# ── run_direct ─────────────────────────────────────────────────────────────


class TestRunDirect:
    def test_run_direct_success(self, cm, tmp_path):
        """Test run_direct with a simple echo command."""
        output, code = cm["run_direct"](
            ["echo", "hello world"],
            str(tmp_path),
            10,
        )
        assert code == 0
        assert "hello world" in output

    def test_run_direct_failure(self, cm, tmp_path):
        """Test run_direct with a failing command."""
        output, code = cm["run_direct"](
            ["false"],
            str(tmp_path),
            10,
        )
        assert code != 0

    def test_run_direct_timeout(self, cm, tmp_path):
        """Test run_direct times out on long-running command."""
        with pytest.raises(subprocess.TimeoutExpired):
            cm["run_direct"](
                ["sleep", "10"],
                str(tmp_path),
                1,
            )

    def test_run_direct_removes_claudecode_env(self, cm, tmp_path):
        """Test that CLAUDECODE env var is removed."""
        # This test verifies the env filtering logic
        with patch.dict(os.environ, {"CLAUDECODE": "test_value"}):
            output, code = cm["run_direct"](
                ["python3", "-c", "import os; print('CLAUDECODE' in os.environ)"],
                str(tmp_path),
                10,
            )
            assert "False" in output


# ── run_pty ────────────────────────────────────────────────────────────────


class TestRunPty:
    def test_run_pty_success(self, cm, tmp_path):
        """Test run_pty with a simple command."""
        output, code = cm["run_pty"](
            ["echo", "pty test"],
            str(tmp_path),
            10,
        )
        assert code == 0
        assert "pty test" in output

    def test_run_pty_failure(self, cm, tmp_path):
        """Test run_pty with a failing command."""
        output, code = cm["run_pty"](
            ["false"],
            str(tmp_path),
            10,
        )
        assert code != 0

    def test_run_pty_strips_ansi(self, cm, tmp_path):
        """Test that run_pty strips ANSI codes."""
        # Python can output ANSI codes
        output, code = cm["run_pty"](
            ["python3", "-c", "print('\\x1b[32mgreen\\x1b[0m')"],
            str(tmp_path),
            10,
        )
        assert code == 0
        # ANSI codes should be stripped
        assert "\x1b[" not in output
        assert "green" in output

    def test_run_pty_timeout(self, cm, tmp_path):
        """Test run_pty kills process on timeout."""
        start = time.time()
        output, code = cm["run_pty"](
            ["sleep", "30"],
            str(tmp_path),
            2,
        )
        elapsed = time.time() - start
        # Should complete within ~3 seconds (timeout + cleanup)
        assert elapsed < 5
        assert code != 0  # Process was killed


# ── CLI subprocess tests ───────────────────────────────────────────────────


class TestCLI:
    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, str(COMMENSAL_PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "backend" in result.stdout.lower() or "task" in result.stdout.lower()

    def test_missing_task_arg(self):
        result = subprocess.run(
            [sys.executable, str(COMMENSAL_PATH)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Should fail with error about missing task argument
        assert result.returncode != 0

    def test_invalid_backend(self):
        result = subprocess.run(
            [sys.executable, str(COMMENSAL_PATH), "-b", "invalid_backend", "test task"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Should fail with invalid choice
        assert result.returncode != 0
        assert "invalid choice" in result.stderr.lower() or "error" in result.stderr.lower()
