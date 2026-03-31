from __future__ import annotations

"""Tests for metabolon.organelles.chromatin — file-based memory store."""

import re
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.organelles.chromatin import (
    MARKS_DIR,
    _MarkIndex,
    _parse_frontmatter,
    add,
    inscribe,
    recall,
    search,
    stale_marks,
    stats,
    status,
    type_counts,
)


# ── helpers ───────────────────────────────────────────────────────────

SAMPLE_MARK = textwrap.dedent("""\
    ---
    name: test-mark
    type: finding
    source: mcp
    category: gotcha
    confidence: 0.9
    ---
    This is the body of the mark.
""")

NO_FRONTMATTER = "Just some plain text without frontmatter.\n"

MALFORMED_FM = textwrap.dedent("""\
    ---
    name: broken
    type
    ---
    Body here.
""")


def _write_mark(directory: Path, filename: str, content: str, mtime_offset: float = 0):
    """Write a mark file and optionally set its mtime into the past."""
    p = directory / filename
    p.write_text(content)
    if mtime_offset:
        import os
        atime = mtime = p.stat().st_mtime - mtime_offset
        os.utime(p, (atime, mtime))
    return p


# ── _parse_frontmatter ────────────────────────────────────────────────

class TestParseFrontmatter:
    def test_extracts_key_value_pairs(self):
        result = _parse_frontmatter(SAMPLE_MARK)
        assert result["name"] == "test-mark"
        assert result["type"] == "finding"
        assert result["source"] == "mcp"
        assert result["category"] == "gotcha"
        assert result["confidence"] == "0.9"

    def test_empty_string_returns_empty_dict(self):
        assert _parse_frontmatter("") == {}

    def test_no_frontmatter_returns_empty_dict(self):
        assert _parse_frontmatter(NO_FRONTMATTER) == {}

    def test_malformed_frontmatter_skips_bad_lines(self):
        result = _parse_frontmatter(MALFORMED_FM)
        assert result["name"] == "broken"
        assert "type" not in result  # line had no colon

    def test_single_field(self):
        text = "---\nname: solo\n---\nBody"
        assert _parse_frontmatter(text) == {"name": "solo"}


# ── _MarkIndex ────────────────────────────────────────────────────────

class TestMarkIndex:
    def test_load_one_indexes_file(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "a.md", SAMPLE_MARK)
        idx._load_one(tmp_path / "a.md")
        assert "a.md" in idx._entries
        assert idx._entries["a.md"]["name"] == "test-mark"

    def test_load_one_skips_unreadable(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        # Nonexistent file should be skipped without error
        idx._load_one(tmp_path / "nonexistent.md")
        assert len(idx._entries) == 0

    def test_ensure_loaded_creates_dir_if_missing(self, tmp_path):
        missing = tmp_path / "nope"
        idx = _MarkIndex(missing)
        idx.ensure_loaded()
        assert missing.is_dir()

    def test_ensure_loaded_lazy(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "a.md", SAMPLE_MARK)
        idx.ensure_loaded()
        assert idx._loaded is True
        count_after_first = len(idx._entries)
        # Add another file — should NOT appear until reload
        _write_mark(tmp_path, "b.md", SAMPLE_MARK)
        assert len(idx._entries) == count_after_first

    def test_reload_forces_refresh(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "a.md", SAMPLE_MARK)
        idx.ensure_loaded()
        _write_mark(tmp_path, "b.md", SAMPLE_MARK)
        idx.reload()
        idx.ensure_loaded()
        assert "b.md" in idx._entries

    def test_invalidate_updates_single_entry(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "a.md", SAMPLE_MARK)
        idx.ensure_loaded()
        # Overwrite with new content
        new_content = SAMPLE_MARK.replace("test-mark", "updated-mark")
        (tmp_path / "a.md").write_text(new_content)
        idx.invalidate("a.md")
        assert idx._entries["a.md"]["name"] == "updated-mark"

    def test_invalidate_removes_old_inverted_index(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "a.md", SAMPLE_MARK)
        idx.ensure_loaded()
        assert "a.md" in idx._by_field.get("name", {}).get("test-mark", set())
        new_content = SAMPLE_MARK.replace("test-mark", "renamed")
        (tmp_path / "a.md").write_text(new_content)
        idx.invalidate("a.md")
        assert "a.md" not in idx._by_field.get("name", {}).get("test-mark", set())

    def test_query_regex_match(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "a.md", SAMPLE_MARK)
        idx.ensure_loaded()
        results = idx.query("body of the mark")
        assert len(results) == 1
        assert results[0]["file"] == "a.md"

    def test_query_no_match_returns_empty(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "a.md", SAMPLE_MARK)
        idx.ensure_loaded()
        assert idx.query("zzzzzzznonexistent") == []

    def test_query_filters_by_category(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "a.md", SAMPLE_MARK)
        other = SAMPLE_MARK.replace("category: gotcha", "category: other")
        _write_mark(tmp_path, "b.md", other)
        idx.ensure_loaded()
        results = idx.query("body", category="gotcha")
        assert len(results) == 1
        assert results[0]["file"] == "a.md"

    def test_query_filters_by_source_enzyme(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        other = SAMPLE_MARK.replace("source: mcp", "source: cli")
        _write_mark(tmp_path, "b.md", other)
        _write_mark(tmp_path, "a.md", SAMPLE_MARK)
        idx.ensure_loaded()
        results = idx.query("body", source_enzyme="cli")
        assert len(results) == 1
        assert results[0]["file"] == "b.md"

    def test_query_nonexistent_category_returns_empty(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        idx.ensure_loaded()
        assert idx.query("anything", category="nope") == []

    def test_query_nonexistent_source_returns_empty(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        idx.ensure_loaded()
        assert idx.query("anything", source_enzyme="nope") == []

    def test_query_respects_limit(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        for i in range(5):
            _write_mark(tmp_path, f"f{i}.md", SAMPLE_MARK)
        idx.ensure_loaded()
        results = idx.query("body", limit=2)
        assert len(results) == 2

    def test_query_truncates_content_to_500(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        long_body = "x" * 1000
        content = f"---\nname: big\ntype: finding\n---\n{long_body}\n"
        _write_mark(tmp_path, "big.md", content)
        idx.ensure_loaded()
        results = idx.query("big", limit=1)
        assert len(results) == 1
        assert len(results[0]["content"]) <= 500

    def test_entry_count(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "a.md", SAMPLE_MARK)
        _write_mark(tmp_path, "b.md", SAMPLE_MARK)
        assert idx.entry_count == 2

    def test_total_bytes(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "a.md", SAMPLE_MARK)
        idx.ensure_loaded()
        assert idx.total_bytes == len(SAMPLE_MARK.encode())

    def test_stale_marks_finds_old(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "old.md", SAMPLE_MARK, mtime_offset=200 * 86400)
        _write_mark(tmp_path, "new.md", SAMPLE_MARK, mtime_offset=10 * 86400)
        idx.ensure_loaded()
        stale = idx.stale_marks(days=180)
        assert len(stale) == 1
        assert stale[0]["file"] == "old.md"
        assert stale[0]["mtime_days"] >= 200

    def test_stale_marks_empty_when_none(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "fresh.md", SAMPLE_MARK, mtime_offset=10)
        idx.ensure_loaded()
        assert idx.stale_marks(days=180) == []

    def test_type_counts(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "a.md", SAMPLE_MARK)
        other = SAMPLE_MARK.replace("type: finding", "type: recipe")
        _write_mark(tmp_path, "b.md", other)
        _write_mark(tmp_path, "c.md", SAMPLE_MARK)
        idx.ensure_loaded()
        counts = idx.type_counts()
        assert counts == {"finding": 2, "recipe": 1}

    def test_type_counts_skips_empty_type(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        no_type = textwrap.dedent("---\nname: x\n---\nbody\n")
        _write_mark(tmp_path, "a.md", no_type)
        idx.ensure_loaded()
        assert idx.type_counts() == {}


# ── Module-level functions (patch MARKS_DIR + _index) ─────────────────

class TestRecall:
    def test_recall_queries_index(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "a.md", SAMPLE_MARK)
        idx.ensure_loaded()
        with patch("metabolon.organelles.chromatin._index", idx):
            results = recall("body of the mark")
        assert len(results) == 1

    def test_recall_empty(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        idx.ensure_loaded()
        with patch("metabolon.organelles.chromatin._index", idx):
            assert recall("nothing") == []


class TestInscribe:
    def test_inscribe_writes_file(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        idx.ensure_loaded()
        with (
            patch("metabolon.organelles.chromatin.MARKS_DIR", tmp_path),
            patch("metabolon.organelles.chromatin._index", idx),
        ):
            result = inscribe("Hello world memory", category="test", confidence=0.5)
        assert result["status"] == "saved"
        written_path = Path(result["path"])
        assert written_path.exists()
        text = written_path.read_text()
        assert "Hello world memory" in text
        assert "category: test" in text
        assert "confidence: 0.5" in text

    def test_inscribe_slug_generation(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        idx.ensure_loaded()
        with (
            patch("metabolon.organelles.chromatin.MARKS_DIR", tmp_path),
            patch("metabolon.organelles.chromatin._index", idx),
        ):
            result = inscribe("Some Special Memory! @#$")
        assert result["file"].startswith("auto_some-special-memory")
        assert result["file"].endswith(".md")

    def test_inscribe_creates_directory(self, tmp_path):
        missing = tmp_path / "new_dir"
        idx = _MarkIndex(missing)
        idx.ensure_loaded()
        with (
            patch("metabolon.organelles.chromatin.MARKS_DIR", missing),
            patch("metabolon.organelles.chromatin._index", idx),
        ):
            result = inscribe("test content")
        assert missing.is_dir()
        assert Path(result["path"]).exists()


class TestSearchAlias:
    def test_search_delegates_to_recall(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "a.md", SAMPLE_MARK)
        idx.ensure_loaded()
        with patch("metabolon.organelles.chromatin._index", idx):
            results = search("body of the mark")
        assert len(results) == 1


class TestAddAlias:
    def test_add_delegates_to_inscribe(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        idx.ensure_loaded()
        with (
            patch("metabolon.organelles.chromatin.MARKS_DIR", tmp_path),
            patch("metabolon.organelles.chromatin._index", idx),
        ):
            result = add("alias test content")
        assert result["status"] == "saved"


class TestStats:
    def test_stats_returns_counts(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "a.md", SAMPLE_MARK)
        idx.ensure_loaded()
        with patch("metabolon.organelles.chromatin._index", idx):
            s = stats()
        assert s["count"] == 1
        assert "size_kb" in s
        assert "path" in s


class TestStatus:
    def test_status_string(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "a.md", SAMPLE_MARK)
        idx.ensure_loaded()
        with patch("metabolon.organelles.chromatin._index", idx):
            s = status()
        assert "1 files" in s
        assert "KB" in s


class TestStaleMarksFunction:
    def test_stale_marks_delegates(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "old.md", SAMPLE_MARK, mtime_offset=200 * 86400)
        idx.ensure_loaded()
        with patch("metabolon.organelles.chromatin._index", idx):
            stale = stale_marks(days=180)
        assert len(stale) == 1


class TestTypeCountsFunction:
    def test_type_counts_delegates(self, tmp_path):
        idx = _MarkIndex(tmp_path)
        _write_mark(tmp_path, "a.md", SAMPLE_MARK)
        idx.ensure_loaded()
        with patch("metabolon.organelles.chromatin._index", idx):
            counts = type_counts()
        assert "finding" in counts
