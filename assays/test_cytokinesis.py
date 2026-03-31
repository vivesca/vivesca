"""Tests for effectors/cytokinesis — deterministic session-close gathering.

Cytokinesis is a script (effectors/cytokinesis), not an importable module.
It is loaded via exec() so that module-level constants can be patched per test.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

CYTOKINESIS_PATH = Path(__file__).resolve().parents[1] / "effectors" / "cytokinesis"


# ── Fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def cyto(tmp_path):
    """Load cytokinesis via exec, redirecting all path constants to tmp_path."""
    ns: dict = {"__name__": "test_cytokinesis"}
    source = CYTOKINESIS_PATH.read_text(encoding="utf-8")
    exec(source, ns)

    # Redirect path constants
    daily_dir = tmp_path / "daily"
    daily_dir.mkdir()
    now_md = tmp_path / "Tonus.md"
    skills_dir = tmp_path / "receptors"
    skills_dir.mkdir()
    claude_skills_dir = tmp_path / "claude_skills"
    claude_skills_dir.mkdir()
    memory_file = tmp_path / "MEMORY.md"
    praxis_file = tmp_path / "Praxis.md"
    praxis_archive_file = tmp_path / "Praxis Archive.md"
    germline_dir = tmp_path / "germline"
    germline_dir.mkdir()
    epigenome_dir = tmp_path / "epigenome"
    epigenome_dir.mkdir()
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    home_dir = tmp_path / "home"
    home_dir.mkdir()

    ns["DAILY_DIR"] = daily_dir
    ns["NOW_MD"] = now_md
    ns["SKILLS"] = skills_dir
    ns["MEMORY"] = memory_file
    ns["MEMORY_LIMIT"] = 150
    ns["DEFAULT_REPOS"] = {
        "germline": germline_dir,
        "epigenome": epigenome_dir,
        "scripts": scripts_dir,
    }

    # Patch module-level names imported from metabolon.locus
    ns["praxis"] = praxis_file
    ns["praxis_archive"] = praxis_archive_file
    ns["claude_skills"] = claude_skills_dir
    ns["home"] = home_dir
    ns["germline"] = germline_dir
    ns["epigenome"] = epigenome_dir

    return ns


def _args(**kwargs):
    """Build a namespace object for subcommand args."""
    defaults = {
        "command": "gather",
        "syntactic": False,
        "perceptual": False,
        "repos": None,
        "title": None,
        "hours": 2,
        "session": "abc123",
        "json": False,
        "input": None,
    }
    defaults.update(kwargs)
    return MagicMock(**defaults)


# ── git_status ──────────────────────────────────────────────────────────────


class TestGitStatus:
    def test_clean_repo(self, cyto, tmp_path):
        repo = tmp_path / "clean_repo"
        repo.mkdir()
        mock_run = MagicMock(return_value=MagicMock(returncode=0, stdout=""))
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["git_status"](repo)
        assert result == ""

    def test_dirty_repo(self, cyto, tmp_path):
        repo = tmp_path / "dirty_repo"
        repo.mkdir()
        mock_run = MagicMock(
            return_value=MagicMock(returncode=0, stdout="M file.py\n?? new.py")
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["git_status"](repo)
        assert "M file.py" in result
        assert "?? new.py" in result

    def test_nonzero_exit_returns_none(self, cyto, tmp_path):
        repo = tmp_path / "not_repo"
        repo.mkdir()
        mock_run = MagicMock(return_value=MagicMock(returncode=128, stdout=""))
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["git_status"](repo)
        assert result is None

    def test_timeout_returns_none(self, cyto, tmp_path):
        repo = tmp_path / "slow"
        repo.mkdir()
        mock_run = MagicMock(side_effect=subprocess.TimeoutExpired("git", 10))
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["git_status"](repo)
        assert result is None

    def test_file_not_found_returns_none(self, cyto, tmp_path):
        repo = tmp_path / "gone"
        repo.mkdir()
        mock_run = MagicMock(side_effect=FileNotFoundError)
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["git_status"](repo)
        assert result is None


# ── now_age ─────────────────────────────────────────────────────────────────


class TestNowAge:
    def test_fresh(self, cyto):
        now_md = cyto["NOW_MD"]
        now_md.write_text("fresh content", encoding="utf-8")
        # mtime is right now → fresh
        label, secs = cyto["now_age"]()
        assert label == "fresh"
        assert secs >= 0

    def test_recent(self, cyto):
        now_md = cyto["NOW_MD"]
        now_md.write_text("recent", encoding="utf-8")
        # Backdate 30 minutes
        old_mtime = time.time() - 1800
        os.utime(str(now_md), (old_mtime, old_mtime))
        label, secs = cyto["now_age"]()
        assert label == "recent"

    def test_stale(self, cyto):
        now_md = cyto["NOW_MD"]
        now_md.write_text("stale", encoding="utf-8")
        old_mtime = time.time() - 7200  # 2 hours
        os.utime(str(now_md), (old_mtime, old_mtime))
        label, secs = cyto["now_age"]()
        assert label == "stale"

    def test_very_stale(self, cyto):
        now_md = cyto["NOW_MD"]
        now_md.write_text("ancient", encoding="utf-8")
        old_mtime = time.time() - 100000  # > 1 day
        os.utime(str(now_md), (old_mtime, old_mtime))
        label, secs = cyto["now_age"]()
        assert label == "very stale"

    def test_missing(self, cyto):
        cyto["NOW_MD"] = cyto["NOW_MD"].parent / "nonexistent_Tonus.md"
        label, secs = cyto["now_age"]()
        assert label == "missing"
        assert secs == -1


# ── memory_lines ────────────────────────────────────────────────────────────


class TestMemoryLines:
    def test_counts_lines(self, cyto):
        cyto["MEMORY"].write_text("line1\nline2\nline3\n", encoding="utf-8")
        assert cyto["memory_lines"]() == 3

    def test_empty_file(self, cyto):
        cyto["MEMORY"].write_text("", encoding="utf-8")
        assert cyto["memory_lines"]() == 0  # sum(1 for _ in open(...)) on empty = 0

    def test_file_not_found(self, cyto):
        cyto["MEMORY"] = cyto["MEMORY"].parent / "NO_SUCH_MEMORY.md"
        assert cyto["memory_lines"]() == 0


# ── skill_gaps ──────────────────────────────────────────────────────────────


class TestSkillGaps:
    def test_no_gaps(self, cyto):
        # Both dirs have same entries → no gaps
        (cyto["SKILLS"] / "skill_a").mkdir()
        (cyto["claude_skills"] / "skill_a").mkdir()
        result = cyto["skill_gaps"]()
        assert result == []

    def test_finds_gap_and_links(self, cyto):
        # skill_b in receptors but not in claude_skills
        (cyto["SKILLS"] / "skill_b").mkdir()
        result = cyto["skill_gaps"]()
        assert result == ["skill_b"]
        # Verify symlink was created
        link = cyto["claude_skills"] / "skill_b"
        assert link.is_symlink()

    def test_skills_dir_missing(self, cyto):
        cyto["SKILLS"] = Path("/nonexistent_skills_dir_xyz")
        result = cyto["skill_gaps"]()
        assert result == []


# ── cli_gaps ────────────────────────────────────────────────────────────────


class TestCliGaps:
    def test_missing_cli(self, cyto):
        skill_dir = cyto["SKILLS"] / "my_tool"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\ncli: nonexistent_cli_tool_xyz\n---\n", encoding="utf-8"
        )
        result = cyto["cli_gaps"]()
        assert len(result) == 1
        assert "nonexistent_cli_tool_xyz" in result[0]

    def test_existing_cli_no_gap(self, cyto):
        skill_dir = cyto["SKILLS"] / "echo_skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\ncli: echo\n---\n", encoding="utf-8"
        )
        result = cyto["cli_gaps"]()
        assert result == []

    def test_no_skill_md(self, cyto):
        skill_dir = cyto["SKILLS"] / "bare_dir"
        skill_dir.mkdir()
        result = cyto["cli_gaps"]()
        assert result == []


# ── rfts_verify ─────────────────────────────────────────────────────────────


class TestRftsVerify:
    def test_no_memory_dir(self, cyto):
        # Use a path whose parent exists but is empty (function iterates MEMORY.parent)
        empty_mem_dir = cyto["home"] / "empty_mem"
        empty_mem_dir.mkdir()
        cyto["MEMORY"] = empty_mem_dir / "MEMORY.md"
        result = cyto["rfts_verify"]()
        assert result == []

    def test_valid_paths_no_issues(self, cyto):
        # Memory file with no path references → no issues
        md = cyto["MEMORY"].parent / "test.md"
        md.write_text("Just some notes with no path references.\n", encoding="utf-8")
        result = cyto["rfts_verify"]()
        assert result == []

    def test_stale_path_flagged(self, cyto):
        md = cyto["MEMORY"].parent / "stale.md"
        md.write_text("Refers to `/Users/terry/phantom/path/deep` entry.\n", encoding="utf-8")
        result = cyto["rfts_verify"]()
        assert len(result) == 1
        assert result[0]["file"] == "stale.md"
        assert any("path:" in i for i in result[0]["issues"])

    def test_protected_file_skipped(self, cyto):
        md = cyto["MEMORY"].parent / "protected.md"
        md.write_text(
            "---\nprotected: true\n---\nRefers to `/Users/terry/phantom/deep/path`.\n",
            encoding="utf-8",
        )
        result = cyto["rfts_verify"]()
        assert result == []


# ── dep_check ───────────────────────────────────────────────────────────────


class TestDepCheck:
    def test_success_with_warnings(self, cyto):
        mock_run = MagicMock(
            return_value=MagicMock(returncode=0, stdout="warn1\nwarn2\n")
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["dep_check"]()
        assert result == ["warn1", "warn2"]

    def test_success_empty(self, cyto):
        mock_run = MagicMock(
            return_value=MagicMock(returncode=0, stdout="")
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["dep_check"]()
        assert result == []

    def test_timeout(self, cyto):
        mock_run = MagicMock(side_effect=subprocess.TimeoutExpired("proteostasis", 30))
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["dep_check"]()
        assert result == []

    def test_not_found(self, cyto):
        mock_run = MagicMock(side_effect=FileNotFoundError)
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["dep_check"]()
        assert result == []


# ── peira_status ────────────────────────────────────────────────────────────


class TestPeiraStatus:
    def test_returns_output(self, cyto):
        mock_run = MagicMock(
            return_value=MagicMock(returncode=0, stdout="exp-42 running")
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            assert cyto["peira_status"]() == "exp-42 running"

    def test_empty_stdout(self, cyto):
        mock_run = MagicMock(return_value=MagicMock(returncode=0, stdout=""))
        with patch.object(cyto["subprocess"], "run", mock_run):
            assert cyto["peira_status"]() is None

    def test_nonzero(self, cyto):
        mock_run = MagicMock(return_value=MagicMock(returncode=1, stdout=""))
        with patch.object(cyto["subprocess"], "run", mock_run):
            assert cyto["peira_status"]() is None

    def test_timeout(self, cyto):
        mock_run = MagicMock(side_effect=subprocess.TimeoutExpired("peira", 10))
        with patch.object(cyto["subprocess"], "run", mock_run):
            assert cyto["peira_status"]() is None

    def test_not_found(self, cyto):
        mock_run = MagicMock(side_effect=FileNotFoundError)
        with patch.object(cyto["subprocess"], "run", mock_run):
            assert cyto["peira_status"]() is None


# ── latest_session_id ──────────────────────────────────────────────────────


class TestLatestSessionId:
    def test_found(self, cyto):
        mock_run = MagicMock(
            return_value=MagicMock(
                returncode=0,
                stdout="Session [abc123] 5 prompts (12:00) - Sonnet\n",
            )
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            assert cyto["latest_session_id"]() == "abc123"

    def test_not_found_nonzero(self, cyto):
        mock_run = MagicMock(return_value=MagicMock(returncode=1, stdout=""))
        with patch.object(cyto["subprocess"], "run", mock_run):
            assert cyto["latest_session_id"]() is None

    def test_timeout(self, cyto):
        mock_run = MagicMock(side_effect=subprocess.TimeoutExpired("engram", 10))
        with patch.object(cyto["subprocess"], "run", mock_run):
            assert cyto["latest_session_id"]() is None

    def test_no_hex_match(self, cyto):
        mock_run = MagicMock(
            return_value=MagicMock(returncode=0, stdout="nothing here\n")
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            assert cyto["latest_session_id"]() is None


# ── run_reflect ─────────────────────────────────────────────────────────────


class TestRunReflect:
    def test_success_with_findings(self, cyto):
        search_json = json.dumps([
            {"role": "you", "snippet": "no not that", "time": "12:00"},
            {"role": "assistant", "snippet": "ok fixing", "time": "12:01"},
        ])
        glm_output = (
            "---\nCATEGORY: taste_calibration\nQUOTE: no not that\n"
            "LESSON: prefer approach B\nMEMORY_TYPE: feedback\n---\n"
        )
        calls = [
            MagicMock(returncode=0, stdout=search_json),   # engram search
            MagicMock(returncode=0, stdout=glm_output),     # channel glm
        ]
        mock_run = MagicMock(side_effect=calls)
        with patch.object(cyto["subprocess"], "run", mock_run):
            findings, usage = cyto["run_reflect"]("abc123")
        assert len(findings) == 1
        assert findings[0]["category"] == "taste_calibration"
        assert usage["input_tokens"] > 0

    def test_empty_messages(self, cyto):
        mock_run = MagicMock(
            return_value=MagicMock(returncode=0, stdout="[]")
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            findings, usage = cyto["run_reflect"]("abc123")
        assert findings == []

    def test_engram_search_fails(self, cyto):
        mock_run = MagicMock(
            return_value=MagicMock(returncode=1, stdout="")
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            findings, usage = cyto["run_reflect"]("abc123")
        assert findings == []

    def test_timeout(self, cyto):
        mock_run = MagicMock(side_effect=subprocess.TimeoutExpired("engram", 30))
        with patch.object(cyto["subprocess"], "run", mock_run):
            findings, usage = cyto["run_reflect"]("abc123")
        assert findings == []


# ── run_methylation_audit ──────────────────────────────────────────────────


class TestRunMethylationAudit:
    def test_no_genome_returns_empty(self, cyto):
        # germline dir exists but has no genome.md
        result = cyto["run_methylation_audit"]()
        assert result == []

    def test_parses_candidates(self, cyto):
        genome = cyto["germline"] / "genome.md"
        genome.write_text("# Constitution\n- rule 1\n- rule 2\n", encoding="utf-8")

        # Create membrane dirs for hooks/skills discovery
        cytoskeleton = cyto["germline"] / "membrane" / "cytoskeleton"
        cytoskeleton.mkdir(parents=True)
        (cytoskeleton / "synapse.py").write_text(
            "def mod_check_foo(): pass\n", encoding="utf-8"
        )
        receptors = cyto["germline"] / "membrane" / "receptors"
        receptors.mkdir(parents=True)
        (receptors / "sortase").mkdir()
        (receptors / "sortase" / "SKILL.md").write_text("skill\n", encoding="utf-8")

        glm_output = (
            "---\nRULE: rule 1 description\nENFORCED_BY: mod_check_foo\n"
            "VERDICT: TRIM\n---\n---\nRULE: rule 2 description\n"
            "ENFORCED_BY: sortase\nVERDICT: KEEP\n---\n"
        )
        mock_run = MagicMock(
            return_value=MagicMock(returncode=0, stdout=glm_output)
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["run_methylation_audit"]()
        # Only TRIM/DEMOTE are included
        assert len(result) == 1
        assert result[0]["verdict"] == "TRIM"

    def test_channel_fails(self, cyto):
        genome = cyto["germline"] / "genome.md"
        genome.write_text("# Constitution\n", encoding="utf-8")
        mock_run = MagicMock(
            return_value=MagicMock(returncode=1, stdout="")
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["run_methylation_audit"]()
        assert result == []


# ── cmd_gather ──────────────────────────────────────────────────────────────


class TestCmdGather:
    def test_syntactic_json_output(self, cyto, capsys):
        # Mock all sub-functions
        cyto["skill_gaps"] = lambda: []
        cyto["cli_gaps"] = lambda: []
        cyto["now_age"] = lambda: ("fresh", 10)
        cyto["rfts_verify"] = lambda: []
        cyto["dep_check"] = lambda: []
        cyto["peira_status"] = lambda: None
        cyto["latest_session_id"] = lambda: None
        cyto["run_methylation_audit"] = lambda: []

        # Memory file for memory_lines
        cyto["MEMORY"].write_text("line\n", encoding="utf-8")

        # Mock git_status to return clean
        cyto["git_status"] = lambda p: ""

        args = _args(syntactic=True)
        cyto["cmd_gather"](args)

        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["repos"]["germline"]["clean"] is True
        assert data["now"]["age_label"] == "fresh"

    def test_perceptual_human_output(self, cyto, capsys):
        cyto["skill_gaps"] = lambda: []
        cyto["cli_gaps"] = lambda: []
        cyto["now_age"] = lambda: ("fresh", 10)
        cyto["rfts_verify"] = lambda: []
        cyto["dep_check"] = lambda: []
        cyto["peira_status"] = lambda: None
        cyto["latest_session_id"] = lambda: None
        cyto["run_methylation_audit"] = lambda: []
        cyto["MEMORY"].write_text("line\n", encoding="utf-8")
        cyto["git_status"] = lambda p: ""

        args = _args(perceptual=True)
        cyto["cmd_gather"](args)

        out = capsys.readouterr().out
        assert "Legatum Gather" in out
        assert "clean" in out

    def test_default_compact_output_dirty_repo(self, cyto, capsys):
        cyto["skill_gaps"] = lambda: ["skill_x"]
        cyto["cli_gaps"] = lambda: []
        cyto["now_age"] = lambda: ("stale", 7200)
        cyto["rfts_verify"] = lambda: []
        cyto["dep_check"] = lambda: []
        cyto["peira_status"] = lambda: None
        cyto["latest_session_id"] = lambda: None
        cyto["run_methylation_audit"] = lambda: []
        cyto["MEMORY"].write_text("line\n" * 10, encoding="utf-8")

        def fake_git_status(path):
            if path.name == "germline":
                return "M foo.py"
            return ""

        cyto["git_status"] = fake_git_status

        args = _args()
        cyto["cmd_gather"](args)

        out = capsys.readouterr().out
        assert "repo:germline dirty" in out
        assert "skills:unlinked skill_x" in out
        assert "now:stale" in out

    def test_memory_over_limit_shown(self, cyto, capsys):
        cyto["skill_gaps"] = lambda: []
        cyto["cli_gaps"] = lambda: []
        cyto["now_age"] = lambda: ("fresh", 10)
        cyto["rfts_verify"] = lambda: []
        cyto["dep_check"] = lambda: []
        cyto["peira_status"] = lambda: None
        cyto["latest_session_id"] = lambda: None
        cyto["run_methylation_audit"] = lambda: []
        cyto["git_status"] = lambda p: ""
        cyto["MEMORY_LIMIT"] = 5
        cyto["MEMORY"].write_text("line\n" * 10, encoding="utf-8")

        args = _args()
        cyto["cmd_gather"](args)

        out = capsys.readouterr().out
        assert "memory:10/5" in out

    def test_extra_repos(self, cyto, capsys):
        cyto["skill_gaps"] = lambda: []
        cyto["cli_gaps"] = lambda: []
        cyto["now_age"] = lambda: ("fresh", 10)
        cyto["rfts_verify"] = lambda: []
        cyto["dep_check"] = lambda: []
        cyto["peira_status"] = lambda: None
        cyto["latest_session_id"] = lambda: None
        cyto["run_methylation_audit"] = lambda: []
        cyto["MEMORY"].write_text("", encoding="utf-8")
        cyto["git_status"] = lambda p: ""

        extra = tmp_path_inner(cyto, "extra_repo")
        extra.mkdir()
        args = _args(syntactic=True, repos=str(extra))
        cyto["cmd_gather"](args)

        out = capsys.readouterr().out
        data = json.loads(out)
        assert "extra_repo" in data["repos"]


def tmp_path_inner(cyto, name):
    """Helper: get a tmp_path-derived path from the cyto fixture's home."""
    return cyto["home"] / name


# ── cmd_archive ─────────────────────────────────────────────────────────────


class TestCmdArchive:
    def test_archives_completed_items(self, cyto, capsys):
        cyto["praxis"].write_text(
            textwrap.dedent("""\
                # Praxis
                - [x] Done task
                - [ ] Open task
            """),
            encoding="utf-8",
        )
        cyto["cmd_archive"](MagicMock())
        praxis_text = cyto["praxis"].read_text(encoding="utf-8")
        assert "- [x] Done task" not in praxis_text
        assert "- [ ] Open task" in praxis_text
        archive_text = cyto["praxis_archive"].read_text(encoding="utf-8")
        assert "Done task" in archive_text

    def test_no_completed_items(self, cyto, capsys):
        cyto["praxis"].write_text(
            "- [ ] Only open tasks\n",
            encoding="utf-8",
        )
        cyto["cmd_archive"](MagicMock())
        out = capsys.readouterr().out
        assert "No completed items" in out

    def test_no_praxis_exits(self, cyto):
        assert not cyto["praxis"].exists()
        with pytest.raises(SystemExit):
            cyto["cmd_archive"](MagicMock())

    def test_adds_done_tag(self, cyto, capsys):
        cyto["praxis"].write_text(
            "- [x] Task without done tag\n",
            encoding="utf-8",
        )
        cyto["cmd_archive"](MagicMock())
        archive_text = cyto["praxis_archive"].read_text(encoding="utf-8")
        today = datetime.now().strftime("%Y-%m-%d")
        assert f"done:{today}" in archive_text

    def test_skips_children_of_completed(self, cyto, capsys):
        cyto["praxis"].write_text(
            textwrap.dedent("""\
                - [x] Parent done
                  - child detail skipped
                - [ ] Next open
            """),
            encoding="utf-8",
        )
        cyto["cmd_archive"](MagicMock())
        praxis_text = cyto["praxis"].read_text(encoding="utf-8")
        assert "child detail" not in praxis_text
        assert "Next open" in praxis_text

    def test_existing_month_section(self, cyto, capsys):
        month_header = f"## {datetime.now().strftime('%B %Y')}"
        cyto["praxis_archive"].write_text(
            f"# Archive\n\n{month_header}\n- old item\n",
            encoding="utf-8",
        )
        cyto["praxis"].write_text(
            "- [x] New done\n",
            encoding="utf-8",
        )
        cyto["cmd_archive"](MagicMock())
        archive_text = cyto["praxis_archive"].read_text(encoding="utf-8")
        assert "New done" in archive_text
        assert "old item" in archive_text


# ── cmd_daily ───────────────────────────────────────────────────────────────


class TestCmdDaily:
    def test_creates_new_daily(self, cyto, capsys):
        cyto["_gather_filed"] = lambda hours=2: []
        cyto["_gather_mechanised"] = lambda hours=2: []
        cyto["_gather_published"] = lambda: []
        args = _args(command="daily", title="My Session")
        cyto["cmd_daily"](args)

        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = cyto["DAILY_DIR"] / f"{today}.md"
        assert daily_file.exists()
        content = daily_file.read_text(encoding="utf-8")
        assert "My Session" in content
        assert "Outcomes" in content

    def test_appends_to_existing_daily(self, cyto, capsys):
        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = cyto["DAILY_DIR"] / f"{today}.md"
        daily_file.write_text(f"# {today} — existing\n", encoding="utf-8")

        cyto["_gather_filed"] = lambda hours=2: ["memory/test.md"]
        cyto["_gather_mechanised"] = lambda hours=2: []
        cyto["_gather_published"] = lambda: []
        args = _args(command="daily", title="Second Session")
        cyto["cmd_daily"](args)

        content = daily_file.read_text(encoding="utf-8")
        assert "Second Session" in content
        assert "test.md" in content

    def test_prefilled_sections(self, cyto, capsys):
        cyto["_gather_filed"] = lambda hours=2: ["memory/a.md", "memory/b.md"]
        cyto["_gather_mechanised"] = lambda hours=2: ["SKILL.md"]
        cyto["_gather_published"] = lambda: ["tweet published"]
        args = _args(command="daily", title="T")
        cyto["cmd_daily"](args)

        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = cyto["DAILY_DIR"] / f"{today}.md"
        content = daily_file.read_text(encoding="utf-8")
        assert "a.md" in content
        assert "SKILL.md" in content
        assert "tweet published" in content


# ── cmd_flush ───────────────────────────────────────────────────────────────


class TestCmdFlush:
    def test_all_clean(self, cyto, capsys):
        cyto["git_status"] = lambda p: ""
        result = cyto["cmd_flush"](MagicMock())
        assert result == []
        out = capsys.readouterr().out
        assert "clean" in out

    def test_commits_dirty_repo(self, cyto, capsys):
        def fake_git_status(path):
            if path.name == "germline":
                return "M file.py\n"
            return ""

        cyto["git_status"] = fake_git_status
        mock_run = MagicMock(
            return_value=MagicMock(returncode=0, stdout="", stderr="")
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["cmd_flush"](MagicMock())
        assert "germline" in result

    def test_unavailable_repo(self, cyto, capsys):
        cyto["git_status"] = lambda p: None
        result = cyto["cmd_flush"](MagicMock())
        assert result == []
        out = capsys.readouterr().out
        assert "unavailable" in out


# ── cmd_reflect ─────────────────────────────────────────────────────────────


class TestCmdReflect:
    def test_with_findings(self, cyto, capsys):
        findings = [{"category": "discovery", "lesson": "learned X", "quote": "wow"}]
        usage = {"input_tokens": 100, "output_tokens": 50}
        cyto["run_reflect"] = lambda sid: (findings, usage)
        args = _args(command="reflect", session="abc123", json=False)
        cyto["cmd_reflect"](args)
        out = capsys.readouterr().out
        assert "1 candidates" in out
        assert "discovery" in out.lower()

    def test_no_findings(self, cyto, capsys):
        cyto["run_reflect"] = lambda sid: ([], {})
        args = _args(command="reflect", session="abc123", json=False)
        cyto["cmd_reflect"](args)
        out = capsys.readouterr().out
        assert "No messages found" in out

    def test_json_output(self, cyto, capsys):
        findings = [{"category": "process_gap", "lesson": "Y"}]
        cyto["run_reflect"] = lambda sid: (findings, {})
        args = _args(command="reflect", session="abc123", json=True)
        cyto["cmd_reflect"](args)
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data[0]["category"] == "process_gap"


# ── cmd_extract ─────────────────────────────────────────────────────────────


class TestCmdExtract:
    def test_from_file(self, cyto, capsys, tmp_path):
        gather_json = tmp_path / "gather.json"
        gather_json.write_text(
            json.dumps({
                "reflect": [
                    {"category": "taste_calibration", "lesson": "L1", "quote": "Q1"}
                ]
            }),
            encoding="utf-8",
        )
        glm_output = "1. FILE | feedback | taste lesson\n"
        mock_run = MagicMock(
            return_value=MagicMock(returncode=0, stdout=glm_output)
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            args = _args(command="extract", input=str(gather_json))
            cyto["cmd_extract"](args)
        out = capsys.readouterr().out
        assert "FILE" in out

    def test_no_candidates(self, cyto, capsys, tmp_path):
        gather_json = tmp_path / "gather_empty.json"
        gather_json.write_text(json.dumps({"reflect": []}), encoding="utf-8")
        args = _args(command="extract", input=str(gather_json))
        cyto["cmd_extract"](args)
        out = capsys.readouterr().out
        assert "no candidates" in out

    def test_bad_json_exits(self, cyto, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not json", encoding="utf-8")
        args = _args(command="extract", input=str(bad))
        with pytest.raises(SystemExit):
            cyto["cmd_extract"](args)


# ── main (argument parsing) ────────────────────────────────────────────────


class TestMain:
    def test_no_command_exits(self, cyto):
        with patch.object(cyto["sys"], "argv", ["cytokinesis"]):
            with pytest.raises(SystemExit):
                cyto["main"]()

    def test_gather_routes(self, cyto, capsys):
        cyto["skill_gaps"] = lambda: []
        cyto["cli_gaps"] = lambda: []
        cyto["now_age"] = lambda: ("fresh", 5)
        cyto["rfts_verify"] = lambda: []
        cyto["dep_check"] = lambda: []
        cyto["peira_status"] = lambda: None
        cyto["latest_session_id"] = lambda: None
        cyto["run_methylation_audit"] = lambda: []
        cyto["MEMORY"].write_text("", encoding="utf-8")
        cyto["git_status"] = lambda p: ""

        with patch.object(cyto["sys"], "argv", ["cytokinesis", "gather"]):
            cyto["main"]()
        out = capsys.readouterr().out
        assert "now:fresh" in out


# ── Helpers: _since_flag, _gather helpers ──────────────────────────────────


class TestHelpers:
    def test_since_flag_format(self, cyto):
        ts = cyto["_since_flag"](hours=2)
        # Should be parseable as ISO-ish
        assert "T" in ts
        # Should be roughly 2 hours ago
        parsed = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
        delta = datetime.now() - parsed
        assert 7000 < delta.total_seconds() < 7300  # ~2 hours ± 5 min

    def test_gather_filed_no_dir(self, cyto):
        # Point home to a tmp location without the memory project dir
        cyto["home"] = Path("/nonexistent_home_xyz")
        result = cyto["_gather_filed"](hours=2)
        assert result == []

    def test_gather_published_no_logs(self, cyto):
        cyto["home"] = cyto["home"] / "empty_home"
        cyto["home"].mkdir()
        result = cyto["_gather_published"]()
        assert result == []
