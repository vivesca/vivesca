"""Tests for metabolon.enzymes.demethylase — signal + mark management tool."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.demethylase import DemethylaseResult, demethylase
from metabolon.organelles.demethylase import DemethylaseReport, MarkAnalysis


# ── helpers ──────────────────────────────────────────────────────────

def _mark(**overrides) -> MarkAnalysis:
    defaults = dict(
        path=Path("/tmp/fake.md"),
        name="test-mark",
        mark_type="feedback",
        durability="methyl",
        protected=False,
        source="cc",
        age_days=10,
        last_modified_days=10,
        access_count=0,
        stale=False,
        reason="",
    )
    defaults.update(overrides)
    return MarkAnalysis(**defaults)


def _report(**overrides) -> DemethylaseReport:
    defaults = dict(
        total_marks=5,
        methyl_marks=3,
        acetyl_marks=2,
        protected_marks=1,
        stale_candidates=[],
        source_distribution={"cc": 3, "gemini": 2},
        type_distribution={"feedback": 4, "finding": 1},
        mark_clusters=[{"topic": "digging", "marks": ["a", "b"], "count": 2}],
    )
    defaults.update(overrides)
    return DemethylaseReport(**defaults)


# ── action: emit ─────────────────────────────────────────────────────

class TestEmit:
    @patch("metabolon.organelles.demethylase.emit_signal")
    def test_emit_success(self, mock_emit):
        mock_emit.return_value = Path("/tmp/signal_alert.md")
        res = demethylase(action="emit", name="alert", content="fire!")
        assert isinstance(res, DemethylaseResult)
        assert "signal_alert.md" in res.results

    def test_emit_missing_name(self):
        res = demethylase(action="emit", name="", content="body")
        assert "requires" in res.results

    def test_emit_missing_content(self):
        res = demethylase(action="emit", name="x", content="")
        assert "requires" in res.results

    @patch("metabolon.organelles.demethylase.emit_signal")
    def test_emit_with_downstream(self, mock_emit):
        mock_emit.return_value = Path("/tmp/signal_x.md")
        res = demethylase(action="emit", name="x", content="c", downstream=["cmd1"])
        assert "1 downstream" in res.results


# ── action: read ─────────────────────────────────────────────────────

class TestRead:
    @patch("metabolon.organelles.demethylase.read_signals")
    def test_read_empty(self, mock_read):
        mock_read.return_value = []
        res = demethylase(action="read")
        assert "No signals" in res.results

    @patch("metabolon.organelles.demethylase.read_signals")
    def test_read_with_signals(self, mock_read):
        mock_read.return_value = [
            {"name": "sig1", "source": "cc", "age_days": 2, "content": "hello"},
            {
                "name": "sig2",
                "source": "gemini",
                "age_days": 5,
                "content": "world",
                "downstream": ["cmd"],
                "cascades_fired": ["cmd"],
            },
        ]
        res = demethylase(action="read")
        assert "2 signal(s)" in res.results
        assert "sig1" in res.results
        assert "Downstream: cmd" in res.results


# ── action: history ──────────────────────────────────────────────────

class TestHistory:
    @patch("metabolon.organelles.demethylase.signal_history")
    def test_history_empty(self, mock_hist):
        mock_hist.return_value = []
        res = demethylase(action="history")
        assert "No signal history" in res.results

    @patch("metabolon.organelles.demethylase.signal_history")
    def test_history_with_entries(self, mock_hist):
        mock_hist.return_value = [
            {
                "timestamp": "2025-01-01",
                "name": "s1",
                "source": "cc",
                "fire_count": 1,
                "deduplicated": False,
                "content": "hi",
            },
        ]
        res = demethylase(action="history")
        assert "1 signal(s)" in res.results
        assert "s1" in res.results


# ── action: transduce ────────────────────────────────────────────────

class TestTransduce:
    @patch("metabolon.organelles.demethylase.transduce")
    def test_transduce_empty(self, mock_tr):
        mock_tr.return_value = []
        res = demethylase(action="transduce")
        assert "No signals transduced" in res.results

    @patch("metabolon.organelles.demethylase.transduce")
    def test_transduce_with_results(self, mock_tr):
        mock_tr.return_value = [
            {"name": "s1", "source": "cc", "cascades_fired": ["cmd1"]},
        ]
        res = demethylase(action="transduce")
        assert "1 signal(s) transduced" in res.results
        assert "cmd1" in res.results


# ── action: resensitize ──────────────────────────────────────────────

class TestResensitize:
    @patch("metabolon.organelles.demethylase.resensitize")
    def test_resensitize_found(self, mock_rs):
        mock_rs.return_value = True
        res = demethylase(action="resensitize", name="my-sig")
        assert "resensitized" in res.results

    @patch("metabolon.organelles.demethylase.resensitize")
    def test_resensitize_not_found(self, mock_rs):
        mock_rs.return_value = False
        res = demethylase(action="resensitize", name="missing")
        assert "No desensitized signal" in res.results

    def test_resensitize_missing_name(self):
        res = demethylase(action="resensitize", name="")
        assert "requires" in res.results


# ── action: sweep ────────────────────────────────────────────────────

class TestSweep:
    @patch("metabolon.organelles.demethylase.format_report")
    @patch("metabolon.organelles.demethylase.sweep")
    def test_sweep_basic(self, mock_sweep, mock_fmt):
        rpt = _report()
        mock_sweep.return_value = rpt
        mock_fmt.return_value = "FORMATTED REPORT"
        res = demethylase(action="sweep")
        assert "5 total" in res.results
        assert "FORMATTED REPORT" in res.results
        # sorted() by key alphabetically → cc=3 first, gemini=2 second
        assert "cc=3, gemini=2" in res.results

    @patch("metabolon.organelles.demethylase.format_report")
    @patch("metabolon.organelles.demethylase.sweep")
    def test_sweep_with_stale(self, mock_sweep, mock_fmt):
        stale = _mark(stale=True, reason="old", path=Path("/tmp/old_mark.md"))
        rpt = _report(stale_candidates=[stale])
        mock_sweep.return_value = rpt
        mock_fmt.return_value = "FMT"
        res = demethylase(action="sweep")
        assert "Stale marks:" in res.results
        assert "old_mark.md" in res.results

    @patch("metabolon.organelles.demethylase.format_report")
    @patch("metabolon.organelles.demethylase.sweep")
    def test_sweep_with_clusters(self, mock_sweep, mock_fmt):
        rpt = _report()
        mock_sweep.return_value = rpt
        mock_fmt.return_value = "FMT"
        res = demethylase(action="sweep")
        assert "Top clusters:" in res.results

    @patch("metabolon.organelles.demethylase.format_report")
    @patch("metabolon.organelles.demethylase.sweep")
    def test_sweep_empty_distributions(self, mock_sweep, mock_fmt):
        rpt = _report(source_distribution={}, type_distribution={}, mark_clusters=[])
        mock_sweep.return_value = rpt
        mock_fmt.return_value = "FMT"
        res = demethylase(action="sweep")
        assert "Source distribution" not in res.results
        assert "Type distribution" not in res.results
        assert "Top clusters" not in res.results


# ── action: record_access ────────────────────────────────────────────

class TestRecordAccess:
    def test_record_access_missing_filename(self):
        res = demethylase(action="record_access", mark_filename="")
        assert "requires" in res.results

    def test_record_access_file_not_found(self):
        with patch("metabolon.locus.marks", Path("/tmp/nonexistent_marks_xyz")):
            res = demethylase(action="record_access", mark_filename="nope.md")
            assert "not found" in res.results.lower()

    def test_record_access_file_exists(self, tmp_path: Path):
        marks = tmp_path / "marks"
        marks.mkdir()
        mark_file = marks / "test.md"
        mark_file.write_text("---\nname: test\n---\nbody")
        with patch("metabolon.locus.marks", marks):
            with patch("metabolon.organelles.demethylase.record_access") as mock_ra:
                res = demethylase(action="record_access", mark_filename="test.md")
                assert "Access recorded" in res.results
                mock_ra.assert_called_once()


# ── action: unknown / edge cases ─────────────────────────────────────

class TestUnknown:
    def test_unknown_action(self):
        res = demethylase(action="foobar")
        assert "Unknown action" in res.results
        assert "emit" in res.results

    def test_action_case_insensitive(self):
        res = demethylase(action="EMIT", name="", content="")
        assert "requires" in res.results

    def test_action_whitespace_trimmed(self):
        res = demethylase(action="  emit  ", name="", content="")
        assert "requires" in res.results


# ── return type ──────────────────────────────────────────────────────

class TestReturnType:
    @patch("metabolon.organelles.demethylase.read_signals")
    def test_returns_demethylase_result(self, mock_read):
        mock_read.return_value = []
        res = demethylase(action="read")
        assert isinstance(res, DemethylaseResult)
        assert isinstance(res.results, str)
