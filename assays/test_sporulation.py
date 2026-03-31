"""Tests for sporulation checkpoint module."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from datetime import UTC, datetime, timedelta
from pathlib import Path

from metabolon.enzymes.sporulation import (
    _gen_codename,
    _checkpoint_path,
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
from metabolon.morphology import Secretion


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


# --- Additional tests for fuller coverage ---


def test_checkpoint_path_format():
    """_checkpoint_path returns correct filename."""
    result = _checkpoint_path("bold-fox")
    assert isinstance(result, Path)
    assert result.name == "checkpoint_bold-fox.md"


def test_checkpoint_path_preserves_codename():
    """_checkpoint_path embeds the codename verbatim."""
    p = _checkpoint_path("keen-owl")
    assert "keen-owl" in str(p)


def test_existing_codenames_extracts_from_stems(tmp_path):
    """_existing_codenames strips 'checkpoint_' prefix from stem."""
    (tmp_path / "checkpoint_alpha-beta.md").write_text("a")
    (tmp_path / "checkpoint_gamma-delta.md").write_text("b")
    # non-matching file should be ignored by glob
    (tmp_path / "other_file.txt").write_text("c")
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        result = _existing_codenames()
    assert result == {"alpha-beta", "gamma-delta"}


def test_purge_stale_ignores_oserror():
    """_purge_stale catches OSError from stat/unlink and continues."""
    mock_dir = MagicMock(spec=Path)
    mock_dir.exists.return_value = True
    mock_p = MagicMock(spec=Path)
    mock_p.stem = "checkpoint_bad-file"
    mock_p.stat.side_effect = OSError("permission denied")
    mock_dir.glob.return_value = [mock_p]
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", mock_dir):
        result = _purge_stale()
    assert result == []


def test_save_with_custom_codename(tmp_path):
    """_save uses the provided codename."""
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        result = _save(
            context="ctx",
            where_we_left_off="wlo",
            action_needed="an",
            codename="swift-elk",
        )
    assert result.codename == "swift-elk"
    assert Path(result.path).exists()
    content = Path(result.path).read_text()
    assert "## Context" in content
    assert "## Where we left off" in content
    assert "## Action needed" in content
    assert "## Passcode: swift-elk" in content


def test_save_frontmatter_contains_name_and_type(tmp_path):
    """Saved checkpoint has correct YAML frontmatter."""
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        result = _save(
            context="ctx",
            where_we_left_off="wlo",
            action_needed="an",
            summary="My summary",
            codename="warm-bee",
        )
    content = Path(result.path).read_text()
    assert "name: warm-bee checkpoint" in content
    assert "type: project" in content
    assert "My summary" in content


def test_save_uses_context_prefix_when_no_summary(tmp_path):
    """When summary is empty, description uses first 80 chars of context."""
    long_ctx = "A" * 200
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        result = _save(
            context=long_ctx,
            where_we_left_off="wlo",
            action_needed="an",
            codename="pale-moon",
        )
    content = Path(result.path).read_text()
    # The description line should contain a truncated version
    desc_line = [l for l in content.splitlines() if l.startswith("description:")][0]
    assert "A" * 80 in desc_line


def test_save_creates_directory(tmp_path):
    """_save calls mkdir(parents=True, exist_ok=True) on checkpoint dir."""
    new_dir = tmp_path / "sub" / "dir"
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", new_dir):
        result = _save(
            context="ctx",
            where_we_left_off="wlo",
            action_needed="an",
            codename="deep-fern",
        )
    assert new_dir.exists()
    assert Path(result.path).exists()


def test_save_reports_purged_checkpoints(tmp_path):
    """_save returns list of purged stale checkpoints."""
    stale = tmp_path / "checkpoint_old-one.md"
    stale.write_text("stale")
    eight_days_ago = (datetime.now(UTC) - timedelta(days=8)).timestamp()
    import os
    os.utime(stale, (eight_days_ago, eight_days_ago))
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        result = _save(
            context="ctx",
            where_we_left_off="wlo",
            action_needed="an",
            codename="new-one",
        )
    assert "old-one" in result.purged


def test_load_handles_oserror_on_unlink(tmp_path):
    """_load with consume=True still returns content if unlink fails."""
    path = tmp_path / "checkpoint_rare-gem.md"
    path.write_text("data")
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        with patch.object(Path, "unlink", side_effect=OSError("busy")):
            result = _load("rare-gem", consume=True)
    assert result.found is True
    assert result.content == "data"


def test_list_handles_oserror_on_read(tmp_path):
    """_list handles OSError on read_text gracefully."""
    (tmp_path / "checkpoint_corrupt.md").write_text("ok")
    real_read = Path.read_text

    def flaky_read(self, *args, **kwargs):
        if "corrupt" in str(self):
            raise OSError("read error")
        return real_read(self, *args, **kwargs)

    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        with patch.object(Path, "read_text", flaky_read):
            result = _list()
    assert len(result.checkpoints) == 1
    assert result.checkpoints[0]["codename"] == "corrupt"
    assert result.checkpoints[0]["description"] == ""


def test_list_sorts_by_path(tmp_path):
    """_list returns checkpoints sorted by filename."""
    for name in ["checkpoint_b-fox.md", "checkpoint_a-cat.md", "checkpoint_c-elk.md"]:
        (tmp_path / name).write_text(f"---\ndescription: {name}\n---\n")
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", tmp_path):
        result = _list()
    names = [c["codename"] for c in result.checkpoints]
    assert names == ["a-cat", "b-fox", "c-elk"]


def test_sporulation_save_dispatch():
    """sporulation dispatches to _save on action='save'."""
    with patch("metabolon.enzymes.sporulation._save") as mock_save:
        mock_save.return_value = SporulationSaveResult(
            codename="x", path="/p", purged=[]
        )
        result = sporulation(
            action="save",
            context="c",
            where_we_left_off="w",
            action_needed="a",
            summary="s",
            codename="x",
        )
        mock_save.assert_called_once_with(
            context="c",
            where_we_left_off="w",
            action_needed="a",
            summary="s",
            codename="x",
        )
    assert isinstance(result, SporulationSaveResult)


def test_sporulation_load_dispatch():
    """sporulation dispatches to _load on action='load'."""
    with patch("metabolon.enzymes.sporulation._load") as mock_load:
        mock_load.return_value = SporulationLoadResult(
            codename="y", content="z", found=True
        )
        result = sporulation(action="load", codename="y", consume=False)
        mock_load.assert_called_once_with(codename="y", consume=False)
    assert isinstance(result, SporulationLoadResult)


def test_sporulation_load_default_consume_true():
    """sporulation load passes consume=True by default."""
    with patch("metabolon.enzymes.sporulation._load") as mock_load:
        mock_load.return_value = SporulationLoadResult(
            codename="z", content="", found=False
        )
        sporulation(action="load", codename="z")
        mock_load.assert_called_once_with(codename="z", consume=True)


def test_result_models_inherit_secretion():
    """All result classes are Secretion subclasses."""
    assert issubclass(SporulationSaveResult, Secretion)
    assert issubclass(SporulationLoadResult, Secretion)
    assert issubclass(SporulationListResult, Secretion)


def test_result_models_are_pydantic():
    """Result models can be instantiated and serialized."""
    sr = SporulationSaveResult(codename="a", path="/b", purged=["c"])
    assert sr.model_dump()["codename"] == "a"

    lr = SporulationLoadResult(codename="x", content="y", found=True)
    assert lr.model_dump()["found"] is True

    li = SporulationListResult(checkpoints=[{"codename": "z", "description": "", "age_days": 0}])
    assert li.model_dump()["checkpoints"][0]["codename"] == "z"
