from __future__ import annotations
"""Integration test: histone enzyme end-to-end save → recall → verify.

Exercises the real file-I/O path through:
  histone(mark)  → chromatin.inscribe() → writes .md file
  histone(search) → chromatin.search()  → in-memory index query
Uses a temp directory so the live epigenome is never touched.
"""


import time
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.enzymes.histone import HistoneResult, histone
from metabolon.morphology.base import EffectorResult, Vital
from metabolon.organelles.chromatin import _MarkIndex


@pytest.fixture()
def tmp_marks(tmp_path: Path):
    """Redirect the chromatin module to use a temporary marks directory."""
    target = tmp_path / "marks"
    target.mkdir()

    fresh_index = _MarkIndex(target)

    with (
        patch("metabolon.organelles.chromatin.MARKS_DIR", target),
        patch("metabolon.organelles.chromatin._index", fresh_index),
    ):
        # Ensure the enzyme's lazy imports pick up the same patched module
        yield target, fresh_index


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_mark_saves_file_to_disk(tmp_marks):
    """Saving a mark should create a .md file with the right content."""
    marks_dir, _ = tmp_marks

    result = histone(action="mark", content="integration test memory", category="test")

    assert isinstance(result, EffectorResult)
    assert result.success
    assert result.data["status"] == "saved"

    saved_path = Path(result.data["path"])
    assert saved_path.exists()
    assert saved_path.suffix == ".md"

    text = saved_path.read_text()
    assert "integration test memory" in text
    assert "category: test" in text


def test_recall_finds_saved_mark(tmp_marks):
    """A mark saved via histone should be findable via search."""
    marks_dir, index = tmp_marks

    # Save
    histone(action="mark", content="recall target alpha", category="test")

    # Small pause to ensure different mtime ordering if needed
    time.sleep(0.05)

    # Recall
    result = histone(action="search", query="recall target alpha")

    assert isinstance(result, HistoneResult)
    assert "recall target alpha" in result.results


def test_roundtrip_content_preserved(tmp_marks):
    """Content saved should be retrievable with full fidelity in the file."""
    marks_dir, _ = tmp_marks

    unique = "e2e-payload-7f3a9b2"
    histone(action="mark", content=unique, category="roundtrip")

    result = histone(action="search", query=unique)
    assert unique in result.results

    # Also verify the raw file on disk
    files = list(marks_dir.glob("*.md"))
    assert len(files) == 1
    raw = files[0].read_text()
    assert unique in raw
    assert "category: roundtrip" in raw
    assert "confidence: 0.8" in raw


def test_category_filtering(tmp_marks):
    """Search with a matching category should find; non-matching should not."""
    histone(action="mark", content="cat-filter-item", category="alpha")

    # Same category → found
    found = histone(action="search", query="cat-filter-item", category="alpha")
    assert "cat-filter-item" in found.results

    # Wrong category → empty
    missing = histone(action="search", query="cat-filter-item", category="beta")
    assert "No results" in missing.results


def test_stats_reflect_saved_marks(tmp_marks):
    """stats action should count files written by mark."""
    histone(action="mark", content="stats-check-1", category="test")
    histone(action="mark", content="stats-check-2", category="test")

    result = histone(action="stats")
    assert isinstance(result, HistoneResult)
    assert "Marks: 2 files" in result.results


def test_status_returns_healthy(tmp_marks):
    """status action should return a Vital with 'ok'."""
    result = histone(action="status")
    assert isinstance(result, Vital)
    assert result.status == "ok"


def test_empty_search_returns_no_results(tmp_marks):
    """Searching an empty store returns 'No results'."""
    result = histone(action="search", query="nonexistent-mark-xyz")
    assert isinstance(result, HistoneResult)
    assert "No results" in result.results


def test_multiple_marks_all_searchable(tmp_marks):
    """Save several marks; each should be independently searchable."""
    payloads = ["mark-aaa-111", "mark-bbb-222", "mark-ccc-333"]
    for p in payloads:
        histone(action="mark", content=p, category="multi")

    for p in payloads:
        result = histone(action="search", query=p)
        assert p in result.results, f"Expected {p!r} in search results"
