"""Tests for ExecutiveSubstrate (constitution)."""

from unittest.mock import patch, MagicMock
from metabolon.metabolism.substrates.constitution import ExecutiveSubstrate


def test_constitution_substrate_name():
    s = ExecutiveSubstrate()
    assert s.name == "constitution"


def test_sense_no_file(tmp_path):
    s = ExecutiveSubstrate(constitution_path=tmp_path / "nonexistent.md")
    assert s.sense() == []


def test_sense_reads_rules(tmp_path):
    constitution = tmp_path / "genome.md"
    constitution.write_text(
        "# Constitution\n\n"
        "**Rule one:** Always verify before asserting.\n"
        "**Rule two:** Never hallucinate imports.\n"
        "Regular text that is not a rule.\n"
    )
    mock_collector = MagicMock()
    mock_collector.recall_since.return_value = []
    s = ExecutiveSubstrate(constitution_path=constitution, collector=mock_collector)
    sensed = s.sense()
    assert isinstance(sensed, list)


def test_candidates_empty_sensed():
    s = ExecutiveSubstrate()
    assert s.candidates([]) == []


def test_constitution_substrate_act_returns_string():
    s = ExecutiveSubstrate()
    result = s.act({"title": "test rule", "signal_count": 0})
    assert isinstance(result, str)


def test_constitution_substrate_report_format():
    s = ExecutiveSubstrate()
    sensed = [{"title": "rule1", "signal_count": 5}]
    report = s.report(sensed, ["pruned rule1"])
    assert isinstance(report, str)
