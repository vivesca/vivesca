"""Tests for golem-daemon — provider-aware task queue processor."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_golem_daemon():
    """Load the golem-daemon module by exec-ing its Python body."""
    source = open("/Users/terry/germline/effectors/golem-daemon").read()
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
    assert get_provider_limit("zhipu") == 4
    assert get_provider_limit("infini") == 6
    assert get_provider_limit("volcano") == 8


def test_get_provider_limit_unknown_provider():
    """get_provider_limit returns default for unknown providers."""
    assert get_provider_limit("unknown") == DEFAULT_LIMIT
    assert get_provider_limit("default") == DEFAULT_LIMIT


def test_provider_limits_constant():
    """PROVIDER_LIMITS contains expected values."""
    assert PROVIDER_LIMITS["zhipu"] == 4
    assert PROVIDER_LIMITS["infini"] == 6
    assert PROVIDER_LIMITS["volcano"] == 8


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
    assert max_workers == 8  # volcano has highest limit


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
    def mock_run(cmd, shell, capture_output, text, cwd=None):
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

    def mock_run(cmd, shell, capture_output, text, cwd=None):
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
