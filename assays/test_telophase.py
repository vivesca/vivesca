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
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

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

    def test_returns_missing_when_file_not_found(self, telophase_ns, fake_home):
        """Missing Tonus.md returns ('missing', -1)."""
        with patch.object(telophase_ns, "NOW_MD", fake_home / "notes" / "Tonus.md"):
            label, secs = telophase_ns["now_age"]()
            assert label == "missing"
            assert secs == -1

    def test_returns_fresh_when_recent(self, telophase_ns, fake_home):
        """File modified < 15 min ago returns ('fresh', seconds)."""
        now_md = fake_home / "notes" / "Tonus.md"
        now_md.write_text("test")
        
        with patch.object(telophase_ns, "NOW_MD", now_md):
            label, secs = telophase_ns["now_age"]()
            assert label == "fresh"
            assert 0 <= secs < 900

    def test_returns_recent_when_older(self, telophase_ns, fake_home):
        """File modified 15-60 min ago returns ('recent', seconds)."""
        now_md = fake_home / "notes" / "Tonus.md"
        now_md.write_text("test")
        # Set mtime to 30 minutes ago
        old_time = time.time() - 1800
        os.utime(now_md, (old_time, old_time))
        
        with patch.object(telophase_ns, "NOW_MD", now_md):
            label, secs = telophase_ns["now_age"]()
            assert label == "recent"
            assert 900 <= secs < 3600

    def test_returns_stale_when_hour_old(self, telophase_ns, fake_home):
        """File modified 1-24 hours ago returns ('stale', seconds)."""
        now_md = fake_home / "notes" / "Tonus.md"
        now_md.write_text("test")
        # Set mtime to 2 hours ago
        old_time = time.time() - 7200
        os.utime(now_md, (old_time, old_time))
        
        with patch.object(telophase_ns, "NOW_MD", now_md):
            label, secs = telophase_ns["now_age"]()
            assert label == "stale"
            assert 3600 <= secs < 86400

    def test_returns_very_stale_when_day_old(self, telophase_ns, fake_home):
        """File modified > 24 hours ago returns ('very stale', seconds)."""
        now_md = fake_home / "notes" / "Tonus.md"
        now_md.write_text("test")
        # Set mtime to 2 days ago
        old_time = time.time() - 172800
        os.utime(now_md, (old_time, old_time))
        
        with patch.object(telophase_ns, "NOW_MD", now_md):
            label, secs = telophase_ns["now_age"]()
            assert label == "very stale"
            assert secs >= 86400


class TestMemoryLines:
    """Tests for memory_lines helper function."""

    def test_returns_zero_when_file_not_found(self, telophase_ns, fake_home):
        """Missing MEMORY.md returns 0."""
        memory = fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md"
        
        with patch.object(telophase_ns, "MEMORY", memory):
            assert telophase_ns["memory_lines"]() == 0

    def test_counts_lines_correctly(self, telophase_ns, fake_home):
        """Returns correct line count."""
        memory = fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md"
        memory.write_text("line1\nline2\nline3\n")
        
        with patch.object(telophase_ns, "MEMORY", memory):
            assert telophase_ns["memory_lines"]() == 3

    def test_counts_empty_file_as_zero(self, telophase_ns, fake_home):
        """Empty file returns 0."""
        memory = fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md"
        memory.write_text("")
        
        with patch.object(telophase_ns, "MEMORY", memory):
            assert telophase_ns["memory_lines"]() == 0


class TestSkillGaps:
    """Tests for skill_gaps helper function."""

    def test_returns_empty_when_no_skills(self, telophase_ns, fake_home):
        """No skills in receptors dir returns empty list."""
        skills = fake_home / "code" / "vivesca" / "receptors"
        claude_skills = fake_home / ".claude" / "skills"
        
        with patch.object(telophase_ns, "SKILLS", skills):
            with patch.object(telophase_ns, "CLAUDE_SKILLS", claude_skills):
                assert telophase_ns["skill_gaps"]() == []

    def test_returns_gap_when_not_linked(self, telophase_ns, fake_home):
        """Skill without symlink in .claude/skills is a gap."""
        skills = fake_home / "code" / "vivesca" / "receptors"
        claude_skills = fake_home / ".claude" / "skills"
        
        # Create a skill file
        (skills / "test_skill.md").write_text("# Test Skill")
        
        with patch.object(telophase_ns, "SKILLS", skills):
            with patch.object(telophase_ns, "CLAUDE_SKILLS", claude_skills):
                gaps = telophase_ns["skill_gaps"]()
                assert "test_skill.md" in gaps

    def test_returns_empty_when_all_linked(self, telophase_ns, fake_home):
        """All skills linked returns empty list."""
        skills = fake_home / "code" / "vivesca" / "receptors"
        claude_skills = fake_home / ".claude" / "skills"
        
        # Create a skill and its symlink
        (skills / "linked_skill.md").write_text("# Linked")
        (claude_skills / "linked_skill.md").symlink_to(skills / "linked_skill.md")
        
        with patch.object(telophase_ns, "SKILLS", skills):
            with patch.object(telophase_ns, "CLAUDE_SKILLS", claude_skills):
                assert telophase_ns["skill_gaps"]() == []

    def test_ignores_hidden_files(self, telophase_ns, fake_home):
        """Hidden files are ignored in gap detection."""
        skills = fake_home / "code" / "vivesca" / "receptors"
        claude_skills = fake_home / ".claude" / "skills"
        
        # Create hidden file
        (skills / ".hidden").write_text("hidden")
        
        with patch.object(telophase_ns, "SKILLS", skills):
            with patch.object(telophase_ns, "CLAUDE_SKILLS", claude_skills):
                assert telophase_ns["skill_gaps"]() == []

    def test_returns_sorted_gaps(self, telophase_ns, fake_home):
        """Gaps are returned in sorted order."""
        skills = fake_home / "code" / "vivesca" / "receptors"
        claude_skills = fake_home / ".claude" / "skills"
        
        # Create multiple skills in non-alphabetical order
        for name in ["z_skill.md", "a_skill.md", "m_skill.md"]:
            (skills / name).write_text(f"# {name}")
        
        with patch.object(telophase_ns, "SKILLS", skills):
            with patch.object(telophase_ns, "CLAUDE_SKILLS", claude_skills):
                gaps = telophase_ns["skill_gaps"]()
                assert gaps == ["a_skill.md", "m_skill.md", "z_skill.md"]

    def test_handles_missing_skills_dir(self, telophase_ns, fake_home):
        """Missing skills directory returns empty list."""
        skills = fake_home / "nonexistent"
        claude_skills = fake_home / ".claude" / "skills"
        
        with patch.object(telophase_ns, "SKILLS", skills):
            with patch.object(telophase_ns, "CLAUDE_SKILLS", claude_skills):
                assert telophase_ns["skill_gaps"]() == []


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
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="[first123] old session\n[last456] current session\n"
            )
            assert telophase_ns["latest_session_id"]() == "last456"

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

    def test_gather_syntactic_output(self, telophase_ns, fake_home):
        """Gather with --syntactic outputs valid JSON."""
        # Patch all paths
        with patch.object(telophase_ns, "HOME", fake_home):
            with patch.object(telophase_ns, "NOTES", fake_home / "notes"):
                with patch.object(telophase_ns, "NOW_MD", fake_home / "notes" / "Tonus.md"):
                    with patch.object(telophase_ns, "SKILLS", fake_home / "code" / "vivesca" / "receptors"):
                        with patch.object(telophase_ns, "CLAUDE_SKILLS", fake_home / ".claude" / "skills"):
                            with patch.object(telophase_ns, "MEMORY", fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md"):
                                with patch.object(telophase_ns, "DEFAULT_REPOS", {}):
                                    # Create Tonus.md for now_age
                                    (fake_home / "notes" / "Tonus.md").write_text("test")
                                    
                                    args = MagicMock(syntactic=True, perceptual=False, repos=None)
                                    
                                    # Capture stdout
                                    from io import StringIO
                                    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                                        telophase_ns["cmd_gather"](args)
                                        output = mock_stdout.getvalue()
                                    
                                    # Should be valid JSON
                                    data = json.loads(output)
                                    assert "repos" in data
                                    assert "skills" in data
                                    assert "memory" in data
                                    assert "now" in data

    def test_gather_compact_output(self, telophase_ns, fake_home):
        """Gather without flags outputs compact text."""
        with patch.object(telophase_ns, "HOME", fake_home):
            with patch.object(telophase_ns, "NOTES", fake_home / "notes"):
                with patch.object(telophase_ns, "NOW_MD", fake_home / "notes" / "Tonus.md"):
                    with patch.object(telophase_ns, "SKILLS", fake_home / "code" / "vivesca" / "receptors"):
                        with patch.object(telophase_ns, "CLAUDE_SKILLS", fake_home / ".claude" / "skills"):
                            with patch.object(telophase_ns, "MEMORY", fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md"):
                                with patch.object(telophase_ns, "DEFAULT_REPOS", {}):
                                    (fake_home / "notes" / "Tonus.md").write_text("test")
                                    
                                    args = MagicMock(syntactic=False, perceptual=False, repos=None)
                                    
                                    from io import StringIO
                                    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                                        telophase_ns["cmd_gather"](args)
                                        output = mock_stdout.getvalue()
                                    
                                    # Should have compact format
                                    assert "memory:" in output
                                    assert "now:" in output

    def test_gather_with_extra_repos(self, telophase_ns, fake_home, tmp_path):
        """Gather with --repos includes extra repositories."""
        extra_repo = tmp_path / "extra"
        extra_repo.mkdir()
        subprocess.run(["git", "init"], cwd=extra_repo, capture_output=True)
        
        with patch.object(telophase_ns, "HOME", fake_home):
            with patch.object(telophase_ns, "NOTES", fake_home / "notes"):
                with patch.object(telophase_ns, "NOW_MD", fake_home / "notes" / "Tonus.md"):
                    with patch.object(telophase_ns, "SKILLS", fake_home / "code" / "vivesca" / "receptors"):
                        with patch.object(telophase_ns, "CLAUDE_SKILLS", fake_home / ".claude" / "skills"):
                            with patch.object(telophase_ns, "MEMORY", fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md"):
                                with patch.object(telophase_ns, "DEFAULT_REPOS", {}):
                                    (fake_home / "notes" / "Tonus.md").write_text("test")
                                    
                                    args = MagicMock(syntactic=True, perceptual=False, repos=str(extra_repo))
                                    
                                    from io import StringIO
                                    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                                        telophase_ns["cmd_gather"](args)
                                        output = mock_stdout.getvalue()
                                    
                                    data = json.loads(output)
                                    assert "extra" in data["repos"]

    def test_gather_detects_dirty_repo(self, telophase_ns, fake_home, tmp_path):
        """Gather detects dirty repository."""
        dirty_repo = tmp_path / "dirty"
        dirty_repo.mkdir()
        subprocess.run(["git", "init"], cwd=dirty_repo, capture_output=True)
        (dirty_repo / "untracked.txt").write_text("test")
        
        with patch.object(telophase_ns, "HOME", fake_home):
            with patch.object(telophase_ns, "NOTES", fake_home / "notes"):
                with patch.object(telophase_ns, "NOW_MD", fake_home / "notes" / "Tonus.md"):
                    with patch.object(telophase_ns, "SKILLS", fake_home / "code" / "vivesca" / "receptors"):
                        with patch.object(telophase_ns, "CLAUDE_SKILLS", fake_home / ".claude" / "skills"):
                            with patch.object(telophase_ns, "MEMORY", fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md"):
                                with patch.object(telophase_ns, "DEFAULT_REPOS", {"dirty": dirty_repo}):
                                    (fake_home / "notes" / "Tonus.md").write_text("test")
                                    
                                    args = MagicMock(syntactic=True, perceptual=False, repos=None)
                                    
                                    from io import StringIO
                                    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                                        telophase_ns["cmd_gather"](args)
                                        output = mock_stdout.getvalue()
                                    
                                    data = json.loads(output)
                                    assert data["repos"]["dirty"]["clean"] is False

    def test_gather_detects_skill_gaps(self, telophase_ns, fake_home):
        """Gather detects unlinked skills."""
        skills = fake_home / "code" / "vivesca" / "receptors"
        (skills / "gap_skill.md").write_text("# Gap")
        
        with patch.object(telophase_ns, "HOME", fake_home):
            with patch.object(telophase_ns, "NOTES", fake_home / "notes"):
                with patch.object(telophase_ns, "NOW_MD", fake_home / "notes" / "Tonus.md"):
                    with patch.object(telophase_ns, "SKILLS", skills):
                        with patch.object(telophase_ns, "CLAUDE_SKILLS", fake_home / ".claude" / "skills"):
                            with patch.object(telophase_ns, "MEMORY", fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md"):
                                with patch.object(telophase_ns, "DEFAULT_REPOS", {}):
                                    (fake_home / "notes" / "Tonus.md").write_text("test")
                                    
                                    args = MagicMock(syntactic=True, perceptual=False, repos=None)
                                    
                                    from io import StringIO
                                    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                                        telophase_ns["cmd_gather"](args)
                                        output = mock_stdout.getvalue()
                                    
                                    data = json.loads(output)
                                    assert "gap_skill.md" in data["skills"]["gaps"]


class TestCmdArchive:
    """Tests for cmd_archive command."""

    def test_archive_no_praxis(self, telophase_ns, fake_home):
        """Archive without Praxis.md exits with error."""
        with patch.object(telophase_ns, "PRAXIS", fake_home / "nonexistent.md"):
            with patch.object(telophase_ns, "PRAXIS_ARCHIVE", fake_home / "archive.md"):
                args = MagicMock()
                with pytest.raises(SystemExit) as exc_info:
                    telophase_ns["cmd_archive"](args)
                assert exc_info.value.code == 1

    def test_archive_no_completed_items(self, telophase_ns, fake_home):
        """Archive with no completed items does nothing."""
        praxis = fake_home / "notes" / "Praxis.md"
        praxis.write_text("- [ ] Todo item\n- [ ] Another todo\n")
        archive = fake_home / "notes" / "Praxis Archive.md"
        archive.write_text("# Archive\n")
        
        with patch.object(telophase_ns, "PRAXIS", praxis):
            with patch.object(telophase_ns, "PRAXIS_ARCHIVE", archive):
                args = MagicMock()
                
                from io import StringIO
                with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                    telophase_ns["cmd_archive"](args)
                    output = mock_stdout.getvalue()
                
                assert "No completed items" in output

    def test_archive_moves_completed_items(self, telophase_ns, fake_home):
        """Archive moves [x] items to archive file."""
        praxis = fake_home / "notes" / "Praxis.md"
        praxis.write_text("- [x] Done task\n- [ ] Todo item\n")
        archive = fake_home / "notes" / "Praxis Archive.md"
        archive.write_text("# Archive\n\n## March 2026\n")
        
        with patch.object(telophase_ns, "PRAXIS", praxis):
            with patch.object(telophase_ns, "PRAXIS_ARCHIVE", archive):
                args = MagicMock()
                
                from io import StringIO
                with patch("sys.stdout", new_callable=StringIO):
                    telophase_ns["cmd_archive"](args)
                
                # Check items moved
                praxis_content = praxis.read_text()
                archive_content = archive.read_text()
                
                assert "- [x] Done task" not in praxis_content
                assert "- [ ] Todo item" in praxis_content
                assert "Done task" in archive_content

    def test_archive_adds_done_tag(self, telophase_ns, fake_home):
        """Archive adds done:YYYY-MM-DD tag to completed items."""
        praxis = fake_home / "notes" / "Praxis.md"
        praxis.write_text("- [x] Task without tag\n")
        archive = fake_home / "notes" / "Praxis Archive.md"
        archive.write_text("# Archive\n\n## March 2026\n")
        
        with patch.object(telophase_ns, "PRAXIS", praxis):
            with patch.object(telophase_ns, "PRAXIS_ARCHIVE", archive):
                args = MagicMock()
                
                from io import StringIO
                with patch("sys.stdout", new_callable=StringIO):
                    telophase_ns["cmd_archive"](args)
                
                archive_content = archive.read_text()
                assert "done:" in archive_content

    def test_archive_skips_children_of_completed(self, telophase_ns, fake_home):
        """Archive skips indented children of completed items."""
        praxis = fake_home / "notes" / "Praxis.md"
        praxis.write_text("- [x] Parent task\n  - Child item\n- [ ] Another task\n")
        archive = fake_home / "notes" / "Praxis Archive.md"
        archive.write_text("# Archive\n\n## March 2026\n")
        
        with patch.object(telophase_ns, "PRAXIS", praxis):
            with patch.object(telophase_ns, "PRAXIS_ARCHIVE", archive):
                args = MagicMock()
                
                from io import StringIO
                with patch("sys.stdout", new_callable=StringIO):
                    telophase_ns["cmd_archive"](args)
                
                archive_content = archive.read_text()
                # Parent should be in archive
                assert "Parent task" in archive_content
                # Child should NOT be in archive
                assert "Child item" not in archive_content

    def test_archive_creates_month_section(self, telophase_ns, fake_home):
        """Archive creates new month section if needed."""
        praxis = fake_home / "notes" / "Praxis.md"
        praxis.write_text("- [x] Done task\n")
        archive = fake_home / "notes" / "Praxis Archive.md"
        archive.write_text("# Archive\n")
        
        with patch.object(telophase_ns, "PRAXIS", praxis):
            with patch.object(telophase_ns, "PRAXIS_ARCHIVE", archive):
                args = MagicMock()
                
                from io import StringIO
                with patch("sys.stdout", new_callable=StringIO):
                    telophase_ns["cmd_archive"](args)
                
                archive_content = archive.read_text()
                # Should have a month header
                assert "## " in archive_content


class TestCmdDaily:
    """Tests for cmd_daily command."""

    def test_daily_creates_new_file(self, telophase_ns, fake_home):
        """Daily creates new daily note if not exists."""
        daily_dir = fake_home / "notes" / "Daily"
        
        with patch.object(telophase_ns, "DAILY_DIR", daily_dir):
            args = MagicMock(title="Test Session")
            
            from io import StringIO
            with patch("sys.stdout", new_callable=StringIO):
                telophase_ns["cmd_daily"](args)
            
            # Find the created file
            today = datetime.now().strftime("%Y-%m-%d")
            daily_file = daily_dir / f"{today}.md"
            assert daily_file.exists()
            
            content = daily_file.read_text()
            assert "Test Session" in content

    def test_daily_appends_to_existing(self, telophase_ns, fake_home):
        """Daily appends to existing daily note."""
        daily_dir = fake_home / "notes" / "Daily"
        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = daily_dir / f"{today}.md"
        daily_file.write_text("# Existing note\n\nSome content\n")
        
        with patch.object(telophase_ns, "DAILY_DIR", daily_dir):
            args = MagicMock(title="New Session")
            
            from io import StringIO
            with patch("sys.stdout", new_callable=StringIO):
                telophase_ns["cmd_daily"](args)
            
            content = daily_file.read_text()
            assert "Existing content" in content
            assert "New Session" in content

    def test_daily_uses_default_title(self, telophase_ns, fake_home):
        """Daily uses 'Session' as default title."""
        daily_dir = fake_home / "notes" / "Daily"
        
        with patch.object(telophase_ns, "DAILY_DIR", daily_dir):
            args = MagicMock(title=None)
            
            from io import StringIO
            with patch("sys.stdout", new_callable=StringIO):
                telophase_ns["cmd_daily"](args)
            
            today = datetime.now().strftime("%Y-%m-%d")
            daily_file = daily_dir / f"{today}.md"
            content = daily_file.read_text()
            assert "Session" in content

    def test_daily_includes_time_range(self, telophase_ns, fake_home):
        """Daily template includes time range placeholder."""
        daily_dir = fake_home / "notes" / "Daily"
        
        with patch.object(telophase_ns, "DAILY_DIR", daily_dir):
            args = MagicMock(title="Test")
            
            from io import StringIO
            with patch("sys.stdout", new_callable=StringIO):
                telophase_ns["cmd_daily"](args)
            
            today = datetime.now().strftime("%Y-%m-%d")
            daily_file = daily_dir / f"{today}.md"
            content = daily_file.read_text()
            # Should have time range format
            assert "??:??" in content


class TestCmdReflect:
    """Tests for cmd_reflect command."""

    def test_reflect_no_session(self, telophase_ns):
        """Reflect with no session outputs nothing found."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            args = MagicMock(session="nosession", json=False)
            
            from io import StringIO
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                telophase_ns["cmd_reflect"](args)
                output = mock_stdout.getvalue()
            
            assert "No messages found" in output

    def test_reflect_json_output(self, telophase_ns):
        """Reflect with --json outputs JSON."""
        with patch.object(telophase_ns, "run_reflect") as mock_reflect:
            mock_reflect.return_value = (
                [{"category": "discovery", "lesson": "test lesson"}],
                {"input_tokens": 100, "output_tokens": 50}
            )
            args = MagicMock(session="test123", json=True)
            
            from io import StringIO
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                telophase_ns["cmd_reflect"](args)
                output = mock_stdout.getvalue()
            
            data = json.loads(output)
            assert len(data) == 1
            assert data[0]["category"] == "discovery"


class TestCmdExtract:
    """Tests for cmd_extract command."""

    def test_extract_from_stdin(self, telophase_ns):
        """Extract reads from stdin when no input file."""
        gather_output = {
            "reflect": [{"category": "discovery", "lesson": "test", "quote": ""}]
        }
        
        with patch.object(telophase_ns, "run_reflect", return_value=([], {})):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="1. FILE: finding | test.md | test description"
                )
                
                from io import StringIO
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
            
            from io import StringIO
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                args = MagicMock(input=str(input_file))
                telophase_ns["cmd_extract"](args)
                output = mock_stdout.getvalue()
            
            assert "SKIP" in output

    def test_extract_no_candidates(self, telophase_ns):
        """Extract with no candidates outputs 'no candidates'."""
        gather_output = {"reflect": []}
        
        from io import StringIO
        with patch("sys.stdin", StringIO(json.dumps(gather_output))):
            with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                args = MagicMock(input=None)
                telophase_ns["cmd_extract"](args)
                output = mock_stdout.getvalue()
            
            assert "no candidates" in output

    def test_extract_invalid_json_exits(self, telophase_ns):
        """Extract with invalid JSON exits with error."""
        from io import StringIO
        with patch("sys.stdin", StringIO("not json")):
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

    def test_main_gather_command(self, telophase_ns, fake_home):
        """Main dispatches to cmd_gather."""
        with patch.object(telophase_ns, "HOME", fake_home):
            with patch.object(telophase_ns, "NOTES", fake_home / "notes"):
                with patch.object(telophase_ns, "NOW_MD", fake_home / "notes" / "Tonus.md"):
                    with patch.object(telophase_ns, "SKILLS", fake_home / "code" / "vivesca" / "receptors"):
                        with patch.object(telophase_ns, "CLAUDE_SKILLS", fake_home / ".claude" / "skills"):
                            with patch.object(telophase_ns, "MEMORY", fake_home / ".claude" / "projects" / "-Users-terry" / "memory" / "MEMORY.md"):
                                with patch.object(telophase_ns, "DEFAULT_REPOS", {}):
                                    (fake_home / "notes" / "Tonus.md").write_text("test")
                                    
                                    with patch("sys.argv", ["telophase", "gather", "--syntactic"]):
                                        from io import StringIO
                                        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
                                            telophase_ns["main"]()
                                            output = mock_stdout.getvalue()
                                        
                                        # Should output JSON
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
