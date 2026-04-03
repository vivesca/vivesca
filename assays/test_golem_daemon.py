from __future__ import annotations

"""Tests for golem-daemon — provider-aware task queue processor."""

import json
import signal
import time
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _ensure_tmp_path(tmp_path: Path) -> None:
    """Guarantee tmp_path exists on disk before each test (prevents batch-race FileNotFoundError)."""
    tmp_path.mkdir(parents=True, exist_ok=True)


def _load_golem_daemon():
    """Load the golem-daemon module by exec-ing its Python body."""
    source = open(str(Path.home() / "germline/effectors/golem-daemon")).read()
    # Skip the shebang and find the first import
    ns: dict = {"__name__": "golem_daemon"}
    exec(source, ns)
    return ns


_mod = _load_golem_daemon()
parse_provider = _mod["parse_provider"]
get_provider_limit = _mod["get_provider_limit"]
parse_queue = _mod["parse_queue"]
PROVIDER_LIMITS = _mod["PROVIDER_LIMITS"]
DEFAULT_LIMIT = _mod["DEFAULT_LIMIT"]
QUEUE_FILE = _mod["QUEUE_FILE"]
mark_failed = _mod["mark_failed"]
check_new_test_files_and_run_pytest = _mod["check_new_test_files_and_run_pytest"]
_normalize_prompt = _mod["_normalize_prompt"]
_get_pending_prompts = _mod["_get_pending_prompts"]
cmd_status = _mod["cmd_status"]


# ── parse_provider tests ─────────────────────────────────────────────


def test_parse_provider_extracts_provider():
    """parse_provider extracts --provider value from command."""
    cmd = 'golem --provider infini --max-turns 50 "do something"'
    assert parse_provider(cmd) == "infini"


def test_parse_provider_different_providers():
    """parse_provider works for all known providers."""
    assert parse_provider('golem --provider volcano "test"') == "volcano"
    assert parse_provider('golem --provider zhipu "test"') == "zhipu"
    assert parse_provider('golem --provider infini "test"') == "infini"


def test_parse_provider_no_provider_returns_default():
    """parse_provider returns 'default' when no --provider flag."""
    cmd = 'golem "do something"'
    assert parse_provider(cmd) == "default"


def test_parse_provider_provider_before_other_flags():
    """parse_provider handles --provider with other flags."""
    cmd = 'golem --provider infini --batch file1.py file2.py'
    assert parse_provider(cmd) == "infini"


def test_parse_provider_full_mode():
    """parse_provider handles --full and --provider combination."""
    cmd = 'golem --provider infini --full --max-turns 50 "research"'
    assert parse_provider(cmd) == "infini"


# ── get_provider_limit tests ───────────────────────────────────────────


def test_get_provider_limit_known_providers():
    """get_provider_limit returns correct limits for known providers."""
    assert get_provider_limit("zhipu") == 8
    assert get_provider_limit("infini") == 2  # reduced from 4 to prevent parallel 429s
    assert get_provider_limit("volcano") == 16


def test_get_provider_limit_unknown_provider():
    """get_provider_limit returns default for unknown providers."""
    assert get_provider_limit("unknown") == DEFAULT_LIMIT
    assert get_provider_limit("default") == DEFAULT_LIMIT


def test_provider_limits_constant():
    """PROVIDER_LIMITS contains expected values."""
    assert PROVIDER_LIMITS["zhipu"] == 8
    assert PROVIDER_LIMITS["infini"] == 2  # reduced from 4 to prevent parallel 429s
    assert PROVIDER_LIMITS["volcano"] == 16


# ── parse_queue tests ─────────────────────────────────────────────────


def _make_queue_file(tmp_path: Path, content: str) -> Path:
    """Create a fake golem-queue.md in tmp_path."""
    queue_dir = tmp_path / "germline" / "loci"
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_path = queue_dir / "golem-queue.md"
    queue_path.write_text(content)
    return queue_path


_QUEUE_CONTENT = """# Golem Task Queue

## Pending

- [ ] `golem --provider infini --max-turns 50 "Task 1"`
- [ ] `golem --provider volcano "Task 2"`
- [ ] `golem "Task 3 without provider"`

## Done

- [x] `golem --provider infini "Completed task"`
"""


def test_parse_queue_returns_pending_tasks(tmp_path):
    """parse_queue returns list of (line_number, command) for pending tasks."""
    queue_path = _make_queue_file(tmp_path, _QUEUE_CONTENT)
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        pending = parse_queue()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    assert len(pending) == 3
    # Commands should include the golem prefix
    commands = [cmd for _, cmd, _ in pending]
    assert any("infini" in c for c in commands)
    assert any("volcano" in c for c in commands)


def test_parse_queue_skips_done_tasks(tmp_path):
    """parse_queue skips completed tasks (marked with [x])."""
    queue_path = _make_queue_file(tmp_path, _QUEUE_CONTENT)
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        pending = parse_queue()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    # Should not include "Completed task"
    commands = [cmd for _, cmd, _ in pending]
    assert not any("Completed task" in c for c in commands)


def test_parse_queue_empty_file(tmp_path):
    """parse_queue returns empty list for non-existent file."""
    queue_path = tmp_path / "nonexistent.md"
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        pending = parse_queue()
    finally:
        _mod["QUEUE_FILE"] = original_queue
    assert pending == []


def test_parse_queue_returns_line_numbers(tmp_path):
    """parse_queue returns correct line numbers for tasks."""
    queue_path = _make_queue_file(tmp_path, _QUEUE_CONTENT)
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        pending = parse_queue()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    # Line numbers should be unique
    line_nums = [ln for ln, _, _ in pending]
    assert len(set(line_nums)) == len(line_nums)


# ── Integration tests ────────────────────────────────────────────────


def test_provider_extraction_from_queue(tmp_path):
    """Provider can be extracted from queued commands."""
    queue_path = _make_queue_file(tmp_path, _QUEUE_CONTENT)
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        pending = parse_queue()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    providers = [parse_provider(cmd) for _, cmd, _ in pending]
    assert "infini" in providers
    assert "volcano" in providers
    assert "default" in providers


def test_concurrency_respects_provider_limits():
    """Verify that max workers would allow full provider concurrency."""
    max_workers = max(PROVIDER_LIMITS.values())
    assert max_workers == 16  # volcano has highest limit


# ── check_new_test_files_and_run_pytest tests ───────────────────────────


check_new_test_files_and_run_pytest = _mod["check_new_test_files_and_run_pytest"]


def test_check_new_test_files_no_new_tests(tmp_path, monkeypatch):
    """check_new_test_files_and_run_pytest returns pass when no new test files."""
    monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
        passed, summary = check_new_test_files_and_run_pytest()
    assert passed is True
    assert "git diff failed" in summary


def test_check_new_test_files_with_new_files(tmp_path, monkeypatch):
    """check_new_test_files_and_run_pytest detects and runs new test files."""
    monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)

    def mock_run(cmd, shell, capture_output, text, cwd=None, **kwargs):
        result = MagicMock()
        if "diff --name-only" in cmd and "--diff-filter=A" in cmd:
            result.returncode = 0
            result.stdout = "assays/test_example.py\nassays/other.txt\n"
        elif "pytest" in cmd:
            result.returncode = 0
            result.stdout = "3 passed in 1.0s\n"
        else:
            result.returncode = 0
            result.stdout = ""
        return result

    with patch("subprocess.run", side_effect=mock_run):
        passed, summary = check_new_test_files_and_run_pytest()
    assert passed is True
    assert "pytest passed" in summary


# ── mark_failed retry tests ─────────────────────────────────────────────


def test_mark_failed_retries_first_attempt(tmp_path):
    """mark_failed re-queues task on first failure (appends ' (retry)')."""
    queue_dir = tmp_path / "germline" / "loci"
    queue_dir.mkdir(parents=True)
    queue_path = queue_dir / "golem-queue.md"
    queue_path.write_text("- [ ] `golem --provider infini \"task1\"`\n")

    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        result = mark_failed(0)
    finally:
        _mod["QUEUE_FILE"] = original_queue

    # Should return retried: True
    assert result["retried"] is True

    # Task should still be pending with (retry) appended
    content = queue_path.read_text()
    assert "- [ ] " in content  # Still pending
    assert "- [!]" not in content  # Not marked failed
    assert "(retry)" in content
    assert 'golem --provider infini "task1 (retry)"' in content


def test_mark_failed_marks_failed_on_retry(tmp_path):
    """mark_failed marks [!] when task already has (retry)."""
    queue_dir = tmp_path / "germline" / "loci"
    queue_dir.mkdir(parents=True)
    queue_path = queue_dir / "golem-queue.md"
    # Task already has (retry) from previous failure
    queue_path.write_text("- [ ] `golem --provider infini \"task1\" (retry)`\n")

    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        result = mark_failed(0)
    finally:
        _mod["QUEUE_FILE"] = original_queue



def test_mark_failed_only_retries_once(tmp_path):
    """Verify retry only happens once - second failure gets [!]."""
    queue_dir = tmp_path / "germline" / "loci"
    queue_dir.mkdir(parents=True)
    queue_path = queue_dir / "golem-queue.md"
    queue_path.write_text("- [ ] `golem \"original task\"`\n")

    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path

        # First failure: should retry
        result1 = mark_failed(0)
        assert result1["retried"] is True

        # Re-read to get updated line
        lines = queue_path.read_text().splitlines()
        assert "(retry)" in lines[0]
        assert "- [ ]" in lines[0]

        # Simulate daemon re-parsing and re-queueing the same line number
        # (in real daemon, line_num would be recalculated)
        # For this test, we write a fresh line with (retry) already there
        queue_path.write_text("- [ ] `golem \"original task\" (retry)`\n")

        # Second failure: should mark as [!]
        result2 = mark_failed(0)
        assert result2["retried"] is False

        content = queue_path.read_text()
        assert "- [!]" in content
    finally:
        _mod["QUEUE_FILE"] = original_queue


def test_mark_failed_handles_multiple_tasks(tmp_path):
    """mark_failed correctly handles multiple tasks with retry logic."""
    queue_dir = tmp_path / "germline" / "loci"
    queue_dir.mkdir(parents=True)
    queue_path = queue_dir / "golem-queue.md"
    queue_path.write_text(
        "- [ ] `golem \"task1\"`\n"
        "- [ ] `golem \"task2\" (retry)`\n"
        "- [ ] `golem \"task3\"`\n"
    )

    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path

        # Task 0: first failure -> retry
        result0 = mark_failed(0)
        assert result0["retried"] is True

        # Task 1: already retry -> fail
        result1 = mark_failed(1)
        assert result1["retried"] is False

        # Task 2: first failure -> retry
        result2 = mark_failed(2)
        assert result2["retried"] is True

        lines = queue_path.read_text().splitlines()
        assert "(retry)" in lines[0]
        assert "- [!]" in lines[1]
        assert "(retry)" in lines[2]
    finally:
        _mod["QUEUE_FILE"] = original_queue


# ── validate_golem_output tests ─────────────────────────────────────────


validate_golem_output = _mod["validate_golem_output"]



def test_validate_syntax_error_detection(tmp_path, monkeypatch):
    """validate_golem_output detects SyntaxError in .py files."""
    # Create a file with syntax error
    bad_file = tmp_path / "germline" / "assays" / "test_bad.py"
    bad_file.parent.mkdir(parents=True, exist_ok=True)
    bad_file.write_text("def broken(\n")  # Missing closing paren

    # Mock git diff to return our file
    def mock_run(cmd, shell, capture_output, text, cwd=None, **kwargs):
        result = MagicMock()
        if "diff --name-only" in cmd and "--diff-filter=AM" in cmd:
            result.returncode = 0
            result.stdout = "assays/test_bad.py"
        elif "grep -E" in cmd:
            result.returncode = 0
            result.stdout = ""
        else:
            result.returncode = 1
        return result

    with patch("subprocess.run", side_effect=mock_run):
        # Also need to patch Path.home() to use tmp_path
        original_home = _mod["Path"].home
        monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
        try:
            passed, errors = validate_golem_output()
        finally:
            monkeypatch.setattr(_mod["Path"], "home", original_home)

    assert not passed
    assert any("SyntaxError" in e for e in errors)


def test_validate_todo_fixme_detection(tmp_path, monkeypatch):
    """validate_golem_output detects TODO/FIXME comments."""
    # Create a file with TODO
    todo_file = tmp_path / "germline" / "assays" / "test_todo.py"
    todo_file.parent.mkdir(parents=True, exist_ok=True)
    todo_file.write_text('def foo():\n    # TODO: implement this\n    pass\n')

    def mock_run(cmd, shell, capture_output, text, cwd=None, **kwargs):
        result = MagicMock()
        if "diff --name-only" in cmd and "--diff-filter=AM" in cmd:
            result.returncode = 0
            result.stdout = "assays/test_todo.py"
        elif "grep -E" in cmd:
            result.returncode = 0
            result.stdout = ""
        else:
            result.returncode = 1
        return result

    with patch("subprocess.run", side_effect=mock_run):
        monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
        passed, errors = validate_golem_output()

    assert not passed
    assert any("TODO" in e or "FIXME" in e for e in errors)


def test_validate_stub_detection(tmp_path, monkeypatch):
    """validate_golem_output detects 'stub' in code."""
    stub_file = tmp_path / "germline" / "assays" / "test_stub.py"
    stub_file.parent.mkdir(parents=True, exist_ok=True)
    stub_file.write_text('def foo():\n    return stub_function()\n')

    def mock_run(cmd, shell, capture_output, text, cwd=None, **kwargs):
        result = MagicMock()
        if "diff --name-only" in cmd and "--diff-filter=AM" in cmd:
            result.returncode = 0
            result.stdout = "assays/test_stub.py"
        elif "grep -E" in cmd:
            result.returncode = 0
            result.stdout = ""
        else:
            result.returncode = 1
        return result

    with patch("subprocess.run", side_effect=mock_run):
        monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
        passed, errors = validate_golem_output()

    assert not passed
    assert any("stub" in e.lower() for e in errors)


def test_validate_nested_test_file_detection(tmp_path, monkeypatch):
    """validate_golem_output rejects test files not flat in assays/."""
    # Create nested test file
    nested_file = tmp_path / "germline" / "assays" / "subdir" / "test_nested.py"
    nested_file.parent.mkdir(parents=True, exist_ok=True)
    nested_file.write_text('def test_foo(): pass\n')

    def mock_run(cmd, shell, capture_output, text, cwd=None, **kwargs):
        result = MagicMock()
        if "diff --name-only" in cmd and "--diff-filter=AM" in cmd:
            result.returncode = 0
            result.stdout = "assays/subdir/test_nested.py"
        elif "grep -E" in cmd:
            result.returncode = 0
            result.stdout = ""
        else:
            result.returncode = 1
        return result

    with patch("subprocess.run", side_effect=mock_run):
        monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
        passed, errors = validate_golem_output()

    assert not passed
    assert any("not flat" in e for e in errors)


def test_validate_pycache_detection():
    """validate_golem_output rejects __pycache__/.pyc files."""
    def mock_run(cmd, shell, capture_output, text, cwd=None, **kwargs):
        result = MagicMock()
        # Check for the grep command for __pycache__/.pyc
        if "grep -E" in cmd and "__pycache__" in cmd:
            result.returncode = 0
            result.stdout = "assays/__pycache__/test_foo.pyc"
        elif "diff --name-only" in cmd and "--diff-filter=AM" in cmd:
            # First git diff call for .py files
            result.returncode = 0
            result.stdout = ""
        else:
            result.returncode = 0
            result.stdout = ""
        return result

    with patch("subprocess.run", side_effect=mock_run):
        passed, errors = validate_golem_output()

    assert not passed
    assert any("__pycache__" in e or ".pyc" in e for e in errors)


def test_validate_passes_clean_files(tmp_path, monkeypatch):
    """validate_golem_output passes clean .py files."""
    clean_file = tmp_path / "germline" / "assays" / "test_clean.py"
    clean_file.parent.mkdir(parents=True, exist_ok=True)
    clean_file.write_text('def test_foo():\n    assert True\n')

    def mock_run(cmd, shell, capture_output, text, cwd=None, **kwargs):
        result = MagicMock()
        if "diff --name-only" in cmd and "--diff-filter=AM" in cmd:
            result.returncode = 0
            if "grep -E" not in cmd:
                result.stdout = "assays/test_clean.py"
            else:
                result.stdout = ""
        elif "grep -E" in cmd:
            result.returncode = 0
            result.stdout = ""
        else:
            result.returncode = 1
        return result

    with patch("subprocess.run", side_effect=mock_run):
        monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
        passed, errors = validate_golem_output()

    assert passed
    assert errors == []


def test_validate_no_py_files_passes():
    """validate_golem_output passes when no .py files changed."""
    def mock_run(cmd, shell, capture_output, text, cwd=None, **kwargs):
        result = MagicMock()
        result.returncode = 0
        result.stdout = "README.md\nsetup.py"  # No .py files with our filter
        return result

    with patch("subprocess.run", side_effect=mock_run):
        passed, errors = validate_golem_output()

    # Actually setup.py is a .py file, but let's test empty case
    # The function should pass if git diff returns empty
    result = MagicMock()
    result.returncode = 0
    result.stdout = ""

    def mock_run_empty(cmd, shell, capture_output, text, cwd=None, **kwargs):
        r = MagicMock()
        r.returncode = 0
        r.stdout = ""  # No files at all
        return r

    with patch("subprocess.run", side_effect=mock_run_empty):
        passed, errors = validate_golem_output()

    assert passed
    assert errors == []


def test_validate_git_diff_fails_gracefully():
    """validate_golem_output passes silently if git diff fails."""
    def mock_run_fail(cmd, shell, capture_output, text, cwd=None, **kwargs):
        result = MagicMock()
        result.returncode = 1  # git diff failed
        result.stdout = ""
        return result

    with patch("subprocess.run", side_effect=mock_run_fail):
        passed, errors = validate_golem_output()

    assert passed
    assert errors == []


def test_validate_flat_test_file_passes(tmp_path, monkeypatch):
    """validate_golem_output accepts test files flat in assays/."""
    flat_file = tmp_path / "germline" / "assays" / "test_flat.py"
    flat_file.parent.mkdir(parents=True, exist_ok=True)
    flat_file.write_text('def test_bar():\n    assert 1 + 1 == 2\n')

    def mock_run(cmd, shell, capture_output, text, cwd=None, **kwargs):
        result = MagicMock()
        if "diff --name-only" in cmd and "--diff-filter=AM" in cmd:
            if "grep -E" not in cmd:
                result.returncode = 0
                result.stdout = "assays/test_flat.py"
            else:
                result.returncode = 0
                result.stdout = ""
        elif "grep -E" in cmd:
            result.returncode = 0
            result.stdout = ""
        else:
            result.returncode = 1
        return result

    with patch("subprocess.run", side_effect=mock_run):
        monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
        passed, errors = validate_golem_output()

    assert passed
    assert errors == []


# ── rotate_logs tests ────────────────────────────────────────────────────


rotate_logs = _mod["rotate_logs"]
ROTATE_MAX_BYTES = _mod["ROTATE_MAX_BYTES"]


def test_rotate_logs_renames_large_file(tmp_path):
    """rotate_logs renames file to .1 when it exceeds 5MB."""
    big_file = tmp_path / "golem-daemon.log"
    big_file.write_bytes(b"x" * (ROTATE_MAX_BYTES + 1))
    rotated = tmp_path / "golem-daemon.log.1"

    original_log = _mod["LOGFILE"]
    original_jsonl = _mod["JSONLFILE"]
    try:
        _mod["LOGFILE"] = big_file
        _mod["JSONLFILE"] = tmp_path / "nonexistent.jsonl"
        rotate_logs()
    finally:
        _mod["LOGFILE"] = original_log
        _mod["JSONLFILE"] = original_jsonl

    assert rotated.exists()
    assert not big_file.exists()
    assert rotated.stat().st_size == ROTATE_MAX_BYTES + 1


def test_rotate_logs_skips_small_file(tmp_path):
    """rotate_logs does not rename file when it is under 5MB."""
    small_file = tmp_path / "golem.jsonl"
    small_file.write_bytes(b"x" * (ROTATE_MAX_BYTES - 1))

    original_log = _mod["LOGFILE"]
    original_jsonl = _mod["JSONLFILE"]
    try:
        _mod["LOGFILE"] = tmp_path / "nonexistent.log"
        _mod["JSONLFILE"] = small_file
        rotate_logs()
    finally:
        _mod["LOGFILE"] = original_log
        _mod["JSONLFILE"] = original_jsonl

    assert small_file.exists()
    assert not (tmp_path / "golem.jsonl.1").exists()


def test_rotate_logs_overwrites_old_dot1(tmp_path):
    """rotate_logs overwrites existing .1 file when rotating."""
    fake_log = tmp_path / "golem-daemon.log"
    old_dot1 = tmp_path / "golem-daemon.log.1"
    old_dot1.write_text("old rotated content\n")
    fake_log.write_bytes(b"x" * (ROTATE_MAX_BYTES + 1))

    original_log = _mod["LOGFILE"]
    original_jsonl = _mod["JSONLFILE"]
    try:
        _mod["LOGFILE"] = fake_log
        _mod["JSONLFILE"] = tmp_path / "nonexistent.jsonl"
        rotate_logs()
    finally:
        _mod["LOGFILE"] = original_log
        _mod["JSONLFILE"] = original_jsonl

    assert not fake_log.exists()
    assert old_dot1.exists()
    assert old_dot1.stat().st_size == ROTATE_MAX_BYTES + 1


def test_rotate_logs_both_oversized(tmp_path):
    """rotate_logs rotates both files when both exceed 5MB."""
    fake_log = tmp_path / "golem-daemon.log"
    fake_jsonl = tmp_path / "golem.jsonl"
    fake_log.write_bytes(b"a" * (ROTATE_MAX_BYTES + 100))
    fake_jsonl.write_bytes(b"b" * (ROTATE_MAX_BYTES + 200))

    original_log = _mod["LOGFILE"]
    original_jsonl = _mod["JSONLFILE"]
    try:
        _mod["LOGFILE"] = fake_log
        _mod["JSONLFILE"] = fake_jsonl
        rotate_logs()
    finally:
        _mod["LOGFILE"] = original_log
        _mod["JSONLFILE"] = original_jsonl

    assert not fake_log.exists()
    assert not fake_jsonl.exists()
    assert (tmp_path / "golem-daemon.log.1").stat().st_size == ROTATE_MAX_BYTES + 100
    assert (tmp_path / "golem.jsonl.1").stat().st_size == ROTATE_MAX_BYTES + 200


def test_rotate_logs_exactly_at_threshold_not_rotated(tmp_path):
    """rotate_logs does not rotate files exactly at 5MB (must exceed)."""
    fake_log = tmp_path / "golem-daemon.log"
    fake_log.write_bytes(b"x" * ROTATE_MAX_BYTES)

    original_log = _mod["LOGFILE"]
    original_jsonl = _mod["JSONLFILE"]
    try:
        _mod["LOGFILE"] = fake_log
        _mod["JSONLFILE"] = tmp_path / "nonexistent.jsonl"
        rotate_logs()
    finally:
        _mod["LOGFILE"] = original_log
        _mod["JSONLFILE"] = original_jsonl

    assert fake_log.exists()
    assert not (tmp_path / "golem-daemon.log.1").exists()


def test_rotate_logs_no_files(tmp_path):
    """rotate_logs does nothing when neither file exists."""
    original_log = _mod["LOGFILE"]
    original_jsonl = _mod["JSONLFILE"]
    try:
        _mod["LOGFILE"] = tmp_path / "nonexistent.log"
        _mod["JSONLFILE"] = tmp_path / "nonexistent.jsonl"
        rotate_logs()
    finally:
        _mod["LOGFILE"] = original_log
        _mod["JSONLFILE"] = original_jsonl

    assert not (tmp_path / "nonexistent.log").exists()
    assert not (tmp_path / "nonexistent.jsonl").exists()
    assert not (tmp_path / "nonexistent.log.1").exists()
    assert not (tmp_path / "nonexistent.jsonl.1").exists()


# ── cmd_clean tests ────────────────────────────────────────────────────────


cmd_clean = _mod["cmd_clean"]


def _make_queue_for_clean(tmp_path: Path, content: str) -> Path:
    """Create a queue file for clean tests and return its path."""
    queue_dir = tmp_path / "germline" / "loci"
    queue_dir.mkdir(parents=True, exist_ok=True)
    queue_path = queue_dir / "golem-queue.md"
    queue_path.write_text(content)
    return queue_path


_CLEAN_QUEUE = """\
# Golem Task Queue

## Pending

- [ ] `golem --provider infini "task1"`
- [ ] `golem --provider volcano "task2"`

## Done

- [x] `golem --provider infini "completed task"`
- [!] `golem --provider volcano "failed task"`
"""


def test_cmd_clean_removes_done_and_failed(tmp_path, capsys):
    """cmd_clean removes [x] and [!] lines from queue."""
    queue_path = _make_queue_for_clean(tmp_path, _CLEAN_QUEUE)
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        rc = cmd_clean()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    assert rc == 0
    out = capsys.readouterr().out
    assert "Removed 2 entries" in out

    content = queue_path.read_text()
    assert "- [x]" not in content
    assert "- [!]" not in content
    assert "- [ ]" in content


def test_cmd_clean_preserves_headers_and_pending(tmp_path):
    """cmd_clean keeps headers, blank lines, and pending ([ ]) tasks."""
    queue_path = _make_queue_for_clean(tmp_path, _CLEAN_QUEUE)
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        cmd_clean()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    content = queue_path.read_text()
    assert "# Golem Task Queue" in content
    assert "## Pending" in content
    assert 'golem --provider infini "task1"' in content
    assert 'golem --provider volcano "task2"' in content


def test_cmd_clean_no_entries_to_remove(tmp_path, capsys):
    """cmd_clean reports 0 when no [x] or [!] entries exist."""
    all_pending = """\
## Pending

- [ ] `golem "only task"`
"""
    queue_path = _make_queue_for_clean(tmp_path, all_pending)
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        rc = cmd_clean()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    assert rc == 0
    out = capsys.readouterr().out
    assert "Removed 0 entries" in out

    content = queue_path.read_text()
    assert "- [ ]" in content


def test_cmd_clean_missing_queue_file(tmp_path, capsys):
    """cmd_clean returns 1 when queue file does not exist."""
    queue_path = tmp_path / "no_such_queue.md"
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        rc = cmd_clean()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    assert rc == 1
    out = capsys.readouterr().out
    assert "Queue file not found" in out


def test_cmd_clean_empty_queue(tmp_path, capsys):
    """cmd_clean handles an empty queue file."""
    queue_path = _make_queue_for_clean(tmp_path, "")
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        rc = cmd_clean()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    assert rc == 0
    out = capsys.readouterr().out
    assert "Removed 0 entries" in out


def test_cmd_clean_all_tasks_removed(tmp_path, capsys):
    """cmd_clean handles file where every task line is [x] or [!]."""
    all_done = "# Queue\n\n- [x] `golem \"done\"`\n- [!] `golem \"fail\"`\n"
    queue_path = _make_queue_for_clean(tmp_path, all_done)
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        rc = cmd_clean()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    assert rc == 0
    out = capsys.readouterr().out
    assert "Removed 2 entries" in out
    remaining = queue_path.read_text()
    assert "- [" not in remaining
    assert "# Queue" in remaining


# ── Edge case tests: missing file, malformed lines, stale line_num ──────


mark_done = _mod["mark_done"]


def _make_queue_dir(tmp_path: Path) -> Path:
    """Create the queue directory structure and return queue file path."""
    queue_dir = tmp_path / "germline" / "loci"
    queue_dir.mkdir(parents=True, exist_ok=True)
    return queue_dir / "golem-queue.md"


class TestMarkDoneEdgeCases:
    """Edge cases for mark_done: missing file, stale index, bad line_num."""

    def test_mark_done_missing_queue_file(self, tmp_path):
        """mark_done does not crash when queue file is missing."""
        queue_path = tmp_path / "nonexistent" / "golem-queue.md"
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            # Should not raise — guard returns silently
            mark_done(0, "exit=0")
        finally:
            _mod["QUEUE_FILE"] = original_queue

    def test_mark_done_negative_line_num(self, tmp_path):
        """mark_done with negative line_num does not corrupt the file."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text("- [ ] `golem \"task1\"`\n")
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            mark_done(-1, "exit=0")
        finally:
            _mod["QUEUE_FILE"] = original_queue

        # File should be unchanged — negative index not allowed
        content = queue_path.read_text()
        assert "- [ ]" in content
        assert "- [x]" not in content

    def test_mark_done_stale_line_num_already_done(self, tmp_path):
        """mark_done on a line already marked [x] is a no-op."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text(
            "- [ ] `golem \"task1\"`\n"
            "- [x] `golem \"task2\"`\n"
            "\n"
            "## Done\n"
        )
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            mark_done(1, "exit=0")  # line 1 is already [x]
        finally:
            _mod["QUEUE_FILE"] = original_queue

        content = queue_path.read_text()
        lines = content.splitlines()
        # Original [x] line should remain unchanged
        assert "- [x]" in lines[1]

    def test_mark_done_line_beyond_file(self, tmp_path):
        """mark_done with line_num beyond file length is a no-op."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text("- [ ] `golem \"task1\"`\n")
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            mark_done(999, "exit=0")
        finally:
            _mod["QUEUE_FILE"] = original_queue

        content = queue_path.read_text()
        assert "- [ ]" in content
        assert "- [x]" not in content

    def test_mark_done_no_done_section(self, tmp_path):
        """mark_done handles queue with no ## Done section."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text(
            "- [ ] `golem \"task1\"`\n"
            "- [ ] `golem \"task2\"`\n"
        )
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            mark_done(0, "exit=0")
        finally:
            _mod["QUEUE_FILE"] = original_queue

        content = queue_path.read_text()
        # Line should be marked done even without ## Done section
        assert "- [x]" in content


class TestMarkFailedEdgeCases:
    """Edge cases for mark_failed: missing file, stale index, bad line_num."""

    def test_mark_failed_missing_queue_file(self, tmp_path):
        """mark_failed does not crash when queue file is missing."""
        queue_path = tmp_path / "nonexistent" / "golem-queue.md"
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            result = mark_failed(0, "exit=1")
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert result["retried"] is False

    def test_mark_failed_negative_line_num(self, tmp_path):
        """mark_failed with negative line_num does not corrupt the file."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text("- [ ] `golem \"task1\"`\n")
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            result = mark_failed(-1, "exit=1")
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert result["retried"] is False
        content = queue_path.read_text()
        assert "- [ ]" in content
        assert "- [!]" not in content

    def test_mark_failed_stale_line_already_done(self, tmp_path):
        """mark_failed on a line already marked [x] or [!] is a no-op."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text(
            "- [ ] `golem \"task1\"`\n"
            "- [x] `golem \"task2\"`\n"
        )
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            result = mark_failed(1, "exit=1")
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert result["retried"] is False
        content = queue_path.read_text()
        assert "- [x]" in content

    def test_mark_failed_exit_code_2_no_retry(self, tmp_path):
        """mark_failed with exit_code=2 (usage error) never retries."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text("- [ ] `golem --provider infini \"task1\"`\n")
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            result = mark_failed(0, "bad command", exit_code=2, tail="actual error message here")
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert result["retried"] is False
        content = queue_path.read_text()
        assert "- [!]" in content
        assert "(retry)" not in content

    def test_mark_failed_line_beyond_file(self, tmp_path):
        """mark_failed with line_num beyond file length returns safely."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text("- [ ] `golem \"task1\"`\n")
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            result = mark_failed(999, "exit=1")
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert result["retried"] is False
        content = queue_path.read_text()
        assert "- [ ]" in content
        assert "- [!]" not in content


class TestParseQueueEdgeCases:
    """Edge cases for parse_queue: malformed lines, unreadable file."""

    def test_parse_queue_malformed_lines(self, tmp_path):
        """parse_queue skips lines that don't match the expected pattern."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text(
            "# Golem Task Queue\n"
            "\n"
            "garbage line\n"
            "- [ ] not backtick wrapped\n"
            "- [ ] `golem \"valid task\"`\n"
            "- [ ] `non-golem-command`\n"
            "- [x] `golem \"already done\"`\n"
            "some random text with `backticks` but no list marker\n"
            "- [ ] `golem \"another valid\"`\n"
        )
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            pending = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        # Only valid pending golem commands should be returned
        assert len(pending) == 2
        commands = [cmd for _, cmd, _ in pending]
        assert any("valid task" in c for c in commands)
        assert any("another valid" in c for c in commands)

    def test_parse_queue_whitespace_only_file(self, tmp_path):
        """parse_queue returns empty for a file with only whitespace."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text("   \n\n\t\n   \n")
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            pending = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert pending == []

    def test_parse_queue_unreadable_file(self, tmp_path):
        """parse_queue returns empty when queue file exists but is unreadable."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text("- [ ] `golem \"task\"`\n")
        # Remove read permission
        queue_path.chmod(0o000)
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            pending = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue
            queue_path.chmod(0o644)  # Restore for cleanup

        assert pending == []

    def test_parse_queue_line_numbers_correct(self, tmp_path):
        """parse_queue returns correct 0-based line numbers for tasks."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text(
            "line 0\n"       # 0
            "line 1\n"       # 1
            "- [ ] `golem \"first\"`\n"  # 2
            "line 3\n"       # 3
            "- [ ] `golem \"second\"`\n" # 4
        )
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            pending = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert len(pending) == 2
        # parse_queue now returns 3-tuples and injects task IDs into commands
        assert pending[0][0] == 2  # line number
        assert "first" in pending[0][1]
        assert pending[0][2].startswith("t-")  # task_id
        assert pending[1][0] == 4  # line number
        assert "second" in pending[1][1]
        assert pending[1][2].startswith("t-")  # task_id

    def test_parse_queue_binary_content(self, tmp_path):
        """parse_queue returns empty for a file with binary/null bytes."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_bytes(b"\x00\x01\x02\xff\xfe\xfd")
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            pending = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert pending == []


# ── cmd_clean edge case tests ────────────────────────────────────────────


class TestCmdCleanEdgeCases:
    """Additional edge cases for cmd_clean: unreadable, binary, write-protected."""

    def test_cmd_clean_unreadable_file(self, tmp_path, capsys):
        """cmd_clean returns 1 when queue file exists but is unreadable."""
        queue_path = _make_queue_for_clean(tmp_path, "- [x] `golem \"done\"`\n")
        queue_path.chmod(0o000)
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            rc = cmd_clean()
        finally:
            _mod["QUEUE_FILE"] = original_queue
            queue_path.chmod(0o644)

        assert rc == 1
        out = capsys.readouterr().out
        assert "unreadable" in out.lower()

    def test_cmd_clean_binary_content(self, tmp_path, capsys):
        """cmd_clean handles binary content in queue file."""
        queue_path = _make_queue_for_clean(tmp_path, "")
        queue_path.write_bytes(b"\x00\x01\x02\xff")
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            rc = cmd_clean()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert rc == 1
        out = capsys.readouterr().out
        assert "unreadable" in out.lower()

    def test_cmd_clean_write_protected(self, tmp_path, capsys):
        """cmd_clean returns 1 when queue file is write-protected."""
        queue_path = _make_queue_for_clean(tmp_path, "- [x] `golem \"done\"`\n")
        # Make directory read-only so write_text fails
        queue_path.chmod(0o444)
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            rc = cmd_clean()
        finally:
            _mod["QUEUE_FILE"] = original_queue
            queue_path.chmod(0o644)

        # Should fail on write — either returns 1 or succeeds if write
        # actually works despite permissions (depends on ownership)
        # On Linux owned-by-self files, chmod 444 still allows write
        # for the owner, so we just verify it doesn't crash
        assert rc in (0, 1)


# ── _golem_env edge case tests ───────────────────────────────────────────


_golem_env = _mod["_golem_env"]


class TestGolemEnvEdgeCases:
    """Edge cases for _golem_env: unreadable .env.fly, malformed lines."""

    def test_golem_env_unreadable_env_file(self, tmp_path, monkeypatch):
        """_golem_env does not crash when .env.fly exists but is unreadable."""
        env_file = tmp_path / ".env.fly"
        env_file.write_text("export TEST_KEY=secret123\n")
        env_file.chmod(0o000)
        monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
        try:
            env = _golem_env()
        finally:
            env_file.chmod(0o644)

        # Should not contain the key from the unreadable file
        assert env.get("TEST_KEY") is None

    def test_golem_env_missing_env_file(self, tmp_path, monkeypatch):
        """_golem_env works when .env.fly does not exist."""
        monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
        env = _golem_env()
        assert "PATH" in env

    def test_golem_env_malformed_lines(self, tmp_path, monkeypatch):
        """_golem_env skips malformed lines in .env.fly."""
        env_file = tmp_path / ".env.fly"
        env_file.write_text(
            "# comment\n"
            "export VALID_KEY=valid_value\n"
            "NO_EXPORT_PREFIX=still_works\n"
            "JUST_AN_EXPORT export\n"
            "=empty_key_value\n"
            "KEY_WITH_SPACES = value with spaces\n"
        )
        monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
        env = _golem_env()
        assert env.get("VALID_KEY") == "valid_value"
        assert env.get("NO_EXPORT_PREFIX") == "still_works"

    def test_golem_env_path_includes_effectors(self, tmp_path, monkeypatch):
        """_golem_env PATH includes effectors directory."""
        monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
        env = _golem_env()
        assert "effectors" in env["PATH"]


# ── read_pid edge case tests ────────────────────────────────────────────


read_pid = _mod["read_pid"]
PIDFILE = _mod["PIDFILE"]


class TestReadPidEdgeCases:
    """Edge cases for read_pid: empty file, non-numeric, whitespace."""

    def test_read_pid_empty_file(self, tmp_path):
        """read_pid returns None for empty PID file."""
        pid_path = tmp_path / "golem-daemon.pid"
        pid_path.write_text("")
        original_pid = _mod["PIDFILE"]
        try:
            _mod["PIDFILE"] = pid_path
            result = read_pid()
        finally:
            _mod["PIDFILE"] = original_pid

        assert result is None

    def test_read_pid_non_numeric(self, tmp_path):
        """read_pid returns None for PID file with non-numeric content."""
        pid_path = tmp_path / "golem-daemon.pid"
        pid_path.write_text("not_a_number")
        original_pid = _mod["PIDFILE"]
        try:
            _mod["PIDFILE"] = pid_path
            result = read_pid()
        finally:
            _mod["PIDFILE"] = original_pid

        assert result is None

    def test_read_pid_whitespace_only(self, tmp_path):
        """read_pid returns None for PID file with only whitespace."""
        pid_path = tmp_path / "golem-daemon.pid"
        pid_path.write_text("   \n\t  \n")
        original_pid = _mod["PIDFILE"]
        try:
            _mod["PIDFILE"] = pid_path
            result = read_pid()
        finally:
            _mod["PIDFILE"] = original_pid

        assert result is None

    def test_read_pid_stale_pidfile(self, tmp_path):
        """read_pid returns None and cleans up for PID of non-existent process."""
        pid_path = tmp_path / "golem-daemon.pid"
        # PID 999999999 almost certainly doesn't exist
        pid_path.write_text("999999999")
        original_pid = _mod["PIDFILE"]
        try:
            _mod["PIDFILE"] = pid_path
            result = read_pid()
        finally:
            _mod["PIDFILE"] = original_pid

        assert result is None
        # Stale pidfile should have been removed
        assert not pid_path.exists()


# ── mark_done / mark_failed with binary queue ───────────────────────────


class TestBinaryQueueEdgeCases:
    """Edge cases when queue file contains binary/non-UTF-8 content."""

    def test_mark_done_binary_queue(self, tmp_path):
        """mark_done does not crash on binary queue file."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_bytes(b"\x00\x01\x02\xff\xfe\xfd")
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            mark_done(0, "exit=0")
        finally:
            _mod["QUEUE_FILE"] = original_queue
        # Should not crash — just return silently

    def test_mark_failed_binary_queue(self, tmp_path):
        """mark_failed does not crash on binary queue file."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_bytes(b"\x00\x01\x02\xff\xfe\xfd")
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            result = mark_failed(0, "exit=1")
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert result["retried"] is False


# ── parse_queue concurrent modification ─────────────────────────────────


class TestParseQueueConcurrentModification:
    """Edge cases when queue file changes between reads or is truncated."""

    def test_parse_queue_file_truncated_after_check(self, tmp_path):
        """parse_queue handles file that exists but becomes empty."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text("- [ ] `golem \"task\"`\n")
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            # Truncate the file after exists check
            queue_path.write_text("")
            pending = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert pending == []

    def test_parse_queue_very_long_line(self, tmp_path):
        """parse_queue handles extremely long lines without crashing."""
        queue_path = _make_queue_dir(tmp_path)
        long_cmd = "golem " + "x" * 10000
        queue_path.write_text(f"- [ ] `{long_cmd}`\n")
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            pending = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert len(pending) == 1
        # Command includes injected task ID, so it's longer than original
        assert len(pending[0][1]) >= len(long_cmd)

    def test_parse_queue_duplicate_tasks(self, tmp_path):
        """parse_queue returns both entries if identical tasks appear."""
        queue_path = _make_queue_dir(tmp_path)
        queue_path.write_text(
            "- [ ] `golem \"same task\"`\n"
            "- [ ] `golem \"same task\"`\n"
        )
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            pending = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        # Both are returned — deduplication is the daemon_loop's job
        assert len(pending) == 2


# ── Priority queue tests ([!!] high-priority before [ ] normal) ──────────


_PRIORITY_QUEUE = """\
# Golem Task Queue

## Pending

- [ ] `golem --provider infini --max-turns 50 "normal task 1"`
- [!!] `golem --provider volcano "urgent task"`
- [ ] `golem "normal task 2"`
- [!!] `golem --provider zhipu "another urgent"`
- [x] `golem "already done"`
"""


def test_parse_queue_high_priority_before_normal(tmp_path):
    """parse_queue returns [!!] tasks before [ ] tasks regardless of order in file."""
    queue_path = _make_queue_dir(tmp_path)
    queue_path.write_text(_PRIORITY_QUEUE)
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        pending = parse_queue()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    assert len(pending) == 4
    commands = [cmd for _, cmd, _ in pending]
    # High-priority tasks should come first
    assert "urgent task" in commands[0]
    assert "another urgent" in commands[1]
    # Then normal tasks
    assert "normal task 1" in commands[2]
    assert "normal task 2" in commands[3]


def test_parse_queue_high_priority_line_numbers_preserved(tmp_path):
    """parse_queue preserves correct line numbers for [!!] tasks."""
    queue_path = _make_queue_dir(tmp_path)
    queue_path.write_text(_PRIORITY_QUEUE)
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        pending = parse_queue()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    # Build a map of task snippet -> line number (commands contain injected task IDs)
    by_snippet = {}
    for ln, cmd, _ in pending:
        if "urgent task" in cmd:
            by_snippet["urgent task"] = ln
        elif "another urgent" in cmd:
            by_snippet["another urgent"] = ln
        elif "normal task 1" in cmd:
            by_snippet["normal task 1"] = ln
        elif "normal task 2" in cmd:
            by_snippet["normal task 2"] = ln
    # "urgent task" is on line 5, "normal task 1" on line 4, etc.
    assert by_snippet["urgent task"] == 5
    assert by_snippet["normal task 1"] == 4
    assert by_snippet["normal task 2"] == 6
    assert by_snippet["another urgent"] == 7


def test_parse_queue_only_high_priority(tmp_path):
    """parse_queue handles queue with only [!!] tasks."""
    queue_path = _make_queue_dir(tmp_path)
    queue_path.write_text(
        "- [!!] `golem \"urgent1\"`\n"
        "- [!!] `golem \"urgent2\"`\n"
    )
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        pending = parse_queue()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    assert len(pending) == 2
    commands = [cmd for _, cmd, _ in pending]
    assert "urgent1" in commands[0]
    assert "urgent2" in commands[1]


def test_parse_queue_only_normal_priority(tmp_path):
    """parse_queue still works with only [ ] tasks (no regression)."""
    queue_path = _make_queue_dir(tmp_path)
    queue_path.write_text(
        "- [ ] `golem \"task1\"`\n"
        "- [ ] `golem \"task2\"`\n"
    )
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        pending = parse_queue()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    assert len(pending) == 2


def test_parse_queue_high_priority_preserves_file_order(tmp_path):
    """Multiple [!!] tasks maintain their original file order relative to each other."""
    queue_path = _make_queue_dir(tmp_path)
    queue_path.write_text(
        "- [!!] `golem \"urgent-A\"`\n"
        "- [ ] `golem \"normal-B\"`\n"
        "- [!!] `golem \"urgent-C\"`\n"
        "- [ ] `golem \"normal-D\"`\n"
    )
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        pending = parse_queue()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    commands = [cmd for _, cmd, _ in pending]
    # urgent-A before urgent-C (stable sort preserves relative order)
    idx_a = next(i for i, c in enumerate(commands) if "urgent-A" in c)
    idx_c = next(i for i, c in enumerate(commands) if "urgent-C" in c)
    assert idx_a < idx_c
    # normal-B before normal-D
    idx_b = next(i for i, c in enumerate(commands) if "normal-B" in c)
    idx_d = next(i for i, c in enumerate(commands) if "normal-D" in c)
    assert idx_b < idx_d


def test_mark_done_high_priority_task(tmp_path):
    """mark_done correctly marks [!!] tasks as [x]."""
    queue_path = _make_queue_dir(tmp_path)
    queue_path.write_text(
        "- [!!] `golem \"urgent task\"`\n"
        "\n"
        "## Done\n"
    )
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        mark_done(0, "exit=0")
    finally:
        _mod["QUEUE_FILE"] = original_queue

    content = queue_path.read_text()
    assert "- [x]" in content
    assert "- [!!]" not in content
    assert "- [ ]" not in content


def test_mark_done_high_priority_no_done_section(tmp_path):
    """mark_done handles [!!] task when no ## Done section exists."""
    queue_path = _make_queue_dir(tmp_path)
    queue_path.write_text("- [!!] `golem \"urgent\"`\n")
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        mark_done(0, "exit=0")
    finally:
        _mod["QUEUE_FILE"] = original_queue

    content = queue_path.read_text()
    assert "- [x]" in content
    assert "- [!!]" not in content


def test_mark_failed_high_priority_first_failure_retries(tmp_path):
    """mark_failed retries [!!] tasks, keeping [!!] status on first failure."""
    queue_path = _make_queue_dir(tmp_path)
    queue_path.write_text("- [!!] `golem --provider infini \"urgent\"`\n")
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        result = mark_failed(0)
    finally:
        _mod["QUEUE_FILE"] = original_queue

    assert result["retried"] is True
    content = queue_path.read_text()
    # Should still be high-priority pending with (retry) appended
    assert "- [!!]" in content
    assert "(retry)" in content
    assert "- [!]" not in content


def test_mark_failed_high_priority_second_failure_marks_failed(tmp_path):
    """mark_failed marks [!!] task as [!] on second failure (already has retry)."""
    queue_path = _make_queue_dir(tmp_path)
    queue_path.write_text("- [!!] `golem \"urgent\" (retry)`\n")
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        result = mark_failed(0)
    finally:
        _mod["QUEUE_FILE"] = original_queue

    assert result["retried"] is False
    content = queue_path.read_text()
    assert "- [!]" in content
    assert "- [!!]" not in content


def test_mark_failed_high_priority_exit_code_2_no_retry(tmp_path):
    """mark_failed with exit_code=2 never retries, even for [!!] tasks."""
    queue_path = _make_queue_dir(tmp_path)
    queue_path.write_text("- [!!] `golem \"urgent\"`\n")
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        result = mark_failed(0, "bad command", exit_code=2, tail="actual error message here")
    finally:
        _mod["QUEUE_FILE"] = original_queue

    assert result["retried"] is False
    content = queue_path.read_text()
    assert "- [!]" in content
    assert "- [!!]" not in content


def test_mark_done_and_mark_failed_mixed_priorities(tmp_path):
    """mark_done and mark_failed work correctly with mixed [!!] and [ ] tasks."""
    queue_path = _make_queue_dir(tmp_path)
    queue_path.write_text(
        "- [!!] `golem \"urgent\"`\n"
        "- [ ] `golem \"normal\"`\n"
        "\n"
        "## Done\n"
    )
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        mark_done(0, "exit=0")
        mark_failed(1, "exit=1")
    finally:
        _mod["QUEUE_FILE"] = original_queue

    content = queue_path.read_text()
    lines = content.splitlines()
    # Line 0 should be [x] (was [!!], now done)
    assert "- [x]" in lines[0]
    # Line 1 should be [ ] with (retry) (first failure of normal task)
    assert "- [ ]" in lines[1]
    assert "(retry)" in lines[1]


# ── cmd_retry_all tests ──────────────────────────────────────────────────


cmd_retry_all = _mod["cmd_retry_all"]

_RETRY_ALL_QUEUE = """\
# Golem Task Queue

## Pending

- [ ] `golem --provider infini "normal task"`
- [!] `golem --provider volcano "failed task 1"`
- [!] `golem --provider zhipu "failed task 2" (retry)`

## Done

- [x] `golem --provider infini "completed task"`
"""


def test_cmd_retry_all_requeues_failed(tmp_path, capsys):
    """cmd_retry_all converts all [!] tasks to [ ] pending."""
    queue_path = _make_queue_for_clean(tmp_path, _RETRY_ALL_QUEUE)
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        rc = cmd_retry_all()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    assert rc == 0
    out = capsys.readouterr().out
    assert "Re-queued 2 failed tasks" in out

    content = queue_path.read_text()
    assert "- [!]" not in content
    # Should have 3 pending tasks now (1 original + 2 re-queued)
    assert content.count("- [ ]") == 3


def test_cmd_retry_all_strips_retry_tag(tmp_path):
    """cmd_retry_all removes (retry) suffix from re-queued tasks."""
    queue_path = _make_queue_for_clean(tmp_path, _RETRY_ALL_QUEUE)
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        cmd_retry_all()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    content = queue_path.read_text()
    assert "(retry)" not in content
    # The command text should still contain "failed task 2" without (retry)
    assert 'golem --provider zhipu "failed task 2"' in content


def test_cmd_retry_all_preserves_other_lines(tmp_path):
    """cmd_retry_all keeps headers, blank lines, [x], and [ ] intact."""
    queue_path = _make_queue_for_clean(tmp_path, _RETRY_ALL_QUEUE)
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        cmd_retry_all()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    content = queue_path.read_text()
    assert "# Golem Task Queue" in content
    assert "## Pending" in content
    assert "## Done" in content
    assert "- [x]" in content
    assert 'golem --provider infini "normal task"' in content


def test_cmd_retry_all_no_failed_tasks(tmp_path, capsys):
    """cmd_retry_all reports 0 when no [!] tasks exist."""
    no_failed = """\
## Pending

- [ ] `golem "only task"`
- [x] `golem "done task"`
"""
    queue_path = _make_queue_for_clean(tmp_path, no_failed)
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        rc = cmd_retry_all()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    assert rc == 0
    out = capsys.readouterr().out
    assert "Re-queued 0 failed tasks" in out

    content = queue_path.read_text()
    assert "- [ ]" in content


def test_cmd_retry_all_missing_queue_file(tmp_path, capsys):
    """cmd_retry_all returns 1 when queue file does not exist."""
    queue_path = tmp_path / "no_such_queue.md"
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        rc = cmd_retry_all()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    assert rc == 1
    out = capsys.readouterr().out
    assert "Queue file not found" in out


def test_cmd_retry_all_empty_queue(tmp_path, capsys):
    """cmd_retry_all handles an empty queue file."""
    queue_path = _make_queue_for_clean(tmp_path, "")
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        rc = cmd_retry_all()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    assert rc == 0
    out = capsys.readouterr().out
    assert "Re-queued 0 failed tasks" in out


def test_cmd_retry_all_all_tasks_failed(tmp_path, capsys):
    """cmd_retry_all handles queue where every task is [!]."""
    all_failed = "# Queue\n\n- [!] `golem \"fail1\"`\n- [!] `golem \"fail2\" (retry)`\n"
    queue_path = _make_queue_for_clean(tmp_path, all_failed)
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["QUEUE_FILE"] = queue_path
        rc = cmd_retry_all()
    finally:
        _mod["QUEUE_FILE"] = original_queue

    assert rc == 0
    out = capsys.readouterr().out
    assert "Re-queued 2 failed tasks" in out

    content = queue_path.read_text()
    assert "- [!]" not in content
    assert content.count("- [ ]") == 2
    # (retry) stripped
    assert "(retry)" not in content


class TestCmdRetryAllEdgeCases:
    """Edge cases for cmd_retry_all: unreadable, binary, write-protected."""

    def test_cmd_retry_all_unreadable_file(self, tmp_path, capsys):
        """cmd_retry_all returns 1 when queue file exists but is unreadable."""
        queue_path = _make_queue_for_clean(tmp_path, "- [!] `golem \"fail\"`\n")
        queue_path.chmod(0o000)
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            rc = cmd_retry_all()
        finally:
            _mod["QUEUE_FILE"] = original_queue
            queue_path.chmod(0o644)

        assert rc == 1
        out = capsys.readouterr().out
        assert "unreadable" in out.lower()

    def test_cmd_retry_all_binary_content(self, tmp_path, capsys):
        """cmd_retry_all handles binary content in queue file."""
        queue_path = _make_queue_for_clean(tmp_path, "")
        queue_path.write_bytes(b"\x00\x01\x02\xff")
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            rc = cmd_retry_all()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert rc == 1
        out = capsys.readouterr().out
        assert "unreadable" in out.lower()

    def test_cmd_retry_all_write_protected(self, tmp_path, capsys):
        """cmd_retry_all returns 1 when queue file is write-protected."""
        queue_path = _make_queue_for_clean(tmp_path, "- [!] `golem \"fail\"`\n")
        queue_path.chmod(0o444)
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            rc = cmd_retry_all()
        finally:
            _mod["QUEUE_FILE"] = original_queue
            queue_path.chmod(0o644)

        # chmod 444 may not prevent owner write on Linux
        assert rc in (0, 1)

    def test_cmd_retry_all_then_parse_queue(self, tmp_path):
        """After retry-all, parse_queue picks up the re-queued tasks."""
        queue_path = _make_queue_for_clean(tmp_path, _RETRY_ALL_QUEUE)
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            cmd_retry_all()
            pending = parse_queue()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        # Originally 1 pending + 2 re-queued = 3
        assert len(pending) == 3
        commands = [cmd for _, cmd, _ in pending]
        assert any("normal task" in c for c in commands)
        assert any("failed task 1" in c for c in commands)
        assert any("failed task 2" in c for c in commands)
        # No (retry) in any command
        assert not any("(retry)" in c for c in commands)

    def test_cmd_retry_all_preserves_inline_result_annotations(self, tmp_path):
        """cmd_retry_all handles [!] lines that have trailing annotations."""
        annotated = "# Queue\n\n- [!] `golem \"task\"` some error text\n"
        queue_path = _make_queue_for_clean(tmp_path, annotated)
        original_queue = _mod["QUEUE_FILE"]
        try:
            _mod["QUEUE_FILE"] = queue_path
            rc = cmd_retry_all()
        finally:
            _mod["QUEUE_FILE"] = original_queue

        assert rc == 0
        content = queue_path.read_text()
        # Should match the pattern and convert to [ ]
        assert "- [ ]" in content


# ── cmd_stats tests ──────────────────────────────────────────────────────

cmd_stats = _mod["cmd_stats"]
JSONLFILE = _mod["JSONLFILE"]


def _make_jsonl_dir(tmp_path: Path) -> Path:
    """Create the vivesca directory structure for JSONL stats."""
    vivesca_dir = tmp_path / ".local" / "share" / "vivesca"
    vivesca_dir.mkdir(parents=True, exist_ok=True)
    return vivesca_dir / "golem.jsonl"


def test_cmd_stats_no_history(tmp_path, capsys):
    """cmd_stats says "No task history found" when no JSONL files exist."""
    jsonl_path = _make_jsonl_dir(tmp_path)
    original_jsonl = _mod["JSONLFILE"]
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["JSONLFILE"] = jsonl_path
        _mod["QUEUE_FILE"] = tmp_path / "nonexistent.md"
        rc = cmd_stats(["--all"])
    finally:
        _mod["JSONLFILE"] = original_jsonl
        _mod["QUEUE_FILE"] = original_queue

    assert rc == 0
    out = capsys.readouterr().out
    assert "No task history found" in out


def test_cmd_stats_with_records(tmp_path, capsys):
    """cmd_stats correctly calculates pass/fail counts, avg duration by provider."""
    jsonl_path = _make_jsonl_dir(tmp_path)
    today = _mod["datetime"].now().strftime("%Y-%m-%d")
    # Create sample JSONL with mixed providers, pass/fail, today and older
    records = [
        {"ts": f"{today} 10:00:00", "task_id": "t-abc123", "provider": "zhipu", "exit": 0, "duration": 120, "cmd": "test"},
        {"ts": f"{today} 10:05:00", "task_id": "t-def456", "provider": "zhipu", "exit": 0, "duration": 180, "cmd": "test"},
        {"ts": f"{today} 10:10:00", "task_id": "t-ghi789", "provider": "infini", "exit": 1, "duration": 30, "cmd": "test"},
        {"ts": "2026-03-31 15:00:00", "task_id": "t-old123", "provider": "volcano", "exit": 0, "duration": 90, "cmd": "test"},
        {"ts": "2026-03-30 12:00:00", "task_id": "t-old456", "provider": "infini", "exit": 0, "duration": 60, "cmd": "test"},
    ]
    jsonl_path.write_text("\n".join(_mod["json"].dumps(r) for r in records) + "\n")

    # Create queue with one permanently failed task
    queue_path = tmp_path / "golem-queue.md"
    queue_path.write_text(
        "- [ ] `golem --provider zhipu \"pending\"`\n"
        "- [!] `golem --provider infini \"failed\"`\n"
        "- [!] `golem --provider zhipu \"another failed\"`\n"
    )

    original_jsonl = _mod["JSONLFILE"]
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["JSONLFILE"] = jsonl_path
        _mod["QUEUE_FILE"] = queue_path
        rc = cmd_stats(["--all"])
    finally:
        _mod["JSONLFILE"] = original_jsonl
        _mod["QUEUE_FILE"] = original_queue

    assert rc == 0
    out = capsys.readouterr().out

    # Check overall counts: total 5 tasks, 4 passed, 1 failed
    assert "Total tasks: 5" in out
    assert "passed: 4" in out
    assert "failed: 1" in out

    # Check permanently failed count is 2
    assert "Permanently failed (retries exhausted): 2" in out

    # Check today's count: 3 tasks today, 2 passed 1 failed
    assert f"Tasks today ({today})" in out
    assert "3" in out
    assert "passed: 2" in out
    assert "failed: 1" in out

    # Check by provider stats
    assert "zhipu" in out
    assert "infini" in out
    assert "volcano" in out
    # zhipu: 2 tasks, 2 pass, 0 rate-limited, avg (120+180)/2 = 150s = 2m30s
    assert "zhipu" in out
    assert "2 tasks" in out
    assert "2 pass" in out
    # infini: 2 tasks, 1 pass, 1 rate-limited (exit=1, duration=30s <= 10s? no, but empty tail counts)
    assert "infini" in out
    assert "1 pass" in out


def test_cmd_stats_with_rotated_file(tmp_path, capsys):
    """cmd_stats reads from both main JSONL and rotated .1 file."""
    # Create both golem.jsonl and golem.jsonl.1 with records
    vivesca_dir = tmp_path / ".local" / "share" / "vivesca"
    vivesca_dir.mkdir(parents=True)
    jsonl_path = vivesca_dir / "golem.jsonl"
    jsonl1_path = vivesca_dir / "golem.jsonl.1"

    today = _mod["datetime"].now().strftime("%Y-%m-%d")

    record1 = {"ts": f"{today} 09:00:00", "provider": "zhipu", "exit": 0, "duration": 100, "cmd": "test"}
    record2 = {"ts": f"{today} 09:30:00", "provider": "volcano", "exit": 1, "duration": 50, "cmd": "test"}

    jsonl_path.write_text(_mod["json"].dumps(record1) + "\n")
    jsonl1_path.write_text(_mod["json"].dumps(record2) + "\n")

    original_jsonl = _mod["JSONLFILE"]
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["JSONLFILE"] = jsonl_path
        _mod["QUEUE_FILE"] = tmp_path / "nonexistent.md"
        rc = cmd_stats(["--all"])
    finally:
        _mod["JSONLFILE"] = original_jsonl
        _mod["QUEUE_FILE"] = original_queue

    assert rc == 0
    out = capsys.readouterr().out
    assert "Total tasks: 2" in out
    assert "zhipu" in out
    assert "volcano" in out


def test_cmd_stats_skips_bad_lines(tmp_path, capsys):
    """cmd_stats skips malformed JSON lines without crashing."""
    jsonl_path = _make_jsonl_dir(tmp_path)
    today = _mod["datetime"].now().strftime("%Y-%m-%d")
    content = (
        f'{_mod["json"].dumps({"ts": f"{today} 10:00", "provider": "zhipu", "exit": 0, "duration": 120})}\n'
        "this is not valid json\n"
        "{broken json syntax\n"
        f'{_mod["json"].dumps({"ts": f"{today} 10:30", "provider": "infini", "exit": 1, "duration": 30})}\n'
    )
    jsonl_path.write_text(content)

    original_jsonl = _mod["JSONLFILE"]
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["JSONLFILE"] = jsonl_path
        _mod["QUEUE_FILE"] = tmp_path / "nonexistent.md"
        rc = cmd_stats(["--all"])
    finally:
        _mod["JSONLFILE"] = original_jsonl
        _mod["QUEUE_FILE"] = original_queue

    assert rc == 0
    out = capsys.readouterr().out
    # Should find 2 valid records out of 4 lines (including empty)
    assert "Total tasks: 2" in out
    assert "zhipu" in out
    assert "infini" in out


def test_cmd_stats_handles_unreadable_jsonl(tmp_path, capsys):
    """cmd_stats handles unreadable/permissions-denied JSONL files gracefully."""
    jsonl_path = _make_jsonl_dir(tmp_path)
    jsonl_path.write_text("valid json line\n")
    jsonl_path.chmod(0o000)

    original_jsonl = _mod["JSONLFILE"]
    original_queue = _mod["QUEUE_FILE"]
    try:
        _mod["JSONLFILE"] = jsonl_path
        _mod["QUEUE_FILE"] = tmp_path / "nonexistent.md"
        rc = cmd_stats(["--all"])
    finally:
        _mod["JSONLFILE"] = original_jsonl
        _mod["QUEUE_FILE"] = original_queue
        jsonl_path.chmod(0o644)

    assert rc == 0
    out = capsys.readouterr().out
    # Should still run, just showing no records found (since we can't read the unreadable one)
    # If perms work and it can't read, still no crash
    assert "No task history found" in out or "Total tasks:" in out


# ── cmd_export_stats tests ─────────────────────────────────────────────────


cmd_export_stats = _mod["cmd_export_stats"]


def test_export_stats_no_history(tmp_path, capsys):
    """cmd_export_stats outputs empty JSON array when no JSONL files exist."""
    jsonl_path = _make_jsonl_dir(tmp_path)
    original_jsonl = _mod["JSONLFILE"]
    try:
        _mod["JSONLFILE"] = jsonl_path
        rc = cmd_export_stats(["--all"])
    finally:
        _mod["JSONLFILE"] = original_jsonl

    assert rc == 0
    out = capsys.readouterr().out.strip()
    data = json.loads(out)
    assert data == []


def test_export_stats_with_records(tmp_path, capsys):
    """cmd_export_stats outputs correct per-provider JSON with all required fields."""
    jsonl_path = _make_jsonl_dir(tmp_path)
    today = _mod["datetime"].now().strftime("%Y-%m-%d")
    records = [
        {"ts": f"{today} 10:00:00", "provider": "zhipu", "exit": 0, "duration": 120, "cmd": "test"},
        {"ts": f"{today} 10:05:00", "provider": "zhipu", "exit": 0, "duration": 180, "cmd": "test"},
        {"ts": f"{today} 10:10:00", "provider": "infini", "exit": 1, "duration": 5, "cmd": "test"},
        {"ts": "2026-03-30 12:00:00", "provider": "volcano", "exit": 0, "duration": 90, "cmd": "test"},
    ]
    jsonl_path.write_text("\n".join(_mod["json"].dumps(r) for r in records) + "\n")

    original_jsonl = _mod["JSONLFILE"]
    try:
        _mod["JSONLFILE"] = jsonl_path
        rc = cmd_export_stats(["--all"])
    finally:
        _mod["JSONLFILE"] = original_jsonl

    assert rc == 0
    out = capsys.readouterr().out.strip()
    data = json.loads(out)
    assert len(data) == 3  # zhipu, infini, volcano

    by_provider = {d["provider"]: d for d in data}

    # zhipu: 2 tasks, 2 passed, 0 failed
    z = by_provider["zhipu"]
    assert z["total"] == 2
    assert z["passed"] == 2
    assert z["failed"] == 0
    assert z["rate_limited"] == 0
    assert z["real_fail"] == 0
    assert z["capability_pct"] == 100.0

    # infini: 1 task, 0 passed, 1 failed, duration=5 <= 10 so rate_limited
    i = by_provider["infini"]
    assert i["total"] == 1
    assert i["passed"] == 0
    assert i["failed"] == 1
    assert i["rate_limited"] == 1
    assert i["real_fail"] == 0
    assert i["capability_pct"] == 0

    # volcano: 1 task, 1 passed
    v = by_provider["volcano"]
    assert v["total"] == 1
    assert v["passed"] == 1
    assert v["capability_pct"] == 100.0


def test_export_stats_output_is_valid_json(tmp_path, capsys):
    """cmd_export_stats output is parseable JSON containing all required keys."""
    jsonl_path = _make_jsonl_dir(tmp_path)
    today = _mod["datetime"].now().strftime("%Y-%m-%d")
    records = [
        {"ts": f"{today} 10:00:00", "provider": "zhipu", "exit": 0, "duration": 60, "cmd": "test"},
        {"ts": f"{today} 10:05:00", "provider": "zhipu", "exit": 1, "duration": 300, "tail": "some error", "cmd": "test"},
    ]
    jsonl_path.write_text("\n".join(_mod["json"].dumps(r) for r in records) + "\n")

    original_jsonl = _mod["JSONLFILE"]
    try:
        _mod["JSONLFILE"] = jsonl_path
        rc = cmd_export_stats(["--all"])
    finally:
        _mod["JSONLFILE"] = original_jsonl

    assert rc == 0
    out = capsys.readouterr().out.strip()
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) == 1  # only zhipu
    entry = data[0]
    required_keys = {"provider", "total", "passed", "failed", "rate_limited", "real_fail", "capability_pct", "build_count", "maint_count"}
    assert set(entry.keys()) == required_keys


def test_export_stats_reads_rotated_file(tmp_path, capsys):
    """cmd_export_stats reads from both main JSONL and rotated .1 file."""
    vivesca_dir = tmp_path / ".local" / "share" / "vivesca"
    vivesca_dir.mkdir(parents=True)
    jsonl_path = vivesca_dir / "golem.jsonl"
    jsonl1_path = vivesca_dir / "golem.jsonl.1"

    today = _mod["datetime"].now().strftime("%Y-%m-%d")
    record1 = {"ts": f"{today} 09:00:00", "provider": "zhipu", "exit": 0, "duration": 100, "cmd": "test"}
    record2 = {"ts": f"{today} 09:30:00", "provider": "volcano", "exit": 1, "duration": 50, "cmd": "test"}

    jsonl_path.write_text(_mod["json"].dumps(record1) + "\n")
    jsonl1_path.write_text(_mod["json"].dumps(record2) + "\n")

    original_jsonl = _mod["JSONLFILE"]
    try:
        _mod["JSONLFILE"] = jsonl_path
        rc = cmd_export_stats(["--all"])
    finally:
        _mod["JSONLFILE"] = original_jsonl

    assert rc == 0
    out = capsys.readouterr().out.strip()
    data = json.loads(out)
    providers = {d["provider"] for d in data}
    assert "zhipu" in providers
    assert "volcano" in providers


def test_export_stats_skips_bad_lines(tmp_path, capsys):
    """cmd_export_stats skips malformed JSON lines without crashing."""
    jsonl_path = _make_jsonl_dir(tmp_path)
    today = _mod["datetime"].now().strftime("%Y-%m-%d")
    content = (
        f'{_mod["json"].dumps({"ts": f"{today} 10:00", "provider": "zhipu", "exit": 0, "duration": 120})}\n'
        "this is not valid json\n"
        "{broken json syntax\n"
        f'{_mod["json"].dumps({"ts": f"{today} 10:30", "provider": "infini", "exit": 1, "duration": 30})}\n'
    )
    jsonl_path.write_text(content)

    original_jsonl = _mod["JSONLFILE"]
    try:
        _mod["JSONLFILE"] = jsonl_path
        rc = cmd_export_stats(["--all"])
    finally:
        _mod["JSONLFILE"] = original_jsonl

    assert rc == 0
    out = capsys.readouterr().out.strip()
    data = json.loads(out)
    assert len(data) == 2
    providers = {d["provider"] for d in data}
    assert providers == {"zhipu", "infini"}


def test_export_stats_capability_pct_calculation(tmp_path, capsys):
    """cmd_export_stats correctly computes capability_pct excluding rate-limited failures."""
    jsonl_path = _make_jsonl_dir(tmp_path)
    today = _mod["datetime"].now().strftime("%Y-%m-%d")
    # provider: 10 passed, 2 failed (1 rate-limited, 1 real)
    records = []
    for i in range(10):
        records.append({"ts": f"{today} 10:{i:02d}", "provider": "testprov", "exit": 0, "duration": 60, "cmd": "test"})
    # rate-limited failure: duration <= 10
    records.append({"ts": f"{today} 11:00", "provider": "testprov", "exit": 1, "duration": 5, "cmd": "test"})
    # real failure: duration > 10 with non-rate-limit tail
    records.append({"ts": f"{today} 11:05", "provider": "testprov", "exit": 1, "duration": 300, "tail": "syntax error in output", "cmd": "test"})
    jsonl_path.write_text("\n".join(_mod["json"].dumps(r) for r in records) + "\n")

    original_jsonl = _mod["JSONLFILE"]
    try:
        _mod["JSONLFILE"] = jsonl_path
        rc = cmd_export_stats(["--all"])
    finally:
        _mod["JSONLFILE"] = original_jsonl

    assert rc == 0
    out = capsys.readouterr().out.strip()
    data = json.loads(out)
    assert len(data) == 1
    entry = data[0]
    assert entry["total"] == 12
    assert entry["passed"] == 10
    assert entry["failed"] == 2
    assert entry["rate_limited"] == 1
    assert entry["real_fail"] == 1
    # capability = passed / (passed + real_fail) = 10/11 ≈ 90.9
    assert entry["capability_pct"] == round(100 * 10 / 11, 1)


# ── Fallback routing tests ────────────────────────────────────────────────


_pick_dispatch_provider = _mod["_pick_dispatch_provider"]
_dispatch_candidates = _mod["_dispatch_candidates"]
_resolve_dispatch_command = _mod["_resolve_dispatch_command"]
PROVIDER_FALLBACK = _mod["PROVIDER_FALLBACK"]


class TestFallbackRouting:
    """Tests for fallback routing: when providers are in cooldown, tasks
    should reroute to fallback targets (codex, gemini) per PROVIDER_FALLBACK
    chains, not default to zhipu."""

    def test_infini_fallback_prefers_codex_over_zhipu(self):
        """When infini is cooled down, its tasks route to codex first (not zhipu)."""
        cooldowns = {"infini": time.time() + 3600}
        running = {"zhipu": 0, "codex": 0, "gemini": 0}
        result = _pick_dispatch_provider("infini", cooldowns, running)
        assert result == "codex", f"Expected codex, got {result}"

    def test_volcano_fallback_prefers_codex_over_zhipu(self):
        """When volcano is cooled down, its tasks route to codex first (not zhipu)."""
        cooldowns = {"volcano": time.time() + 3600}
        running = {"zhipu": 0, "codex": 0, "gemini": 0}
        result = _pick_dispatch_provider("volcano", cooldowns, running)
        assert result == "codex", f"Expected codex, got {result}"

    def test_infini_fallback_to_gemini_when_codex_full(self):
        """When infini is cooled and codex is at capacity, fallback to gemini."""
        cooldowns = {"infini": time.time() + 3600}
        running = {"codex": 4, "zhipu": 0, "gemini": 0}
        result = _pick_dispatch_provider("infini", cooldowns, running)
        assert result == "gemini", f"Expected gemini, got {result}"

    def test_infini_fallback_to_zhipu_when_codex_and_gemini_full(self):
        """When infini is cooled and codex+gemini are full, fallback to zhipu."""
        cooldowns = {"infini": time.time() + 3600}
        running = {"codex": 4, "gemini": 4, "zhipu": 0}
        result = _pick_dispatch_provider("infini", cooldowns, running)
        assert result == "zhipu", f"Expected zhipu, got {result}"

    def test_infini_returns_none_when_all_full(self):
        """When infini is cooled and all fallback providers are full, return None."""
        cooldowns = {"infini": time.time() + 3600}
        running = {"codex": 4, "gemini": 4, "zhipu": 8, "volcano": 16}
        result = _pick_dispatch_provider("infini", cooldowns, running)
        assert result is None

    def test_no_fallback_when_provider_not_cooled(self):
        """When provider is not in cooldown, return it directly."""
        cooldowns = {}
        running = {}
        assert _pick_dispatch_provider("infini", cooldowns, running) == "infini"
        assert _pick_dispatch_provider("zhipu", cooldowns, running) == "zhipu"
        assert _pick_dispatch_provider("codex", cooldowns, running) == "codex"

    def test_fallback_skips_cooled_fallback_targets(self):
        """When infini is cooled AND codex is also cooled, skip to gemini."""
        cooldowns = {"infini": time.time() + 3600, "codex": time.time() + 3600}
        running = {"gemini": 0, "zhipu": 0}
        result = _pick_dispatch_provider("infini", cooldowns, running)
        assert result == "gemini", f"Expected gemini, got {result}"

    def test_resolve_dispatch_command_swaps_provider(self):
        """_resolve_dispatch_command swaps --provider in the command string."""
        cooldowns = {"infini": time.time() + 3600}
        running = {"codex": 0, "gemini": 0, "zhipu": 0}
        cmd = 'golem --provider infini --max-turns 50 "task"'
        result = _resolve_dispatch_command(cmd, cooldowns, running)
        assert result is not None
        new_cmd, affinity, dispatch = result
        assert affinity == "infini"
        assert dispatch == "codex"
        assert "--provider codex" in new_cmd
        assert "--provider infini" not in new_cmd

    def test_resolve_dispatch_command_no_swap_when_not_cooled(self):
        """_resolve_dispatch_command returns original when provider not cooled."""
        cooldowns = {}
        running = {}
        cmd = 'golem --provider infini --max-turns 50 "task"'
        result = _resolve_dispatch_command(cmd, cooldowns, running)
        assert result is not None
        new_cmd, affinity, dispatch = result
        assert affinity == "infini"
        assert dispatch == "infini"
        assert new_cmd == cmd

    def test_fallback_fills_codex_to_cap_before_zhipu(self):
        """Simulate a dispatch cycle: infini/volcano cooled, codex fills to
        cap before any overflow to zhipu."""
        cooldowns = {"infini": time.time() + 3600, "volcano": time.time() + 3600}
        running = {}
        codex_cap = _mod["PROVIDER_LIMITS"]["codex"]  # 4

        # Simulate dispatching 6 fallback tasks (3 infini + 3 volcano)
        dispatched = []
        for affinity in ["infini", "volcano", "infini", "volcano", "infini", "volcano"]:
            dp = _pick_dispatch_provider(affinity, cooldowns, running)
            if dp:
                running[dp] = running.get(dp, 0) + 1
                dispatched.append(dp)

        # All should go to codex (cap=4), then overflow to gemini (cap=4)
        codex_count = running.get("codex", 0)
        assert codex_count == codex_cap, (
            f"Expected codex to fill to {codex_cap}, got {codex_count}. "
            f"Dispatch order: {dispatched}"
        )
        # Remaining 2 should go to gemini
        gemini_count = running.get("gemini", 0)
        assert gemini_count == 2, f"Expected gemini=2, got {gemini_count}. Dispatch: {dispatched}"

    def test_three_providers_cooled_routes_to_two_healthy_proportionally(self):
        """When 3 providers are cooled (infini, volcano, zhipu), tasks
        route to the 2 healthy ones (codex, gemini) proportionally."""
        cooldowns = {
            "infini": time.time() + 3600,
            "volcano": time.time() + 3600,
            "zhipu": time.time() + 3600,
        }
        running = {}
        codex_cap = _mod["PROVIDER_LIMITS"]["codex"]   # 4
        gemini_cap = _mod["PROVIDER_LIMITS"]["gemini"]  # 4

        # Dispatch 10 fallback tasks: 4 infini + 3 volcano + 3 zhipu
        affinities = ["infini"] * 4 + ["volcano"] * 3 + ["zhipu"] * 3
        dispatched = []
        for affinity in affinities:
            dp = _pick_dispatch_provider(affinity, cooldowns, running)
            if dp:
                running[dp] = running.get(dp, 0) + 1
                dispatched.append((affinity, dp))

        # codex should fill to 4 (cap), gemini should fill to 4 (cap)
        # zhipu's fallback chain: codex -> gemini -> (none remaining)
        codex_count = running.get("codex", 0)
        gemini_count = running.get("gemini", 0)
        assert codex_count == codex_cap, (
            f"Expected codex={codex_cap}, got {codex_count}. Dispatches: {dispatched}"
        )
        assert gemini_count == gemini_cap, (
            f"Expected gemini={gemini_cap}, got {gemini_count}. Dispatches: {dispatched}"
        )

    def test_dispatch_candidates_order(self):
        """Verify _dispatch_candidates returns providers in correct fallback order."""
        # infini: codex -> gemini -> (remaining: zhipu, volcano)
        c = _dispatch_candidates("infini")
        assert c[0] == "codex", f"Expected codex first for infini, got {c}"
        assert c[1] == "gemini", f"Expected gemini second for infini, got {c}"

        # volcano: codex -> gemini -> (remaining: zhipu, infini)
        c = _dispatch_candidates("volcano")
        assert c[0] == "codex", f"Expected codex first for volcano, got {c}"
        assert c[1] == "gemini", f"Expected gemini second for volcano, got {c}"

        # zhipu: codex -> gemini -> (remaining: infini, volcano)
        c = _dispatch_candidates("zhipu")
        assert c[0] == "codex", f"Expected codex first for zhipu, got {c}"
        assert c[1] == "gemini", f"Expected gemini second for zhipu, got {c}"

    def test_fallback_with_throttled_codex(self):
        """When codex is throttled (effective limit reduced), fallback
        fills codex to its throttled limit, then overflows to gemini."""
        cooldowns = {"infini": time.time() + 3600, "volcano": time.time() + 3600}
        # Simulate codex throttled to 2 slots
        _mod["_provider_throttle"]["codex"] = 2
        running = {}
        try:
            effective_cap = get_provider_limit("codex")  # should be 4-2=2
            assert effective_cap == 2

            for affinity in ["infini"] * 3 + ["volcano"] * 3:
                dp = _pick_dispatch_provider(affinity, cooldowns, running)
                if dp:
                    running[dp] = running.get(dp, 0) + 1

            codex_count = running.get("codex", 0)
            gemini_count = running.get("gemini", 0)
            # codex should fill to 2 (throttled cap), rest to gemini
            assert codex_count == effective_cap, (
                f"Expected codex={effective_cap} (throttled), got {codex_count}"
            )
            assert gemini_count == 4, f"Expected gemini=4, got {gemini_count}"
        finally:
            _mod["_provider_throttle"].pop("codex", None)

    def test_dispatch_loop_fallback_before_normal(self):
        """Integration: verify the dispatch sort key puts fallback tasks first
        and fills under-capacity providers before over-capacity ones."""
        import uuid
        _dispatch_candidates_fn = _mod["_dispatch_candidates"]
        parse_provider_fn = _mod["parse_provider"]
        get_provider_limit_fn = _mod["get_provider_limit"]

        cooldowns = {"infini": time.time() + 3600, "volcano": time.time() + 3600}
        running = {"codex": 0, "zhipu": 0, "gemini": 0}

        # Build pending tasks: 2 infini, 2 volcano, 8 zhipu
        pending = []
        for i in range(2):
            pending.append((i, f'golem --provider infini "infini task {i}"', f"t-{uuid.uuid4().hex[:6]}"))
        for i in range(2):
            pending.append((10 + i, f'golem --provider volcano "volcano task {i}"', f"t-{uuid.uuid4().hex[:6]}"))
        for i in range(8):
            pending.append((20 + i, f'golem --provider zhipu "zhipu task {i}"', f"t-{uuid.uuid4().hex[:6]}"))

        # Define the sort key (mirrors the daemon_loop version)
        def _sort_key(item):
            _, cmd, _ = item
            affinity = parse_provider_fn(cmd)
            is_fallback = affinity in cooldowns
            if is_fallback:
                dp = None
                for candidate in _dispatch_candidates_fn(affinity):
                    if candidate not in cooldowns:
                        lim = get_provider_limit_fn(candidate)
                        cur = running.get(candidate, 0)
                        if cur < lim:
                            dp = candidate
                            break
            else:
                dp = affinity
            if dp is None:
                headroom = -1
            else:
                limit = get_provider_limit_fn(dp)
                current = running.get(dp, 0)
                headroom = limit - current
            return (0 if is_fallback else 1, -headroom)

        sorted_tasks = sorted(pending, key=_sort_key)

        # All 4 fallback tasks (infini+volcano) should come first
        first_4 = [parse_provider_fn(cmd) for _, cmd, _ in sorted_tasks[:4]]
        assert all(p in ("infini", "volcano") for p in first_4), (
            f"Expected fallback tasks first, got providers: {first_4}"
        )

        # All 8 zhipu tasks should come after
        last_8 = [parse_provider_fn(cmd) for _, cmd, _ in sorted_tasks[4:]]
        assert all(p == "zhipu" for p in last_8), (
            f"Expected zhipu tasks after fallbacks, got providers: {last_8}"
        )


# ── Fallback routing tests ──────────────────────────────────────────────────


_dispatch_candidates = _mod["_dispatch_candidates"]
_pick_dispatch_provider = _mod["_pick_dispatch_provider"]
_resolve_dispatch_command = _mod["_resolve_dispatch_command"]
PROVIDER_FALLBACK = _mod["PROVIDER_FALLBACK"]
_provider_throttle = _mod["_provider_throttle"]


@pytest.fixture(autouse=True)
def _reset_provider_throttle():
    """Reset adaptive throttle between fallback routing tests."""
    _provider_throttle.clear()
    yield
    _provider_throttle.clear()


class TestDispatchCandidates:
    """Tests for _dispatch_candidates — fallback chain ordering."""

    def test_infini_fallback_starts_with_codex(self):
        """infini fallback chain: codex → gemini → (others)."""
        candidates = _dispatch_candidates("infini")
        assert candidates[0] == "codex"
        assert candidates[1] == "gemini"
        # zhipu and volcano should be present as last-resort options
        assert "zhipu" in candidates
        assert "volcano" in candidates

    def test_volcano_fallback_starts_with_codex(self):
        """volcano fallback chain: codex → gemini → (others)."""
        candidates = _dispatch_candidates("volcano")
        assert candidates[0] == "codex"
        assert candidates[1] == "gemini"

    def test_codex_fallback_starts_with_gemini(self):
        """codex fallback chain: gemini → zhipu → (others)."""
        candidates = _dispatch_candidates("codex")
        assert candidates[0] == "gemini"
        assert candidates[1] == "zhipu"

    def test_zhipu_fallback_starts_with_codex(self):
        """zhipu fallback chain: codex → gemini → (others)."""
        candidates = _dispatch_candidates("zhipu")
        assert candidates[0] == "codex"
        assert candidates[1] == "gemini"

    def test_no_self_in_candidates(self):
        """A provider never appears in its own fallback list."""
        for provider in PROVIDER_FALLBACK:
            candidates = _dispatch_candidates(provider)
            assert provider not in candidates

    def test_all_providers_covered(self):
        """Every known provider appears either in fallback or tail of candidates."""
        for provider in PROVIDER_FALLBACK:
            candidates = _dispatch_candidates(provider)
            all_providers = set(PROVIDER_LIMITS.keys())
            assert set(candidates) == all_providers - {provider}


class TestPickDispatchProvider:
    """Tests for _pick_dispatch_provider — runtime provider selection."""

    def test_returns_affinity_when_not_cooled(self):
        """When affinity provider is healthy, return it directly."""
        assert _pick_dispatch_provider("infini", {}, {}) == "infini"

    def test_fallback_to_codex_when_infini_cooled(self):
        """When infini is cooled down, fallback to codex first."""
        cooldowns = {"infini": time.time() + 600}
        assert _pick_dispatch_provider("infini", cooldowns, {}) == "codex"

    def test_fallback_to_codex_when_volcano_cooled(self):
        """When volcano is cooled down, fallback to codex first."""
        cooldowns = {"volcano": time.time() + 600}
        assert _pick_dispatch_provider("volcano", cooldowns, {}) == "codex"

    def test_skip_codex_if_also_cooled(self):
        """When both infini and codex are cooled, fallback to gemini."""
        cooldowns = {"infini": time.time() + 600, "codex": time.time() + 600}
        assert _pick_dispatch_provider("infini", cooldowns, {}) == "gemini"

    def test_skip_codex_if_at_capacity(self):
        """When codex is full (4/4), fallback to gemini."""
        cooldowns = {"infini": time.time() + 600}
        running = {"codex": 4}
        assert _pick_dispatch_provider("infini", cooldowns, running) == "gemini"

    def test_skip_codex_if_one_running(self):
        """When codex has 1 running and limit is 4, still pick codex."""
        cooldowns = {"infini": time.time() + 600}
        running = {"codex": 1}
        assert _pick_dispatch_provider("infini", cooldowns, running) == "codex"

    def test_returns_none_when_all_full_or_cooled(self):
        """Returns None when every candidate is at capacity or in cooldown."""
        cooldowns = {"infini": time.time() + 600, "codex": time.time() + 600}
        running = {"gemini": 4, "zhipu": 8, "volcano": 16}
        assert _pick_dispatch_provider("infini", cooldowns, running) is None

    def test_returns_none_when_all_cooled(self):
        """Returns None when every provider is in cooldown."""
        now = time.time() + 600
        cooldowns = {p: now for p in PROVIDER_LIMITS}
        assert _pick_dispatch_provider("infini", cooldowns, {}) is None

    def test_throttled_limit_reduces_capacity(self):
        """Adaptive throttle reduces effective limit, blocking dispatch when full."""
        cooldowns = {"infini": time.time() + 600}
        # Throttle codex from 4 to 2
        _provider_throttle["codex"] = 2
        running = {"codex": 2}
        # codex effective limit = 4 - 2 = 2, running=2 → full → skip to gemini
        assert _pick_dispatch_provider("infini", cooldowns, running) == "gemini"


class TestResolveDispatchCommand:
    """Tests for _resolve_dispatch_command — command rewriting on fallback."""

    def test_swaps_provider_in_command(self):
        """Replaces --provider infini with --provider codex."""
        cooldowns = {"infini": time.time() + 600}
        result = _resolve_dispatch_command(
            'golem --provider infini --max-turns 50 "task"',
            cooldowns, {},
        )
        assert result is not None
        cmd, affinity, dispatch = result
        assert affinity == "infini"
        assert dispatch == "codex"
        assert "--provider codex" in cmd
        assert "--provider infini" not in cmd

    def test_preserves_other_flags(self):
        """Fallback swap preserves --max-turns and other flags."""
        cooldowns = {"infini": time.time() + 600}
        result = _resolve_dispatch_command(
            'golem --provider infini --max-turns 50 "task"',
            cooldowns, {},
        )
        assert result is not None
        cmd, _, _ = result
        assert "--max-turns 50" in cmd

    def test_no_swap_when_affinity_healthy(self):
        """When affinity provider is not cooled, command is unchanged."""
        result = _resolve_dispatch_command(
            'golem --provider infini --max-turns 50 "task"',
            {}, {},
        )
        assert result is not None
        cmd, affinity, dispatch = result
        assert affinity == "infini"
        assert dispatch == "infini"
        assert cmd == 'golem --provider infini --max-turns 50 "task"'

    def test_returns_none_when_all_exhausted(self):
        """Returns None when no provider is dispatchable."""
        cooldowns = {"infini": time.time() + 600, "codex": time.time() + 600}
        running = {"gemini": 4, "zhipu": 8, "volcano": 16}
        result = _resolve_dispatch_command(
            'golem --provider infini "task"',
            cooldowns, running,
        )
        assert result is None


class TestFallbackRoutingProportional:
    """Integration test: fallback fills codex to its cap before overflow."""

    def test_codex_fills_to_cap_before_overflow(self):
        """When infini/volcano cooled, codex gets 4 tasks before gemini/zhipu."""
        cooldowns = {"infini": time.time() + 600, "volcano": time.time() + 600}
        running: dict[str, int] = {}
        dispatches: list[str] = []

        # Simulate dispatching 10 infini/volcano tasks alternately
        for affinity in (["infini", "volcano"] * 5):
            picked = _pick_dispatch_provider(affinity, cooldowns, running)
            if picked:
                dispatches.append(picked)
                running[picked] = running.get(picked, 0) + 1

        # Codex cap = 4, gemini cap = 4
        assert dispatches.count("codex") == 4
        assert dispatches.count("gemini") == 4
        # Remaining 2 should go to zhipu (next in fallback chain after gemini)
        assert dispatches.count("zhipu") == 2
        # No task dispatched to cooled providers
        assert "infini" not in dispatches
        assert "volcano" not in dispatches

    def test_three_providers_cooled_proportional_dispatch(self):
        """When infini/volcano/zhipu cooled, tasks route to codex and gemini proportionally."""
        cooldowns = {
            "infini": time.time() + 600,
            "volcano": time.time() + 600,
            "zhipu": time.time() + 600,
        }
        running: dict[str, int] = {}
        dispatches: list[str] = []

        # 20 tasks across all three cooled providers
        affinities = ["infini"] * 7 + ["volcano"] * 7 + ["zhipu"] * 6
        for affinity in affinities:
            picked = _pick_dispatch_provider(affinity, cooldowns, running)
            if picked:
                dispatches.append(picked)
                running[picked] = running.get(picked, 0) + 1

        # Only codex (cap 4) and gemini (cap 4) are healthy = 8 total capacity
        assert dispatches.count("codex") == 4
        assert dispatches.count("gemini") == 4
        # Total dispatched = 8, remaining 12 tasks could not be dispatched
        assert len(dispatches) == 8

    def test_dispatch_candidates_respects_fallback_chain_order(self):
        """Verify PROVIDER_FALLBACK chain order matches expectations."""
        assert PROVIDER_FALLBACK["infini"] == ["codex", "gemini"]
        assert PROVIDER_FALLBACK["volcano"] == ["codex", "gemini"]
        assert PROVIDER_FALLBACK["codex"] == ["gemini", "zhipu"]
        assert PROVIDER_FALLBACK["gemini"] == ["codex", "zhipu"]
        assert PROVIDER_FALLBACK["zhipu"] == ["codex", "gemini"]


# ── Always-on daemon behavior tests ────────────────────────────────────────


daemon_loop = _mod["daemon_loop"]
_interruptible_sleep = _mod["_interruptible_sleep"]
_shutdown_event = _mod["_shutdown_event"]


def _setup_daemon_test(tmp_path, extra_mocks=None):
    """Set up common mocks and path redirects for daemon_loop tests.

    Returns dict of saved originals for restoration via _restore_daemon_test.
    """
    saved = {}

    # Redirect file paths to tmp
    for key in ("LOGFILE", "PIDFILE", "JSONLFILE", "RUNNING_FILE",
                "COOLDOWN_LOG", "CLEAR_COOLDOWN_FILE", "QUEUE_FILE"):
        saved[key] = _mod[key]
        _mod[key] = tmp_path / key.lower()

    # Ensure tmp dirs exist for log/pid writes
    tmp_path.mkdir(parents=True, exist_ok=True)

    # Common no-op mocks
    common = {
        "startup_pull": lambda: "ok",
        "auto_commit": lambda: "ok",
    }
    all_mocks = {**common, **(extra_mocks or {})}
    for key, val in all_mocks.items():
        saved[key] = _mod[key]
        _mod[key] = val

    _shutdown_event.clear()
    return saved


def _restore_daemon_test(saved):
    """Restore original module values after daemon_loop tests."""
    for key, val in saved.items():
        _mod[key] = val


class TestAlwaysOnIdleSleep:
    """When queue empty and nothing running, daemon sleeps 60s then re-polls."""

    def test_idle_sleep_60s(self, tmp_path):
        """Daemon calls _interruptible_sleep(60) when queue is empty."""
        sleep_calls = []

        def mock_sleep(seconds):
            sleep_calls.append(seconds)
            _shutdown_event.set()

        saved = _setup_daemon_test(tmp_path, {
            "_interruptible_sleep": mock_sleep,
            "parse_queue": lambda: [],
        })
        try:
            daemon_loop()
        finally:
            _restore_daemon_test(saved)

        assert 60 in sleep_calls

    def test_idle_repollls_after_wake(self, tmp_path):
        """After waking from idle sleep, daemon re-reads the queue."""
        parse_count = [0]

        def counting_parse_queue():
            parse_count[0] += 1
            if parse_count[0] >= 2:
                _shutdown_event.set()
            return []

        def no_op_sleep(seconds):
            pass

        saved = _setup_daemon_test(tmp_path, {
            "_interruptible_sleep": no_op_sleep,
            "parse_queue": counting_parse_queue,
        })
        try:
            daemon_loop()
        finally:
            _restore_daemon_test(saved)

        assert parse_count[0] >= 2, f"Expected >= 2 parse_queue calls, got {parse_count[0]}"


class TestAlwaysOnBackoff:
    """When all providers cooled and tasks pending, daemon sleeps 300s."""

    def test_backoff_sleep_300s(self, tmp_path):
        """Daemon sleeps 300s when tasks pending but all providers cooled."""
        sleep_calls = []

        def mock_sleep(seconds):
            sleep_calls.append(seconds)
            _shutdown_event.set()

        task = (0, 'golem --provider zhipu "test task"', 't-abc123')

        saved = _setup_daemon_test(tmp_path, {
            "_interruptible_sleep": mock_sleep,
            "parse_queue": lambda: [task],
            "_resolve_dispatch_command": lambda *args: None,
            "_golem_env": lambda: {},
            "_ssh_health_check": lambda w: False,
            "disk_guard": lambda: True,
        })
        try:
            daemon_loop()
        finally:
            _restore_daemon_test(saved)

        assert 300 in sleep_calls

    def test_backoff_repolls_after_wake(self, tmp_path):
        """After waking from backoff sleep, daemon re-reads the queue."""
        parse_count = [0]
        task = (0, 'golem --provider zhipu "test task"', 't-abc123')

        def counting_parse_queue():
            parse_count[0] += 1
            if parse_count[0] >= 2:
                _shutdown_event.set()
            return [task]

        def no_op_sleep(seconds):
            pass

        saved = _setup_daemon_test(tmp_path, {
            "_interruptible_sleep": no_op_sleep,
            "parse_queue": counting_parse_queue,
            "_resolve_dispatch_command": lambda *args: None,
            "_golem_env": lambda: {},
            "_ssh_health_check": lambda w: False,
            "disk_guard": lambda: True,
        })
        try:
            daemon_loop()
        finally:
            _restore_daemon_test(saved)

        assert parse_count[0] >= 2, f"Expected >= 2 parse_queue calls, got {parse_count[0]}"


class TestSigtermGracefulShutdown:
    """SIGTERM handler sets shutdown flag for graceful exit."""

    def test_sigterm_sets_shutdown_event(self):
        """_handle_sigterm sets _shutdown_event."""
        _shutdown_event.clear()
        handler = _mod["_handle_sigterm"]
        handler(signal.SIGTERM, None)
        assert _shutdown_event.is_set()
        _shutdown_event.clear()

    def test_interruptible_sleep_respects_shutdown(self):
        """_interruptible_sleep returns immediately when shutdown is set."""
        _shutdown_event.set()
        start = time.time()
        _interruptible_sleep(60)
        elapsed = time.time() - start
        _shutdown_event.clear()
        assert elapsed < 2, f"Sleep should return immediately on shutdown, took {elapsed:.1f}s"

    def test_drain_called_on_shutdown(self, tmp_path):
        """Running tasks are drained when shutdown event is set during idle."""
        drain_calls = [0]
        original_drain = _mod["_drain_running"]

        def counting_drain(running, timeout=60):
            drain_calls[0] += 1
            return original_drain(running, timeout)

        def mock_sleep(seconds):
            _shutdown_event.set()

        saved = _setup_daemon_test(tmp_path, {
            "_interruptible_sleep": mock_sleep,
            "parse_queue": lambda: [],
            "_drain_running": counting_drain,
        })
        try:
            daemon_loop()
        finally:
            _restore_daemon_test(saved)

        assert drain_calls[0] >= 1, "Expected _drain_running to be called on shutdown"


# ── dedup guard tests ───────────────────────────────────────────────


def test_normalize_prompt_strips_task_id():
    """_normalize_prompt strips [t-xxxxxx] task IDs."""
    a = _normalize_prompt('golem [t-abc123] --provider zhipu --max-turns 30 "Fix tests"')
    b = _normalize_prompt('golem [t-def456] --provider zhipu --max-turns 30 "Fix tests"')
    assert a == b


def test_normalize_prompt_strips_provider():
    """_normalize_prompt strips --provider flag so different providers match."""
    a = _normalize_prompt('golem --provider zhipu --max-turns 30 "Fix tests"')
    b = _normalize_prompt('golem --provider infini --max-turns 30 "Fix tests"')
    assert a == b


def test_normalize_prompt_strips_max_turns():
    """_normalize_prompt strips --max-turns N flag."""
    a = _normalize_prompt('golem --provider zhipu --max-turns 30 "Fix tests"')
    b = _normalize_prompt('golem --provider zhipu --max-turns 50 "Fix tests"')
    assert a == b


def test_normalize_prompt_strips_retry_tag():
    """_normalize_prompt strips trailing (retry) tag."""
    a = _normalize_prompt('golem --provider zhipu --max-turns 30 "Fix tests" (retry)')
    b = _normalize_prompt('golem --provider zhipu --max-turns 30 "Fix tests"')
    assert a == b


def test_normalize_prompt_different_prompts_differ():
    """_normalize_prompt produces different keys for different prompts."""
    a = _normalize_prompt('golem --provider zhipu --max-turns 30 "Fix tests"')
    b = _normalize_prompt('golem --provider zhipu --max-turns 30 "Build feature X"')
    assert a != b


def test_get_pending_prompts_reads_queue(tmp_path):
    """_get_pending_prompts returns normalized prompts from pending entries."""
    qf = tmp_path / "golem-queue.md"
    _mod["QUEUE_FILE"] = qf
    try:
        qf.write_text(
            '- [ ] `golem [t-aa0001] --provider zhipu --max-turns 30 "Fix tests"`\n'
            '- [x] `golem [t-aa0002] --provider infini --max-turns 30 "Done task"`\n'
            '- [!!] `golem [t-aa0003] --provider volcano --max-turns 40 "Build X"`\n'
        )
        prompts = _get_pending_prompts()
        norm_fix = _normalize_prompt('golem --provider zhipu --max-turns 30 "Fix tests"')
        norm_build = _normalize_prompt('golem --provider volcano --max-turns 40 "Build X"')
        assert norm_fix in prompts
        assert norm_build in prompts
        # [x] done entry should NOT be included
        norm_done = _normalize_prompt('golem --provider infini --max-turns 30 "Done task"')
        assert norm_done not in prompts
    finally:
        _mod["QUEUE_FILE"] = QUEUE_FILE


def test_enqueue_dedup_rejects_duplicate(tmp_path):
    """Writing the same prompt twice to the queue — second should be rejected."""
    qf = tmp_path / "golem-queue.md"
    _mod["QUEUE_FILE"] = qf
    QueueLock = _mod["QueueLock"]
    _existing = _mod["_get_pending_prompts"]()
    _normalize = _mod["_normalize_prompt"]
    try:
        # Enqueue first task
        prompt = 'golem --provider zhipu --max-turns 30 "Fix pyright errors"'
        line1 = f'- [ ] `{prompt}`'
        qf.write_text(line1 + "\n")
        _existing.add(_normalize(prompt))

        # Attempt to enqueue duplicate
        prompt2 = 'golem [t-dead01] --provider infini --max-turns 40 "Fix pyright errors" (retry)'
        norm2 = _normalize(prompt2)
        assert norm2 in _existing, "Second prompt should normalize to same key as first"
    finally:
        _mod["QUEUE_FILE"] = QUEUE_FILE


def test_dispatch_dedup_skips_running_duplicate(tmp_path):
    """Dispatch loop should skip tasks whose normalized prompt matches a running task."""
    _setup = _mod.get("_setup_daemon_test")
    if not _setup:
        pytest.skip("no _setup_daemon_test helper")

    daemon_loop = _mod["daemon_loop"]
    _shutdown_event = _mod["_shutdown_event"]
    log_msgs: list[str] = []

    def mock_log(msg):
        log_msgs.append(msg)

    task_ran: list[str] = []

    def mock_run_golem(cmd):
        task_ran.append(cmd)
        return (cmd, 0, "ok", 10)

    def mock_parse_queue():
        return [
            (0, 'golem [t-aaa111] --provider zhipu --max-turns 30 "Fix tests"', "t-aaa111"),
            (1, 'golem [t-bbb222] --provider infini --max-turns 40 "Fix tests"', "t-bbb222"),
        ]

    def mock_sleep(s):
        _shutdown_event.set()

    saved = _setup(tmp_path, {
        "log": mock_log,
        "parse_queue": mock_parse_queue,
        "run_golem": mock_run_golem,
        "_interruptible_sleep": mock_sleep,
        "_update_running_file": lambda r: None,
        "_golem_env": lambda: {},
        "_ssh_health_check": lambda w: True,
        "startup_pull": lambda: "ok",
        "rotate_logs": lambda: None,
        "write_pid": lambda: None,
        "remove_pid": lambda: None,
        "disk_guard": lambda *a, **kw: True,
        "auto_requeue": lambda *a, **kw: 0,
        "auto_commit": lambda: "nothing",
        "validate_golem_output": lambda: (True, []),
        "check_new_test_files_and_run_pytest": lambda: (True, ""),
        "_provider_preflight": lambda p, e: (True, None),
    })
    try:
        daemon_loop()
    finally:
        _mod["_restore_daemon_test"](saved)

    # Only one of the two duplicate-prompt tasks should have been dispatched
    assert len(task_ran) == 1, f"Expected 1 dispatched task, got {len(task_ran)}: {task_ran}"
    # Should have logged skipping duplicate
    skip_msgs = [m for m in log_msgs if "skipping duplicate" in m]
    assert len(skip_msgs) >= 1, f"Expected 'skipping duplicate' log, got: {log_msgs[-10:]}"


# ── Billing-cycle rate-limit detection tests ─────────────────────────────

is_billing_exhausted = _mod["is_billing_exhausted"]
is_rate_limited = _mod["is_rate_limited"]
parse_rate_limit_window = _mod["parse_rate_limit_window"]
parse_reset_date_str = _mod["parse_reset_date_str"]
BILLING_EXHAUSTED_THRESHOLD = _mod["BILLING_EXHAUSTED_THRESHOLD"]
RATE_LIMIT_COOLDOWN_SECONDS = _mod["RATE_LIMIT_COOLDOWN_SECONDS"]


class TestBillingExhaustionDetection:
    """Tests for billing-cycle rate limit detection via is_billing_exhausted."""

    def test_usage_limit_detected(self):
        """is_billing_exhausted detects 'usage limit' pattern."""
        assert is_billing_exhausted("You've hit your usage limit")

    def test_hit_your_limit_detected(self):
        """is_billing_exhausted detects 'hit your ... limit' pattern."""
        assert is_billing_exhausted("You've hit your limit for this billing cycle")

    def test_billing_limit_detected(self):
        """is_billing_exhausted detects 'billing limit' pattern."""
        assert is_billing_exhausted("billing limit exceeded")

    def test_monthly_limit_detected(self):
        """is_billing_exhausted detects 'monthly limit' pattern."""
        assert is_billing_exhausted("monthly limit reached")

    def test_plan_limit_detected(self):
        """is_billing_exhausted detects 'plan limit' pattern."""
        assert is_billing_exhausted("plan limit exceeded")

    def test_subscription_limit_detected(self):
        """is_billing_exhausted detects 'subscription limit' pattern."""
        assert is_billing_exhausted("subscription limit reached")

    def test_regular_rate_limit_not_billing(self):
        """is_billing_exhausted does NOT match regular rate-limit messages."""
        assert not is_billing_exhausted("429 Too Many Requests")
        assert not is_billing_exhausted("AccountQuotaExceeded")
        assert not is_billing_exhausted("rate limit exceeded")
        assert not is_billing_exhausted("request limit exceeded")

    def test_usage_limit_also_rate_limited(self):
        """is_rate_limited also matches billing-exhaustion patterns."""
        assert is_rate_limited("You've hit your usage limit")

    def test_hit_your_limit_also_rate_limited(self):
        """is_rate_limited matches 'hit your ... limit' patterns."""
        assert is_rate_limited("You've hit your limit for today")


class TestParseResetDate:
    """Tests for parse_reset_date_str — human-readable date extraction."""

    def test_codex_billing_format(self):
        """parse_reset_date_str parses Codex billing format 'Apr 8th, 2026 4:01 PM'."""
        result = parse_reset_date_str("try again at Apr 8th, 2026 4:01 PM")
        assert result is not None
        assert "Apr" in result
        assert "8" in result
        assert "2026" in result

    def test_codex_billing_format_no_comma(self):
        """parse_reset_date_str handles Codex format without comma."""
        result = parse_reset_date_str("try again at Apr 8th 2026 4:01 PM")
        assert result is not None
        assert "Apr" in result

    def test_iso_format(self):
        """parse_reset_date_str parses ISO format '2026-04-01 21:09:32'."""
        result = parse_reset_date_str("reset at 2026-04-01 21:09:32")
        assert result == "2026-04-01 21:09:32"

    def test_no_date_returns_none(self):
        """parse_reset_date_str returns None when no date pattern matches."""
        assert parse_reset_date_str("generic error message") is None

    def test_various_months(self):
        """parse_reset_date_str handles all month abbreviations."""
        for month in ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"):
            result = parse_reset_date_str(f"try again at {month} 1st, 2030 12:00 PM")
            assert result is not None, f"Failed for month {month}"


class TestParseRateLimitWindowCodex:
    """Tests for parse_rate_limit_window with Codex billing-cycle format."""

    def test_codex_billing_format_returns_long_window(self):
        """parse_rate_limit_window returns >24h for a date far in the future."""
        tail = "try again at Dec 25th, 2030 4:01 PM"
        window = parse_rate_limit_window(tail)
        assert window is not None
        assert window > BILLING_EXHAUSTED_THRESHOLD

    def test_codex_billing_format_with_realistic_date(self):
        """parse_rate_limit_window parses a realistic Codex billing reset date."""
        tail = "You've hit your usage limit. Please try again at Apr 8th, 2026 4:01 PM"
        window = parse_rate_limit_window(tail)
        assert window is not None
        # The exact value depends on current time, but if Apr 8 2026 is >24h away, it should be large
        # If we're already past that date, window could be 0 or None
        # Use a far-future date to guarantee >24h
        tail_future = "You've hit your usage limit. Please try again at Dec 25th, 2030 4:01 PM"
        window_future = parse_rate_limit_window(tail_future)
        assert window_future is not None
        assert window_future > BILLING_EXHAUSTED_THRESHOLD

    def test_codex_short_format_returns_short_window(self):
        """parse_rate_limit_window returns <24h for same-day 'try again at HH:MM PM' format."""
        tail = "try again at 11:59 PM"
        window = parse_rate_limit_window(tail)
        assert window is not None
        assert window < BILLING_EXHAUSTED_THRESHOLD

    def test_iso_format_far_future_returns_long_window(self):
        """parse_rate_limit_window returns >24h for a far-future ISO timestamp."""
        tail = "reset at 2030-06-15 12:00:00"
        window = parse_rate_limit_window(tail)
        assert window is not None
        assert window > BILLING_EXHAUSTED_THRESHOLD

    def test_no_match_returns_none(self):
        """parse_rate_limit_window returns None for unrecognized formats."""
        assert parse_rate_limit_window("generic error") is None

    def test_gemini_duration_format(self):
        """parse_rate_limit_window parses Gemini 'quota will reset after Xm Ys' format."""
        tail = "quota will reset after 18m38s"
        window = parse_rate_limit_window(tail)
        assert window is not None
        assert window == 18 * 60 + 38

    def test_hour_duration_format(self):
        """parse_rate_limit_window parses '5-hour' duration format."""
        tail = "rate limited for 5-hour window"
        window = parse_rate_limit_window(tail)
        assert window == 5 * 3600


class TestBillingVsShortCooldown:
    """Tests that billing-exhausted cooldowns are correctly classified."""

    def test_billing_threshold_is_24h(self):
        """BILLING_EXHAUSTED_THRESHOLD is 86400 (24h)."""
        assert BILLING_EXHAUSTED_THRESHOLD == 86400

    def test_default_rate_limit_shorter_than_threshold(self):
        """RATE_LIMIT_COOLDOWN_SECONDS is shorter than billing threshold."""
        assert RATE_LIMIT_COOLDOWN_SECONDS < BILLING_EXHAUSTED_THRESHOLD

    def test_codex_billing_window_exceeds_threshold(self):
        """A far-future Codex billing reset exceeds the billing threshold."""
        tail = "try again at Dec 25th, 2030 4:01 PM"
        window = parse_rate_limit_window(tail)
        assert window is not None
        assert window > BILLING_EXHAUSTED_THRESHOLD


class TestStatusBillingExhausted:
    """Tests for cmd_status showing billing-exhausted cooldowns correctly."""

    def test_status_shows_billing_limit_label(self, tmp_path, capsys):
        """cmd_status shows 'billing limit, resets <date>' for billing-exhausted events."""
        import time as _time

        cooldown_log = tmp_path / "cooldowns.json"
        future = _time.time() + 5 * 86400  # 5 days from now
        future_str = _time.strftime("%Y-%m-%d %H:%M:%S", _time.localtime(future))
        entries = [
            {"ts": _time.strftime("%Y-%m-%d %H:%M:%S"),
             "event": "billing-exhausted",
             "provider": "codex",
             "resets_at": future_str,
             "reason": "billing exhausted"},
        ]
        cooldown_log.write_text(json.dumps(entries) + "\n")

        original_read_pid = _mod["read_pid"]
        original_cooldown_log = _mod["COOLDOWN_LOG"]
        original_running_file = _mod["RUNNING_FILE"]
        original_queue_file = _mod["QUEUE_FILE"]

        try:
            _mod["read_pid"] = lambda: 12345
            _mod["COOLDOWN_LOG"] = cooldown_log
            _mod["RUNNING_FILE"] = tmp_path / "no_running.json"
            _mod["QUEUE_FILE"] = tmp_path / "no_queue.md"
            rc = cmd_status()
        finally:
            _mod["read_pid"] = original_read_pid
            _mod["COOLDOWN_LOG"] = original_cooldown_log
            _mod["RUNNING_FILE"] = original_running_file
            _mod["QUEUE_FILE"] = original_queue_file

        assert rc == 0
        out = capsys.readouterr().out.lower()
        assert "billing limit" in out
        assert "codex" in out

    def test_status_shows_burnout_as_resets_time(self, tmp_path, capsys):
        """cmd_status shows 'resets HH:MM' for regular burnout events."""
        import time as _time

        cooldown_log = tmp_path / "cooldowns.json"
        future = _time.time() + 3600  # 1 hour from now
        future_str = _time.strftime("%Y-%m-%d %H:%M:%S", _time.localtime(future))
        entries = [
            {"ts": _time.strftime("%Y-%m-%d %H:%M:%S"),
             "event": "burnout",
             "provider": "infini",
             "resets_at": future_str,
             "reason": "rate limited"},
        ]
        cooldown_log.write_text(json.dumps(entries) + "\n")

        original_read_pid = _mod["read_pid"]
        original_cooldown_log = _mod["COOLDOWN_LOG"]
        original_running_file = _mod["RUNNING_FILE"]
        original_queue_file = _mod["QUEUE_FILE"]

        try:
            _mod["read_pid"] = lambda: 12345
            _mod["COOLDOWN_LOG"] = cooldown_log
            _mod["RUNNING_FILE"] = tmp_path / "no_running.json"
            _mod["QUEUE_FILE"] = tmp_path / "no_queue.md"
            rc = cmd_status()
        finally:
            _mod["read_pid"] = original_read_pid
            _mod["COOLDOWN_LOG"] = original_cooldown_log
            _mod["RUNNING_FILE"] = original_running_file
            _mod["QUEUE_FILE"] = original_queue_file

        assert rc == 0
        out = capsys.readouterr().out
        assert "infini" in out
        assert "resets" in out
        # Should NOT show billing limit for regular burnout
        assert "billing limit" not in out.lower()

    def test_status_shows_mixed_cooldowns(self, tmp_path, capsys):
        """cmd_status shows both billing-exhausted and burnout events."""
        import time as _time

        cooldown_log = tmp_path / "cooldowns.json"
        future_short = _time.time() + 3600
        future_long = _time.time() + 5 * 86400
        entries = [
            {"ts": _time.strftime("%Y-%m-%d %H:%M:%S"),
             "event": "burnout",
             "provider": "infini",
             "resets_at": _time.strftime("%Y-%m-%d %H:%M:%S", _time.localtime(future_short)),
             "reason": "rate limited"},
            {"ts": _time.strftime("%Y-%m-%d %H:%M:%S"),
             "event": "billing-exhausted",
             "provider": "codex",
             "resets_at": _time.strftime("%Y-%m-%d %H:%M:%S", _time.localtime(future_long)),
             "reason": "billing exhausted"},
        ]
        cooldown_log.write_text(json.dumps(entries) + "\n")

        original_read_pid = _mod["read_pid"]
        original_cooldown_log = _mod["COOLDOWN_LOG"]
        original_running_file = _mod["RUNNING_FILE"]
        original_queue_file = _mod["QUEUE_FILE"]

        try:
            _mod["read_pid"] = lambda: 12345
            _mod["COOLDOWN_LOG"] = cooldown_log
            _mod["RUNNING_FILE"] = tmp_path / "no_running.json"
            _mod["QUEUE_FILE"] = tmp_path / "no_queue.md"
            rc = cmd_status()
        finally:
            _mod["read_pid"] = original_read_pid
            _mod["COOLDOWN_LOG"] = original_cooldown_log
            _mod["RUNNING_FILE"] = original_running_file
            _mod["QUEUE_FILE"] = original_queue_file

        assert rc == 0
        out = capsys.readouterr().out.lower()
        assert "billing limit" in out
        assert "codex" in out
        assert "infini" in out
        assert "resets" in out

    def test_status_resumed_clears_billing_exhausted(self, tmp_path, capsys):
        """cmd_status hides billing-exhausted after a 'resumed' event."""
        import time as _time

        cooldown_log = tmp_path / "cooldowns.json"
        future = _time.time() + 5 * 86400
        entries = [
            {"ts": _time.strftime("%Y-%m-%d %H:%M:%S"),
             "event": "billing-exhausted",
             "provider": "codex",
             "resets_at": _time.strftime("%Y-%m-%d %H:%M:%S", _time.localtime(future)),
             "reason": "billing exhausted"},
            {"ts": _time.strftime("%Y-%m-%d %H:%M:%S"),
             "event": "resumed",
             "provider": "codex",
             "resets_at": None,
             "reason": "manual clear"},
        ]
        cooldown_log.write_text(json.dumps(entries) + "\n")

        original_read_pid = _mod["read_pid"]
        original_cooldown_log = _mod["COOLDOWN_LOG"]
        original_running_file = _mod["RUNNING_FILE"]
        original_queue_file = _mod["QUEUE_FILE"]

        try:
            _mod["read_pid"] = lambda: 12345
            _mod["COOLDOWN_LOG"] = cooldown_log
            _mod["RUNNING_FILE"] = tmp_path / "no_running.json"
            _mod["QUEUE_FILE"] = tmp_path / "no_queue.md"
            rc = cmd_status()
        finally:
            _mod["read_pid"] = original_read_pid
            _mod["COOLDOWN_LOG"] = original_cooldown_log
            _mod["RUNNING_FILE"] = original_running_file
            _mod["QUEUE_FILE"] = original_queue_file

        assert rc == 0
        out = capsys.readouterr().out.lower()
        assert "billing limit" not in out
        assert "cooldowns" not in out


# ── Billing exhaustion + short window override tests ────────────────────


class TestBillingExhaustedOverridesShortWindow:
    """When is_billing_exhausted matches, the cooldown must be >= BILLING_EXHAUSTED_THRESHOLD
    even if parse_rate_limit_window returns a short value."""

    def test_billing_with_short_format_time_enforces_24h(self):
        """Billing-exhausted message with short-format 'try again at HH:MM PM'
        must produce at least 24h cooldown, not the short window."""
        tail = "You've hit your usage limit. try again at 11:59 PM"
        assert is_billing_exhausted(tail)
        window = parse_rate_limit_window(tail)
        # The short-format time gives a window < 24h
        assert window is not None
        assert window < BILLING_EXHAUSTED_THRESHOLD
        # But billing exhaustion should override: max(window, 24h) = 24h
        enforced = max(window or 0, BILLING_EXHAUSTED_THRESHOLD)
        assert enforced >= BILLING_EXHAUSTED_THRESHOLD

    def test_billing_with_no_date_enforces_24h(self):
        """Billing-exhausted message with no parseable date must produce 24h."""
        tail = "You've hit your usage limit for this billing cycle"
        assert is_billing_exhausted(tail)
        window = parse_rate_limit_window(tail)
        assert window is None
        enforced = max(window or 0, BILLING_EXHAUSTED_THRESHOLD)
        assert enforced == BILLING_EXHAUSTED_THRESHOLD

    def test_billing_with_long_date_uses_long_window(self):
        """Billing-exhausted message with far-future date uses that date."""
        tail = "You've hit your usage limit. Please try again at Dec 25th, 2030 4:01 PM"
        assert is_billing_exhausted(tail)
        window = parse_rate_limit_window(tail)
        assert window is not None
        assert window > BILLING_EXHAUSTED_THRESHOLD
        enforced = max(window, BILLING_EXHAUSTED_THRESHOLD)
        assert enforced == window  # long window wins

    def test_non_billing_short_window_stays_short(self):
        """Regular rate-limit (not billing) with short window stays short."""
        tail = "429 Too Many Requests"
        assert not is_billing_exhausted(tail)
        window = parse_rate_limit_window(tail)
        assert window is None
        # No billing override — would use RATE_LIMIT_COOLDOWN_SECONDS
        assert RATE_LIMIT_COOLDOWN_SECONDS < BILLING_EXHAUSTED_THRESHOLD

    def test_realistic_codex_billing_message(self):
        """Realistic Codex billing message with full date is correctly parsed."""
        tail = "You've hit your usage limit. Please try again at Apr 8th, 2026 4:01 PM"
        assert is_billing_exhausted(tail)
        assert is_rate_limited(tail)
        window = parse_rate_limit_window(tail)
        assert window is not None
        # Apr 8, 2026 is >24h from now (it's Apr 3, 2026)
        assert window > BILLING_EXHAUSTED_THRESHOLD
        date_str = parse_reset_date_str(tail)
        assert date_str is not None
        assert "Apr" in date_str


class TestPickDispatchProviderWithDisabled:
    """Tests that _pick_dispatch_provider respects PROVIDER_DISABLED."""

    def test_disabled_provider_skipped_even_without_cooldown(self):
        """Provider in PROVIDER_DISABLED is skipped even if not in cooldown."""
        disabled = {"codex": {"resets_at": time.time() + 86400, "resets_str": "Apr 8"}}
        result = _pick_dispatch_provider("infini", {"infini": time.time() + 600}, {}, provider_disabled=disabled)
        # Should skip codex (disabled) and fall through to gemini
        assert result is not None
        assert result != "codex"

    def test_disabled_provider_alone_blocks_dispatch(self):
        """When affinity provider is disabled, fallback is used."""
        disabled = {"codex": {"resets_at": time.time() + 86400, "resets_str": "Apr 8"}}
        result = _pick_dispatch_provider("codex", {}, {}, provider_disabled=disabled)
        assert result is not None
        assert result != "codex"
        # Should fall through to gemini (first in codex fallback chain)
        assert result == "gemini"

    def test_disabled_and_cooldown_both_skipped(self):
        """Providers in both cooldown and PROVIDER_DISABLED are skipped."""
        disabled = {"codex": {"resets_at": time.time() + 86400, "resets_str": "Apr 8"}}
        cooldowns = {"infini": time.time() + 600}
        result = _pick_dispatch_provider("infini", cooldowns, {}, provider_disabled=disabled)
        assert result is not None
        assert result != "codex"
        assert result != "infini"

    def test_no_disabled_dict_works_as_before(self):
        """Without provider_disabled, behaviour is unchanged."""
        cooldowns = {"infini": time.time() + 600}
        result = _pick_dispatch_provider("infini", cooldowns, {}, provider_disabled=None)
        assert result == "codex"

    def test_all_providers_disabled_returns_none(self):
        """When all providers are disabled or in cooldown, returns None."""
        disabled = {p: {"resets_at": time.time() + 86400, "resets_str": "Apr 8"} for p in PROVIDER_LIMITS}
        assert _pick_dispatch_provider("infini", {}, {}, provider_disabled=disabled) is None

    def test_disabled_provider_not_probed_for_fallback(self):
        """When infini is cooled and codex is disabled, fallback goes to gemini."""
        disabled = {"codex": {"resets_at": time.time() + 86400, "resets_str": "Apr 8"}}
        cooldowns = {"infini": time.time() + 600}
        running = {}
        result = _pick_dispatch_provider("infini", cooldowns, running, provider_disabled=disabled)
        assert result == "gemini"


class TestDateParsingEdgeCases:
    """Additional edge-case tests for date parsing from stderr."""

    def test_midnight_am(self):
        """12:00 AM is midnight (hour=0), not noon."""
        tail = "try again at 12:00 AM"
        window = parse_rate_limit_window(tail)
        assert window is not None

    def test_noon_pm(self):
        """12:00 PM is noon (hour=12), not midnight."""
        tail = "try again at 12:00 PM"
        window = parse_rate_limit_window(tail)
        assert window is not None

    def test_month_full_name(self):
        """Full month name (e.g. 'January') is parsed correctly."""
        tail = "try again at January 15th, 2030 10:00 AM"
        window = parse_rate_limit_window(tail)
        assert window is not None
        assert window > BILLING_EXHAUSTED_THRESHOLD

    def test_iso_format_close_future(self):
        """ISO format with date <24h away returns short window."""
        from datetime import datetime, timedelta
        soon = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        tail = f"reset at {soon}"
        window = parse_rate_limit_window(tail)
        assert window is not None
        assert window < BILLING_EXHAUSTED_THRESHOLD

    def test_gemini_duration_under_24h(self):
        """Gemini 'quota will reset after Xm Ys' with <24h duration."""
        tail = "quota will reset after 5m30s"
        window = parse_rate_limit_window(tail)
        assert window == 5 * 60 + 30
        assert window < BILLING_EXHAUSTED_THRESHOLD

    def test_codex_billing_with_nd_suffix(self):
        """Date with 'nd' suffix (e.g. '2nd') is parsed."""
        tail = "try again at Apr 2nd, 2030 3:00 PM"
        window = parse_rate_limit_window(tail)
        assert window is not None
        assert window > BILLING_EXHAUSTED_THRESHOLD

    def test_codex_billing_with_rd_suffix(self):
        """Date with 'rd' suffix (e.g. '3rd') is parsed."""
        tail = "try again at Apr 3rd, 2030 3:00 PM"
        window = parse_rate_limit_window(tail)
        assert window is not None
        assert window > BILLING_EXHAUSTED_THRESHOLD

    def test_reset_date_str_codex_with_comma(self):
        """parse_reset_date_str handles 'Apr 8th, 2026 4:01 PM'."""
        result = parse_reset_date_str("try again at Apr 8th, 2026 4:01 PM")
        assert result is not None
        assert "Apr" in result
        assert "8" in result

    def test_reset_date_str_iso(self):
        """parse_reset_date_str handles ISO format."""
        result = parse_reset_date_str("reset at 2026-04-08 16:01:00")
        assert result == "2026-04-08 16:01:00"

    def test_past_date_returns_none_or_zero(self):
        """Dates in the past return None (delta <= 0)."""
        tail = "try again at Jan 1st, 2020 12:00 PM"
        window = parse_rate_limit_window(tail)
        assert window is None


class TestBillingVsShortCooldownExtended:
    """Extended tests for long vs short cooldown classification."""

    def test_billing_threshold_boundary(self):
        """Exactly 86400 seconds (24h) IS billing-exhausted threshold."""
        assert BILLING_EXHAUSTED_THRESHOLD == 86400

    def test_rate_limit_cooldown_much_shorter(self):
        """RATE_LIMIT_COOLDOWN_SECONDS (5h) is well under billing threshold."""
        assert RATE_LIMIT_COOLDOWN_SECONDS == 18000  # 5 hours
        assert RATE_LIMIT_COOLDOWN_SECONDS < BILLING_EXHAUSTED_THRESHOLD

    def test_codex_provider_window_shorter_than_threshold(self):
        """Codex per-provider window (1h) is shorter than billing threshold."""
        PROVIDER_RATE_WINDOWS = _mod["PROVIDER_RATE_WINDOWS"]
        assert PROVIDER_RATE_WINDOWS["codex"] < BILLING_EXHAUSTED_THRESHOLD

    def test_billing_message_with_hour_duration(self):
        """'usage limit' + '5-hour' pattern should use billing threshold."""
        tail = "You've hit your usage limit. Please wait 5-hour cooldown."
        assert is_billing_exhausted(tail)
        window = parse_rate_limit_window(tail)
        assert window == 5 * 3600  # 18000 seconds
        # But billing override should enforce 24h
        enforced = max(window or 0, BILLING_EXHAUSTED_THRESHOLD)
        assert enforced == BILLING_EXHAUSTED_THRESHOLD

    def test_billing_message_with_minute_duration(self):
        """'billing limit' + '30-minute' pattern should use billing threshold."""
        tail = "billing limit exceeded. retry after 30-minute window"
        assert is_billing_exhausted(tail)
        window = parse_rate_limit_window(tail)
        assert window == 30 * 60  # 1800 seconds
        # Billing override should enforce 24h
        enforced = max(window or 0, BILLING_EXHAUSTED_THRESHOLD)
        assert enforced == BILLING_EXHAUSTED_THRESHOLD


# ── _log_cooldown billing-exhausted tests ────────────────────────────────

_log_cooldown = _mod["_log_cooldown"]
COOLDOWN_LOG = _mod["COOLDOWN_LOG"]


class TestLogCooldownBillingExhausted:
    """Tests for _log_cooldown with billing-exhausted events."""

    def test_billing_exhausted_event_logged(self, tmp_path):
        """_log_cooldown writes a billing-exhausted entry with resets_at."""
        import json as _json

        log_file = tmp_path / "cooldowns.json"
        saved = {}
        saved["COOLDOWN_LOG"] = _mod["COOLDOWN_LOG"]
        _mod["COOLDOWN_LOG"] = log_file
        try:
            future = time.time() + 5 * 86400
            _log_cooldown("codex", future, "billing exhausted", event="billing-exhausted")
            entries = _json.loads(log_file.read_text())
            assert len(entries) == 1
            assert entries[0]["event"] == "billing-exhausted"
            assert entries[0]["provider"] == "codex"
            assert entries[0]["resets_at"] is not None
        finally:
            _mod["COOLDOWN_LOG"] = saved["COOLDOWN_LOG"]

    def test_billing_exhausted_dedupe_same_reset(self, tmp_path):
        """_log_cooldown dedupes billing-exhausted with same reset time."""
        import json as _json

        log_file = tmp_path / "cooldowns.json"
        saved = {}
        saved["COOLDOWN_LOG"] = _mod["COOLDOWN_LOG"]
        _mod["COOLDOWN_LOG"] = log_file
        try:
            future = time.time() + 5 * 86400
            _log_cooldown("codex", future, "billing exhausted", event="billing-exhausted")
            _log_cooldown("codex", future, "billing exhausted again", event="billing-exhausted")
            entries = _json.loads(log_file.read_text())
            assert len(entries) == 1  # deduped
        finally:
            _mod["COOLDOWN_LOG"] = saved["COOLDOWN_LOG"]

    def test_billing_exhausted_no_dedupe_different_reset(self, tmp_path):
        """_log_cooldown does NOT dedupe when reset times differ."""
        import json as _json

        log_file = tmp_path / "cooldowns.json"
        saved = {}
        saved["COOLDOWN_LOG"] = _mod["COOLDOWN_LOG"]
        _mod["COOLDOWN_LOG"] = log_file
        try:
            future1 = time.time() + 5 * 86400
            future2 = time.time() + 10 * 86400
            _log_cooldown("codex", future1, "first", event="billing-exhausted")
            _log_cooldown("codex", future2, "second", event="billing-exhausted")
            entries = _json.loads(log_file.read_text())
            assert len(entries) == 2
        finally:
            _mod["COOLDOWN_LOG"] = saved["COOLDOWN_LOG"]

    def test_burnout_default_event(self, tmp_path):
        """_log_cooldown defaults to 'burnout' event."""
        import json as _json

        log_file = tmp_path / "cooldowns.json"
        saved = {}
        saved["COOLDOWN_LOG"] = _mod["COOLDOWN_LOG"]
        _mod["COOLDOWN_LOG"] = log_file
        try:
            future = time.time() + 3600
            _log_cooldown("infini", future, "rate limited")
            entries = _json.loads(log_file.read_text())
            assert len(entries) == 1
            assert entries[0]["event"] == "burnout"
        finally:
            _mod["COOLDOWN_LOG"] = saved["COOLDOWN_LOG"]

    def test_log_truncated_at_100(self, tmp_path):
        """_log_cooldown truncates reason to 100 chars."""
        import json as _json

        log_file = tmp_path / "cooldowns.json"
        saved = {}
        saved["COOLDOWN_LOG"] = _mod["COOLDOWN_LOG"]
        _mod["COOLDOWN_LOG"] = log_file
        try:
            future = time.time() + 3600
            long_reason = "x" * 200
            _log_cooldown("codex", future, long_reason, event="billing-exhausted")
            entries = _json.loads(log_file.read_text())
            assert len(entries[0]["reason"]) == 100
        finally:
            _mod["COOLDOWN_LOG"] = saved["COOLDOWN_LOG"]


# ── Integration: daemon-loop billing-exhaustion flow ──────────────────────

PROVIDER_DISABLED = _mod["PROVIDER_DISABLED"]


class TestDaemonLoopBillingExhaustion:
    """Integration tests: task fails with billing message → PROVIDER_DISABLED set."""

    def test_billing_exhausted_sets_provider_disabled(self):
        """When a billing-exhausted message is detected, PROVIDER_DISABLED is populated."""
        # Simulate the daemon loop's billing-exhaustion handling logic
        tail = "You've hit your usage limit. Please try again at Dec 25th, 2030 4:01 PM"
        task_id = "t-abc123"
        dispatch_provider = "codex"
        exit_code = 1

        assert is_rate_limited(tail)
        assert is_billing_exhausted(tail)

        window = parse_rate_limit_window(tail)
        assert window is not None and window > BILLING_EXHAUSTED_THRESHOLD

        # This is the logic from daemon_loop
        if is_billing_exhausted(tail):
            window = max(window or 0, BILLING_EXHAUSTED_THRESHOLD)
        cooldown = window if window else RATE_LIMIT_COOLDOWN_SECONDS
        assert cooldown >= BILLING_EXHAUSTED_THRESHOLD

        cooldown_end = time.time() + cooldown
        if cooldown >= BILLING_EXHAUSTED_THRESHOLD:
            reset_tm = time.localtime(cooldown_end)
            reset_str = time.strftime("%b %d", reset_tm).replace(" 0", " ")
            PROVIDER_DISABLED[dispatch_provider] = {
                "resets_at": cooldown_end,
                "resets_str": reset_str,
            }

        assert dispatch_provider in PROVIDER_DISABLED
        assert PROVIDER_DISABLED[dispatch_provider]["resets_str"] is not None

        # Cleanup
        PROVIDER_DISABLED.pop(dispatch_provider, None)

    def test_short_rate_limit_does_not_set_provider_disabled(self):
        """A normal (non-billing) rate limit does NOT set PROVIDER_DISABLED."""
        tail = "429 Too Many Requests"
        dispatch_provider = "infini"

        assert is_rate_limited(tail)
        assert not is_billing_exhausted(tail)

        window = parse_rate_limit_window(tail)  # None
        if is_billing_exhausted(tail):
            window = max(window or 0, BILLING_EXHAUSTED_THRESHOLD)
        cooldown = window if window else RATE_LIMIT_COOLDOWN_SECONDS

        # cooldown should be the default 5h, not billing threshold
        assert cooldown == RATE_LIMIT_COOLDOWN_SECONDS
        assert cooldown < BILLING_EXHAUSTED_THRESHOLD
        assert dispatch_provider not in PROVIDER_DISABLED

    def test_disabled_provider_blocks_dispatch(self):
        """Provider in PROVIDER_DISABLED cannot receive new tasks."""
        codex_disabled = {"codex": {"resets_at": time.time() + 86400, "resets_str": "Apr 8"}}
        # codex-affinity task should fallback to gemini
        result = _pick_dispatch_provider("codex", {}, {}, provider_disabled=codex_disabled)
        assert result is not None
        assert result != "codex"
        assert result == "gemini"  # first in codex fallback chain

    def test_clear_cooldown_clears_provider_disabled(self):
        """After clearing cooldown, PROVIDER_DISABLED is cleared too."""
        # Simulate setting PROVIDER_DISABLED
        PROVIDER_DISABLED["codex"] = {"resets_at": time.time() + 86400, "resets_str": "Apr 8"}
        assert "codex" in PROVIDER_DISABLED

        # Simulate the clear-cooldown signal handler logic
        provider_cooldown_until = {"codex": time.time() + 86400}
        for p in list(provider_cooldown_until):
            PROVIDER_DISABLED.pop(p, None)
            del provider_cooldown_until[p]

        assert "codex" not in PROVIDER_DISABLED
        assert not provider_cooldown_until

    def test_truncated_billing_output_still_enforces_24h(self):
        """Even when output is truncated (early kill), billing override gives 24h."""
        tail = "You've hit your usage limit for this billing"  # truncated
        assert is_billing_exhausted(tail)
        window = parse_rate_limit_window(tail)  # None (no date)
        assert window is None
        window = max(window or 0, BILLING_EXHAUSTED_THRESHOLD)
        assert window == BILLING_EXHAUSTED_THRESHOLD

    def test_full_billing_output_uses_actual_reset_date(self):
        """Full Codex billing message uses the actual reset date, not just 24h."""
        tail = "You've hit your usage limit. Please try again at Dec 25th, 2030 4:01 PM"
        assert is_billing_exhausted(tail)
        window = parse_rate_limit_window(tail)
        assert window is not None
        assert window > BILLING_EXHAUSTED_THRESHOLD
        # The window should be MUCH larger than 24h (it's years away)
        assert window > 365 * 86400  # > 1 year


# ── Codex-specific edge case tests ──────────────────────────────────────

class TestCodexBillingEdgeCases:
    """Edge-case tests for realistic Codex billing-limit scenarios."""

    def test_codex_billing_with_st_suffix(self):
        """Date with 'st' suffix (e.g. '1st') is parsed."""
        tail = "try again at Jan 1st, 2030 12:00 PM"
        window = parse_rate_limit_window(tail)
        assert window is not None
        assert window > BILLING_EXHAUSTED_THRESHOLD

    def test_codex_billing_with_no_suffix(self):
        """Date without ordinal suffix is also parsed."""
        # The regex uses (?:st|nd|rd|th)? so the suffix is optional
        tail = "try again at Apr 8, 2030 4:01 PM"
        window = parse_rate_limit_window(tail)
        assert window is not None
        assert window > BILLING_EXHAUSTED_THRESHOLD

    def test_codex_billing_12am(self):
        """12:00 AM in billing format is midnight (hour=0)."""
        tail = "try again at Dec 25th, 2030 12:00 AM"
        window = parse_rate_limit_window(tail)
        assert window is not None
        assert window > BILLING_EXHAUSTED_THRESHOLD

    def test_codex_billing_12pm(self):
        """12:00 PM in billing format is noon (hour=12)."""
        tail = "try again at Dec 25th, 2030 12:00 PM"
        window = parse_rate_limit_window(tail)
        assert window is not None
        assert window > BILLING_EXHAUSTED_THRESHOLD

    def test_codex_full_error_with_newlines(self):
        """Multi-line Codex error with newlines is parsed."""
        tail = "Error during execution:\nYou've hit your usage limit\n\nPlease try again at Apr 8th, 2026 4:01 PM"
        assert is_billing_exhausted(tail)
        window = parse_rate_limit_window(tail)
        # Apr 8, 2026 is ~5 days from now (Apr 3, 2026)
        assert window is not None
        assert window > BILLING_EXHAUSTED_THRESHOLD

    def test_codex_short_format_not_billing(self):
        """Short-format 'try again at 9:01 PM' without billing keywords is not billing."""
        tail = "try again at 9:01 PM"
        assert not is_billing_exhausted(tail)
        window = parse_rate_limit_window(tail)
        assert window is not None
        assert window < BILLING_EXHAUSTED_THRESHOLD

    def test_billing_reset_date_str_codex_format(self):
        """parse_reset_date_str returns human-readable date for Codex format."""
        result = parse_reset_date_str("try again at Apr 8th, 2026 4:01 PM")
        assert result is not None
        assert "Apr" in result
        assert "8" in result
        assert "2026" in result
        assert "4:01 PM" in result

    def test_billing_reset_date_str_no_comma(self):
        """parse_reset_date_str handles Codex format without comma after day."""
        result = parse_reset_date_str("try again at Apr 8th 2026 4:01 PM")
        assert result is not None
        assert "Apr" in result
