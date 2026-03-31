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
    tool: str,
    activations: int = 5,
    success_rate: float = 0.8,
    metabolic_cost: float = 1.0,
    valence: float | None = 0.6,
) -> Emotion:
    return Emotion(
        tool=tool,
        activations=activations,
        success_rate=success_rate,
        metabolic_cost=metabolic_cost,
        valence=valence,
    )


def _mock_collector(signals=None):
    """Return a mock SensorySystem with configurable recall_since."""
    collector = MagicMock()
    collector.recall_since.return_value = signals or []
    return collector


def _mock_genome(tools=None, variants=None):
    """Return a mock Genome.

    tools: list of expressed tool names
    variants: dict mapping tool name -> list[int] of variant ids
    """
    genome = MagicMock()
    genome.expressed_tools.return_value = tools or []
    default_variants = variants or {}
    genome.allele_variants.side_effect = lambda t: default_variants.get(t, [])
    return genome


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------

class TestInit:
    def test_default_construction(self):
        sub = PhenotypeSubstrate()
        assert sub.name == "tools"
        assert sub.collector is not None
        assert sub.genome is not None

    def test_custom_deps(self):
        col = _mock_collector()
        gen = _mock_genome()
        sub = PhenotypeSubstrate(collector=col, genome=gen)
        assert sub.collector is col
        assert sub.genome is gen


# ---------------------------------------------------------------------------
# sense
# ---------------------------------------------------------------------------

class TestSense:
    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_basic_sense(self, mock_sense):
        emotions = {
            "tool_a": _emotion("tool_a", valence=0.9),
            "tool_b": _emotion("tool_b", valence=0.3),
        }
        mock_sense.return_value = emotions
        col = _mock_collector(signals=["s1", "s2"])
        gen = _mock_genome(tools=["tool_a"], variants={"tool_a": [1, 2]})

        sub = PhenotypeSubstrate(collector=col, genome=gen)
        result = sub.sense(days=30)

        # recall_since called with a datetime roughly 30 days ago
        col.recall_since.assert_called_once()
        called_since = col.recall_since.call_args[0][0]
        assert isinstance(called_since, datetime)
        assert (datetime.now(UTC) - called_since).days <= 31

        mock_sense.assert_called_once_with(["s1", "s2"])

        # Both tools should appear (union of emotion keys + catalogued)
        tools_in_result = {r["tool"] for r in result}
        assert tools_in_result == {"tool_a", "tool_b"}

        # tool_a: has emotion, in store, 2 variants
        entry_a = next(r for r in result if r["tool"] == "tool_a")
        assert entry_a["emotion"] == emotions["tool_a"]
        assert entry_a["variant_count"] == 2
        assert entry_a["in_store"] is True

        # tool_b: has emotion, not in store, 0 variants
        entry_b = next(r for r in result if r["tool"] == "tool_b")
        assert entry_b["emotion"] == emotions["tool_b"]
        assert entry_b["variant_count"] == 0
        assert entry_b["in_store"] is False

    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_sense_empty(self, mock_sense):
        mock_sense.return_value = {}
        col = _mock_collector(signals=[])
        gen = _mock_genome(tools=[])

        sub = PhenotypeSubstrate(collector=col, genome=gen)
        assert sub.sense() == []

    @patch("metabolon.metabolism.substrates.tools.sense_affect")
    def test_sense_tool_only_in_genome(self, mock_sense):
        """Tool catalogued but never invoked — should still appear."""
        mock_sense.return_value = {}
        col = _mock_collector(signals=[])
        gen = _mock_genome(tools=["lonely_tool"])

        sub = PhenotypeSubstrate(collector=col, genome=gen)
        result = sub.sense()

        assert len(result) == 1
        assert result[0]["tool"] == "lonely_tool"
        assert result[0]["emotion"] is None
        assert result[0]["in_store"] is True


# ---------------------------------------------------------------------------
# candidates
# ---------------------------------------------------------------------------

class TestCandidates:
    @patch("metabolon.metabolism.substrates.tools.select")
    def test_filters_below_median(self, mock_select):
        mock_select.return_value = ["weak_tool"]
        sub = PhenotypeSubstrate()

        sensed = [
            {"tool": "strong_tool", "emotion": _emotion("strong_tool", valence=0.9), "variant_count": 0, "in_store": True},
            {"tool": "weak_tool", "emotion": _emotion("weak_tool", valence=0.1), "variant_count": 0, "in_store": True},
        ]

        result = sub.candidates(sensed)
        assert len(result) == 1
        assert result[0]["tool"] == "weak_tool"

    @patch("metabolon.metabolism.substrates.tools.select")
    def test_no_candidates(self, mock_select):
        mock_select.return_value = []
        sub = PhenotypeSubstrate()

        sensed = [
            {"tool": "ok_tool", "emotion": _emotion("ok_tool", valence=0.8), "variant_count": 0, "in_store": True},
        ]

        assert sub.candidates(sensed) == []

    @patch("metabolon.metabolism.substrates.tools.select")
    def test_skips_none_emotions(self, mock_select):
        """Entries with emotion=None are passed through (not in phenotype_scores)."""
        mock_select.return_value = []
        sub = PhenotypeSubstrate()

        sensed = [
            {"tool": "unknown", "emotion": None, "variant_count": 0, "in_store": False},
        ]

        # phenotype_scores will be empty, select gets {}
        result = sub.candidates(sensed)
        mock_select.assert_called_once_with({})
        assert result == []


# ---------------------------------------------------------------------------
# act
# ---------------------------------------------------------------------------

class TestAct:
    def test_skip_not_in_store(self):
        sub = PhenotypeSubstrate()
        candidate = {"tool": "ghost", "emotion": None, "in_store": False}
        assert sub.act(candidate) == "skip: ghost not in genome"

    def test_mutation_no_emotion(self):
        sub = PhenotypeSubstrate()
        candidate = {"tool": "new_tool", "emotion": None, "in_store": True}
        assert sub.act(candidate) == "mutation needed for new_tool: no emotion data"

    def test_mutation_no_valence(self):
        sub = PhenotypeSubstrate()
        emo = _emotion("sketchy", activations=2, valence=None)
        candidate = {"tool": "sketchy", "emotion": emo, "in_store": True}
        result = sub.act(candidate)
        assert result == "mutation needed for sketchy: insufficient stimuli (2 invocations)"

    def test_mutation_low_valence(self):
        sub = PhenotypeSubstrate()
        emo = _emotion("sad_tool", valence=0.123)
        candidate = {"tool": "sad_tool", "emotion": emo, "in_store": True}
        result = sub.act(candidate)
        assert result == "mutation needed for sad_tool: valence 0.123"


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

class TestReport:
    def test_empty_report(self):
        sub = PhenotypeSubstrate()
        report = sub.report([], [])
        assert "0 tool(s) sensed" in report

    def test_report_with_data(self):
        sub = PhenotypeSubstrate()
        sensed = [
            {
                "tool": "alpha",
                "emotion": _emotion("alpha", activations=10, success_rate=0.75, valence=0.55),
                "variant_count": 3,
                "in_store": True,
            },
            {
                "tool": "beta",
                "emotion": None,
                "variant_count": 0,
                "in_store": False,
            },
        ]
        acted = ["mutation needed for alpha: valence 0.550"]

        report = sub.report(sensed, acted)

        assert "2 tool(s) sensed" in report
        assert "alpha: valence=0.550" in report
        assert "invocations=10" in report
        assert "success_rate=75.0%" in report
        assert "variants=3" in report
        assert "beta: no signals" in report
        assert "-- Actions --" in report
        assert "mutation needed for alpha" in report

    def test_report_no_actions(self):
        sub = PhenotypeSubstrate()
        sensed = [
            {
                "tool": "ok",
                "emotion": _emotion("ok", valence=0.99),
                "variant_count": 0,
                "in_store": True,
            },
        ]
        report = sub.report(sensed, [])
        assert "-- Actions --" not in report

    def test_report_valence_na(self):
        sub = PhenotypeSubstrate()
        sensed = [
            {
                "tool": "mystery",
                "emotion": _emotion("mystery", valence=None),
                "variant_count": 1,
                "in_store": True,
            },
        ]
        report = sub.report(sensed, [])
        assert "valence=N/A" in report
