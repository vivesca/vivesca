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
