#!/usr/bin/env python3
from __future__ import annotations

"""Tests for metabolon.enzymes.turgor — tonus session state management tool."""


from unittest.mock import patch
import pytest

from metabolon.enzymes.turgor import tonus, ITEM_RE


# ── ITEM_RE regex tests ───────────────────────────────────────────────────────


class TestItemRe:
    def test_matches_correct_format(self):
        """Should match the expected markdown list item format."""
        line = "- [in-progress] **Write tests.** Add comprehensive test coverage"
        m = ITEM_RE.match(line)
        assert m is not None
        assert m.group(1) == "in-progress"
        assert m.group(2) == "Write tests."
        assert m.group(3) == "Add comprehensive test coverage"

    def test_matches_empty_description(self):
        """Should match items with empty description."""
        line = "- [done] **Completed task.**"
        m = ITEM_RE.match(line)
        assert m is not None
        assert m.group(1) == "done"
        assert m.group(2) == "Completed task."
        assert m.group(3) == ""

    def test_ignores_non_matching_lines(self):
        """Should not match lines that don't have the expected format."""
        assert ITEM_RE.match("Regular text") is None
        assert ITEM_RE.match("- Bullet point") is None
        assert ITEM_RE.match("- [ ] Unchecked checkbox") is None


# ── tonus action tests ────────────────────────────────────────────────────────


class TestTonusStatus:
    def test_status_empty_file(self):
        """Should return empty status when file has no items."""
        mock_content = """# Tonus

<!-- last checkpoint: 01/04/2024 ~10:00 HKT -->
"""
        with patch("metabolon.enzymes.turgor._read_tonus", return_value=mock_content):
            result = tonus(action="status")
        assert result["count"] == 0
        assert result["done"] == 0
        assert result["turgor"] == "normal"
        assert result["pressure"] == "0 in-progress / 0 total (0%)"
        assert result["items"] == []

    def test_status_calculates_correct_pressure_normal(self):
        """Should calculate normal turgor pressure correctly."""
        mock_content = """- [in-progress] **Task 1.** First task
- [done] **Task 2.** Second task
- [done] **Task 3.** Third task
<!-- last checkpoint: ... -->
"""
        with patch("metabolon.enzymes.turgor._read_tonus", return_value=mock_content):
            result = tonus(action="status")
        assert result["count"] == 3
        assert result["done"] == 2
        assert result["turgor"] == "normal"

    def test_status_calculates_high_pressure(self):
        """Should detect high turgor when >70% in-progress."""
        mock_content = """- [in-progress] **Task 1.**
- [in-progress] **Task 2.**
- [in-progress] **Task 3.**
- [done] **Task 4.**
<!-- last checkpoint: ... -->
"""
        with patch("metabolon.enzymes.turgor._read_tonus", return_value=mock_content):
            result = tonus(action="status")
        assert result["count"] == 4
        # 3/4 = 75% > 70%
        assert "HIGH" in result["turgor"]

    def test_status_calculates_low_pressure(self):
        """Should detect low turgor when <20% in-progress and total >0."""
        mock_content = """- [in-progress] **Task 1.**
- [done] **Task 2.**
- [done] **Task 3.**
- [done] **Task 4.**
- [done] **Task 5.**
<!-- last checkpoint: ... -->
"""
        with patch("metabolon.enzymes.turgor._read_tonus", return_value=mock_content):
            result = tonus(action="status")
        assert result["count"] == 5
        # 1/5 = 20%, so not low — only when <20%
        # Let's use 1/6 for test below, actually
        pass

    def test_status_calculates_low_pressure_when_below_threshold(self):
        """Should detect low turgor when <20% in-progress and total >0."""
        mock_content = """- [in-progress] **Task 1.**
- [done] **Task 2.**
- [done] **Task 3.**
- [done] **Task 4.**
- [done] **Task 5.**
- [done] **Task 6.**
<!-- last checkpoint: ... -->
"""
        with patch("metabolon.enzymes.turgor._read_tonus", return_value=mock_content):
            result = tonus(action="status")
        assert result["count"] == 6
        assert 1/6 < 0.2
        assert "LOW" in result["turgor"]

    def test_status_parses_items_correctly(self):
        """Should parse items correctly into result dict."""
        mock_content = """- [queued] **Write tests.** For turgor module
- [done] **Cleanup.** Old files
"""
        with patch("metabolon.enzymes.turgor._read_tonus", return_value=mock_content):
            result = tonus(action="status")
        assert len(result["items"]) == 2
        assert result["items"][0] == {
            "status": "queued",
            "label": "Write tests",
            "description": "For turgor module",
        }
        assert result["items"][1]["label"] == "Cleanup"


class TestTonusMark:
    def test_mark_update_existing_item_status(self):
        """Should update status of existing matching item."""
        mock_content = """- [queued] **Write tests.** Add tests
<!-- last checkpoint: old -->
"""
        wrote_content = None

        def mock_write(content):
            nonlocal wrote_content
            wrote_content = content

        with patch("metabolon.enzymes.turgor._read_tonus", return_value=mock_content):
            with patch("metabolon.enzymes.turgor._write_tonus", side_effect=mock_write):
                result = tonus(action="mark", label="Write", item_status="in-progress")

        assert result["success"] is True
        assert "- [in-progress] **Write tests.** Add tests" in wrote_content
        assert "last checkpoint:" in wrote_content  # Should update timestamp

    def test_mark_update_existing_description(self):
        """Should update description of existing matching item."""
        mock_content = """- [in-progress] **Write tests.**
"""
        wrote_content = None

        def mock_write(content):
            nonlocal wrote_content
            wrote_content = content

        with patch("metabolon.enzymes.turgor._read_tonus", return_value=mock_content):
            with patch("metabolon.enzymes.turgor._write_tonus", side_effect=mock_write):
                result = tonus(
                    action="mark",
                    label="Write",
                    description="Add comprehensive tests for turgor",
                )

        assert result["success"] is True
        assert "Add comprehensive tests for turgor" in wrote_content

    def test_mark_both_status_and_description(self):
        """Should update both status and description when both provided."""
        mock_content = """- [queued] **Old item.** Old desc
"""
        wrote_content = None

        def mock_write(content):
            nonlocal wrote_content
            wrote_content = content

        with patch("metabolon.enzymes.turgor._read_tonus", return_value=mock_content):
            with patch("metabolon.enzymes.turgor._write_tonus", side_effect=mock_write):
                result = tonus(
                    action="mark",
                    label="Old",
                    item_status="done",
                    description="New description here",
                )

        assert result["success"] is True
        assert "- [done] **Old item.** New description here" in wrote_content

    def test_mark_create_new_item_when_no_match(self):
        """Should create new item when no match found and both fields provided."""
        mock_content = """# Tonus
Some content
<!-- last checkpoint: ... -->
"""
        wrote_content = None

        def mock_write(content):
            nonlocal wrote_content
            wrote_content = content

        with patch("metabolon.enzymes.turgor._read_tonus", return_value=mock_content):
            with patch("metabolon.enzymes.turgor._write_tonus", side_effect=mock_write):
                result = tonus(
                    action="mark",
                    label="New task",
                    item_status="in-progress",
                    description="This is a new task",
                )

        assert result["success"] is True
        assert "- [in-progress] **New task.** This is a new task" in wrote_content
        # Should insert before the comment
        assert "<!-- last checkpoint:" in wrote_content
        assert wrote_content.index("New task") < wrote_content.index("<!-- last checkpoint")

    def test_mark_create_new_item_appends_when_no_comment(self):
        """Should append new item when no comment found at end."""
        mock_content = """# Tonus
Some content
"""
        wrote_content = None

        def mock_write(content):
            nonlocal wrote_content
            wrote_content = content

        with patch("metabolon.enzymes.turgor._read_tonus", return_value=mock_content):
            with patch("metabolon.enzymes.turgor._write_tonus", side_effect=mock_write):
                result = tonus(
                    action="mark",
                    label="New task",
                    item_status="in-progress",
                    description="This is a new task",
                )

        assert result["success"] is True
        assert "New task" in wrote_content

    def test_mark_fails_when_no_match_and_missing_fields(self):
        """Should return error when no match and not both fields provided."""
        mock_content = """- [done] **Existing.** Item
"""
        with patch("metabolon.enzymes.turgor._read_tonus", return_value=mock_content):
            result = tonus(action="mark", label="Missing", item_status="in-progress")
        assert result["success"] is False
        assert "No item matching" in result["message"]

    def test_mark_fails_when_nothing_to_update(self):
        """Should return error when neither item_status nor description provided."""
        result = tonus(action="mark", label="Anything")
        assert result["success"] is False
        assert "Nothing to update" in result["message"]


class TestTonusUnknownAction:
    def test_unknown_action_returns_error(self):
        """Should return error for unknown action."""
        result = tonus(action="delete", label="test")
        assert result["success"] is False
        assert "Unknown action" in result["message"]
