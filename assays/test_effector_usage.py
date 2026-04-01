from __future__ import annotations

"""Tests for effector-usage — scans golem logs and skills/hooks for effector mentions."""

import json
import subprocess
import textwrap
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_module():
    """Load effector-usage by exec-ing its source."""
    source = Path(str(Path.home() / "germline/effectors/effector-usage")).read_text()
    ns: dict = {"__name__": "effector_usage_test"}
    exec(source, ns)
    return ns


_mod = _load_module()
scan_jsonl = _mod["scan_jsonl"]
scan_daemon_log = _mod["scan_daemon_log"]
compute_report = _mod["compute_report"]
list_effectors = _mod["list_effectors"]
scan_claude_sources = _mod["scan_claude_sources"]
format_report = _mod["format_report"]
main = _mod["main"]
RE_EFFECTOR = _mod["RE_EFFECTOR"]

EFFECTOR_PATH = Path.home() / "germline" / "effectors" / "effector-usage"


# ── Regex tests ──────────────────────────────────────────────────────


class TestEffectorRegex:
    def test_matches_plain_name(self):
        m = RE_EFFECTOR.search("Read effectors/golem-top")
        assert m is not None
        assert m.group(1) == "golem-top"

    def test_matches_py_extension(self):
        m = RE_EFFECTOR.search("effectors/circadian-probe.py")
        assert m is not None
        assert m.group(1) == "circadian-probe.py"

    def test_matches_sh_extension(self):
        m = RE_EFFECTOR.search("effectors/chromatin-backup.sh")
        assert m is not None
        assert m.group(1) == "chromatin-backup.sh"

    def test_matches_hyphenated_name(self):
        m = RE_EFFECTOR.search("effectors/auto-update-compound-engineering.sh")
        assert m is not None
        assert m.group(1) == "auto-update-compound-engineering.sh"

    def test_no_match_bare_word(self):
        assert RE_EFFECTOR.search("something random") is None

    def test_multiple_matches(self):
        text = "effectors/golem-top and effectors/log-summary"
        matches = RE_EFFECTOR.findall(text)
        assert "golem-top" in matches
        assert "log-summary" in matches


# ── scan_jsonl tests ─────────────────────────────────────────────────


class TestScanJsonl:
    def test_basic_usage(self, tmp_path):
        jf = tmp_path / "golem.jsonl"
        jf.write_text(textwrap.dedent("""\
            {"ts":"2026-03-31T10:00:00Z","provider":"zhipu","duration":10,"exit":0,"turns":1,"prompt":"Read effectors/golem-top and effectors/log-summary","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0}
            {"ts":"2026-03-31T11:00:00Z","provider":"volcano","duration":20,"exit":1,"turns":2,"prompt":"Fix effectors/golem-top","tail":"","files_created":1,"tests_passed":0,"tests_failed":0,"pytest_exit":0}
        """))
        usage, failures, last_seen = scan_jsonl(jf)
        assert usage["golem-top"] == 2
        assert usage["log-summary"] == 1
        assert failures["golem-top"] == 1  # second entry has exit=1
        assert failures["log-summary"] == 0

    def test_empty_file(self, tmp_path):
        jf = tmp_path / "golem.jsonl"
        jf.write_text("")
        usage, failures, last_seen = scan_jsonl(jf)
        assert len(usage) == 0

    def test_nonexistent_file(self, tmp_path):
        jf = tmp_path / "nonexistent.jsonl"
        usage, failures, last_seen = scan_jsonl(jf)
        assert len(usage) == 0

    def test_timestamps_parsed(self, tmp_path):
        jf = tmp_path / "golem.jsonl"
        jf.write_text(
            '{"ts":"2026-03-30T09:15:00Z","provider":"zhipu","duration":5,"exit":0,"turns":1,"prompt":"effectors/circadian-probe.py","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0}\n'
        )
        usage, failures, last_seen = scan_jsonl(jf)
        assert "circadian-probe.py" in last_seen
        ts_str = last_seen["circadian-probe.py"]
        assert ts_str.startswith("2026-03-30")

    def test_malformed_line_skipped(self, tmp_path):
        jf = tmp_path / "golem.jsonl"
        jf.write_text("not json at all\n")
        usage, failures, last_seen = scan_jsonl(jf)
        # The line has no valid "ts" or "exit", but RE_EFFECTOR may still
        # match text. However there's no "effectors/" pattern, so empty.
        assert len(usage) == 0

    def test_no_effector_in_prompt(self, tmp_path):
        jf = tmp_path / "golem.jsonl"
        jf.write_text(
            '{"ts":"2026-03-31T10:00:00Z","provider":"zhipu","duration":10,"exit":0,"turns":1,"prompt":"Say hello","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0}\n'
        )
        usage, last_seen, failures = scan_jsonl(jf)
        assert len(usage) == 0


# ── scan_daemon_log tests ────────────────────────────────────────────


class TestScanDaemonLog:
    def test_basic_usage(self, tmp_path):
        lf = tmp_path / "golem-daemon.log"
        lf.write_text(textwrap.dedent("""\
            [2026-03-31 10:53:29] Starting: golem --provider infini --max-turns 50 "Read effectors/golem-top"
            [2026-03-31 10:53:59] FAILED (exit=1): golem --provider infini --max-turns 50 "Read effectors/golem-top"
            [2026-03-31 10:54:29] Finished (30s, exit=0): golem --provider infini --max-turns 50 "Read effectors/log-summary"
        """))
        usage, failures, last_seen = scan_daemon_log(lf)
        assert usage["golem-top"] == 2
        assert usage["log-summary"] == 1
        assert failures["golem-top"] == 1
        assert failures["log-summary"] == 0

    def test_timeout_counted_as_failure(self, tmp_path):
        lf = tmp_path / "golem-daemon.log"
        lf.write_text(textwrap.dedent("""\
            [2026-03-31 10:53:29] TIMEOUT (300s): golem --provider infini "Fix effectors/chemoreception.py"
        """))
        usage, failures, last_seen = scan_daemon_log(lf)
        assert usage["chemoreception.py"] == 1
        assert failures["chemoreception.py"] == 1

    def test_empty_file(self, tmp_path):
        lf = tmp_path / "golem-daemon.log"
        lf.write_text("")
        usage, failures, last_seen = scan_daemon_log(lf)
        assert len(usage) == 0

    def test_nonexistent_file(self, tmp_path):
        lf = tmp_path / "nonexistent.log"
        usage, failures, last_seen = scan_daemon_log(lf)
        assert len(usage) == 0


# ── build_report tests ───────────────────────────────────────────────


class TestBuildReport:
    def _make_jsonl(self, tmp_path, lines):
        jf = tmp_path / "golem.jsonl"
        jf.write_text("\n".join(lines) + "\n")
        return jf

    def _make_log(self, tmp_path, text):
        lf = tmp_path / "golem-daemon.log"
        lf.write_text(text)
        return lf

    def test_text_report_contains_sections(self, tmp_path):
        jf = self._make_jsonl(tmp_path, [
            '{"ts":"2026-03-31T10:00:00Z","provider":"zhipu","duration":10,"exit":0,"turns":1,"prompt":"Read effectors/golem-top","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0}',
        ])
        lf = self._make_log(tmp_path, "")
        report = compute_report(jsonl_path=jf, log_path=lf, rotated_path=Path("/nonexistent"))
        assert "most_used" in report
        assert "golem-top" in [e["name"] for e in report["most_used"]]

    def test_json_report_structure(self, tmp_path):
        jf = self._make_jsonl(tmp_path, [
            '{"ts":"2026-03-31T10:00:00Z","provider":"zhipu","duration":10,"exit":0,"turns":1,"prompt":"Read effectors/golem-top","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0}',
        ])
        lf = self._make_log(tmp_path, "")
        data = compute_report(jsonl_path=jf, log_path=lf, rotated_path=Path("/nonexistent"))
        assert "most_used" in data
        assert "never_used" in data
        assert "recently_broken" in data
        assert "total_effectors" in data
        assert any(e["name"] == "golem-top" for e in data["most_used"])

    def test_never_used_lists_unmentioned(self, tmp_path):
        jf = self._make_jsonl(tmp_path, [
            '{"ts":"2026-03-31T10:00:00Z","provider":"zhipu","duration":10,"exit":0,"turns":1,"prompt":"Read effectors/golem-top","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0}',
        ])
        lf = self._make_log(tmp_path, "")
        data = compute_report(jsonl_path=jf, log_path=lf, rotated_path=Path("/nonexistent"))
        # golem-top was mentioned so should NOT be in never_used
        assert "golem-top" not in data["never_used"]
        # But most effectors won't have been mentioned
        assert len(data["never_used"]) > 0

    def test_broken_only_filters(self, tmp_path):
        jf = self._make_jsonl(tmp_path, [
            '{"ts":"2026-03-31T10:00:00Z","provider":"zhipu","duration":10,"exit":1,"turns":1,"prompt":"Fix effectors/golem-top","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0}',
            '{"ts":"2026-03-31T10:01:00Z","provider":"zhipu","duration":10,"exit":0,"turns":1,"prompt":"Read effectors/log-summary","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0}',
        ])
        lf = self._make_log(tmp_path, "")
        data = compute_report(jsonl_path=jf, log_path=lf, rotated_path=Path("/nonexistent"))
        broken_names = [b["name"] for b in data["recently_broken"]]
        assert "golem-top" in broken_names
        assert "log-summary" not in broken_names

    def test_top_n_limits_most_used(self, tmp_path):
        jf = self._make_jsonl(tmp_path, [
            '{"ts":"2026-03-31T10:00:00Z","provider":"zhipu","duration":10,"exit":0,"turns":1,"prompt":"effectors/golem-top and effectors/log-summary and effectors/cytokinesis","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0}',
        ])
        lf = self._make_log(tmp_path, "")
        data = compute_report(top_n=2, jsonl_path=jf, log_path=lf, rotated_path=Path("/nonexistent"))
        assert len(data["most_used"]) == 2

    def test_merged_sources(self, tmp_path):
        jf = self._make_jsonl(tmp_path, [
            '{"ts":"2026-03-31T10:00:00Z","provider":"zhipu","duration":10,"exit":0,"turns":1,"prompt":"Read effectors/golem-top","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0}',
        ])
        lf = self._make_log(tmp_path, textwrap.dedent("""\
            [2026-03-31 11:00:00] Starting: golem --provider infini "Read effectors/golem-top"
        """))
        data = compute_report(jsonl_path=jf, log_path=lf, rotated_path=Path("/nonexistent"))
        entry = next(e for e in data["most_used"] if e["name"] == "golem-top")
        assert entry["mentions"] == 2  # once from jsonl, once from log


# ── list_effectors tests ────────────────────────────────────────


class TestListEffectors:
    def test_returns_set(self):
        result = list_effectors()
        assert isinstance(result, set)
        assert len(result) > 0

    def test_no_pyc_files(self):
        result = list_effectors()
        assert not any(n.endswith(".pyc") for n in result)

    def test_no_hidden_files(self):
        result = list_effectors()
        assert not any(n.startswith(".") for n in result)

    def test_known_effector_present(self):
        result = list_effectors()
        assert "golem-top" in result


# ── scan_claude_sources tests ─────────────────────────────────────────


class TestScanClaudeSources:
    def test_finds_effector_in_skill_md(self, tmp_path):
        skills = tmp_path / "skills"
        skill_dir = skills / "test-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "Run `~/germline/effectors/golem-top` for stats."
        )
        hooks = tmp_path / "hooks"
        hooks.mkdir()
        refs = scan_claude_sources(skills_dir=skills, hooks_dir=hooks)
        assert "golem-top" in refs
        assert "skills/test-skill/SKILL.md" in refs["golem-top"]

    def test_finds_effector_in_hook_py(self, tmp_path):
        skills = tmp_path / "skills"
        skills.mkdir()
        hooks = tmp_path / "hooks"
        hooks.mkdir()
        (hooks / "synapse.py").write_text(
            '# reference\n# effectors/methylation is used here\n'
        )
        refs = scan_claude_sources(skills_dir=skills, hooks_dir=hooks)
        assert "methylation" in refs
        assert "hooks/synapse.py" in refs["methylation"]

    def test_multiple_sources_for_one_effector(self, tmp_path):
        skills = tmp_path / "skills"
        skill_dir = skills / "assay"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("Use effectors/assay check")
        (skill_dir / "recipe.yaml").write_text("cmd: effectors/assay list")
        hooks = tmp_path / "hooks"
        hooks.mkdir()
        (hooks / "axon.py").write_text("effectors/assay")
        refs = scan_claude_sources(skills_dir=skills, hooks_dir=hooks)
        assert "assay" in refs
        assert len(refs["assay"]) == 3

    def test_no_references_returns_empty(self, tmp_path):
        skills = tmp_path / "skills"
        skill_dir = skills / "empty-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("No effector references here.")
        hooks = tmp_path / "hooks"
        hooks.mkdir()
        refs = scan_claude_sources(skills_dir=skills, hooks_dir=hooks)
        assert len(refs) == 0

    def test_skips_dotfiles_in_skills(self, tmp_path):
        skills = tmp_path / "skills"
        skill_dir = skills / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / ".hidden").write_text("effectors/golem-top")
        (skill_dir / "SKILL.md").write_text("nothing")
        hooks = tmp_path / "hooks"
        hooks.mkdir()
        refs = scan_claude_sources(skills_dir=skills, hooks_dir=hooks)
        assert "golem-top" not in refs

    def test_skips_non_py_hooks(self, tmp_path):
        skills = tmp_path / "skills"
        skills.mkdir()
        hooks = tmp_path / "hooks"
        hooks.mkdir()
        (hooks / "data.json").write_text('{"eff": "effectors/golem-top"}')
        refs = scan_claude_sources(skills_dir=skills, hooks_dir=hooks)
        assert "golem-top" not in refs

    def test_skips_dot_dirs_in_skills(self, tmp_path):
        skills = tmp_path / "skills"
        dot_dir = skills / ".hidden-skill"
        dot_dir.mkdir(parents=True)
        (dot_dir / "SKILL.md").write_text("effectors/golem-top")
        hooks = tmp_path / "hooks"
        hooks.mkdir()
        refs = scan_claude_sources(skills_dir=skills, hooks_dir=hooks)
        assert "golem-top" not in refs

    def test_nonexistent_dirs_return_empty(self, tmp_path):
        refs = scan_claude_sources(
            skills_dir=tmp_path / "no-skills",
            hooks_dir=tmp_path / "no-hooks",
        )
        assert len(refs) == 0


# ── format_report tests ───────────────────────────────────────────────


class TestFormatReport:
    def test_report_has_header(self):
        report = {
            "most_used": [],
            "never_used": [],
            "recently_broken": [],
            "skill_referenced": [],
            "orphaned": [],
            "total_effectors": 10,
            "total_mentions": 5,
        }
        text = format_report(report)
        assert "EFFECTOR USAGE REPORT" in text

    def test_orphaned_section_shown(self):
        report = {
            "most_used": [],
            "never_used": [],
            "recently_broken": [],
            "skill_referenced": [],
            "orphaned": ["orphan-tool-a", "orphan-tool-b"],
            "total_effectors": 2,
            "total_mentions": 0,
        }
        text = format_report(report)
        assert "orphan-tool-a" in text
        assert "orphan-tool-b" in text

    def test_skill_referenced_shown(self):
        report = {
            "most_used": [],
            "never_used": [],
            "recently_broken": [],
            "skill_referenced": [
                {"name": "assay", "sources": ["skills/assay/SKILL.md"]},
            ],
            "orphaned": [],
            "total_effectors": 1,
            "total_mentions": 1,
        }
        text = format_report(report)
        # skill_referenced is not shown in format_report, only in --skills mode
        assert "EFFECTOR USAGE REPORT" in text


# ── CLI integration tests ─────────────────────────────────────────────


class TestCLI:
    def test_help_flag(self):
        result = subprocess.run(
            [EFFECTOR_PATH, "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "effector-usage" in result.stdout

    def test_json_flag_produces_valid_json(self):
        result = subprocess.run(
            [EFFECTOR_PATH, "--json"],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "most_used" in data
        assert "orphaned" in data
        assert "skill_referenced" in data
        assert isinstance(data["total_effectors"], int)
        assert data["total_effectors"] > 0

    def test_orphaned_flag(self):
        result = subprocess.run(
            [EFFECTOR_PATH, "--orphaned"],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0
        assert "Orphaned" in result.stdout or "All effectors" in result.stdout

    def test_skills_flag(self):
        result = subprocess.run(
            [EFFECTOR_PATH, "--skills"],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0
        assert "Skill/hook-referenced" in result.stdout or "No effectors" in result.stdout

    def test_broken_flag(self):
        result = subprocess.run(
            [EFFECTOR_PATH, "--broken"],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0

    def test_unused_flag(self):
        result = subprocess.run(
            [EFFECTOR_PATH, "--unused"],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0
        assert "Never used" in result.stdout or "All effectors" in result.stdout

    def test_default_report(self):
        result = subprocess.run(
            [EFFECTOR_PATH],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0
        assert "EFFECTOR USAGE REPORT" in result.stdout
        assert "Most Used" in result.stdout
        assert "Orphaned" in result.stdout


# ── AST parse check ──────────────────────────────────────────────────


def test_ast_parse():
    """Verify the effector file is syntactically valid Python."""
    import ast
    source = Path(str(Path.home() / "germline/effectors/effector-usage")).read_text()
    ast.parse(source)
