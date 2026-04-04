from __future__ import annotations

"""Tests for demethylase enzyme — signal + mark management dispatcher.

Tests the @tool-decorated demethylase() function in metabolon.enzymes.demethylase
by mocking all organelle-layer imports.  The enzyme uses lazy imports
(inside function body), so we patch at the organelle module.
"""


from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from metabolon.enzymes.demethylase import DemethylaseResult, demethylase

# Organelle module path for patching lazy imports
_ORG = "metabolon.organelles.demethylase"
_LOCUS = "metabolon.locus"


def _make_report(**overrides) -> SimpleNamespace:
    """Build a mock DemethylaseReport with sensible defaults."""
    defaults = dict(
        total_marks=10,
        methyl_marks=6,
        acetyl_marks=3,
        protected_marks=2,
        stale_candidates=[],
        source_distribution={"cc": 7, "goose": 3},
        type_distribution={"feedback": 5, "finding": 3, "project": 2},
        mark_clusters=[{"topic": "tone", "count": 2}],
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# -- emit action --------------------------------------------------------------


class TestEmitAction:
    """demethylase(action='emit', ...) tests."""

    @patch(f"{_ORG}.emit_signal")
    def test_emit_success(self, mock_emit):
        mock_path = MagicMock()
        mock_path.name = "signal_alert.md"
        mock_emit.return_value = mock_path

        result = demethylase(action="emit", name="alert", content="something broke")
        assert isinstance(result, DemethylaseResult)
        assert "Signal emitted: signal_alert.md" in result.results
        mock_emit.assert_called_once_with("alert", "something broke", "unknown", downstream=None)

    @patch(f"{_ORG}.emit_signal")
    def test_emit_with_source_and_downstream(self, mock_emit):
        mock_path = MagicMock()
        mock_path.name = "signal_go.md"
        mock_emit.return_value = mock_path

        result = demethylase(
            action="emit",
            name="go",
            content="proceed",
            source="goose",
            downstream=["echo hello", "echo world"],
        )
        assert "2 downstream commands" in result.results
        mock_emit.assert_called_once_with(
            "go", "proceed", "goose", downstream=["echo hello", "echo world"]
        )

    def test_emit_missing_name(self):
        result = demethylase(action="emit", name="", content="has content")
        assert "emit requires: name, content" in result.results

    def test_emit_missing_content(self):
        result = demethylase(action="emit", name="has_name", content="")
        assert "emit requires: name, content" in result.results

    def test_emit_missing_both(self):
        result = demethylase(action="emit", name="", content="")
        assert "emit requires: name, content" in result.results


# -- read action --------------------------------------------------------------


class TestReadAction:
    """demethylase(action='read', ...) tests."""

    @patch(f"{_ORG}.read_signals")
    def test_read_with_signals(self, mock_read):
        mock_read.return_value = [
            {
                "name": "bug-found",
                "source": "goose",
                "age_days": 2,
                "content": "null pointer in parser",
                "downstream": ["echo alert"],
                "cascades_fired": [],
            },
        ]

        result = demethylase(action="read")
        assert "1 signal(s) pending:" in result.results
        assert "Signal: bug-found" in result.results
        assert "Source: goose" in result.results
        assert "Age: 2 days" in result.results
        assert "Downstream: echo alert" in result.results
        mock_read.assert_called_once_with(
            name_filter=None,
            desensitization_threshold=5,
            include_desensitized=False,
            execute_cascade=False,
        )

    @patch(f"{_ORG}.read_signals")
    def test_read_with_cascades_fired(self, mock_read):
        mock_read.return_value = [
            {
                "name": "chain",
                "source": "cc",
                "age_days": 1,
                "content": "cascaded signal",
                "cascades_fired": ["echo step1", "echo step2"],
            },
        ]
        result = demethylase(action="read")
        assert "Cascades fired: echo step1, echo step2" in result.results

    @patch(f"{_ORG}.read_signals")
    def test_read_no_signals(self, mock_read):
        mock_read.return_value = []
        result = demethylase(action="read")
        assert "No signals found." in result.results

    @patch(f"{_ORG}.read_signals")
    def test_read_passes_filters(self, mock_read):
        mock_read.return_value = []
        demethylase(
            action="read",
            name_filter="test",
            desensitization_threshold=10,
            include_desensitized=True,
            execute_cascade=True,
        )
        mock_read.assert_called_once_with(
            name_filter="test",
            desensitization_threshold=10,
            include_desensitized=True,
            execute_cascade=True,
        )

    @patch(f"{_ORG}.read_signals")
    def test_read_signal_without_optional_fields(self, mock_read):
        """Signal dict without downstream or cascades_fired keys is fine."""
        mock_read.return_value = [
            {"name": "simple", "source": "cc", "age_days": 0, "content": "hi"},
        ]
        result = demethylase(action="read")
        assert "Signal: simple" in result.results
        assert "Downstream" not in result.results
        assert "Cascades fired" not in result.results


# -- history action -----------------------------------------------------------


class TestHistoryAction:
    """demethylase(action='history', ...) tests."""

    @patch(f"{_ORG}.signal_history")
    def test_history_with_entries(self, mock_history):
        mock_history.return_value = [
            {
                "timestamp": "2025-01-15T10:30:00",
                "name": "deploy-done",
                "source": "goose",
                "fire_count": 2,
                "deduplicated": True,
                "content": "Deployed v1.2",
            },
        ]
        result = demethylase(action="history")
        assert "1 signal(s) in history:" in result.results
        assert "[2025-01-15T10:30:00] deploy-done" in result.results
        assert "Fire count: 2" in result.results
        assert "Deduplicated: True" in result.results
        mock_history.assert_called_once_with(limit=20, name_filter=None)

    @patch(f"{_ORG}.signal_history")
    def test_history_no_entries(self, mock_history):
        mock_history.return_value = []
        result = demethylase(action="history")
        assert "No signal history found." in result.results

    @patch(f"{_ORG}.signal_history")
    def test_history_passes_filters(self, mock_history):
        mock_history.return_value = []
        demethylase(action="history", limit=5, name_filter="deploy")
        mock_history.assert_called_once_with(limit=5, name_filter="deploy")

    @patch(f"{_ORG}.signal_history")
    def test_history_multiple_entries(self, mock_history):
        mock_history.return_value = [
            {
                "timestamp": "2025-01-15T10:00:00",
                "name": "first",
                "source": "cc",
                "fire_count": 1,
                "deduplicated": False,
                "content": "c1",
            },
            {
                "timestamp": "2025-01-15T11:00:00",
                "name": "second",
                "source": "goose",
                "fire_count": 3,
                "deduplicated": True,
                "content": "c2",
            },
        ]
        result = demethylase(action="history")
        assert "2 signal(s) in history:" in result.results
        assert "Fire count: 3" in result.results


# -- transduce action ---------------------------------------------------------


class TestTransduceAction:
    """demethylase(action='transduce', ...) tests."""

    @patch(f"{_ORG}.transduce")
    def test_transduce_with_results(self, mock_transduce):
        mock_transduce.return_value = [
            {"name": "cascade-a", "source": "cc", "cascades_fired": ["echo step1"]},
        ]
        result = demethylase(action="transduce")
        assert "1 signal(s) transduced:" in result.results
        assert "Signal: cascade-a" in result.results
        assert "Cascades fired: echo step1" in result.results
        mock_transduce.assert_called_once_with(name_filter=None)

    @patch(f"{_ORG}.transduce")
    def test_transduce_no_results(self, mock_transduce):
        mock_transduce.return_value = []
        result = demethylase(action="transduce")
        assert "No signals transduced." in result.results

    @patch(f"{_ORG}.transduce")
    def test_transduce_with_filter(self, mock_transduce):
        mock_transduce.return_value = []
        demethylase(action="transduce", name_filter="deploy")
        mock_transduce.assert_called_once_with(name_filter="deploy")

    @patch(f"{_ORG}.transduce")
    def test_transduce_no_cascades_fired(self, mock_transduce):
        mock_transduce.return_value = [
            {"name": "no-cascade", "source": "cc"},
        ]
        result = demethylase(action="transduce")
        assert "Signal: no-cascade" in result.results
        assert "Cascades fired" not in result.results

    @patch(f"{_ORG}.transduce")
    def test_transduce_multiple(self, mock_transduce):
        mock_transduce.return_value = [
            {"name": "a", "source": "cc", "cascades_fired": ["cmd1"]},
            {"name": "b", "source": "goose"},
        ]
        result = demethylase(action="transduce")
        assert "2 signal(s) transduced:" in result.results


# -- resensitize action -------------------------------------------------------


class TestResensitizeAction:
    """demethylase(action='resensitize', ...) tests."""

    @patch(f"{_ORG}.resensitize")
    def test_resensitize_success(self, mock_resensitize):
        mock_resensitize.return_value = True
        result = demethylase(action="resensitize", name="tired-receptor")
        assert "resensitized" in result.results
        assert "receptor recycled" in result.results
        mock_resensitize.assert_called_once_with("tired-receptor")

    @patch(f"{_ORG}.resensitize")
    def test_resensitize_not_found(self, mock_resensitize):
        mock_resensitize.return_value = False
        result = demethylase(action="resensitize", name="nonexistent")
        assert "No desensitized signal found" in result.results
        assert "nonexistent" in result.results

    def test_resensitize_missing_name(self):
        result = demethylase(action="resensitize", name="")
        assert "resensitize requires: name" in result.results


# -- sweep action -------------------------------------------------------------


class TestSweepAction:
    """demethylase(action='sweep', ...) tests."""

    @patch(f"{_ORG}.format_report")
    @patch(f"{_ORG}.sweep")
    def test_sweep_basic(self, mock_sweep, mock_format):
        report = _make_report()
        mock_sweep.return_value = report
        mock_format.return_value = "FORMATTED REPORT"

        result = demethylase(action="sweep")
        assert "Marks: 10 total (6 methyl, 3 acetyl, 2 protected)" in result.results
        assert "Stale: 0." in result.results
        assert "FORMATTED REPORT" in result.results
        assert "Source distribution: cc=7, goose=3" in result.results
        assert "Type distribution: feedback=5, finding=3, project=2" in result.results
        assert "Top clusters: 1 shown of 1." in result.results
        mock_sweep.assert_called_once_with(threshold_days=90, dry_run=True)

    @patch(f"{_ORG}.format_report")
    @patch(f"{_ORG}.sweep")
    def test_sweep_with_stale(self, mock_sweep, mock_format):
        from pathlib import Path

        stale = [SimpleNamespace(path=Path("stale1.md")), SimpleNamespace(path=Path("stale2.md"))]
        report = _make_report(stale_candidates=stale)
        mock_sweep.return_value = report
        mock_format.return_value = "REPORT"

        result = demethylase(action="sweep")
        assert "Stale marks: stale1.md, stale2.md" in result.results

    @patch(f"{_ORG}.format_report")
    @patch(f"{_ORG}.sweep")
    def test_sweep_custom_params(self, mock_sweep, mock_format):
        report = _make_report()
        mock_sweep.return_value = report
        mock_format.return_value = "REPORT"

        demethylase(action="sweep", threshold_days=30, dry_run=False)
        mock_sweep.assert_called_once_with(threshold_days=30, dry_run=False)

    @patch(f"{_ORG}.format_report")
    @patch(f"{_ORG}.sweep")
    def test_sweep_no_distributions(self, mock_sweep, mock_format):
        report = _make_report(source_distribution={}, type_distribution={}, mark_clusters=[])
        mock_sweep.return_value = report
        mock_format.return_value = "REPORT"

        result = demethylase(action="sweep")
        assert "Source distribution" not in result.results
        assert "Type distribution" not in result.results
        assert "Top clusters" not in result.results
        assert "Stale marks" not in result.results


# -- record_access action -----------------------------------------------------


class TestRecordAccessAction:
    """demethylase(action='record_access', ...) tests."""

    @patch(f"{_ORG}.record_access")
    @patch(f"{_LOCUS}.marks")
    def test_record_access_success(self, mock_marks_dir, mock_record):
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_marks_dir.__truediv__ = MagicMock(return_value=mock_path)

        result = demethylase(action="record_access", mark_filename="test.md")
        assert "Access recorded for test.md" in result.results
        mock_record.assert_called_once_with(mock_path)

    def test_record_access_missing_filename(self):
        result = demethylase(action="record_access", mark_filename="")
        assert "record_access requires: mark_filename" in result.results


# -- unknown action -----------------------------------------------------------


class TestUnknownAction:
    """demethylase(action='<invalid>') returns error message."""

    def test_unknown_action(self):
        result = demethylase(action="foobar")
        assert "Unknown action 'foobar'" in result.results
        assert "emit" in result.results  # lists valid actions

    @patch(f"{_ORG}.read_signals")
    def test_action_case_insensitive(self, mock_read):
        """Action is lowercased and stripped."""
        mock_read.return_value = []
        result = demethylase(action="  READ  ")
        assert "No signals found." in result.results


# -- return type consistency --------------------------------------------------


class TestReturnType:
    """All branches return DemethylaseResult."""

    @patch(f"{_ORG}.emit_signal")
    def test_emit_returns_demethylase_result(self, mock_emit):
        mock_emit.return_value = MagicMock(name="sig.md")
        r = demethylase(action="emit", name="x", content="y")
        assert isinstance(r, DemethylaseResult)

    @patch(f"{_ORG}.read_signals")
    def test_read_returns_demethylase_result(self, mock_read):
        mock_read.return_value = []
        r = demethylase(action="read")
        assert isinstance(r, DemethylaseResult)

    @patch(f"{_ORG}.signal_history")
    def test_history_returns_demethylase_result(self, mock_history):
        mock_history.return_value = []
        r = demethylase(action="history")
        assert isinstance(r, DemethylaseResult)

    @patch(f"{_ORG}.transduce")
    def test_transduce_returns_demethylase_result(self, mock_transduce):
        mock_transduce.return_value = []
        r = demethylase(action="transduce")
        assert isinstance(r, DemethylaseResult)

    @patch(f"{_ORG}.resensitize")
    def test_resensitize_returns_demethylase_result(self, mock_resensitize):
        mock_resensitize.return_value = True
        r = demethylase(action="resensitize", name="x")
        assert isinstance(r, DemethylaseResult)

    @patch(f"{_ORG}.format_report")
    @patch(f"{_ORG}.sweep")
    def test_sweep_returns_demethylase_result(self, mock_sweep, mock_format):
        mock_sweep.return_value = _make_report()
        mock_format.return_value = "REPORT"
        r = demethylase(action="sweep")
        assert isinstance(r, DemethylaseResult)

    def test_unknown_returns_demethylase_result(self):
        r = demethylase(action="invalid")
        assert isinstance(r, DemethylaseResult)

    def test_validation_errors_return_demethylase_result(self):
        for kwargs in [
            dict(action="emit", name="", content=""),
            dict(action="resensitize", name=""),
            dict(action="record_access", mark_filename=""),
        ]:
            r = demethylase(**kwargs)
            assert isinstance(r, DemethylaseResult), f"Failed for {kwargs}"
