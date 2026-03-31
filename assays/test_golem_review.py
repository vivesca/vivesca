"""Tests for golem-review — META-GOLEM that reviews other golem output and queues work."""
from __future__ import annotations

import subprocess
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
    k: _mod[k] for k in [
        "QUEUE_FILE", "LOGFILE", "REVIEW_FILE", "COPIA_DIR",
        "GERMLINE", "EFFECTORS_DIR", "ASSAYS_DIR",
    ]
}


def _restore():
    for k, v in _ORIG.items():
        _mod[k] = v


def _now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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

    def test_empty_string(self):
        assert parse_since("") == timedelta(minutes=30)


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


# ── scan_log ───────────────────────────────────────────────────────────


class TestScanLog:
    def _with_log(self, tmp_path, content):
        """Set up a temp log file and scan it."""
        log = tmp_path / "golem-daemon.log"
        log.write_text(content)
        _mod["LOGFILE"] = log
        try:
            return scan_log(timedelta(minutes=30))
        finally:
            _restore()

    def test_missing_file(self, tmp_path):
        _mod["LOGFILE"] = tmp_path / "nonexistent.log"
        try:
            r = scan_log(timedelta(minutes=30))
        finally:
            _restore()
        assert r["completed"] == []
        assert r["failed"] == []
        assert r["timeouts"] == []

    def test_completed_exit0(self, tmp_path):
        now = _now_str()
        r = self._with_log(tmp_path, f"[{now}] Finished (120s, exit=0): golem --provider infini \"write tests\"\n")
        assert len(r["completed"]) == 1
        assert "write tests" in r["completed"][0][1]

    def test_failed_nonzero_exit(self, tmp_path):
        now = _now_str()
        r = self._with_log(tmp_path, f"[{now}] Finished (5s, exit=1): golem \"broken task\"\n")
        assert len(r["failed"]) == 1
        assert "broken task" in r["failed"][0][1]

    def test_failed_marker(self, tmp_path):
        now = _now_str()
        r = self._with_log(tmp_path, f"[{now}] FAILED (exit=1): golem \"task X\"\n")
        assert len(r["failed"]) == 1
        assert "task X" in r["failed"][0][1]

    def test_timeout(self, tmp_path):
        now = _now_str()
        r = self._with_log(tmp_path, f"[{now}] TIMEOUT (1800s): golem \"slow task\"\n")
        assert len(r["timeouts"]) == 1
        assert "slow task" in r["timeouts"][0][1]

    def test_ignores_old_entries(self, tmp_path):
        old = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        r = self._with_log(tmp_path, f"[{old}] Finished (10s, exit=0): golem \"old\"\n")
        assert r["completed"] == []

    def test_mixed(self, tmp_path):
        now = _now_str()
        r = self._with_log(tmp_path, (
            f"[{now}] Finished (60s, exit=0): golem \"A\"\n"
            f"[{now}] Finished (30s, exit=1): golem \"B\"\n"
            f"[{now}] TIMEOUT (1800s): golem \"C\"\n"
            f"[{now}] Starting: golem \"D\"\n"
        ))
        assert len(r["completed"]) == 1
        assert len(r["failed"]) == 1
        assert len(r["timeouts"]) == 1

    def test_unreadable(self, tmp_path):
        log = tmp_path / "golem-daemon.log"
        log.write_text("[2026-03-31 10:00:00] Finished (1s, exit=0): golem\n")
        log.chmod(0o000)
        _mod["LOGFILE"] = log
        try:
            r = scan_log(timedelta(minutes=30))
        finally:
            _restore()
            log.chmod(0o644)
        assert r["completed"] == []

    def test_binary_content(self, tmp_path):
        log = tmp_path / "golem-daemon.log"
        log.write_bytes(b"\x00\x01\x02\xff\xfe\xfd")
        _mod["LOGFILE"] = log
        try:
            r = scan_log(timedelta(minutes=30))
        finally:
            _restore()
        assert r["completed"] == []
        assert r["failed"] == []


# ── diagnose_failure ───────────────────────────────────────────────────


class TestDiagnoseFailure:
    def test_import_error(self):
        assert diagnose_failure("golem task", "ImportError: no module") == "import_error"

    def test_module_not_found(self):
        assert diagnose_failure("golem task", "ModuleNotFoundError: lacuna") == "import_error"

    def test_syntax_error(self):
        assert diagnose_failure("golem task", "SyntaxError: invalid") == "syntax_error"

    def test_path_issue(self):
        assert diagnose_failure("golem task", "/Users/terry/germline") == "path_issue"

    def test_timeout(self):
        assert diagnose_failure("golem timeout task", "") == "timeout"

    def test_permission_error(self):
        assert diagnose_failure("golem task", "PermissionError: denied") == "permission_error"

    def test_command_error_exit2(self):
        assert diagnose_failure("exit=2 golem task", "") == "command_error"

    def test_assertion_error(self):
        assert diagnose_failure("golem task", "assert False") == "assertion_error"

    def test_unknown(self):
        assert diagnose_failure("golem task", "some random output") == "unknown"

    def test_returns_string(self):
        result = diagnose_failure("golem task", "")
        assert isinstance(result, str)


# ── check_consulting_content ───────────────────────────────────────────


class TestCheckConsultingContent:
    def test_adequate(self, tmp_path):
        _mod["GERMLINE"] = tmp_path
        copia = tmp_path / "loci" / "copia"
        copia.mkdir(parents=True)
        (copia / "brief.md").write_text("word " * 250)
        try:
            result = check_consulting_content(["loci/copia/brief.md"])
        finally:
            _restore()
        assert len(result) == 1
        assert result[0]["exists"] is True
        assert result[0]["adequate"] is True
        assert result[0]["word_count"] >= 200

    def test_too_short(self, tmp_path):
        _mod["GERMLINE"] = tmp_path
        copia = tmp_path / "loci" / "copia"
        copia.mkdir(parents=True)
        (copia / "short.md").write_text("only a few words")
        try:
            result = check_consulting_content(["loci/copia/short.md"])
        finally:
            _restore()
        assert result[0]["adequate"] is False

    def test_missing(self, tmp_path):
        _mod["GERMLINE"] = tmp_path
        try:
            result = check_consulting_content(["loci/copia/nonexistent.md"])
        finally:
            _restore()
        assert result[0]["exists"] is False
        assert result[0]["adequate"] is False

    def test_empty_list(self):
        assert check_consulting_content([]) == []


# ── run_pytest_on_files ────────────────────────────────────────────────


class TestRunPytestOnFiles:
    def test_empty(self):
        r = run_pytest_on_files([])
        assert r["total_passed"] == 0
        assert r["total_failed"] == 0
        assert r["total_errors"] == 0

    def test_parses_output(self):
        def mock_run(*a, **kw):
            r = MagicMock()
            r.stdout = "3 passed, 1 failed\n"
            r.stderr = ""
            return r
        with patch("subprocess.run", side_effect=mock_run):
            r = run_pytest_on_files(["assays/test_ex.py"])
        assert r["total_passed"] == 3
        assert r["total_failed"] == 1

    def test_timeout(self):
        def mock_timeout(*a, **kw):
            raise subprocess.TimeoutExpired("cmd", 120)
        with patch("subprocess.run", side_effect=mock_timeout):
            r = run_pytest_on_files(["assays/test_slow.py"])
        assert r["total_errors"] == 1

    def test_exception(self):
        def mock_err(*a, **kw):
            raise RuntimeError("broken")
        with patch("subprocess.run", side_effect=mock_err):
            r = run_pytest_on_files(["assays/test_bad.py"])
        assert r["total_errors"] == 1


# ── count_pending_tasks ────────────────────────────────────────────────


class TestCountPendingTasks:
    def test_counts_correctly(self, tmp_path):
        q = tmp_path / "q.md"
        q.write_text(
            "- [ ] `golem \"task1\"`\n"
            "- [!!] `golem \"urgent\"`\n"
            "- [x] `golem \"done\"`\n"
            "- [!] `golem \"failed\"`\n"
            "- [ ] `golem \"task2\"`\n"
        )
        _mod["QUEUE_FILE"] = q
        try:
            assert count_pending_tasks() == 3
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


# ── find_untested_modules ──────────────────────────────────────────────


class TestFindUntestedModules:
    def test_basic(self, tmp_path):
        _mod["EFFECTORS_DIR"] = tmp_path / "eff"
        _mod["ASSAYS_DIR"] = tmp_path / "assays"
        _mod["EFFECTORS_DIR"].mkdir()
        _mod["ASSAYS_DIR"].mkdir()
        (_mod["EFFECTORS_DIR"] / "alpha").write_text("#")
        (_mod["EFFECTORS_DIR"] / "beta").write_text("#")
        (_mod["ASSAYS_DIR"] / "test_alpha.py").write_text("#")
        try:
            untested = find_untested_modules()
        finally:
            _restore()
        assert "beta" in untested
        assert "alpha" not in untested

    def test_empty_dirs(self, tmp_path):
        _mod["EFFECTORS_DIR"] = tmp_path / "eff"
        _mod["ASSAYS_DIR"] = tmp_path / "assays"
        _mod["EFFECTORS_DIR"].mkdir()
        _mod["ASSAYS_DIR"].mkdir()
        try:
            assert find_untested_modules() == []
        finally:
            _restore()


# ── generate_queue_tasks ───────────────────────────────────────────────


class TestGenerateQueueTasks:
    def test_basic(self):
        tasks = generate_queue_tasks(["my-module", "other"], 2)
        assert len(tasks) == 2
        assert all(t.startswith("- [ ]") for t in tasks)
        assert any("my-module" in t for t in tasks)

    def test_limits_count(self):
        assert len(generate_queue_tasks(["a", "b", "c", "d", "e"], 3)) == 3

    def test_empty(self):
        assert generate_queue_tasks([], 10) == []

    def test_provider_rotation(self):
        tasks = generate_queue_tasks(["a", "b", "c", "d"], 4)
        import re
        providers = []
        for t in tasks:
            m = re.search(r'--provider (\w+)', t)
            if m:
                providers.append(m.group(1))
        assert len(set(providers)) > 1


# ── append_tasks_to_queue ──────────────────────────────────────────────


class TestAppendTasksToQueue:
    def test_appends(self, tmp_path):
        q = tmp_path / "q.md"
        q.write_text("# Queue\n\n## Pending\n\n## Done\n")
        _mod["QUEUE_FILE"] = q
        try:
            count = append_tasks_to_queue(['- [ ] `golem "new task"`'])
        finally:
            _restore()
        assert count == 1
        content = q.read_text()
        assert "new task" in content

    def test_empty(self):
        assert append_tasks_to_queue([]) == 0

    def test_creates_file(self, tmp_path):
        q = tmp_path / "new-q.md"
        _mod["QUEUE_FILE"] = q
        try:
            count = append_tasks_to_queue(['- [ ] `golem "task"`'])
        finally:
            _restore()
        assert count == 1
        assert q.exists()


# ── write_fixed_tasks ──────────────────────────────────────────────────


class TestWriteFixedTasks:
    def test_path_issue(self, tmp_path):
        q = tmp_path / "q.md"
        q.write_text("# Queue\n\n## Pending\n\n## Done\n")
        _mod["QUEUE_FILE"] = q
        try:
            count = write_fixed_tasks([
                {"cmd": "golem task", "diagnosis": "path_issue"},
            ])
        finally:
            _restore()
        assert count == 1
        assert "Path.home()" in q.read_text()

    def test_import_error(self, tmp_path):
        q = tmp_path / "q.md"
        q.write_text("# Queue\n\n## Pending\n\n## Done\n")
        _mod["QUEUE_FILE"] = q
        try:
            count = write_fixed_tasks([
                {"cmd": "golem task", "diagnosis": "import_error"},
            ])
        finally:
            _restore()
        assert count == 1
        assert "exec(" in q.read_text()

    def test_timeout_reduces_turns(self, tmp_path):
        q = tmp_path / "q.md"
        q.write_text("# Queue\n\n## Pending\n\n## Done\n")
        _mod["QUEUE_FILE"] = q
        try:
            count = write_fixed_tasks([
                {"cmd": 'golem --max-turns 50 "slow task"', "diagnosis": "timeout"},
            ])
        finally:
            _restore()
        assert count == 1
        content = q.read_text()
        assert "--max-turns 30" in content

    def test_empty(self):
        assert write_fixed_tasks([]) == 0

    def test_unknown_uses_original_cmd(self, tmp_path):
        q = tmp_path / "q.md"
        q.write_text("# Queue\n\n## Pending\n\n## Done\n")
        _mod["QUEUE_FILE"] = q
        try:
            count = write_fixed_tasks([
                {"cmd": 'golem --provider volcano "my special task"', "diagnosis": "unknown"},
            ])
        finally:
            _restore()
        assert count == 1
        assert "my special task" in q.read_text()


# ── read_log_tail ──────────────────────────────────────────────────────


class TestReadLogTail:
    def test_returns_tail(self, tmp_path):
        log = tmp_path / "golem-daemon.log"
        lines = [f"[2026-03-31 10:00:{i:02d}] line {i}" for i in range(10)]
        log.write_text("\n".join(lines))
        _mod["LOGFILE"] = log
        try:
            tail = read_log_tail(3)
        finally:
            _restore()
        assert "line 7" in tail
        assert "line 9" in tail
        assert "line 0" not in tail

    def test_missing_file(self, tmp_path):
        _mod["LOGFILE"] = tmp_path / "nope.log"
        try:
            assert read_log_tail() == ""
        finally:
            _restore()


# ── get_recent_files ───────────────────────────────────────────────────


class TestGetRecentFiles:
    def test_mocked(self):
        def mock_run(*a, **kw):
            r = MagicMock()
            r.returncode = 0
            r.stdout = "assays/test_new.py\neffectors/new_eff\n"
            return r
        with patch("subprocess.run", side_effect=mock_run):
            files = get_recent_files()
        assert "assays/test_new.py" in files

    def test_git_fails(self):
        def mock_fail(*a, **kw):
            r = MagicMock()
            r.returncode = 1
            r.stdout = ""
            return r
        with patch("subprocess.run", side_effect=mock_fail):
            assert get_recent_files() == []

    def test_exception(self):
        with patch("subprocess.run", side_effect=RuntimeError("x")):
            assert get_recent_files() == []


# ── generate_review ────────────────────────────────────────────────────


class TestGenerateReview:
    def _make_activity(self, completed=None, failed=None, timeouts=None):
        return {
            "completed": completed or [],
            "failed": failed or [],
            "timeouts": timeouts or [],
            "start_time": None,
        }

    def test_basic(self):
        review = generate_review(
            activity=self._make_activity(),
            recent_files=[],
            test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
            consulting_results=[],
            failed_diagnoses=[],
            pending_count=5,
            auto_requeue=False,
            queued_count=0,
            fixed_count=0,
        )
        assert "Golem Review" in review
        assert "Activity Summary" in review
        assert "Completed tasks: 0" in review

    def test_with_completed(self):
        activity = self._make_activity(
            completed=[(datetime.now(), "golem task A")],
        )
        review = generate_review(
            activity=activity, recent_files=[],
            test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
            consulting_results=[], failed_diagnoses=[], pending_count=0,
            auto_requeue=False, queued_count=0, fixed_count=0,
        )
        assert "task A" in review

    def test_with_test_results(self):
        test_results = {
            "files": [("assays/test_foo.py", 5, 1, 0)],
            "total_passed": 5, "total_failed": 1, "total_errors": 0,
        }
        review = generate_review(
            activity=self._make_activity(), recent_files=[], test_results=test_results,
            consulting_results=[], failed_diagnoses=[], pending_count=0,
            auto_requeue=False, queued_count=0, fixed_count=0,
        )
        assert "test_foo.py" in review
        assert "5 passed" in review

    def test_with_consulting(self):
        consulting = [{"file": "brief.md", "exists": True, "word_count": 350, "adequate": True}]
        review = generate_review(
            activity=self._make_activity(), recent_files=[], 
            test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
            consulting_results=consulting, failed_diagnoses=[], pending_count=0,
            auto_requeue=False, queued_count=0, fixed_count=0,
        )
        assert "brief.md" in review
        assert "350" in review

    def test_auto_requeue_section(self):
        review = generate_review(
            activity=self._make_activity(), recent_files=[],
            test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
            consulting_results=[], failed_diagnoses=[], pending_count=10,
            auto_requeue=True, queued_count=40, fixed_count=2,
        )
        assert "Auto-Requeue" in review
        assert "40" in review

    def test_timeouts(self):
        activity = self._make_activity(timeouts=[(datetime.now(), "slow task")])
        review = generate_review(
            activity=activity, recent_files=[],
            test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
            consulting_results=[], failed_diagnoses=[], pending_count=0,
            auto_requeue=False, queued_count=0, fixed_count=0,
        )
        assert "slow task" in review


# ── run_review integration ─────────────────────────────────────────────


def _setup(tmp_path):
    """Set up temp environment for integration tests."""
    _mod["GERMLINE"] = tmp_path
    _mod["LOGFILE"] = tmp_path / "golem-daemon.log"
    _mod["REVIEW_FILE"] = tmp_path / "golem-review-latest.md"
    _mod["COPIA_DIR"] = tmp_path
    _mod["QUEUE_FILE"] = tmp_path / "golem-queue.md"
    _mod["EFFECTORS_DIR"] = tmp_path / "effectors"
    _mod["ASSAYS_DIR"] = tmp_path / "assays"

    for d in [_mod["EFFECTORS_DIR"], _mod["ASSAYS_DIR"]]:
        d.mkdir(parents=True, exist_ok=True)

    _mod["LOGFILE"].write_text("")
    _mod["QUEUE_FILE"].write_text("# Queue\n\n## Pending\n\n## Done\n")


class TestRunReview:
    def test_basic(self, tmp_path, capsys):
        _setup(tmp_path)
        try:
            rc = run_review(auto_requeue=False, since=timedelta(minutes=30))
        finally:
            _restore()
        assert rc == 0
        assert _mod["REVIEW_FILE"].exists()
        assert "Golem Review" in capsys.readouterr().out

    def test_with_completed_task(self, tmp_path, capsys):
        _setup(tmp_path)
        now = _now_str()
        _mod["LOGFILE"].write_text(
            f"[{now}] Finished (100s, exit=0): golem --provider infini \"task A\"\n"
        )
        try:
            rc = run_review(auto_requeue=False, since=timedelta(minutes=30))
        finally:
            _restore()
        assert rc == 0
        assert "task A" in capsys.readouterr().out

    def test_auto_requeue_generates_tasks(self, tmp_path, capsys):
        _setup(tmp_path)
        for i in range(5):
            (_mod["EFFECTORS_DIR"] / f"module-{i}").write_text(f"# {i}")
        try:
            rc = run_review(auto_requeue=True, since=timedelta(minutes=30))
        finally:
            _restore()
        assert rc == 0
        q = _mod["QUEUE_FILE"].read_text()
        assert any(f"module-{i}" in q for i in range(5))

    def test_auto_requeue_with_failure(self, tmp_path, capsys):
        _setup(tmp_path)
        now = _now_str()
        _mod["LOGFILE"].write_text(
            f"[{now}] Finished (5s, exit=1): golem --provider infini \"broken task\"\n"
        )
        try:
            rc = run_review(auto_requeue=True, since=timedelta(minutes=30))
        finally:
            _restore()
        assert rc == 0
        out = capsys.readouterr().out
        assert "broken task" in out

    def test_no_log_file(self, tmp_path, capsys):
        _setup(tmp_path)
        _mod["LOGFILE"] = tmp_path / "nonexistent.log"
        try:
            rc = run_review(auto_requeue=False, since=timedelta(minutes=30))
        finally:
            _restore()
        assert rc == 0


# ── Edge cases ─────────────────────────────────────────────────────────


class TestEdgeCases:
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

    def test_write_fixed_tasks_empty_tasks(self):
        assert write_fixed_tasks([]) == 0

    def test_diagnose_combined_cmd_and_output(self):
        # Ensure both cmd and output are checked
        assert diagnose_failure("import_module task", "ImportError: foo") == "import_error"
        assert diagnose_failure("timeout task", "") == "timeout"
