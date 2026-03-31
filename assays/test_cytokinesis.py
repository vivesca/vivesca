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


# ═══════════════════════════════════════════════════════════════════════════════
# Extended coverage: edge cases, error paths, and integration scenarios
# ═══════════════════════════════════════════════════════════════════════════════


# ── rfts_verify: CLI tool detection, issues cap, file-type filtering ──────────


class TestRftsVerifyCliTools:
    def test_scan_suffix_flagged_as_missing(self, cyto):
        """Commands ending in -scan should be checked even without search/run context."""
        md = cyto["MEMORY"].parent / "tools.md"
        md.write_text(
            "We use `phantom-scan` for scanning.\n",
            encoding="utf-8",
        )
        result = cyto["rfts_verify"]()
        assert len(result) == 1
        assert any("cli missing: phantom-scan" in i for i in result[0]["issues"])

    def test_check_suffix_flagged(self, cyto):
        md = cyto["MEMORY"].parent / "checks.md"
        md.write_text("Run `ghost-check` for validation.\n", encoding="utf-8")
        result = cyto["rfts_verify"]()
        assert len(result) == 1
        assert any("cli missing: ghost-check" in i for i in result[0]["issues"])

    def test_run_context_flagged(self, cyto):
        """Backtick word after 'run' (lowercase) should be checked via shutil.which."""
        md = cyto["MEMORY"].parent / "runtool.md"
        md.write_text("We run `no_such_tool_ever` to build.\n", encoding="utf-8")
        result = cyto["rfts_verify"]()
        assert len(result) == 1
        assert any("cli missing: no_such_tool_ever" in i for i in result[0]["issues"])

    def test_search_context_flagged(self, cyto):
        md = cyto["MEMORY"].parent / "searchtool.md"
        md.write_text("Use search `imaginary_finder_xyz` for lookup.\n", encoding="utf-8")
        result = cyto["rfts_verify"]()
        assert len(result) == 1
        assert any("cli missing: imaginary_finder_xyz" in i for i in result[0]["issues"])

    def test_known_words_skipped(self, cyto):
        """Common non-command words like 'done', 'plan', 'build' should be skipped."""
        md = cyto["MEMORY"].parent / "common.md"
        md.write_text("The `plan` was `done`. `build` succeeded.\n", encoding="utf-8")
        result = cyto["rfts_verify"]()
        assert result == []

    def test_issues_capped_at_three(self, cyto):
        """More than 3 issues per file should be truncated to 3."""
        lines = []
        for i in range(5):
            lines.append(f"Refers to `/Users/terry/phantom/deep/path{i}`.")
        md = cyto["MEMORY"].parent / "many.md"
        md.write_text("\n".join(lines) + "\n", encoding="utf-8")
        result = cyto["rfts_verify"]()
        assert len(result) == 1
        assert len(result[0]["issues"]) == 3

    def test_non_md_files_skipped(self, cyto):
        """Files without .md suffix should be skipped."""
        txt_file = cyto["MEMORY"].parent / "notes.txt"
        txt_file.write_text("Refers to `/Users/terry/phantom/path/deep`.\n", encoding="utf-8")
        result = cyto["rfts_verify"]()
        assert result == []

    def test_memory_md_self_skipped(self, cyto):
        """MEMORY.md itself should be skipped."""
        cyto["MEMORY"].write_text(
            "Refers to `/Users/terry/phantom/path/deep`.\n", encoding="utf-8"
        )
        result = cyto["rfts_verify"]()
        assert result == []

    def test_glob_and_template_paths_skipped(self, cyto):
        """Paths with * or YYYY should not be flagged."""
        md = cyto["MEMORY"].parent / "templates.md"
        md.write_text(
            "Archive: `/Users/terry/logs/YYYY/MM/*.log`\n",
            encoding="utf-8",
        )
        result = cyto["rfts_verify"]()
        assert result == []

    def test_valid_path_not_flagged(self, cyto):
        """Paths that exist on disk (under home) should not be flagged."""
        real_dir = cyto["home"] / "real_project"
        real_dir.mkdir()
        (real_dir / "config.yml").write_text("ok\n", encoding="utf-8")
        md = cyto["MEMORY"].parent / "valid.md"
        # Use ~/ so the code resolves via home / path
        md.write_text("Config at `~/real_project/config.yml`.\n", encoding="utf-8")
        result = cyto["rfts_verify"]()
        assert result == []

    def test_md_suffix_fallback(self, cyto):
        """If exact path doesn't exist but .md version does, it's OK."""
        md_file = cyto["home"] / "some_ref.md"
        md_file.write_text("content\n", encoding="utf-8")
        md = cyto["MEMORY"].parent / "refcheck.md"
        # Reference ~/some_ref (no .md) but some_ref.md exists under home
        md.write_text("See `~/some_ref`.\n", encoding="utf-8")
        result = cyto["rfts_verify"]()
        assert result == []


# ── run_reflect: edge cases ───────────────────────────────────────────────────


class TestRunReflectEdgeCases:
    def test_bad_json_returns_empty(self, cyto):
        mock_run = MagicMock(
            return_value=MagicMock(returncode=0, stdout="not json{{{")
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            findings, usage = cyto["run_reflect"]("abc123")
        assert findings == []

    def test_glm_failure_returns_empty(self, cyto):
        """GLM (second call) returns nonzero → empty findings."""
        search_json = json.dumps([
            {"role": "you", "snippet": "hello", "time": "10:00"}
        ])
        calls = [
            MagicMock(returncode=0, stdout=search_json),
            MagicMock(returncode=1, stdout="error"),
        ]
        mock_run = MagicMock(side_effect=calls)
        with patch.object(cyto["subprocess"], "run", mock_run):
            findings, usage = cyto["run_reflect"]("abc123")
        assert findings == []
        assert usage["input_tokens"] > 0  # tokens counted from prompt

    def test_long_assistant_snippet_truncated(self, cyto):
        """Assistant snippets over 500 chars should be truncated."""
        long_text = "x" * 800
        search_json = json.dumps([
            {"role": "assistant", "snippet": long_text, "time": "10:00"},
        ])
        glm_output = "---\nCATEGORY: discovery\nLESSON: found it\n---\n"
        calls = [
            MagicMock(returncode=0, stdout=search_json),
            MagicMock(returncode=0, stdout=glm_output),
        ]
        mock_run = MagicMock(side_effect=calls)
        with patch.object(cyto["subprocess"], "run", mock_run):
            findings, usage = cyto["run_reflect"]("abc123")
        assert len(findings) == 1
        # The long snippet was truncated in the transcript but the call still succeeds
        assert usage["input_tokens"] > 0

    def test_you_snippet_not_truncated(self, cyto):
        """User snippets should NOT be truncated (role != 'you' check is for assistant)."""
        long_text = "y" * 800
        search_json = json.dumps([
            {"role": "you", "snippet": long_text, "time": "10:00"},
        ])
        glm_output = "---\nCATEGORY: taste_calibration\nLESSON: noted\n---\n"
        calls = [
            MagicMock(returncode=0, stdout=search_json),
            MagicMock(returncode=0, stdout=glm_output),
        ]
        mock_run = MagicMock(side_effect=calls)
        with patch.object(cyto["subprocess"], "run", mock_run):
            findings, usage = cyto["run_reflect"]("abc123")
        assert len(findings) == 1

    def test_multiple_findings_parsed(self, cyto):
        search_json = json.dumps([
            {"role": "you", "snippet": "first", "time": "10:00"},
        ])
        glm_output = (
            "---\nCATEGORY: discovery\nLESSON: lesson 1\n---\n"
            "---\nCATEGORY: process_gap\nLESSON: lesson 2\n---\n"
            "---\nCATEGORY: taste_calibration\nLESSON: lesson 3\n---\n"
        )
        calls = [
            MagicMock(returncode=0, stdout=search_json),
            MagicMock(returncode=0, stdout=glm_output),
        ]
        mock_run = MagicMock(side_effect=calls)
        with patch.object(cyto["subprocess"], "run", mock_run):
            findings, usage = cyto["run_reflect"]("abc123")
        assert len(findings) == 3
        assert usage["output_tokens"] > 0

    def test_partial_finding_without_closing_separator(self, cyto):
        """Finding without trailing --- should still be captured."""
        search_json = json.dumps([
            {"role": "you", "snippet": "hint", "time": "10:00"},
        ])
        glm_output = "---\nCATEGORY: discovery\nLESSON: partial\n"  # no trailing ---
        calls = [
            MagicMock(returncode=0, stdout=search_json),
            MagicMock(returncode=0, stdout=glm_output),
        ]
        mock_run = MagicMock(side_effect=calls)
        with patch.object(cyto["subprocess"], "run", mock_run):
            findings, usage = cyto["run_reflect"]("abc123")
        assert len(findings) == 1
        assert findings[0]["lesson"] == "partial"

    def test_empty_snippet_skipped(self, cyto):
        """Messages with empty snippet should not appear in transcript."""
        search_json = json.dumps([
            {"role": "you", "snippet": "", "time": "10:00"},
            {"role": "assistant", "snippet": "   ", "time": "10:01"},
        ])
        calls = [
            MagicMock(returncode=0, stdout=search_json),
        ]
        # With no transcript lines, glm is never called, but the function
        # returns [], {} since messages was truthy but transcript is empty
        mock_run = MagicMock(side_effect=calls)
        with patch.object(cyto["subprocess"], "run", mock_run):
            findings, usage = cyto["run_reflect"]("abc123")
        # Empty transcript → empty findings
        assert findings == []

    def test_glm_exception_returns_usage(self, cyto):
        """Exception during GLM call should still return usage with input_tokens."""
        search_json = json.dumps([
            {"role": "you", "snippet": "hello", "time": "10:00"},
        ])
        calls = [
            MagicMock(returncode=0, stdout=search_json),
            Exception("glm crashed"),
        ]
        mock_run = MagicMock(side_effect=calls)
        with patch.object(cyto["subprocess"], "run", mock_run):
            findings, usage = cyto["run_reflect"]("abc123")
        assert findings == []
        assert usage["input_tokens"] > 0


# ── run_methylation_audit: edge cases ─────────────────────────────────────────


class TestRunMethylationAuditEdgeCases:
    def test_demote_verdict_included(self, cyto):
        genome = cyto["germline"] / "genome.md"
        genome.write_text("# Genome\n- Rule A\n", encoding="utf-8")
        glm_output = (
            "---\nRULE: Rule A\nENFORCED_BY: hook\nVERDICT: DEMOTE\n---\n"
        )
        mock_run = MagicMock(
            return_value=MagicMock(returncode=0, stdout=glm_output)
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["run_methylation_audit"]()
        assert len(result) == 1
        assert result[0]["verdict"] == "DEMOTE"

    def test_keep_verdict_excluded(self, cyto):
        genome = cyto["germline"] / "genome.md"
        genome.write_text("# Genome\n- Rule A\n", encoding="utf-8")
        glm_output = "---\nRULE: Rule A\nENFORCED_BY: hook\nVERDICT: KEEP\n---\n"
        mock_run = MagicMock(
            return_value=MagicMock(returncode=0, stdout=glm_output)
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["run_methylation_audit"]()
        assert result == []

    def test_mixed_verdicts(self, cyto):
        genome = cyto["germline"] / "genome.md"
        genome.write_text("# Genome\n- R1\n- R2\n- R3\n", encoding="utf-8")
        glm_output = (
            "---\nRULE: R1\nENFORCED_BY: a\nVERDICT: TRIM\n---\n"
            "---\nRULE: R2\nENFORCED_BY: b\nVERDICT: KEEP\n---\n"
            "---\nRULE: R3\nENFORCED_BY: c\nVERDICT: DEMOTE\n---\n"
        )
        mock_run = MagicMock(
            return_value=MagicMock(returncode=0, stdout=glm_output)
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["run_methylation_audit"]()
        assert len(result) == 2
        verdicts = {r["verdict"] for r in result}
        assert verdicts == {"TRIM", "DEMOTE"}

    def test_timeout_returns_empty(self, cyto):
        genome = cyto["germline"] / "genome.md"
        genome.write_text("# Genome\n", encoding="utf-8")
        mock_run = MagicMock(
            side_effect=subprocess.TimeoutExpired("channel", 60)
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["run_methylation_audit"]()
        assert result == []

    def test_hook_discovery_mod_check_guard(self, cyto):
        """Verify hooks with def mod_, check_, guard_ prefixes are collected."""
        genome = cyto["germline"] / "genome.md"
        genome.write_text("# Genome\n- Rule\n", encoding="utf-8")
        cytoskeleton = cyto["germline"] / "membrane" / "cytoskeleton"
        cytoskeleton.mkdir(parents=True)
        (cytoskeleton / "synapse.py").write_text(
            "def mod_foo(): pass\ndef unrelated(): pass\ndef check_bar(): pass\n",
            encoding="utf-8",
        )
        (cytoskeleton / "axon.py").write_text(
            "def guard_baz(): pass\n",
            encoding="utf-8",
        )
        receptors = cyto["germline"] / "membrane" / "receptors"
        receptors.mkdir(parents=True)

        # We'll capture the prompt by intercepting the channel call
        glm_output = "---\nRULE: Rule\nENFORCED_BY: mod_foo\nVERDICT: TRIM\n---\n"
        mock_run = MagicMock(
            return_value=MagicMock(returncode=0, stdout=glm_output)
        )
        with patch.object(cyto["subprocess"], "run", mock_run) as mock:
            cyto["run_methylation_audit"]()
        # Verify the prompt includes the hook functions
        call_args = mock.call_args
        prompt = call_args[0][0][-1]  # -p flag value
        assert "mod_foo" in prompt
        assert "check_bar" in prompt
        assert "guard_baz" in prompt

    def test_skill_discovery(self, cyto):
        """Skills with SKILL.md should be listed in the audit prompt."""
        genome = cyto["germline"] / "genome.md"
        genome.write_text("# Genome\n- Rule\n", encoding="utf-8")
        receptors = cyto["germline"] / "membrane" / "receptors"
        receptors.mkdir(parents=True)
        for name in ["sortase", "telophase"]:
            skill_dir = receptors / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")

        glm_output = "---\nRULE: Rule\nVERDICT: KEEP\n---\n"
        mock_run = MagicMock(
            return_value=MagicMock(returncode=0, stdout=glm_output)
        )
        with patch.object(cyto["subprocess"], "run", mock_run) as mock:
            cyto["run_methylation_audit"]()
        call_args = mock.call_args
        prompt = call_args[0][0][-1]
        assert "sortase" in prompt
        assert "telophase" in prompt


# ── cmd_gather: integration with reflect, methylation, deps, peira ────────────


class TestCmdGatherIntegration:
    def _mock_basics(self, cyto, **overrides):
        """Set up common mocks for cmd_gather."""
        defaults = {
            "skill_gaps": lambda: [],
            "cli_gaps": lambda: [],
            "now_age": lambda: ("fresh", 10),
            "rfts_verify": lambda: [],
            "dep_check": lambda: [],
            "peira_status": lambda: None,
            "latest_session_id": lambda: None,
            "run_methylation_audit": lambda: [],
            "git_status": lambda p: "",
        }
        defaults.update(overrides)
        for k, v in defaults.items():
            cyto[k] = v
        cyto["MEMORY"].write_text("line\n", encoding="utf-8")

    def test_reflect_findings_in_syntactic(self, cyto, capsys):
        findings = [{"category": "discovery", "lesson": "found it"}]
        self._mock_basics(cyto,
            latest_session_id=lambda: "abc123",
            run_reflect=lambda sid: (findings, {"input_tokens": 50, "output_tokens": 20}),
        )
        args = _args(syntactic=True)
        cyto["cmd_gather"](args)
        data = json.loads(capsys.readouterr().out)
        assert data["reflect"] == findings
        assert data["reflect_session"] == "abc123"
        assert data["reflect_usage"]["input_tokens"] == 50

    def test_methylation_candidates_in_syntactic(self, cyto, capsys):
        meth = [{"rule": "no debug", "enforced_by": "hook", "verdict": "TRIM"}]
        self._mock_basics(cyto, run_methylation_audit=lambda: meth)
        args = _args(syntactic=True)
        cyto["cmd_gather"](args)
        data = json.loads(capsys.readouterr().out)
        assert len(data["methylation"]) == 1
        assert data["methylation"][0]["verdict"] == "TRIM"

    def test_dep_warnings_in_compact(self, cyto, capsys):
        self._mock_basics(cyto, dep_check=lambda: ["warn: outdated dep"])
        args = _args()
        cyto["cmd_gather"](args)
        out = capsys.readouterr().out
        assert "deps:" in out
        assert "outdated dep" in out

    def test_peira_status_in_compact(self, cyto, capsys):
        self._mock_basics(cyto, peira_status=lambda: "exp-42 running (3d)")
        args = _args()
        cyto["cmd_gather"](args)
        out = capsys.readouterr().out
        assert "peira:exp-42" in out

    def test_cli_gaps_in_compact(self, cyto, capsys):
        self._mock_basics(cyto, cli_gaps=lambda: ["myskill -> missing-tool"])
        args = _args()
        cyto["cmd_gather"](args)
        out = capsys.readouterr().out
        assert "skills:cli-missing myskill -> missing-tool" in out

    def test_rfts_stale_in_compact(self, cyto, capsys):
        rfts_data = [{"file": "stale.md", "issues": ["path: /bad/path"]}]
        self._mock_basics(cyto, rfts_verify=lambda: rfts_data)
        args = _args()
        cyto["cmd_gather"](args)
        out = capsys.readouterr().out
        assert "rfts:1 stale marks" in out
        assert "stale.md" in out

    def test_reflect_candidates_in_compact(self, cyto, capsys):
        findings = [{"category": "taste_calibration", "lesson": "prefers X"}]
        self._mock_basics(cyto,
            latest_session_id=lambda: "sess1",
            run_reflect=lambda sid: (findings, {"input_tokens": 100, "output_tokens": 50}),
        )
        args = _args()
        cyto["cmd_gather"](args)
        out = capsys.readouterr().out
        assert "reflect:1 candidates" in out
        assert "taste_calibration" in out

    def test_methylation_in_compact(self, cyto, capsys):
        meth = [{"rule": "redundant rule", "enforced_by": "hook_x", "verdict": "TRIM"}]
        self._mock_basics(cyto, run_methylation_audit=lambda: meth)
        args = _args()
        cyto["cmd_gather"](args)
        out = capsys.readouterr().out
        assert "methylation:1 demote candidates" in out
        assert "redundant rule" in out

    def test_unavailable_repo_syntactic(self, cyto, capsys):
        self._mock_basics(cyto, git_status=lambda p: None)
        args = _args(syntactic=True)
        cyto["cmd_gather"](args)
        data = json.loads(capsys.readouterr().out)
        assert data["repos"]["germline"]["clean"] is None
        assert data["repos"]["germline"]["status"] == "unavailable"


# ── _print_human: comprehensive human output ──────────────────────────────────


class TestPrintHuman:
    def test_full_output_with_all_sections(self, cyto, capsys):
        results = {
            "repos": {
                "germline": {"clean": True, "status": ""},
                "epigenome": {"clean": False, "status": "M file.py\n?? new.py"},
                "scripts": {"clean": None, "status": "unavailable"},
            },
            "skills": {
                "gaps": ["skill_z"],
                "cli_gaps": ["tool_a -> missing"],
            },
            "memory": {"lines": 200, "limit": 150},
            "now": {"age_label": "very stale", "age_seconds": 100000},
            "rfts": [{"file": "stale.md", "issues": ["path: /gone"]}],
            "deps": ["warn: dep outdated"],
            "peira": "exp-99 running",
            "reflect": [
                {"category": "discovery", "lesson": "learned X", "quote": "wow"},
            ],
            "methylation": [
                {"rule": "redundant", "enforced_by": "hook", "verdict": "TRIM"},
            ],
        }
        cyto["_print_human"](results, "sess1")
        out = capsys.readouterr().out
        assert "Legatum Gather" in out
        assert "germline" in out
        assert "2 dirty" in out  # epigenome has 2 lines
        assert "unavailable" in out
        assert "unlinked" in out
        assert "CLI missing" in out
        assert "200/150" in out
        assert "very stale" in out
        assert "stale marks" in out
        assert "dep:" in out
        assert "Peira" in out
        assert "Reflection" in out
        assert "Methylation" in out
        assert "TRIM" in out

    def test_all_clean_human_output(self, cyto, capsys):
        results = {
            "repos": {"germline": {"clean": True, "status": ""}},
            "skills": {"gaps": [], "cli_gaps": []},
            "memory": {"lines": 10, "limit": 150},
            "now": {"age_label": "fresh", "age_seconds": 10},
            "rfts": [],
            "deps": [],
            "peira": None,
            "reflect": [],
            "methylation": [],
        }
        cyto["_print_human"](results, None)
        out = capsys.readouterr().out
        assert "clean" in out
        assert "synced" in out
        assert "10/150" in out
        assert "fresh" in out
        assert "marks verified" in out
        assert "Deps: current" in out
        assert "Methylation: genome is lean" in out


# ── cmd_archive: edge cases ──────────────────────────────────────────────────


class TestCmdArchiveEdgeCases:
    def test_existing_done_tag_preserved(self, cyto):
        cyto["praxis"].write_text(
            "- [x] Task `done:2026-01-15`\n",
            encoding="utf-8",
        )
        cyto["cmd_archive"](MagicMock())
        archive = cyto["praxis_archive"].read_text(encoding="utf-8")
        # Should not have doubled the done tag
        assert archive.count("done:") == 1

    def test_creates_archive_if_missing(self, cyto, capsys):
        assert not cyto["praxis_archive"].exists()
        cyto["praxis"].write_text("- [x] First archived\n", encoding="utf-8")
        cyto["cmd_archive"](MagicMock())
        assert cyto["praxis_archive"].exists()
        archive = cyto["praxis_archive"].read_text(encoding="utf-8")
        assert "First archived" in archive

    def test_multiple_completed_items(self, cyto, capsys):
        cyto["praxis"].write_text(
            textwrap.dedent("""\
                - [x] Task A
                - [x] Task B
                - [ ] Task C
                - [x] Task D
            """),
            encoding="utf-8",
        )
        cyto["cmd_archive"](MagicMock())
        remaining = cyto["praxis"].read_text(encoding="utf-8")
        assert "Task C" in remaining
        assert "Task A" not in remaining
        archive = cyto["praxis_archive"].read_text(encoding="utf-8")
        assert "Task A" in archive
        assert "Task B" in archive
        assert "Task D" in archive
        out = capsys.readouterr().out
        assert "3 completed" in out

    def test_new_month_section_created(self, cyto, capsys):
        """When the current month header doesn't exist, it should be created."""
        cyto["praxis_archive"].write_text(
            "# Archive\n\n## January 2025\n\n- old item\n",
            encoding="utf-8",
        )
        cyto["praxis"].write_text("- [x] New item\n", encoding="utf-8")
        cyto["cmd_archive"](MagicMock())
        archive = cyto["praxis_archive"].read_text(encoding="utf-8")
        current_month = datetime.now().strftime("%B %Y")
        assert current_month in archive
        assert "New item" in archive
        assert "old item" in archive


# ── cmd_daily: edge cases ────────────────────────────────────────────────────


class TestCmdDailyEdgeCases:
    def test_no_title_uses_session(self, cyto, capsys):
        cyto["_gather_filed"] = lambda hours=2: []
        cyto["_gather_mechanised"] = lambda hours=2: []
        cyto["_gather_published"] = lambda: []
        args = _args(command="daily", title=None)
        cyto["cmd_daily"](args)
        today = datetime.now().strftime("%Y-%m-%d")
        content = (cyto["DAILY_DIR"] / f"{today}.md").read_text(encoding="utf-8")
        assert "Session" in content

    def test_custom_hours_passed(self, cyto, capsys):
        called_with = {}
        def fake_gather_filed(hours=2):
            called_with["hours"] = hours
            return []
        cyto["_gather_filed"] = fake_gather_filed
        cyto["_gather_mechanised"] = lambda hours=2: []
        cyto["_gather_published"] = lambda: []
        args = _args(command="daily", title="T", hours=4)
        cyto["cmd_daily"](args)
        assert called_with["hours"] == 4

    def test_daily_file_has_correct_structure(self, cyto, capsys):
        cyto["_gather_filed"] = lambda hours=2: ["memory/a.md"]
        cyto["_gather_mechanised"] = lambda hours=2: ["SKILL.md"]
        cyto["_gather_published"] = lambda: ["tweet: hello"]
        args = _args(command="daily", title="Structure Test")
        cyto["cmd_daily"](args)
        today = datetime.now().strftime("%Y-%m-%d")
        content = (cyto["DAILY_DIR"] / f"{today}.md").read_text(encoding="utf-8")
        assert "## Session: Structure Test" in content
        assert "### Outcomes" in content
        assert "### Filed" in content
        assert "### Published" in content
        assert "### Mechanised" in content
        assert "### Parked" in content
        assert "### Residual" in content
        assert "### Arc" in content
        assert "memory/a.md" in content
        assert "SKILL.md" in content
        assert "tweet: hello" in content


# ── cmd_flush: edge cases ────────────────────────────────────────────────────


class TestCmdFlushEdgeCases:
    def test_commit_failure_prints_error(self, cyto, capsys):
        def fake_git_status(path):
            return "M file.py\n" if path.name == "germline" else ""

        cyto["git_status"] = fake_git_status
        mock_run = MagicMock(side_effect=RuntimeError("commit lock"))
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["cmd_flush"](MagicMock())
        assert result == []
        out = capsys.readouterr().out
        assert "commit failed" in out

    def test_multiple_dirty_repos(self, cyto, capsys):
        def fake_git_status(path):
            return "M file.py\n"  # all repos dirty

        cyto["git_status"] = fake_git_status
        mock_run = MagicMock(
            return_value=MagicMock(returncode=0, stdout="", stderr="")
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["cmd_flush"](MagicMock())
        assert len(result) == 3  # germline, epigenome, scripts
        out = capsys.readouterr().out
        assert "committed" in out


# ── cmd_extract: error paths ──────────────────────────────────────────────────


class TestCmdExtractEdgeCases:
    def test_glm_failure_exits(self, cyto, tmp_path):
        gather_json = tmp_path / "gather.json"
        gather_json.write_text(
            json.dumps({"reflect": [{"category": "c", "lesson": "L"}]}),
            encoding="utf-8",
        )
        mock_run = MagicMock(
            return_value=MagicMock(returncode=1, stderr="model error")
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            args = _args(command="extract", input=str(gather_json))
            with pytest.raises(SystemExit):
                cyto["cmd_extract"](args)

    def test_glm_exception_exits(self, cyto, tmp_path):
        gather_json = tmp_path / "gather.json"
        gather_json.write_text(
            json.dumps({"reflect": [{"category": "c", "lesson": "L"}]}),
            encoding="utf-8",
        )
        mock_run = MagicMock(side_effect=RuntimeError("boom"))
        with patch.object(cyto["subprocess"], "run", mock_run):
            args = _args(command="extract", input=str(gather_json))
            with pytest.raises(SystemExit):
                cyto["cmd_extract"](args)


# ── _gather_filed: success path ───────────────────────────────────────────────


class TestGatherFiledSuccess:
    def test_returns_committed_files(self, cyto):
        mem_dir = cyto["home"] / ".claude" / "projects" / "-Users-terry" / "memory"
        mem_dir.mkdir(parents=True)
        # Mock 3 git calls: log, diff, ls-files
        calls = [
            MagicMock(returncode=0, stdout="notes.md\nother.md\n"),  # committed
            MagicMock(returncode=0, stdout="uncommitted.md\n"),       # diff
            MagicMock(returncode=0, stdout="new.md\n"),               # untracked
        ]
        mock_run = MagicMock(side_effect=calls)
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["_gather_filed"](hours=2)
        assert "memory/notes.md" in result
        assert "memory/uncommitted.md" in result
        assert "memory/new.md" in result

    def test_filters_memory_files(self, cyto):
        mem_dir = cyto["home"] / ".claude" / "projects" / "-Users-terry" / "memory"
        mem_dir.mkdir(parents=True)
        calls = [
            MagicMock(returncode=0, stdout="MEMORY.md\nnotes.md\n"),
            MagicMock(returncode=0, stdout=""),
            MagicMock(returncode=0, stdout=""),
        ]
        mock_run = MagicMock(side_effect=calls)
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["_gather_filed"](hours=2)
        assert all("MEMORY" not in f for f in result)
        assert "memory/notes.md" in result


# ── _gather_mechanised: success path ─────────────────────────────────────────


class TestGatherMechanisedSuccess:
    def test_finds_skill_files(self, cyto):
        git_output = "membrane/receptors/test-skill/SKILL.md\ndesign.md\n"
        calls = [
            MagicMock(returncode=0, stdout=git_output),
            MagicMock(returncode=0, stdout=""),
        ]
        mock_run = MagicMock(side_effect=calls)
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["_gather_mechanised"](hours=2)
        assert any("SKILL.md" in f for f in result)
        assert "design.md" not in result  # doesn't match keyword

    def test_includes_uncommitted(self, cyto):
        committed = "genome.md\n"
        uncommitted = "synapse.py\n"
        calls = [
            MagicMock(returncode=0, stdout=committed),
            MagicMock(returncode=0, stdout=uncommitted),
        ]
        mock_run = MagicMock(side_effect=calls)
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["_gather_mechanised"](hours=2)
        assert "genome.md" in result
        assert "synapse.py" in result

    def test_exception_returns_empty(self, cyto):
        mock_run = MagicMock(side_effect=subprocess.TimeoutExpired("git", 10))
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["_gather_mechanised"](hours=2)
        assert result == []


# ── _gather_published: success path ──────────────────────────────────────────


class TestGatherPublishedSuccess:
    def test_finds_published_entries(self, cyto):
        log_dir = cyto["home"] / "logs"
        log_dir.mkdir()
        today = datetime.now().strftime("%Y-%m-%d")
        (log_dir / "cron-exocytosis.log").write_text(
            f"{today} tweet published: hello world\n{today} other line\n",
            encoding="utf-8",
        )
        result = cyto["_gather_published"]()
        assert len(result) >= 1
        assert any("tweet" in r.lower() or "published" in r.lower() for r in result)

    def test_old_entries_not_included(self, cyto):
        log_dir = cyto["home"] / "logs"
        log_dir.mkdir()
        (log_dir / "cron-exocytosis.log").write_text(
            "2020-01-01 tweet published: old\n",
            encoding="utf-8",
        )
        result = cyto["_gather_published"]()
        assert result == []


# ── main: routing for all subcommands ─────────────────────────────────────────


class TestMainRouting:
    def test_archive_routes(self, cyto, capsys):
        cyto["praxis"].write_text("- [ ] nothing\n", encoding="utf-8")
        with patch.object(cyto["sys"], "argv", ["cytokinesis", "archive"]):
            cyto["main"]()
        out = capsys.readouterr().out
        assert "No completed items" in out

    def test_daily_routes(self, cyto, capsys):
        cyto["_gather_filed"] = lambda hours=2: []
        cyto["_gather_mechanised"] = lambda hours=2: []
        cyto["_gather_published"] = lambda: []
        with patch.object(cyto["sys"], "argv", ["cytokinesis", "daily", "Test"]):
            cyto["main"]()
        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = cyto["DAILY_DIR"] / f"{today}.md"
        assert daily_file.exists()

    def test_flush_routes(self, cyto, capsys):
        cyto["git_status"] = lambda p: ""
        with patch.object(cyto["sys"], "argv", ["cytokinesis", "flush"]):
            cyto["main"]()
        out = capsys.readouterr().out
        assert "clean" in out

    def test_reflect_routes(self, cyto, capsys):
        cyto["run_reflect"] = lambda sid: ([], {})
        with patch.object(cyto["sys"], "argv", ["cytokinesis", "reflect", "sess1"]):
            cyto["main"]()
        out = capsys.readouterr().out
        assert "No messages found" in out

    def test_extract_routes(self, cyto, tmp_path, capsys):
        gather_json = tmp_path / "g.json"
        gather_json.write_text(json.dumps({"reflect": []}), encoding="utf-8")
        with patch.object(cyto["sys"], "argv",
                          ["cytokinesis", "extract", "--input", str(gather_json)]):
            cyto["main"]()
        out = capsys.readouterr().out
        assert "no candidates" in out


# ── Color constants ───────────────────────────────────────────────────────────


class TestColorConstants:
    def test_reset_is_ansi(self, cyto):
        assert cyto["RESET"] == "\033[0m"

    def test_ok_includes_green_check(self, cyto):
        assert "\033[32m" in cyto["OK"]
        assert "✓" in cyto["OK"]

    def test_warn_includes_yellow(self, cyto):
        assert "\033[33m" in cyto["WARN"]

    def test_err_includes_red(self, cyto):
        assert "\033[31m" in cyto["ERR"]


# ── CLI subprocess (integration) ──────────────────────────────────────────────


class TestCLISubprocess:
    @pytest.mark.skipif(
        not Path("/Users/terry/germline").exists(),
        reason="Script has hardcoded macOS metabolon path",
    )
    def test_help_exits_zero(self):
        r = subprocess.run(
            ["uv", "run", "--script", str(CYTOKINESIS_PATH), "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode == 0
        assert "cytokinesis" in r.stdout.lower() or "session-close" in r.stdout.lower()

    @pytest.mark.skipif(
        not Path("/Users/terry/germline").exists(),
        reason="Script has hardcoded macOS metabolon path",
    )
    def test_gather_help(self):
        r = subprocess.run(
            ["uv", "run", "--script", str(CYTOKINESIS_PATH), "gather", "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode == 0
        assert "--syntactic" in r.stdout

    def test_no_subcommand_exits_nonzero(self):
        r = subprocess.run(
            ["uv", "run", "--script", str(CYTOKINESIS_PATH)],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode != 0

    def test_unknown_subcommand_exits_nonzero(self):
        r = subprocess.run(
            ["uv", "run", "--script", str(CYTOKINESIS_PATH), "nonexistent_xyz"],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode != 0


# ── now_age: boundary conditions ──────────────────────────────────────────────


class TestNowAgeBoundaries:
    def test_exactly_900_seconds_is_recent(self, cyto):
        """At exactly 900s (15 min boundary), should be 'recent', not 'fresh'."""
        now_md = cyto["NOW_MD"]
        now_md.write_text("boundary", encoding="utf-8")
        old_mtime = time.time() - 900
        os.utime(str(now_md), (old_mtime, old_mtime))
        label, _ = cyto["now_age"]()
        assert label == "recent"

    def test_exactly_3600_seconds_is_stale(self, cyto):
        now_md = cyto["NOW_MD"]
        now_md.write_text("boundary", encoding="utf-8")
        old_mtime = time.time() - 3600
        os.utime(str(now_md), (old_mtime, old_mtime))
        label, _ = cyto["now_age"]()
        assert label == "stale"

    def test_exactly_86400_seconds_is_very_stale(self, cyto):
        now_md = cyto["NOW_MD"]
        now_md.write_text("boundary", encoding="utf-8")
        old_mtime = time.time() - 86400
        os.utime(str(now_md), (old_mtime, old_mtime))
        label, _ = cyto["now_age"]()
        assert label == "very stale"

    def test_just_under_fresh_boundary(self, cyto):
        """At 899 seconds, still 'fresh'."""
        now_md = cyto["NOW_MD"]
        now_md.write_text("almost", encoding="utf-8")
        old_mtime = time.time() - 899
        os.utime(str(now_md), (old_mtime, old_mtime))
        label, _ = cyto["now_age"]()
        assert label == "fresh"

    def test_zero_seconds_is_fresh(self, cyto):
        """File touched right now should be fresh."""
        now_md = cyto["NOW_MD"]
        now_md.write_text("just created", encoding="utf-8")
        label, secs = cyto["now_age"]()
        assert label == "fresh"
        assert secs < 5


# ── skill_gaps: dotfiles, multiple gaps, ordering ─────────────────────────────


class TestSkillGapsEdgeCases:
    def test_dotfiles_excluded(self, cyto):
        """Dot-prefixed entries should be ignored in both dirs."""
        (cyto["SKILLS"] / ".hidden").mkdir()
        (cyto["claude_skills"] / ".hidden").mkdir()
        result = cyto["skill_gaps"]()
        assert result == []

    def test_multiple_gaps_sorted(self, cyto):
        """Multiple gaps should be returned in sorted order."""
        for name in ["zebra", "alpha", "mid"]:
            (cyto["SKILLS"] / name).mkdir()
        result = cyto["skill_gaps"]()
        assert result == ["alpha", "mid", "zebra"]

    def test_symlink_target_correct(self, cyto):
        """Auto-linked symlinks should point to the correct target."""
        (cyto["SKILLS"] / "target_skill").mkdir()
        cyto["skill_gaps"]()
        link = cyto["claude_skills"] / "target_skill"
        assert link.is_symlink()
        target = os.readlink(str(link))
        assert "target_skill" in target

    def test_claude_skills_dir_missing_returns_empty(self, cyto):
        """If claude_skills dir doesn't exist, should return empty."""
        (cyto["SKILLS"] / "orphan").mkdir()
        cyto["claude_skills"] = Path("/nonexistent_claude_skills_xyz")
        result = cyto["skill_gaps"]()
        assert result == []


# ── cli_gaps: multiple skills, empty cli name, exception ──────────────────────


class TestCliGapsEdgeCases:
    def test_multiple_skills_with_clis(self, cyto):
        """Multiple skills with missing CLIs should all be reported."""
        for name, cli in [("tool1", "nonexist_aaa"), ("tool2", "nonexist_bbb")]:
            d = cyto["SKILLS"] / name
            d.mkdir()
            (d / "SKILL.md").write_text(f"cli: {cli}\n", encoding="utf-8")
        result = cyto["cli_gaps"]()
        assert len(result) == 2

    def test_empty_cli_name_not_flagged(self, cyto):
        """'cli:' with empty value should not be flagged."""
        d = cyto["SKILLS"] / "empty_cli"
        d.mkdir()
        (d / "SKILL.md").write_text("cli: \n", encoding="utf-8")
        result = cyto["cli_gaps"]()
        assert result == []

    def test_cli_line_only_first_match(self, cyto):
        """Only the first 'cli:' line should be checked (break after match)."""
        d = cyto["SKILLS"] / "multi_cli"
        d.mkdir()
        (d / "SKILL.md").write_text(
            "cli: echo\ncli: nonexistent_zzz\n", encoding="utf-8"
        )
        result = cyto["cli_gaps"]()
        assert result == []  # echo exists, second line ignored

    def test_non_directory_entry_skipped(self, cyto):
        """Non-directory entries in SKILLS should be skipped."""
        (cyto["SKILLS"] / "readme.txt").write_text("not a skill\n", encoding="utf-8")
        result = cyto["cli_gaps"]()
        assert result == []


# ── rfts_verify: path variants, backtick paths ────────────────────────────────


class TestRftsVerifyPaths:
    def test_backtick_path_with_tilde(self, cyto):
        """Paths in backticks starting with ~/ should be resolved."""
        md = cyto["MEMORY"].parent / "tilde.md"
        md.write_text("See `~/nonexistent_dir_xyz/deep/path`.\n", encoding="utf-8")
        result = cyto["rfts_verify"]()
        assert len(result) == 1
        assert any("path:" in i for i in result[0]["issues"])

    def test_single_segment_path_ignored(self, cyto):
        """Paths with <2 segments like /ecphory should not be matched."""
        md = cyto["MEMORY"].parent / "short.md"
        md.write_text("Skill `/ecphory` is useful.\n", encoding="utf-8")
        result = cyto["rfts_verify"]()
        assert result == []

    def test_multiple_files_with_issues(self, cyto):
        """Multiple files with issues should all be reported."""
        for name in ["a.md", "b.md"]:
            md = cyto["MEMORY"].parent / name
            md.write_text(
                f"Refers to `/Users/terry/phantom/{name}/deep`.\n",
                encoding="utf-8",
            )
        result = cyto["rfts_verify"]()
        assert len(result) == 2

    def test_non_utf8_file_skipped(self, cyto):
        """Files that can't be decoded should be silently skipped."""
        md = cyto["MEMORY"].parent / "binary.md"
        md.write_bytes(b"\xff\xfe invalid utf8 `/Users/terry/a/b`\n")
        result = cyto["rfts_verify"]()
        assert result == []


# ── _print_human: edge cases ──────────────────────────────────────────────────


class TestPrintHumanEdgeCases:
    def test_no_session_id_with_clean_state(self, cyto, capsys):
        results = {
            "repos": {"germline": {"clean": True, "status": ""}},
            "skills": {"gaps": [], "cli_gaps": []},
            "memory": {"lines": 5, "limit": 150},
            "now": {"age_label": "fresh", "age_seconds": 5},
            "rfts": [],
            "deps": [],
            "peira": None,
            "reflect": [],
            "methylation": [],
        }
        cyto["_print_human"](results, None)
        out = capsys.readouterr().out
        assert "Legatum Gather" in out
        # No reflect section when no session id and no findings
        assert "Reflection" not in out

    def test_demote_verdict_yellow(self, cyto, capsys):
        """DEMOTE verdict should appear with color markers."""
        results = {
            "repos": {},
            "skills": {"gaps": [], "cli_gaps": []},
            "memory": {"lines": 5, "limit": 150},
            "now": {"age_label": "fresh", "age_seconds": 5},
            "rfts": [],
            "deps": [],
            "peira": None,
            "reflect": [],
            "methylation": [
                {"rule": "old rule", "enforced_by": "hook", "verdict": "DEMOTE"},
            ],
        }
        cyto["_print_human"](results, "sid")
        out = capsys.readouterr().out
        assert "DEMOTE" in out
        assert "old rule" in out

    def test_multiple_reflect_findings(self, cyto, capsys):
        results = {
            "repos": {},
            "skills": {"gaps": [], "cli_gaps": []},
            "memory": {"lines": 5, "limit": 150},
            "now": {"age_label": "fresh", "age_seconds": 5},
            "rfts": [],
            "deps": [],
            "peira": None,
            "reflect": [
                {"category": "discovery", "lesson": "L1", "quote": "Q1"},
                {"category": "process_gap", "lesson": "L2", "quote": ""},
            ],
            "methylation": [],
        }
        cyto["_print_human"](results, "sid")
        out = capsys.readouterr().out
        assert "2 candidates" in out
        assert "Discovery" in out
        assert "Process Gap" in out


# ── _gather_mechanised: keyword matching ──────────────────────────────────────


class TestGatherMechanisedKeywords:
    def test_dendrite_py_matched(self, cyto):
        calls = [
            MagicMock(returncode=0, stdout="dendrite.py\n"),
            MagicMock(returncode=0, stdout=""),
        ]
        mock_run = MagicMock(side_effect=calls)
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["_gather_mechanised"](hours=2)
        assert "dendrite.py" in result

    def test_axon_py_matched(self, cyto):
        calls = [
            MagicMock(returncode=0, stdout="axon.py\n"),
            MagicMock(returncode=0, stdout=""),
        ]
        mock_run = MagicMock(side_effect=calls)
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["_gather_mechanised"](hours=2)
        assert "axon.py" in result

    def test_irrelevant_files_not_matched(self, cyto):
        calls = [
            MagicMock(returncode=0, stdout="readme.md\nsetup.py\n"),
            MagicMock(returncode=0, stdout=""),
        ]
        mock_run = MagicMock(side_effect=calls)
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["_gather_mechanised"](hours=2)
        assert result == []


# ── cmd_archive: children handling ────────────────────────────────────────────


class TestCmdArchiveChildren:
    def test_non_child_after_completed_kept(self, cyto, capsys):
        """Lines after a completed item that aren't children should be kept."""
        cyto["praxis"].write_text(
            textwrap.dedent("""\
                - [x] Completed parent
                  - child skipped
                Regular text line
                - [ ] Open item
            """),
            encoding="utf-8",
        )
        cyto["cmd_archive"](MagicMock())
        remaining = cyto["praxis"].read_text(encoding="utf-8")
        assert "Regular text line" in remaining
        assert "Open item" in remaining
        assert "child skipped" not in remaining
        assert "Completed parent" not in remaining

    def test_nested_children_all_skipped(self, cyto, capsys):
        """Multiple consecutive children of a completed item are all skipped."""
        cyto["praxis"].write_text(
            textwrap.dedent("""\
                - [x] Done parent
                  - child 1
                  - child 2
                  - child 3
                - [ ] Next open
            """),
            encoding="utf-8",
        )
        cyto["cmd_archive"](MagicMock())
        remaining = cyto["praxis"].read_text(encoding="utf-8")
        assert "child 1" not in remaining
        assert "child 2" not in remaining
        assert "child 3" not in remaining
        assert "Next open" in remaining


# ── cmd_daily: residual count ─────────────────────────────────────────────────


class TestCmdDailyResidual:
    def test_residual_count_matches_filed(self, cyto, capsys):
        cyto["_gather_filed"] = lambda hours=2: ["a.md", "b.md", "c.md"]
        cyto["_gather_mechanised"] = lambda hours=2: []
        cyto["_gather_published"] = lambda: []
        args = _args(command="daily", title="R")
        cyto["cmd_daily"](args)
        today = datetime.now().strftime("%Y-%m-%d")
        content = (cyto["DAILY_DIR"] / f"{today}.md").read_text(encoding="utf-8")
        assert "filed=3" in content
        out = capsys.readouterr().out
        assert "Filed=3" in out

    def test_no_published_shows_none(self, cyto, capsys):
        cyto["_gather_filed"] = lambda hours=2: []
        cyto["_gather_mechanised"] = lambda hours=2: []
        cyto["_gather_published"] = lambda: []
        args = _args(command="daily", title="T")
        cyto["cmd_daily"](args)
        today = datetime.now().strftime("%Y-%m-%d")
        content = (cyto["DAILY_DIR"] / f"{today}.md").read_text(encoding="utf-8")
        assert "- none" in content


# ── latest_session_id: multi-line output ──────────────────────────────────────


class TestLatestSessionIdEdgeCases:
    def test_multiple_sessions_picks_last(self, cyto):
        """Should pick the last hex session ID from multi-line output."""
        mock_run = MagicMock(
            return_value=MagicMock(
                returncode=0,
                stdout=(
                    "Session [aaa111] 3 prompts (10:00) - Sonnet\n"
                    "Session [bbb222] 5 prompts (11:00) - Opus\n"
                ),
            )
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["latest_session_id"]()
        assert result == "bbb222"

    def test_mixed_content_extracts_hex(self, cyto):
        """Should extract hex ID even with non-session lines."""
        mock_run = MagicMock(
            return_value=MagicMock(
                returncode=0,
                stdout="header line\nSession [deadbeef] info\nfooter\n",
            )
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["latest_session_id"]()
        assert result == "deadbeef"


# ── run_reflect: env stripping ────────────────────────────────────────────────


class TestRunReflectEnv:
    def test_claudecode_stripped_from_env(self, cyto):
        """The CLAUDECODE env var should be removed from the GLM subprocess call."""
        search_json = json.dumps([
            {"role": "you", "snippet": "hi", "time": "10:00"}
        ])
        glm_output = "---\nCATEGORY: discovery\nLESSON: L\n---\n"
        calls = [
            MagicMock(returncode=0, stdout=search_json),
            MagicMock(returncode=0, stdout=glm_output),
        ]
        mock_run = MagicMock(side_effect=calls)
        with patch.object(cyto["subprocess"], "run", mock_run) as mock:
            cyto["run_reflect"]("abc123")
        # Second call (GLM) should have env without CLAUDECODE
        second_call = mock.call_args_list[1]
        env = second_call.kwargs.get("env") or second_call[1].get("env")
        assert "CLAUDECODE" not in env


# ── dep_check: nonzero exit ───────────────────────────────────────────────────


class TestDepCheckEdgeCases:
    def test_nonzero_exit_returns_empty(self, cyto):
        mock_run = MagicMock(
            return_value=MagicMock(returncode=1, stdout="error")
        )
        with patch.object(cyto["subprocess"], "run", mock_run):
            result = cyto["dep_check"]()
        assert result == []


# ── cmd_gather: unavailable repo in compact ───────────────────────────────────


class TestCmdGatherUnavailableRepo:
    def test_unavailable_repo_in_compact(self, cyto, capsys):
        """Unavailable repos should not appear in compact output at all."""
        cyto["skill_gaps"] = lambda: []
        cyto["cli_gaps"] = lambda: []
        cyto["now_age"] = lambda: ("fresh", 10)
        cyto["rfts_verify"] = lambda: []
        cyto["dep_check"] = lambda: []
        cyto["peira_status"] = lambda: None
        cyto["latest_session_id"] = lambda: None
        cyto["run_methylation_audit"] = lambda: []
        cyto["MEMORY"].write_text("line\n", encoding="utf-8")
        cyto["git_status"] = lambda p: None  # all unavailable

        args = _args()
        cyto["cmd_gather"](args)
        out = capsys.readouterr().out
        # Compact mode should show now:fresh but not repo dirt
        assert "now:fresh" in out
        # Dirty repos are printed; unavailable ones are skipped in compact mode
        assert "repo:" not in out
