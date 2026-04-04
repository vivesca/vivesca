"""Tests for ExecutiveSubstrate — constitution rule parsing and audit."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.metabolism.substrates.constitution import ExecutiveSubstrate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SCAN_PATH = "metabolon.metabolism.substrates.constitution.precision_scan"


@pytest.fixture(autouse=True)
def _suppress_precision_scan():
    """Prevent real precision_scan from running in every sense() call."""
    with patch(_SCAN_PATH, return_value=[]):
        yield


def _make_substrate(tmp_path: Path, content: str, signals=None):
    """Build an ExecutiveSubstrate with a temp constitution file and mock collector."""
    constitution = tmp_path / "genome.md"
    constitution.write_text(content)
    mock_collector = MagicMock()
    mock_collector.recall_since.return_value = signals or []
    return ExecutiveSubstrate(constitution_path=constitution, collector=mock_collector)


def _make_signal(tool: str):
    """Build a lightweight signal-like object with a .tool attribute."""
    sig = MagicMock()
    sig.tool = tool
    return sig


# ---------------------------------------------------------------------------
# sense — file handling
# ---------------------------------------------------------------------------


class TestSenseFileHandling:
    def test_missing_file_returns_empty(self, tmp_path):
        s = ExecutiveSubstrate(constitution_path=tmp_path / "nope.md")
        assert s.sense() == []

    def test_empty_file_returns_empty(self, tmp_path):
        s = _make_substrate(tmp_path, "")
        assert s.sense() == []

    def test_no_bold_rules_returns_empty(self, tmp_path):
        s = _make_substrate(tmp_path, "# Title\nSome text\nMore text\n")
        assert s.sense() == []


# ---------------------------------------------------------------------------
# sense — rule parsing
# ---------------------------------------------------------------------------


class TestSenseRuleParsing:
    def test_parses_single_bold_rule(self, tmp_path):
        s = _make_substrate(tmp_path, "**Always verify.** Do thorough checks.\n")
        rules = s.sense()
        assert len(rules) == 1
        assert rules[0]["title"] == "Always verify"
        assert rules[0]["body"] == "Do thorough checks."

    def test_parses_multiple_bold_rules(self, tmp_path):
        md = (
            "# Constitution\n"
            "**Rule one:** Always verify.\n"
            "Normal line.\n"
            "**Rule two.** Never hallucinate.\n"
        )
        s = _make_substrate(tmp_path, md)
        rules = s.sense()
        assert len(rules) == 2
        titles = {r["title"] for r in rules}
        assert "Rule one:" in titles
        assert "Rule two" in titles

    def test_rule_has_line_field(self, tmp_path):
        s = _make_substrate(tmp_path, "**Testing.** Body text.\n")
        rules = s.sense()
        assert rules[0]["line"] == "**Testing.** Body text."

    def test_skips_non_bold_lines(self, tmp_path):
        md = "- Item one\n- Item two\n**Real rule:** Content.\n"
        s = _make_substrate(tmp_path, md)
        rules = s.sense()
        assert len(rules) == 1
        assert rules[0]["title"] == "Real rule:"


# ---------------------------------------------------------------------------
# sense — enzyme cross-referencing
# ---------------------------------------------------------------------------


class TestSenseEnzymeCrossRef:
    def test_no_signals_marks_no_evidence(self, tmp_path):
        s = _make_substrate(tmp_path, "**deploy_tool:** Use it wisely.\n", signals=[])
        rules = s.sense()
        assert len(rules) == 1
        assert rules[0]["has_evidence"] is False

    def test_matching_signal_sets_evidence(self, tmp_path):
        sig = _make_signal("deploy_tool")
        s = _make_substrate(tmp_path, "**deploy_tool:** Use it.\n", signals=[sig])
        rules = s.sense()
        assert rules[0]["has_evidence"] is True
        assert "deploy_tool" in rules[0]["activated_enzymes"]

    def test_prefix_match_from_underscore_tool(self, tmp_path):
        """If signal tool is 'golem_build', enzyme 'golem' should also match."""
        sig = _make_signal("golem_build")
        s = _make_substrate(tmp_path, "**golem:** Daemon.\n", signals=[sig])
        rules = s.sense()
        assert rules[0]["has_evidence"] is True
        assert "golem" in rules[0]["activated_enzymes"]

    def test_unrelated_signal_no_evidence(self, tmp_path):
        sig = _make_signal("unrelated_tool")
        s = _make_substrate(tmp_path, "**deploy_tool:** Use it.\n", signals=[sig])
        rules = s.sense()
        assert rules[0]["has_evidence"] is False


# ---------------------------------------------------------------------------
# candidates
# ---------------------------------------------------------------------------


class TestCandidates:
    def test_empty_sensed_returns_empty(self):
        s = ExecutiveSubstrate()
        assert s.candidates([]) == []

    def test_filters_to_unevidenced(self):
        s = ExecutiveSubstrate()
        sensed = [
            {"title": "a", "has_evidence": True},
            {"title": "b", "has_evidence": False},
            {"title": "c", "has_evidence": True},
        ]
        result = s.candidates(sensed)
        assert len(result) == 1
        assert result[0]["title"] == "b"

    def test_all_evidenced_returns_empty(self):
        s = ExecutiveSubstrate()
        sensed = [
            {"title": "a", "has_evidence": True},
            {"title": "b", "has_evidence": True},
        ]
        assert s.candidates(sensed) == []


# ---------------------------------------------------------------------------
# act
# ---------------------------------------------------------------------------


class TestAct:
    def test_prune_candidate_for_normal_rule(self):
        s = ExecutiveSubstrate()
        result = s.act({"title": "Stale rule"})
        assert result == "prune candidate: Stale rule"

    def test_rename_action_for_precision_gap(self):
        s = ExecutiveSubstrate()
        result = s.act(
            {
                "title": "Precision gap (naming): foo_bar should be foo_baz",
                "precision_gap": True,
                "references": ["file1.py", "file2.py", "file3.py"],
            }
        )
        assert result.startswith("rename:")
        assert "3 reference(s)" in result


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


class TestReport:
    def test_report_with_no_rules(self):
        s = ExecutiveSubstrate()
        report = s.report([], [])
        assert "0 rule(s) sensed" in report
        assert "0 evidenced" in report

    def test_report_separates_evidenced_and_unevidenced(self):
        s = ExecutiveSubstrate()
        sensed = [
            {"title": "Active", "has_evidence": True, "activated_enzymes": {"tool_a"}},
            {"title": "Dormant", "has_evidence": False, "activated_enzymes": set()},
        ]
        report = s.report(sensed, [])
        assert "Active" in report
        assert "Dormant" in report
        assert "1 evidenced" in report
        assert "1 without evidence" in report

    def test_report_includes_actions(self):
        s = ExecutiveSubstrate()
        report = s.report([], ["prune candidate: Old rule"])
        assert "Actions" in report
        assert "prune candidate: Old rule" in report


# ---------------------------------------------------------------------------
# precision scan integration (re-enable the mock per-test)
# ---------------------------------------------------------------------------


class TestPrecisionScan:
    @patch(_SCAN_PATH)
    def test_precision_gaps_appended_to_rules(self, mock_scan, tmp_path):
        gap = MagicMock()
        gap.closed = False
        gap.kind = "naming"
        gap.description = "foo_bar should be foo_baz in module X"
        gap.references = ["src/a.py", "src/b.py"]
        mock_scan.return_value = [gap]

        s = _make_substrate(tmp_path, "**Deploy:** Push code.\n")
        rules = s.sense()
        titles = [r["title"] for r in rules]
        assert any("Precision gap" in t for t in titles)

    @patch(_SCAN_PATH)
    def test_precision_scan_exception_swallowed(self, mock_scan, tmp_path):
        mock_scan.side_effect = RuntimeError("boom")
        s = _make_substrate(tmp_path, "**Rule:** Something.\n")
        rules = s.sense()
        # Should still return the parsed rule (precision gap just skipped)
        assert len(rules) >= 1

    @patch(_SCAN_PATH)
    def test_closed_gaps_not_appended(self, mock_scan, tmp_path):
        gap = MagicMock()
        gap.closed = True
        mock_scan.return_value = [gap]
        s = _make_substrate(tmp_path, "**Rule:** Content.\n")
        rules = s.sense()
        assert all("Precision gap" not in r["title"] for r in rules)
