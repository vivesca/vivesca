from __future__ import annotations

"""Tests for effectors/update-compound-engineering-skills.sh — bash script tested via subprocess."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "update-compound-engineering-skills.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run(
    args: list[str] | None = None,
    env_extra: dict | None = None,
    home: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run the script with optional HOME override and extra env vars."""
    env = os.environ.copy()
    if home is not None:
        env["HOME"] = str(home)
    if env_extra:
        env.update(env_extra)
    cmd = ["bash", str(SCRIPT)] + (args or [])
    return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)


def _make_installer(tmp_path: Path, exit_code: int = 0, record_file: Path | None = None) -> Path:
    """Create a mock install-skill-from-github.py in the expected location."""
    script_dir = tmp_path / ".codex" / "skills" / ".system" / "skill-installer" / "scripts"
    script_dir.mkdir(parents=True, exist_ok=True)
    installer = script_dir / "install-skill-from-github.py"
    if record_file is not None:
        installer.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            f"with open('{record_file}', 'a') as f:\n"
            "    f.write(repr(sys.argv) + '\\n')\n"
            f"sys.exit({exit_code})\n"
        )
    else:
        installer.write_text(
            "#!/usr/bin/env python3\nimport sys\n"
            f"sys.exit({exit_code})\n"
        )
    installer.chmod(installer.stat().st_mode | stat.S_IEXEC)
    return installer


def _make_skill_dir(tmp_path: Path, name: str) -> Path:
    """Create a fake existing skill directory under ~/.codex/skills/."""
    skill_dir = tmp_path / ".codex" / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "skill.md").write_text(f"# {name}\n")
    return skill_dir


def _codex_skills(tmp_path: Path) -> Path:
    return tmp_path / ".codex" / "skills"


def _backup_dirs(tmp_path: Path) -> list[Path]:
    """Return all backup dirs sorted by name."""
    backup_base = tmp_path / ".codex" / "skills-backup"
    if not backup_base.exists():
        return []
    return sorted(backup_base.iterdir())


# ── script structure tests ──────────────────────────────────────────────


class TestScriptStructure:
    def test_script_exists(self):
        assert SCRIPT.exists()
        assert SCRIPT.is_file()

    def test_script_is_executable(self):
        assert (SCRIPT.stat().st_mode & 0o111) != 0

    def test_script_uses_strict_mode(self):
        content = SCRIPT.read_text()
        assert "set -euo pipefail" in content

    def test_skills_array_contains_expected_skills(self):
        content = SCRIPT.read_text()
        expected = [
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
        lines = content.splitlines()
        start = next(i for i, ln in enumerate(lines) if "SKILLS=(" in ln)
        skills = []
        for ln in lines[start + 1 :]:
            ln = ln.strip()
            if ln == ")":
                break
            if ln and not ln.startswith("#"):
                skills.append(ln.split("#")[0].strip())
        assert skills == expected
        assert len(skills) == 11

    def test_python3_call_paths_match_skills(self):
        """Every skill in SKILLS must appear as a --path argument to python3."""
        content = SCRIPT.read_text()
        lines = content.splitlines()
        # Extract skills
        start = next(i for i, ln in enumerate(lines) if "SKILLS=(" in ln)
        skills = []
        for ln in lines[start + 1 :]:
            ln = ln.strip()
            if ln == ")":
                break
            if ln and not ln.startswith("#"):
                skills.append(ln.split("#")[0].strip())
        # Find the python3 invocation block and extract paths
        path_lines = []
        in_python_block = False
        for ln in lines:
            stripped = ln.strip()
            if "python3" in stripped and "${INSTALLER}" in stripped:
                in_python_block = True
                continue
            if in_python_block:
                if stripped.startswith("${BASE_PATH}/"):
                    skill_name = stripped.split("/")[-1].rstrip("\\").strip()
                    path_lines.append(skill_name)
                elif "exit" in stripped:
                    break
        assert sorted(path_lines) == sorted(skills), (
            f"Mismatch: SKILLS={sorted(skills)} vs paths={sorted(path_lines)}"
        )

    def test_repo_is_set(self):
        content = SCRIPT.read_text()
        assert 'REPO="EveryInc/compound-engineering-plugin"' in content

    def test_base_path_is_set(self):
        content = SCRIPT.read_text()
        assert 'BASE_PATH="plugins/compound-engineering/skills"' in content

    def test_has_err_trap(self):
        content = SCRIPT.read_text()
        assert "trap" in content and "ERR" in content

    def test_restore_and_cleanup_functions_exist(self):
        content = SCRIPT.read_text()
        assert "restore_backup()" in content
        assert "cleanup_partial_installs()" in content


# ── help flag tests ─────────────────────────────────────────────────────


class TestHelpFlag:
    def test_help_exits_zero(self):
        r = _run(["--help"])
        assert r.returncode == 0

    def test_h_short_flag_exits_zero(self):
        r = _run(["-h"])
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = _run(["--help"])
        assert "Usage:" in r.stdout

    def test_help_shows_description(self):
        r = _run(["--help"])
        assert "Install/update compound-engineering skills" in r.stdout

    def test_help_shows_requirements(self):
        r = _run(["--help"])
        assert "python3" in r.stdout
        assert "install-skill-from-github.py" in r.stdout


# ── backup mechanism tests ──────────────────────────────────────────────


class TestBackup:
    def test_creates_backup_dir_on_run(self, tmp_path):
        """A backup directory is created under ~/.codex/skills-backup/."""
        _make_installer(tmp_path)
        _run(home=tmp_path)
        backups = _backup_dirs(tmp_path)
        assert len(backups) >= 1

    def test_backup_dir_has_timestamp_name(self, tmp_path):
        """Backup dir name contains datestamp pattern."""
        _make_installer(tmp_path)
        _run(home=tmp_path)
        backups = _backup_dirs(tmp_path)
        assert len(backups) >= 1
        name = backups[0].name
        assert name.startswith("compound-engineering-")

    def test_existing_skills_backed_up_before_install(self, tmp_path):
        """Existing skill directories are moved to backup before install."""
        record = tmp_path / "install_calls.log"
        _make_installer(tmp_path, record_file=record)
        skill_dir = _make_skill_dir(tmp_path, "agent-browser")
        test_file = skill_dir / "test_marker.txt"
        test_file.write_text("preserved")
        _run(home=tmp_path)
        backups = _backup_dirs(tmp_path)
        assert len(backups) >= 1
        assert (backups[0] / "agent-browser" / "test_marker.txt").exists()

    def test_all_existing_skills_backed_up(self, tmp_path):
        """All pre-existing skill dirs get backed up."""
        _make_installer(tmp_path)
        for name in ["agent-browser", "dspy-ruby", "rclone"]:
            _make_skill_dir(tmp_path, name)
        _run(home=tmp_path)
        backups = _backup_dirs(tmp_path)
        assert len(backups) >= 1
        for name in ["agent-browser", "dspy-ruby", "rclone"]:
            assert (backups[0] / name).exists()

    def test_non_skill_dirs_not_backed_up(self, tmp_path):
        """Directories not in SKILLS array are NOT moved to backup."""
        _make_installer(tmp_path)
        other_dir = _codex_skills(tmp_path) / "some-other-tool"
        other_dir.mkdir(parents=True, exist_ok=True)
        (other_dir / "data.txt").write_text("keep me")
        _run(home=tmp_path)
        assert other_dir.exists()


# ── installer invocation tests ──────────────────────────────────────────


class TestInstallerInvocation:
    def test_installer_called_with_repo(self, tmp_path):
        """Installer receives --repo EveryInc/compound-engineering-plugin."""
        record = tmp_path / "install_calls.log"
        _make_installer(tmp_path, record_file=record)
        _run(home=tmp_path)
        calls = record.read_text()
        assert "EveryInc/compound-engineering-plugin" in calls

    def test_installer_called_with_path_flag(self, tmp_path):
        """Installer receives --path with skill subpaths."""
        record = tmp_path / "install_calls.log"
        _make_installer(tmp_path, record_file=record)
        _run(home=tmp_path)
        calls = record.read_text()
        assert "--path" in calls

    def test_installer_called_with_all_skill_paths(self, tmp_path):
        """Every skill appears in the installer invocation."""
        record = tmp_path / "install_calls.log"
        _make_installer(tmp_path, record_file=record)
        _run(home=tmp_path)
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
            assert skill in calls, f"Skill '{skill}' not found in installer call"

    def test_installer_receives_base_path_prefix(self, tmp_path):
        """Paths include the BASE_PATH prefix (plugins/compound-engineering/skills)."""
        record = tmp_path / "install_calls.log"
        _make_installer(tmp_path, record_file=record)
        _run(home=tmp_path)
        calls = record.read_text()
        assert "plugins/compound-engineering/skills" in calls


# ── error handling / restore tests ──────────────────────────────────────


class TestErrorHandling:
    def test_failing_installer_triggers_err_trap(self, tmp_path):
        """When installer exits non-zero, script exits non-zero."""
        _make_installer(tmp_path, exit_code=1)
        r = _run(home=tmp_path)
        assert r.returncode != 0

    def test_failing_installer_restores_backup(self, tmp_path):
        """Existing skills are restored when installer fails."""
        _make_installer(tmp_path, exit_code=1)
        skill_dir = _make_skill_dir(tmp_path, "agent-browser")
        (skill_dir / "marker.txt").write_text("original")
        _run(home=tmp_path)
        restored = _codex_skills(tmp_path) / "agent-browser" / "marker.txt"
        assert restored.exists()
        assert restored.read_text() == "original"

    def test_failing_installer_cleans_partial(self, tmp_path):
        """Partially installed skills (not in backup) are removed on failure."""
        record = tmp_path / "install_calls.log"
        skills_dir = _codex_skills(tmp_path)
        installer_script = (
            tmp_path / ".codex" / "skills" / ".system" / "skill-installer" / "scripts"
            / "install-skill-from-github.py"
        )
        # Create installer that makes a skill dir then fails
        installer_script.parent.mkdir(parents=True, exist_ok=True)
        installer_script.write_text(
            "#!/usr/bin/env python3\n"
            "import sys, pathlib\n"
            f"skills_dir = pathlib.Path('{skills_dir}')\n"
            "skills_dir.mkdir(parents=True, exist_ok=True)\n"
            "(skills_dir / 'rclone').mkdir(exist_ok=True)\n"
            f"with open('{record}', 'a') as f:\n"
            "    f.write(repr(sys.argv) + '\\n')\n"
            "sys.exit(1)\n"
        )
        installer_script.chmod(installer_script.stat().st_mode | stat.S_IEXEC)
        r = _run(home=tmp_path)
        assert r.returncode != 0
        # rclone was not backed up (didn't exist before) so it should be cleaned up
        assert not (skills_dir / "rclone").exists()

    def test_successful_run_exits_zero(self, tmp_path):
        _make_installer(tmp_path)
        r = _run(home=tmp_path)
        assert r.returncode == 0

    def test_missing_installer_script_fails(self, tmp_path):
        """Script fails if the installer Python script does not exist."""
        r = _run(home=tmp_path)
        assert r.returncode != 0


# ── edge case tests ────────────────────────────────────────────────────


class TestEdgeCases:
    def test_no_existing_skills_succeeds(self, tmp_path):
        """Script succeeds even when no existing skills to back up."""
        _make_installer(tmp_path)
        r = _run(home=tmp_path)
        assert r.returncode == 0

    def test_codex_dir_created_on_run(self, tmp_path):
        """The .codex directory exists after running."""
        _make_installer(tmp_path)
        _run(home=tmp_path)
        assert (tmp_path / ".codex").exists()

    def test_multiple_runs_create_separate_backups(self, tmp_path):
        """Each run creates a new backup directory."""
        import time

        _make_installer(tmp_path)
        _run(home=tmp_path)
        time.sleep(1.1)  # ensure different timestamp in dir name
        _make_installer(tmp_path)
        _run(home=tmp_path)
        backups = _backup_dirs(tmp_path)
        assert len(backups) >= 2

    def test_help_does_not_create_backup(self, tmp_path):
        """--help should not create any backup directories."""
        _run(["--help"], home=tmp_path)
        backup_base = tmp_path / ".codex" / "skills-backup"
        assert not backup_base.exists()
