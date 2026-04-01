from __future__ import annotations

import pytest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from metabolon.enzymes.sporulation import (
    _checkpoint_path,
    _existing_codenames,
    _gen_codename,
    _list,
    _load,
    _purge_stale,
    _save,
    sporulation,
    SporulationSaveResult,
    SporulationLoadResult,
    SporulationListResult,
)


# ---------------------------------------------------------------------------
# _checkpoint_path
# ---------------------------------------------------------------------------
def test_checkpoint_path(tmp_path):
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        result = _checkpoint_path("bold-fox")
        assert result == tmp_path / "checkpoint_bold-fox.md"


# ---------------------------------------------------------------------------
# _existing_codenames
# ---------------------------------------------------------------------------
def test_existing_codenames_empty(tmp_path):
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        assert _existing_codenames() == set()


def test_existing_codenames_returns_names(tmp_path):
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        (tmp_path / "checkpoint_happy-cat.md").write_text("x")
        (tmp_path / "checkpoint_bold-fox.md").write_text("x")
        # non-matching file should be ignored
        (tmp_path / "other.txt").write_text("x")
        result = _existing_codenames()
        assert result == {"happy-cat", "bold-fox"}


def test_existing_codenames_dir_missing(tmp_path):
    missing = tmp_path / "nope"
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", missing):
        assert _existing_codenames() == set()


# ---------------------------------------------------------------------------
# _gen_codename
# ---------------------------------------------------------------------------
def test_gen_codename_produces_valid_name():
    name = _gen_codename(set())
    parts = name.split("-")
    assert len(parts) == 2
    assert parts[0].isalpha()
    assert parts[1].isalpha()


def test_gen_codename_avoids_existing():
    # Use a small existing set so the random generator easily finds a free name
    existing = {"happy-cat", "bold-fox", "calm-owl"}
    name = _gen_codename(existing)
    assert name not in existing
    parts = name.split("-")
    assert len(parts) == 2


# ---------------------------------------------------------------------------
# _purge_stale
# ---------------------------------------------------------------------------
def test_purge_stale_removes_old(tmp_path):
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        old_file = tmp_path / "checkpoint_old-one.md"
        old_file.write_text("stale")
        # Set mtime to 8 days ago
        old_time = datetime.now(UTC).timestamp() - 8 * 86400
        import os
        os.utime(old_file, (old_time, old_time))

        fresh_file = tmp_path / "checkpoint_fresh-one.md"
        fresh_file.write_text("fresh")

        purged = _purge_stale()
        assert purged == ["old-one"]
        assert not old_file.exists()
        assert fresh_file.exists()


def test_purge_stale_dir_missing(tmp_path):
    missing = tmp_path / "nope"
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", missing):
        assert _purge_stale() == []


# ---------------------------------------------------------------------------
# _save
# ---------------------------------------------------------------------------
def test_save_creates_checkpoint(tmp_path):
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path), \
         patch("metabolon.enzymes.sporulation._purge_stale", return_value=[]):
        result = _save(
            context="Building feature X",
            where_we_left_off="- wrote tests\n- need to implement",
            action_needed="1. Write code\n2. Run tests",
            summary="Feature X checkpoint",
            codename="keen-elk",
        )
        assert isinstance(result, SporulationSaveResult)
        assert result.codename == "keen-elk"
        assert str(tmp_path) in result.path
        assert result.purged == []

        path = tmp_path / "checkpoint_keen-elk.md"
        assert path.exists()
        content = path.read_text()
        assert "keen-elk" in content
        assert "Building feature X" in content
        assert "wrote tests" in content
        assert "Write code" in content


def test_save_auto_generates_codename(tmp_path):
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path), \
         patch("metabolon.enzymes.sporulation._purge_stale", return_value=[]):
        result = _save(
            context="Some context",
            where_we_left_off="step 1",
            action_needed="step 2",
        )
        assert result.codename
        assert "-" in result.codename
        assert result.path


def test_save_duplicate_codename_returns_empty_path(tmp_path):
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path), \
         patch("metabolon.enzymes.sporulation._purge_stale", return_value=[]):
        # Create existing checkpoint
        (tmp_path / "checkpoint_bold-fox.md").write_text("old")
        result = _save(
            context="New context",
            where_we_left_off="left off",
            action_needed="action",
            codename="bold-fox",
        )
        assert result.codename == "bold-fox"
        assert result.path == ""


def test_save_reports_purged(tmp_path):
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path), \
         patch("metabolon.enzymes.sporulation._purge_stale", return_value=["stale-1"]):
        result = _save(
            context="ctx",
            where_we_left_off="wlo",
            action_needed="an",
            codename="new-one",
        )
        assert result.purged == ["stale-1"]


# ---------------------------------------------------------------------------
# _load
# ---------------------------------------------------------------------------
def test_load_existing(tmp_path):
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        cp = tmp_path / "checkpoint_warm-owl.md"
        cp.write_text("checkpoint content here")
        result = _load("warm-owl", consume=True)
        assert result.found is True
        assert result.codename == "warm-owl"
        assert "checkpoint content here" in result.content
        # consume=True should delete
        assert not cp.exists()


def test_load_no_consume(tmp_path):
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        cp = tmp_path / "checkpoint_warm-owl.md"
        cp.write_text("checkpoint content here")
        result = _load("warm-owl", consume=False)
        assert result.found is True
        assert cp.exists()  # still there


def test_load_not_found(tmp_path):
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        result = _load("missing-one")
        assert result.found is False
        assert result.content == ""
        assert result.codename == "missing-one"


# ---------------------------------------------------------------------------
# _list
# ---------------------------------------------------------------------------
def test_list_returns_checkpoints(tmp_path):
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        cp = tmp_path / "checkpoint_blue-gem.md"
        cp.write_text(
            "---\nname: blue-gem checkpoint\n"
            "description: Resume point for testing\n"
            "type: project\n---\ncontent"
        )
        result = _list()
        assert isinstance(result, SporulationListResult)
        assert len(result.checkpoints) == 1
        assert result.checkpoints[0]["codename"] == "blue-gem"
        assert "testing" in result.checkpoints[0]["description"]
        assert isinstance(result.checkpoints[0]["age_days"], float)


def test_list_dir_missing(tmp_path):
    missing = tmp_path / "nope"
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", missing):
        result = _list()
        assert result.checkpoints == []


# ---------------------------------------------------------------------------
# sporulation (dispatch)
# ---------------------------------------------------------------------------
def test_sporulation_save_dispatches(tmp_path):
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path), \
         patch("metabolon.enzymes.sporulation._purge_stale", return_value=[]):
        result = sporulation(
            "save",
            context="Test context",
            where_we_left_off="step 1",
            action_needed="step 2",
            codename="swift-crow",
        )
        assert isinstance(result, SporulationSaveResult)
        assert result.codename == "swift-crow"


def test_sporulation_load_dispatches(tmp_path):
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        cp = tmp_path / "checkpoint_tall-oak.md"
        cp.write_text("some content")
        result = sporulation("load", codename="tall-oak")
        assert isinstance(result, SporulationLoadResult)
        assert result.found is True


def test_sporulation_list_dispatches(tmp_path):
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        result = sporulation("list")
        assert isinstance(result, SporulationListResult)


def test_sporulation_unknown_action():
    result = sporulation("destroy")
    assert isinstance(result, str)
    assert "Unknown action" in result
    assert "destroy" in result
