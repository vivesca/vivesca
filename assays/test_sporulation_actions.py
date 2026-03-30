"""Tests for sporulation action-dispatch consolidation."""
from unittest.mock import patch, MagicMock
import pytest

def test_unknown_action():
    from metabolon.enzymes.sporulation import sporulation
    result = sporulation(action="nonexistent")
    assert isinstance(result, str)
    assert "unknown" in result.lower() or "nonexistent" in result.lower()

@patch("metabolon.enzymes.sporulation.CHECKPOINTS_DIR")
def test_save_action(mock_checkpoints_dir, tmp_path):
    from metabolon.enzymes.sporulation import sporulation
    mock_checkpoints_dir.return_value = tmp_path
    with patch("metabolon.enzymes.sporulation.CHECKPOINTS_DIR", tmp_path):
        result = sporulation(action="save", codename="test", summary="test", context="test", action_needed="test", where_we_left_off="test")
        assert isinstance(result, str)

@patch("metabolon.enzymes.sporulation.CHECKPOINTS_DIR")
def test_load_action(mock_checkpoints_dir, tmp_path):
    from metabolon.enzymes.sporulation import sporulation
    with patch("metabolon.enzymes.sporulation.CHECKPOINTS_DIR", tmp_path):
        result = sporulation(action="load", codename="nonexistent")
        assert isinstance(result, str)

@patch("metabolon.enzymes.sporulation.CHECKPOINTS_DIR")
def test_list_action(mock_checkpoints_dir, tmp_path):
    from metabolon.enzymes.sporulation import sporulation
    with patch("metabolon.enzymes.sporulation.CHECKPOINTS_DIR", tmp_path):
        result = sporulation(action="list")
        assert isinstance(result, str)
