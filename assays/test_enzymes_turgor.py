from __future__ import annotations

"""Tests for metabolon.enzymes.turgor — tonus tool (mark/status)."""

import re
from unittest.mock import patch

import pytest

# We test the inner logic directly, bypassing the @tool decorator.
# Import the module and access the wrapped function.
from metabolon.enzymes.turgor import (
    ITEM_RE,
    _read_tonus,
    _write_tonus,
    tonus,
)


# ---------------------------------------------------------------------------
# Fixtures — sample Tonus.md content
# ---------------------------------------------------------------------------

SAMPLE_TONUS = """\
<!-- last checkpoint: 01/01/2026 ~12:00 HKT -->

- [queued] **Write tests.** pending
- [in-progress] **Refactor module.** halfway done
- [done] **Setup project.** completed
"""

TONUS_NO_CHECKPOINT = """\
- [queued] **Write tests.** pending
"""

TONUS_EMPTY = ""


# ---------------------------------------------------------------------------
# Helper — patch _read_tonus / _write_tonus so no real files are touched
# ---------------------------------------------------------------------------

def _patch_io(read_return: str):
    """Return a patcher that stubs _read_tonus and captures _write_tonus calls."""
    return patch.object(
        __import__("metabolon.enzymes.turgor", fromlist=["turgor"]),
        "_read_tonus",
        return_value=read_return,
    )


# ---------------------------------------------------------------------------
# Tests — ITEM_RE
# ---------------------------------------------------------------------------

class TestItemRegex:
    def test_matches_standard_item(self):
        m = ITEM_RE.match("- [in-progress] **Refactor module.** halfway done")
        assert m is not None
        assert m.group(1) == "in-progress"
        assert m.group(2) == "Refactor module."
        assert m.group(3) == "halfway done"

    def test_no_match_plain_line(self):
        assert ITEM_RE.match("some plain text") is None

    def test_no_match_comment(self):
        assert ITEM_RE.match("<!-- last checkpoint: 01/01/2026 ~12:00 HKT -->") is None

    def test_empty_description(self):
        m = ITEM_RE.match("- [done] **Task.**")
        assert m is not None
        assert m.group(3) == ""


# ---------------------------------------------------------------------------
# Tests — status action
# ---------------------------------------------------------------------------

class TestStatus:
    @_patch_io(SAMPLE_TONUS)
    def test_returns_items_and_counts(self, mock_read):
        result = tonus("status")
        assert result["count"] == 3
        assert result["done"] == 1
        labels = [i["label"] for i in result["items"]]
        assert "Write tests" in labels
        assert "Refactor module" in labels
        assert "Setup project" in labels

    @_patch_io(SAMPLE_TONUS)
    def test_pressure_calculation(self, mock_read):
        result = tonus("status")
        # 1 in-progress / 3 total
        assert "1 in-progress / 3 total" in result["pressure"]

    @_patch_io(SAMPLE_TONUS)
    def test_turgor_normal(self, mock_read):
        result = tonus("status")
        assert result["turgor"] == "normal"

    @_patch_io("")
    def test_empty_tonus(self, mock_read):
        result = tonus("status")
        assert result["count"] == 0
        assert result["items"] == []
        assert result["turgor"] == "normal"

    def test_high_turgor(self):
        lines = ["<!-- last checkpoint: x -->"]
        for i in range(8):
            lines.append(f"- [in-progress] **Task {i}.** desc")
        for i in range(2):
            lines.append(f"- [done] **Done {i}.** desc")
        content = "\n".join(lines) + "\n"
        with _patch_io(content) as mock_read:
            result = tonus("status")
        assert result["turgor"] == "HIGH — too many items in-progress, finish before starting"

    def test_low_turgor(self):
        lines = ["<!-- last checkpoint: x -->"]
        for i in range(8):
            lines.append(f"- [done] **Done {i}.** desc")
        for i in range(1):
            lines.append(f"- [queued] **Queued {i}.** desc")
        content = "\n".join(lines) + "\n"
        with _patch_io(content) as mock_read:
            result = tonus("status")
        assert result["turgor"] == "LOW — wilting, pick up pace or reduce scope"


# ---------------------------------------------------------------------------
# Tests — mark action
# ---------------------------------------------------------------------------

class TestMark:
    @_patch_io(SAMPLE_TONUS)
    def test_nothing_to_update(self, mock_read):
        result = tonus("mark", label="irrelevant")
        assert result["success"] is False
        assert "Nothing to update" in result["message"]

    @_patch_io(SAMPLE_TONUS)
    def test_update_status_existing_item(self, mock_read):
        with patch("metabolon.enzymes.turgor._write_tonus") as mock_write:
            result = tonus("mark", label="Write tests", item_status="in-progress")
        assert result["success"] is True
        written = mock_write.call_args[0][0]
        assert "- [in-progress] **Write tests.** pending" in written

    @_patch_io(SAMPLE_TONUS)
    def test_update_description_existing_item(self, mock_read):
        with patch("metabolon.enzymes.turgor._write_tonus") as mock_write:
            result = tonus("mark", label="Refactor module", description="now complete")
        assert result["success"] is True
        written = mock_write.call_args[0][0]
        assert "- [in-progress] **Refactor module.** now complete" in written

    @_patch_io(SAMPLE_TONUS)
    def test_update_both_fields(self, mock_read):
        with patch("metabolon.enzymes.turgor._write_tonus") as mock_write:
            result = tonus("mark", label="Write tests", item_status="done", description="all done")
        assert result["success"] is True
        written = mock_write.call_args[0][0]
        assert "- [done] **Write tests.** all done" in written

    @_patch_io(SAMPLE_TONUS)
    def test_fuzzy_match_case_insensitive(self, mock_read):
        with patch("metabolon.enzymes.turgor._write_tonus") as mock_write:
            result = tonus("mark", label="write tests", item_status="done")
        assert result["success"] is True

    @_patch_io(SAMPLE_TONUS)
    def test_partial_label_match(self, mock_read):
        with patch("metabolon.enzymes.turgor._write_tonus") as mock_write:
            result = tonus("mark", label="refactor", item_status="done")
        assert result["success"] is True

    @_patch_io(SAMPLE_TONUS)
    def test_not_found_no_create(self, mock_read):
        result = tonus("mark", label="nonexistent", item_status="in-progress")
        assert result["success"] is False
        assert "No item matching" in result["message"]

    @_patch_io(SAMPLE_TONUS)
    def test_create_new_item_with_both_fields(self, mock_read):
        with patch("metabolon.enzymes.turgor._write_tonus") as mock_write:
            result = tonus("mark", label="New task", item_status="queued", description="fresh")
        assert result["success"] is True
        written = mock_write.call_args[0][0]
        assert "- [queued] **New task.** fresh" in written

    @_patch_io(SAMPLE_TONUS)
    def test_checkpoint_updated(self, mock_read):
        with patch("metabolon.enzymes.turgor._write_tonus") as mock_write:
            tonus("mark", label="Write tests", item_status="done")
        written = mock_write.call_args[0][0]
        assert "<!-- last checkpoint:" in written

    @_patch_io(TONUS_NO_CHECKPOINT)
    def test_mark_no_checkpoint_in_file(self, mock_read):
        """When there is no checkpoint comment, new item appended (no crash)."""
        with patch("metabolon.enzymes.turgor._write_tonus") as mock_write:
            result = tonus("mark", label="Write tests", item_status="done", description="done")
        assert result["success"] is True

    @_patch_io(SAMPLE_TONUS)
    def test_new_item_inserted_before_comment(self, mock_read):
        with patch("metabolon.enzymes.turgor._write_tonus") as mock_write:
            tonus("mark", label="Brand new", item_status="queued", description="new thing")
        written = mock_write.call_args[0][0]
        lines = written.splitlines()
        # The new item should appear BEFORE the <!-- comment
        comment_idx = next(i for i, l in enumerate(lines) if l.startswith("<!--"))
        new_idx = next(i for i, l in enumerate(lines) if "Brand new" in l)
        assert new_idx < comment_idx


# ---------------------------------------------------------------------------
# Tests — unknown action
# ---------------------------------------------------------------------------

class TestUnknownAction:
    def test_unknown_action_returns_error(self):
        result = tonus("foobar")
        assert result["success"] is False
        assert "Unknown action" in result["message"]
