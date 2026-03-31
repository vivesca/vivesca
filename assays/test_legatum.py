"""Tests for effectors/legatum — deterministic session-close gathering."""

from __future__ import annotations

import json
import sys
import time
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


# ── Module loader ──────────────────────────────────────────────────────────────
def _load_legatum():
    """Load the legatum script via exec (no .py extension)."""
    source = open("/Users/terry/germline/effectors/legatum").read()
    ns: dict = {"__name__": "legatum"}
    exec(source, ns)
    return ns


_mod = _load_legatum()

# Pull out the functions / constants under test
git_status = _mod["git_status"]
now_age = _mod["now_age"]
memory_lines = _mod["memory_lines"]
skill_gaps = _mod["skill_gaps"]
dep_check = _mod["dep_check"]
peira_status = _mod["peira_status"]
latest_session_id = _mod["latest_session_id"]
run_reflect = _mod["run_reflect"]
cmd_gather = _mod["cmd_gather"]
cmd_archive = _mod["cmd_archive"]
cmd_daily = _mod["cmd_daily"]
cmd_reflect = _mod["cmd_reflect"]
cmd_extract = _mod["cmd_extract"]
main = _mod["main"]

NOW_MD = _mod["NOW_MD"]
MEMORY = _mod["MEMORY"]
MEMORY_LIMIT = _mod["MEMORY_LIMIT"]
SKILLS = _mod["SKILLS"]
CLAUDE_SKILLS = _mod["CLAUDE_SKILLS"]
PRAXIS = _mod["PRAXIS"]
PRAXIS_ARCHIVE = _mod["PRAXIS_ARCHIVE"]
DAILY_DIR = _mod["DAILY_DIR"]
DEFAULT_REPOS = _mod["DEFAULT_REPOS"]


# ══════════════════════════════════════════════════════════════════════════════
# git_status
# ══════════════════════════════════════════════════════════════════════════════

class TestGitStatus:
    def test_clean_repo_returns_empty_string(self):
        mock = MagicMock(returncode=0, stdout="  \n")
        with patch("subprocess.run", return_value=mock):
            assert git_status(Path("/some/repo")) == ""

    def test_dirty_repo_returns_status(self):
        output = " M foo.py\n?? new.txt\n"
        mock = MagicMock(returncode=0, stdout=output)
        with patch("subprocess.run", return_value=mock):
            result = git_status(Path("/repo"))
            assert " M foo.py" in result
            assert "?? new.txt" in result

    def test_nonzero_returncode_returns_none(self):
        mock = MagicMock(returncode=128, stdout="")
        with patch("subprocess.run", return_value=mock):
            assert git_status(Path("/nope")) is None

    def test_timeout_returns_none(self):
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 10)):
            assert git_status(Path("/repo")) is None

    def test_filenotfound_returns_none(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert git_status(Path("/repo")) is None


# ══════════════════════════════════════════════════════════════════════════════
# now_age
# ══════════════════════════════════════════════════════════════════════════════

class TestNowAge:
    def test_fresh_under_15_min(self):
        with patch("os.path.getmtime", return_value=time.time() - 500):
            with patch("time.time", return_value=time.time()):
                label, secs = now_age()
                assert label == "fresh"
                assert secs < 900

    def test_recent_under_1_hour(self):
        now = time.time()
        with patch("os.path.getmtime", return_value=now - 1800):
            with patch("time.time", return_value=now):
                label, secs = now_age()
                assert label == "recent"
                assert 900 <= secs < 3600

    def test_stale_under_1_day(self):
        now = time.time()
        with patch("os.path.getmtime", return_value=now - 10000):
            with patch("time.time", return_value=now):
                label, secs = now_age()
                assert label == "stale"
                assert 3600 <= secs < 86400

    def test_very_stale_over_1_day(self):
        now = time.time()
        with patch("os.path.getmtime", return_value=now - 200000):
            with patch("time.time", return_value=now):
                label, secs = now_age()
                assert label == "very stale"
                assert secs >= 86400

    def test_missing_file(self):
        with patch("os.path.getmtime", side_effect=FileNotFoundError):
            label, secs = now_age()
            assert label == "missing"
            assert secs == -1


# ══════════════════════════════════════════════════════════════════════════════
# memory_lines
# ══════════════════════════════════════════════════════════════════════════════

class TestMemoryLines:
    def test_counts_lines(self, tmp_path):
        mem = tmp_path / "MEMORY.md"
        mem.write_text("line1\nline2\nline3\n")
        with patch.object(_mod, "MEMORY", mem):
            with patch("builtins.open", create=True):
                # Need to re-bind since memory_lines references MEMORY at module level
                # We use the function from the reloaded ns with patched global
                pass
        # Since memory_lines uses open(MEMORY) directly, we patch the path
        fake_mem = tmp_path / "MEMORY.md"
        fake_mem.write_text("a\nb\nc\n")
        with patch.object(_mod, "MEMORY", fake_mem):
            result = memory_lines()
        assert result == 3

    def test_missing_returns_zero(self):
        with patch.object(_mod, "MEMORY", Path("/nonexistent/MEMORY.md")):
            assert memory_lines() == 0


# ══════════════════════════════════════════════════════════════════════════════
# skill_gaps
# ══════════════════════════════════════════════════════════════════════════════

class TestSkillGaps:
    def test_no_gaps(self):
        with patch("os.listdir", side_effect=lambda p: ["skill_a", "skill_b"]):
            result = skill_gaps()
            assert result == []

    def test_detects_gaps(self):
        def fake_listdir(path):
            path = str(path)
            if "vivesca" in path or str(SKILLS) == path:
                return ["alpha", "beta", "gamma"]
            if ".claude/skills" in path or str(CLAUDE_SKILLS) == path:
                return ["alpha", "gamma"]
            return []
        with patch("os.listdir", side_effect=fake_listdir):
            result = skill_gaps()
            assert result == ["beta"]

    def test_skips_dotfiles(self):
        def fake_listdir(path):
            path = str(path)
            if "vivesca" in path or str(SKILLS) == path:
                return [".hidden", "visible"]
            if ".claude/skills" in path or str(CLAUDE_SKILLS) == path:
                return ["visible"]
            return []
        with patch("os.listdir", side_effect=fake_listdir):
            result = skill_gaps()
            assert result == []

    def test_missing_dir_returns_empty(self):
        with patch("os.listdir", side_effect=FileNotFoundError):
            assert skill_gaps() == []


# ══════════════════════════════════════════════════════════════════════════════
# dep_check
# ══════════════════════════════════════════════════════════════════════════════

class TestDepCheck:
    def test_returns_warnings(self):
        mock = MagicMock(returncode=0, stdout="pkg-x outdated\npkg-y missing\n")
        with patch("subprocess.run", return_value=mock):
            result = dep_check()
            assert len(result) == 2
            assert "pkg-x outdated" in result

    def test_empty_stdout_returns_empty(self):
        mock = MagicMock(returncode=0, stdout="  \n")
        with patch("subprocess.run", return_value=mock):
            assert dep_check() == []

    def test_timeout_returns_empty(self):
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("x", 30)):
            assert dep_check() == []

    def test_not_found_returns_empty(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert dep_check() == []


# ══════════════════════════════════════════════════════════════════════════════
# peira_status
# ══════════════════════════════════════════════════════════════════════════════

class TestPeiraStatus:
    def test_returns_status_text(self):
        mock = MagicMock(returncode=0, stdout="exp-42 running\n")
        with patch("subprocess.run", return_value=mock):
            assert peira_status() == "exp-42 running"

    def test_nonzero_returns_none(self):
        mock = MagicMock(returncode=1, stdout="")
        with patch("subprocess.run", return_value=mock):
            assert peira_status() is None

    def test_empty_stdout_returns_none(self):
        mock = MagicMock(returncode=0, stdout="  ")
        with patch("subprocess.run", return_value=mock):
            assert peira_status() is None

    def test_timeout_returns_none(self):
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("peira", 10)):
            assert peira_status() is None


# ══════════════════════════════════════════════════════════════════════════════
# latest_session_id
# ══════════════════════════════════════════════════════════════════════════════

class TestLatestSessionId:
    def test_extracts_hex_id(self):
        output = "some line\n[abc123] 5 prompts (2m) - Opus\n"
        mock = MagicMock(returncode=0, stdout=output)
        with patch("subprocess.run", return_value=mock):
            assert latest_session_id() == "abc123"

    def test_no_match_returns_none(self):
        mock = MagicMock(returncode=0, stdout="nothing here\n")
        with patch("subprocess.run", return_value=mock):
            assert latest_session_id() is None

    def test_failure_returns_none(self):
        mock = MagicMock(returncode=1, stdout="")
        with patch("subprocess.run", return_value=mock):
            assert latest_session_id() is None

    def test_timeout_returns_none(self):
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("anam", 10)):
            assert latest_session_id() is None


# ══════════════════════════════════════════════════════════════════════════════
# run_reflect
# ══════════════════════════════════════════════════════════════════════════════

class TestRunReflect:
    def _mock_anam(self, messages_json):
        """Return a mock subprocess.run that responds to anam search."""
        def side_effect(cmd, **kwargs):
            m = MagicMock()
            if "anam" in cmd:
                if "search" in cmd:
                    m.returncode = 0
                    m.stdout = json.dumps(messages_json)
                else:
                    m.returncode = 0
                    m.stdout = "[deadbeef] 3 prompts (1m) - Opus\n"
            elif "channel" in cmd:
                m.returncode = 0
                m.stdout = "---\ncategory: discovery\nquote: found it\nlesson: something new\nmemory_type: finding\n---"
            else:
                m.returncode = 1
                m.stdout = ""
            return m
        return side_effect

    def test_parses_findings(self):
        msgs = [
            {"role": "user", "snippet": "I discovered X", "time": "10:00"},
            {"role": "assistant", "snippet": "Great!", "time": "10:01"},
        ]
        with patch("subprocess.run", side_effect=self._mock_anam(msgs)):
            findings, usage = run_reflect("abc123")
        assert len(findings) >= 1
        assert findings[0]["category"] == "discovery"

    def test_empty_messages_returns_empty(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="[]")
            findings, usage = run_reflect("abc123")
        assert findings == []

    def test_anam_failure_returns_empty(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            findings, usage = run_reflect("abc123")
        assert findings == []

    def test_long_assistant_snippet_truncated(self):
        msgs = [
            {"role": "assistant", "snippet": "x" * 600, "time": "10:00"},
        ]
        with patch("subprocess.run", side_effect=self._mock_anam(msgs)):
            findings, usage = run_reflect("abc123")
        # Should not crash; usage should have input_tokens estimated
        assert usage["input_tokens"] > 0

    def test_channel_failure_returns_empty(self):
        msgs = [{"role": "user", "snippet": "hello", "time": "10:00"}]
        def side_effect(cmd, **kwargs):
            m = MagicMock()
            if "anam" in cmd and "search" in cmd:
                m.returncode = 0
                m.stdout = json.dumps(msgs)
            elif "channel" in cmd:
                m.returncode = 1
                m.stdout = ""
            else:
                m.returncode = 0
                m.stdout = ""
            return m
        with patch("subprocess.run", side_effect=side_effect):
            findings, usage = run_reflect("abc123")
        assert findings == []
        assert usage["input_tokens"] > 0


# ══════════════════════════════════════════════════════════════════════════════
# cmd_gather
# ══════════════════════════════════════════════════════════════════════════════

class TestCmdGather:
    def _make_args(self, **overrides):
        defaults = {"syntactic": False, "perceptual": False, "repos": None}
        defaults.update(overrides)
        return MagicMock(**defaults)

    def test_syntactic_output_is_valid_json(self, capsys):
        args = self._make_args(syntactic=True)
        with patch.object(_mod, "git_status", return_value=""), \
             patch.object(_mod, "skill_gaps", return_value=[]), \
             patch.object(_mod, "memory_lines", return_value=42), \
             patch.object(_mod, "now_age", return_value=("fresh", 100)), \
             patch.object(_mod, "dep_check", return_value=[]), \
             patch.object(_mod, "peira_status", return_value=None), \
             patch.object(_mod, "latest_session_id", return_value=None):
            cmd_gather(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["memory"]["lines"] == 42
        assert data["now"]["age_label"] == "fresh"
        assert data["repos"] != {}

    def test_default_compact_output(self, capsys):
        args = self._make_args()
        with patch.object(_mod, "git_status", return_value=""), \
             patch.object(_mod, "skill_gaps", return_value=[]), \
             patch.object(_mod, "memory_lines", return_value=10), \
             patch.object(_mod, "now_age", return_value=("fresh", 100)), \
             patch.object(_mod, "dep_check", return_value=[]), \
             patch.object(_mod, "peira_status", return_value=None), \
             patch.object(_mod, "latest_session_id", return_value=None):
            cmd_gather(args)
        out = capsys.readouterr().out
        assert "memory:10/" in out
        assert "now:fresh" in out

    def test_dirty_repo_shown_in_compact(self, capsys):
        args = self._make_args()
        def fake_git_status(path):
            if path.name == "skills":
                return " M foo.py"
            return ""
        with patch.object(_mod, "git_status", side_effect=fake_git_status), \
             patch.object(_mod, "skill_gaps", return_value=[]), \
             patch.object(_mod, "memory_lines", return_value=5), \
             patch.object(_mod, "now_age", return_value=("fresh", 50)), \
             patch.object(_mod, "dep_check", return_value=[]), \
             patch.object(_mod, "peira_status", return_value=None), \
             patch.object(_mod, "latest_session_id", return_value=None):
            cmd_gather(args)
        out = capsys.readouterr().out
        assert "repo:skills dirty" in out

    def test_unlinked_skills_shown(self, capsys):
        args = self._make_args()
        with patch.object(_mod, "git_status", return_value=""), \
             patch.object(_mod, "skill_gaps", return_value=["foo", "bar"]), \
             patch.object(_mod, "memory_lines", return_value=5), \
             patch.object(_mod, "now_age", return_value=("fresh", 50)), \
             patch.object(_mod, "dep_check", return_value=[]), \
             patch.object(_mod, "peira_status", return_value=None), \
             patch.object(_mod, "latest_session_id", return_value=None):
            cmd_gather(args)
        out = capsys.readouterr().out
        assert "skills:unlinked foo,bar" in out

    def test_extra_repos(self, capsys):
        args = self._make_args(syntactic=True, repos="/tmp/myrepo")
        with patch.object(_mod, "git_status", return_value=""), \
             patch.object(_mod, "skill_gaps", return_value=[]), \
             patch.object(_mod, "memory_lines", return_value=5), \
             patch.object(_mod, "now_age", return_value=("fresh", 50)), \
             patch.object(_mod, "dep_check", return_value=[]), \
             patch.object(_mod, "peira_status", return_value=None), \
             patch.object(_mod, "latest_session_id", return_value=None):
            cmd_gather(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "myrepo" in data["repos"]

    def test_perceptual_output(self, capsys):
        args = self._make_args(perceptual=True)
        with patch.object(_mod, "git_status", return_value=""), \
             patch.object(_mod, "skill_gaps", return_value=[]), \
             patch.object(_mod, "memory_lines", return_value=5), \
             patch.object(_mod, "now_age", return_value=("fresh", 50)), \
             patch.object(_mod, "dep_check", return_value=[]), \
             patch.object(_mod, "peira_status", return_value=None), \
             patch.object(_mod, "latest_session_id", return_value=None):
            cmd_gather(args)
        out = capsys.readouterr().out
        assert "Legatum Gather" in out

    def test_deps_shown_in_compact(self, capsys):
        args = self._make_args()
        with patch.object(_mod, "git_status", return_value=""), \
             patch.object(_mod, "skill_gaps", return_value=[]), \
             patch.object(_mod, "memory_lines", return_value=5), \
             patch.object(_mod, "now_age", return_value=("fresh", 50)), \
             patch.object(_mod, "dep_check", return_value=["pkg outdated"]), \
             patch.object(_mod, "peira_status", return_value=None), \
             patch.object(_mod, "latest_session_id", return_value=None):
            cmd_gather(args)
        out = capsys.readouterr().out
        assert "deps:pkg outdated" in out

    def test_peira_shown_in_compact(self, capsys):
        args = self._make_args()
        with patch.object(_mod, "git_status", return_value=""), \
             patch.object(_mod, "skill_gaps", return_value=[]), \
             patch.object(_mod, "memory_lines", return_value=5), \
             patch.object(_mod, "now_age", return_value=("fresh", 50)), \
             patch.object(_mod, "dep_check", return_value=[]), \
             patch.object(_mod, "peira_status", return_value="exp-1 active"), \
             patch.object(_mod, "latest_session_id", return_value=None):
            cmd_gather(args)
        out = capsys.readouterr().out
        assert "peira:exp-1 active" in out


# ══════════════════════════════════════════════════════════════════════════════
# cmd_archive
# ══════════════════════════════════════════════════════════════════════════════

class TestCmdArchive:
    def test_no_praxis_exits(self):
        with patch.object(_mod, "PRAXIS", Path("/nonexistent/Praxis.md")):
            with pytest.raises(SystemExit):
                cmd_archive(MagicMock())

    def test_no_completed_items(self, capsys, tmp_path):
        praxis = tmp_path / "Praxis.md"
        praxis.write_text("# Tasks\n\n- [ ] TODO item\n- [ ] Another\n")
        with patch.object(_mod, "PRAXIS", praxis), \
             patch.object(_mod, "PRAXIS_ARCHIVE", tmp_path / "archive.md"):
            cmd_archive(MagicMock())
        out = capsys.readouterr().out
        assert "No completed items" in out

    def test_archives_completed_items(self, tmp_path, capsys):
        praxis = tmp_path / "Praxis.md"
        praxis.write_text("# Tasks\n\n- [x] Done thing\n- [ ] Still todo\n")
        archive = tmp_path / "Praxis Archive.md"
        archive.write_text("# Archive\n\n## January 2026\n\nold item\n")

        with patch.object(_mod, "PRAXIS", praxis), \
             patch.object(_mod, "PRAXIS_ARCHIVE", archive):
            # Patch datetime to control month header
            from datetime import datetime
            fake_now = datetime(2026, 1, 15, 12, 0, 0)
            with patch.object(_mod, "datetime") as mock_dt:
                mock_dt.now.return_value = fake_now
                mock_dt.strftime = datetime.strftime
                # Need strftime to work on the mock
                mock_dt.now.return_value.strftime = lambda fmt: fake_now.strftime(fmt)
                cmd_archive(MagicMock())

        out = capsys.readouterr().out
        assert "Archived 1 completed item" in out

        # Check Praxis has remaining items only
        remaining = praxis.read_text()
        assert "- [ ] Still todo" in remaining
        assert "- [x]" not in remaining

        # Check archive has the completed item
        archive_text = archive.read_text()
        assert "Done thing" in archive_text

    def test_adds_done_tag_if_missing(self, tmp_path, capsys):
        praxis = tmp_path / "Praxis.md"
        praxis.write_text("- [x] Task without done tag\n")
        archive = tmp_path / "Praxis Archive.md"
        archive.write_text("")

        from datetime import datetime
        fake_now = datetime(2026, 3, 31, 12, 0, 0)
        with patch.object(_mod, "PRAXIS", praxis), \
             patch.object(_mod, "PRAXIS_ARCHIVE", archive), \
             patch.object(_mod, "datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.now.return_value.strftime = lambda fmt: fake_now.strftime(fmt)
            cmd_archive(MagicMock())

        archive_text = archive.read_text()
        assert "done:2026-03-31" in archive_text

    def test_preserves_existing_done_tag(self, tmp_path, capsys):
        praxis = tmp_path / "Praxis.md"
        praxis.write_text("- [x] Task `done:2026-01-01`\n")
        archive = tmp_path / "Praxis Archive.md"
        archive.write_text("")

        from datetime import datetime
        fake_now = datetime(2026, 3, 31, 12, 0, 0)
        with patch.object(_mod, "PRAXIS", praxis), \
             patch.object(_mod, "PRAXIS_ARCHIVE", archive), \
             patch.object(_mod, "datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.now.return_value.strftime = lambda fmt: fake_now.strftime(fmt)
            cmd_archive(MagicMock())

        archive_text = archive.read_text()
        # Should only have one done tag
        assert archive_text.count("done:") == 1

    def test_creates_new_month_section(self, tmp_path, capsys):
        praxis = tmp_path / "Praxis.md"
        praxis.write_text("- [x] New task\n")
        archive = tmp_path / "Praxis Archive.md"
        archive.write_text("# Archive\n\n## January 2026\n\nold\n")

        from datetime import datetime
        fake_now = datetime(2026, 3, 31, 12, 0, 0)
        with patch.object(_mod, "PRAXIS", praxis), \
             patch.object(_mod, "PRAXIS_ARCHIVE", archive), \
             patch.object(_mod, "datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.now.return_value.strftime = lambda fmt: fake_now.strftime(fmt)
            cmd_archive(MagicMock())

        archive_text = archive.read_text()
        assert "## March 2026" in archive_text
        assert "New task" in archive_text

    def test_skips_children_of_completed_items(self, tmp_path, capsys):
        praxis = tmp_path / "Praxis.md"
        praxis.write_text("- [x] Parent task\n  - child detail 1\n  - child detail 2\n- [ ] Remaining\n")
        archive = tmp_path / "Praxis Archive.md"
        archive.write_text("")

        from datetime import datetime
        fake_now = datetime(2026, 3, 31, 12, 0, 0)
        with patch.object(_mod, "PRAXIS", praxis), \
             patch.object(_mod, "PRAXIS_ARCHIVE", archive), \
             patch.object(_mod, "datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.now.return_value.strftime = lambda fmt: fake_now.strftime(fmt)
            cmd_archive(MagicMock())

        remaining = praxis.read_text()
        assert "child detail" not in remaining
        assert "- [ ] Remaining" in remaining


# ══════════════════════════════════════════════════════════════════════════════
# cmd_daily
# ══════════════════════════════════════════════════════════════════════════════

class TestCmdDaily:
    def test_creates_new_daily_note(self, tmp_path, capsys):
        daily_dir = tmp_path / "Daily"
        daily_dir.mkdir()

        from datetime import datetime
        fake_now = datetime(2026, 3, 31, 14, 30, 0)
        with patch.object(_mod, "DAILY_DIR", daily_dir), \
             patch.object(_mod, "datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.now.return_value.strftime = lambda fmt: fake_now.strftime(fmt)
            args = MagicMock(title="Test Session")
            cmd_daily(args)

        daily_path = daily_dir / "2026-03-31.md"
        assert daily_path.exists()
        content = daily_path.read_text()
        assert "# 2026-03-31 — Tuesday" in content
        assert "Test Session" in content

    def test_appends_to_existing(self, tmp_path, capsys):
        daily_dir = tmp_path / "Daily"
        daily_dir.mkdir()
        daily_path = daily_dir / "2026-03-31.md"
        daily_path.write_text("# 2026-03-31 — Tuesday\n\nexisting content\n")

        from datetime import datetime
        fake_now = datetime(2026, 3, 31, 14, 30, 0)
        with patch.object(_mod, "DAILY_DIR", daily_dir), \
             patch.object(_mod, "datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.now.return_value.strftime = lambda fmt: fake_now.strftime(fmt)
            args = MagicMock(title="Second Session")
            cmd_daily(args)

        content = daily_path.read_text()
        assert "existing content" in content
        assert "Second Session" in content

    def test_default_title_is_session(self, tmp_path, capsys):
        daily_dir = tmp_path / "Daily"
        daily_dir.mkdir()

        from datetime import datetime
        fake_now = datetime(2026, 3, 31, 14, 30, 0)
        with patch.object(_mod, "DAILY_DIR", daily_dir), \
             patch.object(_mod, "datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.now.return_value.strftime = lambda fmt: fake_now.strftime(fmt)
            args = MagicMock(title=None)
            cmd_daily(args)

        content = (daily_dir / "2026-03-31.md").read_text()
        assert "Session" in content

    def test_template_has_fill_prompt(self, tmp_path, capsys):
        daily_dir = tmp_path / "Daily"
        daily_dir.mkdir()

        from datetime import datetime
        fake_now = datetime(2026, 3, 31, 14, 30, 0)
        with patch.object(_mod, "DAILY_DIR", daily_dir), \
             patch.object(_mod, "datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.now.return_value.strftime = lambda fmt: fake_now.strftime(fmt)
            args = MagicMock(title="Test")
            cmd_daily(args)

        out = capsys.readouterr().out
        assert "fill in outcomes" in out.lower()


# ══════════════════════════════════════════════════════════════════════════════
# cmd_reflect
# ══════════════════════════════════════════════════════════════════════════════

class TestCmdReflect:
    def test_no_findings(self, capsys):
        with patch.object(_mod, "run_reflect", return_value=([], {"input_tokens": 0, "output_tokens": 0})):
            args = MagicMock(session="abc123", json=False)
            cmd_reflect(args)
        out = capsys.readouterr().out
        assert "No messages found" in out

    def test_json_output(self, capsys):
        findings = [{"category": "discovery", "lesson": "something"}]
        with patch.object(_mod, "run_reflect", return_value=(findings, {"input_tokens": 100, "output_tokens": 50})):
            args = MagicMock(session="abc123", json=True)
            cmd_reflect(args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data) == 1
        assert data[0]["category"] == "discovery"

    def test_text_output(self, capsys):
        findings = [
            {"category": "taste_calibration", "lesson": "prefer X over Y", "quote": "use X"},
        ]
        with patch.object(_mod, "run_reflect", return_value=(findings, {"input_tokens": 100, "output_tokens": 50})):
            args = MagicMock(session="abc123", json=False)
            cmd_reflect(args)
        out = capsys.readouterr().out
        assert "Reflection Scan" in out
        assert "Taste Calibration" in out
        assert "prefer X over Y" in out


# ══════════════════════════════════════════════════════════════════════════════
# cmd_extract
# ══════════════════════════════════════════════════════════════════════════════

class TestCmdExtract:
    def test_exits_on_bad_json(self):
        args = MagicMock(input=None)
        with patch("sys.stdin", StringIO("not json")):
            with pytest.raises(SystemExit):
                cmd_extract(args)

    def test_no_candidates(self, capsys):
        data = json.dumps({"reflect": []})
        args = MagicMock(input=None)
        with patch("sys.stdin", StringIO(data)):
            cmd_extract(args)
        out = capsys.readouterr().out
        assert "no candidates" in out

    def test_with_input_file(self, capsys, tmp_path):
        gather = {"reflect": [{"category": "discovery", "lesson": "x", "quote": "y"}]}
        infile = tmp_path / "gather.json"
        infile.write_text(json.dumps(gather))

        mock = MagicMock(returncode=0, stdout="1. FILE: finding | test.md | something learned\n")
        with patch("subprocess.run", return_value=mock):
            args = MagicMock(input=str(infile))
            cmd_extract(args)
        out = capsys.readouterr().out
        assert "FILE" in out

    def test_channel_failure_exits(self, tmp_path):
        gather = {"reflect": [{"category": "discovery", "lesson": "x"}]}
        infile = tmp_path / "gather.json"
        infile.write_text(json.dumps(gather))

        mock = MagicMock(returncode=1, stderr="error")
        with patch("subprocess.run", return_value=mock):
            args = MagicMock(input=str(infile))
            with pytest.raises(SystemExit):
                cmd_extract(args)


# ══════════════════════════════════════════════════════════════════════════════
# main / argument parsing
# ══════════════════════════════════════════════════════════════════════════════

class TestMain:
    def test_no_command_exits(self):
        with patch("sys.argv", ["legatum"]):
            with pytest.raises(SystemExit):
                main()

    def test_gather_command(self, capsys):
        with patch("sys.argv", ["legatum", "gather", "--syntactic"]), \
             patch.object(_mod, "git_status", return_value=""), \
             patch.object(_mod, "skill_gaps", return_value=[]), \
             patch.object(_mod, "memory_lines", return_value=5), \
             patch.object(_mod, "now_age", return_value=("fresh", 50)), \
             patch.object(_mod, "dep_check", return_value=[]), \
             patch.object(_mod, "peira_status", return_value=None), \
             patch.object(_mod, "latest_session_id", return_value=None):
            main()
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "repos" in data

    def test_archive_command(self, tmp_path, capsys):
        praxis = tmp_path / "Praxis.md"
        praxis.write_text("- [ ] nothing to archive\n")
        with patch("sys.argv", ["legatum", "archive"]), \
             patch.object(_mod, "PRAXIS", praxis), \
             patch.object(_mod, "PRAXIS_ARCHIVE", tmp_path / "archive.md"):
            main()
        out = capsys.readouterr().out
        assert "No completed items" in out

    def test_daily_command(self, tmp_path, capsys):
        daily_dir = tmp_path / "Daily"
        daily_dir.mkdir()

        from datetime import datetime
        fake_now = datetime(2026, 3, 31, 14, 30, 0)
        with patch("sys.argv", ["legatum", "daily", "Test"]), \
             patch.object(_mod, "DAILY_DIR", daily_dir), \
             patch.object(_mod, "datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            mock_dt.now.return_value.strftime = lambda fmt: fake_now.strftime(fmt)
            main()
        assert (daily_dir / "2026-03-31.md").exists()

    def test_reflect_command(self, capsys):
        with patch("sys.argv", ["legatum", "reflect", "abc123"]), \
             patch.object(_mod, "run_reflect", return_value=([], {"input_tokens": 0, "output_tokens": 0})):
            main()
        out = capsys.readouterr().out
        assert "No messages found" in out
