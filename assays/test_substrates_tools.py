from __future__ import annotations
"""Tests for metabolon.metabolism.substrates.tools.PhenotypeSubstrate."""


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
    metabolic_cost: float = 10.0,
    valence: float | None = 0.4,
) -> Emotion:
    return Emotion(
        tool=tool,
        activations=activations,
        success_rate=success_rate,
        metabolic_cost=metabolic_cost,
        valence=valence,
    )


def _make_substrate(
    recall_return: list | None = None,
    expressed_tools: list[str] | None = None,
    allele_variants: dict[str, list[int]] | None = None,
) -> PhenotypeSubstrate:
    """Build a PhenotypeSubstrate with mocked collector and genome."""
    collector = MagicMock()
    collector.recall_since.return_value = recall_return or []

    genome = MagicMock()
    genome.expressed_tools.return_value = expressed_tools or []
    if allele_variants:
        genome.allele_variants.side_effect = lambda t: allele_variants.get(t, [])
    else:
        genome.allele_variants.return_value = []

    return PhenotypeSubstrate(collector=collector, genome=genome)


# ===========================================================================
# sense
# ===========================================================================

class TestSense:
    """Tests for PhenotypeSubstrate.sense()."""

    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_empty_signals_and_no_genome(self, mock_sense):
        """No signals and no genome → empty list."""
        mock_sense.return_value = {}
        sub = _make_substrate(recall_return=[], expressed_tools=[])
        result = sub.sense(days=30)
        assert result == []

    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_signals_only(self, mock_sense):
        """Signals exist but no genome entries → sensed with in_store=False."""
        mock_sense.return_value = {"tool_a": _emotion("tool_a")}
        sub = _make_substrate(recall_return=["stub"], expressed_tools=[])
        result = sub.sense(days=30)

        assert len(result) == 1
        entry = result[0]
        assert entry["tool"] == "tool_a"
        assert entry["emotion"] is not None
        assert entry["in_store"] is False
        assert entry["variant_count"] == 0

    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_genome_only(self, mock_sense):
        """No signals but tools in genome → sensed with no emotion."""
        mock_sense.return_value = {}
        sub = _make_substrate(
            recall_return=[],
            expressed_tools=["tool_b"],
            allele_variants={"tool_b": [0, 1]},
        )
        result = sub.sense(days=30)

        assert len(result) == 1
        entry = result[0]
        assert entry["tool"] == "tool_b"
        assert entry["emotion"] is None
        assert entry["in_store"] is True
        assert entry["variant_count"] == 2

    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_mixed_sources_dedup_sorted(self, mock_sense):
        """Signals + genome merge into sorted deduplicated list."""
        mock_sense.return_value = {
            "alpha": _emotion("alpha"),
            "gamma": _emotion("gamma"),
        }
        sub = _make_substrate(
            recall_return=["stub"],
            expressed_tools=["beta", "gamma"],
            allele_variants={"beta": [0], "gamma": [0, 1, 2]},
        )
        result = sub.sense(days=30)

        tools = [r["tool"] for r in result]
        assert tools == ["alpha", "beta", "gamma"]

        # alpha: has emotion, not in genome
        alpha = result[0]
        assert alpha["in_store"] is False
        assert alpha["variant_count"] == 0

        # beta: no emotion, in genome
        beta = result[1]
        assert beta["emotion"] is None
        assert beta["in_store"] is True
        assert beta["variant_count"] == 1

        # gamma: both emotion and genome
        gamma = result[2]
        assert gamma["emotion"] is not None
        assert gamma["in_store"] is True
        assert gamma["variant_count"] == 3

    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_sense_passes_since_to_collector(self, mock_sense):
        """sense() computes `since` from days and passes it to recall_since."""
        mock_sense.return_value = {}
        sub = _make_substrate()
        sub.sense(days=7)

        call_args = sub.collector.recall_since.call_args
        since = call_args[0][0]
        expected_since = datetime.now(UTC) - timedelta(days=7)
        # Allow up to 5 seconds of clock drift
        assert abs((since - expected_since).total_seconds()) < 5


# ===========================================================================
# candidates
# ===========================================================================

class TestCandidates:
    """Tests for PhenotypeSubstrate.candidates()."""

    @patch("metabolon.metabolism.substrates.tools.select")
    def test_empty_sensed(self, mock_select):
        """Empty input returns empty output."""
        mock_select.return_value = []
        sub = _make_substrate()
        assert sub.candidates([]) == []

    @patch("metabolon.metabolism.substrates.tools.select")
    def test_filters_to_unfit(self, mock_select):
        """Only tools returned by select() survive."""
        mock_select.return_value = ["b"]
        sensed = [
            {"tool": "a", "emotion": _emotion("a", valence=0.9)},
            {"tool": "b", "emotion": _emotion("b", valence=0.1)},
            {"tool": "c", "emotion": _emotion("c", valence=0.8)},
        ]
        result = sub.candidates(sensed) if (sub := _make_substrate()) else []
        assert len(result) == 1
        assert result[0]["tool"] == "b"

    @patch("metabolon.metabolism.substrates.tools.select")
    def test_skips_none_emotions(self, mock_select):
        """Entries with emotion=None are not passed to select()."""
        mock_select.return_value = []
        sensed = [
            {"tool": "x", "emotion": None},
        ]
        sub = _make_substrate()
        sub.candidates(sensed)

        # select() should receive empty dict because emotion is None
        mock_select.assert_called_once_with({})


# ===========================================================================
# act
# ===========================================================================

class TestAct:
    """Tests for PhenotypeSubstrate.act()."""

    def test_skip_not_in_store(self):
        """Tool not in genome → skip message."""
        sub = _make_substrate()
        result = sub.act({"tool": "absent", "emotion": None, "in_store": False})
        assert "skip" in result
        assert "absent" in result

    def test_no_emotion_data(self):
        """No emotion → mutation needed, no emotion data."""
        sub = _make_substrate()
        result = sub.act({"tool": "t", "emotion": None, "in_store": True})
        assert "mutation needed" in result
        assert "no emotion data" in result

    def test_none_valence(self):
        """Emotion with None valence → mutation needed, insufficient stimuli."""
        sub = _make_substrate()
        emo = _emotion(valence=None, activations=2)
        result = sub.act({"tool": "t", "emotion": emo, "in_store": True})
        assert "mutation needed" in result
        assert "insufficient stimuli" in result
        assert "2 invocations" in result

    def test_low_valence(self):
        """Low valence → mutation needed, valence shown."""
        sub = _make_substrate()
        emo = _emotion(valence=0.123)
        result = sub.act({"tool": "t", "emotion": emo, "in_store": True})
        assert "mutation needed" in result
        assert "0.123" in result


# ===========================================================================
# report
# ===========================================================================

class TestReport:
    """Tests for PhenotypeSubstrate.report()."""

    def test_empty(self):
        """Empty sensed + no actions → header only."""
        sub = _make_substrate()
        rpt = sub.report([], [])
        assert "0 tool(s) sensed" in rpt

    def test_with_emotion(self):
        """Entry with emotion shows valence, invocations, success_rate."""
        sub = _make_substrate()
        emo = _emotion(valence=0.556, activations=10, success_rate=0.75)
        sensed = [{"tool": "mytool", "emotion": emo, "variant_count": 3}]
        rpt = sub.report(sensed, [])
        assert "mytool" in rpt
        assert "0.556" in rpt
        assert "invocations=10" in rpt
        assert "75.0%" in rpt
        assert "variants=3" in rpt

    def test_with_none_emotion(self):
        """Entry with None emotion shows 'no signals'."""
        sub = _make_substrate()
        sensed = [{"tool": "ghost", "emotion": None, "variant_count": 0}]
        rpt = sub.report(sensed, [])
        assert "ghost" in rpt
        assert "no signals" in rpt

    def test_none_valence_shows_na(self):
        """Emotion with None valence shows 'N/A' for valence."""
        sub = _make_substrate()
        emo = _emotion(valence=None, activations=1)
        sensed = [{"tool": "partial", "emotion": emo, "variant_count": 0}]
        rpt = sub.report(sensed, [])
        assert "N/A" in rpt

    def test_actions_section(self):
        """Acted strings appear under '-- Actions --'."""
        sub = _make_substrate()
        rpt = sub.report([], ["mutation needed for t: valence 0.100"])
        assert "-- Actions --" in rpt
        assert "mutation needed for t" in rpt

    def test_no_actions_section_when_empty(self):
        """No '-- Actions --' section when acted is empty."""
        sub = _make_substrate()
        rpt = sub.report([{"tool": "a", "emotion": None, "variant_count": 0}], [])
        assert "-- Actions --" not in rpt
