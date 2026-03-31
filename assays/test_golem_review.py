"""Tests for golem-review — meta-golem that reviews golem output and queues work."""
from __future__ import annotations

import os
import re
import textwrap
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_golem_review():
    """Load the golem-review module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/golem-review").read()
    ns: dict = {"__name__": "golem_review_test"}
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


# ── parse_since tests ──────────────────────────────────────────────────


def test_parse_since_minutes():
    """parse_since parses '30m' as 30 minutes."""
    assert parse_since("30m") == timedelta(minutes=30)


def test_parse_since_hours():
    """parse_since parses '1h' as 1 hour."""
    assert parse_since("1h") == timedelta(hours=1)


def test_parse_since_seconds():
    """parse_since parses '60s' as 60 seconds."""
    assert parse_since("60s") == timedelta(seconds=60)


def test_parse_since_days():
    """parse_since parses '2d' as 2 days."""
    assert parse_since("2d") == timedelta(days=2)


def test_parse_since_bare_number_defaults_to_minutes():
    """parse_since treats bare number as minutes."""
    assert parse_since("45") == timedelta(minutes=45)


def test_parse_since_invalid_returns_default():
    """parse_since returns 30 minutes for invalid input."""
    assert parse_since("abc") == timedelta(minutes=30)


def test_parse_since_whitespace_trimmed():
    """parse_since trims whitespace."""
    assert parse_since("  15m  ") == timedelta(minutes=15)


# ── parse_log_timestamp tests ──────────────────────────────────────────


def test_parse_log_timestamp_valid():
    """parse_log_timestamp parses standard format."""
    dt = parse_log_timestamp("2026-03-31 10:53:29")
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 3
    assert dt.day == 31
    assert dt.hour == 10


def test_parse_log_timestamp_invalid():
    """parse_log_timestamp returns None for invalid format."""
    assert parse_log_timestamp("not a timestamp") is None


def test_parse_log_timestamp_none():
    """parse_log_timestamp returns None for None input."""
    assert parse_log_timestamp(None) is None


# ── scan_log tests ─────────────────────────────────────────────────────


def test_scan_log_missing_file(tmp_path):
    """scan_log returns empty lists when log file doesn't exist."""
    _mod["LOGFILE"] = tmp_path / "nonexistent.log"
    try:
        result = scan_log(timedelta(minutes=30))
    finally:
        _mod["LOGFILE"] = _mod.get("_orig_LOGFILE", Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log")

    assert result["completed"] == []
    assert result["failed"] == []
    assert result["timeouts"] == []


def test_scan_log_parses_completed(tmp_path):
    """scan_log detects completed tasks (exit=0)."""
    log_file = tmp_path / "golem-daemon.log"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file.write_text(
        f"[{now}] Finished (120s, exit=0): golem --provider infini \"write tests\"\n"
    )
    _mod["LOGFILE"] = log_file
    try:
        result = scan_log(timedelta(minutes=30))
    finally:
        _mod["LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log"

    assert len(result["completed"]) == 1
    assert "write tests" in result["completed"][0][1]


def test_scan_log_parses_failed(tmp_path):
    """scan_log detects failed tasks (exit!=0)."""
    log_file = tmp_path / "golem-daemon.log"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file.write_text(
        f"[{now}] FAILED (exit=1): golem --provider infini \"broken task\"\n"
    )
    _mod["LOGFILE"] = log_file
    try:
        result = scan_log(timedelta(minutes=30))
    finally:
        _mod["LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log"

    assert len(result["failed"]) == 1
    assert "broken task" in result["failed"][0][1]


def test_scan_log_parses_timeouts(tmp_path):
    """scan_log detects timeout tasks."""
    log_file = tmp_path / "golem-daemon.log"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file.write_text(
        f"[{now}] TIMEOUT (1800s): golem --provider volcano \"slow task\"\n"
    )
    _mod["LOGFILE"] = log_file
    try:
        result = scan_log(timedelta(minutes=30))
    finally:
        _mod["LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log"

    assert len(result["timeouts"]) == 1
    assert "slow task" in result["timeouts"][0][1]


def test_scan_log_ignores_old_entries(tmp_path):
    """scan_log skips entries older than the since window."""
    log_file = tmp_path / "golem-daemon.log"
    old_ts = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    log_file.write_text(
        f"[{old_ts}] Finished (10s, exit=0): golem \"old task\"\n"
    )
    _mod["LOGFILE"] = log_file
    try:
        result = scan_log(timedelta(minutes=30))
    finally:
        _mod["LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log"

    assert result["completed"] == []


def test_scan_log_mixed_entries(tmp_path):
    """scan_log handles a mix of completed, failed, and timeout entries."""
    log_file = tmp_path / "golem-daemon.log"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file.write_text(
        f"[{now}] Finished (60s, exit=0): golem \"task A\"\n"
        f"[{now}] FAILED (exit=1): golem \"task B\"\n"
        f"[{now}] TIMEOUT (1800s): golem \"task C\"\n"
        f"[{now}] Starting: golem \"task D\"\n"
        f"[{now}] Idle: 5 pending\n"
    )
    _mod["LOGFILE"] = log_file
    try:
        result = scan_log(timedelta(minutes=30))
    finally:
        _mod["LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log"

    assert len(result["completed"]) == 1
    assert len(result["failed"]) == 1
    assert len(result["timeouts"]) == 1


def test_scan_log_unreadable_file(tmp_path):
    """scan_log returns empty when log file exists but is unreadable."""
    log_file = tmp_path / "golem-daemon.log"
    log_file.write_text("[2026-03-31 10:00:00] Finished (1s, exit=0): golem\n")
    log_file.chmod(0o000)
    _mod["LOGFILE"] = log_file
    try:
        result = scan_log(timedelta(minutes=30))
    finally:
        _mod["LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log"
        log_file.chmod(0o644)

    assert result["completed"] == []


# ── diagnose_failure tests ─────────────────────────────────────────────


def test_diagnose_path_issue():
    """diagnose_failure detects hardcoded /Users/terry/ paths."""
    result = diagnose_failure("golem /Users/terry/germline", "")
    assert "path_issue" in result


def test_diagnose_import_error():
    """diagnose_failure detects ImportError."""
    result = diagnose_failure("golem task", "ImportError: no module")
    assert "import_error" in result


def test_diagnose_timeout():
    """diagnose_failure detects timeout."""
    result = diagnose_failure("golem timeout task", "")
    assert "timeout" in result


def test_diagnose_syntax_error():
    """diagnose_failure detects SyntaxError."""
    result = diagnose_failure("golem task", "SyntaxError: invalid")
    assert "syntax_error" in result


def test_diagnose_permission_error():
    """diagnose_failure detects PermissionError."""
    result = diagnose_failure("golem task", "PermissionError: denied")
    assert "permission_error" in result


def test_diagnose_assertion_error():
    """diagnose_failure detects AssertionError."""
    result = diagnose_failure("golem task", "AssertionError: wrong")
    assert "assertion_error" in result


def test_diagnose_command_error():
    """diagnose_failure detects exit=2 command errors."""
    result = diagnose_failure("exit=2 golem task", "")
    assert "command_error" in result


def test_diagnose_unknown():
    """diagnose_failure returns unknown for unrecognized patterns."""
    result = diagnose_failure("golem task", "some random output")
    assert "unknown" in result


def test_diagnose_path_issue_windows():
    """diagnose_failure detects Windows-style paths."""
    result = diagnose_failure('golem task', 'C:\\Users\\terry\\file')
    assert "path_issue" in result


def test_diagnose_module_not_found():
    """diagnose_failure detects ModuleNotFoundError."""
    result = diagnose_failure("golem task", "ModuleNotFoundError: lacuna")
    assert "import_error" in result


# ── check_consulting_content tests ─────────────────────────────────────


def test_check_consulting_content_exists_and_adequate(tmp_path, monkeypatch):
    """check_consulting_content reports adequate for files with >200 words."""
    monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
    _mod["GERMLINE"] = tmp_path / "germline"
    copia_dir = _mod["GERMLINE"] / "loci" / "copia"
    copia_dir.mkdir(parents=True)
    (copia_dir / "brief.md").write_text("word " * 250)

    result = check_consulting_content(["loci/copia/brief.md"])
    assert len(result) == 1
    assert result[0]["exists"] is True
    assert result[0]["adequate"] is True
    assert result[0]["word_count"] >= 200


def test_check_consulting_content_too_short(tmp_path, monkeypatch):
    """check_consulting_content reports inadequate for files with <=200 words."""
    monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
    _mod["GERMLINE"] = tmp_path / "germline"
    copia_dir = _mod["GERMLINE"] / "loci" / "copia"
    copia_dir.mkdir(parents=True)
    (copia_dir / "short.md").write_text("only a few words")

    result = check_consulting_content(["loci/copia/short.md"])
    assert len(result) == 1
    assert result[0]["exists"] is True
    assert result[0]["adequate"] is False


def test_check_consulting_content_missing_file(tmp_path, monkeypatch):
    """check_consulting_content reports missing for nonexistent files."""
    monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
    _mod["GERMLINE"] = tmp_path / "germline"

    result = check_consulting_content(["loci/copia/nonexistent.md"])
    assert len(result) == 1
    assert result[0]["exists"] is False
    assert result[0]["adequate"] is False


def test_check_consulting_content_empty_list(tmp_path, monkeypatch):
    """check_consulting_content returns empty list for no files."""
    result = check_consulting_content([])
    assert result == []


# ── run_pytest_on_files tests ──────────────────────────────────────────


def test_run_pytest_on_files_empty():
    """run_pytest_on_files returns zeros when no files given."""
    result = run_pytest_on_files([])
    assert result["total_passed"] == 0
    assert result["total_failed"] == 0
    assert result["total_errors"] == 0
    assert result["files"] == []


def test_run_pytest_on_files_parses_output():
    """run_pytest_on_files parses pytest output for pass/fail counts."""
    def mock_run(cmd, shell, capture_output, text, timeout=None, cwd=None):
        r = MagicMock()
        r.stdout = "3 passed, 1 failed\n"
        r.stderr = ""
        r.returncode = 1
        return r

    with patch("subprocess.run", side_effect=mock_run):
        result = run_pytest_on_files(["assays/test_example.py"])

    assert result["total_passed"] == 3
    assert result["total_failed"] == 1
    assert result["total_errors"] == 0
    assert len(result["files"]) == 1


def test_run_pytest_on_files_timeout():
    """run_pytest_on_files handles timeout gracefully."""
    def mock_run_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("cmd", 120)

    with patch("subprocess.run", side_effect=mock_run_timeout):
        result = run_pytest_on_files(["assays/test_slow.py"])

    assert result["total_errors"] == 1
    assert len(result["files"]) == 1
    assert result["files"][0][0] == "assays/test_slow.py"


def test_run_pytest_on_files_errors():
    """run_pytest_on_files parses error counts."""
    def mock_run(cmd, shell, capture_output, text, timeout=None, cwd=None):
        r = MagicMock()
        r.stdout = "0 passed, 2 errors\n"
        r.stderr = ""
        r.returncode = 1
        return r

    with patch("subprocess.run", side_effect=mock_run):
        result = run_pytest_on_files(["assays/test_broken.py"])

    assert result["total_errors"] == 2


# ── count_pending_tasks tests ──────────────────────────────────────────


def test_count_pending_tasks_counts_correctly(tmp_path):
    """count_pending_tasks counts [ ] and [!!] but not [x] or [!]."""
    queue_file = tmp_path / "golem-queue.md"
    queue_file.write_text(
        "- [ ] `golem \"task1\"`\n"
        "- [!!] `golem \"urgent\"`\n"
        "- [x] `golem \"done\"`\n"
        "- [!] `golem \"failed\"`\n"
        "- [ ] `golem \"task2\"`\n"
    )
    _mod["QUEUE_FILE"] = queue_file
    try:
        count = count_pending_tasks()
    finally:
        _mod["QUEUE_FILE"] = Path.home() / "germline" / "loci" / "golem-queue.md"

    assert count == 3  # [ ] + [!!] + [ ]


def test_count_pending_tasks_missing_file(tmp_path):
    """count_pending_tasks returns 0 when queue file missing."""
    _mod["QUEUE_FILE"] = tmp_path / "nonexistent.md"
    try:
        count = count_pending_tasks()
    finally:
        _mod["QUEUE_FILE"] = Path.home() / "germline" / "loci" / "golem-queue.md"

    assert count == 0


def test_count_pending_tasks_empty_file(tmp_path):
    """count_pending_tasks returns 0 for empty queue."""
    queue_file = tmp_path / "golem-queue.md"
    queue_file.write_text("")
    _mod["QUEUE_FILE"] = queue_file
    try:
        count = count_pending_tasks()
    finally:
        _mod["QUEUE_FILE"] = Path.home() / "germline" / "loci" / "golem-queue.md"

    assert count == 0


# ── generate_queue_tasks tests ─────────────────────────────────────────


def test_generate_queue_tasks_basic():
    """generate_queue_tasks creates properly formatted task lines."""
    tasks = generate_queue_tasks(["my-module", "another"], 2)
    assert len(tasks) == 2
    assert tasks[0].startswith("- [ ] `golem")
    assert "my-module" in tasks[0]
    assert "another" in tasks[1]


def test_generate_queue_tasks_limits_count():
    """generate_queue_tasks respects the count limit."""
    tasks = generate_queue_tasks(["a", "b", "c", "d", "e"], 3)
    assert len(tasks) == 3


def test_generate_queue_tasks_empty():
    """generate_queue_tasks returns empty list for no modules."""
    tasks = generate_queue_tasks([], 10)
    assert tasks == []


def test_generate_queue_tasks_provider_rotation():
    """generate_queue_tasks rotates providers across tasks."""
    tasks = generate_queue_tasks(["a", "b", "c", "d"], 4)
    providers = []
    for t in tasks:
        m = re.search(r'--provider (\w+)', t)
        if m:
            providers.append(m.group(1))
    # Should cycle through providers
    assert len(set(providers)) > 1


# ── append_tasks_to_queue tests ────────────────────────────────────────


def test_append_tasks_to_queue(tmp_path):
    """append_tasks_to_queue appends tasks to queue file."""
    queue_file = tmp_path / "golem-queue.md"
    queue_file.write_text("# Existing Queue\n\n- [ ] `golem \"old task\"`\n")
    _mod["QUEUE_FILE"] = queue_file
    _mod["COPIA_DIR"] = tmp_path
    try:
        count = append_tasks_to_queue(['- [ ] `golem \"new task\"`'])
    finally:
        _mod["QUEUE_FILE"] = Path.home() / "germline" / "loci" / "golem-queue.md"

    assert count == 1
    content = queue_file.read_text()
    assert "old task" in content
    assert "new task" in content


def test_append_tasks_to_queue_empty(tmp_path):
    """append_tasks_to_queue returns 0 for empty task list."""
    queue_file = tmp_path / "golem-queue.md"
    queue_file.write_text("# Queue\n")
    _mod["QUEUE_FILE"] = queue_file
    try:
        count = append_tasks_to_queue([])
    finally:
        _mod["QUEUE_FILE"] = Path.home() / "germline" / "loci" / "golem-queue.md"

    assert count == 0


def test_append_tasks_creates_file(tmp_path):
    """append_tasks_to_queue creates queue file if it doesn't exist."""
    queue_file = tmp_path / "new-queue.md"
    _mod["QUEUE_FILE"] = queue_file
    _mod["COPIA_DIR"] = tmp_path
    try:
        count = append_tasks_to_queue(['- [ ] `golem \"task\"`'])
    finally:
        _mod["QUEUE_FILE"] = Path.home() / "germline" / "loci" / "golem-queue.md"

    assert count == 1
    assert queue_file.exists()


# ── write_fixed_tasks tests ────────────────────────────────────────────


def test_write_fixed_tasks(tmp_path):
    """write_fixed_tasks appends diagnosed tasks with fix hints."""
    queue_file = tmp_path / "golem-queue.md"
    queue_file.write_text("# Queue\n")
    _mod["QUEUE_FILE"] = queue_file
    try:
        count = write_fixed_tasks([
            {"cmd": 'golem --provider infini "write tests for foo"', "diagnosis": "path_issue: hardcoded paths"},
            {"cmd": 'golem --provider volcano "fix bar"', "diagnosis": "import_error: bad import"},
        ])
    finally:
        _mod["QUEUE_FILE"] = Path.home() / "germline" / "loci" / "golem-queue.md"

    assert count == 2
    content = queue_file.read_text()
    assert "Path.home()" in content
    assert "exec(open" in content


def test_write_fixed_tasks_empty(tmp_path):
    """write_fixed_tasks returns 0 for empty task list."""
    queue_file = tmp_path / "golem-queue.md"
    queue_file.write_text("# Queue\n")
    _mod["QUEUE_FILE"] = queue_file
    try:
        count = write_fixed_tasks([])
    finally:
        _mod["QUEUE_FILE"] = Path.home() / "germline" / "loci" / "golem-queue.md"

    assert count == 0


def test_write_fixed_tasks_timeout_hint(tmp_path):
    """write_fixed_tasks adds simplification hint for timeout diagnoses."""
    queue_file = tmp_path / "golem-queue.md"
    queue_file.write_text("# Queue\n")
    _mod["QUEUE_FILE"] = queue_file
    try:
        count = write_fixed_tasks([
            {"cmd": 'golem "slow task"', "diagnosis": "timeout: too slow"},
        ])
    finally:
        _mod["QUEUE_FILE"] = Path.home() / "germline" / "loci" / "golem-queue.md"

    assert count == 1
    content = queue_file.read_text()
    assert "simple" in content.lower()


# ── generate_review tests ──────────────────────────────────────────────


def test_generate_review_basic():
    """generate_review produces markdown with expected sections."""
    activity = {
        "completed": [(datetime.now(), "golem task A")],
        "failed": [(datetime.now(), "golem task B", "some error")],
        "timeouts": [],
        "start_time": datetime.now() - timedelta(minutes=30),
    }
    review = generate_review(
        activity=activity,
        recent_files=["assays/test_foo.py"],
        test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
        consulting_results=[],
        failed_diagnoses=[{"cmd": "golem task B", "diagnosis": "unknown: check log"}],
        pending_count=5,
        auto_requeue=False,
        queued_count=0,
        fixed_count=0,
    )
    assert "# Golem Review" in review
    assert "Activity Summary" in review
    assert "Completed Tasks" in review
    assert "Failed Tasks" in review
    assert "pending tasks in queue" in review.lower() or "Pending" in review


def test_generate_review_with_test_results():
    """generate_review includes test results table."""
    activity = {
        "completed": [], "failed": [], "timeouts": [], "start_time": None,
    }
    test_results = {
        "files": [("assays/test_foo.py", 5, 1, 0)],
        "total_passed": 5,
        "total_failed": 1,
        "total_errors": 0,
    }
    review = generate_review(
        activity=activity,
        recent_files=[],
        test_results=test_results,
        consulting_results=[],
        failed_diagnoses=[],
        pending_count=0,
        auto_requeue=False,
        queued_count=0,
        fixed_count=0,
    )
    assert "Test Results" in review
    assert "test_foo.py" in review
    assert "5" in review


def test_generate_review_with_consulting():
    """generate_review includes consulting content checks."""
    activity = {
        "completed": [], "failed": [], "timeouts": [], "start_time": None,
    }
    consulting = [{"file": "brief.md", "exists": True, "word_count": 350, "adequate": True}]
    review = generate_review(
        activity=activity,
        recent_files=["brief.md"],
        test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
        consulting_results=consulting,
        failed_diagnoses=[],
        pending_count=0,
        auto_requeue=False,
        queued_count=0,
        fixed_count=0,
    )
    assert "Consulting Content" in review
    assert "brief.md" in review
    assert "350" in review


def test_generate_review_auto_requeue_section():
    """generate_review includes auto-requeue section when enabled."""
    activity = {
        "completed": [], "failed": [], "timeouts": [], "start_time": None,
    }
    review = generate_review(
        activity=activity,
        recent_files=[],
        test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
        consulting_results=[],
        failed_diagnoses=[],
        pending_count=10,
        auto_requeue=True,
        queued_count=40,
        fixed_count=2,
    )
    assert "Auto-Requeue" in review
    assert "40" in review
    assert "2" in review


def test_generate_review_timeouts():
    """generate_review includes timeout details."""
    activity = {
        "completed": [],
        "failed": [],
        "timeouts": [(datetime.now(), "golem slow task")],
        "start_time": None,
    }
    review = generate_review(
        activity=activity,
        recent_files=[],
        test_results={"files": [], "total_passed": 0, "total_failed": 0, "total_errors": 0},
        consulting_results=[],
        failed_diagnoses=[],
        pending_count=0,
        auto_requeue=False,
        queued_count=0,
        fixed_count=0,
    )
    assert "Timeouts" in review
    assert "slow task" in review


# ── find_untested_modules tests ────────────────────────────────────────


def test_find_untested_modules(tmp_path, monkeypatch):
    """find_untested_modules identifies effectors without tests."""
    monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
    _mod["GERMLINE"] = tmp_path / "germline"
    _mod["EFFECTORS_DIR"] = tmp_path / "germline" / "effectors"
    _mod["ASSAYS_DIR"] = tmp_path / "germline" / "assays"
    _mod["EFFECTORS_DIR"].mkdir(parents=True)
    _mod["ASSAYS_DIR"].mkdir(parents=True)

    # Create effectors
    (_mod["EFFECTORS_DIR"] / "alpha").write_text("# alpha")
    (_mod["EFFECTORS_DIR"] / "beta").write_text("# beta")
    (_mod["EFFECTORS_DIR"] / "gamma").write_text("# gamma")

    # Create test for alpha only
    (_mod["ASSAYS_DIR"] / "test_alpha.py").write_text("def test_alpha(): pass")

    try:
        untested = find_untested_modules()
    finally:
        _mod["GERMLINE"] = Path.home() / "germline"
        _mod["EFFECTORS_DIR"] = Path.home() / "germline" / "effectors"
        _mod["ASSAYS_DIR"] = Path.home() / "germline" / "assays"

    assert "alpha" not in untested
    assert "beta" in untested
    assert "gamma" in untested


def test_find_untested_modules_empty_dirs(tmp_path, monkeypatch):
    """find_untested_modules returns empty when no effectors exist."""
    monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
    _mod["EFFECTORS_DIR"] = tmp_path / "effectors"
    _mod["ASSAYS_DIR"] = tmp_path / "assays"
    _mod["EFFECTORS_DIR"].mkdir(parents=True)
    _mod["ASSAYS_DIR"].mkdir(parents=True)

    try:
        untested = find_untested_modules()
    finally:
        _mod["EFFECTORS_DIR"] = Path.home() / "germline" / "effectors"
        _mod["ASSAYS_DIR"] = Path.home() / "germline" / "assays"

    assert untested == []


# ── run_review integration tests ───────────────────────────────────────


def test_run_review_basic(tmp_path, monkeypatch, capsys):
    """run_review produces output and writes review file."""
    monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
    _mod["GERMLINE"] = tmp_path / "germline"
    _mod["LOGFILE"] = tmp_path / "golem-daemon.log"
    _mod["REVIEW_FILE"] = tmp_path / "golem-review-latest.md"
    _mod["COPIA_DIR"] = tmp_path
    _mod["QUEUE_FILE"] = tmp_path / "golem-queue.md"
    _mod["EFFECTORS_DIR"] = tmp_path / "effectors"
    _mod["ASSAYS_DIR"] = tmp_path / "assays"

    # Create minimal files
    _mod["LOGFILE"].parent.mkdir(parents=True, exist_ok=True)
    _mod["LOGFILE"].write_text("")
    _mod["QUEUE_FILE"].parent.mkdir(parents=True, exist_ok=True)
    _mod["QUEUE_FILE"].write_text("# Queue\n")
    _mod["EFFECTORS_DIR"].mkdir(parents=True, exist_ok=True)
    _mod["ASSAYS_DIR"].mkdir(parents=True, exist_ok=True)

    try:
        rc = run_review(auto_requeue=False, since=timedelta(minutes=30))
    finally:
        _mod["GERMLINE"] = Path.home() / "germline"
        _mod["LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log"
        _mod["REVIEW_FILE"] = Path.home() / "germline" / "loci" / "copia" / "golem-review-latest.md"
        _mod["COPIA_DIR"] = Path.home() / "germline" / "loci" / "copia"
        _mod["QUEUE_FILE"] = Path.home() / "germline" / "loci" / "golem-queue.md"
        _mod["EFFECTORS_DIR"] = Path.home() / "germline" / "effectors"
        _mod["ASSAYS_DIR"] = Path.home() / "germline" / "assays"

    assert rc == 0
    assert _mod["REVIEW_FILE"].exists()
    output = capsys.readouterr().out
    assert "Golem Review" in output


def test_run_review_with_auto_requeue(tmp_path, monkeypatch, capsys):
    """run_review with auto_requeue tops up the queue when <50 pending."""
    monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
    _mod["GERMLINE"] = tmp_path / "germline"
    _mod["LOGFILE"] = tmp_path / "golem-daemon.log"
    _mod["REVIEW_FILE"] = tmp_path / "golem-review-latest.md"
    _mod["COPIA_DIR"] = tmp_path
    _mod["QUEUE_FILE"] = tmp_path / "golem-queue.md"
    _mod["EFFECTORS_DIR"] = tmp_path / "effectors"
    _mod["ASSAYS_DIR"] = tmp_path / "assays"

    _mod["LOGFILE"].parent.mkdir(parents=True, exist_ok=True)
    _mod["LOGFILE"].write_text("")
    _mod["QUEUE_FILE"].parent.mkdir(parents=True, exist_ok=True)
    _mod["QUEUE_FILE"].write_text("# Queue\n")
    _mod["EFFECTORS_DIR"].mkdir(parents=True, exist_ok=True)
    _mod["ASSAYS_DIR"].mkdir(parents=True, exist_ok=True)

    # Create many untested effectors
    for i in range(5):
        (_mod["EFFECTORS_DIR"] / f"module-{i}").write_text(f"# module {i}")

    try:
        rc = run_review(auto_requeue=True, since=timedelta(minutes=30))
    finally:
        _mod["GERMLINE"] = Path.home() / "germline"
        _mod["LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log"
        _mod["REVIEW_FILE"] = Path.home() / "germline" / "loci" / "copia" / "golem-review-latest.md"
        _mod["COPIA_DIR"] = Path.home() / "germline" / "loci" / "copia"
        _mod["QUEUE_FILE"] = Path.home() / "germline" / "loci" / "golem-queue.md"
        _mod["EFFECTORS_DIR"] = Path.home() / "germline" / "effectors"
        _mod["ASSAYS_DIR"] = Path.home() / "germline" / "assays"

    assert rc == 0
    content = _mod["QUEUE_FILE"].read_text()
    assert "Auto-queued" in content


# ── read_log_tail tests ────────────────────────────────────────────────


def test_read_log_tail(tmp_path):
    """read_log_tail returns last N lines of log."""
    log_file = tmp_path / "golem-daemon.log"
    lines = [f"[2026-03-31 10:00:{i:02d}] line {i}" for i in range(10)]
    log_file.write_text("\n".join(lines))
    _mod["LOGFILE"] = log_file
    try:
        tail = read_log_tail(3)
    finally:
        _mod["LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log"

    assert "line 7" in tail
    assert "line 9" in tail
    assert "line 0" not in tail


def test_read_log_tail_missing_file(tmp_path):
    """read_log_tail returns empty string for missing file."""
    _mod["LOGFILE"] = tmp_path / "nonexistent.log"
    try:
        tail = read_log_tail()
    finally:
        _mod["LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log"

    assert tail == ""


# ── get_recent_files tests ─────────────────────────────────────────────


def test_get_recent_files_mocked():
    """get_recent_files returns file list from git diff."""
    def mock_run(cmd, shell, capture_output, text, timeout=None):
        r = MagicMock()
        if "diff --name-only" in cmd:
            r.returncode = 0
            r.stdout = "assays/test_new.py\neffectors/new_effector\n"
        else:
            r.returncode = 0
            r.stdout = ""
        return r

    with patch("subprocess.run", side_effect=mock_run):
        files = get_recent_files(n=5)

    assert "assays/test_new.py" in files
    assert "effectors/new_effector" in files


def test_get_recent_files_git_fails():
    """get_recent_files returns empty list when git fails."""
    def mock_run(cmd, shell, capture_output, text, timeout=None):
        r = MagicMock()
        r.returncode = 1
        r.stdout = ""
        return r

    with patch("subprocess.run", side_effect=mock_run):
        files = get_recent_files(n=5)

    assert files == []


def test_get_recent_files_exception():
    """get_recent_files returns empty list on exception."""
    def mock_run(*args, **kwargs):
        raise RuntimeError("git broken")

    with patch("subprocess.run", side_effect=mock_run):
        files = get_recent_files(n=5)

    assert files == []


# ── Edge case: completed task with exit code in Finished line ──────────


def test_scan_log_finished_nonzero_exit(tmp_path):
    """scan_log detects non-zero exit from Finished line (not just FAILED)."""
    log_file = tmp_path / "golem-daemon.log"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file.write_text(
        f"[{now}] Finished (5s, exit=1): golem --provider volcano \"task X\"\n"
    )
    _mod["LOGFILE"] = log_file
    try:
        result = scan_log(timedelta(minutes=30))
    finally:
        _mod["LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log"

    assert len(result["failed"]) == 1
    assert "task X" in result["failed"][0][1]
    assert len(result["completed"]) == 0


# ── Edge case: binary/corrupt log file ─────────────────────────────────


def test_scan_log_binary_content(tmp_path):
    """scan_log handles binary content in log file."""
    log_file = tmp_path / "golem-daemon.log"
    log_file.write_bytes(b"\x00\x01\x02\xff\xfe\xfd")
    _mod["LOGFILE"] = log_file
    try:
        result = scan_log(timedelta(minutes=30))
    finally:
        _mod["LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log"

    assert result["completed"] == []
    assert result["failed"] == []
