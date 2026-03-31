"""Tests for golem-review — meta-golem that reviews golem output and queues work."""
from __future__ import annotations

import subprocess
import textwrap
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load():
    """Load golem-review by exec-ing its source."""
    source = open("/home/terry/germline/effectors/golem-review").read()
    ns: dict = {"__name__": "golem_review_test"}
    exec(source, ns)
    return ns


_mod = _load()

# Functions under test — these match the actual effector API
parse_since = _mod["parse_since"]
parse_log_timestamp = _mod["parse_log_timestamp"]
scan_log = _mod["scan_log"]
get_recent_files = _mod["get_recent_files"]
run_pytest_on_files = _mod["run_pytest_on_files"]
check_consulting_content = _mod["check_consulting_content"]
diagnose_failure = _mod["diagnose_failure"]
read_log_tail = _mod["read_log_tail"]
count_pending_tasks = _mod["count_pending_tasks"]
find_untested_modules = _mod["find_untested_modules"]
generate_queue_tasks = _mod["generate_queue_tasks"]
append_tasks_to_queue = _mod["append_tasks_to_queue"]
write_fixed_tasks = _mod["write_fixed_tasks"]
generate_review = _mod["generate_review"]
run_review = _mod["run_review"]

# Save originals for restore
_ORIG = {
    "QUEUE_FILE": _mod["QUEUE_FILE"],
    "LOGFILE": _mod["LOGFILE"],
    "REVIEW_FILE": _mod["REVIEW_FILE"],
    "COPIA_DIR": _mod["COPIA_DIR"],
    "GERMLINE": _mod["GERMLINE"],
    "EFFECTORS_DIR": _mod["EFFECTORS_DIR"],
    "ASSAYS_DIR": _mod["ASSAYS_DIR"],
}


def _restore():
    for k, v in _ORIG.items():
        _mod[k] = v


# ── parse_since ────────────────────────────────────────────────────────


class TestParseSince:
    def test_minutes(self):
        assert parse_since("30m") == timedelta(minutes=30)

    def test_hours(self):
        assert parse_since("2h") == timedelta(hours=2)

    def test_seconds(self):
        assert parse_since("60s") == timedelta(seconds=60)

    def test_days(self):
        assert parse_since("1d") == timedelta(days=1)

    def test_bare_number_is_minutes(self):
        assert parse_since("45") == timedelta(minutes=45)

    def test_invalid_returns_default(self):
        assert parse_since("abc") == timedelta(minutes=30)

    def test_whitespace_trimmed(self):
        assert parse_since("  15m  ") == timedelta(minutes=15)


# ── parse_log_timestamp ────────────────────────────────────────────────


class TestParseLogTimestamp:
    def test_valid(self):
        dt = parse_log_timestamp("2026-03-31 10:53:29")
        assert dt is not None
        assert dt.year == 2026 and dt.month == 3 and dt.day == 31

    def test_invalid(self):
        assert parse_log_timestamp("not-a-ts") is None

    def test_none(self):
        assert parse_log_timestamp(None) is None

    def test_empty(self):
        assert parse_log_timestamp("") is None


# ── parse_completed_tasks ──────────────────────────────────────────────


class TestParseCompletedTasks:
    def _now_str(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def test_completed_exit0(self):
        now = self._now_str()
        tasks = parse_completed_tasks(
            f"[{now}] Finished (120s, exit=0): golem --provider infini \"write tests\"\n",
            since_minutes=30,
        )
        assert len(tasks) == 1
        assert tasks[0]["exit_code"] == 0
        assert tasks[0]["duration_s"] == 120
        assert "write tests" in tasks[0]["cmd"]

    def test_failed_exit1(self):
        now = self._now_str()
        tasks = parse_completed_tasks(
            f"[{now}] Finished (5s, exit=1): golem \"broken task\"\n",
            since_minutes=30,
        )
        assert len(tasks) == 1
        assert tasks[0]["exit_code"] == 1

    def test_ignores_old_entries(self):
        old = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        tasks = parse_completed_tasks(
            f"[{old}] Finished (10s, exit=0): golem \"old\"\n",
            since_minutes=30,
        )
        assert tasks == []

    def test_mixed_lines(self):
        now = self._now_str()
        log = (
            f"[{now}] Finished (60s, exit=0): golem \"A\"\n"
            f"[{now}] Finished (30s, exit=1): golem \"B\"\n"
            f"[{now}] Starting: golem \"C\"\n"
            f"[{now}] Idle: 5 pending\n"
        )
        tasks = parse_completed_tasks(log, since_minutes=30)
        assert len(tasks) == 2

    def test_empty_log(self):
        assert parse_completed_tasks("", since_minutes=30) == []

    def test_binary_content(self):
        assert parse_completed_tasks("\x00\x01\x02\xff", since_minutes=30) == []


# ── diagnose_failure ───────────────────────────────────────────────────


class TestDiagnoseFailure:
    def test_timeout(self):
        r = diagnose_failure("golem task", "TIMEOUT after 1800s")
        assert r["diagnosis"] == "timeout"
        assert r["fixed_task"] != ""

    def test_import_error(self):
        r = diagnose_failure("golem task", "ModuleNotFoundError: lacuna")
        assert r["diagnosis"] == "import_error"

    def test_path_issue(self):
        r = diagnose_failure("golem task", "error at /home/terry/file.py")
        assert r["diagnosis"] == "path_issue"

    def test_syntax_error(self):
        r = diagnose_failure("golem task", "SyntaxError: invalid syntax")
        assert r["diagnosis"] == "syntax_error"

    def test_usage_error_exit2(self):
        r = diagnose_failure("golem task", "bad", exit_code=2)
        assert r["diagnosis"] == "usage_error"
        assert r["fixed_task"] == ""

    def test_unknown(self):
        r = diagnose_failure("golem task", "random output")
        assert r["diagnosis"] == "unknown"
        assert r["fixed_task"] == "golem task"

    def test_timeout_reduces_turns(self):
        r = diagnose_failure(
            'golem --max-turns 50 "task"', "TIMEOUT after 1800s"
        )
        assert "--max-turns 30" in r["fixed_task"]

    def test_returns_notes(self):
        r = diagnose_failure("golem task", "error", exit_code=2)
        assert isinstance(r["notes"], list)


# ── check_file_exists ──────────────────────────────────────────────────


class TestCheckFileExists:
    def test_exists(self, tmp_path):
        f = tmp_path / "x.txt"
        f.write_text("hi")
        assert check_file_exists(str(f)) is True

    def test_missing(self, tmp_path):
        assert check_file_exists(str(tmp_path / "nope")) is False


# ── count_words ────────────────────────────────────────────────────────


class TestCountWords:
    def test_counts(self, tmp_path):
        f = tmp_path / "d.md"
        f.write_text("word " * 100)
        assert count_words(str(f)) == 100

    def test_missing(self, tmp_path):
        assert count_words(str(tmp_path / "nope.md")) == 0

    def test_empty(self, tmp_path):
        f = tmp_path / "e.md"
        f.write_text("")
        assert count_words(str(f)) == 0

    def test_unreadable(self, tmp_path):
        f = tmp_path / "s.md"
        f.write_text("secret")
        f.chmod(0o000)
        try:
            assert count_words(str(f)) == 0
        finally:
            f.chmod(0o644)


# ── run_pytest_on_file ─────────────────────────────────────────────────


class TestRunPytestOnFile:
    def test_parses_output(self):
        def mock_run(cmd, capture_output, text, timeout, cwd=None):
            r = MagicMock()
            r.stdout = "3 passed, 1 failed\n"
            r.stderr = ""
            return r
        with patch("subprocess.run", side_effect=mock_run):
            p, f = run_pytest_on_file("assays/test_ex.py")
        assert p == 3 and f == 1

    def test_timeout(self):
        def mock_timeout(*a, **kw):
            raise subprocess.TimeoutExpired("cmd", 120)
        with patch("subprocess.run", side_effect=mock_timeout):
            p, f = run_pytest_on_file("assays/test_slow.py")
        assert p == 0 and f == 0

    def test_exception(self):
        def mock_err(*a, **kw):
            raise RuntimeError("broken")
        with patch("subprocess.run", side_effect=mock_err):
            p, f = run_pytest_on_file("assays/test_bad.py")
        assert p == 0 and f == 0


# ── count_pending_tasks ────────────────────────────────────────────────


class TestCountPendingTasks:
    def test_counts_correctly(self, tmp_path):
        q = tmp_path / "q.md"
        q.write_text(
            "- [ ] `golem \"a\"`\n"
            "- [!!] `golem \"b\"`\n"
            "- [x] `golem \"c\"`\n"
            "- [!] `golem \"d\"`\n"
            "- [ ] `golem \"e\"`\n"
        )
        _mod["QUEUE_FILE"] = q
        try:
            assert count_pending_tasks() == 4  # [ ], [!!], [!], [ ]
        finally:
            _restore()

    def test_missing_file(self, tmp_path):
        _mod["QUEUE_FILE"] = tmp_path / "nope.md"
        try:
            assert count_pending_tasks() == 0
        finally:
            _restore()

    def test_empty(self, tmp_path):
        q = tmp_path / "q.md"
        q.write_text("")
        _mod["QUEUE_FILE"] = q
        try:
            assert count_pending_tasks() == 0
        finally:
            _restore()


# ── generate_requeue_tasks ─────────────────────────────────────────────


class TestGenerateRequeueTasks:
    def test_returns_empty_at_50(self):
        assert generate_requeue_tasks(50) == []
        assert generate_requeue_tasks(100) == []

    def test_generates_for_untested(self, tmp_path):
        eff = tmp_path / "effectors"
        assays = tmp_path / "assays"
        eff.mkdir()
        assays.mkdir()
        _mod["EFFECTORS_DIR"] = eff
        _mod["ASSAYS_DIR"] = assays
        (eff / "alpha").write_text("#")
        (eff / "beta").write_text("#")
        (assays / "test_alpha.py").write_text("#")
        try:
            tasks = generate_requeue_tasks(0)
        finally:
            _restore()
        assert len(tasks) == 1
        assert "beta" in tasks[0]

    def test_limits_to_needed(self, tmp_path):
        eff = tmp_path / "effectors"
        assays = tmp_path / "assays"
        eff.mkdir()
        assays.mkdir()
        _mod["EFFECTORS_DIR"] = eff
        _mod["ASSAYS_DIR"] = assays
        for i in range(10):
            (eff / f"mod{i}").write_text("#")
        try:
            tasks = generate_requeue_tasks(45)
        finally:
            _restore()
        assert len(tasks) == 5

    def test_no_effectors_dir(self, tmp_path):
        _mod["EFFECTORS_DIR"] = tmp_path / "nonexistent"
        try:
            assert generate_requeue_tasks(0) == []
        finally:
            _restore()


# ── write_task_to_queue ────────────────────────────────────────────────


class TestWriteTaskToQueue:
    def test_appends_task(self, tmp_path):
        q = tmp_path / "q.md"
        q.write_text("# Queue\n\n## Pending\n\n## Done\n")
        _mod["QUEUE_FILE"] = q
        try:
            write_task_to_queue('golem "new task"')
        finally:
            _restore()
        content = q.read_text()
        assert "new task" in content
        assert "- [ ]" in content

    def test_high_priority(self, tmp_path):
        q = tmp_path / "q.md"
        q.write_text("# Queue\n\n## Pending\n\n## Done\n")
        _mod["QUEUE_FILE"] = q
        try:
            write_task_to_queue('golem "urgent"', priority="high")
        finally:
            _restore()
        content = q.read_text()
        assert "- [!!]" in content

    def test_creates_file(self, tmp_path):
        q = tmp_path / "new-q.md"
        _mod["QUEUE_FILE"] = q
        try:
            write_task_to_queue('golem "task"')
        finally:
            _restore()
        assert q.exists()
        assert "task" in q.read_text()


# ── build_review_summary ──────────────────────────────────────────────


class TestBuildReviewSummary:
    def test_basic(self):
        s = build_review_summary(
            completed=[{"cmd": "task A", "exit_code": 0, "duration_s": 60, "diagnosis": "success"}],
            failed=[{"cmd": "task B", "exit_code": 1, "diagnosis": "timeout", "notes": ["timed out"]}],
            test_results=[{"file": "test_foo.py", "passed": 5, "failed": 1}],
            content_results=[{"file": "brief.md", "word_count": 350}],
            requeue_count=2,
        )
        assert "Golem Review" in s
        assert "task A" in s
        assert "timeout" in s
        assert "test_foo.py" in s
        assert "brief.md" in s
        assert "Requeued: 2" in s

    def test_empty(self):
        s = build_review_summary([], [], [], [], 0)
        assert "(none)" in s
        assert "(no new test files)" in s
        assert "(no new content files)" in s

    def test_content_short(self):
        s = build_review_summary(
            [], [], [],
            [{"file": "short.md", "word_count": 50}],
            0,
        )
        assert "SHORT" in s

    def test_content_ok(self):
        s = build_review_summary(
            [], [], [],
            [{"file": "long.md", "word_count": 500}],
            0,
        )
        assert "OK" in s


# ── run_review integration ─────────────────────────────────────────────


def _setup_env(tmp_path):
    """Set up a temp germline environment for integration tests."""
    germline = tmp_path / "germline"
    _mod["GERMLINE"] = germline
    _mod["DAEMON_LOG"] = tmp_path / "golem-daemon.log"
    _mod["REVIEW_FILE"] = germline / "loci" / "copia" / "golem-review-latest.md"
    _mod["COPIA_DIR"] = germline / "loci" / "copia"
    _mod["QUEUE_FILE"] = germline / "loci" / "golem-queue.md"
    _mod["EFFECTORS_DIR"] = germline / "effectors"
    _mod["ASSAYS_DIR"] = germline / "assays"

    for d in [_mod["DAEMON_LOG"].parent, _mod["QUEUE_FILE"].parent,
              _mod["COPIA_DIR"], _mod["EFFECTORS_DIR"], _mod["ASSAYS_DIR"]]:
        d.mkdir(parents=True, exist_ok=True)

    _mod["DAEMON_LOG"].write_text("")
    _mod["QUEUE_FILE"].write_text("# Queue\n\n## Pending\n\n## Done\n")


class TestRunReview:
    def test_basic_no_tasks(self, tmp_path, capsys):
        _setup_env(tmp_path)
        try:
            rc = run_review(auto_requeue=False, since_str="30m")
        finally:
            _restore()
        assert rc == 0
        assert _mod["REVIEW_FILE"].exists()
        assert "Golem Review" in capsys.readouterr().out

    def test_with_completed_task(self, tmp_path, capsys):
        _setup_env(tmp_path)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _mod["DAEMON_LOG"].write_text(
            f"[{now}] Finished (100s, exit=0): golem --provider infini \"task A\"\n"
        )
        try:
            rc = run_review(auto_requeue=False, since_str="30m")
        finally:
            _restore()
        assert rc == 0
        out = capsys.readouterr().out
        assert "task A" in out

    def test_auto_requeue_generates_tasks(self, tmp_path, capsys):
        _setup_env(tmp_path)
        for i in range(5):
            (_mod["EFFECTORS_DIR"] / f"module-{i}").write_text(f"# {i}")
        try:
            rc = run_review(auto_requeue=True, since_str="30m")
        finally:
            _restore()
        assert rc == 0
        q = _mod["QUEUE_FILE"].read_text()
        # Should have auto-generated tasks
        assert any(f"module-{i}" in q for i in range(5))

    def test_auto_requeue_failed_task(self, tmp_path, capsys):
        _setup_env(tmp_path)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _mod["DAEMON_LOG"].write_text(
            f"[{now}] Finished (5s, exit=1): golem --provider infini \"broken task\"\n"
        )
        try:
            rc = run_review(auto_requeue=True, since_str="30m")
        finally:
            _restore()
        assert rc == 0
        out = capsys.readouterr().out
        assert "broken task" in out

    def test_no_daemon_log(self, tmp_path, capsys):
        _setup_env(tmp_path)
        _mod["DAEMON_LOG"] = tmp_path / "nonexistent.log"
        try:
            rc = run_review(auto_requeue=False, since_str="30m")
        finally:
            _restore()
        assert rc == 0


# ── Edge cases ─────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_parse_log_timestamp_none_input(self):
        assert parse_log_timestamp(None) is None

    def test_diagnose_empty_output(self):
        r = diagnose_failure("golem task", "", exit_code=1)
        assert r["diagnosis"] == "unknown"

    def test_parse_completed_tasks_none_input(self):
        assert parse_completed_tasks(None) == []  # type: ignore

    def test_write_task_to_unwritable(self, tmp_path):
        q = tmp_path / "readonly" / "q.md"
        q.parent.mkdir(parents=True)
        q.write_text("# Queue\n")
        q.chmod(0o444)
        _mod["QUEUE_FILE"] = q
        try:
            # Should not crash
            write_task_to_queue('golem "task"')
        finally:
            _restore()
            q.chmod(0o644)

    def test_count_pending_unreadable(self, tmp_path):
        q = tmp_path / "q.md"
        q.write_text("- [ ] `golem \"x\"`\n")
        q.chmod(0o000)
        _mod["QUEUE_FILE"] = q
        try:
            assert count_pending_tasks() == 0
        finally:
            _restore()
            q.chmod(0o644)
