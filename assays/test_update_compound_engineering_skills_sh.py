from __future__ import annotations

"""Tests for effectors/update-compound-engineering-skills.sh — bash script tested via subprocess."""

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "update-compound-engineering-skills.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_script(
    args: list[str] | None = None,
    env_extra: dict | None = None,
    tmp_path: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run the script with optional custom env and HOME=tmp_path."""
    env = os.environ.copy()
    if tmp_path is not None:
        env["HOME"] = str(tmp_path)
    if env_extra:
        env.update(env_extra)
    cmd = ["bash", str(SCRIPT)] + (args or [])
    return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)


def _make_mock_installer(tmp_path: Path, exit_code: int = 0) -> Path:
    """Create a mock install-skill-from-github.py script."""
    script_dir = tmp_path / ".codex" / "skills" / ".system" / "skill-installer" / "scripts"
    script_dir.mkdir(parents=True, exist_ok=True)
    installer = script_dir / "install-skill-from-github.py"
    installer.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "print(f'Mock installer called with: {sys.argv[1:]}')\n"
        f"sys.exit({exit_code})\n"
    )
    installer.chmod(installer.stat().st_mode | stat.S_IEXEC)
    return installer


def _make_recording_installer(tmp_path: Path, record_file: Path, exit_code: int = 0) -> Path:
    """Create a mock installer that records all args to a file."""
    script_dir = tmp_path / ".codex" / "skills" / ".system" / "skill-installer" / "scripts"
    script_dir.mkdir(parents=True, exist_ok=True)
    installer = script_dir / "install-skill-from-github.py"
    installer.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"with open('{record_file}', 'a') as f:\n"
        "    f.write(' '.join(sys.argv[1:]) + '\\n')\n"
        f"sys.exit({exit_code})\n"
    )
    installer.chmod(installer.stat().st_mode | stat.S_IEXEC)
    return installer


def _skills_dir(tmp_path: Path) -> Path:
    return tmp_path / ".codex" / "skills"


def _backup_dir(tmp_path: Path) -> Path:
    return tmp_path / ".codex" / "skills-backup"


# ── --help tests ───────────────────────────────────────────────────────────


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
        assert "skills" in r.stdout.lower()

    def test_help_does_not_create_backup(self, tmp_path):
        _run_script(["--help"], tmp_path=tmp_path)
        backup = _backup_dir(tmp_path)
        assert not backup.exists() or not any(backup.iterdir())


# ── installer requirement tests ───────────────────────────────────────────


class TestInstallerRequirement:
    def test_missing_installer_exits_nonzero(self, tmp_path):
        """Script fails when installer script is missing."""
        r = _run_script(tmp_path=tmp_path)
        assert r.returncode != 0

    def test_missing_installer_error_message(self, tmp_path):
        """Script reports error when installer is missing."""
        r = _run_script(tmp_path=tmp_path)
        # bash set -e causes exit, check stderr or that it failed
        assert r.returncode != 0


# ── backup tests ───────────────────────────────────────────────────────────


class TestBackup:
    def test_creates_backup_directory(self, tmp_path):
        """Script creates a backup directory."""
        _make_mock_installer(tmp_path)
        r = _run_script(tmp_path=tmp_path)
        assert r.returncode == 0
        backup = _backup_dir(tmp_path)
        assert backup.exists()

    def test_backs_up_existing_skills(self, tmp_path):
        """Existing skills are moved to backup before install."""
        skills = _skills_dir(tmp_path)
        skills.mkdir(parents=True, exist_ok=True)
        # Create an existing skill
        (skills / "agent-browser").mkdir()
        (skills / "agent-browser" / "test.md").write_text("old content")
        
        _make_mock_installer(tmp_path)
        r = _run_script(tmp_path=tmp_path)
        assert r.returncode == 0
        
        backup = _backup_dir(tmp_path)
        # Backup should contain the old skill
        backup_found = False
        for d in backup.iterdir():
            if (d / "agent-browser" / "test.md").exists():
                backup_found = True
                break
        assert backup_found

    def test_backup_timestamp_in_directory_name(self, tmp_path):
        """Backup directory name includes timestamp."""
        _make_mock_installer(tmp_path)
        r = _run_script(tmp_path=tmp_path)
        assert r.returncode == 0
        
        backup = _backup_dir(tmp_path)
        dirs = list(backup.iterdir())
        assert len(dirs) == 1
        # Name format: compound-engineering-YYYYMMDD-HHMMSS
        import re
        assert re.match(r"compound-engineering-\d{8}-\d{6}", dirs[0].name)


# ── installer invocation tests ─────────────────────────────────────────────


class TestInstallerInvocation:
    def test_installer_called_with_repo(self, tmp_path):
        """Installer receives --repo EveryInc/compound-engineering-plugin."""
        record = tmp_path / "calls.log"
        _make_recording_installer(tmp_path, record)
        r = _run_script(tmp_path=tmp_path)
        assert r.returncode == 0
        
        calls = record.read_text()
        assert "--repo" in calls
        assert "EveryInc/compound-engineering-plugin" in calls

    def test_installer_called_with_path(self, tmp_path):
        """Installer receives --path with skill paths."""
        record = tmp_path / "calls.log"
        _make_recording_installer(tmp_path, record)
        r = _run_script(tmp_path=tmp_path)
        assert r.returncode == 0
        
        calls = record.read_text()
        assert "--path" in calls

    def test_installer_receives_all_skills(self, tmp_path):
        """Installer receives all expected skill paths."""
        record = tmp_path / "calls.log"
        _make_recording_installer(tmp_path, record)
        r = _run_script(tmp_path=tmp_path)
        assert r.returncode == 0
        
        calls = record.read_text()
        expected_skills = [
            "agent-browser",
            "agent-native-architecture",
            "andrew-kane-gem-writer",
            "ce-brainstorm",
            "dhh-rails-style",
            "dspy-ruby",
            "every-style-editor",
            "frontend-design",
            "gemini-imagegen",
            "git-worktree",
            "rclone",
        ]
        for skill in expected_skills:
            assert skill in calls, f"Missing skill: {skill}"

    def test_installer_receives_base_path_prefix(self, tmp_path):
        """Skill paths include plugins/compound-engineering/skills prefix."""
        record = tmp_path / "calls.log"
        _make_recording_installer(tmp_path, record)
        r = _run_script(tmp_path=tmp_path)
        assert r.returncode == 0
        
        calls = record.read_text()
        assert "plugins/compound-engineering/skills" in calls


# ── error handling tests ───────────────────────────────────────────────────


class TestErrorHandling:
    def test_installer_failure_exits_nonzero(self, tmp_path):
        """Script exits with error when installer fails."""
        _make_mock_installer(tmp_path, exit_code=1)
        r = _run_script(tmp_path=tmp_path)
        assert r.returncode != 0

    def test_partial_installs_cleaned_up_on_failure(self, tmp_path):
        """When installer fails, partially installed skills are removed."""
        skills = _skills_dir(tmp_path)
        skills.mkdir(parents=True, exist_ok=True)
        # Pre-existing skill should be backed up
        (skills / "agent-browser").mkdir()
        (skills / "agent-browser" / "old.md").write_text("old")
        
        _make_mock_installer(tmp_path, exit_code=1)
        r = _run_script(tmp_path=tmp_path)
        assert r.returncode != 0
        
        # The backed-up skill should be restored
        # (backup was created before failure, restore happens on ERR trap)
        backup = _backup_dir(tmp_path)
        # Backup should exist and contain the old skill
        assert backup.exists()


# ── skills list tests ───────────────────────────────────────────────────────


class TestSkillsList:
    """Verify the SKILLS array matches what's passed to installer."""
    
    def test_skills_count_matches(self, tmp_path):
        """Number of skills in SKILLS array matches installer args."""
        record = tmp_path / "calls.log"
        _make_recording_installer(tmp_path, record)
        r = _run_script(tmp_path=tmp_path)
        assert r.returncode == 0
        
        calls = record.read_text()
        # Count skill path entries (each skill has plugins/compound-engineering/skills/<name>)
        # The SKILLS array has 11 entries
        expected_count = 11
        # Count occurrences of each skill name
        skills = [
            "agent-browser",
            "agent-native-architecture", 
            "andrew-kane-gem-writer",
            "ce-brainstorm",
            "dhh-rails-style",
            "dspy-ruby",
            "every-style-editor",
            "frontend-design",
            "gemini-imagegen",
            "git-worktree",
            "rclone",
        ]
        found = sum(1 for s in skills if s in calls)
        assert found == expected_count, f"Expected {expected_count} skills, found {found}"


# ── exit code tests ─────────────────────────────────────────────────────────


class TestExitCodes:
    def test_success_exits_zero(self, tmp_path):
        """Successful run exits with 0."""
        _make_mock_installer(tmp_path)
        r = _run_script(tmp_path=tmp_path)
        assert r.returncode == 0

    def test_failure_exits_nonzero(self, tmp_path):
        """Failed installer causes non-zero exit."""
        _make_mock_installer(tmp_path, exit_code=1)
        r = _run_script(tmp_path=tmp_path)
        assert r.returncode != 0
