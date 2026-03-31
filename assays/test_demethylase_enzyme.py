"""Tests for demethylase enzyme — the @tool dispatcher layer.

Mocks organelle-level functions (lazy-imported inside the enzyme body) by
patching metabolon.organelles.demethylase.<func> directly.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.demethylase import DemethylaseResult, demethylase
from metabolon.organelles.demethylase import DemethylaseReport, MarkAnalysis


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mark(path_name: str = "stale.md", **kwargs) -> MarkAnalysis:
    defaults = dict(
        path=Path("/fake") / path_name,
        name="Test mark",
        mark_type="feedback",
        durability="methyl",
        protected=False,
        source="cc",
        age_days=100,
        last_modified_days=100,
        access_count=0,
        stale=True,
        reason="old",
    )
    defaults.update(kwargs)
    return MarkAnalysis(**defaults)


ORGANELLE = "metabolon.organelles.demethylase"


# ---------------------------------------------------------------------------
# emit action
# ---------------------------------------------------------------------------

class TestEmit:
    @patch(f"{ORGANELLE}.emit_signal")
    def test_emit_happy_path(self, mock_emit):
        mock_path = MagicMock()
        mock_path.name = "signal_test.md"
        mock_emit.return_value = mock_path

        result = demethylase(action="emit", name="test-signal", content="hello world")

        mock_emit.assert_called_once_with(
            "test-signal", "hello world", "unknown", downstream=None
        )
        assert result.results == "Signal emitted: signal_test.md"

    @patch(f"{ORGANELLE}.emit_signal")
    def test_emit_with_source_and_downstream(self, mock_emit):
        mock_path = MagicMock()
        mock_path.name = "signal_go.md"
        mock_emit.return_value = mock_path

        downstream = ["echo hi", "echo bye"]
        result = demethylase(
            action="emit",
            name="go-signal",
            content="content",
            source="goose",
            downstream=downstream,
        )

        mock_emit.assert_called_once_with(
            "go-signal", "content", "goose", downstream=downstream
        )
        assert "2 downstream commands" in result.results

    def test_emit_missing_name(self):
        result = demethylase(action="emit", name="", content="body")
        assert "emit requires: name, content" in result.results

    def test_emit_missing_content(self):
        result = demethylase(action="emit", name="sig", content="")
        assert "emit requires: name, content" in result.results


# ---------------------------------------------------------------------------
# read action
# ---------------------------------------------------------------------------

class TestRead:
    @patch(f"{ORGANELLE}.read_signals")
    def test_read_empty(self, mock_read):
        mock_read.return_value = []
        result = demethylase(action="read")
        assert "No signals found" in result.results

    @patch(f"{ORGANELLE}.read_signals")
    def test_read_signals_formatted(self, mock_read):
        mock_read.return_value = [
            {
                "name": "alpha",
                "source": "cc",
                "age_days": 3,
                "content": "hello",
                "downstream": ["echo a"],
                "cascades_fired": ["echo a"],
            }
        ]
        result = demethylase(action="read")
        assert "1 signal(s) pending" in result.results
        assert "Signal: alpha" in result.results
        assert "Source: cc" in result.results
        assert "Age: 3 days" in result.results
        assert "Content: hello" in result.results
        assert "Downstream: echo a" in result.results
        assert "Cascades fired: echo a" in result.results

    @patch(f"{ORGANELLE}.read_signals")
    def test_read_passes_filters(self, mock_read):
        mock_read.return_value = []
        demethylase(
            action="read",
            name_filter="alpha",
            desensitization_threshold=10,
            include_desensitized=True,
            execute_cascade=True,
        )
        mock_read.assert_called_once_with(
            name_filter="alpha",
            desensitization_threshold=10,
            include_desensitized=True,
            execute_cascade=True,
        )

    @patch(f"{ORGANELLE}.read_signals")
    def test_read_signal_without_extras(self, mock_read):
        mock_read.return_value = [
            {"name": "beta", "source": "goose", "age_days": 1, "content": "yo"},
        ]
        result = demethylase(action="read")
        assert "Downstream" not in result.results
        assert "Cascades fired" not in result.results


# ---------------------------------------------------------------------------
# history action
# ---------------------------------------------------------------------------

class TestHistory:
    @patch(f"{ORGANELLE}.signal_history")
    def test_history_empty(self, mock_hist):
        mock_hist.return_value = []
        result = demethylase(action="history")
        assert "No signal history found" in result.results

    @patch(f"{ORGANELLE}.signal_history")
    def test_history_formatted(self, mock_hist):
        mock_hist.return_value = [
            {
                "timestamp": "2025-01-01T00:00:00",
                "name": "sig-a",
                "source": "cc",
                "fire_count": 3,
                "deduplicated": True,
                "content": "body text",
            }
        ]
        result = demethylase(action="history")
        assert "1 signal(s) in history" in result.results
        assert "[2025-01-01T00:00:00] sig-a" in result.results
        assert "Fire count: 3" in result.results
        assert "Deduplicated: True" in result.results

    @patch(f"{ORGANELLE}.signal_history")
    def test_history_passes_args(self, mock_hist):
        mock_hist.return_value = []
        demethylase(action="history", limit=5, name_filter="test")
        mock_hist.assert_called_once_with(limit=5, name_filter="test")


# ---------------------------------------------------------------------------
# transduce action
# ---------------------------------------------------------------------------

class TestTransduce:
    @patch(f"{ORGANELLE}.transduce")
    def test_transduce_none_results(self, mock_trans):
        mock_trans.return_value = []
        result = demethylase(action="transduce")
        assert "No signals transduced" in result.results

    @patch(f"{ORGANELLE}.transduce")
    def test_transduce_with_cascades(self, mock_trans):
        mock_trans.return_value = [
            {"name": "enzyme-cascade", "source": "cc", "cascades_fired": ["echo hi"]},
        ]
        result = demethylase(action="transduce")
        assert "1 signal(s) transduced" in result.results
        assert "Cascades fired: echo hi" in result.results

    @patch(f"{ORGANELLE}.transduce")
    def test_transduce_without_cascades(self, mock_trans):
        mock_trans.return_value = [
            {"name": "plain-signal", "source": "goose", "cascades_fired": []},
        ]
        result = demethylase(action="transduce")
        assert "Cascades fired" not in result.results

    @patch(f"{ORGANELLE}.transduce")
    def test_transduce_passes_name_filter(self, mock_trans):
        mock_trans.return_value = []
        demethylase(action="transduce", name_filter="my-sig")
        mock_trans.assert_called_once_with(name_filter="my-sig")


# ---------------------------------------------------------------------------
# resensitize action
# ---------------------------------------------------------------------------

class TestResensitize:
    @patch(f"{ORGANELLE}.resensitize")
    def test_resensitize_found(self, mock_resens):
        mock_resens.return_value = True
        result = demethylase(action="resensitize", name="tired-receptor")
        mock_resens.assert_called_once_with("tired-receptor")
        assert "resensitized" in result.results
        assert "receptor recycled" in result.results

    @patch(f"{ORGANELLE}.resensitize")
    def test_resensitize_not_found(self, mock_resens):
        mock_resens.return_value = False
        result = demethylase(action="resensitize", name="missing")
        assert "No desensitized signal found" in result.results

    def test_resensitize_missing_name(self):
        result = demethylase(action="resensitize", name="")
        assert "resensitize requires: name" in result.results


# ---------------------------------------------------------------------------
# sweep action
# ---------------------------------------------------------------------------

class TestSweep:
    @patch(f"{ORGANELLE}.format_report")
    @patch(f"{ORGANELLE}.sweep")
    def test_sweep_basic(self, mock_sweep, mock_format):
        report = DemethylaseReport(
            total_marks=10,
            methyl_marks=7,
            acetyl_marks=3,
            protected_marks=2,
        )
        mock_sweep.return_value = report
        mock_format.return_value = "formatted report text"

        result = demethylase(action="sweep", threshold_days=60, dry_run=True)

        mock_sweep.assert_called_once_with(threshold_days=60, dry_run=True)
        mock_format.assert_called_once_with(report)
        assert "Marks: 10 total" in result.results
        assert "7 methyl, 3 acetyl" in result.results
        assert "2 protected" in result.results
        assert "Stale: 0" in result.results
        assert "formatted report text" in result.results

    @patch(f"{ORGANELLE}.format_report")
    @patch(f"{ORGANELLE}.sweep")
    def test_sweep_with_distributions(self, mock_sweep, mock_format):
        report = DemethylaseReport(
            total_marks=5,
            source_distribution={"cc": 3, "goose": 2},
            type_distribution={"feedback": 4, "finding": 1},
            mark_clusters=[{"topic": "tone", "count": 3, "marks": ["a", "b"]}],
            stale_candidates=[_make_mark("old_one.md")],
        )
        mock_sweep.return_value = report
        mock_format.return_value = "report"

        result = demethylase(action="sweep")
        assert "Source distribution: cc=3, goose=2" in result.results
        assert "Type distribution: feedback=4, finding=1" in result.results
        assert "Top clusters: 1 shown of 1" in result.results
        assert "Stale marks: old_one.md" in result.results

    @patch(f"{ORGANELLE}.format_report")
    @patch(f"{ORGANELLE}.sweep")
    def test_sweep_many_clusters_truncated(self, mock_sweep, mock_format):
        clusters = [{"topic": f"t{i}", "count": 2, "marks": ["a"]} for i in range(15)]
        report = DemethylaseReport(mark_clusters=clusters)
        mock_sweep.return_value = report
        mock_format.return_value = "report"

        result = demethylase(action="sweep")
        assert "Top clusters: 10 shown of 15" in result.results


# ---------------------------------------------------------------------------
# record_access action
# ---------------------------------------------------------------------------

class TestRecordAccess:
    def test_record_access_missing_filename(self):
        result = demethylase(action="record_access", mark_filename="")
        assert "record_access requires: mark_filename" in result.results

    def test_record_access_file_not_found(self):
        with patch("metabolon.locus.marks") as mock_marks:
            mark_path = MagicMock()
            mark_path.exists.return_value = False
            mock_marks.__truediv__ = lambda self, other: mark_path

            result = demethylase(action="record_access", mark_filename="gone.md")
            assert "Mark not found: gone.md" in result.results

    def test_record_access_success(self):
        with patch("metabolon.locus.marks") as mock_marks, \
             patch(f"{ORGANELLE}.record_access") as mock_record:
            mark_path = MagicMock()
            mark_path.exists.return_value = True
            mock_marks.__truediv__ = lambda self, other: mark_path

            result = demethylase(action="record_access", mark_filename="exists.md")
            mock_record.assert_called_once_with(mark_path)
            assert "Access recorded for exists.md" in result.results


# ---------------------------------------------------------------------------
# unknown / edge cases
# ---------------------------------------------------------------------------

class TestDispatch:
    def test_unknown_action(self):
        result = demethylase(action="foobar")
        assert "Unknown action 'foobar'" in result.results
        assert "emit, read, history" in result.results

    @patch(f"{ORGANELLE}.emit_signal")
    def test_action_case_insensitive(self, mock_emit):
        mock_path = MagicMock()
        mock_path.name = "sig.md"
        mock_emit.return_value = mock_path

        result = demethylase(action=" EMIT ", name="x", content="y")
        mock_emit.assert_called_once()
        assert "Signal emitted" in result.results

    def test_result_type(self):
        result = demethylase(action="unknown")
        assert isinstance(result, DemethylaseResult)

    @patch(f"{ORGANELLE}.read_signals")
    def test_default_action_params(self, mock_read):
        mock_read.return_value = []
        demethylase(action="read")
        mock_read.assert_called_once_with(
            name_filter=None,
            desensitization_threshold=5,
            include_desensitized=False,
            execute_cascade=False,
        )
