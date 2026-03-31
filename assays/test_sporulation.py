"""Tests for sporulation checkpoint module.

Mocks filesystem to avoid actual file operations.
"""
import pytest
from unittest.mock import patch, MagicMock

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


def test_gen_codename():
    """Test generating unique codenames."""
    existing = {"happy-cat", "bold-fox"}
    result = _gen_codename(existing)
    assert result not in existing
    assert "-" in result
    assert len(result.split("-")) == 2


def test_gen_codename_collision_returns_any():
    """Test after 50 collisions it still returns something."""
    existing = {
        f"{adj}-{noun}"
        for adj in [
            "happy", "calm", "bold", "warm", "keen", "swift", "bright", "quiet",
            "wild", "crisp", "pale", "dark", "soft", "sharp", "cool", "odd", "rare",
            "slim", "tall", "deep", "gold", "iron", "blue", "red", "green", "silver",
            "amber", "coral", "jade", "onyx",
        ]
        for noun in [
            "cat", "fox", "owl", "elk", "bee", "ant", "bat", "cod", "eel", "yak",
            "oak", "elm", "fig", "ash", "bay", "gem", "orb", "arc", "key", "bell",
            "star", "moon", "rain", "leaf", "wave", "fern", "moss", "pine", "crow", "hawk",
        ]
    }
    # All possible combinations are already taken
    result = _gen_codename(existing)
    assert result
    assert "-" in result


def test_existing_codenames_no_dir():
    """Test existing codenames when directory doesn't exist."""
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR") as mock_dir:
        mock_dir.exists.return_value = False
        result = _existing_codenames()
        assert result == set()


def test_existing_codenames_with_files():
    """Test extracting existing codenames from glob."""
    mock_file1 = MagicMock()
    mock_file1.stem = "checkpoint_happy-cat"
    mock_file2 = MagicMock()
    mock_file2.stem = "checkpoint_bold-fox"

    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR") as mock_dir:
        mock_dir.exists.return_value = True
        mock_dir.glob.return_value = [mock_file1, mock_file2]
        result = _existing_codenames()
        assert result == {"happy-cat", "bold-fox"}


def test_purge_stale_no_dir():
    """Test purge_stale when directory doesn't exist."""
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR") as mock_dir:
        mock_dir.exists.return_value = False
        result = _purge_stale()
        assert result == []


def test_purge_stale_removes_old_files():
    """Test purge_stale removes files older than 7 days."""
    from datetime import UTC, datetime
    now_ts = datetime.now(UTC).timestamp()

    mock_old = MagicMock()
    mock_old.stem = "checkpoint_old-spore"
    mock_old.stat().st_mtime = now_ts - (8 * 86400)

    mock_new = MagicMock()
    mock_new.stem = "checkpoint_new-spore"
    mock_new.stat().st_mtime = now_ts - (3 * 86400)

    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR") as mock_dir:
        mock_dir.exists.return_value = True
        mock_dir.glob.return_value = [mock_old, mock_new]
        result = _purge_stale()
        assert "old-spore" in result
        mock_old.unlink.assert_called_once()
        mock_new.unlink.assert_not_called()


def test_save_auto_codename(tmp_path):
    """Test saving with auto-generated codename."""
    test_dir = tmp_path / "test_checkpoints"

    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", test_dir):
        result = _save(
            context="Working on sporulation tests",
            where_we_left_off="Need to write more tests",
            action_needed="Run pytest to verify",
            summary="Writing unit tests",
        )
        assert isinstance(result, SporulationSaveResult)
        assert result.codename
        assert "-" in result.codename
        assert (test_dir / f"checkpoint_{result.codename}.md").exists()
        content = (test_dir / f"checkpoint_{result.codename}.md").read_text()
        assert "sporulation tests" in content
        assert result.codename in content


def test_save_custom_codename_success(tmp_path):
    """Test saving with custom codename."""
    test_dir = tmp_path / "test_checkpoints"
    test_dir.mkdir()

    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", test_dir):
        result = _save(
            context="Test context",
            where_we_left_off="Resume here",
            action_needed="Do work",
            codename="test-spore",
        )
        assert result.codename == "test-spore"
        assert (test_dir / "checkpoint_test-spore.md").exists()


def test_save_custom_codename_already_exists(tmp_path):
    """Test saving with existing custom codename returns error."""
    test_dir = tmp_path / "test_checkpoints"
    test_dir.mkdir()
    (test_dir / "checkpoint_existing-spore.md").write_text("existing")

    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", test_dir):
        result = _save(
            context="Test",
            where_we_left_off="Test",
            action_needed="Test",
            codename="existing-spore",
        )
        assert result.codename == "existing-spore"
        assert result.path == ""


def test_load_not_found():
    """Test loading non-existent checkpoint."""
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR") as mock_dir:
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        with patch("metabolon.enzymes.sporulation._checkpoint_path", return_value=mock_path):
            result = _load("missing-spore")
            assert isinstance(result, SporulationLoadResult)
            assert result.found is False
            assert result.content == ""


def test_load_found_consume(tmp_path):
    """Test loading found checkpoint with consume=True."""
    test_dir = tmp_path / "test_checkpoints"
    test_dir.mkdir()
    codename = "test-load"
    content = """---
name: test checkpoint
description: Test description
---
## Context
Test context
"""
    (test_dir / f"checkpoint_{codename}.md").write_text(content)

    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", test_dir):
        result = _load(codename, consume=True)
        assert result.found is True
        assert "Test context" in result.content
        assert not (test_dir / f"checkpoint_{codename}.md").exists()


def test_load_found_no_consume(tmp_path):
    """Test loading found checkpoint with consume=False leaves file."""
    test_dir = tmp_path / "test_checkpoints"
    test_dir.mkdir()
    codename = "test-load-noconsume"
    content = "Test content"
    (test_dir / f"checkpoint_{codename}.md").write_text(content)

    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", test_dir):
        result = _load(codename, consume=False)
        assert result.found is True
        assert result.content == "Test content"
        assert (test_dir / f"checkpoint_{codename}.md").exists()


def test_list_no_dir():
    """Test listing when no directory exists."""
    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR") as mock_dir:
        mock_dir.exists.return_value = False
        result = _list()
        assert isinstance(result, SporulationListResult)
        assert result.checkpoints == []


def test_list_with_checkpoints(tmp_path):
    """Test listing existing checkpoints."""
    test_dir = tmp_path / "test_checkpoints"
    test_dir.mkdir()

    # Create two checkpoints
    cp1 = test_dir / "checkpoint_list-test1.md"
    cp1.write_text("""---
description: First test checkpoint
---
Context
""")
    cp2 = test_dir / "checkpoint_list-test2.md"
    cp2.write_text("""---
description: Second test checkpoint
---
Context
""")
    # Access the files to set mtime correctly
    cp1.touch()
    cp2.touch()

    with patch("metabolon.enzymes.sporulation._CHECKPOINT_DIR", test_dir):
        result = _list()
        assert len(result.checkpoints) == 2
        codenames = [cp["codename"] for cp in result.checkpoints]
        descriptions = [cp["description"] for cp in result.checkpoints]
        assert "list-test1" in codenames
        assert "list-test2" in codenames
        assert "First test checkpoint" in descriptions
        assert all(cp["age_days"] >= 0 for cp in result.checkpoints)


def test_sporulation_unknown_action():
    """Test sporulation tool with unknown action."""
    result = sporulation("bad_action")
    assert "Unknown action" in result
    assert "save, load, or list" in result


def test_sporulation_save():
    """Test sporulation dispatch to save."""
    with patch("metabolon.enzymes.sporulation._save") as mock_save:
        mock_save.return_value = SporulationSaveResult(codename="test", path="/test", purged=[])
        result = sporulation("save", context="test", where_we_left_off="test", action_needed="test")
        mock_save.assert_called_once()
        assert isinstance(result, SporulationSaveResult)


def test_sporulation_load():
    """Test sporulation dispatch to load."""
    with patch("metabolon.enzymes.sporulation._load") as mock_load:
        mock_load.return_value = SporulationLoadResult(codename="test", content="", found=False)
        result = sporulation("load", codename="test")
        mock_load.assert_called_once()
        assert isinstance(result, SporulationLoadResult)


def test_sporulation_list():
    """Test sporulation dispatch to list."""
    with patch("metabolon.enzymes.sporulation._list") as mock_list:
        mock_list.return_value = SporulationListResult(checkpoints=[])
        result = sporulation("list")
        mock_list.assert_called_once()
        assert isinstance(result, SporulationListResult)
