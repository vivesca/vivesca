"""Tests for golem-review — META-GOLEM review and requeue effector."""
from __future__ import annotations

import textwrap
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_golem_review():
    """Load golem-review module by exec-ing its source."""
    source = Path.home().joinpath("germline", "effectors", "golem-review").read_text()
    ns: dict = {"__name__": "golem_review"}
    exec(source, ns)
    return ns


_mod = _load_golem_review()

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

GERMLINE = _mod["GERMLINE"]
QUEUE_FILE = _mod["QUEUE_FILE"]
LOGFILE = _mod["LOGFILE"]
REVIEW_FILE = _mod["REVIEW_FILE"]
COPIA_DIR = _mod["COPIA_DIR"]
EFFECTORS_DIR = _mod["EFFECTORS_DIR"]
ASSAYS_DIR = _mod["ASSAYS_DIR"]


# ── parse_since tests ─────────────────────────────────────────────────


class TestParseSince:
    def test_minutes(self):
        assert parse_since("30m") == timedelta(minutes=30)

    def test_hours(self):
        assert parse_since("2h") == timedelta(hours=2)

    def test_seconds(self):
        assert parse_since("45s") == timedelta(seconds=45)

    def test_days(self):
        assert parse_since("1d") == timedelta(days=1)

    def test_no_suffix_defaults_minutes(self):
        assert parse_since("30") == timedelta(minutes=30)

    def test_invalid_returns_default(self):
        assert parse_since("abc") == timedelta(minutes=30)


# ── parse_log_timestamp tests ─────────────────────────────────────────


class TestParseLogTimestamp:
    def test_valid_timestamp(self):
        ts = parse_log_timestamp("2026-03-31 14:00:00")
        assert ts is not None
        assert ts.year == 2026
        assert ts.month == 3
        assert ts.day == 31

    def test_invalid_returns_none(self):
        assert parse_log_timestamp("not a timestamp") is None

    def test_none_returns_none(self):
        """parse_log_timestamp handles None input gracefully."""
        assert parse_log_timestamp(None) is None

    def test_empty_returns_none(self):
        assert parse_log_timestamp("") is None


# ── scan_log tests ────────────────────────────────────────────────────


class TestScanLog:
    def _make_log(self, tmp_path: Path, lines: list[str]) -> Path:
        log_path = tmp_path / "golem-daemon.log"
        log_path.write_text("\n".join(lines) + "\n")
        return log_path

    def _now_ts(self, minutes_ago: int = 0) -> str:
        """Return a timestamp string N minutes ago from now."""
        ts = datetime.now() - timedelta(minutes=minutes_ago)
        return ts.strftime("%Y-%m-%d %H:%M:%S")

    def test_completed_task_found(self, tmp_path):
        ts = self._now_ts(1)
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
        assert result["completed"][0][1] == "golem task1..."
        assert len(result["failed"]) == 0

    def test_failed_task_found(self, tmp_path):
        ts = self._now_ts(1)
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
        ts = self._now_ts(1)
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

    def test_mixed_completed_failed_timeout(self, tmp_path):
        log_path = self._make_log(tmp_path, [
            "[2026-03-31 14:00:00] Finished (10s, exit=0): task1",
            "[2026-03-31 14:01:00] FAILED (exit=1): task2",
            "[2026-03-31 14:02:00] Finished (5s, exit=0): task3",
            "[2026-03-31 14:03:00] TIMEOUT (1800s): task4",
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
        log_path = self._make_log(tmp_path, [
            "[2026-03-31 14:00:00] Finished (30s, exit=2): golem bad-cmd...",
        ])
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig

        assert len(result["failed"]) == 1
        assert len(result["completed"]) == 0


# ── get_recent_files tests ────────────────────────────────────────────


class TestGetRecentFiles:
    def test_returns_files_from_git(self):
        def mock_run(cmd, **kw):
            r = MagicMock()
            if "diff --name-only" in cmd:
                r.returncode = 0
                r.stdout = "assays/test_foo.py\neffectors/bar.py\n"
            else:
                r.returncode = 0
                r.stdout = ""
            r.stderr = ""
            return r

        with patch("subprocess.run", side_effect=mock_run):
            result = get_recent_files(5)

        assert "assays/test_foo.py" in result
        assert "effectors/bar.py" in result

    def test_git_failure_returns_empty(self):
        def mock_run(cmd, **kw):
            r = MagicMock()
            r.returncode = 128
            r.stdout = ""
            r.stderr = "fatal: bad revision"
            return r

        with patch("subprocess.run", side_effect=mock_run):
            result = get_recent_files()

        assert result == []


# ── run_pytest_on_files tests ─────────────────────────────────────────


class TestRunPytestOnFiles:
    def test_passing_tests(self):
        def mock_run(cmd, **kw):
            r = MagicMock()
            r.returncode = 0
            r.stdout = "5 passed in 1.2s"
            r.stderr = ""
            return r

        with patch("subprocess.run", side_effect=mock_run):
            result = run_pytest_on_files(["assays/test_example.py"])

        assert result["total_passed"] == 5
        assert result["total_failed"] == 0
        assert len(result["files"]) == 1
        assert result["files"][0][0] == "assays/test_example.py"

    def test_failing_tests(self):
        def mock_run(cmd, **kw):
            r = MagicMock()
            r.returncode = 1
            r.stdout = "3 passed, 2 failed"
            r.stderr = ""
            return r

        with patch("subprocess.run", side_effect=mock_run):
            result = run_pytest_on_files(["assays/test_broken.py"])

        assert result["total_passed"] == 3
        assert result["total_failed"] == 2

    def test_empty_file_list(self):
        result = run_pytest_on_files([])
        assert result["files"] == []
        assert result["total_passed"] == 0

    def test_timeout_handled(self):
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="x", timeout=1)):
            result = run_pytest_on_files(["assays/test_slow.py"])

        assert result["total_errors"] == 1


# ── check_consulting_content tests ────────────────────────────────────


class TestCheckConsultingContent:
    def test_file_with_enough_words(self, tmp_path):
        f = tmp_path / "deep-dive.md"
        f.write_text(" ".join(["word"] * 250))
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            results = check_consulting_content(["deep-dive.md"])
        finally:
            _mod["GERMLINE"] = orig

        assert len(results) == 1
        assert results[0]["adequate"] is True
        assert results[0]["word_count"] == 250

    def test_file_too_short(self, tmp_path):
        f = tmp_path / "thin.md"
        f.write_text("short content only ten words")
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            results = check_consulting_content(["thin.md"])
        finally:
            _mod["GERMLINE"] = orig

        assert results[0]["adequate"] is False

    def test_missing_file(self, tmp_path):
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            results = check_consulting_content(["nonexistent.md"])
        finally:
            _mod["GERMLINE"] = orig

        assert results[0]["exists"] is False
        assert results[0]["adequate"] is False

    def test_unreadable_file(self, tmp_path):
        f = tmp_path / "secret.md"
        f.write_text(" ".join(["x"] * 300))
        f.chmod(0o000)
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            results = check_consulting_content(["secret.md"])
        finally:
            _mod["GERMLINE"] = orig
            f.chmod(0o644)

        assert results[0]["exists"] is True
        assert results[0]["adequate"] is False


# ── diagnose_failure tests ────────────────────────────────────────────


class TestDiagnoseFailure:
    def test_import_error(self):
        result = diagnose_failure("golem task", "ModuleNotFoundError: foo")
        assert "import_error" in result

    def test_syntax_error(self):
        result = diagnose_failure("golem task", "SyntaxError: invalid")
        assert "syntax_error" in result

    def test_hardcoded_path(self):
        result = diagnose_failure("golem /Users/terry/ task", "")
        assert "path_issue" in result

    def test_timeout(self):
        result = diagnose_failure("golem task", "timeout after 1800s")
        assert "timeout" in result

    def test_permission_error(self):
        result = diagnose_failure("golem task", "PermissionError: denied")
        assert "permission_error" in result

    def test_exit_code_2(self):
        result = diagnose_failure("golem task exit=2", "")
        assert "command_error" in result

    def test_unknown_error(self):
        result = diagnose_failure("golem task", "something weird")
        assert "unknown" in result


# ── read_log_tail tests ───────────────────────────────────────────────


class TestReadLogTail:
    def test_returns_last_n_lines(self, tmp_path):
        log_path = tmp_path / "golem-daemon.log"
        log_path.write_text("\n".join([f"line {i}" for i in range(10)]))
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            tail = read_log_tail(3)
        finally:
            _mod["LOGFILE"] = orig

        assert "line 7" in tail
        assert "line 8" in tail
        assert "line 9" in tail
        assert "line 0" not in tail

    def test_missing_file(self, tmp_path):
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = tmp_path / "nope.log"
            tail = read_log_tail()
        finally:
            _mod["LOGFILE"] = orig

        assert tail == ""


# ── count_pending_tasks tests ─────────────────────────────────────────


class TestCountPendingTasks:
    def _make_queue(self, tmp_path: Path, content: str) -> Path:
        qd = tmp_path / "germline" / "loci"
        qd.mkdir(parents=True)
        qf = qd / "golem-queue.md"
        qf.write_text(content)
        return qf

    def test_counts_normal_and_high_priority(self, tmp_path):
        qf = self._make_queue(tmp_path, textwrap.dedent("""\
            - [ ] `golem "task1"`
            - [!!] `golem "urgent"`
            - [x] `golem "done"`
            - [!] `golem "fail"`
            - [ ] `golem "task2"`
        """))
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            count = count_pending_tasks()
        finally:
            _mod["QUEUE_FILE"] = orig

        assert count == 3  # 2 normal + 1 high priority

    def test_empty_queue(self, tmp_path):
        qf = self._make_queue(tmp_path, "")
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            count = count_pending_tasks()
        finally:
            _mod["QUEUE_FILE"] = orig

        assert count == 0

    def test_missing_file(self, tmp_path):
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = tmp_path / "nope.md"
            count = count_pending_tasks()
        finally:
            _mod["QUEUE_FILE"] = orig

        assert count == 0


# ── find_untested_modules tests ───────────────────────────────────────


class TestFindUntestedModules:
    def test_finds_untested(self, tmp_path):
        eff_dir = tmp_path / "effectors"
        eff_dir.mkdir()
        (eff_dir / "foo-tool").write_text("#!/usr/bin/env python3\n")
        (eff_dir / "bar-util.py").write_text("#!/usr/bin/env python3\n")

        assays_dir = tmp_path / "assays"
        assays_dir.mkdir()
        (assays_dir / "test_foo_tool.py").write_text("def test_x(): pass\n")

        orig_eff = _mod["EFFECTORS_DIR"]
        orig_ass = _mod["ASSAYS_DIR"]
        try:
            _mod["EFFECTORS_DIR"] = eff_dir
            _mod["ASSAYS_DIR"] = assays_dir
            untested = find_untested_modules()
        finally:
            _mod["EFFECTORS_DIR"] = orig_eff
            _mod["ASSAYS_DIR"] = orig_ass

        assert "foo-tool" not in untested
        assert "bar-util.py" in untested

    def test_no_effectors_dir(self, tmp_path):
        orig_eff = _mod["EFFECTORS_DIR"]
        try:
            _mod["EFFECTORS_DIR"] = tmp_path / "no_effectors"
            untested = find_untested_modules()
        finally:
            _mod["EFFECTORS_DIR"] = orig_eff

        assert untested == []


# ── generate_queue_tasks tests ────────────────────────────────────────


class TestGenerateQueueTasks:
    def test_generates_correct_count(self):
        tasks = generate_queue_tasks(["foo-tool", "bar.py"], 2)
        assert len(tasks) == 2
        assert all(t.startswith("- [ ] `golem") for t in tasks)

    def test_truncates_to_count(self):
        tasks = generate_queue_tasks(["a", "b", "c"], 2)
        assert len(tasks) == 2

    def test_rotates_providers(self):
        tasks = generate_queue_tasks(["a", "b", "c", "d"], 4)
        providers = []
        for t in tasks:
            import re
            m = re.search(r"--provider (\w+)", t)
            if m:
                providers.append(m.group(1))
        assert len(set(providers)) >= 2

    def test_empty_list(self):
        tasks = generate_queue_tasks([], 50)
        assert tasks == []


# ── append_tasks_to_queue tests ───────────────────────────────────────


class TestAppendTasksToQueue:
    def _make_queue(self, tmp_path: Path, content: str) -> Path:
        qd = tmp_path / "germline" / "loci"
        qd.mkdir(parents=True)
        qf = qd / "golem-queue.md"
        qf.write_text(content)
        return qf

    def test_appends_to_file(self, tmp_path):
        qf = self._make_queue(tmp_path, "## Pending\n")
        orig = _mod["QUEUE_FILE"]
        orig_copia = _mod["COPIA_DIR"]
        try:
            _mod["QUEUE_FILE"] = qf
            _mod["COPIA_DIR"] = tmp_path / "copia"
            added = append_tasks_to_queue(['- [ ] `golem "new task"`'])
        finally:
            _mod["QUEUE_FILE"] = orig
            _mod["COPIA_DIR"] = orig_copia

        assert added == 1
        content = qf.read_text()
        assert 'golem "new task"' in content

    def test_empty_task_list(self, tmp_path):
        qf = self._make_queue(tmp_path, "## Pending\n")
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            added = append_tasks_to_queue([])
        finally:
            _mod["QUEUE_FILE"] = orig

        assert added == 0


# ── write_fixed_tasks tests ───────────────────────────────────────────


class TestWriteFixedTasks:
    def _make_queue(self, tmp_path: Path, content: str) -> Path:
        qd = tmp_path / "germline" / "loci"
        qd.mkdir(parents=True)
        qf = qd / "golem-queue.md"
        qf.write_text(content)
        return qf

    def test_writes_fixed_tasks(self, tmp_path):
        qf = self._make_queue(tmp_path, "## Pending\n")
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            count = write_fixed_tasks([{
                "cmd": 'golem --provider zhipu "do task"',
                "diagnosis": "path_issue: hardcoded /Users/terry/ detected",
            }])
        finally:
            _mod["QUEUE_FILE"] = orig

        assert count == 1
        content = qf.read_text()
        assert "path_issue" in content
        assert "Path.home()" in content

    def test_no_tasks_no_writes(self, tmp_path):
        qf = self._make_queue(tmp_path, "## Pending\n")
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            count = write_fixed_tasks([])
        finally:
            _mod["QUEUE_FILE"] = orig

        assert count == 0

    def test_import_error_fix_hint(self, tmp_path):
        qf = self._make_queue(tmp_path, "## Pending\n")
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            write_fixed_tasks([{
                "cmd": 'golem "write tests"',
                "diagnosis": "import_error: missing module",
            }])
        finally:
            _mod["QUEUE_FILE"] = orig

        content = qf.read_text()
        assert "exec(open" in content


# ── generate_review tests ─────────────────────────────────────────────


class TestGenerateReview:
    def _make_activity(self):
        return {
            "completed": [(datetime(2026, 3, 31, 14, 0, 0), "golem task1")],
            "failed": [],
            "timeouts": [],
            "start_time": datetime(2026, 3, 31, 13, 30, 0),
        }

    def test_summary_contains_sections(self):
        review = generate_review(
            activity=self._make_activity(),
            recent_files=["assays/test_x.py"],
            test_results={
                "files": [("assays/test_x.py", 5, 0, 0)],
                "total_passed": 5,
                "total_failed": 0,
                "total_errors": 0,
            },
            consulting_results=[],
            failed_diagnoses=[],
            pending_count=10,
            auto_requeue=False,
            queued_count=0,
            fixed_count=0,
        )
        assert "## Activity Summary" in review
        assert "Completed tasks" in review
        assert "5 passed" in review

    def test_review_with_failures(self):
        review = generate_review(
            activity={
                "completed": [],
                "failed": [(datetime(2026, 3, 31, 14, 0, 0), "golem bad", "tail")],
                "timeouts": [(datetime(2026, 3, 31, 14, 1, 0), "golem slow")],
                "start_time": datetime(2026, 3, 31, 13, 30, 0),
            },
            recent_files=[],
            test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
            consulting_results=[],
            failed_diagnoses=[{"cmd": "golem bad", "diagnosis": "timeout: exceeded limit"}],
            pending_count=5,
            auto_requeue=True,
            queued_count=0,
            fixed_count=1,
        )
        assert "Failed Tasks" in review
        assert "Timeouts" in review
        assert "Auto-Requeue Actions" in review
        assert "1 fixed" in review

    def test_consulting_section(self):
        review = generate_review(
            activity={"completed": [], "failed": [], "timeouts": [], "start_time": None},
            recent_files=[],
            test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
            consulting_results=[
                {"file": "deep-dive.md", "exists": True, "word_count": 500, "adequate": True},
                {"file": "thin.md", "exists": True, "word_count": 50, "adequate": False},
            ],
            failed_diagnoses=[],
            pending_count=0,
            auto_requeue=False,
            queued_count=0,
            fixed_count=0,
        )
        assert "Consulting Content" in review
        assert "500 words" in review
        assert "TOO SHORT" in review

    def test_empty_review(self):
        review = generate_review(
            activity={"completed": [], "failed": [], "timeouts": [], "start_time": None},
            recent_files=[],
            test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
            consulting_results=[],
            failed_diagnoses=[],
            pending_count=0,
            auto_requeue=False,
            queued_count=0,
            fixed_count=0,
        )
        assert "Golem Review" in review
        assert "Completed tasks" in review


# ── run_review integration tests ──────────────────────────────────────


class TestRunReview:
    def _setup_env(self, tmp_path):
        """Set up temp environment for run_review."""
        log_path = tmp_path / "golem-daemon.log"
        log_path.write_text("")
        queue_dir = tmp_path / "germline" / "loci"
        queue_dir.mkdir(parents=True)
        queue_path = queue_dir / "golem-queue.md"
        queue_path.write_text("## Pending\n")
        copia_dir = tmp_path / "copia"
        copia_dir.mkdir(parents=True)
        review_path = copia_dir / "golem-review-latest.md"

        return {
            "LOGFILE": log_path,
            "QUEUE_FILE": queue_path,
            "REVIEW_FILE": review_path,
            "COPIA_DIR": copia_dir,
            "GERMLINE": tmp_path,
            "EFFECTORS_DIR": tmp_path / "effectors",
            "ASSAYS_DIR": tmp_path / "assays",
        }

    def test_basic_run(self, tmp_path):
        env = self._setup_env(tmp_path)
        originals = {k: _mod[k] for k in env}
        try:
            for k, v in env.items():
                _mod[k] = v

            def mock_run(cmd, **kw):
                r = MagicMock()
                r.returncode = 1
                r.stdout = ""
                r.stderr = ""
                return r

            with patch("subprocess.run", side_effect=mock_run):
                rc = run_review(auto_requeue=False, since=timedelta(minutes=30))
        finally:
            for k, v in originals.items():
                _mod[k] = v

        assert rc == 0
        assert env["REVIEW_FILE"].exists()

    def test_auto_requeue_generates_tasks(self, tmp_path):
        env = self._setup_env(tmp_path)
        # Add an untested effector
        eff_dir = tmp_path / "effectors"
        eff_dir.mkdir()
        (eff_dir / "my-tool").write_text("#!/usr/bin/env python3\n")

        originals = {k: _mod[k] for k in env}
        try:
            for k, v in env.items():
                _mod[k] = v

            def mock_run(cmd, **kw):
                r = MagicMock()
                r.returncode = 1
                r.stdout = ""
                r.stderr = ""
                return r

            with patch("subprocess.run", side_effect=mock_run):
                rc = run_review(auto_requeue=True, since=timedelta(minutes=5))
        finally:
            for k, v in originals.items():
                _mod[k] = v

        assert rc == 0
        queue_content = env["QUEUE_FILE"].read_text()
        assert "my-tool" in queue_content

    def test_review_with_completed_tasks(self, tmp_path):
        env = self._setup_env(tmp_path)
        # Write some log entries
        env["LOGFILE"].write_text(
            "[2026-03-31 14:00:00] Finished (60s, exit=0): golem task completed...\n"
        )

        originals = {k: _mod[k] for k in env}
        try:
            for k, v in env.items():
                _mod[k] = v

            def mock_run(cmd, **kw):
                r = MagicMock()
                r.returncode = 1
                r.stdout = ""
                r.stderr = ""
                return r

            with patch("subprocess.run", side_effect=mock_run):
                rc = run_review(auto_requeue=False, since=timedelta(minutes=30))
        finally:
            for k, v in originals.items():
                _mod[k] = v

        assert rc == 0
        review = env["REVIEW_FILE"].read_text()
        assert "Completed tasks" in review


# ── Edge case tests ───────────────────────────────────────────────────


class TestEdgeCases:
    def test_scan_log_binary_content(self, tmp_path):
        """scan_log handles binary content in log file."""
        log_path = tmp_path / "golem-daemon.log"
        log_path.write_bytes(b"\x00\x01\x02\xff\xfe\xfd")
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig

        # Should not crash
        assert isinstance(result, dict)

    def test_scan_log_unreadable(self, tmp_path):
        """scan_log handles unreadable log file."""
        log_path = tmp_path / "golem-daemon.log"
        log_path.write_text("[2026-03-31 14:00:00] Finished (60s, exit=0): test\n")
        log_path.chmod(0o000)
        orig = _mod["LOGFILE"]
        try:
            _mod["LOGFILE"] = log_path
            result = scan_log(timedelta(minutes=30))
        finally:
            _mod["LOGFILE"] = orig
            log_path.chmod(0o644)

        assert result["completed"] == []

    def test_count_pending_unreadable_queue(self, tmp_path):
        """count_pending_tasks handles unreadable queue file."""
        qd = tmp_path / "germline" / "loci"
        qd.mkdir(parents=True)
        qf = qd / "golem-queue.md"
        qf.write_text("- [ ] `golem \"task\"`\n")
        qf.chmod(0o000)
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            count = count_pending_tasks()
        finally:
            _mod["QUEUE_FILE"] = orig
            qf.chmod(0o644)

        assert count == 0

    def test_write_fixed_tasks_missing_queue(self, tmp_path):
        """write_fixed_tasks handles missing queue file."""
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = tmp_path / "nonexistent" / "queue.md"
            count = write_fixed_tasks([{"cmd": "test", "diagnosis": "unknown"}])
        finally:
            _mod["QUEUE_FILE"] = orig

        # Creates the file
        assert count == 1

    def test_generate_queue_tasks_with_special_chars(self):
        """generate_queue_tasks handles module names with special chars."""
        tasks = generate_queue_tasks(["my-tool", "other.util"], 2)
        assert len(tasks) == 2
        assert "my-tool" in tasks[0] or "my_tool" in tasks[0]

    def test_diagnose_failure_assertion_error(self):
        """diagnose_failure detects assertion errors."""
        result = diagnose_failure("golem task", "assert False")
        assert "assertion_error" in result
