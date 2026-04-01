from __future__ import annotations

"""Tests for metabolon.enzymes.turgor — session state."""

from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

import pytest
from metabolon.enzymes.turgor import tonus

HKT = timezone(timedelta(hours=8))


class TestTurgorTool:
    """Tests for the tonus() MCP tool function."""

    @patch("metabolon.enzymes.turgor._read_tonus")
    def test_status_empty(self, mock_read):
        mock_read.return_value = ""
        result = tonus(action="status")
        
        assert result["items"] == []
        assert result["count"] == 0
        assert result["turgor"] == "normal"
        assert "0 in-progress / 0 total" in result["pressure"]

    @patch("metabolon.enzymes.turgor._read_tonus")
    def test_status_with_items(self, mock_read):
        mock_read.return_value = (
            "- [in-progress] **Coding.** working on tests\n"
            "- [done] **Planning.** done with plan\n"
            "- [queued] **Refactor.** later"
        )
        result = tonus(action="status")
        
        assert len(result["items"]) == 3
        assert result["count"] == 3
        assert result["done"] == 1
        assert "1 in-progress / 3 total" in result["pressure"]
        # 1/3 = 33%, normal
        assert result["turgor"] == "normal"
        
        assert result["items"][0] == {"status": "in-progress", "label": "Coding", "description": "working on tests"}

    @patch("metabolon.enzymes.turgor._read_tonus")
    def test_status_high_pressure(self, mock_read):
        mock_read.return_value = (
            "- [in-progress] **A.** desc\n"
            "- [in-progress] **B.** desc\n"
            "- [in-progress] **C.** desc\n"
            "- [queued] **D.** desc"
        )
        # 3 in-progress / 4 total = 75% > 70%
        result = tonus(action="status")
        assert "HIGH" in result["turgor"]

    @patch("metabolon.enzymes.turgor._read_tonus")
    def test_status_low_pressure(self, mock_read):
        mock_read.return_value = (
            "- [done] **A.** desc\n"
            "- [done] **B.** desc\n"
            "- [done] **C.** desc\n"
            "- [done] **D.** desc\n"
            "- [queued] **E.** desc\n"
            "- [queued] **F.** desc"
        )
        # 0 in-progress / 6 total = 0% < 20%
        result = tonus(action="status")
        assert "LOW" in result["turgor"]

    @patch("metabolon.enzymes.turgor._write_tonus")
    @patch("metabolon.enzymes.turgor._read_tonus")
    @patch("metabolon.enzymes.turgor.datetime")
    def test_mark_update_existing(self, mock_dt, mock_read, mock_write):
        mock_read.return_value = (
            "- [in-progress] **Coding.** working on tests\n"
            "<!-- last checkpoint: 01/01/2026 ~10:00 HKT -->"
        )
        fixed_now = datetime(2026, 4, 1, 12, 0, tzinfo=HKT)
        mock_dt.now.return_value = fixed_now
        
        result = tonus(action="mark", label="coding", item_status="done")
        
        assert result["success"] is True
        mock_write.assert_called_once()
        written_content = mock_write.call_args[0][0]
        assert "- [done] **Coding.** working on tests" in written_content
        assert "<!-- last checkpoint: 01/04/2026 ~12:00 HKT -->" in written_content

    @patch("metabolon.enzymes.turgor._write_tonus")
    @patch("metabolon.enzymes.turgor._read_tonus")
    def test_mark_create_new(self, mock_read, mock_write):
        mock_read.return_value = "- [done] **Old.** task\n<!-- comments -->"
        
        result = tonus(action="mark", label="New Task", item_status="in-progress", description="new desc")
        
        assert result["success"] is True
        written_content = mock_write.call_args[0][0]
        assert "- [in-progress] **New Task.** new desc" in written_content
        # It should insert before <!--
        assert "- [in-progress] **New Task.** new desc\n<!-- comments -->" in written_content

    def test_mark_missing_params(self):
        result = tonus(action="mark", label="something")
        assert result["success"] is False
        assert "Nothing to update" in result["message"]

    @patch("metabolon.enzymes.turgor._read_tonus")
    def test_mark_not_found_no_create(self, mock_read):
        mock_read.return_value = "- [done] **Old.** task"
        result = tonus(action="mark", label="New", item_status="in-progress")
        assert result["success"] is False
        assert "No item matching 'New' found" in result["message"]

    def test_unknown_action(self):
        result = tonus(action="invalid")
        assert result["success"] is False
        assert "Unknown action" in result["message"]
