"""Tests for effector-usage — scans golem logs for effector mentions."""
from __future__ import annotations

import json
import textwrap
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_module():
    """Load effector-usage by exec-ing its source."""
    source = Path("/home/terry/germline/effectors/effector-usage").read_text()
    ns: dict = {"__name__": "effector_usage_test"}
    exec(source, ns)
    return ns


_mod = _load_module()
scan_jsonl = _mod["scan_jsonl"]
scan_daemon_log = _mod["scan_daemon_log"]
compute_report = _mod["compute_report"]
list_effectors = _mod["list_effectors"]
RE_EFFECTOR = _mod["RE_EFFECTOR"]


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
        usage, last_seen, failures = scan_jsonl(jf)
        assert usage["golem-top"] == 2
        assert usage["log-summary"] == 1
        assert failures["golem-top"] == 1  # second entry has exit=1
        assert failures["log-summary"] == 0

    def test_empty_file(self, tmp_path):
        jf = tmp_path / "golem.jsonl"
        jf.write_text("")
        usage, last_seen, failures = scan_jsonl(jf)
        assert len(usage) == 0

    def test_nonexistent_file(self, tmp_path):
        jf = tmp_path / "nonexistent.jsonl"
        usage, last_seen, failures = scan_jsonl(jf)
        assert len(usage) == 0

    def test_timestamps_parsed(self, tmp_path):
        jf = tmp_path / "golem.jsonl"
        jf.write_text(
            '{"ts":"2026-03-30T09:15:00Z","provider":"zhipu","duration":5,"exit":0,"turns":1,"prompt":"effectors/circadian-probe.py","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0}\n'
        )
        usage, last_seen, failures = scan_jsonl(jf)
        assert "circadian-probe.py" in last_seen
        ts = last_seen["circadian-probe.py"][0]
        assert ts.year == 2026
        assert ts.month == 3
        assert ts.day == 30

    def test_malformed_line_skipped(self, tmp_path):
        jf = tmp_path / "golem.jsonl"
        jf.write_text("not json at all\n")
        usage, last_seen, failures = scan_jsonl(jf)
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
        usage, last_seen, failures = scan_daemon_log(lf)
        assert usage["golem-top"] == 2
        assert usage["log-summary"] == 1
        assert failures["golem-top"] == 1
        assert failures["log-summary"] == 0

    def test_timeout_counted_as_failure(self, tmp_path):
        lf = tmp_path / "golem-daemon.log"
        lf.write_text(textwrap.dedent("""\
            [2026-03-31 10:53:29] TIMEOUT (300s): golem --provider infini "Fix effectors/chemoreception.py"
        """))
        usage, last_seen, failures = scan_daemon_log(lf)
        assert usage["chemoreception.py"] == 1
        assert failures["chemoreception.py"] == 1

    def test_empty_file(self, tmp_path):
        lf = tmp_path / "golem-daemon.log"
        lf.write_text("")
        usage, last_seen, failures = scan_daemon_log(lf)
        assert len(usage) == 0

    def test_nonexistent_file(self, tmp_path):
        lf = tmp_path / "nonexistent.log"
        usage, last_seen, failures = scan_daemon_log(lf)
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
        report = build_report(jsonl_path=jf, log_path=lf, rotated_log_path=Path("/nonexistent"), as_json=True)
        data = json.loads(report)
        assert "most_used" in data
        assert "never_used" in data
        assert "recently_broken" in data
        assert "summary" in data
        assert any(e["name"] == "golem-top" for e in data["most_used"])

    def test_never_used_lists_unmentioned(self, tmp_path):
        jf = self._make_jsonl(tmp_path, [
            '{"ts":"2026-03-31T10:00:00Z","provider":"zhipu","duration":10,"exit":0,"turns":1,"prompt":"Read effectors/golem-top","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0}',
        ])
        lf = self._make_log(tmp_path, "")
        report = build_report(jsonl_path=jf, log_path=lf, rotated_log_path=Path("/nonexistent"), as_json=True)
        data = json.loads(report)
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
        report = build_report(jsonl_path=jf, log_path=lf, rotated_log_path=Path("/nonexistent"), broken_only=True, as_json=True)
        data = json.loads(report)
        broken_names = [b["name"] for b in data["recently_broken"]]
        assert "golem-top" in broken_names
        assert "log-summary" not in broken_names

    def test_top_n_limits_most_used(self, tmp_path):
        jf = self._make_jsonl(tmp_path, [
            '{"ts":"2026-03-31T10:00:00Z","provider":"zhipu","duration":10,"exit":0,"turns":1,"prompt":"effectors/golem-top and effectors/log-summary and effectors/cytokinesis","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0}',
        ])
        lf = self._make_log(tmp_path, "")
        report = build_report(jsonl_path=jf, log_path=lf, rotated_log_path=Path("/nonexistent"), top_n=2, as_json=True)
        data = json.loads(report)
        assert len(data["most_used"]) == 2

    def test_merged_sources(self, tmp_path):
        jf = self._make_jsonl(tmp_path, [
            '{"ts":"2026-03-31T10:00:00Z","provider":"zhipu","duration":10,"exit":0,"turns":1,"prompt":"Read effectors/golem-top","tail":"","files_created":0,"tests_passed":0,"tests_failed":0,"pytest_exit":0}',
        ])
        lf = self._make_log(tmp_path, textwrap.dedent("""\
            [2026-03-31 11:00:00] Starting: golem --provider infini "Read effectors/golem-top"
        """))
        report = build_report(jsonl_path=jf, log_path=lf, rotated_log_path=Path("/nonexistent"), as_json=True)
        data = json.loads(report)
        entry = next(e for e in data["most_used"] if e["name"] == "golem-top")
        assert entry["mentions"] == 2  # once from jsonl, once from log


# ── get_known_effectors tests ────────────────────────────────────────


class TestGetKnownEffectors:
    def test_returns_list(self):
        result = get_known_effectors()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_no_pyc_files(self):
        result = get_known_effectors()
        assert not any(n.endswith(".pyc") for n in result)

    def test_no_hidden_files(self):
        result = get_known_effectors()
        assert not any(n.startswith(".") for n in result)

    def test_known_effector_present(self):
        result = get_known_effectors()
        assert "golem-top" in result


# ── AST parse check ──────────────────────────────────────────────────


def test_ast_parse():
    """Verify the effector file is syntactically valid Python."""
    import ast
    source = Path("/home/terry/germline/effectors/effector-usage").read_text()
    ast.parse(source)
