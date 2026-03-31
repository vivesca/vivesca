"""Tests for ExecutiveSubstrate (constitution substrate)."""

from unittest.mock import patch, MagicMock
from metabolon.metabolism.substrates.constitution import ExecutiveSubstrate


def test_name():
    """Verify substrate name is correct."""
from __future__ import annotations

    s = ExecutiveSubstrate()
    assert s.name == "constitution"


def test_sense_no_file(tmp_path):
    """Test sense returns empty list when constitution file doesn't exist."""
    s = ExecutiveSubstrate(constitution_path=tmp_path / "nonexistent.md")
    assert s.sense() == []


def test_sense_reads_rules(tmp_path):
    """Test sense extracts bold-prefixed rules from constitution file."""
    constitution = tmp_path / "genome.md"
    constitution.write_text(
        "# Constitution\n\n"
        "**Rule one:** Always verify before asserting.\n"
        "**Rule two:** Never hallucinate imports.\n"
        "Regular text that is not a rule.\n"
    )
    mock_collector = MagicMock()
    mock_collector.recall_since.return_value = []
    with patch("metabolon.metabolism.substrates.constitution.precision_scan") as mock_ps:
        mock_ps.return_value = []
        s = ExecutiveSubstrate(constitution_path=constitution, collector=mock_collector)
        sensed = s.sense()
        assert isinstance(sensed, list)
        assert len(sensed) == 2
        assert sensed[0]["title"] == "Rule one:"
        assert sensed[1]["title"] == "Rule two:"


def test_sense_cross_references_activated_enzymes(tmp_path):
    """Test sense cross-references rules with active enzymes from signals."""
    constitution = tmp_path / "genome.md"
    constitution.write_text(
        "**rheotaxis:** Analyze flow patterns\n"
        "**glycolysis:** Check energy use\n"
    )
    mock_collector = MagicMock()
    mock_collector.recall_since.return_value = [
        MagicMock(tool="rheotaxis_detect", kind="invocation"),
    ]
    with patch("metabolon.metabolism.substrates.constitution.precision_scan") as mock_ps:
        mock_ps.return_value = []
        s = ExecutiveSubstrate(constitution_path=constitution, collector=mock_collector)
        sensed = s.sense()
        assert len(sensed) == 2
        # rheotaxis should have evidence from rheotaxis_detect
        assert sensed[0]["has_evidence"] is True
        # glycolysis has no evidence
        assert sensed[1]["has_evidence"] is False


def test_candidates_filters_unevidenced_rules():
    """Test candidates returns only rules without evidence."""
    s = ExecutiveSubstrate()
    sensed = [
        {"title": "A", "has_evidence": True},
        {"title": "B", "has_evidence": False},
        {"title": "C", "has_evidence": True},
    ]
    candidates = s.candidates(sensed)
    assert len(candidates) == 1
    assert candidates[0]["title"] == "B"


def test_candidates_empty_sensed():
    """Test candidates returns empty for empty input."""
    s = ExecutiveSubstrate()
    assert s.candidates([]) == []


def test_act_prune_candidate():
    """Test act produces pruning message for unevidenced rules."""
    s = ExecutiveSubstrate()
    result = s.act({"title": "test rule"})
    assert isinstance(result, str)
    assert "prune candidate" in result
    assert "test rule" in result


def test_act_precision_gap():
    """Test act produces rename message for precision gaps."""
    s = ExecutiveSubstrate()
    result = s.act({
        "title": "Precision gap: BadNaming",
        "precision_gap": True,
        "references": ["file1.py", "file2.py"]
    })
    assert isinstance(result, str)
    assert "rename:" in result
    assert "2 reference(s)" in result


def test_report_format():
    """Test report produces human-readable output."""
    s = ExecutiveSubstrate()
    sensed = [
        {"title": "rule1", "has_evidence": True, "activated_enzymes": {"tool1"}},
        {"title": "rule2", "has_evidence": False},
    ]
    report = s.report(sensed, ["pruned rule2"])
    assert isinstance(report, str)
    assert "2 rule(s) sensed" in report
    assert "Rules with signal evidence" in report
    assert "Rules without signal evidence" in report
    assert "pruned rule2" in report


def test_report_shows_summary():
    """Test report shows summary counts."""
    s = ExecutiveSubstrate()
    sensed = [
        {"title": "r1", "has_evidence": True, "activated_enzymes": set()},
        {"title": "r2", "has_evidence": False}
    ]
    report = s.report(sensed, [])
    assert "1 evidenced" in report
    assert "1 without evidence" in report


def test_precision_scan_exception_handled(tmp_path):
    """Test that precision scan exceptions are handled gracefully."""
    constitution = tmp_path / "genome.md"
    constitution.write_text("**Rule:** test\n")
    mock_collector = MagicMock()
    mock_collector.recall_since.return_value = []
    s = ExecutiveSubstrate(constitution_path=constitution, collector=mock_collector)
    # Force exception in precision_scan
    with patch("metabolon.metabolism.substrates.constitution.precision_scan", side_effect=Exception("test")):
        # Should not raise
        sensed = s.sense()
        assert len(sensed) == 1
