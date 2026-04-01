from __future__ import annotations

"""Tests for effectors/update-compound-engineering-skills.sh — bash script tested via subprocess."""

import os
import re
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "update-compound-engineering-skills.sh"


# ── script structure tests ──────────────────────────────────────────────


class TestScriptStructure:
    def test_script_exists(self):
        assert SCRIPT.exists()

    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_has_shebang(self):
        first_line = SCRIPT.read_text().splitlines()[0]
        assert first_line == "#!/usr/bin/env bash"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_script(
    args: list[str] | None = None,
    env_extra: dict | None = None,
    tmp_path: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run the script with optional custom env and tmp_path as HOME."""
    env = os.environ.copy()
    if tmp_path is not None:
        env["HOME"] = str(tmp_path)
    if env_extra:
        env.update(env_extra)
    cmd = ["bash", str(SCRIPT)] + (args or [])
    return subprocess.run(
        cmd, capture_output=True, text=True, env=env, timeout=10,
    )


def _make_mock_bin(tmp_path: Path, name: str, stdout: str = "", exit_code: int = 0) -> Path:
    """Create a mock executable script in tmp_path/bin/<name>."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(f"#!/bin/bash\necho {stdout}\nexit {exit_code}\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bindir


def _make_recording_bin(tmp_path: Path, name: str, record_file: Path, exit_code: int = 0) -> Path:
    """Create a mock bin that records all args to record_file."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / name
    script.write_text(
        "#!/bin/bash\n"
        f'echo "$@" >> {record_file}\n'
        f"exit {exit_code}\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return bindir


def _setup_mock_installer(tmp_path: Path, record_file: Path, exit_code: int = 0):
    """Set up mock install-skill-from-github.py in the expected location."""
    script_dir = tmp_path / ".codex" / "skills" / ".system" / "skill-installer" / "scripts"
    script_dir.mkdir(parents=True, exist_ok=True)
    installer = script_dir / "install-skill-from-github.py"
    installer.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f'with open({repr(str(record_file))}, "a") as f:\n'
        "    f.write(' '.join(sys.argv[1:]) + '\\n')\n"
        f"sys.exit({exit_code})\n"
    )
    installer.chmod(installer.stat().st_mode | stat.S_IEXEC)


# ── --help tests ────────────────────────────────────────────────────────


class TestHelpFlag:
    def test_help_exits_zero(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_h_short_flag_exits_zero(self, tmp_path):
        r = _run_script(["-h"], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_help_shows_usage(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "Usage:" in r.stdout

    def test_help_mentions_skills(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "skills" in r.stdout


# ── script execution tests ──────────────────────────────────────────────


class TestScriptExecution:
    def test_runs_installer_with_all_skills(self, tmp_path):
        """Script runs install-skill-from-github.py with all expected skills."""
        record = tmp_path / "installer_calls.log"
        _setup_mock_installer(tmp_path, record)

        # Also need to set up CODEX_SKILLS_DIR
        codex_skills = tmp_path / ".codex" / "skills"
        codex_skills.mkdir(parents=True, exist_ok=True)

        r = _run_script(tmp_path=tmp_path)
        assert r.returncode == 0

        assert record.exists()
        calls = record.read_text()

        # Check that all skills are passed
        assert "agent-browser" in calls
        assert "agent-native-architecture" in calls
        assert "andrew-kane-gem-writer" in calls
        assert "ce-brainstorm" in calls
        assert "dhh-rails-style" in calls
        assert "dspy-ruby" in calls
        assert "every-style-editor" in calls
        assert "frontend-design" in calls
        assert "gemini-imagegen" in calls
        assert "git-worktree" in calls
        assert "rclone" in calls

        # Check repo and path
        assert "EveryInc/compound-engineering-plugin" in calls
        assert "plugins/compound-engineering/skills" in calls

    def test_creates_backup_dir(self, tmp_path):
        """Script creates a backup directory."""
        record = tmp_path / "installer_calls.log"
        _setup_mock_installer(tmp_path, record)

        # Set up existing skills
        codex_skills = tmp_path / ".codex" / "skills"
        codex_skills.mkdir(parents=True, exist_ok=True)
        (codex_skills / "agent-browser").mkdir()

        r = _run_script(tmp_path=tmp_path)
        assert r.returncode == 0

        # Check backup dir exists
        backup_parent = tmp_path / ".codex" / "skills-backup"
        assert backup_parent.exists()
        backups = list(backup_parent.iterdir())
        assert len(backups) == 1
        assert backups[0].name.startswith("compound-engineering-")

    def test_installer_failure_restores_backup(self, tmp_path):
        """If installer fails, script restores backup."""
        record = tmp_path / "installer_calls.log"
        _setup_mock_installer(tmp_path, record, exit_code=1)

        # Set up existing skills
        codex_skills = tmp_path / ".codex" / "skills"
        codex_skills.mkdir(parents=True, exist_ok=True)
        test_skill = codex_skills / "agent-browser"
        test_skill.mkdir()
        (test_skill / "test.txt").write_text("test content")

        # This should fail and restore backup
        _run_script(tmp_path=tmp_path)

        # Verify the skill was restored
        assert test_skill.exists()
        assert (test_skill / "test.txt").read_text() == "test content"
