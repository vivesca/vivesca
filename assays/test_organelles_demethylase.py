from __future__ import annotations

"""Tests for metabolon/organelles/demethylase.py — internal functions and edge cases.

Focuses on functions and branches NOT covered by assays/test_demethylase.py:
_parse_frontmatter, _validate_downstream_command, _parse_downstream,
_detect_staleness, _cluster_marks, _infer_durability, _infer_protected,
_update_frontmatter_field, _find_existing_signal, format_report, and
sweep/consolidate edge cases.
"""


from pathlib import Path

import pytest

from metabolon.organelles.demethylase import (
    MarkAnalysis,
    _cluster_marks,
    _detect_staleness,
    _effective_threshold,
    _find_existing_signal,
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
# Helpers
# ---------------------------------------------------------------------------


def _write_mark(path: Path, name: str, mtype: str = "feedback", **extra_fm) -> None:
    """Write a minimal mark file with YAML frontmatter."""
    fm_lines = [f"name: {name}", f"type: {mtype}"]
    for k, v in extra_fm.items():
        fm_lines.append(f"{k}: {v}")
    path.write_text("---\n" + "\n".join(fm_lines) + "\n---\n\nBody text.\n")


def _make_mark(**overrides) -> MarkAnalysis:
    """Create a MarkAnalysis with sensible defaults, overridden by **overrides."""
    defaults = dict(
        path=Path("/fake/mark.md"),
        name="test-mark",
        mark_type="feedback",
        durability="methyl",
        protected=False,
        source="cc",
        age_days=100,
        last_modified_days=100,
        access_count=0,
        stale=False,
        reason="",
    )
    defaults.update(overrides)
    return MarkAnalysis(**defaults)


def _patch_signals(monkeypatch, tmp_path: Path) -> Path:
    """Patch SIGNALS_DIR and SIGNAL_HISTORY_PATH to tmp_path subdirs."""
    sig_dir = tmp_path / "signals"
    hist = tmp_path / "state" / "signal-history.jsonl"
    monkeypatch.setattr("metabolon.organelles.demethylase.SIGNALS_DIR", sig_dir)
    monkeypatch.setattr(
        "metabolon.organelles.demethylase.SIGNAL_HISTORY_PATH", hist
    )
    return sig_dir


# ---------------------------------------------------------------------------
# _parse_frontmatter
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_basic_frontmatter(self, tmp_path: Path):
        p = tmp_path / "mark.md"
        p.write_text("---\nname: foo\ntype: bar\n---\n\nbody\n")
        fm = _parse_frontmatter(p)
        assert fm == {"name": "foo", "type": "bar"}

    def test_no_frontmatter(self, tmp_path: Path):
        p = tmp_path / "plain.md"
        p.write_text("Just some text without frontmatter.\n")
        assert _parse_frontmatter(p) == {}

    def test_unclosed_frontmatter(self, tmp_path: Path):
        p = tmp_path / "unclosed.md"
        p.write_text("---\nname: foo\n")
        assert _parse_frontmatter(p) == {}

    def test_empty_file(self, tmp_path: Path):
        p = tmp_path / "empty.md"
        p.write_text("")
        assert _parse_frontmatter(p) == {}

    def test_value_with_colon(self, tmp_path: Path):
        """Values containing colons should be preserved."""
        p = tmp_path / "colon.md"
        p.write_text("---\nname: key: value\n---\n")
        fm = _parse_frontmatter(p)
        assert fm["name"] == "key: value"

    def test_empty_value(self, tmp_path: Path):
        p = tmp_path / "blank.md"
        p.write_text("---\nname:\n---\n")
        fm = _parse_frontmatter(p)
        assert fm["name"] == ""


# ---------------------------------------------------------------------------
# _validate_downstream_command
# ---------------------------------------------------------------------------


class TestValidateDownstreamCommand:
    def test_safe_command(self):
        assert _validate_downstream_command("echo hello") == ["echo", "hello"]

    def test_safe_with_path(self):
        result = _validate_downstream_command("touch /tmp/sentinel")
        assert result == ["touch", "/tmp/sentinel"]

    def test_pipe_rejected(self):
        assert _validate_downstream_command("echo hello | wc -l") is None

    def test_semicolon_rejected(self):
        assert _validate_downstream_command("echo a; echo b") is None

    def test_backtick_rejected(self):
        assert _validate_downstream_command("echo `date`") is None

    def test_dollar_rejected(self):
        assert _validate_downstream_command("echo $HOME") is None

    def test_ampersand_rejected(self):
        assert _validate_downstream_command("sleep 1 &") is None

    def test_redirect_rejected(self):
        assert _validate_downstream_command("echo hi > /tmp/out") is None

    def test_quoted_safe_args(self):
        """shlex.split handles quoted args; no metacharacters in parts."""
        result = _validate_downstream_command('echo "hello world"')
        assert result == ["echo", "hello world"]


# ---------------------------------------------------------------------------
# _parse_downstream
# ---------------------------------------------------------------------------


class TestParseDownstream:
    def test_extracts_downstream_commands(self, tmp_path: Path):
        p = tmp_path / "sig.md"
        p.write_text(
            "---\nname: test\nsource: cc\ndownstream:\n  - echo hello\n  - echo world\n---\n\nbody\n"
        )
        assert _parse_downstream(p) == ["echo hello", "echo world"]

    def test_no_downstream_key(self, tmp_path: Path):
        p = tmp_path / "sig.md"
        p.write_text("---\nname: test\n---\n\nbody\n")
        assert _parse_downstream(p) == []

    def test_no_frontmatter(self, tmp_path: Path):
        p = tmp_path / "sig.md"
        p.write_text("No frontmatter here.\n")
        assert _parse_downstream(p) == []

    def test_empty_list_item(self, tmp_path: Path):
        """Bare '-' (no value) produces an empty-string entry."""
        p = tmp_path / "sig.md"
        p.write_text("---\ndownstream:\n  -\n---\n\nbody\n")
        assert _parse_downstream(p) == [""]

    def test_comment_lines_ignored(self, tmp_path: Path):
        p = tmp_path / "sig.md"
        p.write_text(
            "---\ndownstream:\n  - echo hi\n  # this is a comment\n---\n\nbody\n"
        )
        cmds = _parse_downstream(p)
        assert cmds == ["echo hi"]

    def test_non_list_line_ends_block(self, tmp_path: Path):
        p = tmp_path / "sig.md"
        p.write_text(
            "---\ndownstream:\n  - echo one\nother_key: val\n  - echo two\n---\n\nbody\n"
        )
        cmds = _parse_downstream(p)
        # "  - echo two" comes after a non-list line, so block ended
        assert cmds == ["echo one"]


# ---------------------------------------------------------------------------
# _infer_durability
# ---------------------------------------------------------------------------


class TestInferDurability:
    def test_explicit_in_fm(self):
        assert _infer_durability({"durability": "acetyl"}, Path("x.md")) == "acetyl"

    def test_checkpoint_inferred_acetyl(self):
        assert _infer_durability({}, Path("/marks/checkpoint_abc.md")) == "acetyl"

    def test_resolved_inferred_acetyl(self):
        assert _infer_durability({}, Path("/marks/resolved_issue.md")) == "acetyl"

    def test_default_methyl(self):
        assert _infer_durability({}, Path("/marks/feedback_foo.md")) == "methyl"


# ---------------------------------------------------------------------------
# _infer_source
# ---------------------------------------------------------------------------


class TestInferSource:
    def test_explicit_source(self):
        assert _infer_source({"source": "gemini"}) == "gemini"

    def test_unknown_default(self):
        assert _infer_source({}) == "unknown"


# ---------------------------------------------------------------------------
# _infer_protected
# ---------------------------------------------------------------------------


class TestInferProtected:
    @pytest.mark.parametrize(
        "fm_val", ["true", "True", "yes", "Yes", "TRUE", "YES"]
    )
    def test_frontmatter_true(self, fm_val):
        assert _infer_protected({"protected": fm_val}, Path("x.md")) is True

    def test_frontmatter_false(self):
        assert _infer_protected({"protected": "false"}, Path("x.md")) is False

    def test_no_frontmatter_not_core(self):
        assert _infer_protected({}, Path("x.md")) is False

    @pytest.mark.parametrize(
        "stem",
        [
            "feedback_keep_digging",
            "feedback_hold_position",
            "feedback_pull_the_thread",
            "feedback_more_autonomous",
            "feedback_stop_asking_obvious",
        ],
    )
    def test_core_behavioral_patterns(self, stem: str):
        assert _infer_protected({}, Path(f"/marks/{stem}.md")) is True


# ---------------------------------------------------------------------------
# _detect_staleness
# ---------------------------------------------------------------------------


class TestDetectStaleness:
    def test_protected_never_stale(self):
        mark = _make_mark(protected=True, age_days=9999, durability="methyl")
        result = _detect_staleness(mark, threshold_days=90)
        assert result.stale is False

    def test_acetyl_stale_beyond_14_days(self):
        mark = _make_mark(durability="acetyl", age_days=15, access_count=0)
        result = _detect_staleness(mark)
        assert result.stale is True
        assert "acetyl" in result.reason

    def test_acetyl_not_stale_within_14_days(self):
        mark = _make_mark(durability="acetyl", age_days=10, access_count=0)
        result = _detect_staleness(mark)
        assert result.stale is False

    def test_acetyl_with_access_extends_life(self):
        """One access doubles the threshold: 14 * 2 = 28 days."""
        mark = _make_mark(durability="acetyl", age_days=20, access_count=1)
        result = _detect_staleness(mark)
        assert result.stale is False

        mark2 = _make_mark(durability="acetyl", age_days=29, access_count=1)
        result2 = _detect_staleness(mark2)
        assert result2.stale is True

    def test_methyl_stale_beyond_threshold(self):
        mark = _make_mark(durability="methyl", age_days=91, access_count=0)
        result = _detect_staleness(mark, threshold_days=90)
        assert result.stale is True
        assert "methyl" in result.reason

    def test_methyl_not_stale_within_threshold(self):
        mark = _make_mark(durability="methyl", age_days=89, access_count=0)
        result = _detect_staleness(mark, threshold_days=90)
        assert result.stale is False

    def test_methyl_access_count_extends_life(self):
        """2 accesses → 90 * 4 = 360 day threshold."""
        mark = _make_mark(durability="methyl", age_days=200, access_count=2)
        result = _detect_staleness(mark, threshold_days=90)
        assert result.stale is False

        mark2 = _make_mark(durability="methyl", age_days=361, access_count=2)
        result2 = _detect_staleness(mark2, threshold_days=90)
        assert result2.stale is True

    def test_project_type_extra_decay(self):
        """Project marks use base 30 days instead of general threshold."""
        mark = _make_mark(mark_type="project", durability="methyl", age_days=31, access_count=0)
        result = _detect_staleness(mark, threshold_days=90)
        assert result.stale is True
        assert "project" in result.reason

    def test_project_not_stale_young(self):
        mark = _make_mark(mark_type="project", durability="methyl", age_days=29, access_count=0)
        result = _detect_staleness(mark, threshold_days=90)
        assert result.stale is False

    def test_custom_threshold(self):
        # Must use separate mark objects: _detect_staleness mutates in-place
        mark_stale = _make_mark(durability="methyl", age_days=50, access_count=0)
        assert _detect_staleness(mark_stale, threshold_days=30).stale is True

        mark_fresh = _make_mark(durability="methyl", age_days=50, access_count=0)
        assert _detect_staleness(mark_fresh, threshold_days=60).stale is False


# ---------------------------------------------------------------------------
# _cluster_marks
# ---------------------------------------------------------------------------


class TestClusterMarks:
    def test_cluster_groups_by_topic(self):
        marks = [
            _make_mark(path=Path("/marks/feedback_tone_formal.md")),
            _make_mark(path=Path("/marks/feedback_tone_casual.md")),
        ]
        clusters = _cluster_marks(marks)
        assert len(clusters) == 1
        assert clusters[0]["topic"] == "tone"
        assert clusters[0]["count"] == 2

    def test_single_mark_no_cluster(self):
        marks = [_make_mark(path=Path("/marks/feedback_unique.md"))]
        assert _cluster_marks(marks) == []

    def test_sorted_by_count_descending(self):
        marks = [
            _make_mark(path=Path("/marks/feedback_alpha_one.md")),
            _make_mark(path=Path("/marks/feedback_alpha_two.md")),
            _make_mark(path=Path("/marks/feedback_alpha_three.md")),
            _make_mark(path=Path("/marks/feedback_beta_one.md")),
            _make_mark(path=Path("/marks/feedback_beta_two.md")),
        ]
        clusters = _cluster_marks(marks)
        assert len(clusters) == 2
        assert clusters[0]["topic"] == "alpha"
        assert clusters[0]["count"] == 3
        assert clusters[1]["topic"] == "beta"
        assert clusters[1]["count"] == 2

    def test_no_prefix_ignored(self):
        """Files with no underscore (single word stem) don't form clusters."""
        marks = [
            _make_mark(path=Path("/marks/standalone.md")),
        ]
        assert _cluster_marks(marks) == []


# ---------------------------------------------------------------------------
# _update_frontmatter_field
# ---------------------------------------------------------------------------


class TestUpdateFrontmatterField:
    def test_update_existing_key(self, tmp_path: Path):
        p = tmp_path / "mark.md"
        p.write_text("---\nname: old\n---\n\nbody\n")
        _update_frontmatter_field(p, "name", "new")
        assert "name: new" in p.read_text()

    def test_insert_new_key(self, tmp_path: Path):
        p = tmp_path / "mark.md"
        p.write_text("---\nname: test\n---\n\nbody\n")
        _update_frontmatter_field(p, "fire_count", "3")
        content = p.read_text()
        assert "fire_count: 3" in content
        assert "name: test" in content
        assert "body" in content

    def test_no_frontmatter_is_noop(self, tmp_path: Path):
        p = tmp_path / "plain.md"
        original = "Just text.\n"
        p.write_text(original)
        _update_frontmatter_field(p, "key", "val")
        assert p.read_text() == original

    def test_preserves_body(self, tmp_path: Path):
        p = tmp_path / "mark.md"
        p.write_text("---\nname: test\n---\n\nImportant body.\n")
        _update_frontmatter_field(p, "extra", "data")
        assert "Important body." in p.read_text()


# ---------------------------------------------------------------------------
# _find_existing_signal
# ---------------------------------------------------------------------------


class TestFindExistingSignal:
    def test_finds_matching_signal(self, tmp_path: Path, monkeypatch):
        sig_dir = _patch_signals(monkeypatch, tmp_path)
        emit_signal("my-signal", "content", source="cc")
        result = _find_existing_signal("my-signal")
        assert result is not None
        assert result.parent == sig_dir

    def test_skips_desensitized(self, tmp_path: Path, monkeypatch):
        _patch_signals(monkeypatch, tmp_path)
        # Fire 5 times to desensitize
        for _ in range(5):
            emit_signal("desens-sig", "content", source="cc")
        # Mark as desensitized in frontmatter
        from metabolon.organelles.demethylase import _parse_frontmatter
        sig_path = _find_existing_signal.__wrapped__ if hasattr(_find_existing_signal, '__wrapped__') else None
        # Actually, _find_existing_signal checks desensitized flag, so we need
        # to emit enough that it gets desensitized (5 fires → desensitized=True via read_signals)
        # But _find_existing_signal itself checks fm desensitized, which is set by read_signals
        # Let's set it manually
        sig_dir = tmp_path / "signals"
        sig_files = list(sig_dir.glob("signal_*.md"))
        assert len(sig_files) == 1
        _update_frontmatter_field(sig_files[0], "desensitized", "true")

        result = _find_existing_signal("desens-sig")
        assert result is None

    def test_no_signals_dir(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(
            "metabolon.organelles.demethylase.SIGNALS_DIR", tmp_path / "nonexistent"
        )
        assert _find_existing_signal("anything") is None

    def test_wrong_name_returns_none(self, tmp_path: Path, monkeypatch):
        _patch_signals(monkeypatch, tmp_path)
        emit_signal("signal-a", "content", source="cc")
        assert _find_existing_signal("signal-b") is None


# ---------------------------------------------------------------------------
# format_report
# ---------------------------------------------------------------------------


class TestFormatReport:
    def test_basic_formatting(self):
        from metabolon.organelles.demethylase import DemethylaseReport

        report = DemethylaseReport(
            total_marks=10,
            methyl_marks=6,
            acetyl_marks=4,
            protected_marks=2,
            stale_candidates=[],
            source_distribution={"cc": 5, "gemini": 5},
            type_distribution={"feedback": 7, "finding": 3},
            mark_clusters=[],
        )
        text = format_report(report)
        assert "Demethylase sweep: 10 marks" in text
        assert "Methyl (durable): 6" in text
        assert "Acetyl (volatile): 4" in text
        assert "Protected (CpG): 2" in text
        assert "cc: 5" in text
        assert "feedback: 7" in text

    def test_with_stale_candidates(self):
        from metabolon.organelles.demethylase import DemethylaseReport

        stale = [
            _make_mark(
                path=Path("/marks/old_thing.md"),
                age_days=200,
                durability="methyl",
                protected=False,
                stale=True,
                reason="methyl mark older than 180d",
            )
        ]
        report = DemethylaseReport(
            total_marks=1,
            stale_candidates=stale,
            source_distribution={},
            type_distribution={},
            mark_clusters=[],
        )
        text = format_report(report)
        assert "Stale candidates:" in text
        assert "old_thing.md" in text
        assert "200d" in text

    def test_with_clusters(self):
        from metabolon.organelles.demethylase import DemethylaseReport

        report = DemethylaseReport(
            total_marks=4,
            mark_clusters=[
                {"topic": "tone", "marks": ["feedback_tone_formal", "feedback_tone_casual"], "count": 2}
            ],
            source_distribution={},
            type_distribution={},
        )
        text = format_report(report)
        assert "Mark clusters" in text
        assert "tone (2 marks)" in text


# ---------------------------------------------------------------------------
# record_access edge cases
# ---------------------------------------------------------------------------


class TestRecordAccess:
    def test_no_frontmatter_is_noop(self, tmp_path: Path):
        p = tmp_path / "plain.md"
        p.write_text("No frontmatter at all.\n")
        record_access(p)
        # File should be unchanged
        assert p.read_text() == "No frontmatter at all.\n"

    def test_unclosed_frontmatter_is_noop(self, tmp_path: Path):
        p = tmp_path / "unclosed.md"
        original = "---\nname: test\n"
        p.write_text(original)
        record_access(p)
        assert p.read_text() == original

    def test_adds_missing_access_count(self, tmp_path: Path):
        """If frontmatter has no access_count, record_access adds it as 1."""
        p = tmp_path / "mark.md"
        p.write_text("---\nname: test\n---\n\nBody.\n")
        record_access(p)
        content = p.read_text()
        assert "access_count: 1" in content
        assert "Body." in content

    def test_increments_existing_count(self, tmp_path: Path):
        p = tmp_path / "mark.md"
        p.write_text("---\nname: test\naccess_count: 4\n---\n\nBody.\n")
        record_access(p)
        content = p.read_text()
        assert "access_count: 5" in content


# ---------------------------------------------------------------------------
# sweep edge cases
# ---------------------------------------------------------------------------


class TestSweepEdgeCases:
    def test_sweep_skips_index_files(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr("metabolon.organelles.demethylase.MARKS_DIR", tmp_path)
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        # Create index files that should be skipped
        (tmp_path / "MEMORY.md").write_text("---\nname: mem\n---\n")
        (tmp_path / "methylome.md").write_text("---\nname: meta\n---\n")
        (tmp_path / "decay-tracker.md").write_text("---\nname: decay\n---\n")
        _write_mark(tmp_path / "feedback_real.md", "Real mark", "feedback")

        report = sweep(tmp_path, dry_run=True)
        assert report.total_marks == 1

    def test_sweep_dry_run_false_deletes_stale(self, tmp_path: Path, monkeypatch):
        """With dry_run=False, stale acetyl marks (>14d old) get deleted."""
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        # Create an acetyl mark and artificially age it
        mark_path = tmp_path / "checkpoint_old.md"
        mark_path.write_text("---\nname: old\ntype: project\n---\n\nOld content.\n")
        # Set mtime to 15 days ago
        import os
        import time
        old_time = time.time() - 15 * 86400
        os.utime(mark_path, (old_time, old_time))

        assert mark_path.exists()
        report = sweep(tmp_path, threshold_days=90, dry_run=False)
        # checkpoint → acetyl → base threshold 14d → 15 days old → stale
        assert not mark_path.exists()
        assert any(m.stale for m in report.stale_candidates)

    def test_sweep_cleans_stale_signals(self, tmp_path: Path, monkeypatch):
        """Sweep cleans signal files older than 14 days from SIGNALS_DIR."""
        import os
        import time

        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        sig_dir = _patch_signals(monkeypatch, tmp_path)

        # Create a signal and age it
        sig_path = sig_dir / "signal_old_20250101-000000_abc123.md"
        sig_path.parent.mkdir(parents=True, exist_ok=True)
        sig_path.write_text("---\nname: old-sig\n---\n\ncontent\n")
        old_time = time.time() - 15 * 86400
        os.utime(sig_path, (old_time, old_time))

        report = sweep(tmp_path, dry_run=True)
        # Signal should appear in stale_candidates but not be deleted (dry_run)
        assert sig_path.exists()
        assert any(s.path == sig_path for s in report.stale_candidates)

    def test_sweep_dry_run_false_deletes_stale_signals(self, tmp_path: Path, monkeypatch):
        """With dry_run=False, stale signals are actually deleted."""
        import os
        import time

        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        sig_dir = _patch_signals(monkeypatch, tmp_path)

        sig_path = sig_dir / "signal_old_20250101-000000_abc123.md"
        sig_path.parent.mkdir(parents=True, exist_ok=True)
        sig_path.write_text("---\nname: old-sig\n---\n\ncontent\n")
        old_time = time.time() - 15 * 86400
        os.utime(sig_path, (old_time, old_time))

        sweep(tmp_path, dry_run=False)
        assert not sig_path.exists()

    def test_sweep_source_distribution_includes_all(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        _write_mark(tmp_path / "feedback_a.md", "A", "feedback", source="cc")
        _write_mark(tmp_path / "feedback_b.md", "B", "feedback", source="gemini")
        _write_mark(tmp_path / "feedback_c.md", "C", "feedback")  # no source → unknown

        report = sweep(tmp_path, dry_run=True)
        assert report.source_distribution["cc"] == 1
        assert report.source_distribution["gemini"] == 1
        assert report.source_distribution["unknown"] == 1


# ---------------------------------------------------------------------------
# consolidate edge cases
# ---------------------------------------------------------------------------


class TestConsolidateEdgeCases:
    def test_consolidate_empty_dir(self, tmp_path: Path, monkeypatch):
        """Consolidation on empty marks dir produces empty report."""
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        empty = tmp_path / "empty_marks"
        empty.mkdir()
        report = consolidate(empty)
        assert report.today_marks == []
        assert report.clusters_found == []
        assert report.strengthened == []
        assert report.methylome_updated is True

    def test_consolidate_strengthens_accessed_marks(self, tmp_path: Path, monkeypatch):
        """Marks modified today with access_count > 0 are strengthened."""
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        d = tmp_path / "marks"
        d.mkdir()
        _write_mark(d / "feedback_one.md", "One", "feedback", access_count="3")
        _write_mark(d / "feedback_two.md", "Two", "feedback", access_count="0")

        report = consolidate(d)
        assert any(m.access_count > 0 for m in report.strengthened)

    def test_consolidate_skips_index_files(self, tmp_path: Path, monkeypatch):
        """MEMORY.md, methylome.md, decay-tracker.md are skipped."""
        monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
        d = tmp_path / "marks"
        d.mkdir()
        (d / "MEMORY.md").write_text("---\nname: mem\n---\n")
        _write_mark(d / "feedback_real.md", "Real", "feedback")

        report = consolidate(d)
        assert len(report.today_marks) == 1
        assert report.today_marks[0].name == "Real"


# ---------------------------------------------------------------------------
# signal_history edge cases
# ---------------------------------------------------------------------------


class TestSignalHistoryEdgeCases:
    def test_limit_zero_returns_empty(self, tmp_path: Path, monkeypatch):
        _patch_signals(monkeypatch, tmp_path)
        emit_signal("sig", "content", source="cc")
        assert signal_history(limit=0) == []

    def test_negative_limit_returns_empty(self, tmp_path: Path, monkeypatch):
        _patch_signals(monkeypatch, tmp_path)
        emit_signal("sig", "content", source="cc")
        assert signal_history(limit=-1) == []

    def test_no_history_file(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(
            "metabolon.organelles.demethylase.SIGNAL_HISTORY_PATH",
            tmp_path / "nonexistent" / "history.jsonl",
        )
        assert signal_history() == []

    def test_malformed_jsonl_line_skipped(self, tmp_path: Path, monkeypatch):
        hist = tmp_path / "state" / "signal-history.jsonl"
        hist.parent.mkdir(parents=True)
        hist.write_text("not json\n")
        monkeypatch.setattr(
            "metabolon.organelles.demethylase.SIGNAL_HISTORY_PATH", hist
        )
        monkeypatch.setattr(
            "metabolon.organelles.demethylase.SIGNALS_DIR", tmp_path / "signals"
        )
        assert signal_history() == []


# ---------------------------------------------------------------------------
# read_signals edge cases
# ---------------------------------------------------------------------------


class TestReadSignalsEdgeCases:
    def test_skips_transduced_signals(self, tmp_path: Path, monkeypatch):
        _patch_signals(monkeypatch, tmp_path)
        emit_signal("trans-sig", "content", source="cc")
        # Manually mark as transduced
        sig_dir = tmp_path / "signals"
        sig_file = list(sig_dir.glob("signal_*.md"))[0]
        _update_frontmatter_field(sig_file, "transduced", "true")

        results = read_signals()
        assert len(results) == 0

    def test_rejected_downstream_command(self, tmp_path: Path, monkeypatch):
        """Shell metacharacters in downstream command → REJECTED."""
        _patch_signals(monkeypatch, tmp_path)
        emit_signal(
            "bad-cascade",
            "trigger",
            source="cc",
            downstream=["echo hack; rm -rf /"],
        )
        results = read_signals(execute_cascade=True)
        assert len(results) == 1
        assert any("REJECTED" in c for c in results[0]["cascades_fired"])

    def test_failed_downstream_command(self, tmp_path: Path, monkeypatch):
        """Non-zero exit code → FAILED."""
        _patch_signals(monkeypatch, tmp_path)
        emit_signal(
            "fail-cascade",
            "trigger",
            source="cc",
            downstream=["false"],  # command that always exits 1
        )
        results = read_signals(execute_cascade=True)
        assert len(results) == 1
        assert any("FAILED" in c for c in results[0]["cascades_fired"])

    def test_no_signals_dir(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(
            "metabolon.organelles.demethylase.SIGNALS_DIR",
            tmp_path / "nonexistent",
        )
        assert read_signals() == []


# ---------------------------------------------------------------------------
# resensitize edge cases
# ---------------------------------------------------------------------------


class TestResensitizeEdgeCases:
    def test_no_signals_dir(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(
            "metabolon.organelles.demethylase.SIGNALS_DIR",
            tmp_path / "nonexistent",
        )
        assert resensitize("anything") is False

    def test_non_desensitized_signal(self, tmp_path: Path, monkeypatch):
        _patch_signals(monkeypatch, tmp_path)
        emit_signal("active-sig", "content", source="cc")
        # Signal exists but is not desensitized → False
        assert resensitize("active-sig") is False

    def test_no_matching_name(self, tmp_path: Path, monkeypatch):
        _patch_signals(monkeypatch, tmp_path)
        emit_signal("signal-a", "content", source="cc")
        assert resensitize("signal-b") is False


# ---------------------------------------------------------------------------
# emit_signal edge cases
# ---------------------------------------------------------------------------


class TestEmitSignalEdgeCases:
    def test_emit_without_downstream(self, tmp_path: Path, monkeypatch):
        """No downstream block in file when downstream=None."""
        _patch_signals(monkeypatch, tmp_path)
        path = emit_signal("bare-signal", "content", source="cc")
        content = path.read_text()
        assert "downstream:" not in content

    def test_emit_creates_signals_dir(self, tmp_path: Path, monkeypatch):
        sig_dir = tmp_path / "new_signals"
        hist = tmp_path / "state" / "signal-history.jsonl"
        monkeypatch.setattr("metabolon.organelles.demethylase.SIGNALS_DIR", sig_dir)
        monkeypatch.setattr(
            "metabolon.organelles.demethylase.SIGNAL_HISTORY_PATH", hist
        )
        assert not sig_dir.exists()
        emit_signal("fresh", "content", source="cc")
        assert sig_dir.exists()

    def test_emit_writes_history_jsonl(self, tmp_path: Path, monkeypatch):
        hist = _patch_signals(monkeypatch, tmp_path) / ".." / "state" / "signal-history.jsonl"
        hist = tmp_path / "state" / "signal-history.jsonl"
        emit_signal("hist-test", "content", source="cc")
        assert hist.exists()
        lines = hist.read_text().strip().splitlines()
        assert len(lines) == 1
        import json
        entry = json.loads(lines[0])
        assert entry["name"] == "hist-test"
        assert entry["deduplicated"] is False
        assert entry["fire_count"] == 1


# ---------------------------------------------------------------------------
# transduce edge cases
# ---------------------------------------------------------------------------


class TestTransduceEdgeCases:
    def test_transduce_no_downstream_returns_empty(self, tmp_path: Path, monkeypatch):
        """Signal with no downstream commands → filtered out by transduce."""
        _patch_signals(monkeypatch, tmp_path)
        emit_signal("no-downstream", "content", source="cc")
        results = transduce()
        assert results == []

    def test_transduce_with_name_filter(self, tmp_path: Path, monkeypatch):
        _patch_signals(monkeypatch, tmp_path)
        emit_signal("alpha-signal", "a", source="cc", downstream=["echo a"])
        emit_signal("beta-signal", "b", source="cc", downstream=["echo b"])

        results = transduce(name_filter="alpha")
        assert len(results) == 1
        assert results[0]["name"] == "alpha-signal"


# ---------------------------------------------------------------------------
# analyze_mark integration
# ---------------------------------------------------------------------------


class TestAnalyzeMark:
    def test_unknown_source_when_missing(self, tmp_path: Path):
        p = tmp_path / "mark.md"
        p.write_text("---\nname: test\ntype: feedback\n---\n\nBody.\n")
        mark = analyze_mark(p)
        assert mark.source == "unknown"

    def test_resolved_durability(self, tmp_path: Path):
        p = tmp_path / "resolved_bug.md"
        p.write_text("---\nname: fixed\ntype: finding\n---\n\nBody.\n")
        mark = analyze_mark(p)
        assert mark.durability == "acetyl"

    def test_core_protected_pattern(self, tmp_path: Path):
        p = tmp_path / "feedback_keep_digging.md"
        p.write_text("---\nname: dig\ntype: feedback\n---\n\nBody.\n")
        mark = analyze_mark(p)
        assert mark.protected is True
