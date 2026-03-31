"""Tests for sporulation checkpoint module."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import UTC, datetime, timedelta
from pathlib import Path

from metabolon.enzymes.sporulation import (
    _gen_codename,
    _existing_codenames,
    _purge_stale,
    _save,
    _load,
    _list,
    sporulation,
    SporulationSaveResult,
    SporulationLoadResult,
    SporulationListResult,
)


def test_gen_codename_generates_unique():
    """_gen_codename returns unique name not in existing."""
    existing = {"happy-cat", "bold-fox"}
    for _ in range(10):
        name = _gen_codename(existing)
        assert name not in existing
        assert "-" in name
        adj, noun = name.split("-", 1)
        assert adj
        assert noun


def test_existing_codenames_no_dir():
    """_existing_codenames returns empty set if dir doesn't exist."""
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", Path("/nonexistent")):
        result = _existing_codenames()
        assert result == set()


def test_purge_stale_no_dir():
    """_purge_stale returns empty list if dir doesn't exist."""
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", Path("/nonexistent")):
        result = _purge_stale()
        assert result == []


def test_purge_stale_removes_old_files(tmp_path):
    """_purge_stale removes files older than 7 days."""
    checkpoint_dir = tmp_path
    old_file = checkpoint_dir / "checkpoint_old-cat.md"
    new_file = checkpoint_dir / "checkpoint_new-fox.md"

    old_file.write_text("old")
    new_file.write_text("new")

    # Set old_file mtime to 8 days ago
    eight_days_ago = (datetime.now(UTC) - timedelta(days=8)).timestamp()
    import os
    os.utime(old_file, (eight_days_ago, eight_days_ago))

    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", checkpoint_dir):
        purged = _purge_stale()
        assert purged == ["old-cat"]
        assert not old_file.exists()
        assert new_file.exists()


def test_save_generates_codename(tmp_path):
    """_save generates codename when none provided."""
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        result = _save(
            context="Working on tests",
            where_we_left_off="Writing test cases",
            action_needed="Run pytest",
        )
        assert isinstance(result, SporulationSaveResult)
        assert result.codename
        assert "-" in result.codename
        assert Path(result.path).exists()
        assert result.codename in Path(result.path).read_text()


def test_save_rejects_duplicate_codename(tmp_path):
    """_save doesn't overwrite existing checkpoint."""
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        # Create existing
        existing_path = tmp_path / "checkpoint_test-cat.md"
        existing_path.write_text("existing")
        result = _save(
            context="context",
            where_we_left_off="left",
            action_needed="action",
            codename="test-cat",
        )
        assert result.codename == "test-cat"
        assert result.path == ""
        # Original still exists
        assert existing_path.exists()


def test_load_not_found_returns_not_found():
    """_load returns found=False when checkpoint doesn't exist."""
    result = _load("nonexistent-codename", consume=True)
    assert isinstance(result, SporulationLoadResult)
    assert result.found is False
    assert result.content == ""


def test_list_no_dir_returns_empty():
    """_list returns empty list when checkpoint dir doesn't exist."""
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", Path("/nonexistent")):
        result = _list()
        assert isinstance(result, SporulationListResult)
        assert result.checkpoints == []


def test_sporulation_unknown_action():
    """sporulation returns error message for unknown action."""
    result = sporulation(action="unknown")
    assert result == "Unknown action 'unknown'. Use save, load, or list."


def test_sporulation_list_action():
    """sporulation list action returns SporulationListResult."""
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", Path("/nonexistent")):
        result = sporulation(action="list")
        assert isinstance(result, SporulationListResult)


def test_load_found_consumes(tmp_path):
    """_load consumes (deletes) the checkpoint when consume=True."""
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        codename = "test-bird"
        path = tmp_path / f"checkpoint_{codename}.md"
        path.write_text("test content")
        result = _load(codename, consume=True)
        assert isinstance(result, SporulationLoadResult)
        assert result.found is True
        assert result.content == "test content"
        assert not path.exists()


def test_load_found_no_consume_keeps(tmp_path):
    """_load doesn't delete when consume=False."""
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        codename = "test-tree"
        path = tmp_path / f"checkpoint_{codename}.md"
        path.write_text("test content")
        result = _load(codename, consume=False)
        assert result.found is True
        assert path.exists()


def test_list_parses_description(tmp_path):
    """_list extracts description from checkpoint file."""
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        codename = "happy-owl"
        path = tmp_path / f"checkpoint_{codename}.md"
        content = """---
name: happy-owl checkpoint
description: Resume point for testing (now)
---
content
"""
        path.write_text(content)
        result = _list()
        assert len(result.checkpoints) == 1
        cp = result.checkpoints[0]
        assert cp["codename"] == "happy-owl"
        assert "Resume point" in cp["description"]
        assert cp["age_days"] >= 0
