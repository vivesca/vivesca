"""Tests for demethylase — active memory erasure."""

from __future__ import annotations

from pathlib import Path

import pytest

from metabolon.organelles.demethylase import (
    DemethylaseReport,
    MarkAnalysis,
    analyze_mark,
    sweep,
)


def _write_mark(path: Path, name: str, mtype: str = "feedback", **extra_fm):
    """Write a minimal mark file with frontmatter."""
    fm_lines = [f"name: {name}", f"type: {mtype}"]
    for k, v in extra_fm.items():
        fm_lines.append(f"{k}: {v}")
    path.write_text(f"---\n" + "\n".join(fm_lines) + "\n---\n\nContent here.\n")


@pytest.fixture
def marks_dir(tmp_path: Path) -> Path:
    d = tmp_path / "marks"
    d.mkdir()
    _write_mark(d / "feedback_keep_digging.md", "Keep digging", "feedback")
    _write_mark(d / "finding_stale_path.md", "Stale path finding", "finding")
    _write_mark(d / "user_hair_care.md", "Hair care", "user", source="cc")
    _write_mark(d / "project_old_thing.md", "Old project", "project")
    _write_mark(d / "checkpoint_abc.md", "Checkpoint", "project")
    _write_mark(d / "feedback_protected.md", "Protected", "feedback", protected="true")
    _write_mark(d / "feedback_with_source.md", "Sourced", "feedback", source="gemini", durability="acetyl")
    return d


def test_analyze_mark(marks_dir: Path):
    mark = analyze_mark(marks_dir / "feedback_keep_digging.md")
    assert mark.name == "Keep digging"
    assert mark.mark_type == "feedback"
    assert mark.protected  # core behavioral correction
    assert mark.durability == "methyl"


def test_acetyl_inferred_from_checkpoint(marks_dir: Path):
    mark = analyze_mark(marks_dir / "checkpoint_abc.md")
    assert mark.durability == "acetyl"


def test_explicit_durability(marks_dir: Path):
    mark = analyze_mark(marks_dir / "feedback_with_source.md")
    assert mark.durability == "acetyl"
    assert mark.source == "gemini"


def test_protected_from_frontmatter(marks_dir: Path):
    mark = analyze_mark(marks_dir / "feedback_protected.md")
    assert mark.protected


def test_source_from_frontmatter(marks_dir: Path):
    mark = analyze_mark(marks_dir / "user_hair_care.md")
    assert mark.source == "cc"


def test_sweep_counts(marks_dir: Path):
    report = sweep(marks_dir, threshold_days=90, dry_run=True)
    assert report.total_marks == 7
    assert report.protected_marks >= 2  # keep_digging + explicit protected


def test_sweep_finds_clusters(marks_dir: Path):
    # Add more marks to create a cluster
    _write_mark(marks_dir / "feedback_tone_formal.md", "Tone formal", "feedback")
    _write_mark(marks_dir / "feedback_tone_casual.md", "Tone casual", "feedback")
    report = sweep(marks_dir, threshold_days=90, dry_run=True)
    topic_names = [c["topic"] for c in report.mark_clusters]
    assert any("tone" in t for t in topic_names)


def test_sweep_dry_run_preserves_files(marks_dir: Path):
    # Make a mark old enough to be stale by using acetyl + any age > 14d
    # Can't easily fake mtime in test, so just verify dry_run doesn't delete
    count_before = len(list(marks_dir.glob("*.md")))
    sweep(marks_dir, threshold_days=0, dry_run=True)
    count_after = len(list(marks_dir.glob("*.md")))
    assert count_before == count_after


def test_type_distribution(marks_dir: Path):
    report = sweep(marks_dir, threshold_days=90, dry_run=True)
    assert "feedback" in report.type_distribution
    assert "finding" in report.type_distribution
    assert report.type_distribution["feedback"] >= 3
