from __future__ import annotations

"""Comprehensive tests for ConsolidationSubstrate (memory.py)."""


from datetime import UTC, datetime
from unittest.mock import MagicMock

from metabolon.metabolism.signals import Outcome, Stimulus
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
    def test_valid_frontmatter(self):
        text = "---\nname: test-memory\ntype: feedback\n---\nBody here."
        result = _parse_frontmatter(text)
        assert result == {"name": "test-memory", "type": "feedback"}

    def test_no_frontmatter(self):
        text = "Just a regular file with no frontmatter."
        assert _parse_frontmatter(text) == {}

    def test_empty_frontmatter(self):
        text = "---\n---\nBody."
        result = _parse_frontmatter(text)
        assert result == {}

    def test_single_dash_lines(self):
        text = "---\ntype: finding\n---\nSome content"
        result = _parse_frontmatter(text)
        assert result["type"] == "finding"

    def test_extra_whitespace_in_values(self):
        text = "---\n  name :   spaced name  \n---\n"
        result = _parse_frontmatter(text)
        assert result["name"] == "spaced name"

    def test_multiple_keys(self):
        text = "---\nname: abc\ntype: user\ndescription: a desc\n---\n"
        result = _parse_frontmatter(text)
        assert len(result) == 3
        assert result["description"] == "a desc"

    def test_value_with_colon(self):
        text = "---\nname: key\nvalue: has: colon\n---\n"
        result = _parse_frontmatter(text)
        assert result["value"] == "has: colon"


# ---------------------------------------------------------------------------
# _keyword_overlap
# ---------------------------------------------------------------------------


class TestKeywordOverlap:
    def test_basic_overlap(self):
        result = _keyword_overlap("testing memory files", "memory files are great")
        assert "memory" in result
        assert "files" in result

    def test_no_overlap(self):
        result = _keyword_overlap("alpha beta gamma", "delta epsilon zeta")
        assert result == set()

    def test_case_insensitive(self):
        result = _keyword_overlap("Python Testing", "python testing")
        assert "python" in result
        assert "testing" in result

    def test_min_word_len_filter(self):
        # words < 4 chars should be excluded
        result = _keyword_overlap("the cat sat", "the cat hat")
        assert result == set()

    def test_min_word_len_custom(self):
        result = _keyword_overlap("cat dog", "cat dog", min_word_len=3)
        assert "cat" in result
        assert "dog" in result

    def test_alphanumeric_words(self):
        result = _keyword_overlap("tool_abc something", "tool_abc else")
        assert "tool_abc" in result

    def test_empty_strings(self):
        assert _keyword_overlap("", "") == set()

    def test_one_empty(self):
        assert _keyword_overlap("hello world", "") == set()


# ---------------------------------------------------------------------------
# ConsolidationSubstrate.__init__
# ---------------------------------------------------------------------------


class TestInit:
    def test_custom_paths(self, tmp_path):
        mem_dir = tmp_path / "mem"
        const_path = tmp_path / "genome.md"
        collector = MagicMock()
        s = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=const_path,
            collector=collector,
        )
        assert s.memory_dir == mem_dir
        assert s.constitution_path == const_path
        assert s.collector is collector

    def test_defaults(self):
        s = ConsolidationSubstrate()
        assert s.memory_dir.name == "memory"
        assert s.constitution_path.name == "genome.md"
        assert s.name == "memory"

    def test_name_attribute(self):
        assert ConsolidationSubstrate.name == "memory"


# ---------------------------------------------------------------------------
# sense
# ---------------------------------------------------------------------------


class TestSense:
    def test_missing_memory_dir(self, tmp_path):
        s = ConsolidationSubstrate(
            memory_dir=tmp_path / "nonexistent",
            constitution_path=tmp_path / "genome.md",
            collector=MagicMock(),
        )
        assert s.sense() == []

    def test_empty_memory_dir(self, tmp_path):
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        s = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "genome.md",
            collector=MagicMock(),
        )
        assert s.sense() == []

    def test_ignores_memory_md_file(self, tmp_path):
        """MEMORY.md should be excluded from sensing."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "MEMORY.md").write_text("# Index\n")
        s = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "genome.md",
            collector=MagicMock(),
        )
        assert s.sense() == []

    def test_senses_single_file(self, tmp_path):
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "test-feedback.md").write_text(
            "---\nname: my-feedback\ntype: feedback\n---\nSome feedback body."
        )
        collector = MagicMock()
        collector.recall_since.return_value = []

        s = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "genome.md",
            collector=collector,
        )
        result = s.sense()

        assert len(result) == 1
        assert result[0]["name"] == "my-feedback"
        assert result[0]["type"] == "feedback"
        assert result[0]["description"] == ""
        assert isinstance(result[0]["constitution_overlap"], set)
        assert result[0]["signal_match"] is False

    def test_senses_multiple_files_sorted(self, tmp_path):
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "z-mem.md").write_text("---\ntype: user\n---\nZ")
        (mem_dir / "a-mem.md").write_text("---\ntype: project\n---\nA")

        collector = MagicMock()
        collector.recall_since.return_value = []

        s = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "genome.md",
            collector=collector,
        )
        result = s.sense()
        assert len(result) == 2
        # sorted by filename
        assert result[0]["name"] == "a-mem"
        assert result[1]["name"] == "z-mem"

    def test_constitution_overlap_detected(self, tmp_path):
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "overlap.md").write_text(
            "---\ntype: feedback\n---\nTesting memory consolidation rules."
        )

        constitution = tmp_path / "genome.md"
        constitution.write_text("Memory consolidation rules for testing purposes.")

        collector = MagicMock()
        collector.recall_since.return_value = []

        s = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=constitution,
            collector=collector,
        )
        result = s.sense()
        overlap = result[0]["constitution_overlap"]
        # Should find overlapping significant words
        assert isinstance(overlap, set)
        assert len(overlap) > 0
        assert "memory" in overlap
        assert "consolidation" in overlap

    def test_signal_match_from_tool_names(self, tmp_path):
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        # Include text with a tool name
        (mem_dir / "tool-mem.md").write_text(
            "---\ntype: finding\n---\nUse Bash tool for running scripts."
        )

        collector = MagicMock()
        signal = Stimulus(
            ts=datetime.now(UTC),
            tool="Bash",
            outcome=Outcome.success,
        )
        collector.recall_since.return_value = [signal]

        s = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "genome.md",
            collector=collector,
        )
        result = s.sense()
        assert result[0]["signal_match"] is True

    def test_signal_match_from_tool_prefix(self, tmp_path):
        """Tools with underscores contribute their prefix to enzyme set."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "sig.md").write_text("---\ntype: finding\n---\nUsing Write for output.")

        collector = MagicMock()
        signal = Stimulus(
            ts=datetime.now(UTC),
            tool="Write_file",
            outcome=Outcome.success,
        )
        collector.recall_since.return_value = [signal]

        s = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "genome.md",
            collector=collector,
        )
        result = s.sense()
        # "write" from "Write_file" prefix should match "Write" in the text
        assert result[0]["signal_match"] is True

    def test_no_signal_match(self, tmp_path):
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "nosig.md").write_text(
            "---\ntype: feedback\n---\nCompletely unrelated content."
        )

        collector = MagicMock()
        collector.recall_since.return_value = []

        s = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "genome.md",
            collector=collector,
        )
        result = s.sense()
        assert result[0]["signal_match"] is False

    def test_unknown_type_has_default_target(self, tmp_path):
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "weird.md").write_text("---\ntype: unknown_thing\n---\n")

        collector = MagicMock()
        collector.recall_since.return_value = []

        s = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "genome.md",
            collector=collector,
        )
        result = s.sense()
        assert result[0]["target"] == ("Unknown", "No migration rule for this type")

    def test_target_matches_pathway(self, tmp_path):
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "ref.md").write_text("---\ntype: reference\n---\n")

        collector = MagicMock()
        collector.recall_since.return_value = []

        s = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "genome.md",
            collector=collector,
        )
        result = s.sense()
        assert result[0]["target"] == CONSOLIDATION_PATHWAYS["reference"]

    def test_file_without_frontmatter(self, tmp_path):
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "bare.md").write_text("No frontmatter here, just text.")

        collector = MagicMock()
        collector.recall_since.return_value = []

        s = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "genome.md",
            collector=collector,
        )
        result = s.sense()
        assert len(result) == 1
        assert result[0]["type"] == "unknown"
        assert result[0]["name"] == "bare"  # falls back to stem


# ---------------------------------------------------------------------------
# candidates
# ---------------------------------------------------------------------------


class TestCandidates:
    def _make_mem(self, **overrides):
        base = {
            "path": "/fake/path.md",
            "name": "test",
            "description": "",
            "type": "feedback",
            "text": "some text",
            "target": ("Constitution", "desc"),
            "constitution_overlap": set(),
            "signal_match": False,
        }
        base.update(overrides)
        return base

    def test_empty_sensed(self):
        s = ConsolidationSubstrate()
        assert s.candidates([]) == []

    # -- feedback --

    def test_feedback_high_overlap_already_promoted(self):
        s = ConsolidationSubstrate()
        mem = self._make_mem(type="feedback", constitution_overlap={"a", "b", "c", "d", "e"})
        results = s.candidates([mem])
        assert results[0]["action"] == "already_promoted"

    def test_feedback_with_signal_high_priority(self):
        s = ConsolidationSubstrate()
        mem = self._make_mem(type="feedback", signal_match=True)
        results = s.candidates([mem])
        assert results[0]["action"] == "promote"
        assert results[0]["priority"] == "high (signal evidence)"

    def test_feedback_plain_promote(self):
        s = ConsolidationSubstrate()
        mem = self._make_mem(type="feedback")
        results = s.candidates([mem])
        assert results[0]["action"] == "promote"
        assert "priority" not in results[0]

    # -- finding --

    def test_finding_with_signal_program(self):
        s = ConsolidationSubstrate()
        mem = self._make_mem(type="finding", signal_match=True)
        results = s.candidates([mem])
        assert results[0]["action"] == "program"
        assert results[0]["priority"] == "high (signal evidence)"

    def test_finding_plain_program(self):
        s = ConsolidationSubstrate()
        mem = self._make_mem(type="finding")
        results = s.candidates([mem])
        assert results[0]["action"] == "program"
        assert "priority" not in results[0]

    # -- project / reference --

    def test_project_migrate(self):
        s = ConsolidationSubstrate()
        mem = self._make_mem(type="project")
        results = s.candidates([mem])
        assert results[0]["action"] == "migrate"

    def test_reference_migrate(self):
        s = ConsolidationSubstrate()
        mem = self._make_mem(type="reference")
        results = s.candidates([mem])
        assert results[0]["action"] == "migrate"

    # -- user --

    def test_user_high_overlap_already_promoted(self):
        s = ConsolidationSubstrate()
        mem = self._make_mem(type="user", constitution_overlap={"a", "b", "c", "d", "e"})
        results = s.candidates([mem])
        assert results[0]["action"] == "already_promoted"

    def test_user_promote(self):
        s = ConsolidationSubstrate()
        mem = self._make_mem(type="user")
        results = s.candidates([mem])
        assert results[0]["action"] == "promote"

    # -- unknown --

    def test_unknown_type(self):
        s = ConsolidationSubstrate()
        mem = self._make_mem(type="random_type")
        results = s.candidates([mem])
        assert results[0]["action"] == "unknown"

    # -- dead flag --

    def test_dead_no_overlap_no_signal(self):
        s = ConsolidationSubstrate()
        mem = self._make_mem(type="feedback", constitution_overlap=set(), signal_match=False)
        results = s.candidates([mem])
        assert results[0].get("dead") is True

    def test_not_dead_with_signal(self):
        s = ConsolidationSubstrate()
        mem = self._make_mem(type="feedback", signal_match=True)
        results = s.candidates([mem])
        assert "dead" not in results[0]

    def test_not_dead_with_overlap(self):
        s = ConsolidationSubstrate()
        mem = self._make_mem(type="feedback", constitution_overlap={"alpha", "beta"})
        results = s.candidates([mem])
        assert "dead" not in results[0]

    def test_already_promoted_not_dead_even_if_no_overlap_no_signal(self):
        """already_promoted should not be flagged dead."""
        s = ConsolidationSubstrate()
        mem = self._make_mem(
            type="feedback",
            constitution_overlap={"a", "b", "c", "d", "e"},
            signal_match=False,
        )
        results = s.candidates([mem])
        assert results[0]["action"] == "already_promoted"
        assert "dead" not in results[0]

    def test_multiple_candidates(self):
        s = ConsolidationSubstrate()
        m1 = self._make_mem(name="fb", type="feedback", signal_match=True)
        m2 = self._make_mem(name="pr", type="project")
        m3 = self._make_mem(name="fd", type="finding")
        results = s.candidates([m1, m2, m3])
        assert len(results) == 3
        assert results[0]["action"] == "promote"
        assert results[1]["action"] == "migrate"
        assert results[2]["action"] == "program"


# ---------------------------------------------------------------------------
# act
# ---------------------------------------------------------------------------


class TestAct:
    def test_prune_dead(self):
        s = ConsolidationSubstrate()
        result = s.act(
            {
                "name": "stale",
                "action": "promote",
                "dead": True,
                "constitution_overlap": set(),
            }
        )
        assert result.startswith("prune candidate: stale")
        assert "no signal or constitution evidence" in result

    def test_already_promoted(self):
        s = ConsolidationSubstrate()
        result = s.act(
            {
                "name": "old",
                "action": "already_promoted",
                "constitution_overlap": {"a", "b", "c", "d", "e"},
            }
        )
        assert result.startswith("already promoted: old")
        assert "overlap: 5 keywords" in result

    def test_promote_with_priority(self):
        s = ConsolidationSubstrate()
        result = s.act(
            {
                "name": "hot",
                "action": "promote",
                "priority": "high (signal evidence)",
            }
        )
        assert result == "promote to constitution: hot [high (signal evidence)]"

    def test_promote_without_priority(self):
        s = ConsolidationSubstrate()
        result = s.act({"name": "cool", "action": "promote"})
        assert result == "promote to constitution: cool"

    def test_program_with_priority(self):
        s = ConsolidationSubstrate()
        result = s.act(
            {
                "name": "prog",
                "action": "program",
                "priority": "high (signal evidence)",
            }
        )
        assert result == "program candidate: prog [high (signal evidence)]"

    def test_program_without_priority(self):
        s = ConsolidationSubstrate()
        result = s.act({"name": "prog", "action": "program"})
        assert result == "program candidate: prog"

    def test_migrate(self):
        s = ConsolidationSubstrate()
        result = s.act(
            {
                "name": "ref-doc",
                "action": "migrate",
                "target": ("tool-index.md or skill file", "Pointers belong where the action is"),
            }
        )
        assert "migrate to tool-index.md or skill file: ref-doc" in result
        assert "Pointers belong where the action is" in result

    def test_unknown_action_falls_back(self):
        s = ConsolidationSubstrate()
        result = s.act({"name": "mystery", "action": "unknown", "type": "weird"})
        assert result == "review: mystery (type=weird)"

    def test_no_action_key(self):
        s = ConsolidationSubstrate()
        result = s.act({"name": "bare", "type": "feedback"})
        assert result.startswith("review:")


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


class TestReport:
    def test_empty_sensed_no_actions(self):
        s = ConsolidationSubstrate()
        report = s.report([], [])
        assert "0 file(s) sensed" in report
        assert "Summary:" in report

    def test_with_types(self):
        s = ConsolidationSubstrate()
        sensed = [
            {"type": "feedback"},
            {"type": "feedback"},
            {"type": "finding"},
        ]
        report = s.report(sensed, [])
        assert "feedback: 2" in report
        assert "finding: 1" in report
        assert "Constitution" in report  # target for feedback

    def test_with_actions(self):
        s = ConsolidationSubstrate()
        sensed = [{"type": "feedback"}]
        acted = [
            "promote to constitution: mem1 [high (signal evidence)]",
            "already promoted: mem2 (overlap: 6 keywords)",
            "program candidate: mem3",
            "migrate to Chromatin: mem4 (rationale)",
            "prune candidate: mem5 (no signal or constitution evidence)",
        ]
        report = s.report(sensed, acted)
        assert "Promote:" in report
        assert "Already promoted:" in report
        assert "Program:" in report
        assert "Migrate:" in report
        assert "Prune:" in report

    def test_summary_counts(self):
        s = ConsolidationSubstrate()
        acted = [
            "promote to constitution: a",
            "promote to constitution: b",
            "already promoted: c",
            "program candidate: d",
            "migrate to X: e",
            "prune candidate: f",
        ]
        report = s.report([], acted)
        assert "2 to promote" in report
        assert "1 already promoted" in report
        assert "1 to program" in report
        assert "1 to migrate" in report
        assert "1 to prune" in report

    def test_other_actions(self):
        s = ConsolidationSubstrate()
        acted = ["review: something (type=unknown)"]
        report = s.report([], acted)
        assert "Other:" in report
        assert "review: something" in report

    def test_no_actions_section_when_empty(self):
        s = ConsolidationSubstrate()
        report = s.report([{"type": "feedback"}], [])
        assert "-- Actions --" not in report

    def test_type_with_unknown_pathway(self):
        s = ConsolidationSubstrate()
        sensed = [{"type": "mystery_type"}]
        report = s.report(sensed, [])
        assert "mystery_type: 1" in report
        assert "Unknown" in report


# ---------------------------------------------------------------------------
# Integration: sense → candidates → act → report pipeline
# ---------------------------------------------------------------------------


class TestPipeline:
    def test_full_pipeline(self, tmp_path):
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()

        # Create memory files
        (mem_dir / "feedback-1.md").write_text(
            "---\nname: good-feedback\ntype: feedback\n---\nAlways verify tests pass."
        )
        (mem_dir / "finding-1.md").write_text(
            "---\nname: bash-finding\ntype: finding\n---\nBash tool usage pattern."
        )
        (mem_dir / "project-1.md").write_text(
            "---\nname: old-project\ntype: project\n---\nLegacy project notes."
        )
        (mem_dir / "stale-1.md").write_text(
            "---\nname: stale-note\ntype: feedback\n---\nTotally irrelevant orphan words."
        )

        constitution = tmp_path / "genome.md"
        constitution.write_text("Always verify tests pass in the constitution.")

        collector = MagicMock()
        signal = Stimulus(
            ts=datetime.now(UTC),
            tool="Bash",
            outcome=Outcome.success,
        )
        collector.recall_since.return_value = [signal]

        sub = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=constitution,
            collector=collector,
        )

        # sense
        sensed = sub.sense()
        assert len(sensed) == 4

        # candidates
        candidates = sub.candidates(sensed)
        assert len(candidates) == 4

        # act
        acted = [sub.act(c) for c in candidates]
        assert all(isinstance(a, str) for a in acted)

        # report
        report = sub.report(sensed, acted)
        assert "4 file(s) sensed" in report
        assert "Summary:" in report
