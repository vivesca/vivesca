"""Tests for PhenotypeSubstrate (tools substrate)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from metabolon.metabolism.substrates.tools import PhenotypeSubstrate


def test_name():
    """Verify substrate name is correct."""
    s = PhenotypeSubstrate()
    assert s.name == "tools"


def test_init_defaults():
    """Test default initialization."""
    s = PhenotypeSubstrate()
    assert s.collector is not None
    assert s.genome is not None


def test_sense_empty():
    """Test sense with no signals or tools."""
    mock_collector = MagicMock()
    mock_collector.recall_since.return_value = []
    mock_genome = MagicMock()
    mock_genome.expressed_tools.return_value = []
    s = PhenotypeSubstrate(collector=mock_collector, genome=mock_genome)
    sensed = s.sense()
    assert isinstance(sensed, list)
    assert len(sensed) == 0


def test_sense_with_data():
    """Test sense combines signals and genome data."""
    mock_collector = MagicMock()
    mock_collector.recall_since.return_value = [
        MagicMock(tool="rheotaxis", kind="invocation"),
    ]
    mock_genome = MagicMock()
    mock_genome.expressed_tools.return_value = ["rheotaxis", "histone"]
    mock_genome.allele_variants.side_effect = lambda tool: [f"{tool}_v1", f"{tool}_v2"] if tool == "rheotaxis" else []

    with patch("metabolon.metabolism.substrates.tools.sense_affect") as mock_affect:
        mock_emotion = MagicMock(valence=0.8, activations=5, success_rate=0.8)
        mock_affect.return_value = {"rheotaxis": mock_emotion}
        s = PhenotypeSubstrate(collector=mock_collector, genome=mock_genome)
        sensed = s.sense()
        assert isinstance(sensed, list)
        assert len(sensed) == 2  # rheotaxis and histone
        # Check sorted order
        assert sensed[0]["tool"] == "histone"
        assert sensed[1]["tool"] == "rheotaxis"
        assert sensed[1]["variant_count"] == 2
        assert sensed[1]["in_store"] is True


def test_sense_handles_emotions_correctly():
    """Test sense correctly assigns emotions to tools."""
    mock_collector = MagicMock()
    mock_collector.recall_since.return_value = [MagicMock(tool="tool_a")]
    mock_genome = MagicMock()
    mock_genome.expressed_tools.return_value = ["tool_a", "tool_b"]
    mock_genome.allele_variants.return_value = []

    with patch("metabolon.metabolism.substrates.tools.sense_affect") as mock_affect:
        mock_emotion_a = MagicMock(valence=0.5, activations=10)
        mock_affect.return_value = {"tool_a": mock_emotion_a}
        s = PhenotypeSubstrate(collector=mock_collector, genome=mock_genome)
        sensed = s.sense()
        assert sensed[0]["tool"] == "tool_a"
        assert sensed[0]["emotion"] is mock_emotion_a
        assert sensed[1]["tool"] == "tool_b"
        assert sensed[1]["emotion"] is None


def test_candidates_filters_unfit():
    """Test candidates selects unfit candidates from sensed data."""
    s = PhenotypeSubstrate()
    with patch("metabolon.metabolism.substrates.tools.select") as mock_select:
        mock_select.return_value = {"tool_b"}
        sensed = [
            {"tool": "tool_a", "emotion": MagicMock()},
            {"tool": "tool_b", "emotion": MagicMock()},
        ]
        candidates = s.candidates(sensed)
        assert len(candidates) == 1
        assert candidates[0]["tool"] == "tool_b"
        mock_select.assert_called_once()


def test_candidates_empty_with_no_emotions():
    """Test candidates returns empty when there are no emotions."""
    s = PhenotypeSubstrate()
    with patch("metabolon.metabolism.substrates.tools.select") as mock_select:
        mock_select.return_value = set()
        sensed = [{"tool": "tool_a", "emotion": None}]
        candidates = s.candidates(sensed)
        assert len(candidates) == 0


def test_act_skip_not_in_store():
    """Test act skips tools not in genome."""
    s = PhenotypeSubstrate()
    result = s.act({"tool": "ghost", "emotion": None, "in_store": False})
    assert "skip: ghost not in genome" in result


def test_act_no_emotion_data():
    """Test act flags need mutation when no emotion data."""
    s = PhenotypeSubstrate()
    result = s.act({"tool": "unknown", "emotion": None, "in_store": True})
    assert "mutation needed for unknown: no emotion data" in result


def test_act_insufficient_stimuli():
    """Test act flags insufficient data."""
    s = PhenotypeSubstrate()
    from unittest.mock import MagicMock
    fitness = MagicMock(valence=None, activations=2)
    result = s.act({"tool": "new_tool", "emotion": fitness, "in_store": True})
    assert "mutation needed for new_tool: insufficient stimuli" in result


def test_act_valence_problem():
    """Test act reports valence value for mutation candidates."""
    s = PhenotypeSubstrate()
    from unittest.mock import MagicMock
    fitness = MagicMock(valence=0.123, activations=10)
    result = s.act({"tool": "bad_tool", "emotion": fitness, "in_store": True})
    assert "mutation needed for bad_tool: valence 0.123" in result


def test_report_format():
    """Test report produces human-readable output."""
    s = PhenotypeSubstrate()
    from unittest.mock import MagicMock
    fitness = MagicMock(valence=0.5, activations=10, success_rate=0.9)
    sensed = [
        {"tool": "good_tool", "emotion": fitness, "variant_count": 3},
        {"tool": "no_signal_tool", "emotion": None, "variant_count": 0},
    ]
    report = s.report(sensed, [])
    assert "2 tool(s) sensed" in report
    assert "valence=0.500" in report
    assert "invocations=10" in report
    assert "success_rate=90.0%" in report
    assert "variants=3" in report
    assert "no signals" in report


def test_report_with_actions():
    """Test report includes actions section when there are actions."""
    s = PhenotypeSubstrate()
    report = s.report([], ["mutation needed for bad_tool"])
    assert "0 tool(s) sensed" in report
    assert "-- Actions --" in report
    assert "mutation needed for bad_tool" in report
