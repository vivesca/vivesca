from __future__ import annotations

"""Tests for demethylase enzyme — signal + mark management tools."""


from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.demethylase import demethylase


# ---------------------------------------------------------------------------
# TestDemethylase
# ---------------------------------------------------------------------------


class TestDemethylase:
    """Tests for the demethylase enzyme top-level dispatch."""

    # -- unknown action -----------------------------------------------------

    def test_unknown_action_returns_error(self) -> None:
        result = demethylase(action="invalid")
        assert "Unknown action 'invalid'" in result.results
        assert "emit, read, history, transduce, resensitize, sweep, record_access" in result.results

    def test_action_is_case_insensitive(self) -> None:
        result = demethylase(action="EMIT")
        # Should not say "Unknown action" — it parsed "emit" but lacked params
        assert "Unknown action" not in result.results

    # -- emit ---------------------------------------------------------------

    def test_emit_missing_params_returns_error(self) -> None:
        result = demethylase(action="emit")
        assert "emit requires: name, content" in result.results
        result = demethylase(action="emit", name="test")
        assert "emit requires: name, content" in result.results

    @patch("metabolon.organelles.demethylase.emit_signal")
    def test_emit_success(self, mock_emit: MagicMock) -> None:
        mock_emit.return_value = Path("/tmp/test-signal.json")
        result = demethylase(action="emit", name="test", content="hello", source="src")
        assert "Signal emitted: test-signal.json" in result.results

    @patch("metabolon.organelles.demethylase.emit_signal")
    def test_emit_with_downstream(self, mock_emit: MagicMock) -> None:
        mock_emit.return_value = Path("/tmp/cmd-signal.json")
        result = demethylase(
            action="emit",
            name="cmd",
            content="data",
            downstream=["shell:echo hi", "python:print"],
        )
        assert "Signal emitted: cmd-signal.json" in result.results
        assert "2 downstream commands" in result.results

    @patch("metabolon.organelles.demethylase.emit_signal")
    def test_emit_no_downstream_note(self, mock_emit: MagicMock) -> None:
        mock_emit.return_value = Path("/tmp/solo.json")
        result = demethylase(action="emit", name="solo", content="x")
        assert "downstream" not in result.results

    # -- read ---------------------------------------------------------------

    @patch("metabolon.organelles.demethylase.read_signals")
    def test_read_no_signals(self, mock_read: MagicMock) -> None:
        mock_read.return_value = []
        result = demethylase(action="read")
        assert "No signals found." in result.results

    @patch("metabolon.organelles.demethylase.read_signals")
    def test_read_with_signals(self, mock_read: MagicMock) -> None:
        mock_read.return_value = [
            {
                "name": "test-signal",
                "source": "test",
                "age_days": 1,
                "content": "hello world",
                "downstream": ["cmd1", "cmd2"],
                "cascades_fired": ["cmd1"],
            }
        ]
        result = demethylase(action="read")
        assert "1 signal(s) pending:" in result.results
        assert "Signal: test-signal" in result.results
        assert "Source: test" in result.results
        assert "Age: 1 days" in result.results
        assert "Content: hello world" in result.results
        assert "Downstream: cmd1, cmd2" in result.results
        assert "Cascades fired: cmd1" in result.results

    @patch("metabolon.organelles.demethylase.read_signals")
    def test_read_signal_without_optional_fields(self, mock_read: MagicMock) -> None:
        mock_read.return_value = [
            {
                "name": "minimal",
                "source": "bot",
                "age_days": 0,
                "content": "hi",
            }
        ]
        result = demethylase(action="read")
        assert "Signal: minimal" in result.results
        assert "Downstream" not in result.results
        assert "Cascades fired" not in result.results

    # -- history ------------------------------------------------------------

    @patch("metabolon.organelles.demethylase.signal_history")
    def test_history_no_signals(self, mock_history: MagicMock) -> None:
        mock_history.return_value = []
        result = demethylase(action="history")
        assert "No signal history found." in result.results

    @patch("metabolon.organelles.demethylase.signal_history")
    def test_history_with_signals(self, mock_history: MagicMock) -> None:
        mock_history.return_value = [
            {
                "timestamp": "2026-04-01T00:00:00Z",
                "name": "test-signal",
                "source": "test",
                "fire_count": 3,
                "deduplicated": 1,
                "content": "hello history",
            }
        ]
        result = demethylase(action="history")
        assert "1 signal(s) in history:" in result.results
        assert "test-signal" in result.results
        assert "Source: test" in result.results
        assert "Fire count: 3" in result.results
        assert "Deduplicated: 1" in result.results
        assert "Content: hello history" in result.results

    # -- transduce ----------------------------------------------------------

    @patch("metabolon.organelles.demethylase.transduce")
    def test_transduce_no_results(self, mock_transduce: MagicMock) -> None:
        mock_transduce.return_value = []
        result = demethylase(action="transduce")
        assert "No signals transduced." in result.results

    @patch("metabolon.organelles.demethylase.transduce")
    def test_transduce_with_results(self, mock_transduce: MagicMock) -> None:
        mock_transduce.return_value = [
            {"name": "test-signal", "source": "test", "cascades_fired": ["cmd1"]},
        ]
        result = demethylase(action="transduce")
        assert "1 signal(s) transduced:" in result.results
        assert "Signal: test-signal" in result.results
        assert "Cascades fired: cmd1" in result.results

    @patch("metabolon.organelles.demethylase.transduce")
    def test_transduce_without_cascades(self, mock_transduce: MagicMock) -> None:
        mock_transduce.return_value = [
            {"name": "bare", "source": "bot"},
        ]
        result = demethylase(action="transduce")
        assert "Signal: bare" in result.results
        assert "Cascades fired" not in result.results

    # -- resensitize --------------------------------------------------------

    def test_resensitize_missing_name(self) -> None:
        result = demethylase(action="resensitize")
        assert "resensitize requires: name" in result.results

    @patch("metabolon.organelles.demethylase.resensitize")
    def test_resensitize_found(self, mock_resensitize: MagicMock) -> None:
        mock_resensitize.return_value = True
        result = demethylase(action="resensitize", name="test-signal")
        assert "resensitized — receptor recycled to surface" in result.results

    @patch("metabolon.organelles.demethylase.resensitize")
    def test_resensitize_not_found(self, mock_resensitize: MagicMock) -> None:
        mock_resensitize.return_value = False
        result = demethylase(action="resensitize", name="nonexistent")
        assert "No desensitized signal found with name 'nonexistent'" in result.results

    # -- sweep --------------------------------------------------------------

    @patch("metabolon.organelles.demethylase.format_report")
    @patch("metabolon.organelles.demethylase.sweep")
    def test_sweep_minimal(self, mock_sweep: MagicMock, mock_format: MagicMock) -> None:
        mock_report = MagicMock()
        mock_report.total_marks = 10
        mock_report.methyl_marks = 5
        mock_report.acetyl_marks = 3
        mock_report.protected_marks = 2
        mock_report.stale_candidates = []
        mock_report.source_distribution = {}
        mock_report.type_distribution = {}
        mock_report.mark_clusters = []
        mock_sweep.return_value = mock_report
        mock_format.return_value = "Sweep report body"

        result = demethylase(action="sweep")
        assert "Marks: 10 total (5 methyl, 3 acetyl, 2 protected). Stale: 0." in result.results
        assert "Sweep report body" in result.results

    @patch("metabolon.organelles.demethylase.format_report")
    @patch("metabolon.organelles.demethylase.sweep")
    def test_sweep_with_stale_and_distributions(
        self, mock_sweep: MagicMock, mock_format: MagicMock
    ) -> None:
        stale1 = MagicMock()
        stale1.path = Path("/tmp/old_mark.md")
        stale2 = MagicMock()
        stale2.path = Path("/tmp/another_mark.md")

        mock_report = MagicMock()
        mock_report.total_marks = 50
        mock_report.methyl_marks = 25
        mock_report.acetyl_marks = 20
        mock_report.protected_marks = 5
        mock_report.stale_candidates = [stale1, stale2]
        mock_report.source_distribution = {"golem": 10, "manual": 3}
        mock_report.type_distribution = {"methyl": 25}
        mock_report.mark_clusters = list(range(15))  # 15 clusters
        mock_sweep.return_value = mock_report
        mock_format.return_value = "report"

        result = demethylase(action="sweep")
        assert "Stale: 2." in result.results
        assert "Stale marks: old_mark.md, another_mark.md" in result.results
        assert "Source distribution: golem=10, manual=3" in result.results
        assert "Type distribution: methyl=25" in result.results
        assert "Top clusters: 10 shown of 15." in result.results

    # -- record_access ------------------------------------------------------

    def test_record_access_missing_filename(self) -> None:
        result = demethylase(action="record_access")
        assert "record_access requires: mark_filename" in result.results

    @patch("metabolon.organelles.demethylase.record_access")
    @patch("metabolon.locus.marks", Path("/tmp/nonexistent_marks_dir"))
    def test_record_access_mark_not_found(self, mock_record: MagicMock) -> None:
        result = demethylase(action="record_access", mark_filename="nonexistent.mark")
        assert "Mark not found: nonexistent.mark" in result.results
        mock_record.assert_not_called()

    @patch("metabolon.organelles.demethylase.record_access")
    def test_record_access_success(self, mock_record: MagicMock, tmp_path: Path) -> None:
        mark_file = tmp_path / "test.mark"
        mark_file.write_text("mark content")

        with patch("metabolon.locus.marks", tmp_path):
            result = demethylase(action="record_access", mark_filename="test.mark")

        assert "Access recorded for test.mark" in result.results
        mock_record.assert_called_once()
        called_path = mock_record.call_args[0][0]
        assert called_path == mark_file
