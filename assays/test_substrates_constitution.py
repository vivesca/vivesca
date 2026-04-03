"""Tests for metabolon.metabolism.substrates.constitution."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.metabolism.signals import SensorySystem, Stimulus
from metabolon.metabolism.substrates.constitution import ExecutiveSubstrate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_stimulus(tool: str, days_ago: int = 0) -> Stimulus:
    return Stimulus(
        tool=tool,
        outcome="success",
        ts=datetime.now(UTC) - timedelta(days=days_ago),
    )


def _sample_constitution(tmp_path: Path) -> Path:
    genome = tmp_path / "genome.md"
    genome.write_text(
        "**Use biological names.** Enzymes and organelles must use precise terms.\n"
        "**Keep modules small.** Each organelle should do one thing.\n"
        "**No bare except.** Always specify exception types.\n"
    )
    return genome


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExecutiveSubstrateInit:
    def test_default_constitution_path(self):
        sub = ExecutiveSubstrate()
        expected = Path.home() / ".local" / "share" / "vivesca" / "genome.md"
        assert sub.constitution_path == expected

    def test_custom_constitution_path(self, tmp_path: Path):
        custom = tmp_path / "custom.md"
        sub = ExecutiveSubstrate(constitution_path=custom)
        assert sub.constitution_path == custom

    def test_name_attribute(self):
        assert ExecutiveSubstrate.name == "constitution"


class TestSense:
    def test_sense_no_file_returns_empty(self, tmp_path: Path):
        sub = ExecutiveSubstrate(
            constitution_path=tmp_path / "nonexistent.md",
            collector=MagicMock(spec=SensorySystem),
        )
        assert sub.sense() == []

    def test_sense_extracts_bold_rules(self, tmp_path: Path):
        genome = _sample_constitution(tmp_path)
        mock_collector = MagicMock(spec=SensorySystem)
        mock_collector.recall_since.return_value = []
        sub = ExecutiveSubstrate(
            constitution_path=genome, collector=mock_collector,
        )
        rules = sub.sense()
        assert len(rules) >= 3
        titles = [r["title"] for r in rules]
        assert "Use biological names" in titles
        assert "Keep modules small" in titles
        assert "No bare except" in titles

    def test_sense_cross_references_signals(self, tmp_path: Path):
        genome = _sample_constitution(tmp_path)
        mock_collector = MagicMock(spec=SensorySystem)
        mock_collector.recall_since.return_value = [
            _make_stimulus("biological_scanner"),
            _make_stimulus("naming_check"),
        ]
        sub = ExecutiveSubstrate(
            constitution_path=genome, collector=mock_collector,
        )
        rules = sub.sense()
        bio_rule = next(r for r in rules if r["title"] == "Use biological names")
        assert bio_rule["has_evidence"] is True
        assert "biological" in bio_rule["activated_enzymes"]

    def test_sense_unevidenced_rules_marked(self, tmp_path: Path):
        genome = _sample_constitution(tmp_path)
        mock_collector = MagicMock(spec=SensorySystem)
        mock_collector.recall_since.return_value = [
            _make_stimulus("totally_unrelated_tool"),
        ]
        sub = ExecutiveSubstrate(
            constitution_path=genome, collector=mock_collector,
        )
        rules = sub.sense()
        for r in rules:
            if "precision_gap" not in r:
                assert r["has_evidence"] is False
                assert len(r["activated_enzymes"]) == 0

    @patch("metabolon.metabolism.substrates.constitution.precision_scan")
    def test_sense_includes_precision_gaps(self, mock_scan, tmp_path: Path):
        genome = _sample_constitution(tmp_path)
        mock_collector = MagicMock(spec=SensorySystem)
        mock_collector.recall_since.return_value = []
        gap = MagicMock()
        gap.closed = False
        gap.kind = "vocabulary"
        gap.description = "old_term to new_term: reason"
        gap.references = ["file_a.py", "file_b.py"]
        mock_scan.return_value = [gap]
        sub = ExecutiveSubstrate(
            constitution_path=genome, collector=mock_collector,
        )
        rules = sub.sense()
        gap_rules = [r for r in rules if r.get("precision_gap")]
        assert len(gap_rules) == 1
        assert "Precision gap" in gap_rules[0]["title"]
        assert gap_rules[0]["references"] == ["file_a.py", "file_b.py"]

    @patch("metabolon.metabolism.substrates.constitution.precision_scan")
    def test_sense_ignores_closed_precision_gaps(self, mock_scan, tmp_path: Path):
        genome = _sample_constitution(tmp_path)
        mock_collector = MagicMock(spec=SensorySystem)
        mock_collector.recall_since.return_value = []
        gap = MagicMock()
        gap.closed = True
        mock_scan.return_value = [gap]
        sub = ExecutiveSubstrate(
            constitution_path=genome, collector=mock_collector,
        )
        rules = sub.sense()
        gap_rules = [r for r in rules if r.get("precision_gap")]
        assert len(gap_rules) == 0


class TestCandidates:
    def test_candidates_filters_unevidenced(self):
        sub = ExecutiveSubstrate()
        sensed = [
            {"title": "A", "has_evidence": True},
            {"title": "B", "has_evidence": False},
            {"title": "C", "has_evidence": False, "precision_gap": True},
        ]
        cands = sub.candidates(sensed)
        assert len(cands) == 2
        assert all(not c.get("has_evidence", False) for c in cands)

    def test_candidates_all_evidenced_returns_empty(self):
        sub = ExecutiveSubstrate()
        sensed = [
            {"title": "A", "has_evidence": True},
            {"title": "B", "has_evidence": True},
        ]
        assert sub.candidates(sensed) == []


class TestAct:
    def test_act_prune_candidate(self):
        sub = ExecutiveSubstrate()
        result = sub.act({"title": "Old rule", "has_evidence": False})
        assert result == "prune candidate: Old rule"

    def test_act_precision_gap(self):
        sub = ExecutiveSubstrate()
        candidate = {
            "title": "Precision gap (vocab): foo",
            "precision_gap": True,
            "references": ["a.py", "b.py", "c.py"],
        }
        result = sub.act(candidate)
        assert result.startswith("rename:")
        assert "3 reference(s)" in result


class TestReport:
    def test_report_format(self):
        sub = ExecutiveSubstrate()
        sensed = [
            {
                "title": "Rule A",
                "has_evidence": True,
                "activated_enzymes": {"enzyme_x"},
            },
            {"title": "Rule B", "has_evidence": False, "activated_enzymes": set()},
        ]
        acted = ["prune candidate: Rule B"]
        report = sub.report(sensed, acted)
        assert "Executive substrate: 2 rule(s) sensed" in report
        assert "Rule A" in report
        assert "Rule B" in report
        assert "1 evidenced, 1 without evidence." in report
        assert "prune candidate: Rule B" in report

    def test_report_empty_sensed(self):
        sub = ExecutiveSubstrate()
        report = sub.report([], [])
        assert "0 rule(s) sensed" in report
        assert "(none)" in report
        assert "0 evidenced, 0 without evidence." in report
