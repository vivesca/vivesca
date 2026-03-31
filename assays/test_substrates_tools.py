"""Tests for metabolon/metabolism/substrates/tools.py — PhenotypeSubstrate.

Covers sense, candidates, act, and report with mocked externals.
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

from metabolon.metabolism.fitness import Emotion
from metabolon.metabolism.substrates.tools import PhenotypeSubstrate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _emotion(
    tool: str = "alpha",
    activations: int = 5,
    success_rate: float = 0.8,
    metabolic_cost: float = 10.0,
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
    expressed_tools: list[str] | None = None,
    allele_variants: dict[str, list[int]] | None = None,
):
    """Build a PhenotypeSubstrate with mocked collector and genome."""
    collector = MagicMock()
    collector.recall_since.return_value = []

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
    """Tests for PhenotypeSubstrate.sense."""

    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_empty_returns_empty_list(self, mock_affect):
        mock_affect.return_value = {}
        s = _make_substrate(expressed_tools=[])
        assert s.sense() == []

    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_merges_emotions_and_catalogued(self, mock_affect):
        """Tools from both emotions and genome appear in output."""
        mock_affect.return_value = {
            "read_file": _emotion("read_file"),
        }
        s = _make_substrate(
            expressed_tools=["search"],
            allele_variants={"search": [0, 1]},
        )
        sensed = s.sense()
        tools = {e["tool"] for e in sensed}
        assert tools == {"read_file", "search"}

    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_overlap_deduplicates(self, mock_affect):
        """A tool in both emotions and genome appears once."""
        mock_affect.return_value = {
            "search": _emotion("search"),
        }
        s = _make_substrate(
            expressed_tools=["search"],
            allele_variants={"search": [0, 1, 2]},
        )
        sensed = s.sense()
        assert len(sensed) == 1
        assert sensed[0]["tool"] == "search"
        assert sensed[0]["in_store"] is True
        assert sensed[0]["variant_count"] == 3

    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_emotion_none_for_uncatalogued(self, mock_affect):
        """A tool with emotion but not in genome gets emotion, in_store=False."""
        mock_affect.return_value = {"grep": _emotion("grep", valence=0.9)}
        s = _make_substrate(expressed_tools=[])
        sensed = s.sense()
        assert len(sensed) == 1
        assert sensed[0]["emotion"] is not None
        assert sensed[0]["in_store"] is False
        assert sensed[0]["variant_count"] == 0

    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_emotion_none_when_missing(self, mock_affect):
        """A catalogued tool with no emotion data gets emotion=None."""
        mock_affect.return_value = {}
        s = _make_substrate(
            expressed_tools=["orphan"],
            allele_variants={"orphan": [0]},
        )
        sensed = s.sense()
        assert len(sensed) == 1
        assert sensed[0]["emotion"] is None
        assert sensed[0]["in_store"] is True
        assert sensed[0]["variant_count"] == 1

    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_sorted_output(self, mock_affect):
        """Output is sorted by tool name."""
        mock_affect.return_value = {
            "zebra": _emotion("zebra"),
            "alpha": _emotion("alpha"),
        }
        s = _make_substrate(expressed_tools=["mango"])
        sensed = s.sense()
        names = [e["tool"] for e in sensed]
        assert names == sorted(names)

    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_days_parameter_passed(self, mock_affect):
        """sense passes days arg through to compute `since` datetime."""
        mock_affect.return_value = {}
        s = _make_substrate()
        s.sense(days=7)
        # Verify recall_since was called (with some datetime)
        s.collector.recall_since.assert_called_once()
        call_arg = s.collector.recall_since.call_args[0][0]
        # Just verify it's a datetime; exact value depends on now()
        from datetime import datetime
        assert isinstance(call_arg, datetime)


# ===========================================================================
# candidates
# ===========================================================================

class TestCandidates:
    """Tests for PhenotypeSubstrate.candidates."""

    @patch("metabolon.metabolism.substrates.tools.select")
    def test_empty_sensed_returns_empty(self, mock_select):
        mock_select.return_value = []
        s = PhenotypeSubstrate()
        assert s.candidates([]) == []

    @patch("metabolon.metabolism.substrates.tools.select")
    def test_filters_to_unfit(self, mock_select):
        """Only tools returned by select() survive."""
        mock_select.return_value = ["beta"]
        sensed = [
            {"tool": "alpha", "emotion": _emotion("alpha", valence=0.9)},
            {"tool": "beta", "emotion": _emotion("beta", valence=0.1)},
        ]
        s = PhenotypeSubstrate()
        result = s.candidates(sensed)
        assert len(result) == 1
        assert result[0]["tool"] == "beta"

    @patch("metabolon.metabolism.substrates.tools.select")
    def test_none_emotions_excluded_from_scores(self, mock_select):
        """Entries with emotion=None are not passed to select()."""
        mock_select.return_value = []
        sensed = [
            {"tool": "no_data", "emotion": None},
        ]
        s = PhenotypeSubstrate()
        s.candidates(sensed)
        # select should receive an empty dict
        mock_select.assert_called_once_with({})

    @patch("metabolon.metabolism.substrates.tools.select")
    def test_returns_all_if_all_unfit(self, mock_select):
        mock_select.return_value = ["x", "y"]
        sensed = [
            {"tool": "x", "emotion": _emotion("x")},
            {"tool": "y", "emotion": _emotion("y")},
        ]
        s = PhenotypeSubstrate()
        result = s.candidates(sensed)
        assert len(result) == 2

    @patch("metabolon.metabolism.substrates.tools.select")
    def test_returns_empty_if_none_unfit(self, mock_select):
        mock_select.return_value = []
        sensed = [
            {"tool": "x", "emotion": _emotion("x", valence=0.9)},
        ]
        s = PhenotypeSubstrate()
        assert s.candidates(sensed) == []


# ===========================================================================
# act
# ===========================================================================

class TestAct:
    """Tests for PhenotypeSubstrate.act."""

    def test_skip_not_in_store(self):
        s = PhenotypeSubstrate()
        result = s.act({"tool": "ghost", "emotion": None, "in_store": False})
        assert result == "skip: ghost not in genome"

    def test_mutation_no_emotion(self):
        s = PhenotypeSubstrate()
        result = s.act({"tool": "alpha", "emotion": None, "in_store": True})
        assert result == "mutation needed for alpha: no emotion data"

    def test_mutation_none_valence(self):
        s = PhenotypeSubstrate()
        em = _emotion("alpha", activations=2, valence=None)
        result = s.act({"tool": "alpha", "emotion": em, "in_store": True})
        assert "insufficient stimuli" in result
        assert "2 invocations" in result

    def test_mutation_with_valence(self):
        s = PhenotypeSubstrate()
        em = _emotion("alpha", valence=0.123)
        result = s.act({"tool": "alpha", "emotion": em, "in_store": True})
        assert result == "mutation needed for alpha: valence 0.123"


# ===========================================================================
# report
# ===========================================================================

class TestReport:
    """Tests for PhenotypeSubstrate.report."""

    def test_empty(self):
        s = PhenotypeSubstrate()
        rpt = s.report([], [])
        assert "0 tool(s) sensed" in rpt

    def test_shows_tool_with_emotion(self):
        s = PhenotypeSubstrate()
        em = _emotion("search", valence=0.75, success_rate=0.9, activations=12)
        sensed = [{"tool": "search", "emotion": em, "variant_count": 2, "in_store": True}]
        rpt = s.report(sensed, [])
        assert "search" in rpt
        assert "valence=0.750" in rpt
        assert "invocations=12" in rpt
        assert "success_rate=90.0%" in rpt

    def test_shows_valence_na(self):
        s = PhenotypeSubstrate()
        em = _emotion("grep", valence=None, activations=1)
        sensed = [{"tool": "grep", "emotion": em, "variant_count": 0, "in_store": True}]
        rpt = s.report(sensed, [])
        assert "valence=N/A" in rpt

    def test_shows_no_signals(self):
        s = PhenotypeSubstrate()
        sensed = [{"tool": "orphan", "emotion": None, "variant_count": 1, "in_store": True}]
        rpt = s.report(sensed, [])
        assert "no signals" in rpt

    def test_actions_section(self):
        s = PhenotypeSubstrate()
        acted = ["mutation needed for x: valence 0.100"]
        rpt = s.report([], acted)
        assert "-- Actions --" in rpt
        assert "mutation needed for x" in rpt

    def test_no_actions_section_when_empty(self):
        s = PhenotypeSubstrate()
        rpt = s.report([], [])
        assert "-- Actions --" not in rpt

    def test_multiple_tools(self):
        s = PhenotypeSubstrate()
        sensed = [
            {"tool": "alpha", "emotion": _emotion("alpha", valence=0.5), "variant_count": 1, "in_store": True},
            {"tool": "beta", "emotion": None, "variant_count": 0, "in_store": False},
        ]
        rpt = s.report(sensed, [])
        assert "2 tool(s) sensed" in rpt
        assert "alpha" in rpt
        assert "beta" in rpt
