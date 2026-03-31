"""Tests for golem-review — meta-golem that reviews golem output and queues work."""
from __future__ import annotations

import subprocess
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

# Extract current public functions
parse_since_arg = _mod["parse_since_arg"]
parse_log_timestamp = _mod["parse_log_timestamp"]
parse_completed_tasks = _mod["parse_completed_tasks"]
check_file_exists = _mod["check_file_exists"]
count_words = _mod["count_words"]
run_pytest_on_file = _mod["run_pytest_on_file"]
diagnose_failure = _mod["diagnose_failure"]
build_review_summary = _mod["build_review_summary"]
count_pending_tasks = _mod["count_pending_tasks"]
find_untested_effectors = _mod["find_untested_effectors"]
generate_requeue_tasks = _mod["generate_requeue_tasks"]
append_tasks_to_queue = _mod["append_tasks_to_queue"]
run_review = _mod["run_review"]

# Constants for restore
_ORIG_QUEUE_FILE = _mod["QUEUE_FILE"]
_ORIG_DAEMON_LOG = _mod["DAEMON_LOG"]
_ORIG_REVIEW_FILE = _mod["REVIEW_FILE"]
_ORIG_COPIA_DIR = _mod["COPIA_DIR"]
_ORIG_GERMLINE = _mod["GERMLINE"]
_ORIG_EFFECTORS_DIR = _mod["EFFECTORS_DIR"]
_ORIG_ASSAYS_DIR = _mod["ASSAYS_DIR"]


def _restore_paths():
    """Restore all module-level path constants after test mutation."""
    _mod["QUEUE_FILE"] = _ORIG_QUEUE_FILE
    _mod["DAEMON_LOG"] = _ORIG_DAEMON_LOG
    _mod["REVIEW_FILE"] = _ORIG_REVIEW_FILE
    _mod["COPIA_DIR"] = _ORIG_COPIA_DIR
    _mod["GERMLINE"] = _ORIG_GERMLINE
    _mod["EFFECTORS_DIR"] = _ORIG_EFFECTORS_DIR
    _mod["ASSAYS_DIR"] = _ORIG_ASSAYS_DIR


# ── parse_since_arg tests ──────────────────────────────────────────────


def test_parse_since_arg_minutes():
    """parse_since_arg parses '30m' as 30."""
    assert parse_since_arg("30m") == 30


def test_parse_since_arg_hours():
    """parse_since_arg parses '2h' as 120."""
    assert parse_since_arg("2h") == 120


def test_parse_since_arg_bare_number():
    """parse_since_arg treats bare number as minutes."""
    assert parse_since_arg("45") == 45


def test_parse_since_arg_none():
    """parse_since_arg returns 30 for None input."""
    assert parse_since_arg(None) == 30


def test_parse_since_arg_invalid():
    """parse_since_arg returns 30 for invalid input."""
    assert parse_since_arg("abc") == 30


def test_parse_since_arg_whitespace():
    """parse_since_arg trims whitespace."""
    assert parse_since_arg("  15m  ") == 15


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


def test_parse_log_timestamp_empty_string():
    """parse_log_timestamp returns None for empty string."""
    assert parse_log_timestamp("") is None


# ── parse_completed_tasks tests ────────────────────────────────────────


def test_parse_completed_tasks_basic():
    """parse_completed_tasks parses Finished lines with exit=0."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_text = f"[{now}] Finished (120s, exit=0): golem --provider infini \"write tests\"\n"
    tasks = parse_completed_tasks(log_text, since_minutes=30)
    assert len(tasks) == 1
    assert tasks[0]["exit_code"] == 0
    assert tasks[0]["duration_s"] == 120
    assert "write tests" in tasks[0]["cmd"]


def test_parse_completed_tasks_failed():
    """parse_completed_tasks detects non-zero exit codes."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_text = f"[{now}] Finished (5s, exit=1): golem \"broken task\"\n"
    tasks = parse_completed_tasks(log_text, since_minutes=30)
    assert len(tasks) == 1
    assert tasks[0]["exit_code"] == 1


def test_parse_completed_tasks_ignores_old():
    """parse_completed_tasks skips entries older than window."""
    old_ts = (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    log_text = f"[{old_ts}] Finished (10s, exit=0): golem \"old task\"\n"
    tasks = parse_completed_tasks(log_text, since_minutes=30)
    assert tasks == []


def test_parse_completed_tasks_mixed():
    """parse_completed_tasks handles mix of success/failure in one log."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_text = (
        f"[{now}] Finished (60s, exit=0): golem \"task A\"\n"
        f"[{now}] Finished (30s, exit=1): golem \"task B\"\n"
        f"[{now}] Starting: golem \"task C\"\n"
        f"[{now}] Idle: 5 pending\n"
    )
    tasks = parse_completed_tasks(log_text, since_minutes=30)
    assert len(tasks) == 2
    assert tasks[0]["exit_code"] == 0
    assert tasks[1]["exit_code"] == 1


def test_parse_completed_tasks_empty_log():
    """parse_completed_tasks returns empty list for empty log."""
    assert parse_completed_tasks("", since_minutes=30) == []


def test_parse_completed_tasks_binary_content():
    """parse_completed_tasks handles binary-like content."""
    log_text = "\x00\x01\x02\xff\xfe\xfd"
    assert parse_completed_tasks(log_text, since_minutes=30) == []


# ── check_file_exists tests ────────────────────────────────────────────


def test_check_file_exists_true(tmp_path):
    """check_file_exists returns True for existing file."""
    f = tmp_path / "exists.txt"
    f.write_text("hello")
    assert check_file_exists(str(f)) is True


def test_check_file_exists_false(tmp_path):
    """check_file_exists returns False for nonexistent file."""
    assert check_file_exists(str(tmp_path / "nope.txt")) is False


# ── count_words tests ──────────────────────────────────────────────────


def test_count_words_existing_file(tmp_path):
    """count_words returns correct count for existing file."""
    f = tmp_path / "doc.md"
    f.write_text("word " * 100)
    assert count_words(str(f)) == 100


def test_count_words_missing_file(tmp_path):
    """count_words returns 0 for missing file."""
    assert count_words(str(tmp_path / "missing.md")) == 0


def test_count_words_empty_file(tmp_path):
    """count_words returns 0 for empty file."""
    f = tmp_path / "empty.md"
    f.write_text("")
    assert count_words(str(f)) == 0


def test_count_words_unreadable(tmp_path):
    """count_words returns 0 for unreadable file."""
    f = tmp_path / "secret.md"
    f.write_text("classified")
    f.chmod(0o000)
    try:
        assert count_words(str(f)) == 0
    finally:
        f.chmod(0o644)


# ── run_pytest_on_file tests ───────────────────────────────────────────


def test_run_pytest_on_file_parses_output():
    """run_pytest_on_file parses pytest output for pass/fail counts."""
    def mock_run(cmd, shell, capture_output, text, timeout=None):
        r = MagicMock()
        r.stdout = "3 passed, 1 failed\n"
        r.stderr = ""
        return r

    with patch("subprocess.run", side_effect=mock_run):
        passed, failed = run_pytest_on_file("assays/test_example.py")

    assert passed == 3
    assert failed == 1


def test_run_pytest_on_file_timeout():
    """run_pytest_on_file handles timeout gracefully."""
    def mock_run_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("cmd", 120)

    with patch("subprocess.run", side_effect=mock_run_timeout):
        passed, failed = run_pytest_on_file("assays/test_slow.py")

    assert passed == 0
    assert failed == 0


def test_run_pytest_on_file_exception():
    """run_pytest_on_file handles other exceptions."""
    def mock_run_error(*args, **kwargs):
        raise RuntimeError("broken")

    with patch("subprocess.run", side_effect=mock_run_error):
        passed, failed = run_pytest_on_file("assays/test_broken.py")

    assert passed == 0
    assert failed == 0


# ── diagnose_failure tests ─────────────────────────────────────────────


def test_diagnose_path_issue():
    """diagnose_failure detects hardcoded /home/terry/ paths."""
    result = diagnose_failure("golem /home/terry/germline", "")
    assert result["diagnosis"] == "path_issue"


def test_diagnose_import_error():
    """diagnose_failure detects ImportError."""
    result = diagnose_failure("golem task", "ImportError: no module")
    assert result["diagnosis"] == "import_error"


def test_diagnose_timeout():
    """diagnose_failure detects timeout."""
    result = diagnose_failure("golem timeout task", "")
    assert result["diagnosis"] == "timeout"


def test_diagnose_syntax_error():
    """diagnose_failure detects SyntaxError."""
    result = diagnose_failure("golem task", "SyntaxError: invalid")
    assert result["diagnosis"] == "syntax_error"


def test_diagnose_permission_error():
    """diagnose_failure detects PermissionError."""
    result = diagnose_failure("golem task", "PermissionError: denied")
    assert result["diagnosis"] == "permission_error"


def test_diagnose_usage_error_exit_2():
    """diagnose_failure detects usage errors via exit code 2."""
    result = diagnose_failure("golem task", "", exit_code=2)
    assert result["diagnosis"] == "usage_error"


def test_diagnose_unknown():
    """diagnose_failure returns unknown for unrecognized patterns."""
    result = diagnose_failure("golem task", "some random output")
    assert result["diagnosis"] == "unknown"


def test_diagnose_path_issue_windows():
    """diagnose_failure detects Windows-style paths."""
    result = diagnose_failure('golem task', 'C:\\Users\\terry\\file')
    assert result["diagnosis"] == "path_issue"


def test_diagnose_module_not_found():
    """diagnose_failure detects ModuleNotFoundError."""
    result = diagnose_failure("golem task", "ModuleNotFoundError: lacuna")
    assert result["diagnosis"] == "import_error"


def test_diagnose_produces_fixed_task():
    """diagnose_failure always produces a fixed_task string."""
    result = diagnose_failure('golem --provider infini --max-turns 50 "fix foo"', "")
    assert "fixed_task" in result
    assert isinstance(result["fixed_task"], str)
    assert len(result["fixed_task"]) > 0


def test_diagnose_path_issue_fixed_task_has_hint():
    """diagnose_failure adds Path.home() hint for path_issue."""
    result = diagnose_failure("golem /home/terry/", "")
    assert "Path.home()" in result["fixed_task"]


def test_diagnose_import_error_fixed_task_has_hint():
    """diagnose_failure adds exec hint for import_error."""
    result = diagnose_failure("golem task", "ImportError: foo")
    assert "exec(" in result["fixed_task"]


def test_diagnose_timeout_reduces_turns():
    """diagnose_failure reduces turns for timeout diagnosis."""
    result = diagnose_failure(
        'golem --provider infini --max-turns 50 timeout "big task"', ""
    )
    assert "max-turns" in result["fixed_task"]
    # Should have fewer turns than original 50
    import re
    m = re.search(r"--max-turns (\d+)", result["fixed_task"])
    assert m is not None
    assert int(m.group(1)) < 50


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
        _restore_paths()

    assert count == 3  # [ ] + [!!] + [ ]


def test_count_pending_tasks_missing_file(tmp_path):
    """count_pending_tasks returns 0 when queue file missing."""
    _mod["QUEUE_FILE"] = tmp_path / "nonexistent.md"
    try:
        count = count_pending_tasks()
    finally:
        _restore_paths()

    assert count == 0


def test_count_pending_tasks_empty_file(tmp_path):
    """count_pending_tasks returns 0 for empty queue."""
    queue_file = tmp_path / "golem-queue.md"
    queue_file.write_text("")
    _mod["QUEUE_FILE"] = queue_file
    try:
        count = count_pending_tasks()
    finally:
        _restore_paths()

    assert count == 0


# ── find_untested_effectors tests ──────────────────────────────────────


def test_find_untested_effectors(tmp_path):
    """find_untested_effectors identifies effectors without tests."""
    _mod["EFFECTORS_DIR"] = tmp_path / "effectors"
    _mod["ASSAYS_DIR"] = tmp_path / "assays"
    _mod["EFFECTORS_DIR"].mkdir(parents=True)
    _mod["ASSAYS_DIR"].mkdir(parents=True)

    (_mod["EFFECTORS_DIR"] / "alpha").write_text("# alpha")
    (_mod["EFFECTORS_DIR"] / "beta").write_text("# beta")
    (_mod["EFFECTORS_DIR"] / "gamma").write_text("# gamma")
    (_mod["ASSAYS_DIR"] / "test_alpha.py").write_text("def test_alpha(): pass")

    try:
        untested = find_untested_effectors()
    finally:
        _restore_paths()

    assert "alpha" not in untested
    assert "beta" in untested
    assert "gamma" in untested


def test_find_untested_effectors_empty(tmp_path):
    """find_untested_effectors returns empty when no effectors exist."""
    _mod["EFFECTORS_DIR"] = tmp_path / "effectors"
    _mod["ASSAYS_DIR"] = tmp_path / "assays"
    _mod["EFFECTORS_DIR"].mkdir(parents=True)
    _mod["ASSAYS_DIR"].mkdir(parents=True)

    try:
        untested = find_untested_effectors()
    finally:
        _restore_paths()

    assert untested == []


def test_find_untested_effectors_all_tested(tmp_path):
    """find_untested_effectors returns empty when all have tests."""
    _mod["EFFECTORS_DIR"] = tmp_path / "effectors"
    _mod["ASSAYS_DIR"] = tmp_path / "assays"
    _mod["EFFECTORS_DIR"].mkdir(parents=True)
    _mod["ASSAYS_DIR"].mkdir(parents=True)

    (_mod["EFFECTORS_DIR"] / "my-tool").write_text("# tool")
    (_mod["ASSAYS_DIR"] / "test_my_tool.py").write_text("def test_tool(): pass")

    try:
        untested = find_untested_effectors()
    finally:
        _restore_paths()

    assert untested == []


# ── generate_requeue_tasks tests ───────────────────────────────────────


def test_generate_requeue_tasks_basic():
    """generate_requeue_tasks creates properly formatted task lines."""
    _mod["EFFECTORS_DIR"] = Path("/tmp/nonexistent_effectors_for_test")
    _mod["ASSAYS_DIR"] = Path("/tmp/nonexistent_assays_for_test")
    try:
        # No effectors => empty
        tasks = generate_requeue_tasks(current_pending=0)
    finally:
        _restore_paths()

    # With no untested effectors (dirs don't exist), returns empty
    assert isinstance(tasks, list)


def test_generate_requeue_tasks_at_50_returns_empty():
    """generate_requeue_tasks returns empty when 50+ pending."""
    tasks = generate_requeue_tasks(current_pending=50)
    assert tasks == []
    tasks = generate_requeue_tasks(current_pending=100)
    assert tasks == []


def test_generate_requeue_tasks_with_modules(tmp_path):
    """generate_requeue_tasks creates tasks for untested modules."""
    _mod["EFFECTORS_DIR"] = tmp_path / "effectors"
    _mod["ASSAYS_DIR"] = tmp_path / "assays"
    _mod["EFFECTORS_DIR"].mkdir(parents=True)
    _mod["ASSAYS_DIR"].mkdir(parents=True)

    for i in range(5):
        (_mod["EFFECTORS_DIR"] / f"module-{i}").write_text(f"# module {i}")

    try:
        tasks = generate_requeue_tasks(current_pending=0)
    finally:
        _restore_paths()

    assert len(tasks) == 5
    for t in tasks:
        assert t.startswith("- [ ] `golem")
        assert "--provider" in t


def test_generate_requeue_tasks_limits_to_needed(tmp_path):
    """generate_requeue_tasks limits to 50 - current_pending."""
    _mod["EFFECTORS_DIR"] = tmp_path / "effectors"
    _mod["ASSAYS_DIR"] = tmp_path / "assays"
    _mod["EFFECTORS_DIR"].mkdir(parents=True)
    _mod["ASSAYS_DIR"].mkdir(parents=True)

    for i in range(10):
        (_mod["EFFECTORS_DIR"] / f"mod-{i}").write_text(f"# {i}")

    try:
        tasks = generate_requeue_tasks(current_pending=45)
    finally:
        _restore_paths()

    assert len(tasks) == 5  # 50 - 45 = 5 needed


def test_generate_requeue_tasks_provider_rotation(tmp_path):
    """generate_requeue_tasks rotates providers across tasks."""
    _mod["EFFECTORS_DIR"] = tmp_path / "effectors"
    _mod["ASSAYS_DIR"] = tmp_path / "assays"
    _mod["EFFECTORS_DIR"].mkdir(parents=True)
    _mod["ASSAYS_DIR"].mkdir(parents=True)

    for i in range(4):
        (_mod["EFFECTORS_DIR"] / f"mod-{i}").write_text(f"# {i}")

    try:
        tasks = generate_requeue_tasks(current_pending=0)
    finally:
        _restore_paths()

    import re
    providers = []
    for t in tasks:
        m = re.search(r'--provider (\w+)', t)
        if m:
            providers.append(m.group(1))
    assert len(set(providers)) > 1


# ── append_tasks_to_queue tests ────────────────────────────────────────


def test_append_tasks_to_queue(tmp_path):
    """append_tasks_to_queue appends tasks to queue file."""
    queue_file = tmp_path / "golem-queue.md"
    queue_file.write_text("# Existing Queue\n\n- [ ] `golem \"old task\"`\n")
    _mod["QUEUE_FILE"] = queue_file
    try:
        count = append_tasks_to_queue(['- [ ] `golem "new task"`'])
    finally:
        _restore_paths()

    assert count == 1
    content = queue_file.read_text()
    assert "old task" in content
    assert "new task" in content
    assert "Auto-queued" in content


def test_append_tasks_to_queue_empty():
    """append_tasks_to_queue returns 0 for empty task list."""
    count = append_tasks_to_queue([])
    assert count == 0


def test_append_tasks_creates_file(tmp_path):
    """append_tasks_to_queue creates queue file if it doesn't exist."""
    queue_file = tmp_path / "new-queue.md"
    _mod["QUEUE_FILE"] = queue_file
    try:
        count = append_tasks_to_queue(['- [ ] `golem "task"`'])
    finally:
        _restore_paths()

    assert count == 1
    assert queue_file.exists()


# ── build_review_summary tests ─────────────────────────────────────────


def test_build_review_summary_basic():
    """build_review_summary produces markdown with expected sections."""
    review = build_review_summary(
        completed=[{"cmd": "golem task A", "exit_code": 0, "duration_s": 60}],
        failed=[{"cmd": "golem task B", "exit_code": 1, "duration_s": 30}],
        test_results=[{"file": "assays/test_foo.py", "passed": 5, "failed": 1}],
        content_results=[{"file": "brief.md", "word_count": 350}],
        requeue_count=0,
    )
    assert "Golem Review" in review
    assert "Completed Tasks" in review
    assert "Failed Tasks" in review
    assert "Test Results" in review
    assert "Content Quality" in review
    assert "task A" in review
    assert "task B" in review
    assert "test_foo.py" in review
    assert "brief.md" in review


def test_build_review_summary_empty():
    """build_review_summary handles empty inputs."""
    review = build_review_summary(
        completed=[], failed=[], test_results=[], content_results=[], requeue_count=0,
    )
    assert "Golem Review" in review
    assert "(none)" in review
    assert "(no new test files)" in review
    assert "(no new content files)" in review


def test_build_review_summary_with_requeue_count():
    """build_review_summary includes requeue count."""
    review = build_review_summary(
        completed=[], failed=[], test_results=[], content_results=[], requeue_count=5,
    )
    assert "Requeued: 5" in review


def test_build_review_summary_content_thin():
    """build_review_summary marks thin content."""
    review = build_review_summary(
        completed=[], failed=[], test_results=[],
        content_results=[{"file": "short.md", "word_count": 50}],
        requeue_count=0,
    )
    assert "thin" in review


def test_build_review_summary_content_adequate():
    """build_review_summary marks adequate content."""
    review = build_review_summary(
        completed=[], failed=[], test_results=[],
        content_results=[{"file": "long.md", "word_count": 500}],
        requeue_count=0,
    )
    assert "adequate" in review


# ── run_review integration tests ───────────────────────────────────────


def test_run_review_basic(tmp_path, capsys):
    """run_review produces output and writes review file."""
    germline = tmp_path / "germline"
    copia_dir = germline / "loci" / "copia"

    _mod["GERMLINE"] = germline
    _mod["DAEMON_LOG"] = tmp_path / "golem-daemon.log"
    _mod["REVIEW_FILE"] = copia_dir / "golem-review-latest.md"
    _mod["COPIA_DIR"] = copia_dir
    _mod["QUEUE_FILE"] = germline / "loci" / "golem-queue.md"
    _mod["EFFECTORS_DIR"] = germline / "effectors"
    _mod["ASSAYS_DIR"] = germline / "assays"

    # Create minimal files
    _mod["DAEMON_LOG"].parent.mkdir(parents=True, exist_ok=True)
    _mod["DAEMON_LOG"].write_text("")
    _mod["QUEUE_FILE"].parent.mkdir(parents=True, exist_ok=True)
    _mod["QUEUE_FILE"].write_text("# Queue\n")
    _mod["EFFECTORS_DIR"].mkdir(parents=True, exist_ok=True)
    _mod["ASSAYS_DIR"].mkdir(parents=True, exist_ok=True)

    try:
        rc = run_review(auto_requeue=False, since=timedelta(minutes=30))
    finally:
        _restore_paths()

    assert rc == 0
    assert _mod["REVIEW_FILE"].exists()
    output = capsys.readouterr().out
    assert "Golem Review" in output


def test_run_review_with_auto_requeue(tmp_path, capsys):
    """run_review with auto_requeue tops up the queue when <50 pending."""
    germline = tmp_path / "germline"
    copia_dir = germline / "loci" / "copia"

    _mod["GERMLINE"] = germline
    _mod["DAEMON_LOG"] = tmp_path / "golem-daemon.log"
    _mod["REVIEW_FILE"] = copia_dir / "golem-review-latest.md"
    _mod["COPIA_DIR"] = copia_dir
    _mod["QUEUE_FILE"] = germline / "loci" / "golem-queue.md"
    _mod["EFFECTORS_DIR"] = germline / "effectors"
    _mod["ASSAYS_DIR"] = germline / "assays"

    _mod["DAEMON_LOG"].parent.mkdir(parents=True, exist_ok=True)
    _mod["DAEMON_LOG"].write_text("")
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
        _restore_paths()

    assert rc == 0
    content = _mod["QUEUE_FILE"].read_text()
    assert "Auto-queued" in content


def test_run_review_with_completed_task(tmp_path, capsys):
    """run_review processes a completed task from the log."""
    germline = tmp_path / "germline"
    copia_dir = germline / "loci" / "copia"

    _mod["GERMLINE"] = germline
    _mod["DAEMON_LOG"] = tmp_path / "golem-daemon.log"
    _mod["REVIEW_FILE"] = copia_dir / "golem-review-latest.md"
    _mod["COPIA_DIR"] = copia_dir
    _mod["QUEUE_FILE"] = germline / "loci" / "golem-queue.md"
    _mod["EFFECTORS_DIR"] = germline / "effectors"
    _mod["ASSAYS_DIR"] = germline / "assays"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _mod["DAEMON_LOG"].parent.mkdir(parents=True, exist_ok=True)
    _mod["DAEMON_LOG"].write_text(
        f"[{now}] Finished (100s, exit=0): golem --provider infini \"task A\"\n"
    )
    _mod["QUEUE_FILE"].parent.mkdir(parents=True, exist_ok=True)
    _mod["QUEUE_FILE"].write_text("# Queue\n")
    _mod["EFFECTORS_DIR"].mkdir(parents=True, exist_ok=True)
    _mod["ASSAYS_DIR"].mkdir(parents=True, exist_ok=True)

    try:
        rc = run_review(auto_requeue=False, since=timedelta(minutes=30))
    finally:
        _restore_paths()

    assert rc == 0
    output = capsys.readouterr().out
    assert "task A" in output


def test_run_review_with_failed_task_auto_requeue(tmp_path, capsys):
    """run_review diagnoses failures and writes fixed tasks when auto_requeue."""
    germline = tmp_path / "germline"
    copia_dir = germline / "loci" / "copia"

    _mod["GERMLINE"] = germline
    _mod["DAEMON_LOG"] = tmp_path / "golem-daemon.log"
    _mod["REVIEW_FILE"] = copia_dir / "golem-review-latest.md"
    _mod["COPIA_DIR"] = copia_dir
    _mod["QUEUE_FILE"] = germline / "loci" / "golem-queue.md"
    _mod["EFFECTORS_DIR"] = germline / "effectors"
    _mod["ASSAYS_DIR"] = germline / "assays"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _mod["DAEMON_LOG"].parent.mkdir(parents=True, exist_ok=True)
    _mod["DAEMON_LOG"].write_text(
        f"[{now}] Finished (5s, exit=1): golem --provider infini \"import lacuna\"\n"
    )
    _mod["QUEUE_FILE"].parent.mkdir(parents=True, exist_ok=True)
    _mod["QUEUE_FILE"].write_text("# Queue\n")
    _mod["EFFECTORS_DIR"].mkdir(parents=True, exist_ok=True)
    _mod["ASSAYS_DIR"].mkdir(parents=True, exist_ok=True)

    try:
        rc = run_review(auto_requeue=True, since=timedelta(minutes=30))
    finally:
        _restore_paths()

    assert rc == 0
    queue_content = _mod["QUEUE_FILE"].read_text()
    # Should have a fixed task with the import fix hint
    assert "exec(" in queue_content


# ── Edge case: empty log + empty queue ─────────────────────────────────


def test_run_review_empty_everything(tmp_path, capsys):
    """run_review handles completely empty state."""
    germline = tmp_path / "germline"
    copia_dir = germline / "loci" / "copia"

    _mod["GERMLINE"] = germline
    _mod["DAEMON_LOG"] = tmp_path / "nonexistent.log"
    _mod["REVIEW_FILE"] = copia_dir / "golem-review-latest.md"
    _mod["COPIA_DIR"] = copia_dir
    _mod["QUEUE_FILE"] = germline / "loci" / "golem-queue.md"
    _mod["EFFECTORS_DIR"] = germline / "effectors"
    _mod["ASSAYS_DIR"] = germline / "assays"

    # Don't create log file at all
    _mod["QUEUE_FILE"].parent.mkdir(parents=True, exist_ok=True)
    _mod["QUEUE_FILE"].write_text("")
    _mod["EFFECTORS_DIR"].mkdir(parents=True, exist_ok=True)
    _mod["ASSAYS_DIR"].mkdir(parents=True, exist_ok=True)

    try:
        rc = run_review(auto_requeue=False, since=timedelta(minutes=30))
    finally:
        _restore_paths()

    assert rc == 0
    assert "(none)" in capsys.readouterr().out
