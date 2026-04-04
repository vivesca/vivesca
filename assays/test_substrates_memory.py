"""Tests for metabolon.metabolism.substrates.memory."""

from __future__ import annotations

from unittest.mock import MagicMock

from metabolon.metabolism.signals import SensorySystem, Stimulus
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
    def test_extracts_yaml_keys(self):
        text = "---\nname: my-memory\ntype: feedback\n---\nBody text."
        result = _parse_frontmatter(text)
        assert result == {"name": "my-memory", "type": "feedback"}

    def test_empty_string(self):
        assert _parse_frontmatter("") == {}

    def test_no_frontmatter(self):
        assert _parse_frontmatter("Just a plain doc\nNo yaml here") == {}

    def test_extra_whitespace(self):
        text = "---\n  name  :  spaced  \n---\n"
        result = _parse_frontmatter(text)
        assert result["name"] == "spaced"


# ---------------------------------------------------------------------------
# _keyword_overlap
# ---------------------------------------------------------------------------


class TestKeywordOverlap:
    def test_finds_shared_words(self):
        overlap = _keyword_overlap("terraform plan applies", "terraform destroy plan")
        assert "terraform" in overlap
        assert "plan" in overlap

    def test_no_overlap(self):
        overlap = _keyword_overlap("alpha beta gamma", "delta epsilon zeta")
        assert overlap == set()

    def test_min_word_len_filters(self):
        overlap = _keyword_overlap("big database cluster", "big database system", min_word_len=5)
        assert "database" in overlap
        assert "big" not in overlap

    def test_case_insensitive(self):
        overlap = _keyword_overlap("Terraform Plan", "terraform plan")
        assert "terraform" in overlap
        assert "plan" in overlap


# ---------------------------------------------------------------------------
# ConsolidationSubstrate.sense
# ---------------------------------------------------------------------------


class TestSense:
    def test_returns_empty_when_dir_missing(self, tmp_path):
        sub = ConsolidationSubstrate(
            memory_dir=tmp_path / "nope",
            constitution_path=tmp_path / "const.md",
            collector=SensorySystem(tmp_path / "signals.jsonl"),
        )
        assert sub.sense() == []

    def test_returns_empty_when_no_md_files(self, tmp_path):
        memory_dir = tmp_path / "mem"
        memory_dir.mkdir()
        sub = ConsolidationSubstrate(
            memory_dir=memory_dir,
            constitution_path=tmp_path / "const.md",
            collector=SensorySystem(tmp_path / "signals.jsonl"),
        )
        assert sub.sense() == []

    def test_senses_memory_files(self, tmp_path):
        memory_dir = tmp_path / "mem"
        memory_dir.mkdir()
        (memory_dir / "001.md").write_text(
            "---\nname: hook-check\ntype: finding\n---\nAlways run hooks before push."
        )
        (memory_dir / "MEMORY.md").write_text("# Index\n")  # should be excluded

        collector = MagicMock(spec=SensorySystem)
        collector.recall_since.return_value = []

        sub = ConsolidationSubstrate(
            memory_dir=memory_dir,
            constitution_path=tmp_path / "const.md",
            collector=collector,
        )
        results = sub.sense()

        assert len(results) == 1
        assert results[0]["name"] == "hook-check"
        assert results[0]["type"] == "finding"
        assert results[0]["signal_match"] is False

    def test_detects_signal_match(self, tmp_path):
        memory_dir = tmp_path / "mem"
        memory_dir.mkdir()
        (memory_dir / "002.md").write_text(
            "---\nname: deploy-note\ntype: project\n---\nUse terraform apply in CI."
        )

        stim = Stimulus(tool="terraform_apply", outcome="success")
        collector = MagicMock(spec=SensorySystem)
        collector.recall_since.return_value = [stim]

        sub = ConsolidationSubstrate(
            memory_dir=memory_dir,
            constitution_path=tmp_path / "const.md",
            collector=collector,
        )
        results = sub.sense()
        assert results[0]["signal_match"] is True

    def test_detects_constitution_overlap(self, tmp_path):
        memory_dir = tmp_path / "mem"
        memory_dir.mkdir()
        (memory_dir / "003.md").write_text(
            "---\nname: pref\ntype: user\n---\nI prefer pytest over unittest."
        )
        (tmp_path / "const.md").write_text("Always use pytest for testing.")

        collector = MagicMock(spec=SensorySystem)
        collector.recall_since.return_value = []

        sub = ConsolidationSubstrate(
            memory_dir=memory_dir,
            constitution_path=tmp_path / "const.md",
            collector=collector,
        )
        results = sub.sense()
        assert "pytest" in results[0]["constitution_overlap"]


# ---------------------------------------------------------------------------
# ConsolidationSubstrate.candidates
# ---------------------------------------------------------------------------


class TestCandidates:
    def _make_mem(self, type_: str, overlap: set[str] | None = None, signal: bool = False) -> dict:
        return {
            "path": "/fake.md",
            "name": "test-mem",
            "description": "",
            "type": type_,
            "text": "body",
            "target": CONSOLIDATION_PATHWAYS.get(type_, ("Unknown", "")),
            "constitution_overlap": overlap if overlap is not None else set(),
            "signal_match": signal,
        }

    def test_feedback_high_overlap_already_promoted(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        mem = self._make_mem(
            "feedback", overlap={"pytest", "always", "testing", "session", "config"}
        )
        results = sub.candidates([mem])
        assert results[0]["action"] == "already_promoted"

    def test_feedback_with_signal_high_priority(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        mem = self._make_mem("feedback", signal=True)
        results = sub.candidates([mem])
        assert results[0]["action"] == "promote"
        assert "high" in results[0].get("priority", "")

    def test_finding_action_program(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        mem = self._make_mem("finding")
        results = sub.candidates([mem])
        assert results[0]["action"] == "program"

    def test_project_action_migrate(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        mem = self._make_mem("project")
        results = sub.candidates([mem])
        assert results[0]["action"] == "migrate"

    def test_reference_action_migrate(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        mem = self._make_mem("reference")
        results = sub.candidates([mem])
        assert results[0]["action"] == "migrate"

    def test_user_low_overlap_promote(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        mem = self._make_mem("user", overlap=set())
        results = sub.candidates([mem])
        assert results[0]["action"] == "promote"

    def test_dead_flag_when_no_overlap_no_signal(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        mem = self._make_mem("finding", overlap=set(), signal=False)
        results = sub.candidates([mem])
        assert results[0].get("dead") is True

    def test_unknown_type(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        mem = self._make_mem("random_type")
        results = sub.candidates([mem])
        assert results[0]["action"] == "unknown"


# ---------------------------------------------------------------------------
# ConsolidationSubstrate.act
# ---------------------------------------------------------------------------


class TestAct:
    def test_prune_candidate(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        candidate = {"action": "promote", "name": "stale-mem", "dead": True, "type": "feedback"}
        result = sub.act(candidate)
        assert result.startswith("prune candidate: stale-mem")

    def test_already_promoted(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        candidate = {
            "action": "already_promoted",
            "name": "done",
            "constitution_overlap": {"pytest", "always"},
            "type": "feedback",
        }
        result = sub.act(candidate)
        assert "already promoted" in result
        assert "2 keywords" in result

    def test_promote_with_priority(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        candidate = {
            "action": "promote",
            "name": "hot-item",
            "priority": "high (signal evidence)",
            "type": "feedback",
        }
        result = sub.act(candidate)
        assert "promote to constitution" in result
        assert "high (signal evidence)" in result

    def test_program_candidate(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        candidate = {"action": "program", "name": "hook-rule", "type": "finding"}
        result = sub.act(candidate)
        assert result.startswith("program candidate: hook-rule")

    def test_migrate_includes_target(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        candidate = {
            "action": "migrate",
            "name": "arch-note",
            "type": "project",
            "target": ("Chromatin note", "Project state belongs in source of truth"),
        }
        result = sub.act(candidate)
        assert "migrate to Chromatin note" in result

    def test_unknown_action_reviews(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        candidate = {"action": "unknown", "name": "odd", "type": "mystery"}
        result = sub.act(candidate)
        assert result.startswith("review:")


# ---------------------------------------------------------------------------
# ConsolidationSubstrate.report
# ---------------------------------------------------------------------------


class TestReport:
    def test_report_format(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        sensed = [
            {"type": "feedback", "name": "a"},
            {"type": "finding", "name": "b"},
            {"type": "feedback", "name": "c"},
        ]
        acted = [
            "promote to constitution: a",
            "program candidate: b",
            "already promoted: c (overlap: 0 keywords)",
        ]
        report = sub.report(sensed, acted)
        assert "3 file(s) sensed" in report
        assert "feedback: 2" in report
        assert "finding: 1" in report
        assert "Summary: 1 to promote" in report
        assert "1 already promoted" in report
        assert "1 to program" in report

    def test_empty_report(self):
        sub = ConsolidationSubstrate.__new__(ConsolidationSubstrate)
        report = sub.report([], [])
        assert "0 file(s) sensed" in report
