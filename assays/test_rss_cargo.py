"""Tests for endocytosis_rss/cargo.py - JSONL cargo store."""

from datetime import UTC, datetime
from pathlib import Path

from metabolon.organelles.endocytosis_rss.cargo import (
    append_cargo,
    recall_cargo,
    recall_title_prefixes,
    rotate_cargo,
    _title_prefix,
)


def test_append_cargo_creates_file(tmp_path):
    """Test append_cargo creates file and writes articles."""
    cargo_path = tmp_path / "cargo.jsonl"
    articles = [
        {"title": "Test Article", "source": "Feed", "score": 5},
    ]
    
    append_cargo(cargo_path, articles)
    assert cargo_path.exists()
    content = cargo_path.read_text()
    assert "Test Article" in content


def test_append_cargo_appends_not_overwrite(tmp_path):
    """Test append_cargo appends to existing file."""
    cargo_path = tmp_path / "cargo.jsonl"
    
    append_cargo(cargo_path, [{"title": "First"}])
    append_cargo(cargo_path, [{"title": "Second"}])
    
    lines = cargo_path.read_text().strip().split("\n")
    assert len(lines) == 2


def test_recall_cargo_empty_file(tmp_path):
    """Test recall_cargo returns empty list for nonexistent file."""
    result = recall_cargo(tmp_path / "nonexistent.jsonl")
    assert result == []


def test_recall_cargo_reads_all(tmp_path):
    """Test recall_cargo reads all entries."""
    cargo_path = tmp_path / "cargo.jsonl"
    articles = [
        {"title": "A", "date": "2024-01-10"},
        {"title": "B", "date": "2024-01-15"},
    ]
    append_cargo(cargo_path, articles)
    
    result = recall_cargo(cargo_path)
    assert len(result) == 2


def test_recall_cargo_filters_by_since(tmp_path):
    """Test recall_cargo filters entries by since date."""
    cargo_path = tmp_path / "cargo.jsonl"
    articles = [
        {"title": "Old", "date": "2024-01-10"},
        {"title": "New", "date": "2024-01-15"},
    ]
    append_cargo(cargo_path, articles)
    
    result = recall_cargo(cargo_path, since="2024-01-12")
    assert len(result) == 1
    assert result[0]["title"] == "New"


def test_recall_cargo_filters_by_month(tmp_path):
    """Test recall_cargo filters entries by month prefix."""
    cargo_path = tmp_path / "cargo.jsonl"
    articles = [
        {"title": "Jan", "date": "2024-01-15"},
        {"title": "Feb", "date": "2024-02-15"},
    ]
    append_cargo(cargo_path, articles)
    
    result = recall_cargo(cargo_path, month="2024-02")
    assert len(result) == 1
    assert result[0]["title"] == "Feb"


def test_recall_cargo_skips_invalid_json(tmp_path):
    """Test recall_cargo skips malformed JSON lines."""
    cargo_path = tmp_path / "cargo.jsonl"
    cargo_path.write_text('{"title": "Valid"}\ninvalid json\n{"title": "Also Valid"}\n')
    
    result = recall_cargo(cargo_path)
    assert len(result) == 2


def test_recall_cargo_skips_non_dicts(tmp_path):
    """Test recall_cargo skips non-dict JSON values."""
    cargo_path = tmp_path / "cargo.jsonl"
    cargo_path.write_text('["list", "not", "dict"]\n{"title": "Valid"}\n42\n')
    
    result = recall_cargo(cargo_path)
    assert len(result) == 1


def test_recall_title_prefixes_extracts(tmp_path):
    """Test recall_title_prefixes extracts normalized prefixes."""
    cargo_path = tmp_path / "cargo.jsonl"
    articles = [
        {"title": "Bitcoin Price Surges to New Highs"},
        {"title": "Ethereum Update Released"},
    ]
    append_cargo(cargo_path, articles)
    
    prefixes = recall_title_prefixes(cargo_path)
    assert len(prefixes) == 2


def test_rss_cargo_recall_title_prefixes_empty_file(tmp_path):
    """Test recall_title_prefixes returns empty set for nonexistent file."""
    result = recall_title_prefixes(tmp_path / "nonexistent.jsonl")
    assert result == set()


def test_title_prefix_matches_log():
    """Test cargo._title_prefix matches log._title_prefix logic."""
    from metabolon.organelles.endocytosis_rss.log import _title_prefix as log_prefix
    
    title = "The Quick Brown Fox Jumps Over"
    assert _title_prefix(title) == log_prefix(title)


def test_rotate_cargo_no_rotation_needed(tmp_path):
    """Test rotate_cargo does nothing when all entries are recent."""
    cargo_path = tmp_path / "cargo.jsonl"
    archive_dir = tmp_path / "archive"
    
    articles = [{"title": "Recent", "date": "2024-01-15"}]
    append_cargo(cargo_path, articles)
    
    now = datetime(2024, 1, 16, tzinfo=UTC)
    rotate_cargo(cargo_path, archive_dir, retain_days=14, now=now)
    
    assert not archive_dir.exists()


def test_rotate_cargo_archives_old_entries(tmp_path):
    """Test rotate_cargo moves old entries to archive."""
    cargo_path = tmp_path / "cargo.jsonl"
    archive_dir = tmp_path / "archive"
    
    articles = [
        {"title": "Old", "date": "2024-01-01"},
        {"title": "Recent", "date": "2024-01-20"},
    ]
    append_cargo(cargo_path, articles)
    
    now = datetime(2024, 1, 20, tzinfo=UTC)
    rotate_cargo(cargo_path, archive_dir, retain_days=7, now=now)
    
    # Old entry should be archived
    archive_path = archive_dir / "cargo-2024-01.jsonl"
    assert archive_path.exists()
    
    # Cargo should only have recent
    remaining = recall_cargo(cargo_path)
    assert len(remaining) == 1
    assert remaining[0]["title"] == "Recent"


def test_rotate_cargo_nonexistent_file(tmp_path):
    """Test rotate_cargo handles nonexistent cargo file."""
    cargo_path = tmp_path / "nonexistent.jsonl"
    archive_dir = tmp_path / "archive"
    
    # Should not raise
    rotate_cargo(cargo_path, archive_dir, retain_days=14)
