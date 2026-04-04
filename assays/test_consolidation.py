"""Tests for metabolon.metabolism.substrates.memory — ConsolidationSubstrate."""

from __future__ import annotations

import textwrap
from datetime import UTC, datetime
from unittest.mock import MagicMock

from metabolon.metabolism.substrates.memory import (
    CONSOLIDATION_PATHWAYS,
    ConsolidationSubstrate,
    _keyword_overlap,
    _parse_frontmatter,
)

# ---------------------------------------------------------------------------
# _parse_frontmatter
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_extracts_key_value_pairs(self):
        md = textwrap.dedent("""\
            ---
            name: foo
            type: feedback
            ---
            body text
        """)
        result = _parse_frontmatter(md)
        assert result == {"name": "foo", "type": "feedback"}

    def test_returns_empty_on_no_frontmatter(self):
        assert _parse_frontmatter("just body text") == {}

    def test_handles_empty_frontmatter_block(self):
        md = "---\n---\nbody"
        assert _parse_frontmatter(md) == {}


# ---------------------------------------------------------------------------
# _keyword_overlap
# ---------------------------------------------------------------------------


class TestKeywordOverlap:
    def test_finds_common_words(self):
        overlap = _keyword_overlap("pytest runner fails", "pytest suite passes")
        assert "pytest" in overlap

    def test_ignores_short_words(self):
        overlap = _keyword_overlap("the big cat", "the big dog", min_word_len=4)
        # "the" and "big" are < 4 chars, so nothing matches
        assert overlap == set()

    def test_no_overlap(self):
        overlap = _keyword_overlap("alpha beta gamma", "delta epsilon zeta")
        assert overlap == set()


# ---------------------------------------------------------------------------
# ConsolidationSubstrate.sense
# ---------------------------------------------------------------------------


class TestSense:
    def test_returns_empty_when_dir_missing(self, tmp_path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "nonexistent",
            constitution_path=tmp_path / "nope.md",
        )
        assert sub.sense() == []

    def test_returns_empty_when_no_md_files(self, tmp_path):
        (tmp_path / "memory").mkdir()
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "nope.md",
        )
        assert sub.sense() == []

    def test_parses_memory_files(self, tmp_path):
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "test-mem.md").write_text(
            "---\nname: my-mem\ntype: feedback\ndescription: a test memory\n---\nbody text\n"
        )

        mock_collector = MagicMock()
        mock_collector.recall_since.return_value = []

        sub = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "nope.md",
            collector=mock_collector,
        )
        results = sub.sense()
        assert len(results) == 1
        assert results[0]["name"] == "my-mem"
        assert results[0]["type"] == "feedback"
        assert results[0]["target"] == CONSOLIDATION_PATHWAYS["feedback"]

    def test_skips_memory_md_index(self, tmp_path):
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "MEMORY.md").write_text("# index\n")
        (mem_dir / "real.md").write_text("---\nname: real\ntype: finding\n---\nbody\n")

        mock_collector = MagicMock()
        mock_collector.recall_since.return_value = []

        sub = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "nope.md",
            collector=mock_collector,
        )
        results = sub.sense()
        assert len(results) == 1
        assert results[0]["name"] == "real"

    def test_signal_match_detected(self, tmp_path):
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "sig.md").write_text("---\nname: sig\ntype: finding\n---\npytest runner\n")

        stim = MagicMock()
        stim.tool = "pytest_runner"
        stim.created_at = datetime.now(UTC)

        mock_collector = MagicMock()
        mock_collector.recall_since.return_value = [stim]

        sub = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "nope.md",
            collector=mock_collector,
        )
        results = sub.sense()
        assert results[0]["signal_match"] is True


# ---------------------------------------------------------------------------
# ConsolidationSubstrate.candidates
# ---------------------------------------------------------------------------


class TestCandidates:
    def _make(self, mem_type, overlap=None, signal_match=False):
        return {
            "name": "test",
            "type": mem_type,
            "constitution_overlap": overlap or set(),
            "signal_match": signal_match,
            "target": CONSOLIDATION_PATHWAYS.get(mem_type, ("Unknown", "")),
        }

    def test_feedback_with_high_overlap_already_promoted(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        mem = self._make("feedback", overlap={"alpha", "beta", "gamma", "delta", "epsilon"})
        results = sub.candidates([mem])
        assert results[0]["action"] == "already_promoted"

    def test_feedback_with_signal_is_high_priority(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        mem = self._make("feedback", signal_match=True)
        results = sub.candidates([mem])
        assert results[0]["action"] == "promote"
        assert "high" in results[0]["priority"]

    def test_finding_becomes_program(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        mem = self._make("finding")
        results = sub.candidates([mem])
        assert results[0]["action"] == "program"

    def test_project_type_migrates(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        mem = self._make("project")
        results = sub.candidates([mem])
        assert results[0]["action"] == "migrate"

    def test_no_overlap_no_signal_is_dead(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        mem = self._make("feedback", overlap=set(), signal_match=False)
        results = sub.candidates([mem])
        assert results[0].get("dead") is True

    def test_unknown_type(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        mem = self._make("weird_type")
        results = sub.candidates([mem])
        assert results[0]["action"] == "unknown"


# ---------------------------------------------------------------------------
# ConsolidationSubstrate.act
# ---------------------------------------------------------------------------


class TestAct:
    def test_dead_candidate_pruned(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        result = sub.act(
            {"name": "old-mem", "action": "promote", "dead": True, "type": "feedback"}
        )
        assert result.startswith("prune candidate")

    def test_already_promoted(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        result = sub.act(
            {
                "name": "mem",
                "action": "already_promoted",
                "type": "feedback",
                "constitution_overlap": {"a", "b", "c", "d", "e"},
            }
        )
        assert "already promoted" in result
        assert "5 keywords" in result

    def test_promote_action(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        result = sub.act({"name": "mem", "action": "promote", "type": "feedback"})
        assert result.startswith("promote to constitution")

    def test_promote_with_priority(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        result = sub.act(
            {
                "name": "mem",
                "action": "promote",
                "type": "feedback",
                "priority": "high (signal evidence)",
            }
        )
        assert "[high (signal evidence)]" in result

    def test_program_action(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        result = sub.act({"name": "gotcha", "action": "program", "type": "finding"})
        assert result.startswith("program candidate")

    def test_migrate_action(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        result = sub.act(
            {
                "name": "notes",
                "action": "migrate",
                "type": "project",
                "target": ("Chromatin note", "Project state"),
            }
        )
        assert "migrate to Chromatin note" in result

    def test_unknown_action_falls_back_to_review(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        result = sub.act({"name": "x", "action": "unknown", "type": "mystery"})
        assert result.startswith("review:")


# ---------------------------------------------------------------------------
# ConsolidationSubstrate.report
# ---------------------------------------------------------------------------


class TestReport:
    def test_report_includes_type_counts(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        sensed = [
            {"type": "feedback"},
            {"type": "feedback"},
            {"type": "finding"},
        ]
        report = sub.report(sensed, [])
        assert "feedback: 2" in report
        assert "finding: 1" in report

    def test_report_groups_actions(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        sensed = [{"type": "feedback"}]
        acted = [
            "promote to constitution: a",
            "promote to constitution: b",
            "program candidate: c",
            "migrate to X: d",
            "prune candidate: e",
        ]
        report = sub.report(sensed, acted)
        assert "Promote:" in report
        assert "Program:" in report
        assert "Migrate:" in report
        assert "Prune:" in report

    def test_report_summary_counts(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        acted = [
            "promote to constitution: a",
            "already promoted: b (overlap: 5 keywords)",
            "program candidate: c",
            "migrate to X: d",
            "prune candidate: e",
        ]
        report = sub.report([], acted)
        assert "1 to promote" in report
        assert "1 already promoted" in report
        assert "1 to program" in report
        assert "1 to migrate" in report
        assert "1 to prune" in report
