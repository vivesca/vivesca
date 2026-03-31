"""Tests for ConsolidationSubstrate — memory file metabolism."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from metabolon.metabolism.substrates.memory import (
    _parse_frontmatter,
    _keyword_overlap,
    CONSOLIDATION_PATHWAYS,
    ConsolidationSubstrate,
)


class TestConsolidationPathways:
    def test_pathways_defined(self):
        assert "feedback" in CONSOLIDATION_PATHWAYS
        assert "finding" in CONSOLIDATION_PATHWAYS
        assert "user" in CONSOLIDATION_PATHWAYS
        assert "project" in CONSOLIDATION_PATHWAYS
        assert "reference" in CONSOLIDATION_PATHWAYS

    def test_pathway_structure(self):
        for key, value in CONSOLIDATION_PATHWAYS.items():
            assert isinstance(value, tuple)
            assert len(value) == 2
            target, rationale = value
            assert isinstance(target, str)
            assert isinstance(rationale, str)


class TestParseFrontmatter:
    def test_extracts_yaml_frontmatter(self):
        text = """---
name: test
type: feedback
---
# Content here"""
        result = _parse_frontmatter(text)
        assert result["name"] == "test"
        assert result["type"] == "feedback"

    def test_handles_missing_frontmatter(self):
        text = "# No frontmatter here"
        result = _parse_frontmatter(text)
        assert result == {}

    def test_handles_partial_frontmatter(self):
        text = "---\nname: test\n---"
        result = _parse_frontmatter(text)
        assert result["name"] == "test"

    def test_handles_empty_frontmatter(self):
        text = "---\n---\nContent"
        result = _parse_frontmatter(text)
        assert result == {}

    def test_handles_multiline_values(self):
        text = """---
name: test
description: This is a long description
---
Content"""
        result = _parse_frontmatter(text)
        assert result["name"] == "test"
        assert result["description"] == "This is a long description"


class TestKeywordOverlap:
    def test_finds_common_words(self):
        text_a = "The quick brown fox jumps"
        text_b = "The lazy brown dog sleeps"
        result = _keyword_overlap(text_a, text_b)
        assert "the" in result  # case insensitive
        assert "brown" in result

    def test_respects_min_word_len(self):
        text_a = "a big cat sat"
        text_b = "a big dog ran"
        # Default min_word_len=4, so "a", "big" should be excluded
        result = _keyword_overlap(text_a, text_b, min_word_len=4)
        assert result == set()  # "a" and "big" are too short

    def test_returns_empty_for_no_overlap(self):
        text_a = "apple orange banana"
        text_b = "carrot potato tomato"
        result = _keyword_overlap(text_a, text_b)
        assert result == set()

    def test_handles_alphanumeric(self):
        text_a = "python3 and nodejs"
        text_b = "python3 is great"
        result = _keyword_overlap(text_a, text_b)
        assert "python3" in result


class TestConsolidationSubstrateInit:
    def test_default_paths(self):
        sub = ConsolidationSubstrate()
        assert "memory" in str(sub.memory_dir)
        assert "genome.md" in str(sub.constitution_path)

    def test_custom_paths(self, tmp_path: Path):
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        constitution = tmp_path / "genome.md"
        constitution.write_text("# Constitution")

        sub = ConsolidationSubstrate(
            memory_dir=memory_dir,
            constitution_path=constitution,
        )
        assert sub.memory_dir == memory_dir
        assert sub.constitution_path == constitution


class TestSense:
    def test_missing_memory_dir_returns_empty(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "nonexistent",
            constitution_path=tmp_path / "genome.md",
        )
        result = sub.sense(days=30)
        assert result == []

    def test_empty_memory_dir_returns_empty(self, tmp_path: Path):
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()

        sub = ConsolidationSubstrate(
            memory_dir=memory_dir,
            constitution_path=tmp_path / "genome.md",
        )
        result = sub.sense(days=30)
        assert result == []

    def test_parses_memory_files(self, tmp_path: Path):
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "test1.md").write_text("""---
name: Test Memory
type: feedback
description: A test memory
---
# Test content here
""")

        sub = ConsolidationSubstrate(
            memory_dir=memory_dir,
            constitution_path=tmp_path / "genome.md",
        )

        # Mock the collector to return empty signals
        mock_collector = MagicMock()
        mock_collector.recall_since.return_value = []
        sub.collector = mock_collector

        result = sub.sense(days=30)
        assert len(result) == 1
        assert result[0]["name"] == "Test Memory"
        assert result[0]["type"] == "feedback"

    def test_excludes_memory_md(self, tmp_path: Path):
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "MEMORY.md").write_text("# Index")
        (memory_dir / "test.md").write_text("---\nname: test\n---\nContent")

        sub = ConsolidationSubstrate(
            memory_dir=memory_dir,
            constitution_path=tmp_path / "genome.md",
        )
        mock_collector = MagicMock()
        mock_collector.recall_since.return_value = []
        sub.collector = mock_collector

        result = sub.sense(days=30)
        # MEMORY.md should be excluded
        names = [r["name"] for r in result]
        assert "MEMORY" not in names

    def test_detects_constitution_overlap(self, tmp_path: Path):
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        constitution = tmp_path / "genome.md"
        constitution.write_text("Always run tests before committing. Testing is important.")

        (memory_dir / "test.md").write_text("""---
name: Testing Rule
type: feedback
---
Always run tests before pushing. Testing matters.
""")

        sub = ConsolidationSubstrate(
            memory_dir=memory_dir,
            constitution_path=constitution,
        )
        mock_collector = MagicMock()
        mock_collector.recall_since.return_value = []
        sub.collector = mock_collector

        result = sub.sense(days=30)
        assert len(result) == 1
        overlap = result[0]["constitution_overlap"]
        assert "test" in overlap or "tests" in overlap or "testing" in overlap

    def test_detects_signal_match(self, tmp_path: Path):
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()

        (memory_dir / "test.md").write_text("""---
name: Bash Rule
type: feedback
---
Use bash carefully.
""")

        sub = ConsolidationSubstrate(
            memory_dir=memory_dir,
            constitution_path=tmp_path / "genome.md",
        )

        # Mock signal with bash tool
        mock_signal = MagicMock()
        mock_signal.tool = "Bash"
        mock_collector = MagicMock()
        mock_collector.recall_since.return_value = [mock_signal]
        sub.collector = mock_collector

        result = sub.sense(days=30)
        assert result[0]["signal_match"] is True

    def test_handles_unknown_type(self, tmp_path: Path):
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()

        (memory_dir / "test.md").write_text("""---
name: Unknown
type: weird_type
---
Content
""")

        sub = ConsolidationSubstrate(
            memory_dir=memory_dir,
            constitution_path=tmp_path / "genome.md",
        )
        mock_collector = MagicMock()
        mock_collector.recall_since.return_value = []
        sub.collector = mock_collector

        result = sub.sense(days=30)
        assert result[0]["type"] == "weird_type"
        assert result[0]["target"] == ("Unknown", "No migration rule for this type")


class TestCandidates:
    def test_feedback_with_high_overlap_already_promoted(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        sensed = [{
            "name": "test",
            "type": "feedback",
            "constitution_overlap": {"word1", "word2", "word3", "word4", "word5"},
            "signal_match": False,
        }]
        result = sub.candidates(sensed)
        assert result[0]["action"] == "already_promoted"

    def test_feedback_with_signal_high_priority(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        sensed = [{
            "name": "test",
            "type": "feedback",
            "constitution_overlap": set(),
            "signal_match": True,
        }]
        result = sub.candidates(sensed)
        assert result[0]["action"] == "promote"
        assert "high" in result[0]["priority"]

    def test_finding_with_signal_becomes_program(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        sensed = [{
            "name": "test",
            "type": "finding",
            "constitution_overlap": set(),
            "signal_match": True,
        }]
        result = sub.candidates(sensed)
        assert result[0]["action"] == "program"
        assert "high" in result[0]["priority"]

    def test_project_becomes_migrate(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        sensed = [{
            "name": "test",
            "type": "project",
            "constitution_overlap": set(),
            "signal_match": False,
            "target": ("Chromatin note", "Project state"),
        }]
        result = sub.candidates(sensed)
        assert result[0]["action"] == "migrate"

    def test_reference_becomes_migrate(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        sensed = [{
            "name": "test",
            "type": "reference",
            "constitution_overlap": set(),
            "signal_match": False,
            "target": ("tool-index.md", "Pointers"),
        }]
        result = sub.candidates(sensed)
        assert result[0]["action"] == "migrate"

    def test_user_with_overlap_already_promoted(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        sensed = [{
            "name": "test",
            "type": "user",
            "constitution_overlap": {"a", "b", "c", "d", "e", "f"},
            "signal_match": False,
        }]
        result = sub.candidates(sensed)
        assert result[0]["action"] == "already_promoted"

    def test_marks_dead_candidates(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        sensed = [{
            "name": "test",
            "type": "feedback",
            "constitution_overlap": set(),
            "signal_match": False,
        }]
        result = sub.candidates(sensed)
        assert result[0].get("dead") is True

    def test_does_not_mark_already_promoted_as_dead(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        sensed = [{
            "name": "test",
            "type": "feedback",
            "constitution_overlap": {"a", "b", "c", "d", "e"},
            "signal_match": False,
        }]
        result = sub.candidates(sensed)
        assert result[0]["action"] == "already_promoted"
        assert result[0].get("dead") is not True


class TestAct:
    def test_act_dead_candidate(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        candidate = {"name": "test", "dead": True, "type": "feedback"}
        result = sub.act(candidate)
        assert "prune" in result.lower()

    def test_act_already_promoted(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        candidate = {
            "name": "test",
            "action": "already_promoted",
            "constitution_overlap": {"a", "b", "c", "d", "e"},
        }
        result = sub.act(candidate)
        assert "already promoted" in result.lower()

    def test_act_promote(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        candidate = {"name": "test", "action": "promote"}
        result = sub.act(candidate)
        assert "promote" in result.lower()

    def test_act_promote_with_priority(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        candidate = {"name": "test", "action": "promote", "priority": "high (signal evidence)"}
        result = sub.act(candidate)
        assert "promote" in result.lower()
        assert "high" in result

    def test_act_program(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        candidate = {"name": "test", "action": "program"}
        result = sub.act(candidate)
        assert "program" in result.lower()

    def test_act_migrate(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        candidate = {
            "name": "test",
            "action": "migrate",
            "target": ("Chromatin note", "Project state belongs in source of truth"),
        }
        result = sub.act(candidate)
        assert "migrate" in result.lower()
        assert "Chromatin" in result

    def test_act_unknown_type(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        candidate = {"name": "test", "action": "unknown", "type": "weird"}
        result = sub.act(candidate)
        assert "review" in result.lower()


class TestReport:
    def test_empty_report(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        report = sub.report([], [])
        assert "0 file(s) sensed" in report

    def test_report_with_sensed(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        sensed = [
            {"name": "test1", "type": "feedback", "constitution_overlap": set(), "signal_match": False},
            {"name": "test2", "type": "finding", "constitution_overlap": set(), "signal_match": True},
        ]
        report = sub.report(sensed, [])
        assert "2 file(s) sensed" in report
        assert "feedback:" in report
        assert "finding:" in report

    def test_report_with_actions(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        acted = [
            "promote to constitution: test1",
            "program candidate: test2",
            "migrate to Chromatin: test3",
            "prune candidate: test4",
        ]
        report = sub.report([], acted)
        assert "Promote:" in report
        assert "Program:" in report
        assert "Migrate:" in report
        assert "Prune:" in report

    def test_report_summary(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        acted = [
            "promote to constitution: test1",
            "already promoted: test2",
            "program candidate: test3",
            "migrate to Chromatin: test4",
            "prune candidate: test5",
        ]
        report = sub.report([], acted)
        assert "Summary:" in report
        assert "1 to promote" in report
        assert "1 already promoted" in report
        assert "1 to program" in report
        assert "1 to migrate" in report
        assert "1 to prune" in report

    def test_report_by_type(self, tmp_path: Path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "memory",
            constitution_path=tmp_path / "genome.md",
        )
        sensed = [
            {"name": "a", "type": "feedback", "constitution_overlap": set(), "signal_match": False},
            {"name": "b", "type": "feedback", "constitution_overlap": set(), "signal_match": False},
            {"name": "c", "type": "user", "constitution_overlap": set(), "signal_match": False},
        ]
        report = sub.report(sensed, [])
        assert "feedback: 2" in report
        assert "user: 1" in report
