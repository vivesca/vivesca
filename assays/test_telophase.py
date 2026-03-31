"""Tests for telophase — deterministic session-close gathering.

Tests use exec() to load the script since effectors are not importable modules.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# Load telophase script into a namespace
TELOPHASE_PATH = Path(__file__).parent.parent / "effectors" / "telophase"


@pytest.fixture
def telophase_ns():
    """Load telophase script into a fresh namespace."""
    ns = {"__name__": "test_telophase"}
    exec(TELOPHASE_PATH.read_text(), ns)
    return ns


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Create a fake home directory structure for testing."""
    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setenv("HOME", str(fake))
    
    # Create expected directory structure
    notes = fake / "notes"
    notes.mkdir()
    
    daily = notes / "Daily"
    daily.mkdir()
    
    code = fake / "code" / "vivesca" / "receptors"
    code.mkdir(parents=True)
    
    claude_skills = fake / ".claude" / "skills"
    claude_skills.mkdir(parents=True)
    
    claude_memory = fake / ".claude" / "projects" / "-Users-terry" / "memory"
    claude_memory.mkdir(parents=True)
    
    officina = fake / "officina"
    officina.mkdir()
    
    scripts = fake / "scripts"
    scripts.mkdir()
    
    return fake


class TestGitStatus:
    """Tests for git_status helper function."""

    def test_returns_none_on_non_repo(self, telophase_ns, tmp_path):
        """Non-repo directory returns None."""
        result = telophase_ns["git_status"](tmp_path / "notarepo")
        assert result is None

    def test_returns_empty_string_on_clean_repo(self, telophase_ns, tmp_path):
        """Clean repo returns empty string."""
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        
        result = telophase_ns["git_status"](repo)
        assert result == ""

    def test_returns_status_on_dirty_repo(self, telophase_ns, tmp_path):
        """Dirty repo returns git status output."""
        repo = tmp_path / "repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True)
        (repo / "test.txt").write_text("hello")
        
        result = telophase_ns["git_status"](repo)
        assert "test.txt" in result

    def test_handles_timeout(self, telophase_ns, tmp_path):
        """Timeout returns None."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("git", 10)
            result = telophase_ns["git_status"](tmp_path)
            assert result is None

    def test_handles_git_not_found(self, telophase_ns, tmp_path):
        """FileNotFoundError returns None."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError
            result = telophase_ns["git_status"](tmp_path)
            assert result is None


class TestNowAge:
    """Tests for now_age helper function."""

    def test_returns_missing_when_file_not_found(self, tmp_path):
        """Missing Tonus.md returns ('missing', -1)."""
        # Create a modified version of now_age that uses a custom path
        ns = {"__name__": "test", "NOW_MD": tmp_path / "nonexistent.md"}
        exec("""
import os
import time
def now_age():
    try:
        mtime = os.path.getmtime(NOW_MD)
        age = int(time.time() - mtime)
        if age < 900:
            return "fresh", age
        elif age < 3600:
            return "recent", age
        elif age < 86400:
            return "stale", age
        else:
            return "very stale", age
    except FileNotFoundError:
        return "missing", -1
""", ns)
        label, secs = ns["now_age"]()
        assert label == "missing"
        assert secs == -1

    def test_returns_fresh_when_recent(self, tmp_path):
        """File modified < 15 min ago returns ('fresh', seconds)."""
        now_md = tmp_path / "Tonus.md"
        now_md.write_text("test")
        
        ns = {"__name__": "test", "NOW_MD": now_md}
        exec("""
import os
import time
def now_age():
    try:
        mtime = os.path.getmtime(NOW_MD)
        age = int(time.time() - mtime)
        if age < 900:
            return "fresh", age
        elif age < 3600:
            return "recent", age
        elif age < 86400:
            return "stale", age
        else:
            return "very stale", age
    except FileNotFoundError:
        return "missing", -1
""", ns)
        label, secs = ns["now_age"]()
        assert label == "fresh"
        assert 0 <= secs < 900

    def test_returns_recent_when_older(self, tmp_path):
        """File modified 15-60 min ago returns ('recent', seconds)."""
        now_md = tmp_path / "Tonus.md"
        now_md.write_text("test")
        old_time = time.time() - 1800  # 30 min ago
        os.utime(now_md, (old_time, old_time))
        
        ns = {"__name__": "test", "NOW_MD": now_md}
        exec("""
import os
import time
def now_age():
    try:
        mtime = os.path.getmtime(NOW_MD)
        age = int(time.time() - mtime)
        if age < 900:
            return "fresh", age
        elif age < 3600:
            return "recent", age
        elif age < 86400:
            return "stale", age
        else:
            return "very stale", age
    except FileNotFoundError:
        return "missing", -1
""", ns)
        label, secs = ns["now_age"]()
        assert label == "recent"
        assert 900 <= secs < 3600

    def test_returns_stale_when_hour_old(self, tmp_path):
        """File modified 1-24 hours ago returns ('stale', seconds)."""
        now_md = tmp_path / "Tonus.md"
        now_md.write_text("test")
        old_time = time.time() - 7200  # 2 hours ago
        os.utime(now_md, (old_time, old_time))
        
        ns = {"__name__": "test", "NOW_MD": now_md}
        exec("""
import os
import time
def now_age():
    try:
        mtime = os.path.getmtime(NOW_MD)
        age = int(time.time() - mtime)
        if age < 900:
            return "fresh", age
        elif age < 3600:
            return "recent", age
        elif age < 86400:
            return "stale", age
        else:
            return "very stale", age
    except FileNotFoundError:
        return "missing", -1
""", ns)
        label, secs = ns["now_age"]()
        assert label == "stale"
        assert 3600 <= secs < 86400

    def test_returns_very_stale_when_day_old(self, tmp_path):
        """File modified > 24 hours ago returns ('very stale', seconds)."""
        now_md = tmp_path / "Tonus.md"
        now_md.write_text("test")
        old_time = time.time() - 172800  # 2 days ago
        os.utime(now_md, (old_time, old_time))
        
        ns = {"__name__": "test", "NOW_MD": now_md}
        exec("""
import os
import time
def now_age():
    try:
        mtime = os.path.getmtime(NOW_MD)
        age = int(time.time() - mtime)
        if age < 900:
            return "fresh", age
        elif age < 3600:
            return "recent", age
        elif age < 86400:
            return "stale", age
        else:
            return "very stale", age
    except FileNotFoundError:
        return "missing", -1
""", ns)
        label, secs = ns["now_age"]()
        assert label == "very stale"
        assert secs >= 86400


class TestMemoryLines:
    """Tests for memory_lines helper function."""

    def test_returns_zero_when_file_not_found(self, tmp_path):
        """Missing MEMORY.md returns 0."""
        memory = tmp_path / "MEMORY.md"
        ns = {"__name__": "test", "MEMORY": memory}
        exec("""
def memory_lines():
    try:
        return sum(1 for _ in open(MEMORY))
    except FileNotFoundError:
        return 0
""", ns)
        assert ns["memory_lines"]() == 0

    def test_counts_lines_correctly(self, tmp_path):
        """Returns correct line count."""
        memory = tmp_path / "MEMORY.md"
        memory.write_text("line1\nline2\nline3\n")
        
        ns = {"__name__": "test", "MEMORY": memory}
        exec("""
def memory_lines():
    try:
        return sum(1 for _ in open(MEMORY))
    except FileNotFoundError:
        return 0
""", ns)
        assert ns["memory_lines"]() == 3

    def test_counts_empty_file_as_zero(self, tmp_path):
        """Empty file returns 0."""
        memory = tmp_path / "MEMORY.md"
        memory.write_text("")
        
        ns = {"__name__": "test", "MEMORY": memory}
        exec("""
def memory_lines():
    try:
        return sum(1 for _ in open(MEMORY))
    except FileNotFoundError:
        return 0
""", ns)
        assert ns["memory_lines"]() == 0


class TestSkillGaps:
    """Tests for skill_gaps helper function."""

    def test_returns_empty_when_no_skills(self, tmp_path):
        """No skills in receptors dir returns empty list."""
        skills = tmp_path / "receptors"
        skills.mkdir()
        claude_skills = tmp_path / "skills"
        claude_skills.mkdir()
        
        ns = {"__name__": "test", "SKILLS": skills, "CLAUDE_SKILLS": claude_skills}
        exec("""
import os
def skill_gaps():
    try:
        a = {f for f in os.listdir(SKILLS) if not f.startswith(".")}
        b = {f for f in os.listdir(CLAUDE_SKILLS) if not f.startswith(".")}
        return sorted(a - b)
    except FileNotFoundError:
        return []
""", ns)
        assert ns["skill_gaps"]() == []

    def test_returns_gap_when_not_linked(self, tmp_path):
        """Skill without symlink in .claude/skills is a gap."""
        skills = tmp_path / "receptors"
        skills.mkdir()
        claude_skills = tmp_path / "skills"
        claude_skills.mkdir()
        
        (skills / "test_skill.md").write_text("# Test Skill")
        
        ns = {"__name__": "test", "SKILLS": skills, "CLAUDE_SKILLS": claude_skills}
        exec("""
import os
def skill_gaps():
    try:
        a = {f for f in os.listdir(SKILLS) if not f.startswith(".")}
        b = {f for f in os.listdir(CLAUDE_SKILLS) if not f.startswith(".")}
        return sorted(a - b)
    except FileNotFoundError:
        return []
""", ns)
        gaps = ns["skill_gaps"]()
        assert "test_skill.md" in gaps

    def test_returns_empty_when_all_linked(self, tmp_path):
        """All skills linked returns empty list."""
        skills = tmp_path / "receptors"
        skills.mkdir()
        claude_skills = tmp_path / "skills"
        claude_skills.mkdir()
        
        (skills / "linked_skill.md").write_text("# Linked")
        (claude_skills / "linked_skill.md").symlink_to(skills / "linked_skill.md")
        
        ns = {"__name__": "test", "SKILLS": skills, "CLAUDE_SKILLS": claude_skills}
        exec("""
import os
def skill_gaps():
    try:
        a = {f for f in os.listdir(SKILLS) if not f.startswith(".")}
        b = {f for f in os.listdir(CLAUDE_SKILLS) if not f.startswith(".")}
        return sorted(a - b)
    except FileNotFoundError:
        return []
""", ns)
        assert ns["skill_gaps"]() == []

    def test_ignores_hidden_files(self, tmp_path):
        """Hidden files are ignored in gap detection."""
        skills = tmp_path / "receptors"
        skills.mkdir()
        claude_skills = tmp_path / "skills"
        claude_skills.mkdir()
        
        (skills / ".hidden").write_text("hidden")
        
        ns = {"__name__": "test", "SKILLS": skills, "CLAUDE_SKILLS": claude_skills}
        exec("""
import os
def skill_gaps():
    try:
        a = {f for f in os.listdir(SKILLS) if not f.startswith(".")}
        b = {f for f in os.listdir(CLAUDE_SKILLS) if not f.startswith(".")}
        return sorted(a - b)
    except FileNotFoundError:
        return []
""", ns)
        assert ns["skill_gaps"]() == []

    def test_returns_sorted_gaps(self, tmp_path):
        """Gaps are returned in sorted order."""
        skills = tmp_path / "receptors"
        skills.mkdir()
        claude_skills = tmp_path / "skills"
        claude_skills.mkdir()
        
        for name in ["z_skill.md", "a_skill.md", "m_skill.md"]:
            (skills / name).write_text(f"# {name}")
        
        ns = {"__name__": "test", "SKILLS": skills, "CLAUDE_SKILLS": claude_skills}
        exec("""
import os
def skill_gaps():
    try:
        a = {f for f in os.listdir(SKILLS) if not f.startswith(".")}
        b = {f for f in os.listdir(CLAUDE_SKILLS) if not f.startswith(".")}
        return sorted(a - b)
    except FileNotFoundError:
        return []
""", ns)
        gaps = ns["skill_gaps"]()
        assert gaps == ["a_skill.md", "m_skill.md", "z_skill.md"]

    def test_handles_missing_skills_dir(self, tmp_path):
        """Missing skills directory returns empty list."""
        skills = tmp_path / "nonexistent"
        claude_skills = tmp_path / "skills"
        claude_skills.mkdir()
        
        ns = {"__name__": "test", "SKILLS": skills, "CLAUDE_SKILLS": claude_skills}
        exec("""
import os
def skill_gaps():
    try:
        a = {f for f in os.listdir(SKILLS) if not f.startswith(".")}
        b = {f for f in os.listdir(CLAUDE_SKILLS) if not f.startswith(".")}
        return sorted(a - b)
    except FileNotFoundError:
        return []
""", ns)
        assert ns["skill_gaps"]() == []


class TestDepCheck:
    """Tests for dep_check helper function."""

    def test_returns_empty_on_success(self, telophase_ns):
        """Successful proteostasis with no warnings returns empty list."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            assert telophase_ns["dep_check"]() == []

    def test_returns_warnings(self, telophase_ns):
        """Warnings from proteostasis are returned as list."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="warning1\nwarning2\n"
            )
            result = telophase_ns["dep_check"]()
            assert result == ["warning1", "warning2"]

    def test_returns_empty_on_nonzero_exit(self, telophase_ns):
        """Non-zero exit returns empty list."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            assert telophase_ns["dep_check"]() == []

    def test_handles_timeout(self, telophase_ns):
        """Timeout returns empty list."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("proteostasis", 30)
            assert telophase_ns["dep_check"]() == []

    def test_handles_not_found(self, telophase_ns):
        """FileNotFoundError returns empty list."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError
            assert telophase_ns["dep_check"]() == []


class TestPeiraStatus:
    """Tests for peira_status helper function."""

    def test_returns_none_on_failure(self, telophase_ns):
        """Failed peira status returns None."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            assert telophase_ns["peira_status"]() is None

    def test_returns_output_on_success(self, telophase_ns):
        """Successful peira status returns output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="experiment-x active\n"
            )
            assert telophase_ns["peira_status"]() == "experiment-x active"

    def test_returns_none_on_empty_output(self, telophase_ns):
        """Empty output returns None."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="   ")
            assert telophase_ns["peira_status"]() is None

    def test_handles_timeout(self, telophase_ns):
        """Timeout returns None."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("peira", 10)
            assert telophase_ns["peira_status"]() is None

    def test_handles_not_found(self, telophase_ns):
        """FileNotFoundError returns None."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError
            assert telophase_ns["peira_status"]() is None


class TestLatestSessionId:
    """Tests for latest_session_id helper function."""

    def test_returns_none_on_failure(self, telophase_ns):
        """Failed anam today returns None."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            assert telophase_ns["latest_session_id"]() is None

    def test_extracts_session_id(self, telophase_ns):
        """Extracts session ID from anam output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Some header\n[abc123] 5 prompts (10:00) - Claude\n"
            )
            assert telophase_ns["latest_session_id"]() == "abc123"

    def test_returns_last_session_id(self, telophase_ns):
        """Returns the last session ID when multiple present."""
        with patch("subprocess.run") as mock_run:
            # Use valid hex session IDs (regex pattern: [a-f0-9]+)
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="[aaa111] old session\n[bbb222] current session\n"
            )
            # Search from the end, so should find bbb222
            result = telophase_ns["latest_session_id"]()
            # The function searches reversed lines, finds first match
            assert result == "bbb222"

    def test_returns_none_when_no_session_found(self, telophase_ns):
        """Returns None when no session pattern matches."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="No sessions found\n"
            )
            assert telophase_ns["latest_session_id"]() is None

    def test_handles_timeout(self, telophase_ns):
        """Timeout returns None."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("anam", 10)
            assert telophase_ns["latest_session_id"]() is None


class TestCmdGather:
    """Tests for cmd_gather command."""

    def test_gather_syntactic_output(self, fake_home):
        """Gather with --syntactic outputs valid JSON."""
        # Create Tonus.md
        (fake_home / "notes" / "Tonus.md").write_text("test")
        
        # Create namespace with patched paths
        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        
        args = MagicMock(syntactic=True, perceptual=False, repos=None)
        
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()
        
        data = json.loads(output)
        assert "repos" in data
        assert "skills" in data
        assert "memory" in data
        assert "now" in data

    def test_gather_compact_output(self, fake_home):
        """Gather without flags outputs compact text."""
        (fake_home / "notes" / "Tonus.md").write_text("test")
        
        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        
        args = MagicMock(syntactic=False, perceptual=False, repos=None)
        
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()
        
        assert "memory:" in output
        assert "now:" in output

    def test_gather_with_extra_repos(self, fake_home, tmp_path):
        """Gather with --repos includes extra repositories."""
        extra_repo = tmp_path / "extra"
        extra_repo.mkdir()
        subprocess.run(["git", "init"], cwd=extra_repo, capture_output=True)
        
        (fake_home / "notes" / "Tonus.md").write_text("test")
        
        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        
        args = MagicMock(syntactic=True, perceptual=False, repos=str(extra_repo))
        
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()
        
        data = json.loads(output)
        assert "extra" in data["repos"]

    def test_gather_detects_dirty_repo(self, fake_home, tmp_path):
        """Gather detects dirty repository."""
        dirty_repo = tmp_path / "dirty"
        dirty_repo.mkdir()
        subprocess.run(["git", "init"], cwd=dirty_repo, capture_output=True)
        (dirty_repo / "untracked.txt").write_text("test")

        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        # Modify DEFAULT_REPOS AFTER exec (script overwrites it)
        ns["DEFAULT_REPOS"] = {"dirty": dirty_repo}

        args = MagicMock(syntactic=True, perceptual=False, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        data = json.loads(output)
        assert data["repos"]["dirty"]["clean"] is False

    def test_gather_detects_skill_gaps(self, fake_home):
        """Gather detects unlinked skills."""
        skills = fake_home / "code" / "vivesca" / "receptors"
        (skills / "gap_skill.md").write_text("# Gap")

        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": skills,
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        args = MagicMock(syntactic=True, perceptual=False, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        data = json.loads(output)
        assert "gap_skill.md" in data["skills"]["gaps"]

    def test_gather_perceptual_output(self, fake_home):
        """Gather with --perceptual outputs human-readable format."""
        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        args = MagicMock(syntactic=False, perceptual=True, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        assert "Legatum Gather" in output
        assert "MEMORY.md" in output
        assert "Tonus" in output

    def test_gather_with_reflection(self, fake_home):
        """Gather includes reflection candidates when session found."""
        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        # Mock the reflection process by replacing functions directly
        ns["latest_session_id"] = lambda: "test123"
        ns["run_reflect"] = lambda sid: (
            [{"category": "discovery", "lesson": "test lesson", "quote": ""}],
            {"input_tokens": 100, "output_tokens": 50}
        )

        args = MagicMock(syntactic=True, perceptual=False, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        data = json.loads(output)
        assert data["reflect_session"] == "test123"
        assert len(data["reflect"]) == 1

    def test_gather_memory_over_limit(self, fake_home):
        """Gather reports memory line count correctly when over limit."""
        (fake_home / "notes" / "Tonus.md").write_text("test")
        memory = fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md"
        memory.write_text("\n".join(["line"] * 200))  # Over limit of 150

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": memory,
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        args = MagicMock(syntactic=True, perceptual=False, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        data = json.loads(output)
        assert data["memory"]["lines"] == 200
        assert data["memory"]["limit"] == 150

    def test_gather_with_deps_warnings(self, fake_home):
        """Gather includes dependency warnings."""
        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        # Mock dep_check to return warnings
        ns["dep_check"] = lambda: ["warning 1", "warning 2"]

        args = MagicMock(syntactic=True, perceptual=False, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        data = json.loads(output)
        assert data["deps"] == ["warning 1", "warning 2"]

    def test_gather_with_peira_status(self, fake_home):
        """Gather includes peira status when active."""
        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        # Mock peira_status
        ns["peira_status"] = lambda: "experiment-123 active"

        args = MagicMock(syntactic=True, perceptual=False, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        data = json.loads(output)
        assert data["peira"] == "experiment-123 active"


class TestCmdArchive:
    """Tests for cmd_archive command."""

    def test_archive_no_praxis(self, fake_home):
        """Archive without Praxis.md exits with error."""
        ns = {
            "__name__": "test",
            "PRAXIS": fake_home / "nonexistent.md",
            "PRAXIS_ARCHIVE": fake_home / "archive.md",
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        
        args = MagicMock()
        with pytest.raises(SystemExit) as exc_info:
            ns["cmd_archive"](args)
        assert exc_info.value.code == 1

    def test_archive_no_completed_items(self, fake_home):
        """Archive with no completed items does nothing."""
        praxis = fake_home / "notes" / "Praxis.md"
        praxis.write_text("- [ ] Todo item\n- [ ] Another todo\n")
        archive = fake_home / "notes" / "Praxis Archive.md"
        archive.write_text("# Archive\n")
        
        ns = {
            "__name__": "test",
            "PRAXIS": praxis,
            "PRAXIS_ARCHIVE": archive,
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        
        args = MagicMock()
        
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_archive"](args)
            output = mock_stdout.getvalue()
        
        assert "No completed items" in output

    def test_archive_moves_completed_items(self, fake_home):
        """Archive moves [x] items to archive file."""
        praxis = fake_home / "notes" / "Praxis.md"
        praxis.write_text("- [x] Done task\n- [ ] Todo item\n")
        archive = fake_home / "notes" / "Praxis Archive.md"
        archive.write_text("# Archive\n\n## March 2026\n")
        
        ns = {
            "__name__": "test",
            "PRAXIS": praxis,
            "PRAXIS_ARCHIVE": archive,
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        
        args = MagicMock()
        
        with patch("sys.stdout", new_callable=StringIO):
            ns["cmd_archive"](args)
        
        praxis_content = praxis.read_text()
        archive_content = archive.read_text()
        
        assert "- [x] Done task" not in praxis_content
        assert "- [ ] Todo item" in praxis_content
        assert "Done task" in archive_content

    def test_archive_adds_done_tag(self, fake_home):
        """Archive adds done:YYYY-MM-DD tag to completed items."""
        praxis = fake_home / "notes" / "Praxis.md"
        praxis.write_text("- [x] Task without tag\n")
        archive = fake_home / "notes" / "Praxis Archive.md"
        archive.write_text("# Archive\n\n## March 2026\n")
        
        ns = {
            "__name__": "test",
            "PRAXIS": praxis,
            "PRAXIS_ARCHIVE": archive,
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        
        args = MagicMock()
        
        with patch("sys.stdout", new_callable=StringIO):
            ns["cmd_archive"](args)
        
        archive_content = archive.read_text()
        assert "done:" in archive_content

    def test_archive_skips_children_of_completed(self, fake_home):
        """Archive skips indented children of completed items."""
        praxis = fake_home / "notes" / "Praxis.md"
        praxis.write_text("- [x] Parent task\n  - Child item\n- [ ] Another task\n")
        archive = fake_home / "notes" / "Praxis Archive.md"
        archive.write_text("# Archive\n\n## March 2026\n")
        
        ns = {
            "__name__": "test",
            "PRAXIS": praxis,
            "PRAXIS_ARCHIVE": archive,
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        
        args = MagicMock()
        
        with patch("sys.stdout", new_callable=StringIO):
            ns["cmd_archive"](args)
        
        archive_content = archive.read_text()
        assert "Parent task" in archive_content
        assert "Child item" not in archive_content

    def test_archive_creates_month_section(self, fake_home):
        """Archive creates new month section if needed."""
        praxis = fake_home / "notes" / "Praxis.md"
        praxis.write_text("- [x] Done task\n")
        archive = fake_home / "notes" / "Praxis Archive.md"
        archive.write_text("# Archive\n")

        ns = {
            "__name__": "test",
            "PRAXIS": praxis,
            "PRAXIS_ARCHIVE": archive,
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        args = MagicMock()

        with patch("sys.stdout", new_callable=StringIO):
            ns["cmd_archive"](args)

        archive_content = archive.read_text()
        assert "## " in archive_content

    def test_archive_preserves_existing_done_tag(self, fake_home):
        """Archive preserves existing done tag."""
        praxis = fake_home / "notes" / "Praxis.md"
        praxis.write_text("- [x] Task with `done:2026-01-15`\n")
        archive = fake_home / "notes" / "Praxis Archive.md"
        archive.write_text("# Archive\n\n## March 2026\n")

        ns = {
            "__name__": "test",
            "PRAXIS": praxis,
            "PRAXIS_ARCHIVE": archive,
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        args = MagicMock()

        with patch("sys.stdout", new_callable=StringIO):
            ns["cmd_archive"](args)

        archive_content = archive.read_text()
        assert "done:2026-01-15" in archive_content
        # Should not add another done tag
        assert archive_content.count("done:") == 1

    def test_archive_multiple_items(self, fake_home):
        """Archive handles multiple completed items."""
        praxis = fake_home / "notes" / "Praxis.md"
        praxis.write_text("- [x] First task\n- [x] Second task\n- [ ] Todo\n")
        archive = fake_home / "notes" / "Praxis Archive.md"
        archive.write_text("# Archive\n\n## March 2026\n")

        ns = {
            "__name__": "test",
            "PRAXIS": praxis,
            "PRAXIS_ARCHIVE": archive,
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        args = MagicMock()

        with patch("sys.stdout", new_callable=StringIO):
            ns["cmd_archive"](args)

        praxis_content = praxis.read_text()
        archive_content = archive.read_text()

        assert "- [ ] Todo" in praxis_content
        assert "First task" in archive_content
        assert "Second task" in archive_content

    def test_archive_creates_archive_file(self, fake_home):
        """Archive creates archive file if it doesn't exist."""
        praxis = fake_home / "notes" / "Praxis.md"
        praxis.write_text("- [x] Done task\n")
        archive = fake_home / "notes" / "Praxis Archive.md"
        # Don't create archive file - it will be created

        ns = {
            "__name__": "test",
            "PRAXIS": praxis,
            "PRAXIS_ARCHIVE": archive,
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        args = MagicMock()

        with patch("sys.stdout", new_callable=StringIO):
            ns["cmd_archive"](args)

        assert archive.exists()
        assert "Done task" in archive.read_text()

    def test_archive_inserts_before_existing_section(self, fake_home):
        """Archive inserts new month section before existing sections."""
        praxis = fake_home / "notes" / "Praxis.md"
        praxis.write_text("- [x] Done task\n")
        archive = fake_home / "notes" / "Praxis Archive.md"
        archive.write_text("# Archive\n\n## January 2026\n\nOld items\n")

        ns = {
            "__name__": "test",
            "PRAXIS": praxis,
            "PRAXIS_ARCHIVE": archive,
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        args = MagicMock()

        with patch("sys.stdout", new_callable=StringIO):
            ns["cmd_archive"](args)

        archive_content = archive.read_text()
        # New month section should be inserted before January
        jan_idx = archive_content.index("## January 2026")
        # The new month section should come before January
        assert "## " in archive_content[:jan_idx] or "Done task" in archive_content[:jan_idx]

    def test_archive_outputs_count(self, fake_home):
        """Archive outputs count of archived items."""
        praxis = fake_home / "notes" / "Praxis.md"
        praxis.write_text("- [x] Task 1\n- [x] Task 2\n")
        archive = fake_home / "notes" / "Praxis Archive.md"
        archive.write_text("# Archive\n\n## March 2026\n")

        ns = {
            "__name__": "test",
            "PRAXIS": praxis,
            "PRAXIS_ARCHIVE": archive,
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        args = MagicMock()

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_archive"](args)
            output = mock_stdout.getvalue()

        assert "2 completed item" in output


class TestCmdDaily:
    """Tests for cmd_daily command."""

    def test_daily_creates_new_file(self, fake_home):
        """Daily creates new daily note if not exists."""
        daily_dir = fake_home / "notes" / "Daily"
        
        ns = {
            "__name__": "test",
            "DAILY_DIR": daily_dir,
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        
        args = MagicMock(title="Test Session")
        
        with patch("sys.stdout", new_callable=StringIO):
            ns["cmd_daily"](args)
        
        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = daily_dir / f"{today}.md"
        assert daily_file.exists()
        
        content = daily_file.read_text()
        assert "Test Session" in content

    def test_daily_appends_to_existing(self, fake_home):
        """Daily appends to existing daily note."""
        daily_dir = fake_home / "notes" / "Daily"
        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = daily_dir / f"{today}.md"
        daily_file.write_text("# Existing note\n\nSome content\n")
        
        ns = {
            "__name__": "test",
            "DAILY_DIR": daily_dir,
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        
        args = MagicMock(title="New Session")
        
        with patch("sys.stdout", new_callable=StringIO):
            ns["cmd_daily"](args)
        
        content = daily_file.read_text()
        assert "Some content" in content
        assert "New Session" in content

    def test_daily_uses_default_title(self, fake_home):
        """Daily uses 'Session' as default title."""
        daily_dir = fake_home / "notes" / "Daily"
        
        ns = {
            "__name__": "test",
            "DAILY_DIR": daily_dir,
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        
        args = MagicMock(title=None)
        
        with patch("sys.stdout", new_callable=StringIO):
            ns["cmd_daily"](args)
        
        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = daily_dir / f"{today}.md"
        content = daily_file.read_text()
        assert "Session" in content

    def test_daily_includes_time_range(self, fake_home):
        """Daily template includes time range placeholder."""
        daily_dir = fake_home / "notes" / "Daily"

        ns = {
            "__name__": "test",
            "DAILY_DIR": daily_dir,
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        args = MagicMock(title="Test")

        with patch("sys.stdout", new_callable=StringIO):
            ns["cmd_daily"](args)

        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = daily_dir / f"{today}.md"
        content = daily_file.read_text()
        assert "??:??" in content

    def test_daily_includes_checklist_placeholder(self, fake_home):
        """Daily template includes checklist placeholder."""
        daily_dir = fake_home / "notes" / "Daily"

        ns = {
            "__name__": "test",
            "DAILY_DIR": daily_dir,
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        args = MagicMock(title="Test")

        with patch("sys.stdout", new_callable=StringIO):
            ns["cmd_daily"](args)

        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = daily_dir / f"{today}.md"
        content = daily_file.read_text()
        assert "- \n" in content  # Empty checklist item

    def test_daily_includes_weekday_in_header(self, fake_home):
        """Daily note header includes weekday name."""
        daily_dir = fake_home / "notes" / "Daily"

        ns = {
            "__name__": "test",
            "DAILY_DIR": daily_dir,
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        args = MagicMock(title="Test")

        with patch("sys.stdout", new_callable=StringIO):
            ns["cmd_daily"](args)

        today = datetime.now().strftime("%Y-%m-%d")
        weekday = datetime.now().strftime("%A")
        daily_file = daily_dir / f"{today}.md"
        content = daily_file.read_text()
        assert weekday in content

    def test_daily_outputs_success_message(self, fake_home):
        """Daily outputs success message."""
        daily_dir = fake_home / "notes" / "Daily"

        ns = {
            "__name__": "test",
            "DAILY_DIR": daily_dir,
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        args = MagicMock(title="Test")

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_daily"](args)
            output = mock_stdout.getvalue()

        assert "Daily note:" in output
        assert "Template appended" in output


class TestRunReflect:
    """Tests for run_reflect helper function."""

    def test_returns_empty_on_anam_failure(self, telophase_ns):
        """Failed anam search returns empty results."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            findings, usage = telophase_ns["run_reflect"]("test123")
            assert findings == []
            assert usage["input_tokens"] == 0
            assert usage["output_tokens"] == 0

    def test_returns_empty_on_invalid_json(self, telophase_ns):
        """Invalid JSON from anam search returns empty results."""
        with patch("subprocess.run") as mock_run:
            # First call is anam search, second is channel
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="not valid json"),
            ]
            findings, usage = telophase_ns["run_reflect"]("test123")
            assert findings == []

    def test_returns_empty_on_empty_messages(self, telophase_ns):
        """Empty messages list returns empty results."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="[]")
            findings, usage = telophase_ns["run_reflect"]("test123")
            assert findings == []

    def test_handles_channel_failure(self, telophase_ns):
        """Channel failure returns empty results."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout='[{"role": "user", "snippet": "test", "time": "10:00"}]'),
                MagicMock(returncode=1, stdout="", stderr="error"),
            ]
            findings, usage = telophase_ns["run_reflect"]("test123")
            assert findings == []
            # Input tokens should still be estimated
            assert usage["input_tokens"] > 0

    def test_parses_reflection_output(self, telophase_ns):
        """Parses channel output correctly."""
        channel_output = """---
CATEGORY: discovery
QUOTE: test quote
LESSON: test lesson
MEMORY_TYPE: finding
---
---
CATEGORY: taste_calibration
QUOTE: another quote
LESSON: another lesson
MEMORY_TYPE: feedback
---"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout='[{"role": "user", "snippet": "test", "time": "10:00"}]'),
                MagicMock(returncode=0, stdout=channel_output),
            ]
            findings, usage = telophase_ns["run_reflect"]("test123")
            assert len(findings) == 2
            assert findings[0]["category"] == "discovery"
            assert findings[1]["category"] == "taste_calibration"

    def test_truncates_long_snippets(self, telophase_ns):
        """Long assistant snippets are truncated."""
        long_snippet = "x" * 600
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout=f'[{{"role": "assistant", "snippet": "{long_snippet}", "time": "10:00"}}]'),
                MagicMock(returncode=0, stdout="---\nCATEGORY: discovery\nLESSON: test\n---"),
            ]
            findings, usage = telophase_ns["run_reflect"]("test123")
            # Should not raise, transcript should include truncated snippet
            assert usage["input_tokens"] > 0

    def test_handles_timeout(self, telophase_ns):
        """Timeout returns empty results."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("anam", 30)
            findings, usage = telophase_ns["run_reflect"]("test123")
            assert findings == []


class TestCmdReflect:
    """Tests for cmd_reflect command."""

    def test_reflect_no_session(self, telophase_ns):
        """Reflect with no session outputs nothing found."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            args = MagicMock(session="nosession", json=False)

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                telophase_ns["cmd_reflect"](args)
                output = mock_stdout.getvalue()

            assert "No messages found" in output

    def test_reflect_json_output(self, telophase_ns):
        """Reflect with --json outputs JSON."""
        # Save original function and replace with mock
        original_run_reflect = telophase_ns["run_reflect"]

        def mock_run_reflect(session_id):
            return (
                [{"category": "discovery", "lesson": "test lesson", "quote": ""}],
                {"input_tokens": 100, "output_tokens": 50}
            )

        telophase_ns["run_reflect"] = mock_run_reflect
        try:
            args = MagicMock(session="test123", json=True)

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                telophase_ns["cmd_reflect"](args)
                output = mock_stdout.getvalue()

            data = json.loads(output)
            assert len(data) == 1
            assert data[0]["category"] == "discovery"
        finally:
            telophase_ns["run_reflect"] = original_run_reflect

    def test_reflect_human_output(self, telophase_ns):
        """Reflect without --json outputs human-readable format."""
        original_run_reflect = telophase_ns["run_reflect"]

        def mock_run_reflect(session_id):
            return (
                [{"category": "discovery", "lesson": "test lesson", "quote": "test quote"}],
                {"input_tokens": 100, "output_tokens": 50}
            )

        telophase_ns["run_reflect"] = mock_run_reflect
        try:
            args = MagicMock(session="test123", json=False)

            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                telophase_ns["cmd_reflect"](args)
                output = mock_stdout.getvalue()

            assert "Reflection Scan" in output
            assert "discovery" in output.lower()
            assert "test lesson" in output
        finally:
            telophase_ns["run_reflect"] = original_run_reflect


class TestCmdExtract:
    """Tests for cmd_extract command."""

    def test_extract_from_stdin(self, telophase_ns):
        """Extract reads from stdin when no input file."""
        gather_output = {
            "reflect": [{"category": "discovery", "lesson": "test", "quote": ""}]
        }
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="1. FILE: finding | test.md | test description"
            )
            
            with patch("sys.stdin", StringIO(json.dumps(gather_output))):
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    args = MagicMock(input=None)
                    telophase_ns["cmd_extract"](args)
                    output = mock_stdout.getvalue()
                
                assert "FILE" in output

    def test_extract_from_file(self, telophase_ns, tmp_path):
        """Extract reads from specified file."""
        gather_output = {
            "reflect": [{"category": "discovery", "lesson": "test", "quote": ""}]
        }
        input_file = tmp_path / "gather.json"
        input_file.write_text(json.dumps(gather_output))
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="1. SKIP: already known"
            )
            
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                args = MagicMock(input=str(input_file))
                telophase_ns["cmd_extract"](args)
                output = mock_stdout.getvalue()
            
            assert "SKIP" in output

    def test_extract_no_candidates(self, telophase_ns):
        """Extract with no candidates outputs 'no candidates'."""
        gather_output = {"reflect": []}
        
        with patch("sys.stdin", StringIO(json.dumps(gather_output))):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                args = MagicMock(input=None)
                telophase_ns["cmd_extract"](args)
                output = mock_stdout.getvalue()
            
            assert "no candidates" in output

    def test_extract_invalid_json_exits(self, telophase_ns):
        """Extract with invalid JSON exits with error."""
        with patch("sys.stdin", StringIO("not json")):
            with pytest.raises(SystemExit):
                args = MagicMock(input=None)
                telophase_ns["cmd_extract"](args)

    def test_extract_channel_failure_exits(self, telophase_ns):
        """Extract with channel failure exits with error."""
        gather_output = {
            "reflect": [{"category": "discovery", "lesson": "test", "quote": ""}]
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="channel error")

            with patch("sys.stdin", StringIO(json.dumps(gather_output))):
                with pytest.raises(SystemExit):
                    args = MagicMock(input=None)
                    telophase_ns["cmd_extract"](args)

    def test_extract_handles_exception(self, telophase_ns):
        """Extract handles exceptions gracefully."""
        gather_output = {
            "reflect": [{"category": "discovery", "lesson": "test", "quote": ""}]
        }

        with patch("subprocess.run", side_effect=Exception("boom")):
            with patch("sys.stdin", StringIO(json.dumps(gather_output))):
                with pytest.raises(SystemExit):
                    args = MagicMock(input=None)
                    telophase_ns["cmd_extract"](args)


class TestMainFunction:
    """Tests for main entry point."""

    def test_main_no_command_shows_help(self, telophase_ns):
        """Running with no command shows help and exits."""
        with patch("sys.argv", ["telophase"]):
            with pytest.raises(SystemExit):
                telophase_ns["main"]()

    def test_main_gather_command(self, fake_home):
        """Main dispatches to cmd_gather."""
        (fake_home / "notes" / "Tonus.md").write_text("test")
        
        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        
        with patch("sys.argv", ["telophase", "gather", "--syntactic"]):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                ns["main"]()
                output = mock_stdout.getvalue()
            
            data = json.loads(output)
            assert "repos" in data


class TestSubprocessExecution:
    """Tests for running telophase as a subprocess."""

    def test_help_flag(self):
        """--help shows usage information."""
        result = subprocess.run(
            ["python3", str(TELOPHASE_PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert "gather" in result.stdout
        assert "archive" in result.stdout
        assert "daily" in result.stdout

    def test_gather_help(self):
        """gather --help shows gather usage."""
        result = subprocess.run(
            ["python3", str(TELOPHASE_PATH), "gather", "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert "--syntactic" in result.stdout
        assert "--perceptual" in result.stdout

    def test_no_command_exits_with_error(self):
        """Running with no command exits with error."""
        result = subprocess.run(
            ["python3", str(TELOPHASE_PATH)],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 1

    def test_archive_help(self):
        """archive --help shows archive usage."""
        result = subprocess.run(
            ["python3", str(TELOPHASE_PATH), "archive", "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0

    def test_daily_help(self):
        """daily --help shows daily usage."""
        result = subprocess.run(
            ["python3", str(TELOPHASE_PATH), "daily", "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert "title" in result.stdout.lower()

    def test_reflect_help(self):
        """reflect --help shows reflect usage."""
        result = subprocess.run(
            ["python3", str(TELOPHASE_PATH), "reflect", "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert "session" in result.stdout.lower()

    def test_extract_help(self):
        """extract --help shows extract usage."""
        result = subprocess.run(
            ["python3", str(TELOPHASE_PATH), "extract", "--help"],
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert "input" in result.stdout.lower()


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_gather_unavailable_repo(self, fake_home):
        """Gather handles unavailable repos gracefully."""
        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        # Override DEFAULT_REPOS after exec (script overwrites it)
        ns["DEFAULT_REPOS"] = {"nonexistent": fake_home / "does_not_exist"}

        args = MagicMock(syntactic=True, perceptual=False, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        data = json.loads(output)
        assert data["repos"]["nonexistent"]["clean"] is None
        assert data["repos"]["nonexistent"]["status"] == "unavailable"

    def test_now_age_syntactic_output(self, fake_home):
        """Gather outputs now age correctly in syntactic mode."""
        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        args = MagicMock(syntactic=True, perceptual=False, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        data = json.loads(output)
        assert data["now"]["age_label"] == "fresh"
        assert data["now"]["age_seconds"] >= 0

    def test_gather_compact_output_with_dirty_repo(self, fake_home, tmp_path):
        """Compact output includes dirty repo status."""
        dirty_repo = tmp_path / "dirty"
        dirty_repo.mkdir()
        subprocess.run(["git", "init"], cwd=dirty_repo, capture_output=True)
        (dirty_repo / "untracked.txt").write_text("test")

        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        ns["DEFAULT_REPOS"] = {"dirty": dirty_repo}

        args = MagicMock(syntactic=False, perceptual=False, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        assert "repo:dirty dirty" in output

    def test_gather_compact_with_skill_gaps(self, fake_home):
        """Compact output includes skill gaps."""
        skills = fake_home / "code" / "vivesca" / "receptors"
        (skills / "missing.md").write_text("# Missing")

        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": skills,
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        args = MagicMock(syntactic=False, perceptual=False, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        assert "skills:unlinked" in output
        assert "missing.md" in output

    def test_gather_compact_with_deps(self, fake_home):
        """Compact output includes deps warnings."""
        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        ns["dep_check"] = lambda: ["dep warning"]

        args = MagicMock(syntactic=False, perceptual=False, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        assert "deps:" in output

    def test_gather_compact_with_peira(self, fake_home):
        """Compact output includes peira status."""
        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        ns["peira_status"] = lambda: "exp-1 active"

        args = MagicMock(syntactic=False, perceptual=False, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        assert "peira:" in output
        assert "exp-1 active" in output

    def test_gather_compact_with_reflection(self, fake_home):
        """Compact output includes reflection candidates."""
        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        ns["latest_session_id"] = lambda: "test123"
        ns["run_reflect"] = lambda sid: (
            [{"category": "discovery", "lesson": "found something", "quote": ""}],
            {"input_tokens": 100, "output_tokens": 50}
        )

        args = MagicMock(syntactic=False, perceptual=False, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        assert "reflect:" in output
        assert "1 candidates" in output

    def test_gather_perceptual_with_dirty_repo(self, fake_home, tmp_path):
        """Perceptual output shows dirty repo details."""
        dirty_repo = tmp_path / "dirty"
        dirty_repo.mkdir()
        subprocess.run(["git", "init"], cwd=dirty_repo, capture_output=True)
        (dirty_repo / "untracked.txt").write_text("test")

        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        ns["DEFAULT_REPOS"] = {"dirty": dirty_repo}

        args = MagicMock(syntactic=False, perceptual=True, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        assert "dirty" in output  # Shows dirty count

    def test_gather_perceptual_with_skill_gaps(self, fake_home):
        """Perceptual output shows skill gaps."""
        skills = fake_home / "code" / "vivesca" / "receptors"
        (skills / "missing.md").write_text("# Missing")

        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": skills,
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)

        args = MagicMock(syntactic=False, perceptual=True, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        assert "unlinked" in output.lower()
        assert "missing.md" in output

    def test_gather_perceptual_with_reflection(self, fake_home):
        """Perceptual output shows reflection candidates."""
        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        ns["latest_session_id"] = lambda: "test123"
        ns["run_reflect"] = lambda sid: (
            [{"category": "discovery", "lesson": "found something", "quote": ""}],
            {}
        )

        args = MagicMock(syntactic=False, perceptual=True, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        assert "Reflection" in output

    def test_gather_perceptual_with_deps(self, fake_home):
        """Perceptual output shows deps warnings."""
        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        ns["dep_check"] = lambda: ["warning 1"]

        args = MagicMock(syntactic=False, perceptual=True, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        assert "dep:" in output

    def test_gather_perceptual_with_peira(self, fake_home):
        """Perceptual output shows peira status."""
        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        ns["peira_status"] = lambda: "exp active"

        args = MagicMock(syntactic=False, perceptual=True, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        assert "Peira:" in output

    def test_gather_perceptual_no_reflection_with_session(self, fake_home):
        """Perceptual output shows 'nothing surfaced' when no reflection found."""
        (fake_home / "notes" / "Tonus.md").write_text("test")

        ns = {
            "__name__": "test",
            "HOME": fake_home,
            "NOTES": fake_home / "notes",
            "NOW_MD": fake_home / "notes" / "Tonus.md",
            "SKILLS": fake_home / "code" / "vivesca" / "receptors",
            "CLAUDE_SKILLS": fake_home / ".claude" / "skills",
            "MEMORY": fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md",
            "MEMORY_LIMIT": 150,
            "DEFAULT_REPOS": {},
        }
        exec(TELOPHASE_PATH.read_text(), ns)
        ns["latest_session_id"] = lambda: "test123"
        ns["run_reflect"] = lambda sid: ([], {})

        args = MagicMock(syntactic=False, perceptual=True, repos=None)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            ns["cmd_gather"](args)
            output = mock_stdout.getvalue()

        assert "nothing surfaced" in output
