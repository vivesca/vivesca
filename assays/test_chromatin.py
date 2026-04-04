"""Tests for chromatin memory module."""

import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from metabolon.organelles.chromatin import _MarkIndex, stale_marks, type_counts


def test_type_counts():
    """Test type_counts counts marks by type correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        marks_dir = Path(tmpdir)
        index = _MarkIndex(marks_dir)

        # Create test marks with different types
        (marks_dir / "mark1.md").write_text(
            """---
name: test1
type: finding
---
Content 1
"""
        )
        (marks_dir / "mark2.md").write_text(
            """---
name: test2
type: finding
---
Content 2
"""
        )
        (marks_dir / "mark3.md").write_text(
            """---
name: test3
type: note
---
Content 3
"""
        )
        (marks_dir / "mark4.md").write_text(
            """---
name: test4
---
Content 4 (no type)
"""
        )

        index.ensure_loaded()
        counts = index.type_counts()

        assert counts == {"finding": 2, "note": 1}


def test_stale_marks():
    """Test stale_marks correctly identifies old marks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        marks_dir = Path(tmpdir)
        index = _MarkIndex(marks_dir)

        now = datetime.now(UTC).timestamp()
        day_seconds = 86400

        # Fresh mark (1 day old)
        mark1 = marks_dir / "fresh.md"
        mark1.write_text(
            """---
name: fresh
type: test
---
Fresh content
"""
        )
        # Set mtime to 1 day ago
        mark1.touch()
        os.utime(mark1, (now - day_seconds, now - day_seconds))

        # Stale mark (200 days old)
        mark2 = marks_dir / "stale.md"
        mark2.write_text(
            """---
name: stale
type: test
---
Stale content
"""
        )
        mark2.touch()
        os.utime(mark2, (now - 200 * day_seconds, now - 200 * day_seconds))

        # Very stale mark (300 days old)
        mark3 = marks_dir / "very_stale.md"
        mark3.write_text(
            """---
name: very_stale
type: test
---
Very stale content
"""
        )
        mark3.touch()
        os.utime(mark3, (now - 300 * day_seconds, now - 300 * day_seconds))

        index.ensure_loaded()

        # Default cutoff 180 days
        stale = index.stale_marks()
        assert len(stale) == 2
        # Oldest first
        assert stale[0]["name"] == "very_stale"
        assert stale[1]["name"] == "stale"
        assert stale[0]["mtime_days"] > 290
        assert stale[1]["mtime_days"] > 190

        # Custom cutoff 250 days
        stale_250 = index.stale_marks(days=250)
        assert len(stale_250) == 1
        assert stale_250[0]["name"] == "very_stale"

        # Custom cutoff 400 days
        stale_400 = index.stale_marks(days=400)
        assert len(stale_400) == 0


def test_module_level_functions_exist():
    """Test that module-level functions are available."""
    # Just check they don't throw
    counts = type_counts()
    assert isinstance(counts, dict)

    stale = stale_marks()
    assert isinstance(stale, list)
