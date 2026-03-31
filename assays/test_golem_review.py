"""Tests for golem-review — meta-golem that reviews golem output and queues work."""
from __future__ import annotations

import subprocess
import textwrap
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── Load module under test ──────────────────────────────────────────────

def _load_golem_review():
    """Load golem-review by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/golem-review").read()
    ns: dict = {"__name__": "golem_review"}
    exec(source, ns)
    return ns


_mod = _load_golem_review()

# Pull in key functions
parse_completed_tasks = _mod["parse_completed_tasks"]
diagnose_failure = _mod["diagnose_failure"]
check_file_exists = _mod["check_file_exists"]
count_words = _mod["count_words"]
parse_since_arg = _mod["parse_since_arg"]
build_review_summary = _mod["build_review_summary"]
generate_requeue_tasks = _mod["generate_requeue_tasks"]
run_pytest_on_file = _mod["run_pytest_on_file"]
count_pending_tasks = _mod["count_pending_tasks"]


# ── parse_since_arg ──────────────────────────────────────────────────────


class TestParseSinceArg:
    def test_default_returns_30_minutes(self):
        result = parse_since_arg("30m")
        assert result == 30

    def test_parses_minutes(self):
        assert parse_since_arg("5m") == 5
        assert parse_since_arg("120m") == 120

    def test_parses_hours(self):
        assert parse_since_arg("1h") == 60
        assert parse_since_arg("2h") == 120

    def test_unknown_suffix_returns_default(self):
        # Falls back to default 30 for unrecognized formats
        assert parse_since_arg("30x") == 30

    def test_pure_number_returns_default(self):
        assert parse_since_arg("30") == 30


# ── parse_completed_tasks ────────────────────────────────────────────────


_SAMPLE_LOG = textwrap.dedent("""\
    [2026-03-31 10:53:29] Daemon started
    [2026-03-31 10:53:29] Starting: golem --provider infini --max-turns 50 "Write tests for foo"...
    [2026-03-31 10:53:29] Finished (30s, exit=0): golem --provider infini --max-turns 50 "Write tests for foo"...
    [2026-03-31 10:53:29] Starting: golem --provider volcano "Build bar module"...
    [2026-03-31 10:54:29] Finished (60s, exit=1): golem --provider volcano "Build bar module"...
    [2026-03-31 10:55:29] FAILED (exit=1): golem --provider volcano "Build bar module"...
    [2026-03-31 10:55:30] VALIDATION WARN: golem --provider zhipu "check stuff"... → SyntaxError in assays/test_x.py
    [2026-03-31 10:56:00] Starting: golem --provider zhipu "Research topic"...
    [2026-03-31 10:57:00] Finished (60s, exit=0): golem --provider zhipu "Research topic"...
    [2026-03-31 10:58:00] Idle: 0 pending
""")


class TestParseCompletedTasks:
    def test_finds_successful_tasks(self):
        tasks = parse_completed_tasks(_SAMPLE_LOG, since_minutes=120)
        successes = [t for t in tasks if t["exit_code"] == 0]
        assert len(successes) == 2

    def test_finds_failed_tasks(self):
        tasks = parse_completed_tasks(_SAMPLE_LOG, since_minutes=120)
        failures = [t for t in tasks if t["exit_code"] != 0]
        assert len(failures) == 1
        assert failures[0]["exit_code"] == 1

    def test_extracts_command_text(self):
        tasks = parse_completed_tasks(_SAMPLE_LOG, since_minutes=120)
        cmds = [t["cmd"] for t in tasks]
        assert any("Write tests for foo" in c for c in cmds)

    def test_extracts_duration(self):
        tasks = parse_completed_tasks(_SAMPLE_LOG, since_minutes=120)
        success = [t for t in tasks if "Write tests" in t["cmd"]][0]
        assert success["duration_s"] == 30

    def test_empty_log_returns_empty(self):
        tasks = parse_completed_tasks("", since_minutes=30)
        assert tasks == []

    def test_no_finished_lines_returns_empty(self):
        log = "[2026-03-31 10:53:29] Daemon started\n[2026-03-31 10:54:00] Idle: 0 pending\n"
        tasks = parse_completed_tasks(log, since_minutes=30)
        assert tasks == []

    def test_old_entries_filtered_out(self):
        """Entries older than the window are excluded."""
        old_log = "[2020-01-01 00:00:00] Finished (10s, exit=0): golem \"old task\"...\n"
        tasks = parse_completed_tasks(old_log, since_minutes=30)
        assert tasks == []

    def test_extracts_timestamp(self):
        tasks = parse_completed_tasks(_SAMPLE_LOG, since_minutes=120)
        assert all("timestamp" in t for t in tasks)

    def test_returns_list_of_dicts(self):
        tasks = parse_completed_tasks(_SAMPLE_LOG, since_minutes=120)
        for t in tasks:
            assert "cmd" in t
            assert "exit_code" in t
            assert "duration_s" in t


# ── diagnose_failure ─────────────────────────────────────────────────────


class TestDiagnoseFailure:
    def test_timeout_diagnosis(self):
        result = diagnose_failure("golem --provider infini \"big task\"", "timeout after 1800s")
        assert result["diagnosis"] == "timeout"

    def test_import_error_diagnosis(self):
        result = diagnose_failure("golem \"task\"", "ImportError: No module named 'foo'")
        assert result["diagnosis"] == "import_error"

    def test_module_not_found_diagnosis(self):
        result = diagnose_failure("golem \"task\"", "ModuleNotFoundError: No module named 'bar'")
        assert result["diagnosis"] == "import_error"

    def test_path_error_diagnosis(self):
        result = diagnose_failure("golem \"task\"", "/home/terry/ not found")
        assert result["diagnosis"] == "path_issue"

    def test_syntax_error_diagnosis(self):
        result = diagnose_failure("golem \"task\"", "SyntaxError: invalid syntax")
        assert result["diagnosis"] == "syntax_error"

    def test_generic_failure(self):
        result = diagnose_failure("golem \"task\"", "something went wrong")
        assert result["diagnosis"] == "unknown"

    def test_exit_code_2_is_usage_error(self):
        result = diagnose_failure("golem \"task\"", "exit code 2", exit_code=2)
        assert result["diagnosis"] == "usage_error"

    def test_returns_fixed_task_info(self):
        result = diagnose_failure("golem --provider infini \"big task\"", "timeout after 1800s")
        assert "fixed_task" in result
        assert "big task" in result["fixed_task"]

    def test_timeout_gets_lower_turns(self):
        result = diagnose_failure(
            "golem --provider infini --max-turns 50 \"big task\"",
            "timeout after 1800s"
        )
        assert "--max-turns" in result["fixed_task"]
        m = __import__("re").search(r"--max-turns\s+(\d+)", result["fixed_task"])
        assert m is not None
        assert int(m.group(1)) < 50

    def test_timeout_adds_turns_when_missing(self):
        result = diagnose_failure("golem --provider infini \"big task\"", "timeout after 1800s")
        assert "--max-turns" in result["fixed_task"]

    def test_returns_notes(self):
        result = diagnose_failure("golem \"task\"", "timeout after 60s")
        assert "notes" in result
        assert len(result["notes"]) > 0


# ── check_file_exists ────────────────────────────────────────────────────


class TestCheckFileExists:
    def test_file_exists(self, tmp_path):
        f = tmp_path / "test_foo.py"
        f.write_text("pass")
        assert check_file_exists(str(f)) is True

    def test_file_missing(self, tmp_path):
        assert check_file_exists(str(tmp_path / "nonexistent.py")) is False


# ── count_words ──────────────────────────────────────────────────────────


class TestCountWords:
    def test_counts_words(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("word " * 250)
        assert count_words(str(f)) == 250

    def test_missing_file_returns_zero(self, tmp_path):
        assert count_words(str(tmp_path / "missing.md")) == 0

    def test_empty_file_returns_zero(self, tmp_path):
        f = tmp_path / "empty.md"
        f.write_text("")
        assert count_words(str(f)) == 0


# ── run_pytest_on_file ──────────────────────────────────────────────────


class TestRunPytestOnFile:
    def test_passing_test(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "1 passed"
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            passed, failed = run_pytest_on_file("assays/test_good.py")
        assert passed > 0
        assert failed == 0

    def test_failing_test(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "1 failed"
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            passed, failed = run_pytest_on_file("assays/test_bad.py")
        assert failed > 0

    def test_subprocess_timeout(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pytest", 120)):
            passed, failed = run_pytest_on_file("assays/test_slow.py")
        assert passed == 0
        assert failed == 0


# ── build_review_summary ────────────────────────────────────────────────


class TestBuildReviewSummary:
    def test_summary_contains_sections(self):
        summary = build_review_summary(
            completed=[{"cmd": "golem \"task1\"", "exit_code": 0, "duration_s": 30, "diagnosis": "success"}],
            failed=[],
            test_results=[{"file": "assays/test_a.py", "passed": 5, "failed": 0}],
            content_results=[{"file": "loci/copia/doc.md", "word_count": 300}],
            requeue_count=0,
        )
        assert "task1" in summary
        assert "assays/test_a.py" in summary

    def test_empty_summary(self):
        summary = build_review_summary(
            completed=[], failed=[], test_results=[], content_results=[], requeue_count=0
        )
        assert isinstance(summary, str)
        assert "Summary" in summary

    def test_failed_tasks_in_summary(self):
        summary = build_review_summary(
            completed=[],
            failed=[{"cmd": "golem \"bad\"", "exit_code": 1, "diagnosis": "timeout", "notes": "too slow"}],
            test_results=[],
            content_results=[],
            requeue_count=1,
        )
        assert "timeout" in summary
        assert "bad" in summary

    def test_content_quality_check(self):
        summary = build_review_summary(
            completed=[], failed=[], test_results=[],
            content_results=[{"file": "doc.md", "word_count": 50}],
            requeue_count=0,
        )
        assert "SHORT" in summary  # 50 < 200

    def test_content_quality_passes(self):
        summary = build_review_summary(
            completed=[], failed=[], test_results=[],
            content_results=[{"file": "doc.md", "word_count": 300}],
            requeue_count=0,
        )
        assert "OK" in summary


# ── generate_requeue_tasks ───────────────────────────────────────────────


class TestGenerateRequeueTasks:
    def test_generates_tasks_for_untested_effectors(self, tmp_path, monkeypatch):
        eff_dir = tmp_path / "germline" / "effectors"
        eff_dir.mkdir(parents=True)
        (eff_dir / "foo-tool").write_text("#!/bin/bash")
        (eff_dir / "bar-tool.py").write_text("pass")

        assay_dir = tmp_path / "germline" / "assays"
        assay_dir.mkdir(parents=True)
        # test for foo-tool exists, but not for bar-tool
        (assay_dir / "test_foo-tool.py").write_text("def test_foo(): pass")

        monkeypatch.setattr(_mod, "GERMLINE", tmp_path / "germline")
        monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
        tasks = generate_requeue_tasks(current_pending=0)
        assert isinstance(tasks, list)
        assert any("bar-tool" in t for t in tasks)

    def test_respects_max_count(self, tmp_path, monkeypatch):
        eff_dir = tmp_path / "germline" / "effectors"
        eff_dir.mkdir(parents=True)
        for i in range(100):
            (eff_dir / f"tool-{i}").write_text("#!/bin/bash")

        assay_dir = tmp_path / "germline" / "assays"
        assay_dir.mkdir(parents=True)

        monkeypatch.setattr(_mod, "GERMLINE", tmp_path / "germline")
        monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
        tasks = generate_requeue_tasks(current_pending=0)
        assert len(tasks) <= 50

    def test_returns_empty_when_enough_pending(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_mod, "GERMLINE", tmp_path / "germline")
        monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
        tasks = generate_requeue_tasks(current_pending=60)
        assert tasks == []

    def test_skips_test_prefixed_files(self, tmp_path, monkeypatch):
        eff_dir = tmp_path / "germline" / "effectors"
        eff_dir.mkdir(parents=True)
        (eff_dir / "test-dashboard").write_text("#!/bin/bash")

        assay_dir = tmp_path / "germline" / "assays"
        assay_dir.mkdir(parents=True)

        monkeypatch.setattr(_mod, "GERMLINE", tmp_path / "germline")
        monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
        tasks = generate_requeue_tasks(current_pending=0)
        # test-dashboard starts with "test" — should be skipped
        assert not any("test-dashboard" in t for t in tasks)

    def test_no_effectors_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_mod, "GERMLINE", tmp_path / "nonexistent")
        monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
        tasks = generate_requeue_tasks(current_pending=0)
        assert tasks == []


# ── count_pending_tasks ──────────────────────────────────────────────────


class TestCountPendingTasks:
    def test_counts_pending(self, tmp_path, monkeypatch):
        queue = tmp_path / "queue.md"
        queue.write_text(
            "- [ ] `golem \"task1\"`\n"
            "- [!] `golem \"task2\"`\n"
            "- [x] `golem \"task3\"`\n"
            "- [!!] `golem \"task4\"`\n"
        )
        monkeypatch.setattr(_mod, "QUEUE_FILE", queue)
        assert count_pending_tasks() == 3  # [ ], [!], [!!]

    def test_empty_queue(self, tmp_path, monkeypatch):
        queue = tmp_path / "queue.md"
        queue.write_text("# Queue\n\n")
        monkeypatch.setattr(_mod, "QUEUE_FILE", queue)
        assert count_pending_tasks() == 0

    def test_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(_mod, "QUEUE_FILE", tmp_path / "nonexistent.md")
        assert count_pending_tasks() == 0


# ── Main integration test ──────────────────────────────────────────────


class TestMainIntegration:
    def test_help_flag(self, capsys):
        with patch("sys.argv", ["golem-review", "--help"]):
            rc = _mod["main"]()
        assert rc == 0
        out = capsys.readouterr().out
        assert "golem-review" in out

    def test_once_flag_runs_review(self, tmp_path, monkeypatch, capsys):
        log_content = (
            "[2026-03-31 10:53:29] Finished (10s, exit=0): "
            "golem \"test task\"...\n"
        )
        log_file = tmp_path / "golem-daemon.log"
        log_file.write_text(log_content)
        queue_file = tmp_path / "germline" / "loci" / "golem-queue.md"
        queue_file.parent.mkdir(parents=True)
        queue_file.write_text("# Queue\n\n## Pending\n\n")
        report_dir = tmp_path / "germline" / "loci" / "copia"
        report_dir.mkdir(parents=True)

        monkeypatch.setattr(_mod, "DAEMON_LOG", log_file)
        monkeypatch.setattr(_mod, "QUEUE_FILE", queue_file)
        monkeypatch.setattr(_mod, "GERMLINE", tmp_path / "germline")
        monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)

        def mock_run(cmd, **kwargs):
            r = MagicMock()
            r.returncode = 0
            r.stdout = ""
            r.stderr = ""
            return r

        with patch("subprocess.run", side_effect=mock_run):
            with patch("sys.argv", ["golem-review", "--once", "--since", "30m"]):
                rc = _mod["main"]()

        assert rc == 0
        report_file = report_dir / "golem-review-latest.md"
        assert report_file.exists()

    def test_no_daemon_log_returns_early(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(_mod, "DAEMON_LOG", tmp_path / "nonexistent.log")
        with patch("sys.argv", ["golem-review", "--once"]):
            rc = _mod["main"]()
        assert rc == 0
        out = capsys.readouterr().out
        assert "No daemon log" in out

    def test_auto_requeue_writes_to_queue(self, tmp_path, monkeypatch, capsys):
        # Create a log with a failure
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_content = (
            f"[{now}] Finished (10s, exit=1): "
            f"golem --provider zhipu \"task to fix\"...\n"
        )
        log_file = tmp_path / "golem-daemon.log"
        log_file.write_text(log_content)
        queue_file = tmp_path / "germline" / "loci" / "golem-queue.md"
        queue_file.parent.mkdir(parents=True)
        queue_file.write_text("# Queue\n\n## Pending\n\n")
        report_dir = tmp_path / "germline" / "loci" / "copia"
        report_dir.mkdir(parents=True)
        eff_dir = tmp_path / "germline" / "effectors"
        eff_dir.mkdir(parents=True)

        monkeypatch.setattr(_mod, "DAEMON_LOG", log_file)
        monkeypatch.setattr(_mod, "QUEUE_FILE", queue_file)
        monkeypatch.setattr(_mod, "GERMLINE", tmp_path / "germline")
        monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)

        def mock_run(cmd, **kwargs):
            r = MagicMock()
            r.returncode = 0
            r.stdout = ""
            r.stderr = ""
            return r

        with patch("subprocess.run", side_effect=mock_run):
            with patch("sys.argv", ["golem-review", "--once", "--auto-requeue"]):
                rc = _mod["main"]()

        assert rc == 0
        queue_content = queue_file.read_text()
        assert "task to fix" in queue_content
