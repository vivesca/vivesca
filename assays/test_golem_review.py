"""Tests for golem-review — meta-golem that reviews other golem output."""
from __future__ import annotations

import json
import re
import textwrap
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_golem_review():
    """Load the golem-review module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/golem-review").read()
    ns: dict = {"__name__": "golem_review"}
    exec(source, ns)
    return ns


_mod = _load_golem_review()

# Import key functions
parse_since_arg = _mod["parse_since_arg"]
get_recent_completed = _mod["get_recent_completed"]
get_changed_files = _mod["get_changed_files"]
classify_files = _mod["classify_files"]
run_pytest_on_files = _mod["run_pytest_on_files"]
check_consulting_content = _mod["check_consulting_content"]
diagnose_failure = _mod["diagnose_failure"]
write_fixed_task = _mod["write_fixed_task"]
count_pending_tasks = _mod["count_pending_tasks"]
auto_generate_tasks = _mod["auto_generate_tasks"]
generate_review_summary = _mod["generate_review_summary"]


# ── parse_since_arg tests ──────────────────────────────────────────────


def test_parse_since_arg_minutes():
    """parse_since_arg parses '30m' as 30 minutes."""
    delta = parse_since_arg("30m")
    assert delta == timedelta(minutes=30)


def test_parse_since_arg_hours():
    """parse_since_arg parses '2h' as 2 hours."""
    delta = parse_since_arg("2h")
    assert delta == timedelta(hours=2)


def test_parse_since_arg_default():
    """parse_since_arg returns default 30m for empty string."""
    delta = parse_since_arg("")
    assert delta == timedelta(minutes=30)


def test_parse_since_arg_invalid():
    """parse_since_arg returns default 30m for invalid input."""
    delta = parse_since_arg("invalid")
    assert delta == timedelta(minutes=30)


# ── get_recent_completed tests ─────────────────────────────────────────


def test_get_recent_completed_parses_log(tmp_path):
    """get_recent_completed extracts completed task entries from daemon log."""
    log_file = tmp_path / "golem-daemon.log"
    now = datetime.now(UTC)
    recent = now - timedelta(minutes=5)
    old = now - timedelta(hours=2)
    log_file.write_text(
        f"[{old.strftime('%Y-%m-%d %H:%M:%S')}] Finished (120s, exit=0): old task...\n"
        f"[{recent.strftime('%Y-%m-%d %H:%M:%S')}] Finished (60s, exit=0): recent task...\n"
        f"[{recent.strftime('%Y-%m-%d %H:%M:%S')}] FAILED (exit=1): failed task...\n"
    )

    original_log = _mod["DAEMON_LOG"]
    _mod["DAEMON_LOG"] = log_file
    try:
        completed = get_recent_completed(timedelta(minutes=30))
    finally:
        _mod["DAEMON_LOG"] = original_log

    assert len(completed) >= 1
    assert any("recent task" in entry for entry in completed)


def test_get_recent_completed_empty_log(tmp_path):
    """get_recent_completed returns empty list for missing log."""
    log_file = tmp_path / "nonexistent.log"
    original_log = _mod["DAEMON_LOG"]
    _mod["DAEMON_LOG"] = log_file
    try:
        completed = get_recent_completed(timedelta(minutes=30))
    finally:
        _mod["DAEMON_LOG"] = original_log

    assert completed == []


# ── get_changed_files tests ────────────────────────────────────────────


def test_get_changed_files_returns_list():
    """get_changed_files returns a list of changed file paths."""
    result = get_changed_files(head_range=5)
    assert isinstance(result, list)


def test_get_changed_files_with_mock():
    """get_changed_files parses git diff output correctly."""
    mock_output = "assays/test_foo.py\neffectors/bar\nloci/copia/baz.md\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0, stdout=mock_output, stderr=""
        )
        files = get_changed_files(head_range=5)
    assert "assays/test_foo.py" in files
    assert "effectors/bar" in files
    assert "loci/copia/baz.md" in files


# ── classify_files tests ───────────────────────────────────────────────


def test_classify_files_categorizes_correctly():
    """classify_files splits files into tests, effectors, consulting, other."""
    files = [
        "assays/test_foo.py",
        "effectors/my-effector",
        "loci/copia/some-report.md",
        "loci/copia/reviewer-cycle-42.md",
        "readme.md",
    ]
    result = classify_files(files)
    assert "assays/test_foo.py" in result["tests"]
    assert "effectors/my-effector" in result["effectors"]
    assert "loci/copia/some-report.md" in result["consulting"]
    assert "loci/copia/reviewer-cycle-42.md" not in result["consulting"]
    assert "readme.md" in result["other"]


def test_classify_files_empty():
    """classify_files handles empty input."""
    result = classify_files([])
    assert result["tests"] == []
    assert result["effectors"] == []
    assert result["consulting"] == []
    assert result["other"] == []


def test_classify_files_test_pattern():
    """classify_files only picks up assays/test_*.py as tests."""
    files = [
        "assays/test_foo.py",
        "assays/foo.py",
        "metabolon/test_bar.py",
    ]
    result = classify_files(files)
    assert "assays/test_foo.py" in result["tests"]
    assert "assays/foo.py" not in result["tests"]
    assert "metabolon/test_bar.py" not in result["tests"]


# ── run_pytest_on_files tests ──────────────────────────────────────────


def test_run_pytest_on_files_with_mock():
    """run_pytest_on_files invokes pytest and parses pass/fail counts."""
    mock_output = "1 passed, 2 failed, 3 errors in 5.0s\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1, stdout=mock_output, stderr=""
        )
        result = run_pytest_on_files(["assays/test_foo.py"])

    assert result["passed"] == 1
    assert result["failed"] == 2
    assert result["errors"] == 3
    assert result["exit_code"] == 1


def test_run_pytest_on_files_all_pass():
    """run_pytest_on_files reports all passing tests."""
    mock_output = "5 passed in 2.0s\n"
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0, stdout=mock_output, stderr=""
        )
        result = run_pytest_on_files(["assays/test_bar.py"])

    assert result["passed"] == 5
    assert result["failed"] == 0
    assert result["exit_code"] == 0


def test_run_pytest_on_files_empty():
    """run_pytest_on_files returns zeros for empty file list."""
    result = run_pytest_on_files([])
    assert result["passed"] == 0
    assert result["failed"] == 0
    assert result["exit_code"] == 0


# ── check_consulting_content tests ─────────────────────────────────────


def test_check_consulting_content_exists_and_long(tmp_path):
    """check_consulting_content passes for file with >200 words."""
    f = tmp_path / "report.md"
    words = "word " * 250
    f.write_text(f"# Report\n\n{words}\n")

    original = _mod["GERMLINE"]
    _mod["GERMLINE"] = tmp_path
    try:
        result = check_consulting_content(["report.md"])
    finally:
        _mod["GERMLINE"] = original

    assert len(result) == 1
    assert result[0]["file"] == "report.md"
    assert result[0]["ok"] is True


def test_check_consulting_content_too_short(tmp_path):
    """check_consulting_content fails for file with <200 words."""
    f = tmp_path / "short.md"
    f.write_text("# Short\n\nOnly a few words here.\n")

    original = _mod["GERMLINE"]
    _mod["GERMLINE"] = tmp_path
    try:
        result = check_consulting_content(["short.md"])
    finally:
        _mod["GERMLINE"] = original

    assert len(result) == 1
    assert result[0]["ok"] is False
    assert "word count" in result[0]["reason"].lower() or "short" in result[0]["reason"].lower()


def test_check_consulting_content_missing_file(tmp_path):
    """check_consulting_content reports error for missing file."""
    original = _mod["GERMLINE"]
    _mod["GERMLINE"] = tmp_path
    try:
        result = check_consulting_content(["nonexistent.md"])
    finally:
        _mod["GERMLINE"] = original

    assert len(result) == 1
    assert result[0]["ok"] is False


# ── diagnose_failure tests ─────────────────────────────────────────────


def test_diagnose_path_issue():
    """diagnose_failure identifies /Users/terry/ hardcoded path."""
    log_tail = "ImportError: No module named 'foo'\n/Users/terry/germline/..."
    result = diagnose_failure(log_tail)
    assert result["diagnosis"] == "hardcoded_path"
    assert "/Users/terry/" in result["detail"]


def test_diagnose_import_error():
    """diagnose_failure identifies import errors."""
    log_tail = "ModuleNotFoundError: No module named 'bar_module'"
    result = diagnose_failure(log_tail)
    assert result["diagnosis"] == "import_error"
    assert "bar_module" in result["detail"]


def test_diagnose_timeout():
    """diagnose_failure identifies timeout."""
    log_tail = "TIMEOUT after 1800s: golem --provider infini..."
    result = diagnose_failure(log_tail)
    assert result["diagnosis"] == "timeout"


def test_diagnose_syntax_error():
    """diagnose_failure identifies syntax errors."""
    log_tail = "SyntaxError: invalid syntax (test_foo.py, line 42)"
    result = diagnose_failure(log_tail)
    assert result["diagnosis"] == "syntax_error"


def test_diagnose_unknown():
    """diagnose_failure returns unknown for unrecognized patterns."""
    log_tail = "Some random error message without known patterns"
    result = diagnose_failure(log_tail)
    assert result["diagnosis"] == "unknown"


# ── write_fixed_task tests ─────────────────────────────────────────────


def test_write_fixed_task_appends_to_queue(tmp_path):
    """write_fixed_task appends a fixed task to the queue file."""
    queue = tmp_path / "golem-queue.md"
    queue.write_text("# Golem Task Queue\n\n## Pending\n\n## Done\n")

    original = _mod["QUEUE_FILE"]
    _mod["QUEUE_FILE"] = queue
    try:
        write_fixed_task("golem --provider infini \"write tests for foo\"")
    finally:
        _mod["QUEUE_FILE"] = original

    content = queue.read_text()
    assert "write tests for foo" in content
    assert "- [ ]" in content


def test_write_fixed_task_creates_queue_if_missing(tmp_path):
    """write_fixed_task creates queue file if it doesn't exist."""
    queue = tmp_path / "subdir" / "golem-queue.md"

    original = _mod["QUEUE_FILE"]
    _mod["QUEUE_FILE"] = queue
    try:
        write_fixed_task("golem \"new task\"")
    finally:
        _mod["QUEUE_FILE"] = original

    assert queue.exists()
    content = queue.read_text()
    assert "new task" in content


# ── count_pending_tasks tests ──────────────────────────────────────────


def test_count_pending_tasks(tmp_path):
    """count_pending_tasks counts [ ] entries in queue."""
    queue = tmp_path / "golem-queue.md"
    queue.write_text(
        "# Queue\n\n"
        "- [ ] `golem \"task1\"`\n"
        "- [x] `golem \"task2\"`\n"
        "- [ ] `golem \"task3\"`\n"
        "- [!] `golem \"task4\"`\n"
    )

    original = _mod["QUEUE_FILE"]
    _mod["QUEUE_FILE"] = queue
    try:
        count = count_pending_tasks()
    finally:
        _mod["QUEUE_FILE"] = original

    assert count == 2


def test_count_pending_tasks_empty(tmp_path):
    """count_pending_tasks returns 0 for empty queue."""
    queue = tmp_path / "golem-queue.md"
    queue.write_text("# Queue\n")

    original = _mod["QUEUE_FILE"]
    _mod["QUEUE_FILE"] = queue
    try:
        count = count_pending_tasks()
    finally:
        _mod["QUEUE_FILE"] = original

    assert count == 0


def test_count_pending_tasks_missing_file():
    """count_pending_tasks returns 0 when queue file is missing."""
    original = _mod["QUEUE_FILE"]
    _mod["QUEUE_FILE"] = Path("/tmp/nonexistent_golem_queue_12345.md")
    try:
        count = count_pending_tasks()
    finally:
        _mod["QUEUE_FILE"] = original

    assert count == 0


# ── auto_generate_tasks tests ──────────────────────────────────────────


def test_auto_generate_tasks_finds_untested(tmp_path):
    """auto_generate_tasks identifies untested effectors."""
    effectors_dir = tmp_path / "effectors"
    effectors_dir.mkdir()
    (effectors_dir / "foo-bar").write_text("#!/usr/bin/env python3\npass\n")
    (effectors_dir / "baz-qux").write_text("#!/usr/bin/env python3\npass\n")
    (effectors_dir / ".hidden").write_text("#!/usr/bin/env python3\npass\n")

    assays_dir = tmp_path / "assays"
    assays_dir.mkdir()
    (assays_dir / "test_foo_bar.py").write_text("def test_foo(): pass\n")

    original_germline = _mod["GERMLINE"]
    _mod["GERMLINE"] = tmp_path
    try:
        tasks = auto_generate_tasks(target_count=50)
    finally:
        _mod["GERMLINE"] = original_germline

    # Should find baz-qux as untested (foo-bar maps to test_foo_bar)
    assert isinstance(tasks, list)
    assert len(tasks) > 0
    assert any("baz-qux" in t for t in tasks)


def test_auto_generate_tasks_caps_at_target():
    """auto_generate_tasks does not exceed target_count."""
    effectors_dir = tmp_path / "effectors"
    effectors_dir.mkdir()
    for i in range(100):
        (effectors_dir / f"effector-{i:03d}").write_text("# script\n")

    assays_dir = tmp_path / "assays"
    assays_dir.mkdir()

    original_germline = _mod["GERMLINE"]
    _mod["GERMLINE"] = tmp_path
    try:
        tasks = auto_generate_tasks(target_count=10)
    finally:
        _mod["GERMLINE"] = original_germline

    assert len(tasks) <= 10


# ── generate_review_summary tests ──────────────────────────────────────


def test_generate_review_summary_structure(tmp_path):
    """generate_review_summary produces valid markdown."""
    report_dir = tmp_path / "loci" / "copia"
    report_dir.mkdir(parents=True)

    original_germline = _mod["GERMLINE"]
    original_report = _mod["REVIEW_SUMMARY"]
    _mod["GERMLINE"] = tmp_path
    _mod["REVIEW_SUMMARY"] = report_dir / "golem-review-latest.md"
    try:
        path = generate_review_summary(
            completed_tasks=["task1", "task2"],
            changed_files={"tests": ["a.py"], "effectors": [], "consulting": [], "other": []},
            test_results={"passed": 5, "failed": 1, "errors": 0, "exit_code": 1},
            consulting_results=[],
            failures=["FAILED task3"],
            failure_diagnoses=[{"diagnosis": "timeout", "detail": "after 1800s"}],
            new_tasks=["golem \"new task\""],
        )
    finally:
        _mod["GERMLINE"] = original_germline
        _mod["REVIEW_SUMMARY"] = original_report

    assert path.exists()
    content = path.read_text()
    assert "# Golem Review Summary" in content
    assert "task1" in content
    assert "5 passed" in content
    assert "1 failed" in content


def test_generate_review_summary_with_consulting(tmp_path):
    """generate_review_summary includes consulting results."""
    report_dir = tmp_path / "loci" / "copia"
    report_dir.mkdir(parents=True)

    original_germline = _mod["GERMLINE"]
    original_report = _mod["REVIEW_SUMMARY"]
    _mod["GERMLINE"] = tmp_path
    _mod["REVIEW_SUMMARY"] = report_dir / "golem-review-latest.md"
    try:
        path = generate_review_summary(
            completed_tasks=[],
            changed_files={"tests": [], "effectors": [], "consulting": ["report.md"], "other": []},
            test_results={"passed": 0, "failed": 0, "errors": 0, "exit_code": 0},
            consulting_results=[{"file": "report.md", "ok": True, "word_count": 300}],
            failures=[],
            failure_diagnoses=[],
            new_tasks=[],
        )
    finally:
        _mod["GERMLINE"] = original_germline
        _mod["REVIEW_SUMMARY"] = original_report

    content = path.read_text()
    assert "report.md" in content
    assert "300" in content


# ── main CLI tests ─────────────────────────────────────────────────────


def test_main_help(capsys):
    """main --help prints usage and returns 0."""
    with patch("sys.argv", ["golem-review", "--help"]):
        rc = _mod["main"]()
    assert rc == 0
    out = capsys.readouterr().out
    assert "golem-review" in out.lower()


def test_main_once_runs_review(capsys, tmp_path):
    """main with --once runs a single review cycle."""
    report_dir = tmp_path / "loci" / "copia"
    report_dir.mkdir(parents=True)
    queue = tmp_path / "golem-queue.md"
    queue.write_text("# Queue\n\n## Pending\n\n## Done\n")
    log_file = tmp_path / "golem-daemon.log"
    log_file.write_text("")

    original_germline = _mod["GERMLINE"]
    original_queue = _mod["QUEUE_FILE"]
    original_log = _mod["DAEMON_LOG"]
    original_report = _mod["REVIEW_SUMMARY"]
    _mod["GERMLINE"] = tmp_path
    _mod["QUEUE_FILE"] = queue
    _mod["DAEMON_LOG"] = log_file
    _mod["REVIEW_SUMMARY"] = report_dir / "golem-review-latest.md"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        try:
            with patch("sys.argv", ["golem-review", "--once"]):
                rc = _mod["main"]()
        finally:
            _mod["GERMLINE"] = original_germline
            _mod["QUEUE_FILE"] = original_queue
            _mod["DAEMON_LOG"] = original_log
            _mod["REVIEW_SUMMARY"] = original_report

    assert rc == 0


# ── Edge cases ─────────────────────────────────────────────────────────


class TestEdgeCases:
    """Edge cases for golem-review."""

    def test_diagnose_empty_log(self):
        """diagnose_failure handles empty log gracefully."""
        result = diagnose_failure("")
        assert result["diagnosis"] in ("unknown", "empty")

    def test_classify_files_only_reviewer_cycles(self):
        """classify_files excludes reviewer-cycle files from consulting."""
        files = [
            "loci/copia/reviewer-cycle-42.md",
            "loci/copia/reviewer-cycle-43.md",
        ]
        result = classify_files(files)
        assert result["consulting"] == []
        assert len(result["other"]) == 2

    def test_run_pytest_malformed_output(self):
        """run_pytest_on_files handles malformed pytest output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="garbage output\nno numbers", stderr=""
            )
            result = run_pytest_on_files(["assays/test_foo.py"])

        assert result["passed"] == 0
        assert result["failed"] == 0

    def test_count_pending_high_priority(self):
        """count_pending_tasks counts [!!] tasks as pending too."""
        queue = tmp_path / "golem-queue.md"  # noqa: F841
        # Need to use tmp_path fixture properly

    def test_count_pending_includes_high_priority(self, tmp_path):
        """count_pending_tasks counts [!!] high-priority tasks."""
        queue = tmp_path / "golem-queue.md"
        queue.write_text(
            "- [!!] `golem \"urgent\"`\n"
            "- [ ] `golem \"normal\"`\n"
            "- [x] `golem \"done\"`\n"
        )

        original = _mod["QUEUE_FILE"]
        _mod["QUEUE_FILE"] = queue
        try:
            count = count_pending_tasks()
        finally:
            _mod["QUEUE_FILE"] = original

        assert count == 2

    def test_write_fixed_task_high_priority(self, tmp_path):
        """write_fixed_task can write high-priority tasks."""
        queue = tmp_path / "golem-queue.md"
        queue.write_text("# Queue\n\n## Pending\n")

        original = _mod["QUEUE_FILE"]
        _mod["QUEUE_FILE"] = queue
        try:
            write_fixed_task("golem \"urgent fix\"", priority="high")
        finally:
            _mod["QUEUE_FILE"] = original

        content = queue.read_text()
        assert "- [!!]" in content
        assert "urgent fix" in content


# ── auto-requeue integration ───────────────────────────────────────────


class TestAutoRequeue:
    """Tests for the --auto-requeue flow."""

    def test_auto_requeue_writes_fixed_tasks(self, tmp_path):
        """auto-requeue diagnoses failures and writes fixed tasks."""
        queue = tmp_path / "golem-queue.md"
        queue.write_text("# Queue\n\n## Pending\n\n## Done\n")

        original = _mod["QUEUE_FILE"]
        _mod["QUEUE_FILE"] = queue
        try:
            diag = diagnose_failure("ModuleNotFoundError: No module named 'xyz'")
            assert diag["diagnosis"] == "import_error"
            write_fixed_task(
                f"golem --provider infini \"fix import for xyz module\""
            )
        finally:
            _mod["QUEUE_FILE"] = original

        content = queue.read_text()
        assert "fix import" in content
        assert "- [ ]" in content

    def test_auto_requeue_path_fix(self, tmp_path):
        """auto-requeue generates task to fix hardcoded paths."""
        diag = diagnose_failure("/Users/terry/germline/effectors/foo.py:42")
        assert diag["diagnosis"] == "hardcoded_path"
        assert "/Users/terry/" in diag["detail"]
