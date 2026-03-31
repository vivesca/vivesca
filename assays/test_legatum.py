"""Tests for effectors/legatum (telophase) - Deterministic session-close gathering."""

import os
import json
import sys
import subprocess
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
from pathlib import Path

import pytest

# Add the effectors directory to path so we can import legatum/telophase
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'effectors'))

# Since legatum is a symlink to telophase, import from telophase
import telophase as legatum


# ──────────────────────────────────────────────────────────────────────────────
# git_status tests
# ──────────────────────────────────────────────────────────────────────────────

def test_git_status_clean_repo():
    """Test git_status returns empty string for clean repo."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr=""
        )
        result = legatum.git_status(Path("/fake/repo"))
        assert result == ""
        mock_run.assert_called_once()


def test_git_status_dirty_repo():
    """Test git_status returns status for dirty repo."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=" M file.py\n?? new.py",
            stderr=""
        )
        result = legatum.git_status(Path("/fake/repo"))
        assert result == " M file.py\n?? new.py"
        mock_run.assert_called_once()


def test_git_status_not_a_repo():
    """Test git_status returns None when not a git repo."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="fatal: not a git repository"
        )
        result = legatum.git_status(Path("/fake/repo"))
        assert result is None


def test_git_status_exception():
    """Test git_status returns None on exception."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = legatum.git_status(Path("/fake/repo"))
        assert result is None


def test_git_status_timeout():
    """Test git_status returns None on timeout."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(["git"], 10)
        result = legatum.git_status(Path("/fake/repo"))
        assert result is None


# ──────────────────────────────────────────────────────────────────────────────
# now_age tests
# ──────────────────────────────────────────────────────────────────────────────

def test_now_age_fresh():
    """Test now_age categorizes fresh (<15min)."""
    current_time = 1000000
    mtime = current_time - 500  # 8m20s ago

    with patch('os.path.getmtime') as mock_mtime:
        mock_mtime.return_value = mtime
        with patch('time.time') as mock_time:
            mock_time.return_value = current_time
            label, age = legatum.now_age()
            assert label == "fresh"
            assert age == 500


def test_now_age_recent():
    """Test now_age categorizes recent (<1hr)."""
    current_time = 1000000
    mtime = current_time - 2000  # ~33min ago

    with patch('os.path.getmtime') as mock_mtime:
        mock_mtime.return_value = mtime
        with patch('time.time') as mock_time:
            mock_time.return_value = current_time
            label, age = legatum.now_age()
            assert label == "recent"
            assert age == 2000


def test_now_age_stale():
    """Test now_age categorizes stale (<1day)."""
    current_time = 1000000
    mtime = current_time - 3600 * 6  # 6 hours ago

    with patch('os.path.getmtime') as mock_mtime:
        mock_mtime.return_value = mtime
        with patch('time.time') as mock_time:
            mock_time.return_value = current_time
            label, age = legatum.now_age()
            assert label == "stale"
            assert age == 21600


def test_now_age_very_stale():
    """Test now_age categorizes very stale (>1day)."""
    current_time = 1000000
    mtime = current_time - 86400 * 2  # 2 days ago

    with patch('os.path.getmtime') as mock_mtime:
        mock_mtime.return_value = mtime
        with patch('time.time') as mock_time:
            mock_time.return_value = current_time
            label, age = legatum.now_age()
            assert label == "very stale"
            assert age == 172800


def test_now_age_missing():
    """Test now_age returns missing when file not found."""
    with patch('os.path.getmtime') as mock_mtime:
        mock_mtime.side_effect = FileNotFoundError()
        label, age = legatum.now_age()
        assert label == "missing"
        assert age == -1


# ──────────────────────────────────────────────────────────────────────────────
# memory_lines tests
# ──────────────────────────────────────────────────────────────────────────────

def test_memory_lines_counts_lines():
    """Test memory_lines counts lines correctly."""
    mock_data = "line1\nline2\nline3\n"
    with patch('builtins.open', mock_open(read_data=mock_data)):
        result = legatum.memory_lines()
        assert result == 3


def test_memory_lines_missing():
    """Test memory_lines returns 0 when file not found."""
    with patch('builtins.open') as mock_open_obj:
        mock_open_obj.side_effect = FileNotFoundError()
        result = legatum.memory_lines()
        assert result == 0


# ──────────────────────────────────────────────────────────────────────────────
# skill_gaps tests
# ──────────────────────────────────────────────────────────────────────────────

def test_skill_gaps_finds_unlinked_skills():
    """Test skill_gaps returns skills in SKILLS not in CLAUDE_SKILLS."""
    skills_dir = ["skill1", "skill2", ".hidden", "skill3"]
    claude_dir = ["skill1", ".DS_Store", "skill4"]

    with patch('os.listdir') as mock_listdir:
        mock_listdir.side_effect = [skills_dir, claude_dir]
        result = legatum.skill_gaps()
        assert sorted(result) == ["skill2", "skill3"]


def test_skill_gaps_empty_when_all_synced():
    """Test skill_gaps returns empty when all skills are linked."""
    skills_dir = ["skill1", "skill2"]
    claude_dir = ["skill1", "skill2"]

    with patch('os.listdir') as mock_listdir:
        mock_listdir.side_effect = [skills_dir, claude_dir]
        result = legatum.skill_gaps()
        assert result == []


def test_skill_gaps_handles_missing_directory():
    """Test skill_gaps returns empty list when directory not found."""
    with patch('os.listdir') as mock_listdir:
        mock_listdir.side_effect = FileNotFoundError()
        result = legatum.skill_gaps()
        assert result == []


# ──────────────────────────────────────────────────────────────────────────────
# dep_check tests
# ──────────────────────────────────────────────────────────────────────────────

def test_dep_check_returns_warnings():
    """Test dep_check returns warnings from proteostasis."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="warning: dep1 out of date\nwarning: dep2 missing\n",
            stderr=""
        )
        result = legatum.dep_check()
        assert result == ["warning: dep1 out of date", "warning: dep2 missing"]


def test_dep_check_empty_on_error():
    """Test dep_check returns empty when proteostasis fails."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="command not found"
        )
        result = legatum.dep_check()
        assert result == []


def test_dep_check_empty_on_exception():
    """Test dep_check returns empty on exception."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = legatum.dep_check()
        assert result == []


# ──────────────────────────────────────────────────────────────────────────────
# peira_status tests
# ──────────────────────────────────────────────────────────────────────────────

def test_peira_status_returns_active_info():
    """Test peira_status returns active experiment info."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="experiment: test-exp\nstage: running\n",
            stderr=""
        )
        result = legatum.peira_status()
        assert result == "experiment: test-exp\nstage: running"


def test_peira_status_none_when_no_output():
    """Test peira_status returns None when no output."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr=""
        )
        result = legatum.peira_status()
        assert result is None


def test_peira_status_none_on_error():
    """Test peira_status returns None on error."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="error"
        )
        result = legatum.peira_status()
        assert result is None


# ──────────────────────────────────────────────────────────────────────────────
# latest_session_id tests
# ──────────────────────────────────────────────────────────────────────────────

def test_latest_session_id_extracts_from_today():
    """Test latest_session_id extracts last session ID from anam today."""
    output = """some line
[abc123] 15 prompts (12:34) - Claude
another line"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=output,
            stderr=""
        )
        result = legatum.latest_session_id()
        assert result == "abc123"


def test_latest_session_id_none_when_no_match():
    """Test latest_session_id returns None when no session ID found."""
    output = """no session here
nothing matches"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=output,
            stderr=""
        )
        result = legatum.latest_session_id()
        assert result is None


def test_latest_session_id_none_on_error():
    """Test latest_session_id returns None on error."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="error"
        )
        result = legatum.latest_session_id()
        assert result is None


# ──────────────────────────────────────────────────────────────────────────────
# cmd_archive tests
# ──────────────────────────────────────────────────────────────────────────────

def test_cmd_archive_no_praxis_file(capsys):
    """Test cmd_archive exits when Praxis.md not found."""
    with patch.object(legatum.PRAXIS, 'exists', return_value=False):
        with pytest.raises(SystemExit):
            args = MagicMock()
            legatum.cmd_archive(args)
        captured = capsys.readouterr()
        assert "No Praxis.md found" in captured.err


def test_cmd_archive_no_completed_items(capsys, tmp_path):
    """Test cmd_archive reports no completed items to archive."""
    praxis_content = """- [ ] item 1
- [ ] item 2
  - [ ] subitem
"""
    praxis_path = tmp_path / "Praxis.md"
    praxis_path.write_text(praxis_content)
    archive_path = tmp_path / "Praxis Archive.md"

    with patch.object(legatum, 'PRAXIS', praxis_path):
        with patch.object(legatum, 'PRAXIS_ARCHIVE', archive_path):
            args = MagicMock()
            legatum.cmd_archive(args)
            captured = capsys.readouterr()
            assert "No completed items to archive" in captured.out
            # Original content unchanged
            assert praxis_path.read_text() == praxis_content


def test_cmd_archive_archives_completed_items(capsys, tmp_path):
    """Test cmd_archive archives completed [x] items."""
    praxis_content = """- [ ] item 1
- [x] completed item A
  - subitem 1
  - subitem 2
- [ ] item 2
- [x] done:2026-03-01 already tagged
- [ ] item 3
"""
    today = datetime.now().strftime("%Y-%m-%d")

    praxis_path = tmp_path / "Praxis.md"
    praxis_path.write_text(praxis_content)
    archive_path = tmp_path / "Praxis Archive.md"

    with patch.object(legatum, 'PRAXIS', praxis_path):
        with patch.object(legatum, 'PRAXIS_ARCHIVE', archive_path):
            args = MagicMock()
            legatum.cmd_archive(args)

            # Check remaining content - completed items are gone
            remaining = praxis_path.read_text()
            assert "- [ ] item 1" in remaining
            assert "- [ ] item 2" in remaining
            assert "- [ ] item 3" in remaining
            assert "completed item A" not in remaining
            assert "already tagged" not in remaining

            # Check archive has the completed items
            archive_content = archive_path.read_text()
            assert "completed item A" in archive_content
            assert f"`done:{today}`" in archive_content
            assert "already tagged" in archive_content
            assert "done:2026-03-01" in archive_content

            captured = capsys.readouterr()
            assert "Archived 2 completed item(s)" in captured.out


def test_cmd_archive_creates_new_month_section(tmp_path):
    """Test cmd_archive creates new month section when none exists."""
    praxis_content = "- [x] test item\n"
    praxis_path = tmp_path / "Praxis.md"
    praxis_path.write_text(praxis_content)
    archive_path = tmp_path / "Praxis Archive.md"
    archive_path.write_text("Intro text\n\n")

    with patch.object(legatum, 'PRAXIS', praxis_path):
        with patch.object(legatum, 'PRAXIS_ARCHIVE', archive_path):
            args = MagicMock()
            legatum.cmd_archive(args)

            archive_content = archive_path.read_text()
            month_header = datetime.now().strftime("%B %Y")
            assert month_header in archive_content
            assert "test item" in archive_content


# ──────────────────────────────────────────────────────────────────────────────
# cmd_daily tests
# ──────────────────────────────────────────────────────────────────────────────

def test_cmd_daily_creates_new_file(capsys, tmp_path):
    """Test cmd_daily creates new daily note with header."""
    daily_dir = tmp_path / "Daily"
    daily_dir.mkdir()

    today = datetime.now().strftime("%Y-%m-%d")
    weekday = datetime.now().strftime("%A")

    with patch.object(legatum, 'DAILY_DIR', daily_dir):
        args = MagicMock()
        args.title = "Test Session"
        legatum.cmd_daily(args)

        daily_path = daily_dir / f"{today}.md"
        assert daily_path.exists()
        content = daily_path.read_text()
        assert f"# {today} — {weekday}" in content
        assert "— Test Session" in content
        captured = capsys.readouterr()
        assert "Daily note" in captured.out


def test_cmd_daily_appends_to_existing_file(capsys, tmp_path):
    """Test cmd_daily appends to existing daily note."""
    daily_dir = tmp_path / "Daily"
    daily_dir.mkdir()
    today = datetime.now().strftime("%Y-%m-%d")
    daily_path = daily_dir / f"{today}.md"
    daily_path.write_text("# Existing content\n\nPrevious entry\n")

    with patch.object(legatum, 'DAILY_DIR', daily_dir):
        args = MagicMock()
        args.title = None
        legatum.cmd_daily(args)

        content = daily_path.read_text()
        assert "# Existing content" in content
        assert "Previous entry" in content
        assert "— Session" in content  # default title


# ──────────────────────────────────────────────────────────────────────────────
# cmd_gather tests with integration
# ──────────────────────────────────────────────────────────────────────────────

def test_cmd_gather_json_output():
    """Test cmd_gather produces JSON output."""
    args = MagicMock()
    args.syntactic = True
    args.perceptual = False
    args.repos = None

    with patch('telophase.git_status') as mock_git:
        mock_git.return_value = ""  # all clean
        with patch('telophase.skill_gaps') as mock_skills:
            mock_skills.return_value = []
            with patch('telophase.memory_lines') as mock_mem:
                mock_mem.return_value = 50
                with patch('telophase.now_age') as mock_now:
                    mock_now.return_value = ("fresh", 400)
                    with patch('telophase.dep_check') as mock_deps:
                        mock_deps.return_value = []
                        with patch('telophase.peira_status') as mock_peira:
                            mock_peira.return_value = None
                            with patch('telophase.latest_session_id') as mock_sid:
                                mock_sid.return_value = None

                                import io
                                from contextlib import redirect_stdout

                                output = io.StringIO()
                                with redirect_stdout(output):
                                    legatum.cmd_gather(args)

                                # Parse and verify JSON
                                result = json.loads(output.getvalue())
                                assert "repos" in result
                                assert "skills" in result
                                assert "memory" in result
                                assert "now" in result
                                assert "deps" in result
                                assert "peira" in result

                                assert result["memory"]["lines"] == 50
                                assert result["now"]["age_label"] == "fresh"
                                assert result["now"]["age_seconds"] == 400


def test_cmd_gather_with_extra_repos():
    """Test cmd_gather accepts extra repos."""
    args = MagicMock()
    args.syntactic = True
    args.perceptual = False
    args.repos = "/fake/path/repo1,/another/path/repo2"

    called_labels = []

    def mock_git_status(path):
        called_labels.append(path.name)
        return ""

    with patch('telophase.git_status', side_effect=mock_git_status):
        with patch('telophase.skill_gaps') as mock_skills:
            mock_skills.return_value = []
            with patch('telophase.memory_lines') as mock_mem:
                mock_mem.return_value = 50
                with patch('telophase.now_age') as mock_now:
                    mock_now.return_value = ("fresh", 400)
                    with patch('telophase.dep_check') as mock_deps:
                        mock_deps.return_value = []
                        with patch('telophase.peira_status') as mock_peira:
                            mock_peira.return_value = None
                            with patch('telophase.latest_session_id') as mock_sid:
                                mock_sid.return_value = None

                                import io
                                from contextlib import redirect_stdout

                                output = io.StringIO()
                                with redirect_stdout(output):
                                    legatum.cmd_gather(args)

                                # Check that extra repos were processed
                                assert "repo1" in called_labels
                                assert "repo2" in called_labels


# ──────────────────────────────────────────────────────────────────────────────
# run_reflect tests
# ──────────────────────────────────────────────────────────────────────────────

def test_run_reflect_parses_findings():
    """Test run_reflect correctly parses findings from LLM output."""
    session_id = "abc123"

    # Mock anam search output
    anam_output = json.dumps([
        {"role": "user", "snippet": "Test message", "time": "12:34"},
        {"role": "you", "snippet": "Response", "time": "12:35"},
    ])

    # Mock channel glm output with proper formatted findings
    llm_output = """---
category: taste_calibration
quote: User said this was wrong
lesson: Always check this first
memory_type: feedback
---
category: discovery
quote: Found something new
lesson: System behaves differently than expected
memory_type: finding
"""

    with patch('subprocess.run') as mock_run:
        # First call: anam search
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=anam_output),
            MagicMock(returncode=0, stdout=llm_output),
        ]

        findings, usage = legatum.run_reflect(session_id)

        assert len(findings) == 2
        assert findings[0]["category"] == "taste_calibration"
        assert findings[0]["quote"] == "User said this was wrong"
        assert findings[0]["lesson"] == "Always check this first"
        assert findings[0]["memory_type"] == "feedback"
        assert findings[1]["category"] == "discovery"
        assert usage["input_tokens"] > 0
        assert usage["output_tokens"] > 0


def test_run_reflect_empty_on_anam_error():
    """Test run_reflect returns empty when anam fails."""
    session_id = "abc123"
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        findings, usage = legatum.run_reflect(session_id)
        assert findings == []
        assert usage["input_tokens"] == 0


def test_run_reflect_empty_on_channel_error():
    """Test run_reflect returns empty when channel fails."""
    session_id = "abc123"
    anam_output = json.dumps([{"role": "user", "snippet": "test"}])

    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=anam_output),
            MagicMock(returncode=1, stdout=""),
        ]
        findings, usage = legatum.run_reflect(session_id)
        assert findings == []


# ──────────────────────────────────────────────────────────────────────────────
# main/argparse tests
# ──────────────────────────────────────────────────────────────────────────────

def test_main_help(capsys):
    """Test main prints help when no command given."""
    with patch.object(sys, 'argv', ['legatum']):
        with pytest.raises(SystemExit):
            legatum.main()
        captured = capsys.readouterr()
        assert "Deterministic session-close gathering" in captured.out
        assert "gather" in captured.out
        assert "archive" in captured.out
        assert "daily" in captured.out
        assert "reflect" in captured.out
        assert "extract" in captured.out


def test_main_gather_command():
    """Test main parses gather command."""
    args_called = None

    def mock_cmd_gather(args):
        nonlocal args_called
        args_called = args

    with patch.object(sys, 'argv', ['legatum', 'gather', '--syntactic', '--repos', 'test/repo']):
        with patch('telophase.cmd_gather', side_effect=mock_cmd_gather):
            legatum.main()
            assert args_called is not None
            assert args_called.command == "gather"
            assert args_called.syntactic is True
            assert args_called.repos == "test/repo"


def test_main_daily_command():
    """Test main parses daily command."""
    args_called = None

    def mock_cmd_daily(args):
        nonlocal args_called
        args_called = args

    with patch.object(sys, 'argv', ['legatum', 'daily', 'Planning Session']):
        with patch('telophase.cmd_daily', side_effect=mock_cmd_daily):
            legatum.main()
            assert args_called is not None
            assert args_called.command == "daily"
            assert args_called.title == "Planning Session"


def test_main_reflect_command():
    """Test main parses reflect command."""
    args_called = None

    def mock_cmd_reflect(args):
        nonlocal args_called
        args_called = args

    with patch.object(sys, 'argv', ['legatum', 'reflect', 'abc123', '--json']):
        with patch('telophase.cmd_reflect', side_effect=mock_cmd_reflect):
            legatum.main()
            assert args_called is not None
            assert args_called.command == "reflect"
            assert args_called.session == "abc123"
            assert args_called.json is True


def test_main_extract_command():
    """Test main parses extract command."""
    args_called = None

    def mock_cmd_extract(args):
        nonlocal args_called
        args_called = args

    with patch.object(sys, 'argv', ['legatum', 'extract', '--input', 'gather.json']):
        with patch('telophase.cmd_extract', side_effect=mock_cmd_extract):
            legatum.main()
            assert args_called is not None
            assert args_called.command == "extract"
            assert args_called.input == "gather.json"


# ──────────────────────────────────────────────────────────────────────────────
# cmd_extract tests
# ──────────────────────────────────────────────────────────────────────────────

def test_cmd_extract_requires_json(capsys, tmp_path):
    """Test cmd_extract fails on non-JSON input."""
    args = MagicMock()
    args.input = str(tmp_path / "bad.txt")
    (tmp_path / "bad.txt").write_text("not valid json")

    with patch.object(sys, 'stdin') as mock_stdin:
        mock_stdin.read.return_value = "not valid json"
        with pytest.raises(SystemExit):
            legatum.cmd_extract(args)
        captured = capsys.readouterr()
        assert "extract requires gather --syntactic output (JSON)" in captured.err


def test_cmd_extract_works_with_valid_json(capsys, tmp_path):
    """Test cmd_extract processes valid JSON input."""
    test_data = {
        "reflect": [
            {"category": "taste_calibration", "lesson": "test lesson", "quote": "test quote"}
        ]
    }
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(test_data))

    args = MagicMock()
    args.input = str(input_path)

    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="---\n1. FILE: feedback | lesson.md | Test lesson\n---",
            stderr=""
        )
        import io
        from contextlib import redirect_stdout
        output = io.StringIO()
        with redirect_stdout(output):
            legatum.cmd_extract(args)

        assert "FILE: feedback | lesson.md | Test lesson" in output.getvalue()
        mock_run.assert_called_once()
