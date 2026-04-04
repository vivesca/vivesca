"""Tests for metabolon/metabolism/substrates/memory.py — ConsolidationSubstrate."""

from __future__ import annotations

import textwrap
from unittest.mock import MagicMock

from metabolon.metabolism.substrates.memory import (
    CONSOLIDATION_PATHWAYS,
    ConsolidationSubstrate,
    _keyword_overlap,
    _parse_frontmatter,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_md(name: str, mem_type: str, body: str = "") -> str:
    """Return a markdown string with frontmatter."""
    return textwrap.dedent(f"""\
        ---
        name: {name}
        type: {mem_type}
        description: test memory
        ---
        {body}
    """)


# ---------------------------------------------------------------------------
# _parse_frontmatter
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_basic(self):
        text = "---\nname: foo\ntype: feedback\n---\nbody"
        meta = _parse_frontmatter(text)
        assert meta["name"] == "foo"
        assert meta["type"] == "feedback"

    def test_no_frontmatter(self):
        assert _parse_frontmatter("just text") == {}

    def test_incomplete_delimiters(self):
        assert _parse_frontmatter("---\nname: foo") == {}


# ---------------------------------------------------------------------------
# _keyword_overlap
# ---------------------------------------------------------------------------


class TestKeywordOverlap:
    def test_shared_words(self):
        overlap = _keyword_overlap("python testing framework", "python web framework")
        assert "python" in overlap
        assert "framework" in overlap

    def test_no_overlap(self):
        assert _keyword_overlap("alpha beta", "gamma delta") == set()

    def test_min_word_len(self):
        overlap = _keyword_overlap("the big cat", "the big dog", min_word_len=4)
        assert "big" not in overlap  # too short at len=3

    def test_case_insensitive(self):
        overlap = _keyword_overlap("Python Testing", "python testing")
        assert "python" in overlap


# ---------------------------------------------------------------------------
# ConsolidationSubstrate.sense
# ---------------------------------------------------------------------------


class TestSense:
    def test_empty_dir(self, tmp_path):
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        sub = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "nonexistent.md",
            collector=MagicMock(recall_since=MagicMock(return_value=[])),
        )
        assert sub.sense() == []

    def test_nonexistent_dir(self, tmp_path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "nope",
            constitution_path=tmp_path / "nonexistent.md",
            collector=MagicMock(recall_since=MagicMock(return_value=[])),
        )
        assert sub.sense() == []

    def test_senses_files(self, tmp_path):
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "alpha.md").write_text(_make_md("alpha", "feedback", "testing python"))
        (mem_dir / "MEMORY.md").write_text("skip me")  # should be excluded

        collector = MagicMock()
        collector.recall_since.return_value = []
        sub = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "nonexistent.md",
            collector=collector,
        )
        results = sub.sense()
        assert len(results) == 1
        assert results[0]["name"] == "alpha"
        assert results[0]["type"] == "feedback"

    def test_signal_match(self, tmp_path):
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "beta.md").write_text(_make_md("beta", "finding", "pytest fixture"))

        signal = MagicMock()
        signal.tool = "pytest"
        collector = MagicMock()
        collector.recall_since.return_value = [signal]

        sub = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "nonexistent.md",
            collector=collector,
        )
        results = sub.sense()
        assert results[0]["signal_match"] is True


# ---------------------------------------------------------------------------
# ConsolidationSubstrate.candidates
# ---------------------------------------------------------------------------


class TestCandidates:
    def _make_sensed(self, mem_type: str, overlap_size: int = 0, signal: bool = False):
        return {
            "name": "test",
            "type": mem_type,
            "constitution_overlap": {f"word{i}" for i in range(overlap_size)},
            "signal_match": signal,
            "target": CONSOLIDATION_PATHWAYS.get(mem_type, ("Unknown", "")),
        }

    def test_feedback_promote(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        result = sub.candidates([self._make_sensed("feedback")])
        assert result[0]["action"] == "promote"

    def test_feedback_already_promoted(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        result = sub.candidates([self._make_sensed("feedback", overlap_size=6)])
        assert result[0]["action"] == "already_promoted"

    def test_feedback_high_priority_signal(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        result = sub.candidates([self._make_sensed("feedback", signal=True)])
        assert result[0]["action"] == "promote"
        assert "high" in result[0].get("priority", "")

    def test_finding_program(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        result = sub.candidates([self._make_sensed("finding")])
        assert result[0]["action"] == "program"

    def test_project_migrate(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        result = sub.candidates([self._make_sensed("project")])
        assert result[0]["action"] == "migrate"

    def test_dead_candidate(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        result = sub.candidates([self._make_sensed("finding")])
        assert result[0].get("dead") is True

    def test_user_already_promoted(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        result = sub.candidates([self._make_sensed("user", overlap_size=7)])
        assert result[0]["action"] == "already_promoted"

    def test_unknown_type(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        result = sub.candidates([self._make_sensed("random_type")])
        assert result[0]["action"] == "unknown"


# ---------------------------------------------------------------------------
# ConsolidationSubstrate.act
# ---------------------------------------------------------------------------


class TestAct:
    def test_prune(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        msg = sub.act({"name": "x", "action": "promote", "dead": True})
        assert msg.startswith("prune candidate")

    def test_already_promoted(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        msg = sub.act(
            {"name": "x", "action": "already_promoted", "constitution_overlap": {"a", "b"}}
        )
        assert "already promoted" in msg

    def test_promote(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        msg = sub.act({"name": "x", "action": "promote"})
        assert "promote to constitution" in msg

    def test_promote_with_priority(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        msg = sub.act({"name": "x", "action": "promote", "priority": "high"})
        assert "[high]" in msg

    def test_program(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        msg = sub.act({"name": "x", "action": "program"})
        assert "program candidate" in msg

    def test_migrate(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        msg = sub.act(
            {
                "name": "x",
                "action": "migrate",
                "target": ("Chromatin", "Project state"),
            }
        )
        assert "migrate to Chromatin" in msg

    def test_unknown_action(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        msg = sub.act({"name": "x", "action": "unknown", "type": "foo"})
        assert "review" in msg


# ---------------------------------------------------------------------------
# ConsolidationSubstrate.report
# ---------------------------------------------------------------------------


class TestReport:
    def test_report_format(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        sensed = [{"type": "feedback"}, {"type": "finding"}]
        acted = ["promote to constitution: alpha", "program candidate: beta"]
        report = sub.report(sensed, acted)
        assert "2 file(s) sensed" in report
        assert "Promote:" in report
        assert "Program:" in report
        assert "Summary:" in report

    def test_report_empty(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        report = sub.report([], [])
        assert "0 file(s) sensed" in report
