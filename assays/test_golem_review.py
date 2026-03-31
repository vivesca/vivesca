"""Tests for golem-review — META-GOLEM review and requeue effector."""
from __future__ import annotations

import textwrap
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

parse_log_since = _mod["parse_log_since"]
get_changed_files = _mod["get_changed_files"]
run_tests_on_files = _mod["run_tests_on_files"]
check_consulting_content = _mod["check_consulting_content"]
diagnose_failure = _mod["diagnose_failure"]
get_failed_tasks_from_queue = _mod["get_failed_tasks_from_queue"]
write_fixed_tasks = _mod["write_fixed_tasks"]
generate_summary = _mod["generate_summary"]
count_pending_tasks = _mod["count_pending_tasks"]
find_untested_effectors = _mod["find_untested_effectors"]
generate_queue_tasks = _mod["generate_queue_tasks"]
append_tasks_to_queue = _mod["append_tasks_to_queue"]
write_summary = _mod["write_summary"]
main = _mod["main"]

GERMLINE = _mod["GERMLINE"]
QUEUE_FILE = _mod["QUEUE_FILE"]
DAEMON_LOG = _mod["DAEMON_LOG"]
REVIEW_SUMMARY = _mod["REVIEW_SUMMARY"]


# ── parse_log_since tests ─────────────────────────────────────────────


class TestParseLogSince:
    def _make_log(self, tmp_path: Path, lines: list[str]) -> Path:
        log_path = tmp_path / "golem-daemon.log"
        log_path.write_text("\n".join(lines) + "\n")
        return log_path

    def test_completed_task_found(self, tmp_path):
        """parse_log_since finds completed tasks in the time window."""
        log_path = self._make_log(tmp_path, [
            "[2026-03-31 14:00:00] Starting: golem --provider zhipu task1",
            "[2026-03-31 14:01:00] Finished (60s, exit=0): golem --provider zhipu task1...",
        ])
        orig = _mod["DAEMON_LOG"]
        try:
            _mod["DAEMON_LOG"] = log_path
            result = parse_log_since(60)
        finally:
            _mod["DAEMON_LOG"] = orig

        assert result["total_completed"] == 1
        assert result["total_failed"] == 0

    def test_failed_task_found(self, tmp_path):
        """parse_log_since finds failed tasks."""
        log_path = self._make_log(tmp_path, [
            "[2026-03-31 14:00:00] FAILED (exit=1): golem task...",
        ])
        orig = _mod["DAEMON_LOG"]
        try:
            _mod["DAEMON_LOG"] = log_path
            result = parse_log_since(60)
        finally:
            _mod["DAEMON_LOG"] = orig

        assert result["total_failed"] == 1
        assert result["total_completed"] == 0

    def test_old_entries_excluded(self, tmp_path):
        """parse_log_since excludes entries outside the time window."""
        log_path = self._make_log(tmp_path, [
            "[2020-01-01 00:00:00] Finished (60s, exit=0): old task...",
            "[2020-01-01 00:01:00] FAILED (exit=1): old fail...",
        ])
        orig = _mod["DAEMON_LOG"]
        try:
            _mod["DAEMON_LOG"] = log_path
            result = parse_log_since(30)
        finally:
            _mod["DAEMON_LOG"] = orig

        assert result["total_completed"] == 0
        assert result["total_failed"] == 0

    def test_missing_log_file(self, tmp_path):
        """parse_log_since handles missing log file gracefully."""
        orig = _mod["DAEMON_LOG"]
        try:
            _mod["DAEMON_LOG"] = tmp_path / "nonexistent.log"
            result = parse_log_since(30)
        finally:
            _mod["DAEMON_LOG"] = orig

        assert result["total_completed"] == 0
        assert result["total_failed"] == 0

    def test_mixed_completed_and_failed(self, tmp_path):
        """parse_log_since counts both completed and failed correctly."""
        log_path = self._make_log(tmp_path, [
            "[2026-03-31 14:00:00] Finished (10s, exit=0): task1",
            "[2026-03-31 14:01:00] FAILED (exit=1): task2",
            "[2026-03-31 14:02:00] Finished (5s, exit=0): task3",
            "[2026-03-31 14:03:00] FAILED (exit=124): task4 timeout",
        ])
        orig = _mod["DAEMON_LOG"]
        try:
            _mod["DAEMON_LOG"] = log_path
            result = parse_log_since(60)
        finally:
            _mod["DAEMON_LOG"] = orig

        assert result["total_completed"] == 2
        assert result["total_failed"] == 2

    def test_empty_log_file(self, tmp_path):
        """parse_log_since handles empty log file."""
        log_path = self._make_log(tmp_path, [])
        orig = _mod["DAEMON_LOG"]
        try:
            _mod["DAEMON_LOG"] = log_path
            result = parse_log_since(30)
        finally:
            _mod["DAEMON_LOG"] = orig

        assert result["total_completed"] == 0
        assert result["total_failed"] == 0


# ── get_changed_files tests ────────────────────────────────────────────


class TestGetChangedFiles:
    def test_returns_test_and_effector_files(self):
        """get_changed_files categorizes files correctly."""
        def mock_run(cmd, **kw):
            r = MagicMock()
            if "diff --name-only" in cmd:
                r.returncode = 0
                r.stdout = (
                    "assays/test_foo.py\n"
                    "effectors/bar.py\n"
                    "metabolon/baz.py\n"
                )
                r.stderr = ""
            else:
                r.returncode = 1
                r.stdout = ""
                r.stderr = ""
            return r

        with patch("subprocess.run", side_effect=mock_run):
            result = get_changed_files()

        assert "assays/test_foo.py" in result["new_tests"]
        assert "effectors/bar.py" in result["new_effectors"]

    def test_git_failure_returns_empty(self):
        """get_changed_files returns empty dicts on git failure."""
        def mock_run(cmd, **kw):
            r = MagicMock()
            r.returncode = 1
            r.stdout = ""
            r.stderr = "fatal: not a git repo"
            return r

        with patch("subprocess.run", side_effect=mock_run):
            result = get_changed_files()

        assert result["new_tests"] == []
        assert result["new_effectors"] == []


# ── run_tests_on_files tests ──────────────────────────────────────────


class TestRunTestsOnFiles:
    def test_passing_test(self):
        """run_tests_on_files records passed/failed counts."""
        def mock_run(cmd, **kw):
            r = MagicMock()
            r.returncode = 0
            r.stdout = "5 passed in 1.2s"
            r.stderr = ""
            return r

        with patch("subprocess.run", side_effect=mock_run):
            results = run_tests_on_files(["assays/test_example.py"])

        assert len(results) == 1
        assert results[0]["passed"] == 5
        assert results[0]["failed"] == 0
        assert results[0]["ok"] is True

    def test_failing_test(self):
        """run_tests_on_files records failures."""
        def mock_run(cmd, **kw):
            r = MagicMock()
            r.returncode = 1
            r.stdout = "3 passed, 2 failed"
            r.stderr = ""
            return r

        with patch("subprocess.run", side_effect=mock_run):
            results = run_tests_on_files(["assays/test_broken.py"])

        assert results[0]["passed"] == 3
        assert results[0]["failed"] == 2
        assert results[0]["ok"] is False

    def test_empty_file_list(self):
        """run_tests_on_files returns empty list when no files given."""
        results = run_tests_on_files([])
        assert results == []

    def test_timeout_handled(self):
        """run_tests_on_files handles timeout."""
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="x", timeout=1)):
            results = run_tests_on_files(["assays/test_slow.py"])

        assert results[0]["exit_code"] == 124
        assert results[0]["ok"] is False


# ── check_consulting_content tests ────────────────────────────────────


class TestCheckConsultingContent:
    def test_file_with_enough_words(self, tmp_path):
        """check_consulting_content passes files with >200 words."""
        f = tmp_path / "deep-dive.md"
        f.write_text(" ".join(["word"] * 250))
        orig_germline = _mod["GERMLINE"]
        orig_epi = _mod["EPIGENOME"]
        try:
            _mod["GERMLINE"] = tmp_path
            _mod["EPIGENOME"] = tmp_path
            results = check_consulting_content([str(f.relative_to(tmp_path))])
        finally:
            _mod["GERMLINE"] = orig_germline
            _mod["EPIGENOME"] = orig_epi

        assert len(results) == 1
        assert results[0]["ok"] is True
        assert results[0]["words"] == 250

    def test_file_too_short(self, tmp_path):
        """check_consulting_content flags files with <=200 words."""
        f = tmp_path / "thin.md"
        f.write_text("short content only ten words")
        orig_germline = _mod["GERMLINE"]
        orig_epi = _mod["EPIGENOME"]
        try:
            _mod["GERMLINE"] = tmp_path
            _mod["EPIGENOME"] = tmp_path
            results = check_consulting_content([str(f.relative_to(tmp_path))])
        finally:
            _mod["GERMLINE"] = orig_germline
            _mod["EPIGENOME"] = orig_epi

        assert len(results) == 1
        assert results[0]["ok"] is False

    def test_missing_file(self, tmp_path):
        """check_consulting_content reports missing file."""
        orig_germline = _mod["GERMLINE"]
        orig_epi = _mod["EPIGENOME"]
        try:
            _mod["GERMLINE"] = tmp_path
            _mod["EPIGENOME"] = tmp_path
            results = check_consulting_content(["nonexistent.md"])
        finally:
            _mod["GERMLINE"] = orig_germline
            _mod["EPIGENOME"] = orig_epi

        assert results[0]["exists"] is False
        assert results[0]["ok"] is False


# ── diagnose_failure tests ────────────────────────────────────────────


class TestDiagnoseFailure:
    def test_import_error(self):
        label, hint = diagnose_failure("ModuleNotFoundError: No module named 'foo'")
        assert label == "import error"
        assert "import" in hint.lower()

    def test_syntax_error(self):
        label, hint = diagnose_failure("SyntaxError: invalid syntax")
        assert label == "syntax error"

    def test_hardcoded_path(self):
        label, hint = diagnose_failure("/home/terry/germline not found")
        assert label == "hardcoded Mac path"
        assert "Path.home()" in hint

    def test_timeout(self):
        label, hint = diagnose_failure("subprocess.TimeoutExpired after 1800s")
        assert label == "timeout"

    def test_unknown_error(self):
        label, hint = diagnose_failure("something weird happened")
        assert label == "unknown"

    def test_permission_error(self):
        label, hint = diagnose_failure("PermissionError: [Errno 13]")
        assert label == "permission denied"

    def test_file_not_found(self):
        label, hint = diagnose_failure("FileNotFoundError: missing.py")
        assert label == "missing file"


# ── get_failed_tasks_from_queue tests ─────────────────────────────────


class TestGetFailedTasksFromQueue:
    def _make_queue(self, tmp_path: Path, content: str) -> Path:
        qd = tmp_path / "germline" / "loci"
        qd.mkdir(parents=True)
        qf = qd / "golem-queue.md"
        qf.write_text(content)
        return qf

    def test_extracts_failed_tasks(self, tmp_path):
        qf = self._make_queue(tmp_path, textwrap.dedent("""\
            - [ ] `golem "pending"`
            - [!] `golem "failed1"`
            - [!] `golem "failed2" (retry)`
            - [x] `golem "done"`
        """))
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            result = get_failed_tasks_from_queue()
        finally:
            _mod["QUEUE_FILE"] = orig

        assert len(result) == 2
        assert result[0]["cmd"] == 'golem "failed1"'
        assert result[1]["cmd"] == 'golem "failed2" (retry)'

    def test_no_failed_tasks(self, tmp_path):
        qf = self._make_queue(tmp_path, "- [ ] `golem \"ok\"`\n")
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            result = get_failed_tasks_from_queue()
        finally:
            _mod["QUEUE_FILE"] = orig

        assert result == []

    def test_missing_queue(self, tmp_path):
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = tmp_path / "nope.md"
            result = get_failed_tasks_from_queue()
        finally:
            _mod["QUEUE_FILE"] = orig

        assert result == []


# ── write_fixed_tasks tests ───────────────────────────────────────────


class TestWriteFixedTasks:
    def _make_queue(self, tmp_path: Path, content: str) -> Path:
        qd = tmp_path / "germline" / "loci"
        qd.mkdir(parents=True)
        qf = qd / "golem-queue.md"
        qf.write_text(content)
        return qf

    def test_writes_fixed_tasks(self, tmp_path):
        qf = self._make_queue(tmp_path, textwrap.dedent("""\
            ## Pending

            - [!] `golem "task1" (retry)`
            - [ ] `golem "task2"`
        """))
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            count = write_fixed_tasks(
                [{"cmd": 'golem "task1" (retry)', "line_num": 2}],
                [{"hint": "Fix syntax errors"}],
            )
        finally:
            _mod["QUEUE_FILE"] = orig

        assert count == 1
        content = qf.read_text()
        assert "FIX: Fix syntax errors" in content
        # Should have stripped (retry)
        assert 'golem "task1"' in content
        assert "(retry)" not in content.split("FIX")[0]

    def test_no_tasks_no_writes(self, tmp_path):
        qf = self._make_queue(tmp_path, "## Pending\n")
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            count = write_fixed_tasks([], [])
        finally:
            _mod["QUEUE_FILE"] = orig

        assert count == 0


# ── generate_summary tests ────────────────────────────────────────────


class TestGenerateSummary:
    def test_summary_contains_sections(self):
        summary = generate_summary(
            log_data={"total_completed": 3, "total_failed": 1,
                      "completed": [], "failed": []},
            changed={"new_tests": ["assays/test_x.py"],
                     "new_effectors": ["effectors/y.py"],
                     "new_consulting": [], "other": []},
            test_results=[{"file": "assays/test_x.py", "passed": 5, "failed": 0, "ok": True, "tail": ""}],
            consulting_results=[],
            diagnoses=[{"cmd": "task", "label": "timeout", "hint": "reduce scope"}],
            fixed_count=1,
        )
        assert "## Task Activity" in summary
        assert "Completed: 3" in summary
        assert "Failed: 1" in summary
        assert "## Test Results" in summary
        assert "## Failure Diagnoses" in summary
        assert "timeout" in summary
        assert "Fixed tasks requeued: 1" in summary

    def test_summary_no_data(self):
        summary = generate_summary(
            log_data={"total_completed": 0, "total_failed": 0,
                      "completed": [], "failed": []},
            changed={"new_tests": [], "new_effectors": [],
                     "new_consulting": [], "other": []},
            test_results=[], consulting_results=[],
            diagnoses=[], fixed_count=0,
        )
        assert "Completed: 0" in summary
        assert "All tests OK: yes" in summary


# ── count_pending_tasks tests ─────────────────────────────────────────


class TestCountPendingTasks:
    def _make_queue(self, tmp_path: Path, content: str) -> Path:
        qd = tmp_path / "germline" / "loci"
        qd.mkdir(parents=True)
        qf = qd / "golem-queue.md"
        qf.write_text(content)
        return qf

    def test_counts_correctly(self, tmp_path):
        qf = self._make_queue(tmp_path, textwrap.dedent("""\
            - [ ] `golem "task1"`
            - [ ] `golem "task2"`
            - [x] `golem "done"`
            - [!] `golem "fail"`
            - [ ] `golem "task3"`
        """))
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            count = count_pending_tasks()
        finally:
            _mod["QUEUE_FILE"] = orig

        assert count == 3

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


# ── find_untested_effectors tests ─────────────────────────────────────


class TestFindUntestedEffectors:
    def test_finds_untested(self, tmp_path):
        """find_untested_effectors identifies effectors without tests."""
        eff_dir = tmp_path / "effectors"
        eff_dir.mkdir()
        (eff_dir / "foo-tool").write_text("#!/usr/bin/env python3\n")
        (eff_dir / "bar-util.py").write_text("#!/usr/bin/env python3\n")
        (eff_dir / "tested-thing").write_text("#!/usr/bin/env python3\n")

        assays_dir = tmp_path / "assays"
        assays_dir.mkdir()
        (assays_dir / "test_tested_thing.py").write_text("def test_x(): pass\n")

        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            untested = find_untested_effectors()
        finally:
            _mod["GERMLINE"] = orig

        assert "foo-tool" in untested
        assert "bar-util.py" in untested
        assert "tested-thing" not in untested

    def test_no_effectors_dir(self, tmp_path):
        """find_untested_effectors returns empty if no effectors dir."""
        orig = _mod["GERMLINE"]
        try:
            _mod["GERMLINE"] = tmp_path
            result = find_untested_effectors()
        finally:
            _mod["GERMLINE"] = orig

        assert result == []


# ── generate_queue_tasks tests ────────────────────────────────────────


class TestGenerateQueueTasks:
    def test_generates_correct_count(self):
        tasks = generate_queue_tasks(["foo-tool", "bar-util.py"], count=2)
        assert len(tasks) == 2
        assert all(t.startswith("- [ ] `golem") for t in tasks)

    def test_truncates_to_count(self):
        tasks = generate_queue_tasks(["a", "b", "c", "d"], count=2)
        assert len(tasks) == 2

    def test_rotates_providers(self):
        tasks = generate_queue_tasks(["a", "b", "c", "d"], count=4)
        providers = []
        for t in tasks:
            m = __import__("re").search(r"--provider (\w+)", t)
            if m:
                providers.append(m.group(1))
        # Should cycle through providers
        assert len(set(providers)) >= 2

    def test_empty_list(self):
        tasks = generate_queue_tasks([], count=50)
        assert tasks == []


# ── append_tasks_to_queue tests ───────────────────────────────────────


class TestAppendTasksToQueue:
    def _make_queue(self, tmp_path: Path, content: str) -> Path:
        qd = tmp_path / "germline" / "loci"
        qd.mkdir(parents=True)
        qf = qd / "golem-queue.md"
        qf.write_text(content)
        return qf

    def test_appends_to_pending(self, tmp_path):
        qf = self._make_queue(tmp_path, textwrap.dedent("""\
            ## Pending

            - [ ] `golem "existing"`

            ## Done
        """))
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            added = append_tasks_to_queue(['- [ ] `golem "new task"`'])
        finally:
            _mod["QUEUE_FILE"] = orig

        assert added == 1
        content = qf.read_text()
        assert 'golem "new task"' in content
        assert 'golem "existing"' in content

    def test_empty_task_list(self, tmp_path):
        qf = self._make_queue(tmp_path, "## Pending\n")
        orig = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = qf
            added = append_tasks_to_queue([])
        finally:
            _mod["QUEUE_FILE"] = orig

        assert added == 0


# ── write_summary tests ───────────────────────────────────────────────


class TestWriteSummary:
    def test_writes_file(self, tmp_path):
        target = tmp_path / "copia" / "golem-review-latest.md"
        orig = _mod["REVIEW_SUMMARY"]
        try:
            _mod["REVIEW_SUMMARY"] = target
            path = write_summary("# Test Summary\n\nHello")
        finally:
            _mod["REVIEW_SUMMARY"] = orig

        assert path == target
        assert target.exists()
        assert "Test Summary" in target.read_text()


# ── main integration tests ────────────────────────────────────────────


class TestMain:
    def test_help_flag(self, capsys):
        rc = main(["--help"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "META-GOLEM" in out

    def test_basic_run(self, tmp_path, capsys):
        """main runs end-to-end with mocked git and missing log."""
        log_path = tmp_path / "golem-daemon.log"
        log_path.write_text("")
        queue_dir = tmp_path / "germline" / "loci"
        queue_dir.mkdir(parents=True)
        queue_path = queue_dir / "golem-queue.md"
        queue_path.write_text("## Pending\n")
        summary_path = tmp_path / "copia" / "golem-review-latest.md"

        orig_log = _mod["DAEMON_LOG"]
        orig_queue = _mod["QUEUE_FILE"]
        orig_summary = _mod["REVIEW_SUMMARY"]
        orig_germline = _mod["GERMLINE"]

        def mock_run(cmd, **kw):
            r = MagicMock()
            r.returncode = 1
            r.stdout = ""
            r.stderr = ""
            return r

        try:
            _mod["DAEMON_LOG"] = log_path
            _mod["QUEUE_FILE"] = queue_path
            _mod["REVIEW_SUMMARY"] = summary_path
            _mod["GERMLINE"] = tmp_path

            with patch("subprocess.run", side_effect=mock_run):
                rc = main(["--since", "30m"])
        finally:
            _mod["DAEMON_LOG"] = orig_log
            _mod["QUEUE_FILE"] = orig_queue
            _mod["REVIEW_SUMMARY"] = orig_summary
            _mod["GERMLINE"] = orig_germline

        assert rc == 0
        assert summary_path.exists()
        out = capsys.readouterr().out
        assert "Reviewing last 30m" in out

    def test_auto_requeue(self, tmp_path, capsys):
        """main with --auto-requeue generates tasks when queue is thin."""
        log_path = tmp_path / "golem-daemon.log"
        log_path.write_text("")
        queue_dir = tmp_path / "germline" / "loci"
        queue_dir.mkdir(parents=True)
        queue_path = queue_dir / "golem-queue.md"
        queue_path.write_text("## Pending\n")
        summary_path = tmp_path / "copia" / "golem-review-latest.md"
        eff_dir = tmp_path / "effectors"
        eff_dir.mkdir()
        (eff_dir / "untested-eff").write_text("#!/usr/bin/env python3\n")

        orig_log = _mod["DAEMON_LOG"]
        orig_queue = _mod["QUEUE_FILE"]
        orig_summary = _mod["REVIEW_SUMMARY"]
        orig_germline = _mod["GERMLINE"]

        def mock_run(cmd, **kw):
            r = MagicMock()
            r.returncode = 1
            r.stdout = ""
            r.stderr = ""
            return r

        try:
            _mod["DAEMON_LOG"] = log_path
            _mod["QUEUE_FILE"] = queue_path
            _mod["REVIEW_SUMMARY"] = summary_path
            _mod["GERMLINE"] = tmp_path

            with patch("subprocess.run", side_effect=mock_run):
                rc = main(["--auto-requeue", "--since", "5"])
        finally:
            _mod["DAEMON_LOG"] = orig_log
            _mod["QUEUE_FILE"] = orig_queue
            _mod["REVIEW_SUMMARY"] = orig_summary
            _mod["GERMLINE"] = orig_germline

        assert rc == 0
        out = capsys.readouterr().out
        assert "Auto-generated" in out
