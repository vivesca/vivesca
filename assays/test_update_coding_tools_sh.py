from __future__ import annotations

"""Tests for effectors/update-coding-tools.sh — bash script tested via subprocess.

The script auto-updates coding tools (brew, npm, pnpm, uv, cargo, mas) and runs
a post-update self-heal check. Tests use PATH overrides with mock binaries so
no real package manager is invoked.
"""

import json
import os
import re
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "update-coding-tools.sh"


def _read_script() -> str:
    return SCRIPT.read_text()


# ── helpers ─────────────────────────────────────────────────────────────


def _make_mock_bin(
    tmp_path: Path, name: str, stdout: str = "", exit_code: int = 0,
) -> Path:
    """Create a mock executable script in tmp_path/bin/<name>."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(f"#!/bin/bash\necho {stdout}\nexit {exit_code}\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bindir


def _make_recording_bin(
    tmp_path: Path, name: str, record_file: Path, exit_code: int = 0,
) -> Path:
    """Create a mock bin that records all args to record_file."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(
        "#!/bin/bash\n"
        f'echo "$@" >> {record_file}\n'
        f"exit {exit_code}\n",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bindir


def _make_all_mocks(tmp_path: Path, exit_code: int = 0) -> Path:
    """Create mock binaries for every command the script calls.

    Returns the bin directory to prepend to PATH.
    """
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)

    # All commands the script calls or that command -v checks
    commands = [
        # Package managers
        "brew",
        # npm / pnpm / uv / cargo / mas
        "npm", "pnpm", "uv", "cargo", "mas",
        # REPAIR associative array keys checked via command -v
        "claude", "opencode", "gemini", "codex", "agent-browser",
        # date — mock for deterministic output
        "date",
    ]
    for cmd in commands:
        script = bindir / cmd
        script.write_text(f"#!/bin/bash\nexit {exit_code}\n")
        script.chmod(script.stat().st_mode | stat.S_IEXEC)

    # brew must pretend shellenv works
    (bindir / "brew").write_text(
        '#!/bin/bash\nif [ "$1" = "shellenv" ]; then exit 0; fi\nexit 0\n',
    )
    (bindir / "brew").chmod(0o755)

    # date: output a fixed timestamp
    (bindir / "date").write_text(
        '#!/bin/bash\necho "2026-04-01T12:00:00Z"\n',
    )
    (bindir / "date").chmod(0o755)

    return bindir


def _essential_system_dir(tmp_path: Path) -> Path:
    """Create a dir with symlinks to only essential system tools.

    Prevents system-installed tools like codex/gemini from leaking into
    tests that expect them to be absent.
    """
    sysdir = tmp_path / "_sys"
    sysdir.mkdir(exist_ok=True)
    for cmd in ("bash", "cat", "chmod", "date", "mkdir", "sed", "tee", "touch", "tr"):
        src = Path(f"/usr/bin/{cmd}")
        if src.exists() and not (sysdir / cmd).exists():
            (sysdir / cmd).symlink_to(src)
    return sysdir


def _run_script(
    tmp_path: Path,
    extra_env: dict | None = None,
    bindir: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run the full script with all commands mocked.

    Mock bindir is prepended to PATH so mocked commands take priority,
    but system commands like bash, cat, tee are still found via
    symlinks in a restricted system dir (no codex/gemini leak-through).
    """
    if bindir is None:
        bindir = _make_all_mocks(tmp_path)
    sysdir = _essential_system_dir(tmp_path)
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    # bindir (mocks) > restricted system dir (essentials only) —
    # avoids /usr/bin/codex etc. leaking into repair tests.
    env["PATH"] = str(bindir) + os.pathsep + str(sysdir)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True, text=True, env=env, timeout=30,
    )


def _log_file(tmp_path: Path) -> Path:
    return tmp_path / ".coding-tools-update.log"


def _health_file(tmp_path: Path) -> Path:
    return tmp_path / ".coding-tools-health.json"


# ── Structural tests ────────────────────────────────────────────────────


class TestScriptStructure:
    """Verify the script has required structural elements."""

    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_executable(self):
        mode = SCRIPT.stat().st_mode
        assert mode & stat.S_IEXEC, "update-coding-tools.sh should be executable"

    def test_shebang(self):
        lines = _read_script().splitlines()
        assert lines[0] == "#!/usr/bin/env bash"

    def test_strict_mode(self):
        content = _read_script()
        assert "set -e" in content


class TestSyntaxCheck:
    """Verify the script is syntactically valid bash."""

    def test_bash_syntax_valid(self):
        r = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            capture_output=True, text=True, timeout=10,
        )
        assert r.returncode == 0, f"Syntax error:\n{r.stderr}"


# ── Update section presence ─────────────────────────────────────────────


class TestUpdateSections:
    """Verify all 6 update sections are present."""

    def test_has_brew_section(self):
        content = _read_script()
        assert "brew update" in content
        assert "brew upgrade" in content
        assert "brew cleanup" in content

    def test_has_npm_section(self):
        content = _read_script()
        assert "npm update -g" in content

    def test_has_pnpm_section(self):
        content = _read_script()
        assert "pnpm update -g" in content

    def test_has_uv_section(self):
        content = _read_script()
        assert "uv tool upgrade --all" in content

    def test_has_cargo_section(self):
        content = _read_script()
        assert "cargo binstall" in content
        assert "compound-perplexity" in content
        assert "typos-cli" in content

    def test_has_mas_section(self):
        content = _read_script()
        assert "mas upgrade" in content

    def test_has_cask_upgrade(self):
        content = _read_script()
        assert "brew upgrade --cask --greedy" in content

    def test_has_brew_cleanup(self):
        content = _read_script()
        assert "brew cleanup --prune=7" in content


# ── PATH setup ──────────────────────────────────────────────────────────


class TestPathSetup:
    """Verify the script sets up PATH correctly."""

    def test_includes_cargo_bin(self):
        content = _read_script()
        assert "$HOME/.cargo/bin" in content

    def test_includes_npm_global(self):
        content = _read_script()
        assert "$HOME/.npm-global/bin" in content

    def test_includes_local_bin(self):
        content = _read_script()
        assert "$HOME/.local/bin" in content

    def test_includes_pnpm(self):
        content = _read_script()
        assert "$HOME/Library/pnpm" in content


# ── Logging tests ───────────────────────────────────────────────────────


class TestLogging:
    """Test that the script creates and populates a log file."""

    def test_creates_log_file(self, tmp_path):
        _run_script(tmp_path)
        assert _log_file(tmp_path).exists()

    def test_log_has_start_marker(self, tmp_path):
        _run_script(tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "===" in log_text

    def test_log_has_update_brew_message(self, tmp_path):
        _run_script(tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Updating brew" in log_text

    def test_log_has_update_npm_message(self, tmp_path):
        _run_script(tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Updating npm globals" in log_text

    def test_log_has_update_pnpm_message(self, tmp_path):
        _run_script(tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Updating pnpm globals" in log_text

    def test_log_has_update_uv_message(self, tmp_path):
        _run_script(tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Updating uv tools" in log_text

    def test_log_has_update_cargo_message(self, tmp_path):
        _run_script(tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Updating cargo tools" in log_text

    def test_log_has_update_mas_message(self, tmp_path):
        _run_script(tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Updating Mac App Store" in log_text

    def test_log_has_completion_marker(self, tmp_path):
        _run_script(tmp_path)
        log_text = _log_file(tmp_path).read_text()
        assert "Updates complete" in log_text


# ── Health file tests ───────────────────────────────────────────────────


class TestHealthFile:
    """Test the post-update health check and JSON output."""

    def test_creates_health_file(self, tmp_path):
        _run_script(tmp_path)
        assert _health_file(tmp_path).exists()

    def test_health_file_valid_json(self, tmp_path):
        _run_script(tmp_path)
        data = json.loads(_health_file(tmp_path).read_text())
        assert "status" in data
        assert "checked" in data
        assert "failures" in data

    def test_health_ok_when_all_commands_found(self, tmp_path):
        """All mocked commands exist via command -v → status ok."""
        _run_script(tmp_path)
        data = json.loads(_health_file(tmp_path).read_text())
        assert data["status"] == "ok"
        assert data["failures"] == []

    def test_health_degraded_when_repair_fails(self, tmp_path):
        """If a REPAIR target is missing after repair attempt → degraded."""
        bindir = _make_all_mocks(tmp_path)
        # Remove the 'mas' mock so command -v mas fails
        # brew mock can't actually install mas, so repair fails
        (bindir / "mas").unlink()
        _run_script(tmp_path, bindir=bindir)
        data = json.loads(_health_file(tmp_path).read_text())
        assert data["status"] == "degraded"
        assert "mas" in data["failures"]

    def test_health_file_has_timestamp(self, tmp_path):
        _run_script(tmp_path)
        data = json.loads(_health_file(tmp_path).read_text())
        assert re.search(r"\d{4}-\d{2}-\d{2}", data["checked"]) is not None


# ── Repair associative array ────────────────────────────────────────────


class TestRepairArray:
    """Verify the REPAIR associative array contains expected keys."""

    def test_has_brew_repair(self):
        content = _read_script()
        assert "[brew]=" in content

    def test_has_claude_repair(self):
        content = _read_script()
        assert "[claude]=" in content

    def test_has_opencode_repair(self):
        content = _read_script()
        assert "[opencode]=" in content

    def test_has_gemini_repair(self):
        content = _read_script()
        assert "[gemini]=" in content

    def test_has_codex_repair(self):
        content = _read_script()
        assert "[codex]=" in content

    def test_has_agent_browser_repair(self):
        content = _read_script()
        assert "[agent-browser]=" in content

    def test_has_mas_repair(self):
        content = _read_script()
        assert "[mas]=" in content

    def test_repair_uses_brew_install(self):
        content = _read_script()
        assert "brew install" in content


# ── Error tolerance (|| true) ──────────────────────────────────────────


class TestErrorTolerance:
    """Verify update commands use || true so failures don't abort."""

    def test_brew_update_has_or_true(self):
        content = _read_script()
        # Find the line with "brew update" and check it has || true
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("brew update") and "shellenv" not in stripped:
                assert "|| true" in stripped, f"brew update missing || true: {stripped}"
                break

    def test_brew_upgrade_has_or_true(self):
        content = _read_script()
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("brew upgrade") and "|| true" not in stripped:
                pass  # Could be the one with || true on same line
            if stripped.startswith("brew upgrade") and "|| true" in stripped:
                return
        # Also check two-line pattern
        assert "|| true" in content, "brew upgrade should have || true"

    def test_npm_update_has_or_true(self):
        content = _read_script()
        for line in content.splitlines():
            if "npm update -g" in line:
                assert "|| true" in line
                break

    def test_cargo_binstall_has_or_true(self):
        content = _read_script()
        for line in content.splitlines():
            if "cargo binstall" in line:
                assert "|| true" in line
                break

    def test_mas_upgrade_has_or_true(self):
        content = _read_script()
        for line in content.splitlines():
            if "mas upgrade" in line:
                assert "|| true" in line
                break


# ── Script output verification ─────────────────────────────────────────


class TestScriptOutput:
    """Verify the script's echo messages for each section."""

    def test_verifying_critical_tools_message(self):
        content = _read_script()
        assert "Verifying critical tools" in content

    def test_repair_message(self):
        content = _read_script()
        assert "Repairing" in content

    def test_health_ok_message(self):
        content = _read_script()
        assert "Health: ok" in content

    def test_health_degraded_message(self):
        content = _read_script()
        assert "Health: DEGRADED" in content


# ── Log file location ───────────────────────────────────────────────────


class TestLogFileLocation:
    """Test that the log file uses $HOME."""

    def test_log_uses_home_env(self, tmp_path):
        """Log file is written to $HOME/.coding-tools-update.log."""
        _run_script(tmp_path)
        log = tmp_path / ".coding-tools-update.log"
        assert log.exists()

    def test_script_exits_0_on_success(self, tmp_path):
        r = _run_script(tmp_path)
        assert r.returncode == 0


# ── Recording-mock tests (verify actual invocations) ────────────────────


class TestCommandInvocations:
    """Verify each update section calls the correct command with correct args."""

    def _make_recording_env(self, tmp_path, record_cmd):
        """Create mocks where record_cmd records its invocations, others are silent."""
        bindir = tmp_path / "bin"
        bindir.mkdir(exist_ok=True)
        record_file = tmp_path / "calls.log"

        # The command under test records to file
        _make_recording_bin(tmp_path, record_cmd, record_file)

        # All other commands are silent no-ops
        all_cmds = [
            "brew", "npm", "pnpm", "uv", "cargo", "mas",
            "claude", "opencode", "gemini", "codex", "agent-browser",
        ]
        for cmd in all_cmds:
            if cmd != record_cmd:
                _make_mock_bin(tmp_path, cmd)

        return bindir, record_file

    def test_brew_update_called(self, tmp_path):
        bindir, record = self._make_recording_env(tmp_path, "brew")
        _run_script(tmp_path, bindir=bindir)
        calls = record.read_text()
        assert "update" in calls

    def test_brew_upgrade_called(self, tmp_path):
        bindir, record = self._make_recording_env(tmp_path, "brew")
        _run_script(tmp_path, bindir=bindir)
        calls = record.read_text()
        assert "upgrade" in calls

    def test_brew_cleanup_called(self, tmp_path):
        bindir, record = self._make_recording_env(tmp_path, "brew")
        _run_script(tmp_path, bindir=bindir)
        calls = record.read_text()
        assert "cleanup" in calls

    def test_brew_cask_greedy_upgrade_called(self, tmp_path):
        bindir, record = self._make_recording_env(tmp_path, "brew")
        _run_script(tmp_path, bindir=bindir)
        calls = record.read_text()
        assert "--cask" in calls
        assert "--greedy" in calls

    def test_npm_update_global_called(self, tmp_path):
        bindir, record = self._make_recording_env(tmp_path, "npm")
        _run_script(tmp_path, bindir=bindir)
        calls = record.read_text()
        assert "update -g" in calls

    def test_pnpm_update_global_called(self, tmp_path):
        bindir, record = self._make_recording_env(tmp_path, "pnpm")
        _run_script(tmp_path, bindir=bindir)
        calls = record.read_text()
        assert "update -g" in calls

    def test_uv_tool_upgrade_all_called(self, tmp_path):
        bindir, record = self._make_recording_env(tmp_path, "uv")
        _run_script(tmp_path, bindir=bindir)
        calls = record.read_text()
        assert "tool upgrade --all" in calls

    def test_cargo_binstall_called_with_packages(self, tmp_path):
        bindir, record = self._make_recording_env(tmp_path, "cargo")
        _run_script(tmp_path, bindir=bindir)
        calls = record.read_text()
        assert "binstall" in calls
        assert "compound-perplexity" in calls
        assert "typos-cli" in calls

    def test_cargo_binstall_uses_y_flag(self, tmp_path):
        bindir, record = self._make_recording_env(tmp_path, "cargo")
        _run_script(tmp_path, bindir=bindir)
        calls = record.read_text()
        assert "-y" in calls

    def test_mas_upgrade_called(self, tmp_path):
        bindir, record = self._make_recording_env(tmp_path, "mas")
        _run_script(tmp_path, bindir=bindir)
        calls = record.read_text()
        assert "upgrade" in calls


# ── Resilience tests (script survives individual failures) ──────────────


class TestResilience:
    """Verify the script continues when individual update commands fail."""

    def test_continues_after_brew_failure(self, tmp_path):
        bindir = _make_all_mocks(tmp_path, exit_code=0)
        # Make only brew fail
        (bindir / "brew").write_text("#!/bin/bash\nexit 1\n")
        (bindir / "brew").chmod(0o755)
        r = _run_script(tmp_path, bindir=bindir)
        assert r.returncode == 0

    def test_continues_after_npm_failure(self, tmp_path):
        bindir = _make_all_mocks(tmp_path, exit_code=0)
        (bindir / "npm").write_text("#!/bin/bash\nexit 1\n")
        (bindir / "npm").chmod(0o755)
        r = _run_script(tmp_path, bindir=bindir)
        assert r.returncode == 0

    def test_continues_after_cargo_failure(self, tmp_path):
        bindir = _make_all_mocks(tmp_path, exit_code=0)
        (bindir / "cargo").write_text("#!/bin/bash\nexit 1\n")
        (bindir / "cargo").chmod(0o755)
        r = _run_script(tmp_path, bindir=bindir)
        assert r.returncode == 0

    def test_continues_after_all_update_commands_fail(self, tmp_path):
        """Script still reaches health check even when every updater fails."""
        bindir = _make_all_mocks(tmp_path, exit_code=1)
        r = _run_script(tmp_path, bindir=bindir)
        # Health check tools still exist, so script should succeed
        assert r.returncode == 0
        # Health file should exist (ok because health tools still present)
        assert _health_file(tmp_path).exists()

    def test_log_records_all_sections_despite_failures(self, tmp_path):
        """Log mentions all section headers even when commands fail."""
        bindir = _make_all_mocks(tmp_path, exit_code=1)
        _run_script(tmp_path, bindir=bindir)
        log_text = _log_file(tmp_path).read_text()
        assert "Updating brew" in log_text
        assert "Updating npm globals" in log_text
        assert "Updating pnpm globals" in log_text
        assert "Updating uv tools" in log_text
        assert "Updating cargo tools" in log_text
        assert "Updating Mac App Store" in log_text


# ── Health repair path tests ────────────────────────────────────────────


class TestHealthRepair:
    """Verify health check repair logic with missing / restored tools."""

    def test_repair_attempted_for_missing_tool(self, tmp_path):
        """When a tool is missing, repair command is invoked."""
        bindir = _make_all_mocks(tmp_path)
        # Remove opencode so command -v fails
        (bindir / "opencode").unlink()
        # Record what brew gets called with (repair uses brew install)
        record = tmp_path / "brew_calls.log"
        (bindir / "brew").write_text(
            "#!/bin/bash\n"
            f'echo "$@" >> {record}\n'
            "exit 0\n",
        )
        (bindir / "brew").chmod(0o755)
        _run_script(tmp_path, bindir=bindir)
        calls = record.read_text()
        assert "install opencode" in calls

    def test_multiple_missing_tools_all_reported(self, tmp_path):
        """Multiple missing tools all appear in health failures."""
        bindir = _make_all_mocks(tmp_path)
        # Remove two tools
        (bindir / "mas").unlink()
        (bindir / "codex").unlink()
        _run_script(tmp_path, bindir=bindir)
        data = json.loads(_health_file(tmp_path).read_text())
        assert data["status"] == "degraded"
        assert "mas" in data["failures"]
        assert "codex" in data["failures"]
        assert len(data["failures"]) == 2

    def test_health_degraded_with_single_missing_tool(self, tmp_path):
        """Single missing tool results in degraded status with one failure."""
        bindir = _make_all_mocks(tmp_path)
        (bindir / "gemini").unlink()
        _run_script(tmp_path, bindir=bindir)
        data = json.loads(_health_file(tmp_path).read_text())
        assert data["status"] == "degraded"
        assert data["failures"] == ["gemini"]

    def test_health_ok_after_successful_repair(self, tmp_path):
        """If brew install creates the missing binary, health is ok."""
        bindir = _make_all_mocks(tmp_path)
        # Remove claude, but make brew install recreate it
        (bindir / "claude").unlink()
        brew_repair = bindir / "brew"
        brew_repair.write_text(
            "#!/bin/bash\n"
            f'if [[ "$*" == *claude* ]]; then touch {bindir / "claude"} && chmod +x {bindir / "claude"}; fi\n'
            "exit 0\n",
        )
        brew_repair.chmod(0o755)
        _run_script(tmp_path, bindir=bindir)
        data = json.loads(_health_file(tmp_path).read_text())
        assert data["status"] == "ok"

    def test_log_shows_repair_attempt(self, tmp_path):
        """Log contains 'Repairing <cmd>' when a tool is missing."""
        bindir = _make_all_mocks(tmp_path)
        (bindir / "codex").unlink()
        _run_script(tmp_path, bindir=bindir)
        log_text = _log_file(tmp_path).read_text()
        assert "Repairing codex" in log_text

    def test_log_shows_degraded_message(self, tmp_path):
        """Log contains DEGRADED message when repair fails."""
        bindir = _make_all_mocks(tmp_path)
        (bindir / "codex").unlink()
        _run_script(tmp_path, bindir=bindir)
        log_text = _log_file(tmp_path).read_text()
        assert "DEGRADED" in log_text

    def test_log_shows_health_ok_when_all_present(self, tmp_path):
        """Log contains 'Health: ok' when all tools are found."""
        bindir = _make_all_mocks(tmp_path)
        _run_script(tmp_path, bindir=bindir)
        log_text = _log_file(tmp_path).read_text()
        assert "Health: ok" in log_text


# ── Stdout echo verification ────────────────────────────────────────────


class TestStdoutMessages:
    """Verify the script outputs section headers to stdout via tee."""

    def test_stdout_mentions_brew_update(self, tmp_path):
        r = _run_script(tmp_path)
        assert "Updating brew" in r.stdout

    def test_stdout_mentions_npm_update(self, tmp_path):
        r = _run_script(tmp_path)
        assert "Updating npm globals" in r.stdout

    def test_stdout_mentions_cargo_update(self, tmp_path):
        r = _run_script(tmp_path)
        assert "Updating cargo tools" in r.stdout

    def test_stdout_mentions_updates_complete(self, tmp_path):
        r = _run_script(tmp_path)
        assert "Updates complete" in r.stdout
