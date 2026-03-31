#!/usr/bin/env python3
"""Tests for queue-gen effector."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Load the queue-gen module
queue_gen_path = Path("/home/terry/germline/effectors/queue-gen")
queue_gen_code = queue_gen_path.read_text()
_queue_gen_dict = {}
exec(queue_gen_code, _queue_gen_dict)


class QueueGenModule:
    """Wrapper for accessing queue-gen module attributes."""
    _original_keys = set(_queue_gen_dict.keys())

    def __getattr__(self, name):
        return _queue_gen_dict[name]

    def __setattr__(self, name, value):
        _queue_gen_dict[name] = value

    def __delattr__(self, name):
        if name in QueueGenModule._original_keys:
            pass
        elif name in _queue_gen_dict:
            del _queue_gen_dict[name]


qg = QueueGenModule()


# ---------------------------------------------------------------------------
# Test file_to_test_name
# ---------------------------------------------------------------------------

def test_file_to_test_name_with_hyphen():
    """Test converting hyphenated names to test names."""
    path = Path("effectors/foo-bar")
    assert qg.file_to_test_name(path) == "test_foo_bar.py"


def test_file_to_test_name_with_underscore():
    """Test converting underscored names to test names."""
    path = Path("effectors/foo_bar.py")
    assert qg.file_to_test_name(path) == "test_foo_bar.py"


def test_file_to_test_name_nested_path():
    """Test converting nested paths to test names."""
    path = Path("metabolon/organelles/baz.py")
    assert qg.file_to_test_name(path) == "test_baz.py"


def test_file_to_test_name_no_extension():
    """Test converting file without extension."""
    path = Path("effectors/script")
    assert qg.file_to_test_name(path) == "test_script.py"


# ---------------------------------------------------------------------------
# Test get_file_lines
# ---------------------------------------------------------------------------

def test_get_file_lines_counts_non_empty():
    """Test that get_file_lines counts non-empty lines."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("line1\n\nline2\nline3\n")
        f.flush()
        result = qg.get_file_lines(Path(f.name))
    Path(f.name).unlink()
    assert result == 3


def test_get_file_lines_empty_file():
    """Test that get_file_lines returns 0 for empty file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("\n\n\n")
        f.flush()
        result = qg.get_file_lines(Path(f.name))
    Path(f.name).unlink()
    assert result == 0


def test_get_file_lines_handles_error():
    """Test that get_file_lines returns 0 on error."""
    result = qg.get_file_lines(Path("/nonexistent/file.py"))
    assert result == 0


# ---------------------------------------------------------------------------
# Test batch_entries
# ---------------------------------------------------------------------------

def test_batch_entries_large_file_solo():
    """Test that large files get their own batch."""
    FileEntry = _queue_gen_dict["FileEntry"]
    large_entry = FileEntry(Path("big.py"), 600, "test_big.py")
    small_entry = FileEntry(Path("small.py"), 100, "test_small.py")

    batches = qg.batch_entries([large_entry, small_entry])

    assert len(batches) == 2
    assert len(batches[0]) == 1
    assert batches[0][0].lines >= qg.LARGE


def test_batch_entries_medium_files_batched():
    """Test that medium files are batched in pairs."""
    FileEntry = _queue_gen_dict["FileEntry"]
    entries = [
        FileEntry(Path(f"med{i}.py"), 250, f"test_med{i}.py")
        for i in range(4)
    ]

    batches = qg.batch_entries(entries)

    # 4 medium files = 2 batches of 2
    assert len(batches) == 2
    assert all(len(b) == 2 for b in batches)


def test_batch_entries_small_files_batched():
    """Test that small files are batched in groups of 4."""
    FileEntry = _queue_gen_dict["FileEntry"]
    entries = [
        FileEntry(Path(f"small{i}.py"), 100, f"test_small{i}.py")
        for i in range(8)
    ]

    batches = qg.batch_entries(entries)

    # 8 small files = 2 batches of 4
    assert len(batches) == 2
    assert all(len(b) == 4 for b in batches)


def test_batch_entries_respects_size_order():
    """Test that entries are processed in size order."""
    FileEntry = _queue_gen_dict["FileEntry"]
    entries = [
        FileEntry(Path("tiny.py"), 50, "test_tiny.py"),
        FileEntry(Path("huge.py"), 800, "test_huge.py"),
        FileEntry(Path("medium.py"), 300, "test_medium.py"),
    ]

    batches = qg.batch_entries(entries)

    # Large file should be first (sorted descending)
    assert batches[0][0].lines == 800


# ---------------------------------------------------------------------------
# Test generate_entry
# ---------------------------------------------------------------------------

def test_generate_entry_single_file():
    """Test generating entry for a single file."""
    FileEntry = _queue_gen_dict["FileEntry"]
    entry = FileEntry(Path("/home/terry/germline/effectors/foo.py"), 150, "test_foo.py")

    result = qg.generate_entry([entry], "zhipu", 30)

    assert "#### Write tests for effectors/foo.py" in result
    assert "test_foo.py" in result
    assert "--provider zhipu" in result
    assert "--max-turns 30" in result


def test_generate_entry_large_file():
    """Test that large files get higher turn limit."""
    FileEntry = _queue_gen_dict["FileEntry"]
    entry = FileEntry(Path("/home/terry/germline/effectors/big.py"), 700, "test_big.py")

    result = qg.generate_entry([entry], "volcano", 30)

    assert "--max-turns 50" in result  # 30 + 20 for large files


def test_generate_entry_large_file_caps_at_60():
    """Test that turn limit caps at 60 for large files."""
    FileEntry = _queue_gen_dict["FileEntry"]
    entry = FileEntry(Path("/home/terry/germline/effectors/huge.py"), 1000, "test_huge.py")

    result = qg.generate_entry([entry], "volcano", 50)

    assert "--max-turns 60" in result  # capped


def test_generate_entry_multiple_files():
    """Test generating entry for multiple files."""
    FileEntry = _queue_gen_dict["FileEntry"]
    entries = [
        FileEntry(Path("/home/terry/germline/effectors/a.py"), 100, "test_a.py"),
        FileEntry(Path("/home/terry/germline/effectors/b.py"), 100, "test_b.py"),
    ]

    result = qg.generate_entry(entries, "infini", 30)

    assert "#### Write tests for 2 modules (200 lines total)" in result
    assert "test_a.py" in result
    assert "test_b.py" in result
    assert "effectors/a.py" in result
    assert "effectors/b.py" in result


def test_generate_entry_includes_retry_marker():
    """Test that entries have the checkbox format for retry tracking."""
    FileEntry = _queue_gen_dict["FileEntry"]
    entry = FileEntry(Path("/home/terry/germline/effectors/foo.py"), 100, "test_foo.py")

    result = qg.generate_entry([entry], "zhipu", 30)

    assert "- [ ]" in result


# ---------------------------------------------------------------------------
# Test scan_directory integration (uses temp directories)
# ---------------------------------------------------------------------------

def test_scan_directory_finds_untested_files():
    """Test that scan_directory finds files without tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test file in assays (mocked)
        assays_dir = tmppath / "assays"
        assays_dir.mkdir()
        (assays_dir / "test_tested.py").touch()

        # Create source files
        src_dir = tmppath / "src"
        src_dir.mkdir()
        (src_dir / "tested.py").write_text("def foo(): pass\n")
        (src_dir / "untested.py").write_text("def bar(): pass\n")

        with patch.object(qg, "ASSAYS_DIR", assays_dir):
            with patch.object(qg, "GERMLINE", tmppath):
                entries = qg.scan_directory(src_dir)

        assert len(entries) == 1
        assert entries[0].path.name == "untested.py"


def test_scan_directory_excludes_patterns():
    """Test that scan_directory excludes configured patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        src_dir = tmppath / "src"
        src_dir.mkdir()

        # Create files that should be excluded
        (src_dir / "__pycache__").mkdir()
        (src_dir / "__pycache__" / "cache.pyc").write_text("binary")
        (src_dir / "test_foo.py").write_text("def test_foo(): pass\n")
        (src_dir / "conftest.py").write_text("fixtures\n")
        (src_dir / "README.md").write_text("docs\n")

        # Create file that should be included
        (src_dir / "actual.py").write_text("def real(): pass\n")

        with patch.object(qg, "ASSAYS_DIR", tmppath / "assays"):
            entries = qg.scan_directory(src_dir)

        names = [e.path.name for e in entries]
        assert "actual.py" in names
        assert "test_foo.py" not in names
        assert "conftest.py" not in names
        assert "README.md" not in names


def test_scan_directory_sorted_by_size():
    """Test that scan_directory returns entries sorted by size descending."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        src_dir = tmppath / "src"
        src_dir.mkdir()

        (src_dir / "small.py").write_text("a\n")
        (src_dir / "big.py").write_text("\n".join(f"line{i}" for i in range(100)))
        (src_dir / "medium.py").write_text("\n".join(f"line{i}" for i in range(50)))

        with patch.object(qg, "ASSAYS_DIR", tmppath / "assays"):
            entries = qg.scan_directory(src_dir)

        assert entries[0].path.name == "big.py"
        assert entries[-1].path.name == "small.py"


# ---------------------------------------------------------------------------
# Test has_test
# ---------------------------------------------------------------------------

def test_has_test_returns_true_for_existing():
    """Test has_test returns True when test exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "test_exists.py").touch()

        with patch.object(qg, "ASSAYS_DIR", tmppath):
            assert qg.has_test("test_exists.py") is True


def test_has_test_returns_false_for_missing():
    """Test has_test returns False when test doesn't exist."""
    with patch.object(qg, "ASSAYS_DIR", Path("/nonexistent")):
        assert qg.has_test("test_missing.py") is False
