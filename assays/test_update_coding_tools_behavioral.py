from __future__ import annotations

"""Behavioral tests for effectors/update-coding-tools.sh.

Runs the script via subprocess with mocked PATH (fake brew, npm, etc.)
to verify runtime behavior: repair loop, health JSON, log output, error resilience.
"""

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "update-coding-tools.sh"
LOG_NAME = ".coding-tools-update.log"
HEALTH_NAME = ".coding-tools-health.json"


# ── helpers ─────────────────────────────────────────────────────────────


def _create_fake_bin(tmp_path: Path, name: str, body: str) -> Path:
    """Create an executable fake binary in tmp_path/bin/."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(f"#!/bin/bash\n{body}\n")
    script.chmod(script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return script


def _env_with_fake_path(tmp_path: Path) -> dict[str, str]:
    """Build env dict with HOME=tmp_path and PATH=fake bin + /usr/bin for system tools."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    # Fake bin first (so mocked brew/npm/etc are found), then /usr/bin for
    # bash, tee, date, sed, and any other system utilities the script needs.
    env["PATH"] = str(tmp_path / "bin") + ":" + "/usr/bin"
    # Strip any brew-related vars so the fake brew is the only one found
    for key in list(env):
        if "HOMEBREW" in key.upper():
            del env[key]
    return env


def _run_script(tmp_path: Path, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run the real script with HOME and PATH overridden to use fakes."""
    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env=_env_with_fake_path(tmp_path),
        timeout=timeout,
    )


# ── fixture: minimal fake command set ──────────────────────────────────


@pytest.fixture()
def fake_tools(tmp_path: Path) -> Path:
    """Set up fake brew + all other commands the script invokes."""
    # Fake brew: must handle "shellenv", "update", "upgrade", "cleanup", "install"
    _create_fake_bin(tmp_path, "brew", """\
case "$1" in
    shellenv) echo 'export PATH="/opt/homebrew/bin:$PATH"' ;;
    update|upgrade|cleanup|install) echo "brew $*: ok" ;;
    *) echo "brew $*: ok" ;;
esac
""")
    # Fake npm, pnpm, uv, cargo, mas — just succeed
    for cmd in ("npm", "pnpm", "uv", "cargo", "mas"):
        _create_fake_bin(tmp_path, cmd, f'echo "{cmd} $*: ok"')
    # Fake all commands checked in repair loop
    for cmd in ("claude", "opencode", "gemini", "codex", "agent-browser"):
        _create_fake_bin(tmp_path, cmd, f'echo "{cmd} ok"')
    return tmp_path


# ── 1. Happy path: all tools present ──────────────────────────────────


class TestHappyPath:
    def test_exits_zero(self, fake_tools: Path):
        r = _run_script(fake_tools)
        assert r.returncode == 0, f"stderr: {r.stderr}"

    def test_creates_log_file(self, fake_tools: Path):
        _run_script(fake_tools)
        log = fake_tools / LOG_NAME
        assert log.exists(), "Log file should be created"

    def test_creates_health_file(self, fake_tools: Path):
        _run_script(fake_tools)
        health = fake_tools / HEALTH_NAME
        assert health.exists(), "Health file should be created"

    def test_health_file_is_valid_json(self, fake_tools: Path):
        _run_script(fake_tools)
        health = fake_tools / HEALTH_NAME
        data = json.loads(health.read_text())
        assert "status" in data
        assert "checked" in data
        assert "failures" in data

    def test_health_file_status_ok_when_all_present(self, fake_tools: Path):
        _run_script(fake_tools)
        health = fake_tools / HEALTH_NAME
        data = json.loads(health.read_text())
        assert data["status"] == "ok"
        assert data["failures"] == []

    def test_log_contains_timestamp(self, fake_tools: Path):
        _run_script(fake_tools)
        log = (fake_tools / LOG_NAME).read_text()
        assert "===" in log  # === $(date) === markers

    def test_log_contains_updating_sections(self, fake_tools: Path):
        _run_script(fake_tools)
        log = (fake_tools / LOG_NAME).read_text()
        for section in ["Updating brew", "Updating npm", "Updating pnpm",
                        "Updating uv", "Updating cargo", "Updating Mac App Store"]:
            assert section in log, f"Missing section: {section}"

    def test_log_contains_completion_marker(self, fake_tools: Path):
        _run_script(fake_tools)
        log = (fake_tools / LOG_NAME).read_text()
        assert "Updates complete" in log

    def test_log_contains_verifying_section(self, fake_tools: Path):
        _run_script(fake_tools)
        log = (fake_tools / LOG_NAME).read_text()
        assert "Verifying critical tools" in log

    def test_health_checked_is_iso_format(self, fake_tools: Path):
        _run_script(fake_tools)
        data = json.loads((fake_tools / HEALTH_NAME).read_text())
        # Should be like 2025-01-15T12:00:00Z
        checked = data["checked"]
        assert checked.endswith("Z")
        assert "T" in checked


# ── 2. Repair loop: missing tools → degraded ──────────────────────────


class TestRepairLoopDegraded:
    """Remove some tools so the repair loop can't find them → degraded health."""

    def _setup_with_missing(self, tmp_path: Path, missing: list[str]) -> Path:
        """Create fake env where named tools are absent."""
        _create_fake_bin(tmp_path, "brew", """\
case "$1" in
    shellenv) echo 'export PATH="/opt/homebrew/bin:$PATH"' ;;
    *) echo "brew $*: ok" ;;
esac
""")
        for cmd in ("npm", "pnpm", "uv", "cargo", "mas"):
            _create_fake_bin(tmp_path, cmd, f'echo "{cmd} ok"')
        # Only provide tools NOT in the missing list
        for cmd in ("claude", "opencode", "gemini", "codex", "agent-browser"):
            if cmd not in missing:
                _create_fake_bin(tmp_path, cmd, f'echo "{cmd} ok"')
        return tmp_path

    def test_missing_claude_produces_degraded(self, tmp_path: Path):
        self._setup_with_missing(tmp_path, ["claude"])
        r = _run_script(tmp_path)
        assert r.returncode == 0
        data = json.loads((tmp_path / HEALTH_NAME).read_text())
        assert data["status"] == "degraded"
        assert "claude" in data["failures"]

    def test_missing_multiple_tools(self, tmp_path: Path):
        self._setup_with_missing(tmp_path, ["opencode", "codex"])
        r = _run_script(tmp_path)
        assert r.returncode == 0
        data = json.loads((tmp_path / HEALTH_NAME).read_text())
        assert data["status"] == "degraded"
        assert len(data["failures"]) >= 2

    def test_degraded_log_mentions_repair_attempt(self, tmp_path: Path):
        self._setup_with_missing(tmp_path, ["claude"])
        _run_script(tmp_path)
        log = (tmp_path / LOG_NAME).read_text()
        assert "Repairing" in log or "DEGRADED" in log

    def test_all_repair_tools_missing(self, tmp_path: Path):
        """If all repairable tools are missing, all should appear in failures."""
        all_repairable = ["claude", "opencode", "gemini", "codex", "agent-browser"]
        self._setup_with_missing(tmp_path, all_repairable)
        r = _run_script(tmp_path)
        assert r.returncode == 0
        data = json.loads((tmp_path / HEALTH_NAME).read_text())
        assert data["status"] == "degraded"
        assert len(data["failures"]) == len(all_repairable)


# ── 3. Error resilience: one command fails, others still run ──────────


class TestErrorResilience:
    def test_failing_npm_does_not_stop_script(self, fake_tools: Path):
        """Replace npm with a failing version; script should still complete."""
        _create_fake_bin(fake_tools, "npm", "echo 'npm failed' >&2; exit 1")
        r = _run_script(fake_tools)
        assert r.returncode == 0

    def test_failing_brew_update_does_not_stop_script(self, fake_tools: Path):
        """brew update fails but script continues."""
        _create_fake_bin(fake_tools, "brew", """\
case "$1" in
    shellenv) echo 'export PATH="/opt/homebrew/bin:$PATH"' ;;
    update) echo 'update failed' >&2; exit 1 ;;
    *) echo "brew $*: ok" ;;
esac
""")
        r = _run_script(fake_tools)
        assert r.returncode == 0

    def test_failing_cargo_continues(self, fake_tools: Path):
        _create_fake_bin(fake_tools, "cargo", "exit 1")
        r = _run_script(fake_tools)
        assert r.returncode == 0

    def test_log_shows_subsequent_sections_after_failure(self, fake_tools: Path):
        """npm fails but cargo section still appears in log."""
        _create_fake_bin(fake_tools, "npm", "exit 1")
        _run_script(fake_tools)
        log = (fake_tools / LOG_NAME).read_text()
        assert "Updating cargo" in log


# ── 4. PATH configuration verification ────────────────────────────────


class TestPathSetup:
    def test_script_extends_path_with_cargo_bin(self, fake_tools: Path):
        """The PATH export in the script should include .cargo/bin."""
        src = SCRIPT.read_text()
        assert ".cargo/bin" in src

    def test_brew_shellenv_evaluated(self, fake_tools: Path):
        """brew shellenv must be eval'd before other brew commands."""
        src = SCRIPT.read_text()
        shellenv_pos = src.index("brew shellenv")
        update_pos = src.index("brew update")
        assert shellenv_pos < update_pos


# ── 5. Health file structure validation ───────────────────────────────


class TestHealthFileStructure:
    def test_ok_health_has_all_required_fields(self, fake_tools: Path):
        _run_script(fake_tools)
        data = json.loads((fake_tools / HEALTH_NAME).read_text())
        for field in ("status", "checked", "failures"):
            assert field in data, f"Missing field: {field}"

    def test_degraded_health_failures_is_list(self, tmp_path: Path):
        """When degraded, failures field must be a list of strings."""
        # Create minimal fakes with one missing tool
        _create_fake_bin(tmp_path, "brew", """\
case "$1" in
    shellenv) echo 'export PATH="/opt/homebrew/bin:$PATH"' ;;
    *) echo "ok" ;;
esac
""")
        for cmd in ("npm", "pnpm", "uv", "cargo", "mas"):
            _create_fake_bin(tmp_path, cmd, "echo ok")
        # Missing claude, opencode, etc.
        _run_script(tmp_path)
        data = json.loads((tmp_path / HEALTH_NAME).read_text())
        assert isinstance(data["failures"], list)
        for f in data["failures"]:
            assert isinstance(f, str)

    def test_ok_failures_is_empty_list(self, fake_tools: Path):
        _run_script(fake_tools)
        data = json.loads((fake_tools / HEALTH_NAME).read_text())
        assert data["failures"] == []
        assert isinstance(data["failures"], list)


# ── 6. Log file format ────────────────────────────────────────────────


class TestLogFileFormat:
    def test_log_starts_with_timestamp(self, fake_tools: Path):
        _run_script(fake_tools)
        first_line = (fake_tools / LOG_NAME).read_text().splitlines()[0]
        assert first_line.startswith("===")
        assert first_line.endswith("===")

    def test_log_ends_with_completion_marker(self, fake_tools: Path):
        _run_script(fake_tools)
        lines = (fake_tools / LOG_NAME).read_text().strip().splitlines()
        last = lines[-1]
        assert "Updates complete" in last
        assert "===" in last

    def test_log_has_section_for_each_updater(self, fake_tools: Path):
        _run_script(fake_tools)
        log = (fake_tools / LOG_NAME).read_text()
        expected_sections = [
            "Updating brew",
            "Updating npm",
            "Updating pnpm",
            "Updating uv",
            "Updating cargo",
            "Updating Mac App Store",
        ]
        for section in expected_sections:
            assert section in log, f"Missing log section: {section}"

    def test_log_file_appends_not_overwrites(self, fake_tools: Path):
        """Running twice should append to the log, not overwrite."""
        _run_script(fake_tools)
        _run_script(fake_tools)
        log = (fake_tools / LOG_NAME).read_text()
        # Should have at least 2 start markers
        start_count = log.count("=== $(date)")
        # Actually the === markers will have actual timestamps, not $(date)
        # Count "===" lines instead
        marker_count = sum(1 for line in log.splitlines() if line.startswith("==="))
        assert marker_count >= 4  # 2 runs × (1 start + 1 end) minimum
