from __future__ import annotations

"""Tests for golem-review — META-GOLEM review and requeue effector."""

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

# Functions under test
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


def _recent_ts(minutes_ago: int = 0) -> str:
    """Return a timestamp string N minutes ago from now."""
    ts = datetime.now() - timedelta(minutes=minutes_ago)
    return ts.strftime("%Y-%m-%d %H:%M:%S")


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

    def test_empty(self):
        assert parse_log_timestamp("") is None


# ── scan_log ───────────────────────────────────────────────────────────


class TestScanLog:
    def _make_log(self, tmp_path, lines):
        log_path = tmp_path / "golem-daemon.log"
        log_path.write_text("\n".join(lines) + "\n")
        return log_path

    def test_completed_task_found(self, tmp_path):
        ts = _recent_ts(5)
        log_path = self._make_log(tmp_path, [
            f"[{ts}] Starting: golem task1",
            f"[{ts}] Finished (60s, exit=0): golem task1...",
        ])
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert len(result["completed"]) == 1
        assert result["completed"][0][1] == "golem task1"
        assert len(result["failed"]) == 0

    def test_failed_task_found(self, tmp_path):
        ts = _recent_ts(2)
        log_path = self._make_log(tmp_path, [
            f"[{ts}] FAILED (exit=1): golem task...",
        ])
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert len(result["failed"]) == 1
        assert len(result["completed"]) == 0

    def test_timeout_detected(self, tmp_path):
        ts = _recent_ts(1)
        log_path = self._make_log(tmp_path, [
            f"[{ts}] TIMEOUT (1800s): golem slow-task...",
        ])
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert len(result["timeouts"]) == 1

    def test_old_entries_excluded(self, tmp_path):
        log_path = self._make_log(tmp_path, [
            "[2020-01-01 00:00:00] Finished (60s, exit=0): old task...",
        ])
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert len(result["completed"]) == 0

    def test_missing_log_file(self, tmp_path):
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = tmp_path / "nonexistent.log"
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert result["completed"] == []
        assert result["failed"] == []

    def test_mixed(self, tmp_path):
        log_path = self._make_log(tmp_path, [
            f"[{_recent_ts(10)}] Finished (10s, exit=0): task1",
            f"[{_recent_ts(9)}] FAILED (exit=1): task2",
            f"[{_recent_ts(8)}] Finished (5s, exit=0): task3",
            f"[{_recent_ts(7)}] TIMEOUT (1800s): task4",
        ])
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert len(result["completed"]) == 2
        assert len(result["failed"]) == 1
        assert len(result["timeouts"]) == 1

    def test_empty_log(self, tmp_path):
        log_path = self._make_log(tmp_path, [])
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert result["completed"] == []
        assert result["failed"] == []

    def test_finished_nonzero_exit_is_failed(self, tmp_path):
        ts = _recent_ts(3)
        log_path = self._make_log(tmp_path, [
            f"[{ts}] Finished (30s, exit=2): golem bad-cmd...",
        ])
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert len(result["failed"]) == 1
        assert len(result["completed"]) == 0


# ── diagnose_failure ───────────────────────────────────────────────────


class TestDiagnoseFailure:
    def test_import_error(self):
        r = diagnose_failure("golem task", "ModuleNotFoundError: foo")
        assert "import_error" in r

    def test_syntax_error(self):
        r = diagnose_failure("golem task", "SyntaxError: invalid")
        assert "syntax_error" in r

    def test_hardcoded_path(self):
        r = diagnose_failure("golem /Users/terry/ task", "")
        assert "path_issue" in r

    def test_timeout(self):
        r = diagnose_failure("golem task", "timeout after 1800s")
        assert "timeout" in r

    def test_permission_error(self):
        r = diagnose_failure("golem task", "PermissionError: denied")
        assert "permission_error" in r

    def test_exit_code_2(self):
        r = diagnose_failure("golem task exit=2", "")
        assert "command_error" in r

    def test_unknown(self):
        r = diagnose_failure("golem task", "something weird")
        assert "unknown" in r

    def test_assertion_error(self):
        r = diagnose_failure("golem task", "assert False")
        assert "assertion_error" in r


# ── get_recent_files ───────────────────────────────────────────────────


class TestGetRecentFiles:
    def test_returns_files(self):
        def mock_run(cmd, **kw):
            r = MagicMock()
            r.returncode = 0 if "diff" in cmd else 1
            r.stdout = "assays/test_foo.py\neffectors/bar.py\n" if "diff" in cmd else ""
            r.stderr = ""
            return r
        with patch("subprocess.run", side_effect=mock_run):
            result = get_recent_files(5)
        assert "assays/test_foo.py" in result

    def test_git_failure(self):
        def mock_run(cmd, **kw):
            r = MagicMock()
            r.returncode = 128
            r.stdout = ""
            r.stderr = "fatal"
            return r
        with patch("subprocess.run", side_effect=mock_run):
            result = get_recent_files()
        assert result == []


# ── run_pytest_on_files ────────────────────────────────────────────────


class TestRunPytestOnFiles:
    def test_passing(self):
        def mock_run(cmd, **kw):
            r = MagicMock()
            r.returncode = 0
            r.stdout = "5 passed in 1.2s"
            r.stderr = ""
            return r
        with patch("subprocess.run", side_effect=mock_run):
            result = run_pytest_on_files(["assays/test_ex.py"])
        assert result["total_passed"] == 5

    def test_failing(self):
        def mock_run(cmd, **kw):
            r = MagicMock()
            r.returncode = 1
            r.stdout = "3 passed, 2 failed"
            r.stderr = ""
            return r
        with patch("subprocess.run", side_effect=mock_run):
            result = run_pytest_on_files(["assays/test_brk.py"])
        assert result["total_failed"] == 2

    def test_empty(self):
        result = run_pytest_on_files([])
        assert result["total_passed"] == 0

    def test_timeout(self):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("c", 1)):
            result = run_pytest_on_files(["assays/test_slow.py"])
        assert result["total_errors"] == 1


# ── check_consulting_content ───────────────────────────────────────────


class TestCheckConsultingContent:
    def test_enough_words(self, tmp_path):
        f = tmp_path / "deep.md"
        f.write_text(" ".join(["word"] * 250))
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["deep.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["adequate"] is True

    def test_too_short(self, tmp_path):
        f = tmp_path / "thin.md"
        f.write_text("short")
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["thin.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["adequate"] is False

    def test_missing(self, tmp_path):
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            r = check_consulting_content(["nope.md"])
        finally:
            _mod["GERMLINE"] = orig
        assert r[0]["exists"] is False


# ── read_log_tail ──────────────────────────────────────────────────────


class TestReadLogTail:
    def test_last_n(self, tmp_path):
        log_path = tmp_path / "golem-daemon.log"
        log_path.write_text("\n".join([f"line {i}" for i in range(10)]))
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            tail = read_log_tail(3)
        finally:
            _mod["LOGFILE"] = orig
        assert "line 7" in tail
        assert "line 0" not in tail

    def test_missing(self, tmp_path):
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = tmp_path / "nope.log"
            tail = read_log_tail()
        finally:
            _mod["LOGFILE"] = orig
        assert tail == ""


# ── count_pending_tasks ────────────────────────────────────────────────


class TestCountPendingTasks:
    def _make_queue(self, tmp_path, content):
        qd = tmp_path / "germline" / "loci"
        qd.mkdir(parents=True)
        qf = qd / "golem-queue.md"
        qf.write_text(content)
        return qf

    def test_counts(self, tmp_path):
        qf = self._make_queue(tmp_path, (
            "- [ ] `golem \"a\"`\n"
            "- [!!] `golem \"b\"`\n"
            "- [x] `golem \"c\"`\n"
            "- [!] `golem \"d\"`\n"
            "- [ ] `golem \"e\"`\n"
        ))
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            assert count_pending_tasks() == 3
        finally:
            _mod["QUEUE_FILE"] = orig

    def test_empty(self, tmp_path):
        qf = self._make_queue(tmp_path, "")
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            assert count_pending_tasks() == 0
        finally:
            _mod["QUEUE_FILE"] = orig

    def test_missing(self, tmp_path):
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = tmp_path / "nope.md"
            assert count_pending_tasks() == 0
        finally:
            _mod["QUEUE_FILE"] = orig


# ── find_untested_modules ──────────────────────────────────────────────


class TestFindUntestedModules:
    def test_finds_untested(self, tmp_path):
        eff = tmp_path / "effectors"
        eff.mkdir()
        (eff / "foo-tool").write_text("#")
        (eff / "bar.py").write_text("#")
        assays = tmp_path / "assays"
        assays.mkdir()
        (assays / "test_foo_tool.py").write_text("#")
        orig_e = _mod["EFFECTORS_DIR"]
        orig_a = _mod["ASSAYS_DIR"]
        try:
            _mod["EFFECTORS_DIR"] = eff
            _mod["ASSAYS_DIR"] = assays
            r = find_untested_modules()
        finally:
            _mod["EFFECTORS_DIR"] = orig_e
            _mod["ASSAYS_DIR"] = orig_a
        assert "foo-tool" not in r
        assert "bar.py" in r

    def test_no_dir(self, tmp_path):
        orig = _mod["EFFECTORS_DIR"]
        try:
            _mod["EFFECTORS_DIR"] = tmp_path / "nope"
            assert find_untested_modules() == []
        finally:
            _mod["EFFECTORS_DIR"] = orig


# ── generate_queue_tasks ───────────────────────────────────────────────


class TestGenerateQueueTasks:
    def test_count(self):
        tasks = generate_queue_tasks(["a", "b"], 2)
        assert len(tasks) == 2

    def test_truncates(self):
        tasks = generate_queue_tasks(["a", "b", "c"], 2)
        assert len(tasks) == 2

    def test_providers_rotate(self):
        tasks = generate_queue_tasks(["a", "b", "c"], 3)
        providers = []
        for t in tasks:
            m = __import__("re").search(r"--provider (\w+)", t)
            if m:
                providers.append(m.group(1))
        assert len(set(providers)) >= 2

    def test_empty(self):
        assert generate_queue_tasks([], 50) == []


# ── append_tasks_to_queue ──────────────────────────────────────────────


class TestAppendTasksToQueue:
    def test_appends(self, tmp_path):
        qf = tmp_path / "golem-queue.md"
        qf.write_text("## Pending\n")
        orig = _mod["QUEUE_FILE"]
        orig_c = _mod["COPIA_DIR"]
        try:
            _mod["QUEUE_FILE"] = qf
            _mod["COPIA_DIR"] = tmp_path / "copia"
            added = append_tasks_to_queue(["- [ ] `golem \"new\"`"])
        finally:
            _mod["QUEUE_FILE"] = orig
            _mod["COPIA_DIR"] = orig_c
        assert added == 1
        assert "new" in qf.read_text()

    def test_empty(self, tmp_path):
        qf = tmp_path / "golem-queue.md"
        qf.write_text("## Pending\n")
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            assert append_tasks_to_queue([]) == 0
        finally:
            _mod["QUEUE_FILE"] = orig


# ── write_fixed_tasks ──────────────────────────────────────────────────


class TestWriteFixedTasks:
    def test_writes(self, tmp_path):
        qf = tmp_path / "golem-queue.md"
        qf.write_text("## Pending\n")
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            c = write_fixed_tasks([{"cmd": "golem t", "diagnosis": "path_issue: x"}])
        finally:
            _mod["QUEUE_FILE"] = orig
        assert c == 1
        assert "path_issue" in qf.read_text()

    def test_empty(self, tmp_path):
        qf = tmp_path / "golem-queue.md"
        qf.write_text("## Pending\n")
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            assert write_fixed_tasks([]) == 0
        finally:
            _mod["QUEUE_FILE"] = orig


# ── generate_review ────────────────────────────────────────────────────


class TestGenerateReview:
    def test_basic(self):
        r = generate_review(
            activity={"completed": [(datetime(2026,3,31,14,0,0), "t1")], "failed": [], "timeouts": [], "start_time": None},
            recent_files=["assays/test_x.py"],
            test_results={"files": [("assays/test_x.py", 5, 0, 0)], "total_passed": 5, "total_failed": 0, "total_errors": 0},
            consulting_results=[], failed_diagnoses=[], pending_count=10,
            auto_requeue=False, queued_count=0, fixed_count=0,
        )
        assert "## Activity Summary" in r
        assert "5 passed" in r

    def test_with_failures(self):
        r = generate_review(
            activity={"completed": [], "failed": [(datetime.now(), "bad", "")], "timeouts": [(datetime.now(), "slow")], "start_time": None},
            recent_files=[], test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
            consulting_results=[], failed_diagnoses=[{"cmd": "bad", "diagnosis": "timeout"}],
            pending_count=5, auto_requeue=True, queued_count=0, fixed_count=1,
        )
        assert "Failed Tasks" in r
        assert "1 fixed" in r

    def test_empty(self):
        r = generate_review(
            {"completed": [], "failed": [], "timeouts": [], "start_time": None},
            [], {"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
            [], [], 0, False, 0, 0,
        )
        assert "Golem Review" in r


# ── run_review integration ─────────────────────────────────────────────


def _setup_env(tmp_path):
    germline = tmp_path / "germline"
    germline.mkdir(parents=True)
    lp = tmp_path / "golem-daemon.log"
    lp.write_text("")
    cd = germline / "loci" / "copia"
    cd.mkdir(parents=True)
    rp = cd / "golem-review-latest.md"
    qd = germline / "loci"
    qd.mkdir(parents=True)
    qp = qd / "golem-queue.md"
    qp.write_text("## Pending\n\n## Done\n")
    ed = germline / "effectors"
    ed.mkdir()
    ad = germline / "assays"
    ad.mkdir()
    return {"GERMLINE": germline, "LOGFILE": lp, "REVIEW_FILE": rp, "COPIA_DIR": cd,
            "QUEUE_FILE": qp, "EFFECTORS_DIR": ed, "ASSAYS_DIR": ad}


class TestRunReview:
    def test_basic(self, tmp_path, capsys):
        env = _setup_env(tmp_path)
        orig = {k: _mod[k] for k in env}
        try:
            for k, v in env.items():
                _mod[k] = v
            def mock_run(cmd, **kw):
                r = MagicMock(); r.returncode = 1; r.stdout = ""; r.stderr = ""
                return r
            with patch("subprocess.run", side_effect=mock_run):
                rc = run_review(auto_requeue=False, since=timedelta(minutes=30))
        finally:
            for k, v in orig.items():
                _mod[k] = v
        assert rc == 0
        assert env["REVIEW_FILE"].exists()

    def test_with_task(self, tmp_path, capsys):
        env = _setup_env(tmp_path)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        env["LOGFILE"].write_text(f"[{now}] Finished (100s, exit=0): golem task A\n")
        orig = {k: _mod[k] for k in env}
        try:
            for k, v in env.items():
                _mod[k] = v
            def mock_run(cmd, **kw):
                r = MagicMock(); r.returncode = 1; r.stdout = ""; r.stderr = ""
                return r
            with patch("subprocess.run", side_effect=mock_run):
                rc = run_review(auto_requeue=False, since=timedelta(minutes=30))
        finally:
            for k, v in orig.items():
                _mod[k] = v
        assert rc == 0
        assert "task A" in capsys.readouterr().out

    def test_auto_requeue(self, tmp_path, capsys):
        env = _setup_env(tmp_path)
        for i in range(5):
            (env["EFFECTORS_DIR"] / f"mod-{i}").write_text("#")
        orig = {k: _mod[k] for k in env}
        try:
            for k, v in env.items():
                _mod[k] = v
            def mock_run(cmd, **kw):
                r = MagicMock(); r.returncode = 1; r.stdout = ""; r.stderr = ""
                return r
            with patch("subprocess.run", side_effect=mock_run):
                rc = run_review(auto_requeue=True, since=timedelta(minutes=5))
        finally:
            for k, v in orig.items():
                _mod[k] = v
        assert rc == 0
        q = env["QUEUE_FILE"].read_text()
        assert any(f"mod-{i}" in q for i in range(5))


# ── Edge cases ─────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_scan_log_binary(self, tmp_path):
        lp = tmp_path / "golem-daemon.log"
        lp.write_bytes(b"\x00\x01\x02\xff")
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = lp
            r = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
        assert isinstance(r, dict)

    def test_count_pending_unreadable(self, tmp_path):
        q = tmp_path / "q.md"
        q.write_text("- [ ] `golem x`\n")
        q.chmod(0o000)
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = q
            assert count_pending_tasks() == 0
        finally:
            _mod["QUEUE_FILE"] = orig
            q.chmod(0o644)
