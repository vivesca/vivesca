"""Tests for golem-review — meta-golem that reviews golem output and queues more work."""
from __future__ import annotations

import json
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_golem_review():
    """Load the golem-review module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/golem-review").read()
    ns: dict = {"__name__": "golem_review_test"}
    exec(source, ns)
    return ns


# ── parse_log_recent tests ─────────────────────────────────────────────


class TestParseLogRecent:
    """Tests for parse_log_recent — extracts completed/failed tasks from daemon log."""

    def setup_method(self):
        self._mod = _load_golem_review()
        self.parse_log_recent = self._mod["parse_log_recent"]

    def test_extracts_finished_tasks(self, tmp_path):
        """parse_log_recent returns tasks with Finished lines."""
        log = tmp_path / "golem-daemon.log"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write_text(
            f"[{now}] Finished (120s, exit=0): golem --provider zhipu \"build something\"\n"
            f"[{now}] Finished (60s, exit=1): golem --provider volcano \"broken task\"\n"
        )
        tasks = self.parse_log_recent(log, since_minutes=30)
        assert len(tasks) == 2
        assert tasks[0]["exit_code"] == 0
        assert tasks[1]["exit_code"] == 1

    def test_filters_by_since_minutes(self, tmp_path):
        """parse_log_recent only returns tasks within the time window."""
        log = tmp_path / "golem-daemon.log"
        now = datetime.now()
        recent = now.strftime("%Y-%m-%d %H:%M:%S")
        old = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        log.write_text(
            f"[{old}] Finished (10s, exit=0): golem \"old task\"\n"
            f"[{recent}] Finished (10s, exit=0): golem \"recent task\"\n"
        )
        tasks = self.parse_log_recent(log, since_minutes=30)
        assert len(tasks) == 1
        assert "recent task" in tasks[0]["cmd"]

    def test_skips_non_finished_lines(self, tmp_path):
        """parse_log_recent ignores Starting/Queued/Running lines."""
        log = tmp_path / "golem-daemon.log"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write_text(
            f"[{now}] Starting: golem \"something\"\n"
            f"[{now}] Running: 4 tasks\n"
            f"[{now}] Queued [zhipu]: golem \"else\"\n"
        )
        tasks = self.parse_log_recent(log, since_minutes=30)
        assert tasks == []

    def test_handles_missing_log_file(self, tmp_path):
        """parse_log_recent returns empty list for missing file."""
        log = tmp_path / "nonexistent.log"
        tasks = self.parse_log_recent(log, since_minutes=30)
        assert tasks == []

    def test_extracts_duration_and_cmd(self, tmp_path):
        """parse_log_recent extracts duration, exit code, and command."""
        log = tmp_path / "golem-daemon.log"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write_text(
            f'[{now}] Finished (543s, exit=0): golem --provider zhipu --max-turns 35 "Create effectors/foo"\n'
        )
        tasks = self.parse_log_recent(log, since_minutes=30)
        assert len(tasks) == 1
        assert tasks[0]["duration"] == 543
        assert tasks[0]["exit_code"] == 0
        assert "effectors/foo" in tasks[0]["cmd"]

    def test_timeout_exit_code(self, tmp_path):
        """parse_log_recent captures timeout (exit=124) entries."""
        log = tmp_path / "golem-daemon.log"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write_text(
            f'[{now}] Finished (1800s, exit=124): golem --provider zhipu "slow task"\n'
        )
        tasks = self.parse_log_recent(log, since_minutes=30)
        assert len(tasks) == 1
        assert tasks[0]["exit_code"] == 124


# ── parse_jsonl_recent tests ────────────────────────────────────────────


class TestParseJsonlRecent:
    """Tests for parse_jsonl_recent — reads golem.jsonl for structured data."""

    def setup_method(self):
        self._mod = _load_golem_review()
        self.parse_jsonl_recent = self._mod["parse_jsonl_recent"]

    def test_reads_jsonl_entries(self, tmp_path):
        """parse_jsonl_recent returns structured entries from JSONL."""
        jsonl = tmp_path / "golem.jsonl"
        now = datetime.now(timezone.utc).isoformat()
        jsonl.write_text(
            json.dumps({
                "ts": now, "provider": "zhipu", "duration": 120,
                "exit": 0, "turns": 30, "prompt": "build X",
                "files_created": 2, "tests_passed": 5, "tests_failed": 1,
                "pytest_exit": 1
            }) + "\n"
        )
        entries = self.parse_jsonl_recent(jsonl, since_minutes=30)
        assert len(entries) == 1
        assert entries[0]["provider"] == "zhipu"
        assert entries[0]["tests_passed"] == 5
        assert entries[0]["tests_failed"] == 1

    def test_filters_by_time(self, tmp_path):
        """parse_jsonl_recent only returns recent entries."""
        jsonl = tmp_path / "golem.jsonl"
        now = datetime.now(timezone.utc)
        recent = now.isoformat()
        old = (now - timedelta(hours=2)).isoformat()
        jsonl.write_text(
            json.dumps({"ts": old, "provider": "zhipu", "duration": 10,
                        "exit": 0, "turns": 1, "prompt": "old",
                        "files_created": 0, "tests_passed": 0, "tests_failed": 0,
                        "pytest_exit": 0}) + "\n"
            + json.dumps({"ts": recent, "provider": "volcano", "duration": 20,
                          "exit": 0, "turns": 2, "prompt": "recent",
                          "files_created": 1, "tests_passed": 3, "tests_failed": 0,
                          "pytest_exit": 0}) + "\n"
        )
        entries = self.parse_jsonl_recent(jsonl, since_minutes=30)
        assert len(entries) == 1
        assert entries[0]["provider"] == "volcano"

    def test_handles_missing_file(self, tmp_path):
        """parse_jsonl_recent returns empty for missing file."""
        jsonl = tmp_path / "nonexistent.jsonl"
        entries = self.parse_jsonl_recent(jsonl, since_minutes=30)
        assert entries == []

    def test_handles_malformed_json(self, tmp_path):
        """parse_jsonl_recent skips malformed lines gracefully."""
        jsonl = tmp_path / "golem.jsonl"
        now = datetime.now(timezone.utc).isoformat()
        jsonl.write_text(
            "not json at all\n"
            + json.dumps({"ts": now, "provider": "zhipu", "duration": 10,
                          "exit": 0, "turns": 1, "prompt": "good",
                          "files_created": 0, "tests_passed": 0, "tests_failed": 0,
                          "pytest_exit": 0}) + "\n"
            + "\n"
        )
        entries = self.parse_jsonl_recent(jsonl, since_minutes=30)
        assert len(entries) == 1


# ── check_output_files tests ───────────────────────────────────────────


class TestCheckOutputFiles:
    """Tests for check_output_files — verifies output files were created."""

    def setup_method(self):
        self._mod = _load_golem_review()
        self.check_output_files = self._mod["check_output_files"]

    def test_detects_new_files(self, tmp_path):
        """check_output_files returns list of files changed in recent commits."""
        germline = tmp_path / "germline"
        germline.mkdir()
        (germline / "assays").mkdir()
        (germline / "assays" / "test_new.py").write_text("def test_x(): pass\n")

        with patch("subprocess.run") as mock_run:
            result = MagicMock()
            result.returncode = 0
            result.stdout = "assays/test_new.py\neffectors/new-tool\n"
            mock_run.return_value = result
            files = self.check_output_files(str(germline), head_range=5)
        assert "assays/test_new.py" in files

    def test_handles_git_failure(self, tmp_path):
        """check_output_files returns empty list on git failure."""
        with patch("subprocess.run") as mock_run:
            result = MagicMock()
            result.returncode = 1
            result.stdout = ""
            mock_run.return_value = result
            files = self.check_output_files(str(tmp_path / "germline"), head_range=5)
        assert files == []


# ── run_pytest_on_files tests ───────────────────────────────────────────


class TestRunPytestOnFiles:
    """Tests for run_pytest_on_files — runs pytest and counts pass/fail."""

    def setup_method(self):
        self._mod = _load_golem_review()
        self.run_pytest_on_files = self._mod["run_pytest_on_files"]

    def test_passing_tests(self):
        """run_pytest_on_files returns pass count when tests pass."""
        with patch("subprocess.run") as mock_run:
            result = MagicMock()
            result.returncode = 0
            result.stdout = "2 passed in 0.5s\n"
            mock_run.return_value = result
            passed, failed, output = self.run_pytest_on_files(
                ["/home/terry/germline/assays/test_foo.py"],
                cwd="/home/terry/germline"
            )
        assert passed == 2
        assert failed == 0

    def test_failing_tests(self):
        """run_pytest_on_files returns fail count when tests fail."""
        with patch("subprocess.run") as mock_run:
            result = MagicMock()
            result.returncode = 1
            result.stdout = "3 passed, 2 failed in 1.2s\n"
            mock_run.return_value = result
            passed, failed, output = self.run_pytest_on_files(
                ["/home/terry/germline/assays/test_bar.py"],
                cwd="/home/terry/germline"
            )
        assert passed == 3
        assert failed == 2

    def test_empty_file_list(self):
        """run_pytest_on_files returns zeros for empty file list."""
        passed, failed, output = self.run_pytest_on_files([], cwd="/home/terry/germline")
        assert passed == 0
        assert failed == 0

    def test_timeout_handled(self):
        """run_pytest_on_files handles timeout gracefully."""
        import subprocess
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="pytest", timeout=120)
            passed, failed, output = self.run_pytest_on_files(
                ["/home/terry/germline/assays/test_timeout.py"],
                cwd="/home/terry/germline"
            )
        assert passed == 0
        assert "timeout" in output.lower()


# ── check_consulting_content tests ──────────────────────────────────────


class TestCheckConsultingContent:
    """Tests for check_consulting_content — verifies consulting files exist and have >200 words."""

    def setup_method(self):
        self._mod = _load_golem_review()
        self.check_consulting_content = self._mod["check_consulting_content"]

    def test_good_consulting_file(self, tmp_path):
        """check_consulting_content returns ok for files with >200 words."""
        f = tmp_path / "article.md"
        f.write_text(" ".join(["word"] * 250))
        result = self.check_consulting_content([str(f)])
        assert len(result) == 1
        assert result[0]["ok"] is True
        assert result[0]["words"] >= 200

    def test_short_consulting_file(self, tmp_path):
        """check_consulting_content flags files with <200 words."""
        f = tmp_path / "short.md"
        f.write_text("Short content here only.")
        result = self.check_consulting_content([str(f)])
        assert len(result) == 1
        assert result[0]["ok"] is False

    def test_missing_file(self, tmp_path):
        """check_consulting_content handles missing files."""
        result = self.check_consulting_content([str(tmp_path / "missing.md")])
        assert len(result) == 1
        assert result[0]["ok"] is False

    def test_empty_list(self):
        """check_consulting_content handles empty list."""
        result = self.check_consulting_content([])
        assert result == []


# ── diagnose_failure tests ──────────────────────────────────────────────


class TestDiagnoseFailure:
    """Tests for diagnose_failure — diagnoses common failure patterns."""

    def setup_method(self):
        self._mod = _load_golem_review()
        self.diagnose_failure = self._mod["diagnose_failure"]

    def test_path_issue(self):
        """diagnose_failure identifies /Users/terry path issues."""
        log_tail = "FileNotFoundError: /Users/terry/germline/effectors/foo"
        result = self.diagnose_failure(log_tail)
        assert result["category"] == "path_issue"
        assert "Users" in result["detail"] or "path" in result["detail"].lower()

    def test_import_error(self):
        """diagnose_failure identifies import errors."""
        log_tail = "ModuleNotFoundError: No module named 'metabolon.foo'"
        result = self.diagnose_failure(log_tail)
        assert result["category"] == "import_error"

    def test_timeout(self):
        """diagnose_failure identifies timeout."""
        log_tail = "timeout after 1800s"
        result = self.diagnose_failure(log_tail)
        assert result["category"] == "timeout"

    def test_syntax_error(self):
        """diagnose_failure identifies syntax errors."""
        log_tail = "SyntaxError: invalid syntax (test_foo.py, line 42)"
        result = self.diagnose_failure(log_tail)
        assert result["category"] == "syntax_error"

    def test_unknown_failure(self):
        """diagnose_failure returns unknown for unrecognized patterns."""
        log_tail = "something weird happened"
        result = self.diagnose_failure(log_tail)
        assert result["category"] == "unknown"

    def test_permission_error(self):
        """diagnose_failure identifies permission errors."""
        log_tail = "PermissionError: [Errno 13] Permission denied: '/root/file'"
        result = self.diagnose_failure(log_tail)
        assert result["category"] == "permission_error"


# ── generate_fixed_task tests ──────────────────────────────────────────


class TestGenerateFixedTask:
    """Tests for generate_fixed_task — creates fixed task spec from failure diagnosis."""

    def setup_method(self):
        self._mod = _load_golem_review()
        self.generate_fixed_task = self._mod["generate_fixed_task"]

    def test_path_fix_task(self):
        """generate_fixed_task produces a corrected task for path issues."""
        diagnosis = {"category": "path_issue", "detail": "Used /Users/terry/ instead of /home/terry/"}
        original_cmd = 'golem --provider zhipu "Create effectors/foo"'
        fixed = self.generate_fixed_task(original_cmd, diagnosis)
        assert "golem" in fixed
        assert "/home/terry/" in fixed or "Path.home()" in fixed

    def test_import_fix_task(self):
        """generate_fixed_task produces a corrected task for import errors."""
        diagnosis = {"category": "import_error", "detail": "ModuleNotFoundError: metabolon.foo"}
        original_cmd = 'golem --provider zhipu "Build effectors/bar"'
        fixed = self.generate_fixed_task(original_cmd, diagnosis)
        assert "golem" in fixed
        assert "import" in fixed.lower() or "module" in fixed.lower()

    def test_timeout_fix_task(self):
        """generate_fixed_task produces a task with more turns for timeouts."""
        diagnosis = {"category": "timeout", "detail": "timeout after 1800s"}
        original_cmd = 'golem --provider zhipu --max-turns 25 "Big task"'
        fixed = self.generate_fixed_task(original_cmd, diagnosis)
        assert "golem" in fixed
        # Should increase turns or split the task
        assert "max-turns" not in fixed or "35" in fixed or "40" in fixed or "50" in fixed or "split" in fixed.lower()

    def test_unknown_produces_retry(self):
        """generate_fixed_task produces a retry task for unknown failures."""
        diagnosis = {"category": "unknown", "detail": "unrecognized error"}
        original_cmd = 'golem --provider zhipu "Some task"'
        fixed = self.generate_fixed_task(original_cmd, diagnosis)
        assert "golem" in fixed


# ── count_pending_tasks tests ──────────────────────────────────────────


class TestCountPendingTasks:
    """Tests for count_pending_tasks — counts [ ] tasks in queue."""

    def setup_method(self):
        self._mod = _load_golem_review()
        self.count_pending_tasks = self._mod["count_pending_tasks"]

    def test_counts_pending(self, tmp_path):
        """count_pending_tasks returns correct count of [ ] entries."""
        queue = tmp_path / "golem-queue.md"
        queue.write_text(
            "# Queue\n\n"
            "- [ ] `golem \"task1\"`\n"
            "- [ ] `golem \"task2\"`\n"
            "- [x] `golem \"done1\"`\n"
            "- [!] `golem \"fail1\"`\n"
            "- [ ] `golem \"task3\"`\n"
        )
        count = self.count_pending_tasks(queue)
        assert count == 3

    def test_missing_file(self, tmp_path):
        """count_pending_tasks returns 0 for missing file."""
        count = self.count_pending_tasks(tmp_path / "nope.md")
        assert count == 0

    def test_empty_file(self, tmp_path):
        """count_pending_tasks returns 0 for empty file."""
        queue = tmp_path / "golem-queue.md"
        queue.write_text("")
        count = self.count_pending_tasks(queue)
        assert count == 0


# ── generate_queue_tasks tests ─────────────────────────────────────────


class TestGenerateQueueTasks:
    """Tests for generate_queue_tasks — auto-generates tasks for untested effectors."""

    def setup_method(self):
        self._mod = _load_golem_review()
        self.generate_queue_tasks = self._mod["generate_queue_tasks"]

    def test_generates_for_untested_effectors(self, tmp_path):
        """generate_queue_tasks produces tasks for effectors lacking tests."""
        effectors_dir = tmp_path / "effectors"
        effectors_dir.mkdir()
        (effectors_dir / "my-tool").write_text("#!/usr/bin/env python3\nprint('hi')")
        (effectors_dir / "other-tool").write_text("#!/usr/bin/env python3\nprint('bye')")

        assays_dir = tmp_path / "assays"
        assays_dir.mkdir()
        # Only test for my-tool
        (assays_dir / "test_my_tool.py").write_text("def test_foo(): pass\n")

        tasks = self.generate_queue_tasks(
            str(effectors_dir), str(assays_dir), count=50
        )
        assert len(tasks) > 0
        # Should include a task for other-tool (no test)
        assert any("other-tool" in t or "other_tool" in t for t in tasks)

    def test_respects_count_limit(self, tmp_path):
        """generate_queue_tasks limits output to count."""
        effectors_dir = tmp_path / "effectors"
        effectors_dir.mkdir()
        for i in range(20):
            (effectors_dir / f"tool-{i}").write_text("# script")

        assays_dir = tmp_path / "assays"
        assays_dir.mkdir()

        tasks = self.generate_queue_tasks(
            str(effectors_dir), str(assays_dir), count=5
        )
        assert len(tasks) <= 5

    def test_skips_already_tested(self, tmp_path):
        """generate_queue_tasks skips effectors with existing tests."""
        effectors_dir = tmp_path / "effectors"
        effectors_dir.mkdir()
        (effectors_dir / "tested-tool").write_text("# script")

        assays_dir = tmp_path / "assays"
        assays_dir.mkdir()
        (assays_dir / "test_tested_tool.py").write_text("def test_foo(): pass\n")

        tasks = self.generate_queue_tasks(
            str(effectors_dir), str(assays_dir), count=50
        )
        assert len(tasks) == 0


# ── write_review_summary tests ─────────────────────────────────────────


class TestWriteReviewSummary:
    """Tests for write_review_summary — writes review summary to loci/copia/."""

    def setup_method(self):
        self._mod = _load_golem_review()
        self.write_review_summary = self._mod["write_review_summary"]

    def test_writes_summary_file(self, tmp_path):
        """write_review_summary creates the markdown review file."""
        out_file = tmp_path / "golem-review-latest.md"
        summary = {
            "completed": 10,
            "failed": 2,
            "tests_passed": 45,
            "tests_failed": 3,
            "consulting_ok": 8,
            "consulting_thin": 1,
            "diagnoses": [
                {"category": "path_issue", "detail": "/Users/terry/", "fixed_cmd": 'golem "fixed"'}
            ],
            "requeued": 1,
            "auto_generated": 0,
        }
        self.write_review_summary(out_file, summary)
        assert out_file.exists()
        content = out_file.read_text()
        assert "completed" in content.lower() or "10" in content
        assert "failed" in content.lower() or "2" in content

    def test_summary_is_valid_markdown(self, tmp_path):
        """write_review_summary produces valid markdown with headers."""
        out_file = tmp_path / "golem-review-latest.md"
        summary = {
            "completed": 0, "failed": 0,
            "tests_passed": 0, "tests_failed": 0,
            "consulting_ok": 0, "consulting_thin": 0,
            "diagnoses": [], "requeued": 0, "auto_generated": 0,
        }
        self.write_review_summary(out_file, summary)
        content = out_file.read_text()
        assert content.startswith("#")  # Has markdown header


# ── parse_since_arg tests ──────────────────────────────────────────────


class TestParseSinceArg:
    """Tests for parse_since_arg — parses --since argument (e.g., 30m, 2h)."""

    def setup_method(self):
        self._mod = _load_golem_review()
        self.parse_since_arg = self._mod["parse_since_arg"]

    def test_minutes(self):
        """parse_since_arg handles Xm format."""
        assert self.parse_since_arg("30m") == 30

    def test_hours(self):
        """parse_since_arg handles Xh format."""
        assert self.parse_since_arg("2h") == 120

    def test_default(self):
        """parse_since_arg defaults to 30 minutes."""
        assert self.parse_since_arg(None) == 30

    def test_plain_number(self):
        """parse_since_arg handles plain number (minutes)."""
        assert self.parse_since_arg("60") == 60

    def test_invalid(self):
        """parse_since_arg returns 30 for invalid input."""
        assert self.parse_since_arg("invalid") == 30


# ── append_to_queue tests ──────────────────────────────────────────────


class TestAppendToQueue:
    """Tests for append_to_queue — appends fixed tasks to golem-queue.md."""

    def setup_method(self):
        self._mod = _load_golem_review()
        self.append_to_queue = self._mod["append_to_queue"]

    def test_appends_tasks(self, tmp_path):
        """append_to_queue adds new task lines to queue."""
        queue = tmp_path / "golem-queue.md"
        queue.write_text("# Queue\n\n## Pending\n")
        self.append_to_queue(queue, ['golem --provider zhipu "fixed task 1"'])
        content = queue.read_text()
        assert "fixed task 1" in content

    def test_appends_multiple_tasks(self, tmp_path):
        """append_to_queue adds multiple tasks."""
        queue = tmp_path / "golem-queue.md"
        queue.write_text("# Queue\n\n## Pending\n")
        self.append_to_queue(queue, [
            'golem --provider zhipu "task A"',
            'golem --provider volcano "task B"',
        ])
        content = queue.read_text()
        assert "task A" in content
        assert "task B" in content

    def test_formats_as_pending(self, tmp_path):
        """append_to_queue formats tasks as pending ([ ])."""
        queue = tmp_path / "golem-queue.md"
        queue.write_text("# Queue\n\n## Pending\n")
        self.append_to_queue(queue, ['golem --provider zhipu "task"'])
        content = queue.read_text()
        assert "- [ ]" in content

    def test_handles_missing_file(self, tmp_path):
        """append_to_queue creates queue file if missing."""
        queue = tmp_path / "golem-queue.md"
        self.append_to_queue(queue, ['golem --provider zhipu "new task"'])
        assert queue.exists()
        content = queue.read_text()
        assert "new task" in content


# ── Integration test ────────────────────────────────────────────────────


class TestIntegration:
    """Integration: full review cycle with mocked subprocess/git."""

    def setup_method(self):
        self._mod = _load_golem_review()

    def test_full_review_cycle(self, tmp_path):
        """Full review cycle: parse logs, check files, write summary, requeue."""
        # Setup
        log = tmp_path / "golem-daemon.log"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.write_text(
            f'[{now}] Finished (100s, exit=0): golem --provider zhipu "build foo"\n'
            f'[{now}] Finished (200s, exit=1): golem --provider volcano "build bar"\n'
        )

        jsonl = tmp_path / "golem.jsonl"
        now_iso = datetime.now(timezone.utc).isoformat()
        jsonl.write_text(
            json.dumps({"ts": now_iso, "provider": "zhipu", "duration": 100,
                        "exit": 0, "turns": 20, "prompt": "build foo",
                        "files_created": 2, "tests_passed": 5, "tests_failed": 0,
                        "pytest_exit": 0}) + "\n"
            + json.dumps({"ts": now_iso, "provider": "volcano", "duration": 200,
                          "exit": 1, "turns": 15, "prompt": "build bar",
                          "files_created": 0, "tests_passed": 0, "tests_failed": 3,
                          "pytest_exit": 1}) + "\n"
        )

        queue = tmp_path / "golem-queue.md"
        queue.write_text("# Queue\n\n## Pending\n\n- [ ] `golem --provider zhipu \"existing task\"`\n")

        out_file = tmp_path / "golem-review-latest.md"

        # Mock git diff and pytest
        with patch("subprocess.run") as mock_run:
            git_result = MagicMock()
            git_result.returncode = 0
            git_result.stdout = "assays/test_foo.py\nassays/test_bar.py\n"

            pytest_result_ok = MagicMock()
            pytest_result_ok.returncode = 0
            pytest_result_ok.stdout = "5 passed in 1s\n"

            pytest_result_fail = MagicMock()
            pytest_result_fail.returncode = 1
            pytest_result_fail.stdout = "3 passed, 2 failed in 2s\n"

            mock_run.side_effect = [git_result, pytest_result_ok, pytest_result_fail]

            review_fn = self._mod["run_review"]
            summary = review_fn(
                log_path=log,
                jsonl_path=jsonl,
                queue_path=queue,
                output_path=out_file,
                germline_dir=str(tmp_path),
                since_minutes=30,
                auto_requeue=True,
            )

        assert out_file.exists()
        assert summary["completed"] >= 1
        assert summary["failed"] >= 1
        assert isinstance(summary["diagnoses"], list)
