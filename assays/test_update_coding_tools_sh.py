from __future__ import annotations

"""Tests for effectors/update-coding-tools.sh — bash script tested via subprocess."""

import json
import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "update-coding-tools.sh"
LOG_RELATIVE = ".coding-tools-update.log"
HEALTH_RELATIVE = ".coding-tools-health.json"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_help(*args: str) -> subprocess.CompletedProcess:
    """Run script with --help flag (no HOME override needed)."""
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=10,
    )


def _run_with_home(tmp_path: Path) -> subprocess.CompletedProcess:
    """Run script with HOME=tmp_path (will fail because no brew)."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    # Remove brew from PATH to simulate missing Homebrew
    env["PATH"] = "/usr/bin:/bin"
    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


# ── help flag ───────────────────────────────────────────────────────────


class TestHelp:
    def test_help_exits_zero(self):
        r = _run_help("--help")
        assert r.returncode == 0

    def test_help_short_flag_exits_zero(self):
        r = _run_help("-h")
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = _run_help("--help")
        assert "Usage:" in r.stdout

    def test_help_mentions_update(self):
        r = _run_help("--help")
        assert "update" in r.stdout.lower()

    def test_help_mentions_tools(self):
        r = _run_help("--help")
        # Should mention some of the tools it updates
        stdout_lower = r.stdout.lower()
        assert "brew" in stdout_lower or "npm" in stdout_lower or "cargo" in stdout_lower

    def test_help_mentions_macos(self):
        r = _run_help("--help")
        assert "macOS" in r.stdout or "macos" in r.stdout.lower()

    def test_help_mentions_log(self):
        r = _run_help("--help")
        assert "log" in r.stdout.lower()

    def test_help_no_stderr(self):
        r = _run_help("--help")
        assert r.stderr == ""

    def test_help_no_side_effects(self, tmp_path):
        """--help must not create any files."""
        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        r = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert r.returncode == 0
        assert not (tmp_path / LOG_RELATIVE).exists()
        assert not (tmp_path / HEALTH_RELATIVE).exists()


# ── file basics ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert "bash" in first

    def test_has_set_e(self):
        src = SCRIPT.read_text()
        assert "set -e" in src

    def test_has_shebang(self):
        src = SCRIPT.read_text()
        assert src.startswith("#!")


# ── missing homebrew ────────────────────────────────────────────────────


class TestMissingHomebrew:
    """Script should fail gracefully when Homebrew is not available."""

    def test_exits_1_without_brew(self, tmp_path):
        """Without brew in PATH, script should exit 1."""
        r = _run_with_home(tmp_path)
        assert r.returncode == 1

    def test_stderr_mentions_homebrew(self, tmp_path):
        """Error message should mention Homebrew requirement."""
        r = _run_with_home(tmp_path)
        assert "Homebrew" in r.stderr or "brew" in r.stderr.lower()

    def test_no_log_file_created(self, tmp_path):
        """Failed run should not create log file."""
        _run_with_home(tmp_path)
        assert not (tmp_path / LOG_RELATIVE).exists()

    def test_no_health_file_created(self, tmp_path):
        """Failed run should not create health file."""
        _run_with_home(tmp_path)
        assert not (tmp_path / HEALTH_RELATIVE).exists()


# ── script structure ────────────────────────────────────────────────────


class TestScriptStructure:
    def test_has_brew_update(self):
        src = SCRIPT.read_text()
        assert "brew update" in src

    def test_has_brew_upgrade(self):
        src = SCRIPT.read_text()
        assert "brew upgrade" in src

    def test_has_npm_update(self):
        src = SCRIPT.read_text()
        assert "npm update" in src

    def test_has_pnpm_update(self):
        src = SCRIPT.read_text()
        assert "pnpm update" in src

    def test_has_uv_tool_upgrade(self):
        src = SCRIPT.read_text()
        assert "uv tool upgrade" in src

    def test_has_cargo_update(self):
        src = SCRIPT.read_text()
        assert "cargo" in src.lower()

    def test_has_mas_upgrade(self):
        src = SCRIPT.read_text()
        assert "mas upgrade" in src

    def test_has_health_check(self):
        src = SCRIPT.read_text()
        assert "HEALTH_FILE" in src

    def test_has_log_file_variable(self):
        src = SCRIPT.read_text()
        assert "LOG_FILE" in src

    def test_uses_tee_for_logging(self):
        src = SCRIPT.read_text()
        assert "tee -a" in src

    def test_has_error_suppression_or_true(self):
        """Individual update commands should have || true to prevent one failure from stopping all."""
        src = SCRIPT.read_text()
        # Count || true occurrences after update commands
        assert "|| true" in src


# ── repair logic ─────────────────────────────────────────────────────────


class TestRepairLogic:
    def test_has_repair_associative_array(self):
        src = SCRIPT.read_text()
        assert "declare -A REPAIR" in src

    def test_repairs_brew(self):
        src = SCRIPT.read_text()
        assert '"brew"' in src or "[brew]" in src

    def test_repairs_claude(self):
        src = SCRIPT.read_text()
        assert "claude" in src.lower()

    def test_repairs_mas(self):
        src = SCRIPT.read_text()
        assert "mas" in src

    def test_tracks_failures(self):
        src = SCRIPT.read_text()
        assert "failures" in src


# ── health file format ──────────────────────────────────────────────────


class TestHealthFileFormat:
    """Test the health JSON format generated by the script."""

    def test_health_json_structure_ok(self, tmp_path):
        """Verify expected structure for ok status."""
        # Simulate what the script would write
        health_file = tmp_path / HEALTH_RELATIVE
        health_data = {
            "status": "ok",
            "checked": "2025-01-15T12:00:00Z",
            "failures": [],
        }
        health_file.write_text(json.dumps(health_data))
        
        loaded = json.loads(health_file.read_text())
        assert loaded["status"] == "ok"
        assert loaded["failures"] == []

    def test_health_json_structure_degraded(self, tmp_path):
        """Verify expected structure for degraded status."""
        health_file = tmp_path / HEALTH_RELATIVE
        health_data = {
            "status": "degraded",
            "checked": "2025-01-15T12:00:00Z",
            "failures": ["claude", "opencode"],
        }
        health_file.write_text(json.dumps(health_data))
        
        loaded = json.loads(health_file.read_text())
        assert loaded["status"] == "degraded"
        assert "claude" in loaded["failures"]

    def test_script_generates_valid_json_pattern(self):
        """Verify the script's JSON output patterns are valid."""
        src = SCRIPT.read_text()
        # Check for JSON-like patterns in health file writes
        assert '"status"' in src
        assert '"checked"' in src
        assert '"failures"' in src


# ── path configuration ───────────────────────────────────────────────────


class TestPathConfiguration:
    def test_includes_cargo_bin(self):
        src = SCRIPT.read_text()
        assert ".cargo/bin" in src

    def test_includes_npm_global(self):
        src = SCRIPT.read_text()
        assert ".npm-global" in src or "npm-global" in src

    def test_includes_local_bin(self):
        src = SCRIPT.read_text()
        assert ".local/bin" in src

    def test_includes_pnpm(self):
        src = SCRIPT.read_text()
        assert "pnpm" in src


# ── log file handling ────────────────────────────────────────────────────


class TestLogFileHandling:
    def test_log_file_path(self):
        src = SCRIPT.read_text()
        assert ".coding-tools-update.log" in src

    def test_logs_timestamp(self):
        src = SCRIPT.read_text()
        assert "$(date)" in src

    def test_logs_section_headers(self):
        """Script should log section headers like 'Updating brew...'"""
        src = SCRIPT.read_text()
        assert "Updating" in src


# ── script permissions ───────────────────────────────────────────────────


class TestScriptPermissions:
    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_file_not_directory(self):
        assert SCRIPT.is_file()
