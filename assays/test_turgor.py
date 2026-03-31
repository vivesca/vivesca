"""Tests for turgor tonus tool."""
from unittest.mock import patch, mock_open
import pytest


def test_unknown_action():
    """Test unknown action returns error."""
    from metabolon.enzymes.turgor import tonus
    result = tonus(action="unknown")
    assert not result["success"]
    assert "Unknown action" in result["message"]


@patch("metabolon.enzymes.turgor._read_tonus")
def test_status_empty(mock_read):
    """Test status with empty file."""
    from metabolon.enzymes.turgor import tonus
    mock_read.return_value = ""
    result = tonus(action="status")
    assert result["count"] == 0
    assert result["turgor"] == "normal"
    assert result["pressure"] == "0 in-progress / 0 total (0%)"


sample_tonus = """# Tonus

- [in-progress] **Write tests.** Complete test coverage for all enzymes
- [done] **Refactor code.** Clean up old implementations
- [queued] **Review PR.** Check incoming changes
<!-- last checkpoint: 31/03/2026 ~10:00 HKT -->
"""


@patch("metabolon.enzymes.turgor._read_tonus")
def test_status_normal_pressure(mock_read):
    """Test status with normal pressure calculation."""
    from metabolon.enzymes.turgor import tonus
    mock_read.return_value = sample_tonus
    result = tonus(action="status")
    assert result["count"] == 3
    assert result["done"] == 1
    assert result["in_progress"] == 1
    assert result["turgor"] == "normal"
    assert len(result["items"]) == 3
    # Check first item parsed correctly
    item = next(i for i in result["items"] if i["label"] == "Write tests")
    assert item["status"] == "in-progress"
    assert item["description"] == "Complete test coverage for all enzymes"


@patch("metabolon.enzymes.turgor._read_tonus")
def test_status_high_pressure(mock_read):
    """Test status detects high pressure (>70%)."""
    from metabolon.enzymes.turgor import tonus
    high_content = """
- [in-progress] **Item 1.** First
- [in-progress] **Item 2.** Second
- [in-progress] **Item 3.** Third
- [done] **Item 4.** Fourth
"""
    mock_read.return_value = high_content
    result = tonus(action="status")
    assert "HIGH — too many items in-progress" in result["turgor"]


@patch("metabolon.enzymes.turgor._read_tonus")
def test_status_low_pressure(mock_read):
    """Test status detects low pressure (<20%)."""
    from metabolon.enzymes.turgor import tonus
    low_content = """
- [in-progress] **Item 1.** First
- [done] **Item 2.** Second
- [done] **Item 3.** Third
- [done] **Item 4.** Fourth
- [done] **Item 5.** Fifth
"""
    mock_read.return_value = low_content
    result = tonus(action="status")
    assert "LOW — wilting" in result["turgor"]


def test_mark_no_update_provided():
    """Test mark returns error when nothing to update."""
    from metabolon.enzymes.turgor import tonus
    result = tonus(action="mark", label="Test")
    assert not result["success"]
    assert "Nothing to update" in result["message"]


@patch("metabolon.enzymes.turgor._write_tonus")
@patch("metabolon.enzymes.turgor._read_tonus")
def test_mark_update_existing_status(mock_read, mock_write):
    """Test mark updates status of existing item."""
    from metabolon.enzymes.turgor import tonus
    mock_read.return_value = sample_tonus
    result = tonus(action="mark", label="Write tests", item_status="done")
    assert result["success"]
    assert "Updated" in result["message"]
    # Verify write was called
    assert mock_write.called
    # Check that the status was changed in the written content
    written_content = mock_write.call_args[0][0]
    assert "- [done] **Write tests.**" in written_content


@patch("metabolon.enzymes.turgor._write_tonus")
@patch("metabolon.enzymes.turgor._read_tonus")
def test_mark_update_existing_description(mock_read, mock_write):
    """Test mark updates description of existing item."""
    from metabolon.enzymes.turgor import tonus
    mock_read.return_value = sample_tonus
    result = tonus(action="mark", label="Write tests", description="Updated description for tests")
    assert result["success"]
    written_content = mock_write.call_args[0][0]
    assert "Updated description for tests" in written_content


@patch("metabolon.enzymes.turgor._write_tonus")
@patch("metabolon.enzymes.turgor._read_tonus")
def test_mark_create_new_item(mock_read, mock_write):
    """Test mark creates new item when no match found."""
    from metabolon.enzymes.turgor import tonus
    mock_read.return_value = sample_tonus
    result = tonus(
        action="mark",
        label="New task",
        item_status="in-progress",
        description="This is a brand new task",
    )
    assert result["success"]
    written_content = mock_write.call_args[0][0]
    assert "- [in-progress] **New task.** This is a brand new task" in written_content
    # New item should be inserted before the last comment
    assert written_content.index("New task") < written_content.index("last checkpoint")


@patch("metabolon.enzymes.turgor._write_tonus")
@patch("metabolon.enzymes.turgor._read_tonus")
def test_mark_no_match_cannot_create(mock_read, mock_write):
    """Test mark returns error when no match and insufficient data for create."""
    from metabolon.enzymes.turgor import tonus
    mock_read.return_value = sample_tonus
    result = tonus(action="mark", label="Does not exist", item_status="in-progress")
    assert not result["success"]
    assert "No item matching" in result["message"]
    assert not mock_write.called


@patch("metabolon.enzymes.turgor.TONUS")
def test_private_read_write(mock_tonus_path):
    """Test _read_tonus and _write_tonus work with Path operations."""
    from metabolon.enzymes.turgor import _read_tonus, _write_tonus
    test_content = "test content"
    mock_tonus_path.with_suffix.return_value = mock_tonus_path
    mock_tonus_path.read_text.return_value = test_content
    
    result = _read_tonus()
    assert result == test_content
    assert mock_tonus_path.read_text.called
    
    _write_tonus(test_content)
    assert mock_tonus_path.with_suffix.called
    assert mock_tonus_path.write_text.called
    assert mock_tonus_path.replace.called
