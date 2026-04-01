from __future__ import annotations

"""Tests for PhenotypeSubstrate (tools)."""


from unittest.mock import MagicMock, patch
from metabolon.metabolism.substrates.tools import PhenotypeSubstrate


def test_tools_substrate_name():
    s = PhenotypeSubstrate()
    assert s.name == "tools"


def test_tools_substrate_sense_empty():
    mock_collector = MagicMock()
    mock_collector.recall_since.return_value = []
    mock_genome = MagicMock()
    mock_genome.expressed_tools.return_value = []
    s = PhenotypeSubstrate(collector=mock_collector, genome=mock_genome)
    sensed = s.sense()
    assert isinstance(sensed, list)


def test_tools_substrate_sense_with_data():
    mock_collector = MagicMock()
    mock_collector.recall_since.return_value = [
        MagicMock(tool="rheotaxis", kind="invocation"),
    ]
    mock_genome = MagicMock()
    mock_genome.expressed_tools.return_value = ["rheotaxis", "histone"]
    with patch("metabolon.metabolism.substrates.tools.sense_affect") as mock_affect:
        mock_affect.return_value = {"rheotaxis": MagicMock(valence=0.8, arousal=0.5)}
        s = PhenotypeSubstrate(collector=mock_collector, genome=mock_genome)
        sensed = s.sense()
        assert isinstance(sensed, list)


def test_candidates_from_sensed():
    s = PhenotypeSubstrate()
    # candidates filters sensed data — test with empty
    assert isinstance(s.candidates([]), list)


def test_tools_substrate_act_returns_string():
    s = PhenotypeSubstrate()
    from unittest.mock import MagicMock as MM
    result = s.act({"tool": "rheotaxis", "emotion": MM(valence=0.5, arousal=0.3), "description": "search", "in_store": True})
    assert isinstance(result, str)


def test_tools_substrate_report_format():
    s = PhenotypeSubstrate()
    report = s.report([], [])
    assert isinstance(report, str)
