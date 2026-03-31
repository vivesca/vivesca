"""Tests for metabolon.metabolism.substrates.tools.PhenotypeSubstrate."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from metabolon.metabolism.fitness import Emotion
from metabolon.metabolism.substrates.tools import PhenotypeSubstrate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _emotion(
    tool: str = "t1",
    activations: int = 5,
    success_rate: float = 0.8,
    metabolic_cost: float = 1.0,
    valence: float | None = 0.5,
) -> Emotion:
    return Emotion(
        tool=tool,
        activations=activations,
        success_rate=success_rate,
        metabolic_cost=metabolic_cost,
        valence=valence,
    )


def _make_substrate(
    recall_since_return=None,
    expressed_tools_return=None,
    allele_variants_return=None,
) -> PhenotypeSubstrate:
    """Build a PhenotypeSubstrate with mocked collector and genome."""
    collector = MagicMock()
    collector.recall_since.return_value = recall_since_return or []

    genome = MagicMock()
    genome.expressed_tools.return_value = expressed_tools_return or []
    if allele_variants_return is not None:
        genome.allele_variants.return_value = allele_variants_return
    else:
        genome.allele_variants.return_value = []

    return PhenotypeSubstrate(collector=collector, genome=genome)


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------

class TestInit:
    def test_default_name(self):
        sub = _make_substrate()
        assert sub.name == "tools"

    def test_creates_defaults_when_none(self):
        with patch(
            "metabolon.metabolism.substrates.tools.SensorySystem"
        ) as MockCollector, patch(
            "metabolon.metabolism.substrates.tools.Genome"
        ) as MockGenome:
            sub = PhenotypeSubstrate()
            MockCollector.assert_called_once()
            MockGenome.assert_called_once()
            assert sub.collector is MockCollector.return_value
            assert sub.genome is MockGenome.return_value

    def test_uses_provided_deps(self):
        collector = MagicMock()
        genome = MagicMock()
        sub = PhenotypeSubstrate(collector=collector, genome=genome)
        assert sub.collector is collector
        assert sub.genome is genome


# ---------------------------------------------------------------------------
# sense
# ---------------------------------------------------------------------------

class TestSense:
    @patch("metabolon.metabolism.substrates.tools.sense_affect", return_value={})
    def test_empty_signals(self, mock_sense):
        sub = _make_substrate(recall_since_return=[], expressed_tools_return=[])
        result = sub.sense(days=30)
        assert result == []
        # Verify the collector was called with a datetime ~30 days ago
        args, _ = sub.collector.recall_since.call_args
        since = args[0]
        assert isinstance(since, datetime)
        assert since <= datetime.now(UTC)

    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_merges_emotions_and_catalogued(self, mock_sense):
        """Tools from emotions AND genome should appear, deduplicated."""
        mock_sense.return_value = {
            "tool_a": _emotion("tool_a"),
        }
        sub = _make_substrate(
            recall_since_return=[MagicMock()],
            expressed_tools_return=["tool_b"],
            allele_variants_return=[1, 2],
        )
        result = sub.sense(days=7)
        tools = [r["tool"] for r in result]
        assert "tool_a" in tools
        assert "tool_b" in tools

    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_sense_entry_fields(self, mock_sense):
        e = _emotion("tool_a", activations=10, success_rate=0.9, valence=0.33)
        mock_sense.return_value = {"tool_a": e}
        sub = _make_substrate(
            expressed_tools_return=["tool_a"],
            allele_variants_return=[1, 2, 3],
        )
        result = sub.sense()
        assert len(result) == 1
        entry = result[0]
        assert entry["tool"] == "tool_a"
        assert entry["emotion"] is e
        assert entry["variant_count"] == 3
        assert entry["in_store"] is True

    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_tool_not_in_store(self, mock_sense):
        """A tool appearing only in emotions, not genome, has in_store=False."""
        mock_sense.return_value = {"orphan": _emotion("orphan")}
        sub = _make_substrate(expressed_tools_return=[])
        result = sub.sense()
        assert len(result) == 1
        assert result[0]["in_store"] is False
        assert result[0]["variant_count"] == 0


# ---------------------------------------------------------------------------
# candidates
# ---------------------------------------------------------------------------

class TestCandidates:
    @patch("metabolon.metabolism.substrates.tools.select", return_value=[])
    def test_no_candidates(self, mock_select):
        sub = _make_substrate()
        sensed = [{"tool": "t1", "emotion": _emotion("t1", valence=0.9)}]
        result = sub.candidates(sensed)
        assert result == []

    @patch("metabolon.metabolism.substrates.tools.select")
    def test_selects_unfit(self, mock_select):
        mock_select.return_value = ["bad_tool"]
        sub = _make_substrate()
        sensed = [
            {"tool": "good_tool", "emotion": _emotion("good_tool", valence=0.9)},
            {"tool": "bad_tool", "emotion": _emotion("bad_tool", valence=-0.2)},
        ]
        result = sub.candidates(sensed)
        assert len(result) == 1
        assert result[0]["tool"] == "bad_tool"

    def test_skips_none_emotions(self):
        """Entries with emotion=None should be passed over when building scores."""
        sub = _make_substrate()
        sensed = [
            {"tool": "no_data", "emotion": None},
        ]
        with patch("metabolon.metabolism.substrates.tools.select") as mock_sel:
            mock_sel.return_value = []
            sub.candidates(sensed)
            # select should be called with empty dict since emotion is None
            mock_sel.assert_called_once_with({})


# ---------------------------------------------------------------------------
# act
# ---------------------------------------------------------------------------

class TestAct:
    def test_skip_not_in_store(self):
        sub = _make_substrate()
        candidate = {"tool": "ghost", "emotion": None, "in_store": False}
        result = sub.act(candidate)
        assert result == "skip: ghost not in genome"

    def test_no_emotion_data(self):
        sub = _make_substrate()
        candidate = {"tool": "t1", "emotion": None, "in_store": True}
        result = sub.act(candidate)
        assert result == "mutation needed for t1: no emotion data"

    def test_none_valence(self):
        sub = _make_substrate()
        e = _emotion("t1", activations=2, valence=None)
        candidate = {"tool": "t1", "emotion": e, "in_store": True}
        result = sub.act(candidate)
        assert result == "mutation needed for t1: insufficient stimuli (2 invocations)"

    def test_low_valence(self):
        sub = _make_substrate()
        e = _emotion("t1", valence=0.123)
        candidate = {"tool": "t1", "emotion": e, "in_store": True}
        result = sub.act(candidate)
        assert result == "mutation needed for t1: valence 0.123"


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

class TestReport:
    def test_empty_sensed(self):
        sub = _make_substrate()
        report = sub.report([], [])
        assert "0 tool(s) sensed" in report

    def test_report_with_emotion(self):
        sub = _make_substrate()
        e = _emotion("mytool", activations=7, success_rate=0.857, valence=0.42)
        sensed = [{"tool": "mytool", "emotion": e, "variant_count": 2}]
        report = sub.report(sensed, [])
        assert "mytool" in report
        assert "valence=0.420" in report
        assert "success_rate=85.7%" in report
        assert "invocations=7" in report

    def test_report_no_signals(self):
        sub = _make_substrate()
        sensed = [{"tool": "quiet", "emotion": None, "variant_count": 0}]
        report = sub.report(sensed, [])
        assert "quiet: no signals" in report

    def test_report_none_valence_shows_na(self):
        sub = _make_substrate()
        e = _emotion("t1", valence=None)
        sensed = [{"tool": "t1", "emotion": e, "variant_count": 1}]
        report = sub.report(sensed, [])
        assert "valence=N/A" in report

    def test_report_with_actions(self):
        sub = _make_substrate()
        acted = ["mutation needed for t1: valence 0.100"]
        report = sub.report([], acted)
        assert "-- Actions --" in report
        assert "mutation needed for t1" in report

    def test_report_no_actions_section_when_empty(self):
        sub = _make_substrate()
        report = sub.report([], [])
        assert "-- Actions --" not in report
