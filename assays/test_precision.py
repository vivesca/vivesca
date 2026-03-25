"""Tests for metabolism.precision — gap detection."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from metabolon.metabolism.mismatch_repair import _detect_orphan_gaps


def test_orphan_gap_detected(tmp_path: Path) -> None:
    """A resource URI absent from all consumer files is orphaned."""
    # Create a fake resources/ dir with one @resource decorator.
    resources_dir = tmp_path / "resources"
    resources_dir.mkdir()
    (resources_dir / "example.py").write_text(
        dedent("""\
        from fastmcp.resources import resource

        @resource("vivesca://example")
        def example() -> str:
            return "hello"
        """)
    )

    # Consumer file that does NOT mention the URI.
    consumer = tmp_path / "consumer.md"
    consumer.write_text("# Nothing here\n")

    gaps = _detect_orphan_gaps(tmp_path, consumer_files=[consumer])
    assert len(gaps) == 1
    assert gaps[0].uri == "vivesca://example"
    assert gaps[0].source_file == "example.py"


def test_orphan_gap_absent_when_referenced(tmp_path: Path) -> None:
    """A resource URI present in a consumer file is NOT flagged."""
    resources_dir = tmp_path / "resources"
    resources_dir.mkdir()
    (resources_dir / "example.py").write_text(
        dedent("""\
        from fastmcp.resources import resource

        @resource("vivesca://example")
        def example() -> str:
            return "hello"
        """)
    )

    consumer = tmp_path / "consumer.md"
    consumer.write_text("Read `vivesca://example` at session start.\n")

    gaps = _detect_orphan_gaps(tmp_path, consumer_files=[consumer])
    assert len(gaps) == 0


def test_orphan_gap_no_resources_dir(tmp_path: Path) -> None:
    """No resources directory — no gaps, no crash."""
    consumer = tmp_path / "consumer.md"
    consumer.write_text("# Nothing\n")

    gaps = _detect_orphan_gaps(tmp_path, consumer_files=[consumer])
    assert gaps == []
