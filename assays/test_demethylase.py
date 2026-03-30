"""Tests for demethylase — active memory erasure and consolidation."""

from __future__ import annotations

from pathlib import Path

import pytest

from metabolon.organelles.demethylase import (
    ConsolidationReport,
    DemethylaseReport,
    MarkAnalysis,
    _effective_threshold,
    analyze_mark,
    consolidate,
    emit_signal,
    read_signals,
    record_access,
    resensitize,
    signal_history,
    sweep,
    transduce,
)


def _write_mark(path: Path, name: str, mtype: str = "feedback", **extra_fm):
    """Write a minimal mark file with frontmatter."""
    fm_lines = [f"name: {name}", f"type: {mtype}"]
    for k, v in extra_fm.items():
        fm_lines.append(f"{k}: {v}")
    path.write_text(f"---\n" + "\n".join(fm_lines) + "\n---\n\nContent here.\n")


def _patch_home(monkeypatch, home_path: Path) -> None:
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home_path))


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


def test_sweep_counts(marks_dir: Path, tmp_path: Path, monkeypatch):
    _patch_home(monkeypatch, tmp_path)
    report = sweep(marks_dir, threshold_days=90, dry_run=True)
    assert report.total_marks == 7
    assert report.protected_marks >= 2  # keep_digging + explicit protected


def test_sweep_finds_clusters(marks_dir: Path, tmp_path: Path, monkeypatch):
    _patch_home(monkeypatch, tmp_path)
    # Add more marks to create a cluster
    _write_mark(marks_dir / "feedback_tone_formal.md", "Tone formal", "feedback")
    _write_mark(marks_dir / "feedback_tone_casual.md", "Tone casual", "feedback")
    report = sweep(marks_dir, threshold_days=90, dry_run=True)
    topic_names = [c["topic"] for c in report.mark_clusters]
    assert any("tone" in t for t in topic_names)


def test_sweep_dry_run_preserves_files(marks_dir: Path, tmp_path: Path, monkeypatch):
    _patch_home(monkeypatch, tmp_path)
    # Make a mark old enough to be stale by using acetyl + any age > 14d
    # Can't easily fake mtime in test, so just verify dry_run doesn't delete
    count_before = len(list(marks_dir.glob("*.md")))
    sweep(marks_dir, threshold_days=0, dry_run=True)
    count_after = len(list(marks_dir.glob("*.md")))
    assert count_before == count_after


def test_type_distribution(marks_dir: Path, tmp_path: Path, monkeypatch):
    _patch_home(monkeypatch, tmp_path)
    report = sweep(marks_dir, threshold_days=90, dry_run=True)
    assert "feedback" in report.type_distribution
    assert "finding" in report.type_distribution
    assert report.type_distribution["feedback"] >= 3


# -- Spaced repetition tests --


def test_effective_threshold_no_accesses():
    assert _effective_threshold(90, 0) == 90


def test_effective_threshold_doubles_per_access():
    assert _effective_threshold(90, 1) == 180
    assert _effective_threshold(90, 2) == 360
    assert _effective_threshold(90, 3) == 720


def test_effective_threshold_capped():
    # Cap at 2^8 = 256x
    assert _effective_threshold(90, 8) == 90 * 256
    assert _effective_threshold(90, 100) == 90 * 256  # beyond cap, same


def test_record_access(marks_dir: Path):
    mark_path = marks_dir / "feedback_keep_digging.md"
    record_access(mark_path)
    content = mark_path.read_text()
    assert "access_count: 1" in content

    record_access(mark_path)
    content = mark_path.read_text()
    assert "access_count: 2" in content


def test_record_access_preserves_body(marks_dir: Path):
    mark_path = marks_dir / "finding_stale_path.md"
    original_body = "Content here."
    record_access(mark_path)
    content = mark_path.read_text()
    assert original_body in content
    assert "access_count: 1" in content


def test_analyze_reads_access_count(marks_dir: Path):
    mark_path = marks_dir / "feedback_keep_digging.md"
    record_access(mark_path)
    record_access(mark_path)
    mark = analyze_mark(mark_path)
    assert mark.access_count == 2


# -- Signal channel tests (paracrine signaling) --


def test_emit_signal(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("metabolon.organelles.demethylase.SIGNALS_DIR", tmp_path / "signals")
    monkeypatch.setattr(
        "metabolon.organelles.demethylase.SIGNAL_HISTORY_PATH",
        tmp_path / "state" / "signal-history.jsonl",
    )
    path = emit_signal("test-finding", "Goose found a bug in fasti", source="goose")
    assert path.exists()
    content = path.read_text()
    assert "durability: acetyl" in content
    assert "source: goose" in content
    assert "Goose found a bug in fasti" in content


def test_read_signals(tmp_path: Path, monkeypatch):
    sig_dir = tmp_path / "signals"
    monkeypatch.setattr("metabolon.organelles.demethylase.SIGNALS_DIR", sig_dir)
    monkeypatch.setattr(
        "metabolon.organelles.demethylase.SIGNAL_HISTORY_PATH",
        tmp_path / "state" / "signal-history.jsonl",
    )
    # Desensitization: duplicate signals merge into one file (fire_count incremented)
    emit_signal("refactor-done", "Task 3 complete", source="goose")
    emit_signal("refactor-done", "Task 5 complete", source="goose")  # deduplicates
    emit_signal("other-signal", "Something else", source="cc")

    all_signals = read_signals()
    # Two unique signal names → two files (refactor-done fire_count=2, other-signal fire_count=1)
    assert len(all_signals) == 2

    filtered = read_signals(name_filter="refactor")
    assert len(filtered) == 1
    assert filtered[0]["source"] == "goose"
    assert filtered[0]["fire_count"] == 2  # both fires recorded


def test_read_signals_empty(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("metabolon.organelles.demethylase.SIGNALS_DIR", tmp_path / "nonexistent")
    assert read_signals() == []


def test_signal_history_returns_last_n(tmp_path: Path, monkeypatch):
    sig_dir = tmp_path / "signals"
    history_path = tmp_path / "state" / "signal-history.jsonl"
    monkeypatch.setattr("metabolon.organelles.demethylase.SIGNALS_DIR", sig_dir)
    monkeypatch.setattr("metabolon.organelles.demethylase.SIGNAL_HISTORY_PATH", history_path)

    emit_signal("first-signal", "First content", source="cc")
    emit_signal("second-signal", "Second content", source="goose")
    emit_signal("second-signal", "Second content again", source="goose")

    history = signal_history(limit=2)
    assert [entry["name"] for entry in history] == ["second-signal", "second-signal"]
    assert history[0]["fire_count"] == 2
    assert history[0]["deduplicated"] is True
    assert "timestamp" in history[0]
    assert history[1]["fire_count"] == 1


def test_signal_history_filters_by_name(tmp_path: Path, monkeypatch):
    sig_dir = tmp_path / "signals"
    history_path = tmp_path / "state" / "signal-history.jsonl"
    monkeypatch.setattr("metabolon.organelles.demethylase.SIGNALS_DIR", sig_dir)
    monkeypatch.setattr("metabolon.organelles.demethylase.SIGNAL_HISTORY_PATH", history_path)

    emit_signal("sleep-report", "Overnight summary", source="cc")
    emit_signal("build-report", "Build completed", source="goose")

    history = signal_history(limit=10, name_filter="sleep")
    assert len(history) == 1
    assert history[0]["name"] == "sleep-report"


# -- Sleep consolidation tests --


def test_consolidation_finds_recent_marks(marks_dir: Path, tmp_path: Path, monkeypatch):
    """Marks modified today (last_modified_days == 0) appear in today_marks."""
    # All marks in the fixture were just written, so last_modified_days == 0
    monkeypatch.setattr(
        "metabolon.organelles.demethylase.MARKS_DIR", marks_dir
    )
    _patch_home(monkeypatch, tmp_path)

    report = consolidate(marks_dir)
    assert isinstance(report, ConsolidationReport)
    # All fixture marks were written in this test run — they're all "today"
    assert len(report.today_marks) > 0
    assert all(m.last_modified_days == 0 for m in report.today_marks)


def test_consolidation_clusters_new_with_existing(marks_dir: Path, tmp_path: Path, monkeypatch):
    """Clusters span today's marks and existing marks by shared topic prefix."""
    # Add a second feedback_tone mark so the cluster forms
    _write_mark(marks_dir / "feedback_tone_formal.md", "Tone formal", "feedback")
    _write_mark(marks_dir / "feedback_tone_casual.md", "Tone casual", "feedback")
    _patch_home(monkeypatch, tmp_path)

    report = consolidate(marks_dir)
    topic_names = [c["topic"] for c in report.clusters_found]
    # tone cluster should appear since we have 2 tone marks
    assert any("tone" in t for t in topic_names)
    # All clusters must have count >= 2 (combinatorial pattern requirement)
    assert all(c["count"] >= 2 for c in report.clusters_found)


# -- Desensitization tests --


def test_emit_signal_increments_fire_count(tmp_path: Path, monkeypatch):
    """Emitting the same signal name twice increments fire_count instead of creating a duplicate."""
    sig_dir = tmp_path / "signals"
    monkeypatch.setattr("metabolon.organelles.demethylase.SIGNALS_DIR", sig_dir)
    monkeypatch.setattr(
        "metabolon.organelles.demethylase.SIGNAL_HISTORY_PATH",
        tmp_path / "state" / "signal-history.jsonl",
    )

    path1 = emit_signal("repeat-signal", "First fire", source="cc")
    path2 = emit_signal("repeat-signal", "Second fire", source="cc")

    # Should be the same file — no duplicate created
    assert path1 == path2

    from metabolon.organelles.demethylase import _parse_frontmatter
    fm = _parse_frontmatter(path1)
    assert int(fm.get("fire_count", "0")) == 2

    # Only one file in the signals dir
    signal_files = list(sig_dir.glob("signal_*.md"))
    assert len(signal_files) == 1


def test_desensitized_signals_excluded(tmp_path: Path, monkeypatch):
    """Signals with fire_count >= desensitization_threshold are excluded from read_signals."""
    sig_dir = tmp_path / "signals"
    monkeypatch.setattr("metabolon.organelles.demethylase.SIGNALS_DIR", sig_dir)
    monkeypatch.setattr(
        "metabolon.organelles.demethylase.SIGNAL_HISTORY_PATH",
        tmp_path / "state" / "signal-history.jsonl",
    )

    # Emit the same signal 5 times — should reach the default threshold of 5
    for _ in range(5):
        emit_signal("noisy-signal", "Repeated content", source="cc")

    # With default threshold=5, fire_count=5 is desensitized → excluded
    results = read_signals(desensitization_threshold=5)
    names = [s["name"] for s in results]
    assert "noisy-signal" not in names


def test_desensitized_signals_included_with_flag(tmp_path: Path, monkeypatch):
    """include_desensitized=True returns desensitized signals with desensitized=True flag."""
    sig_dir = tmp_path / "signals"
    monkeypatch.setattr("metabolon.organelles.demethylase.SIGNALS_DIR", sig_dir)
    monkeypatch.setattr(
        "metabolon.organelles.demethylase.SIGNAL_HISTORY_PATH",
        tmp_path / "state" / "signal-history.jsonl",
    )

    for _ in range(5):
        emit_signal("noisy-signal", "Repeated content", source="cc")

    results = read_signals(desensitization_threshold=5, include_desensitized=True)
    names = [s["name"] for s in results]
    assert "noisy-signal" in names

    desensitized_signal = next(s for s in results if s["name"] == "noisy-signal")
    assert desensitized_signal["desensitized"] is True
    assert desensitized_signal["fire_count"] == 5


def test_resensitize_resets_signal(tmp_path: Path, monkeypatch):
    """resensitize() resets a desensitized signal so it appears in read_signals again."""
    sig_dir = tmp_path / "signals"
    monkeypatch.setattr("metabolon.organelles.demethylase.SIGNALS_DIR", sig_dir)
    monkeypatch.setattr(
        "metabolon.organelles.demethylase.SIGNAL_HISTORY_PATH",
        tmp_path / "state" / "signal-history.jsonl",
    )

    # Drive signal to desensitization
    for _ in range(5):
        emit_signal("tired-receptor", "Same content", source="cc")

    # Confirm it's excluded
    assert read_signals(desensitization_threshold=5) == []

    # Resensitize it
    recycled = resensitize("tired-receptor")
    assert recycled is True

    # Now it should appear again with fire_count reset to 1
    results = read_signals(desensitization_threshold=5)
    names = [s["name"] for s in results]
    assert "tired-receptor" in names
    reset_signal = next(s for s in results if s["name"] == "tired-receptor")
    assert reset_signal["fire_count"] == 1
    assert reset_signal["desensitized"] is False

    # resensitize on a non-desensitized signal returns False
    assert resensitize("tired-receptor") is False


def test_consolidation_report_structure(marks_dir: Path, tmp_path: Path, monkeypatch):
    """ConsolidationReport has all required fields and daily summary is written."""
    _patch_home(monkeypatch, tmp_path)

    report = consolidate(marks_dir)

    # Check dataclass fields exist and have correct types
    assert isinstance(report.today_marks, list)
    assert isinstance(report.clusters_found, list)
    assert isinstance(report.strengthened, list)
    assert isinstance(report.methylome_updated, bool)

    # Daily summary file must be written
    date_str = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
    summary_path = tmp_path / "epigenome" / "chromatin" / "Daily" / f"{date_str}-consolidation.md"
    assert summary_path.exists(), f"Expected consolidation summary at {summary_path}"
    content = summary_path.read_text()
    assert "Chromatin Remodeling" in content
    assert "Phase 1:" in content
    assert "Phase 2:" in content
    assert report.methylome_updated is True


# -- Signal cascade (transduction) tests --


def test_emit_signal_with_downstream(tmp_path: Path, monkeypatch):
    """emit_signal stores downstream commands in frontmatter as a YAML list."""
    sig_dir = tmp_path / "signals"
    monkeypatch.setattr("metabolon.organelles.demethylase.SIGNALS_DIR", sig_dir)
    monkeypatch.setattr(
        "metabolon.organelles.demethylase.SIGNAL_HISTORY_PATH",
        tmp_path / "state" / "signal-history.jsonl",
    )

    cmds = ["echo hello", "echo world"]
    path = emit_signal("cascade-test", "Trigger downstream", source="cc", downstream=cmds)
    content = path.read_text()

    assert "downstream:" in content
    assert "- echo hello" in content
    assert "- echo world" in content


def test_transduce_executes_commands(tmp_path: Path, monkeypatch):
    """transduce() runs downstream shell commands and reports what fired."""
    sig_dir = tmp_path / "signals"
    monkeypatch.setattr("metabolon.organelles.demethylase.SIGNALS_DIR", sig_dir)
    monkeypatch.setattr(
        "metabolon.organelles.demethylase.SIGNAL_HISTORY_PATH",
        tmp_path / "state" / "signal-history.jsonl",
    )

    sentinel = tmp_path / "cascade_fired.txt"
    emit_signal(
        "enzyme-cascade",
        "Activate kinase chain",
        source="cc",
        downstream=[f"touch {sentinel}"],
    )

    results = transduce()
    assert len(results) == 1
    assert results[0]["name"] == "enzyme-cascade"
    assert len(results[0]["cascades_fired"]) == 1
    assert sentinel.exists(), "Downstream command should have created sentinel file"


def test_transduce_marks_as_transduced(tmp_path: Path, monkeypatch):
    """After transduce(), the signal file has transduced: true in frontmatter."""
    sig_dir = tmp_path / "signals"
    monkeypatch.setattr("metabolon.organelles.demethylase.SIGNALS_DIR", sig_dir)
    monkeypatch.setattr(
        "metabolon.organelles.demethylase.SIGNAL_HISTORY_PATH",
        tmp_path / "state" / "signal-history.jsonl",
    )

    path = emit_signal(
        "mark-test",
        "One-shot cascade",
        source="cc",
        downstream=["echo once"],
    )

    transduce()

    content = path.read_text()
    assert "transduced: true" in content


def test_transduce_skips_already_transduced(tmp_path: Path, monkeypatch):
    """A signal already marked transduced is not returned or re-executed by transduce()."""
    sig_dir = tmp_path / "signals"
    monkeypatch.setattr("metabolon.organelles.demethylase.SIGNALS_DIR", sig_dir)
    monkeypatch.setattr(
        "metabolon.organelles.demethylase.SIGNAL_HISTORY_PATH",
        tmp_path / "state" / "signal-history.jsonl",
    )

    counter = tmp_path / "count.txt"
    counter.write_text("0")
    emit_signal(
        "one-shot",
        "Fire once only",
        source="cc",
        downstream=[f"echo x >> {counter}"],
    )

    # First transduce — should fire
    results1 = transduce()
    assert len(results1) == 1

    # Second transduce — already transduced, should be skipped
    results2 = transduce()
    assert len(results2) == 0

    # Command ran exactly once
    fired_count = counter.read_text().strip().count("\n") + 1
    assert fired_count == 1
