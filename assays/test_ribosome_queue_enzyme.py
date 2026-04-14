"""Tests for metabolon/enzymes/ribosome_queue.py — MCP tool for ribosome queue management."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from metabolon.morphology.base import EffectorResult

if TYPE_CHECKING:
    from pathlib import Path

# ── Fixtures ──────────────────────────────────────────────────────────────────

QUEUE_STUB = textwrap.dedent("""\
    ### Pending

    - [ ] `ribosome [t-aaaa01] --provider zhipu --max-turns 10 "First pending task"`
    - [!] `ribosome [t-bbbb02] --provider zhipu --max-turns 15 "A failed task (retry)"`
    - [ ] `ribosome [t-cccc03] [t-tag1] [t-tag2] --provider zhipu --max-turns 5 "Tagged task"`

    ### Completed

    - [x] `ribosome [t-done01] --provider zhipu --max-turns 10 "Already done"`
""")


@pytest.fixture
def tmp_queue(tmp_path: Path):
    """Create a temporary queue file and patch QUEUE_PATH."""
    qfile = tmp_path / "translation-queue.md"
    qfile.write_text(QUEUE_STUB, encoding="utf-8")
    with patch("metabolon.enzymes.ribosome_queue.QUEUE_PATH", qfile):
        yield qfile


@pytest.fixture
def enzyme():
    """Import and return the ribosome_queue tool function."""
    from metabolon.enzymes.ribosome_queue import ribosome_queue as fn

    return fn


# ── list ──────────────────────────────────────────────────────────────────────


def test_list_returns_all_tasks(enzyme, tmp_queue):
    result = enzyme(action="list")
    data = result.data
    assert data["total"] == 4
    assert data["pending"] == 2
    assert data["failed"] == 1
    assert data["completed"] == 1


def test_list_empty_queue(enzyme, tmp_path):
    qfile = tmp_path / "empty-queue.md"
    qfile.write_text("### Pending\n\n### Completed\n\n", encoding="utf-8")
    with patch("metabolon.enzymes.ribosome_queue.QUEUE_PATH", qfile):
        result = enzyme(action="list")
    assert "empty" in result.output.lower()


# ── add ───────────────────────────────────────────────────────────────────────


def test_add_appends_pending_entry(enzyme, tmp_queue):
    result = enzyme(
        action="add",
        task_id="t-new01",
        provider="zhipu",
        max_turns=20,
        prompt="Brand new task",
    )
    assert "Added task t-new01" in result.output

    # Verify it's on disk
    content = tmp_queue.read_text(encoding="utf-8")
    assert "t-new01" in content
    assert "Brand new task" in content
    assert "- [ ]" in content


def test_add_rejects_duplicate(enzyme, tmp_queue):
    result = enzyme(
        action="add",
        task_id="t-aaaa01",
        prompt="Duplicate",
    )
    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "already exists" in result.message


def test_add_requires_task_id_and_prompt(enzyme, tmp_queue):
    result = enzyme(action="add")
    assert isinstance(result, EffectorResult)
    assert result.success is False


def test_add_creates_file_if_missing(enzyme, tmp_path):
    qfile = tmp_path / "nonexistent.md"
    with patch("metabolon.enzymes.ribosome_queue.QUEUE_PATH", qfile):
        result = enzyme(
            action="add",
            task_id="t-fresh",
            prompt="First ever task",
        )
    assert "Added task t-fresh" in result.output
    assert qfile.exists()


# ── remove ────────────────────────────────────────────────────────────────────


def test_remove_deletes_entry(enzyme, tmp_queue):
    result = enzyme(action="remove", task_id="t-aaaa01")
    assert "Removed task t-aaaa01" in result.output

    content = tmp_queue.read_text(encoding="utf-8")
    assert "t-aaaa01" not in content


def test_remove_not_found(enzyme, tmp_queue):
    result = enzyme(action="remove", task_id="t-nope")
    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "not found" in result.message


def test_remove_requires_task_id(enzyme, tmp_queue):
    result = enzyme(action="remove")
    assert isinstance(result, EffectorResult)
    assert result.success is False


# ── status ────────────────────────────────────────────────────────────────────


def test_status_returns_task_info(enzyme, tmp_queue):
    result = enzyme(action="status", task_id="t-aaaa01")
    assert "pending" in result.output.lower()
    assert "First pending task" in result.output


def test_status_failed_task(enzyme, tmp_queue):
    result = enzyme(action="status", task_id="t-bbbb02")
    assert "failed" in result.output.lower()


def test_status_not_found(enzyme, tmp_queue):
    result = enzyme(action="status", task_id="t-nope")
    assert isinstance(result, EffectorResult)
    assert result.success is False


# ── complete ──────────────────────────────────────────────────────────────────


def test_complete_changes_checkbox(enzyme, tmp_queue):
    result = enzyme(action="complete", task_id="t-aaaa01")
    assert "completed" in result.output.lower()

    content = tmp_queue.read_text(encoding="utf-8")
    # Should now contain - [x] for t-aaaa01
    for line in content.splitlines():
        if "t-aaaa01" in line:
            assert "- [x]" in line


def test_complete_idempotent(enzyme, tmp_queue):
    enzyme(action="complete", task_id="t-aaaa01")
    result = enzyme(action="complete", task_id="t-aaaa01")
    assert "already completed" in result.output.lower()


def test_complete_not_found(enzyme, tmp_queue):
    result = enzyme(action="complete", task_id="t-nope")
    assert isinstance(result, EffectorResult)
    assert result.success is False


# ── fail ──────────────────────────────────────────────────────────────────────


def test_fail_changes_checkbox(enzyme, tmp_queue):
    result = enzyme(action="fail", task_id="t-cccc03")
    assert "failed" in result.output.lower()

    content = tmp_queue.read_text(encoding="utf-8")
    for line in content.splitlines():
        if "t-cccc03" in line:
            assert "- [!]" in line


def test_fail_idempotent(enzyme, tmp_queue):
    enzyme(action="fail", task_id="t-cccc03")
    result = enzyme(action="fail", task_id="t-cccc03")
    assert "already failed" in result.output.lower()


# ── unknown action ────────────────────────────────────────────────────────────


def test_unknown_action(enzyme, tmp_queue):
    result = enzyme(action="bogus")
    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "Unknown action" in result.message
