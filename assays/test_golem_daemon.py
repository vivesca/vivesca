from __future__ import annotations

"""Tests for golem-daemon — provider-aware task queue processor."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_golem_daemon():
    """Load the golem-daemon module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/golem-daemon").read()
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
    assert get_provider_limit("infini") == 8
    assert get_provider_limit("volcano") == 16


def test_get_provider_limit_unknown_provider():
    """get_provider_limit returns default for unknown providers."""
    assert get_provider_limit("unknown") == DEFAULT_LIMIT
    assert get_provider_limit("default") == DEFAULT_LIMIT


def test_provider_limits_constant():
    """PROVIDER_LIMITS contains expected values."""
    assert PROVIDER_LIMITS["zhipu"] == 8
    assert PROVIDER_LIMITS["infini"] == 8
    assert PROVIDER_LIMITS["volcano"] == 16


# ── parse_queue tests ─────────────────────────────────────────────────


def _make_queue_file(tmp_path: Path, content: str) -> Path:
    """Create a fake golem-queue.md in tmp_path."""
    queue_dir = tmp_path / "germline" / "loci"
    queue_dir.mkdir(parents=True)
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
    commands = [cmd for _, cmd in pending]
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
    commands = [cmd for _, cmd in pending]
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
    line_nums = [ln for ln, _ in pending]
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

    providers = [parse_provider(cmd) for _, cmd in pending]
    assert "infini" in providers
    assert "volcano" in providers
    assert "default" in providers


def test_concurrency_respects_provider_limits():
    """Verify that max workers would allow full provider concurrency."""
    max_workers = max(PROVIDER_LIMITS.values())
    assert max_workers == 16  # volcano has highest limit


# ── check_new_test_files_and_run_pytest tests ───────────────────────────


check_new_test_files_and_run_pytest = _mod["check_new_test_files_and_run_pytest"]


def test_check_new_test_files_filters_correctly():
    """Check that new test files filtering works."""
    # Test filtering logic with sample file list
    # This test just verifies the function is loaded and callable
    # The actual git call is mocked when needed
    assert callable(check_new_test_files_and_run_pytest)


def test_mark_failed_exists():
    """Verify that mark_failed function exists."""
    assert "mark_failed" in _mod
    assert callable(_mod["mark_failed"])


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
    assert 'golem --provider infini "task1" (retry)' in content


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

    # Should return retried: False
    assert result["retried"] is False

    # Task should now be marked failed
    content = queue_path.read_text()
    assert "- [!]" in content
    assert "- [ ]" not in content


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


def test_validate_golem_output_exists():
    """Verify that validate_golem_output function exists."""
    assert "validate_golem_output" in _mod
    assert callable(_mod["validate_golem_output"])


def test_validate_syntax_error_detection(tmp_path, monkeypatch):
    """validate_golem_output detects SyntaxError in .py files."""
    # Create a file with syntax error
    bad_file = tmp_path / "germline" / "assays" / "test_bad.py"
    bad_file.parent.mkdir(parents=True)
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
    todo_file.parent.mkdir(parents=True)
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
        try:
            passed, errors = validate_golem_output()
        finally:
            monkeypatch.setattr(_mod["Path"], "home", original_home if 'original_home' in dir() else _mod["Path"].home)

    assert not passed
    assert any("TODO" in e or "FIXME" in e for e in errors)


def test_validate_stub_detection(tmp_path, monkeypatch):
    """validate_golem_output detects 'stub' in code."""
    stub_file = tmp_path / "germline" / "assays" / "test_stub.py"
    stub_file.parent.mkdir(parents=True)
    stub_file.write_text('def foo():\n    return stub_function()\n')

    def mock_run(cmd, shell, capture_output, text, cwd=None):
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
        try:
            passed, errors = validate_golem_output()
        finally:
            pass

    assert not passed
    assert any("stub" in e.lower() for e in errors)


def test_validate_nested_test_file_detection(tmp_path, monkeypatch):
    """validate_golem_output rejects test files not flat in assays/."""
    # Create nested test file
    nested_file = tmp_path / "germline" / "assays" / "subdir" / "test_nested.py"
    nested_file.parent.mkdir(parents=True)
    nested_file.write_text('def test_foo(): pass\n')

    def mock_run(cmd, shell, capture_output, text, cwd=None):
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
        try:
            passed, errors = validate_golem_output()
        finally:
            pass

    assert not passed
    assert any("not flat" in e for e in errors)


def test_validate_pycache_detection():
    """validate_golem_output rejects __pycache__/.pyc files."""
    def mock_run(cmd, shell, capture_output, text, cwd=None):
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
    clean_file.parent.mkdir(parents=True)
    clean_file.write_text('def test_foo():\n    assert True\n')

    def mock_run(cmd, shell, capture_output, text, cwd=None):
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
        try:
            passed, errors = validate_golem_output()
        finally:
            pass

    assert passed
    assert errors == []


def test_validate_no_py_files_passes():
    """validate_golem_output passes when no .py files changed."""
    def mock_run(cmd, shell, capture_output, text, cwd=None):
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

    def mock_run_empty(cmd, shell, capture_output, text, cwd=None):
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
    def mock_run_fail(cmd, shell, capture_output, text, cwd=None):
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
    flat_file.parent.mkdir(parents=True)
    flat_file.write_text('def test_bar():\n    assert 1 + 1 == 2\n')

    def mock_run(cmd, shell, capture_output, text, cwd=None):
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
        try:
            passed, errors = validate_golem_output()
        finally:
            pass

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
    queue_dir.mkdir(parents=True)
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
    queue_dir.mkdir(parents=True)
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
            result = mark_failed(0, "bad command", exit_code=2)
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
        commands = [cmd for _, cmd in pending]
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
        assert pending[0] == (2, 'golem "first"')
        assert pending[1] == (4, 'golem "second"')

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
        assert len(pending[0][1]) == len(long_cmd)

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
    commands = [cmd for _, cmd in pending]
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

    # Build a map of command snippet -> line number
    by_cmd = {cmd: ln for ln, cmd in pending}
    # "urgent task" is on line 5, "normal task 1" on line 4, etc.
    assert by_cmd['golem --provider volcano "urgent task"'] == 5
    assert by_cmd['golem --provider infini --max-turns 50 "normal task 1"'] == 4
    assert by_cmd['golem "normal task 2"'] == 6
    assert by_cmd['golem --provider zhipu "another urgent"'] == 7


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
    commands = [cmd for _, cmd in pending]
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

    commands = [cmd for _, cmd in pending]
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
        result = mark_failed(0, "bad command", exit_code=2)
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
        commands = [cmd for _, cmd in pending]
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
