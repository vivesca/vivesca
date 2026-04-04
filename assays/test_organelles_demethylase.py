from __future__ import annotations

"""Tests for metabolon.organelles.demethylase — active memory erasure and
consolidation, ephemeral signal channel, and downstream cascade execution.

All filesystem interactions are redirected to tmp_path fixtures.
External calls (subprocess, datetime) are mocked where needed.
"""

import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

import metabolon.organelles.demethylase as dm
from metabolon.organelles.demethylase import (
    ConsolidationReport,
    DemethylaseReport,
    MarkAnalysis,
    _cluster_marks,
    _detect_staleness,
    _effective_threshold,
    _infer_durability,
    _infer_protected,
    _infer_source,
    _parse_downstream,
    _parse_frontmatter,
    _update_frontmatter_field,
    _validate_downstream_command,
    analyze_mark,
    consolidate,
    emit_signal,
    format_report,
    read_signals,
    record_access,
    resensitize,
    signal_history,
    sweep,
    transduce,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def marks_dir(tmp_path):
    """Temporary marks directory populated with sample mark files."""
    d = tmp_path / "marks"
    d.mkdir()
    return d


@pytest.fixture
def signals_dir(tmp_path):
    """Temporary signals directory; patches SIGNALS_DIR for signal tests."""
    d = tmp_path / "signals"
    d.mkdir()
    return d


@pytest.fixture(autouse=True)
def _patch_paths(marks_dir, signals_dir, tmp_path):
    """Redirect module-level paths to tmp directories for every test."""
    dm.MARKS_DIR = marks_dir
    dm.SIGNALS_DIR = signals_dir
    dm.SIGNAL_HISTORY_PATH = tmp_path / "signal-history.jsonl"
    return


def _write_mark(directory, name, frontmatter=None, body=""):
    """Helper to create a mark file with frontmatter."""
    path = directory / name
    if frontmatter is None:
        frontmatter = {"name": name.replace(".md", ""), "type": "feedback", "source": "cc"}
    fm_lines = [f"{k}: {v}" for k, v in frontmatter.items()]
    content = "---\n" + "\n".join(fm_lines) + "\n---\n\n" + body + "\n"
    path.write_text(content, encoding="utf-8")
    return path


def _write_mark_with_age(directory, filename, age_days, frontmatter=None):
    """Write a mark file and set its mtime to age_days ago."""
    path = _write_mark(directory, filename, frontmatter=frontmatter)
    old_time = (datetime.now() - timedelta(days=age_days)).timestamp()
    os.utime(path, (old_time, old_time))
    return path


def _make_mark(path, age_days=10, access_count=0, **overrides):
    """Create a MarkAnalysis with sensible defaults."""
    defaults = dict(
        path=path,
        name=path.stem,
        mark_type="feedback",
        durability="methyl",
        protected=False,
        source="cc",
        age_days=age_days,
        last_modified_days=age_days,
        access_count=access_count,
    )
    defaults.update(overrides)
    return MarkAnalysis(**defaults)


# ===================================================================
# _parse_frontmatter
# ===================================================================


class TestParseFrontmatter:
    def test_basic_frontmatter(self, tmp_path):
        p = tmp_path / "test.md"
        p.write_text("---\nname: foo\ntype: bar\n---\nbody\n")
        assert _parse_frontmatter(p) == {"name": "foo", "type": "bar"}

    def test_no_frontmatter(self, tmp_path):
        p = tmp_path / "test.md"
        p.write_text("Just a regular file\n")
        assert _parse_frontmatter(p) == {}

    def test_unclosed_frontmatter(self, tmp_path):
        p = tmp_path / "test.md"
        p.write_text("---\nname: foo\n")
        assert _parse_frontmatter(p) == {}

    def test_empty_frontmatter(self, tmp_path):
        p = tmp_path / "test.md"
        p.write_text("---\n---\nbody\n")
        assert _parse_frontmatter(p) == {}

    def test_multiline_value_uses_first_colon(self, tmp_path):
        p = tmp_path / "test.md"
        p.write_text("---\nreason: old mark: extra\n---\n")
        result = _parse_frontmatter(p)
        assert result["reason"] == "old mark: extra"

    def test_colon_in_value_preserved(self, tmp_path):
        p = tmp_path / "test.md"
        p.write_text("---\nurl: https://example.com\n---\n")
        assert _parse_frontmatter(p)["url"] == "https://example.com"


# ===================================================================
# _validate_downstream_command
# ===================================================================


class TestValidateDownstreamCommand:
    def test_safe_command(self):
        assert _validate_downstream_command("echo hello") == ["echo", "hello"]

    def test_pipe_rejected(self):
        assert _validate_downstream_command("echo foo | wc") is None

    def test_semicolon_rejected(self):
        assert _validate_downstream_command("ls; rm -rf /") is None

    def test_backtick_rejected(self):
        assert _validate_downstream_command("echo `whoami`") is None

    def test_dollar_rejected(self):
        assert _validate_downstream_command("echo $HOME") is None

    def test_ampersand_rejected(self):
        assert _validate_downstream_command("sleep 10 &") is None

    def test_redirect_rejected(self):
        assert _validate_downstream_command("cat /etc/passwd > /tmp/x") is None

    def test_quoted_safe_command(self):
        assert _validate_downstream_command("echo 'hello world'") == ["echo", "hello world"]


# ===================================================================
# _parse_downstream
# ===================================================================


class TestParseDownstream:
    def test_extracts_commands(self, tmp_path):
        p = tmp_path / "s.md"
        p.write_text("---\nname: test\ndownstream:\n  - echo hello\n  - ls /tmp\n---\nbody\n")
        assert _parse_downstream(p) == ["echo hello", "ls /tmp"]

    def test_no_downstream(self, tmp_path):
        p = tmp_path / "s.md"
        p.write_text("---\nname: test\n---\nbody\n")
        assert _parse_downstream(p) == []

    def test_no_frontmatter(self, tmp_path):
        p = tmp_path / "s.md"
        p.write_text("no fm here\n")
        assert _parse_downstream(p) == []

    def test_empty_bullet(self, tmp_path):
        p = tmp_path / "s.md"
        p.write_text("---\nname: test\ndownstream:\n  -\n---\nbody\n")
        assert _parse_downstream(p) == [""]

    def test_comment_after_downstream_ignored(self, tmp_path):
        p = tmp_path / "s.md"
        p.write_text("---\nname: test\ndownstream:\n  # this is a comment\n  - echo hi\n---\n")
        assert _parse_downstream(p) == ["echo hi"]


# ===================================================================
# _infer_durability
# ===================================================================


class TestInferDurability:
    def test_from_frontmatter(self, tmp_path):
        p = tmp_path / "mymark.md"
        assert _infer_durability({"durability": "acetyl"}, p) == "acetyl"

    def test_checkpoint_is_acetyl(self, tmp_path):
        p = tmp_path / "checkpoint_123.md"
        assert _infer_durability({}, p) == "acetyl"

    def test_resolved_is_acetyl(self, tmp_path):
        p = tmp_path / "resolved_bug.md"
        assert _infer_durability({}, p) == "acetyl"

    def test_default_is_methyl(self, tmp_path):
        p = tmp_path / "feedback_keep.md"
        assert _infer_durability({}, p) == "methyl"


# ===================================================================
# _infer_source
# ===================================================================


class TestInferSource:
    def test_from_frontmatter(self):
        assert _infer_source({"source": "gemini"}) == "gemini"

    def test_unknown_default(self):
        assert _infer_source({}) == "unknown"


# ===================================================================
# _infer_protected
# ===================================================================


class TestInferProtected:
    def test_frontmatter_true(self, tmp_path):
        p = tmp_path / "custom.md"
        assert _infer_protected({"protected": "true"}, p) is True

    def test_frontmatter_yes(self, tmp_path):
        p = tmp_path / "custom.md"
        assert _infer_protected({"protected": "yes"}, p) is True

    def test_frontmatter_false(self, tmp_path):
        p = tmp_path / "custom.md"
        assert _infer_protected({"protected": "false"}, p) is False

    def test_core_pattern_protected(self, tmp_path):
        for name in [
            "feedback_keep_digging",
            "feedback_hold_position",
            "feedback_pull_the_thread",
            "feedback_more_autonomous",
            "feedback_stop_asking_obvious",
        ]:
            p = tmp_path / f"{name}.md"
            assert _infer_protected({}, p) is True, f"{name} should be protected"

    def test_non_core_not_protected(self, tmp_path):
        p = tmp_path / "feedback_other.md"
        assert _infer_protected({}, p) is False


# ===================================================================
# _effective_threshold
# ===================================================================


class TestEffectiveThreshold:
    def test_zero_accesses(self):
        assert _effective_threshold(90, 0) == 90

    def test_one_access_doubles(self):
        assert _effective_threshold(90, 1) == 180

    def test_three_accesses_octuples(self):
        assert _effective_threshold(14, 3) == 14 * 8

    def test_cap_at_eight(self):
        # 2^8 = 256, 2^9 = 512 but capped at 8
        assert _effective_threshold(90, 9) == 90 * 256
        assert _effective_threshold(90, 100) == 90 * 256

    def test_acetyl_base(self):
        assert _effective_threshold(14, 0) == 14
        assert _effective_threshold(14, 2) == 56


# ===================================================================
# _detect_staleness
# ===================================================================


class TestDetectStaleness:
    def test_protected_never_stale(self):
        m = _make_mark(Path("/dummy"), age_days=999, protected=True)
        result = _detect_staleness(m)
        assert result.stale is False

    def test_acetyl_stale_over_threshold(self):
        m = _make_mark(Path("/dummy"), age_days=20, durability="acetyl", access_count=0)
        result = _detect_staleness(m)
        assert result.stale is True
        assert "acetyl" in result.reason

    def test_acetyl_fresh_under_threshold(self):
        m = _make_mark(Path("/dummy"), age_days=10, durability="acetyl", access_count=0)
        result = _detect_staleness(m)
        assert result.stale is False

    def test_methyl_stale_over_90_days(self):
        m = _make_mark(Path("/dummy"), age_days=100, durability="methyl", access_count=0)
        result = _detect_staleness(m)
        assert result.stale is True
        assert "methyl" in result.reason

    def test_methyl_fresh_under_90(self):
        m = _make_mark(Path("/dummy"), age_days=50, durability="methyl", access_count=0)
        result = _detect_staleness(m)
        assert result.stale is False

    def test_access_extends_life(self):
        # 90 * 2^1 = 180 days; age 100 should NOT be stale
        m = _make_mark(Path("/dummy"), age_days=100, durability="methyl", access_count=1)
        result = _detect_staleness(m)
        assert result.stale is False

    def test_project_type_faster_decay(self):
        # project marks decay at base 30 days
        m = _make_mark(
            Path("/dummy"), age_days=50, mark_type="project", durability="methyl", access_count=0
        )
        result = _detect_staleness(m)
        assert result.stale is True
        assert "project" in result.reason

    def test_project_not_stale_when_young(self):
        m = _make_mark(
            Path("/dummy"), age_days=20, mark_type="project", durability="methyl", access_count=0
        )
        result = _detect_staleness(m)
        assert result.stale is False

    def test_custom_threshold(self):
        m = _make_mark(Path("/dummy"), age_days=50, durability="methyl", access_count=0)
        result = _detect_staleness(m, threshold_days=30)
        assert result.stale is True


# ===================================================================
# _cluster_marks
# ===================================================================


class TestClusterMarks:
    def test_clusters_by_prefix(self, tmp_path):
        marks = [
            _make_mark(tmp_path / "feedback_keep_digging.md"),
            _make_mark(tmp_path / "feedback_hold_position.md"),
            _make_mark(tmp_path / "feedback_more_autonomous.md"),
        ]
        clusters = _cluster_marks(marks)
        # All three have different topic words (keep, hold, more) — no cluster ≥ 2
        assert clusters == []

    def test_two_same_topic_cluster(self, tmp_path):
        marks = [
            _make_mark(tmp_path / "feedback_keep_digging.md"),
            _make_mark(tmp_path / "feedback_keep_going.md"),
        ]
        clusters = _cluster_marks(marks)
        assert any(c["topic"] == "keep" and c["count"] == 2 for c in clusters)

    def test_single_mark_no_cluster(self, tmp_path):
        marks = [_make_mark(tmp_path / "feedback_unique.md")]
        clusters = _cluster_marks(marks)
        assert clusters == []

    def test_empty_marks(self):
        assert _cluster_marks([]) == []

    def test_no_underscore_no_cluster(self, tmp_path):
        marks = [_make_mark(tmp_path / "simple.md"), _make_mark(tmp_path / "plain.md")]
        clusters = _cluster_marks(marks)
        assert clusters == []


# ===================================================================
# analyze_mark
# ===================================================================


class TestAnalyzeMark:
    def test_basic_analysis(self, marks_dir):
        p = _write_mark(
            marks_dir,
            "feedback_test.md",
            {
                "name": "test_mark",
                "type": "feedback",
                "source": "cc",
                "durability": "methyl",
            },
        )
        m = analyze_mark(p)
        assert m.name == "test_mark"
        assert m.mark_type == "feedback"
        assert m.source == "cc"
        assert m.durability == "methyl"
        assert m.age_days == 0
        assert m.stale is False

    def test_fallback_to_stem(self, marks_dir):
        p = _write_mark(marks_dir, "my_special_mark.md")
        m = analyze_mark(p)
        assert m.name == "my_special_mark"

    def test_access_count_parsed(self, marks_dir):
        p = _write_mark(
            marks_dir,
            "counted.md",
            {
                "name": "counted",
                "type": "feedback",
                "source": "cc",
                "access_count": "3",
            },
        )
        m = analyze_mark(p)
        assert m.access_count == 3


# ===================================================================
# consolidate
# ===================================================================


class TestConsolidate:
    def test_empty_directory(self, marks_dir):
        report = consolidate(marks_dir)
        assert isinstance(report, ConsolidationReport)
        assert report.today_marks == []
        assert report.methylome_updated is True

    def test_today_marks_detected(self, marks_dir):
        _write_mark(marks_dir, "today_mark.md")
        report = consolidate(marks_dir)
        assert len(report.today_marks) == 1

    def test_skips_index_files(self, marks_dir):
        for name in ["MEMORY.md", "methylome.md", "decay-tracker.md"]:
            (marks_dir / name).write_text("---\n---\nbody\n")
        _write_mark(marks_dir, "real_mark.md")
        report = consolidate(marks_dir)
        assert len(report.today_marks) == 1

    def test_strengthens_accessed_marks(self, marks_dir):
        _write_mark(
            marks_dir,
            "accessed.md",
            {
                "name": "accessed",
                "type": "feedback",
                "source": "cc",
                "access_count": "2",
            },
        )
        report = consolidate(marks_dir)
        assert len(report.strengthened) == 1
        assert report.strengthened[0].access_count == 2

    def test_no_strengthen_without_access(self, marks_dir):
        _write_mark(
            marks_dir,
            "unaccessed.md",
            {
                "name": "unaccessed",
                "type": "feedback",
                "source": "cc",
            },
        )
        report = consolidate(marks_dir)
        assert report.strengthened == []

    def test_writes_daily_summary(self, marks_dir, tmp_path):
        with patch.object(Path, "home", return_value=tmp_path):
            report = consolidate(marks_dir)
        assert report.methylome_updated is True


# ===================================================================
# sweep
# ===================================================================


class TestSweep:
    def test_empty_directory(self, marks_dir):
        report = sweep(marks_dir)
        assert report.total_marks == 0
        assert report.stale_candidates == []

    def test_counts_marks(self, marks_dir):
        _write_mark(
            marks_dir,
            "m1.md",
            {"name": "m1", "type": "feedback", "source": "cc", "durability": "methyl"},
        )
        _write_mark(
            marks_dir,
            "a1.md",
            {"name": "a1", "type": "feedback", "source": "cc", "durability": "acetyl"},
        )
        report = sweep(marks_dir)
        assert report.total_marks == 2
        assert report.methyl_marks == 1
        assert report.acetyl_marks == 1

    def test_stale_detected(self, marks_dir):
        _write_mark_with_age(
            marks_dir,
            "old_mark.md",
            age_days=100,
            frontmatter={
                "name": "old_mark",
                "type": "feedback",
                "source": "cc",
                "durability": "methyl",
            },
        )
        report = sweep(marks_dir, threshold_days=90)
        assert len(report.stale_candidates) >= 1

    def test_dry_run_does_not_delete(self, marks_dir):
        p = _write_mark_with_age(
            marks_dir,
            "stale.md",
            age_days=200,
            frontmatter={
                "name": "stale",
                "type": "feedback",
                "source": "cc",
                "durability": "acetyl",
            },
        )
        sweep(marks_dir, dry_run=True)
        assert p.exists()

    def test_non_dry_run_deletes_stale(self, marks_dir):
        p = _write_mark_with_age(
            marks_dir,
            "stale.md",
            age_days=200,
            frontmatter={
                "name": "stale",
                "type": "feedback",
                "source": "cc",
                "durability": "acetyl",
            },
        )
        sweep(marks_dir, dry_run=False)
        assert not p.exists()

    def test_protected_not_deleted(self, marks_dir):
        p = _write_mark_with_age(marks_dir, "feedback_keep_digging.md", age_days=500)
        sweep(marks_dir, dry_run=False)
        assert p.exists()

    def test_source_distribution(self, marks_dir):
        _write_mark(marks_dir, "s1.md", {"name": "s1", "type": "feedback", "source": "cc"})
        _write_mark(marks_dir, "s2.md", {"name": "s2", "type": "feedback", "source": "gemini"})
        report = sweep(marks_dir)
        assert report.source_distribution["cc"] == 1
        assert report.source_distribution["gemini"] == 1

    def test_type_distribution(self, marks_dir):
        _write_mark(marks_dir, "t1.md", {"name": "t1", "type": "feedback", "source": "cc"})
        _write_mark(marks_dir, "t2.md", {"name": "t2", "type": "finding", "source": "cc"})
        report = sweep(marks_dir)
        assert report.type_distribution["feedback"] == 1
        assert report.type_distribution["finding"] == 1

    def test_skips_index_files(self, marks_dir):
        for name in ["MEMORY.md", "methylome.md", "decay-tracker.md"]:
            (marks_dir / name).write_text("---\n---\nbody\n")
        report = sweep(marks_dir)
        assert report.total_marks == 0

    def test_stale_signals_counted(self, marks_dir, signals_dir):
        # Create a stale signal file (>14 days old)
        sig = signals_dir / "signal_test.md"
        sig.write_text("---\nname: test\n---\nbody\n")
        old = (datetime.now() - timedelta(days=20)).timestamp()
        os.utime(sig, (old, old))
        report = sweep(marks_dir)
        assert report.total_marks >= 1
        assert any(s.mark_type == "signal" for s in report.stale_candidates)


# ===================================================================
# format_report
# ===================================================================


class TestFormatReport:
    def test_basic_report(self):
        report = DemethylaseReport(
            total_marks=10,
            methyl_marks=7,
            acetyl_marks=3,
            protected_marks=2,
            stale_candidates=[],
            source_distribution={"cc": 5, "gemini": 5},
            type_distribution={"feedback": 8, "finding": 2},
        )
        text = format_report(report)
        assert "10 marks" in text
        assert "Methyl (durable): 7" in text
        assert "Acetyl (volatile): 3" in text
        assert "Protected (CpG): 2" in text
        assert "cc: 5" in text
        assert "feedback: 8" in text

    def test_with_clusters(self):
        report = DemethylaseReport(
            mark_clusters=[{"topic": "keep", "count": 3, "marks": ["a", "b", "c"]}],
        )
        text = format_report(report)
        assert "keep" in text

    def test_with_stale_candidates(self):
        m = MarkAnalysis(
            path=Path("/dummy/old.md"),
            name="old",
            mark_type="feedback",
            durability="acetyl",
            protected=False,
            source="cc",
            age_days=100,
            last_modified_days=100,
            stale=True,
            reason="too old",
        )
        report = DemethylaseReport(stale_candidates=[m])
        text = format_report(report)
        assert "old.md" in text
        assert "too old" in text


# ===================================================================
# record_access
# ===================================================================


class TestRecordAccess:
    def test_increments_existing(self, tmp_path):
        p = tmp_path / "mark.md"
        p.write_text("---\nname: test\naccess_count: 3\n---\nbody\n")
        record_access(p)
        text = p.read_text()
        assert "access_count: 4" in text

    def test_adds_when_missing(self, tmp_path):
        p = tmp_path / "mark.md"
        p.write_text("---\nname: test\n---\nbody\n")
        record_access(p)
        text = p.read_text()
        assert "access_count: 1" in text

    def test_no_frontmatter_noop(self, tmp_path):
        p = tmp_path / "plain.md"
        p.write_text("no frontmatter here\n")
        original = p.read_text()
        record_access(p)
        assert p.read_text() == original

    def test_unclosed_frontmatter_noop(self, tmp_path):
        p = tmp_path / "unclosed.md"
        p.write_text("---\nname: test\n")
        original = p.read_text()
        record_access(p)
        assert p.read_text() == original


# ===================================================================
# emit_signal
# ===================================================================


class TestEmitSignal:
    def test_creates_signal_file(self, signals_dir):
        path = emit_signal("test_sig", "hello world", source="cc")
        assert path.exists()
        assert "test_sig" in path.name
        content = path.read_text()
        assert "hello world" in content
        assert "source: cc" in content

    def test_signal_has_frontmatter(self, signals_dir):
        path = emit_signal("sig1", "body text")
        text = path.read_text()
        assert text.startswith("---")
        fm = _parse_frontmatter(path)
        assert fm["name"] == "sig1"
        assert fm["type"] == "signal"
        assert fm["durability"] == "acetyl"
        assert fm["fire_count"] == "1"

    def test_deduplication_increments_fire_count(self, signals_dir):
        first = emit_signal("dup", "first")
        second = emit_signal("dup", "second call")
        assert second == first  # same path
        fm = _parse_frontmatter(first)
        assert fm["fire_count"] == "2"

    def test_downstream_commands_written(self, signals_dir):
        path = emit_signal("cascade_sig", "body", downstream=["echo hi", "ls /tmp"])
        text = path.read_text()
        assert "downstream:" in text
        assert "- echo hi" in text
        assert "- ls /tmp" in text

    def test_signal_history_appended(self, tmp_path, signals_dir):
        emit_signal("hist_test", "body", source="cc")
        history_path = dm.SIGNAL_HISTORY_PATH
        assert history_path.exists()
        lines = history_path.read_text().strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["name"] == "hist_test"
        assert entry["source"] == "cc"
        assert entry["deduplicated"] is False

    def test_signal_history_dedup_entry(self, signals_dir):
        emit_signal("dedup_hist", "first")
        emit_signal("dedup_hist", "second")
        lines = dm.SIGNAL_HISTORY_PATH.read_text().strip().splitlines()
        assert len(lines) == 2
        entry2 = json.loads(lines[1])
        assert entry2["deduplicated"] is True
        assert entry2["fire_count"] == 2


# ===================================================================
# read_signals
# ===================================================================


class TestReadSignals:
    def test_empty_directory(self, signals_dir):
        assert read_signals() == []

    def test_reads_signals(self, signals_dir):
        emit_signal("sig_a", "content a")
        emit_signal("sig_b", "content b")
        result = read_signals()
        assert len(result) == 2
        names = {s["name"] for s in result}
        assert "sig_a" in names
        assert "sig_b" in names

    def test_name_filter(self, signals_dir):
        emit_signal("alpha_one", "a1")
        emit_signal("alpha_two", "a2")
        emit_signal("beta_one", "b1")
        result = read_signals(name_filter="alpha")
        assert len(result) == 2

    def test_skips_transduced(self, signals_dir):
        path = emit_signal("trans", "body")
        _update_frontmatter_field(path, "transduced", "true")
        result = read_signals()
        assert len(result) == 0

    def test_desensitization_threshold(self, signals_dir):
        # Fire signal 5 times to hit default threshold
        for _ in range(5):
            emit_signal("noisy", "repeated")
        result = read_signals()  # default threshold=5
        assert len(result) == 0

    def test_include_desensitized(self, signals_dir):
        for _ in range(5):
            emit_signal("noisy2", "repeated")
        result = read_signals(include_desensitized=True)
        assert len(result) == 1
        assert result[0]["desensitized"] is True

    def test_execute_cascade(self, signals_dir):
        emit_signal("cascade", "body", downstream=["echo hello"])
        result = read_signals(execute_cascade=True)
        assert len(result) == 1
        assert "echo hello" in result[0]["cascades_fired"]
        # Should now be marked transduced
        result2 = read_signals()
        assert len(result2) == 0

    def test_execute_cascade_rejects_shell_injection(self, signals_dir):
        emit_signal("inject", "body", downstream=["echo foo | wc"])
        result = read_signals(execute_cascade=True)
        assert len(result) == 1
        assert result[0]["cascades_fired"][0].startswith("REJECTED")

    def test_execute_cascade_handles_failure(self, signals_dir):
        emit_signal("bad_cmd", "body", downstream=["false"])
        with patch.object(
            subprocess, "run", side_effect=subprocess.CalledProcessError(1, "false")
        ):
            result = read_signals(execute_cascade=True)
        assert len(result) == 1
        assert result[0]["cascades_fired"][0].startswith("FAILED")


# ===================================================================
# resensitize
# ===================================================================


class TestResensitize:
    def test_resensitize_desensitized_signal(self, signals_dir):
        for _ in range(6):
            emit_signal("recoverable", "body")
        # read_signals marks it as desensitized when fire_count >= threshold
        read_signals()
        result = resensitize("recoverable")
        assert result is True
        # Should now be readable again
        signals = read_signals()
        assert len(signals) == 1

    def test_no_match_returns_false(self, signals_dir):
        emit_signal("other", "body")
        assert resensitize("nonexistent") is False

    def test_not_desensitized_returns_false(self, signals_dir):
        emit_signal("fresh", "body")
        assert resensitize("fresh") is False

    def test_no_signals_dir(self, tmp_path):
        dm.SIGNALS_DIR = tmp_path / "nonexistent"
        assert resensitize("anything") is False


# ===================================================================
# transduce
# ===================================================================


class TestTransduce:
    def test_transduce_with_downstream(self, signals_dir):
        emit_signal("trans_test", "body", downstream=["echo trans"])
        result = transduce()
        assert len(result) == 1
        assert result[0]["name"] == "trans_test"
        assert "echo trans" in result[0]["cascades_fired"]

    def test_transduce_no_downstream(self, signals_dir):
        emit_signal("no_downstream", "body")
        result = transduce()
        assert len(result) == 0

    def test_transduce_with_filter(self, signals_dir):
        emit_signal("target_alpha", "body", downstream=["echo a"])
        emit_signal("other_beta", "body", downstream=["echo b"])
        result = transduce(name_filter="target")
        assert len(result) == 1
        assert result[0]["name"] == "target_alpha"


# ===================================================================
# signal_history
# ===================================================================


class TestSignalHistory:
    def test_empty_history(self):
        assert signal_history() == []

    def test_returns_recent(self, signals_dir):
        emit_signal("h1", "body")
        emit_signal("h2", "body")
        result = signal_history(limit=10)
        assert len(result) == 2

    def test_limit_respected(self, signals_dir):
        for i in range(5):
            emit_signal(f"lim_{i}", "body")
        result = signal_history(limit=2)
        assert len(result) == 2

    def test_name_filter(self, signals_dir):
        emit_signal("alpha_one", "body")
        emit_signal("beta_two", "body")
        result = signal_history(name_filter="alpha")
        assert len(result) == 1
        assert result[0]["name"] == "alpha_one"

    def test_zero_limit_returns_empty(self, signals_dir):
        emit_signal("x", "body")
        assert signal_history(limit=0) == []

    def test_malformed_line_skipped(self, signals_dir):
        dm.SIGNAL_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with dm.SIGNAL_HISTORY_PATH.open("a") as f:
            f.write("not json\n")
        emit_signal("good", "body")
        result = signal_history()
        assert len(result) == 1
        assert result[0]["name"] == "good"


# ===================================================================
# _update_frontmatter_field
# ===================================================================


class TestUpdateFrontmatterField:
    def test_updates_existing_field(self, tmp_path):
        p = tmp_path / "test.md"
        p.write_text("---\nname: old\n---\nbody\n")
        _update_frontmatter_field(p, "name", "new")
        assert _parse_frontmatter(p)["name"] == "new"

    def test_adds_new_field(self, tmp_path):
        p = tmp_path / "test.md"
        p.write_text("---\nname: test\n---\nbody\n")
        _update_frontmatter_field(p, "extra", "value")
        fm = _parse_frontmatter(p)
        assert fm["name"] == "test"
        assert fm["extra"] == "value"

    def test_no_frontmatter_noop(self, tmp_path):
        p = tmp_path / "test.md"
        p.write_text("plain text\n")
        _update_frontmatter_field(p, "key", "val")
        assert p.read_text() == "plain text\n"

    def test_body_preserved(self, tmp_path):
        p = tmp_path / "test.md"
        p.write_text("---\nname: test\n---\n\nBody line 1\nBody line 2\n")
        _update_frontmatter_field(p, "name", "updated")
        text = p.read_text()
        assert "Body line 1" in text
        assert "Body line 2" in text
