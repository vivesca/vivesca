"""Tests for the Substrate protocol and its three implementations.

Each substrate is tested through the full sense -> candidates -> act -> report
cycle using fixture data — no real signals or filesystem state required.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from metabolon.metabolism.signals import Outcome, SensorySystem, Stimulus
from metabolon.metabolism.substrate import Substrate
from metabolon.metabolism.substrates import receptor_catalog
from metabolon.metabolism.substrates.constitution import ExecutiveSubstrate
from metabolon.metabolism.substrates.memory import ConsolidationSubstrate
from metabolon.metabolism.substrates.tools import PhenotypeSubstrate
from metabolon.metabolism.variants import Genome

# ── Helpers ──────────────────────────────────────────────────────────


def _make_signal(
    tool: str,
    outcome: Outcome = Outcome.success,
    days_ago: int = 0,
) -> Stimulus:
    s = Stimulus(
        tool=tool,
        outcome=outcome,
        substrate_consumed=100,
        product_released=50,
        response_latency=200,
    )
    if days_ago:
        s.ts = datetime.now(UTC) - timedelta(days=days_ago)
    return s


def _write_memory(
    dir: Path,
    filename: str,
    name: str,
    description: str,
    type: str,
    body: str = "",
) -> Path:
    fp = dir / filename
    fp.write_text(f"---\nname: {name}\ndescription: {description}\ntype: {type}\n---\n\n{body}\n")
    return fp


SAMPLE_CONSTITUTION = """\
# Constitution

## Core Rules

**Opus default.** Sonnet when weekly % > 70% or parallel subagents. Haiku for lookups.

**Token-conscious.** Every token that doesn't improve the output is wasted.

**Route by role, not cost.** Use fasti for calendar, noesis for search, oghma for memory.

**Lean toward doing.** Reversible + in scope = act and report.

**Debate, don't defer.** State your view, push back on disagreements.
"""


@pytest.fixture
def redirect_defaults(tmp_path):
    """Redirect SensorySystem and Genome defaults to tmp_path."""
    sig_defaults = SensorySystem.__init__.__defaults__
    var_defaults = Genome.__init__.__defaults__

    SensorySystem.__init__.__defaults__ = (tmp_path / "signals.jsonl",)
    Genome.__init__.__defaults__ = (tmp_path / "variants", 5)

    yield tmp_path

    SensorySystem.__init__.__defaults__ = sig_defaults
    Genome.__init__.__defaults__ = var_defaults


# ── Registry ─────────────────────────────────────────────────────────


class TestRegistry:
    def test_registry_contains_all_substrates(self):
        reg = receptor_catalog()
        assert "phenotype" in reg
        assert "executive" in reg
        assert "consolidation" in reg
        assert "respiration" in reg
        assert "hygiene" in reg

    def test_registry_values_are_classes(self):
        reg = receptor_catalog()
        for name, cls in reg.items():
            assert callable(cls), f"{name} should be callable"

    def test_registry_instances_have_name(self):
        reg = receptor_catalog()
        for name, cls in reg.items():
            instance = cls.__new__(cls)
            assert hasattr(instance, "name"), f"{name} should have a name attribute"


# ── Substrate Protocol ───────────────────────────────────────────────


class TestSubstrateProtocol:
    def test_tool_substrate_is_substrate(self):
        assert isinstance(PhenotypeSubstrate(), Substrate)

    def test_constitution_substrate_is_substrate(self):
        assert isinstance(ExecutiveSubstrate(), Substrate)

    def test_memory_substrate_is_substrate(self):
        assert isinstance(ConsolidationSubstrate(), Substrate)


# ── PhenotypeSubstrate ────────────────────────────────────────────────────


class TestToolSubstrate:
    def test_sense_empty(self, tmp_path, redirect_defaults):
        """No signals and no variant store returns empty."""
        substrate = PhenotypeSubstrate()
        sensed = substrate.sense(days=7)
        assert sensed == []

    def test_sense_with_signals(self, tmp_path, redirect_defaults):
        """Signals produce sensed entries with fitness."""
        collector = SensorySystem()
        for _ in range(5):
            collector.append(_make_signal("fasti_list_events"))
        for _ in range(3):
            collector.append(_make_signal("oghma_search", Outcome.error))

        substrate = PhenotypeSubstrate(collector=collector)
        sensed = substrate.sense(days=7)

        assert len(sensed) == 2
        tools = {e["tool"] for e in sensed}
        assert "fasti_list_events" in tools
        assert "oghma_search" in tools

    def test_sense_with_variant_store(self, tmp_path, redirect_defaults):
        """Tools in variant store appear even without signals."""
        store = Genome()
        store.seed_tool("my_tool", "A description")

        substrate = PhenotypeSubstrate(genome=store)
        sensed = substrate.sense(days=7)

        assert len(sensed) == 1
        assert sensed[0]["tool"] == "my_tool"
        assert sensed[0]["in_store"] is True
        assert sensed[0]["emotion"] is None

    def test_candidates_below_median(self, tmp_path, redirect_defaults):
        """Tools below median fitness are candidates."""
        collector = SensorySystem()
        # Tool A: 5 successes
        for _ in range(5):
            collector.append(_make_signal("a"))
        # Tool B: 5 errors
        for _ in range(5):
            collector.append(_make_signal("b", Outcome.error))
        # Tool C: 5 mixed
        for _ in range(3):
            collector.append(_make_signal("c"))
        for _ in range(2):
            collector.append(_make_signal("c", Outcome.error))

        substrate = PhenotypeSubstrate(collector=collector)
        sensed = substrate.sense(days=7)
        cands = substrate.candidates(sensed)

        cand_tools = {c["tool"] for c in cands}
        assert "b" in cand_tools  # worst fitness

    def test_act_not_in_store(self, tmp_path, redirect_defaults):
        """Act on tool not in store returns skip."""
        substrate = PhenotypeSubstrate()
        result = substrate.act(
            {"tool": "x", "emotion": None, "in_store": False, "variant_count": 0}
        )
        assert "skip" in result
        assert "not in genome" in result

    def test_act_no_emotion(self, tmp_path, redirect_defaults):
        """Act on tool with no emotion returns mutation needed."""
        substrate = PhenotypeSubstrate()
        result = substrate.act(
            {"tool": "x", "emotion": None, "in_store": True, "variant_count": 0}
        )
        assert "mutation needed" in result

    def test_full_cycle(self, tmp_path, redirect_defaults):
        """Full sense -> candidates -> act -> report cycle."""
        collector = SensorySystem()
        store = Genome()
        store.seed_tool("good_tool", "Works well")
        store.seed_tool("bad_tool", "Needs work")

        for _ in range(5):
            collector.append(_make_signal("good_tool"))
        for _ in range(5):
            collector.append(_make_signal("bad_tool", Outcome.error))

        substrate = PhenotypeSubstrate(collector=collector, genome=store)
        sensed = substrate.sense(days=7)
        cands = substrate.candidates(sensed)
        acted = [substrate.act(c) for c in cands]
        report = substrate.report(sensed, acted)

        assert "Phenotype substrate" in report
        assert "good_tool" in report
        assert "bad_tool" in report
        assert "Actions" in report

    def test_report_no_actions(self, tmp_path, redirect_defaults):
        """Report without actions omits the actions section."""
        substrate = PhenotypeSubstrate()
        report = substrate.report([], [])
        assert "Phenotype substrate: 0 tool(s) sensed" in report
        assert "Actions" not in report


# ── ExecutiveSubstrate ────────────────────────────────────────────


class TestConstitutionSubstrate:
    def test_sense_no_constitution(self, tmp_path):
        """Missing constitution returns empty."""
        substrate = ExecutiveSubstrate(
            constitution_path=tmp_path / "nonexistent.md",
            collector=SensorySystem(tmp_path / "signals.jsonl"),
        )
        assert substrate.sense() == []

    def test_sense_extracts_rules(self, tmp_path):
        """Rules are extracted from bold-prefixed lines."""
        constitution_path = tmp_path / "genome.md"
        constitution_path.write_text(SAMPLE_CONSTITUTION)

        substrate = ExecutiveSubstrate(
            constitution_path=constitution_path,
            collector=SensorySystem(tmp_path / "signals.jsonl"),
        )
        sensed = substrate.sense()

        # Constitution rules (5) + any precision gaps detected
        constitution_rules = [r for r in sensed if not r.get("precision_gap")]
        assert len(constitution_rules) == 5
        titles = {r["title"] for r in constitution_rules}
        assert "Opus default" in titles
        assert "Route by role, not cost" in titles

    def test_sense_with_signals_marks_evidence(self, tmp_path):
        """Rules mentioning tools with signals are marked as evidenced."""
        constitution_path = tmp_path / "genome.md"
        constitution_path.write_text(SAMPLE_CONSTITUTION)

        collector = SensorySystem(tmp_path / "signals.jsonl")
        collector.append(_make_signal("fasti_list_events"))
        collector.append(_make_signal("noesis_search"))

        substrate = ExecutiveSubstrate(
            constitution_path=constitution_path,
            collector=collector,
        )
        sensed = substrate.sense()

        # "Route by role, not cost" mentions fasti and noesis
        route_rule = next(r for r in sensed if r["title"] == "Route by role, not cost")
        assert route_rule["has_evidence"] is True

        # "Debate, don't defer" mentions no tools
        debate_rule = next(r for r in sensed if r["title"] == "Debate, don't defer")
        assert debate_rule["has_evidence"] is False

    def test_candidates_are_unevidenced(self, tmp_path):
        """Candidates are rules without signal evidence."""
        constitution_path = tmp_path / "genome.md"
        constitution_path.write_text(SAMPLE_CONSTITUTION)

        collector = SensorySystem(tmp_path / "signals.jsonl")
        collector.append(_make_signal("fasti_list_events"))

        substrate = ExecutiveSubstrate(
            constitution_path=constitution_path,
            collector=collector,
        )
        sensed = substrate.sense()
        cands = substrate.candidates(sensed)

        cand_titles = {c["title"] for c in cands}
        # "Route by role" mentions fasti — should NOT be a candidate
        assert "Route by role, not cost" not in cand_titles
        # Rules without tool mentions should be candidates
        assert "Debate, don't defer" in cand_titles

    def test_act_returns_prune_proposal(self, tmp_path):
        """Act returns a prune candidate string."""
        substrate = ExecutiveSubstrate(
            constitution_path=tmp_path / "c.md",
            collector=SensorySystem(tmp_path / "s.jsonl"),
        )
        result = substrate.act({"title": "Lean toward doing", "has_evidence": False})
        assert result == "prune candidate: Lean toward doing"

    def test_full_cycle(self, tmp_path):
        """Full sense -> candidates -> act -> report cycle."""
        constitution_path = tmp_path / "genome.md"
        constitution_path.write_text(SAMPLE_CONSTITUTION)

        collector = SensorySystem(tmp_path / "signals.jsonl")
        collector.append(_make_signal("fasti_list_events"))

        substrate = ExecutiveSubstrate(
            constitution_path=constitution_path,
            collector=collector,
        )
        sensed = substrate.sense()
        cands = substrate.candidates(sensed)
        acted = [substrate.act(c) for c in cands]
        report = substrate.report(sensed, acted)

        assert "Executive substrate" in report
        assert "evidenced" in report
        assert "without evidence" in report

    def test_report_empty(self, tmp_path):
        """Report on empty sense returns sensible output."""
        substrate = ExecutiveSubstrate(
            constitution_path=tmp_path / "c.md",
            collector=SensorySystem(tmp_path / "s.jsonl"),
        )
        report = substrate.report([], [])
        assert "Executive substrate: 0 rule(s) sensed" in report


# ── ConsolidationSubstrate ──────────────────────────────────────────────────


class TestMemorySubstrate:
    def test_sense_no_directory(self, tmp_path):
        """Missing memory directory returns empty."""
        substrate = ConsolidationSubstrate(
            memory_dir=tmp_path / "nonexistent",
            constitution_path=tmp_path / "c.md",
            collector=SensorySystem(tmp_path / "s.jsonl"),
        )
        assert substrate.sense() == []

    def test_sense_empty_directory(self, tmp_path):
        """Empty memory directory returns empty."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()

        substrate = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "c.md",
            collector=SensorySystem(tmp_path / "s.jsonl"),
        )
        assert substrate.sense() == []

    def test_sense_skips_memory_md(self, tmp_path):
        """MEMORY.md is skipped — it's an index, not a memory."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        (mem_dir / "MEMORY.md").write_text("# Index\n")
        _write_memory(mem_dir, "feedback_test.md", "Test", "A test", "feedback")

        substrate = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "c.md",
            collector=SensorySystem(tmp_path / "s.jsonl"),
        )
        sensed = substrate.sense()
        assert len(sensed) == 1
        assert sensed[0]["name"] == "Test"

    def test_sense_classifies_types(self, tmp_path):
        """Memories are classified by their frontmatter type."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        _write_memory(mem_dir, "feedback_lean.md", "Lean", "Act and report", "feedback")
        _write_memory(mem_dir, "finding_hook.md", "Hook issue", "Post-commit", "finding")
        _write_memory(mem_dir, "project_v.md", "Vivesca", "MCP project", "project")

        constitution_path = tmp_path / "c.md"
        constitution_path.write_text("# Empty\n")

        substrate = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=constitution_path,
            collector=SensorySystem(tmp_path / "s.jsonl"),
        )
        sensed = substrate.sense()

        types = {m["type"] for m in sensed}
        assert types == {"feedback", "finding", "project"}

    def test_sense_detects_signal_match(self, tmp_path):
        """Memories mentioning tools with signals get signal_match=True."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        _write_memory(
            mem_dir,
            "finding_fasti.md",
            "Fasti issue",
            "A fasti problem",
            "finding",
            body="The fasti tool has a timezone bug.",
        )

        collector = SensorySystem(tmp_path / "s.jsonl")
        collector.append(_make_signal("fasti_list_events"))

        substrate = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "c.md",
            collector=collector,
        )
        sensed = substrate.sense()
        assert sensed[0]["signal_match"] is True

    def test_sense_detects_constitution_overlap(self, tmp_path):
        """Memories overlapping with constitution get overlap keywords."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        _write_memory(
            mem_dir,
            "feedback_lean.md",
            "Lean toward doing",
            "Act and report",
            "feedback",
            body="Lean toward doing. Reversible + in scope = act and report. "
            "Debate, don't defer. State your view. Token-conscious. "
            "Gather before responding. Collect all data first. "
            "Scope narrowly. Route by role.",
        )

        constitution_path = tmp_path / "c.md"
        constitution_path.write_text(SAMPLE_CONSTITUTION)

        substrate = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=constitution_path,
            collector=SensorySystem(tmp_path / "s.jsonl"),
        )
        sensed = substrate.sense()
        assert len(sensed[0]["constitution_overlap"]) >= 5

    def test_candidates_feedback_already_promoted(self, tmp_path):
        """Feedback with high overlap is marked already_promoted."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        _write_memory(
            mem_dir,
            "feedback_lean.md",
            "Lean",
            "Lean doing",
            "feedback",
            body="Lean toward doing. Reversible + in scope = act and report. "
            "Debate, don't defer. State your view. Token-conscious. "
            "Gather before responding. Collect all data first. "
            "Scope narrowly. Route by role.",
        )

        constitution_path = tmp_path / "c.md"
        constitution_path.write_text(SAMPLE_CONSTITUTION)

        substrate = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=constitution_path,
            collector=SensorySystem(tmp_path / "s.jsonl"),
        )
        sensed = substrate.sense()
        cands = substrate.candidates(sensed)
        assert cands[0]["action"] == "already_promoted"

    def test_candidates_finding_with_signal(self, tmp_path):
        """Finding with signal match is high-priority program candidate."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        _write_memory(
            mem_dir,
            "finding_fasti.md",
            "Fasti issue",
            "fasti problem",
            "finding",
            body="The fasti tool has a timezone bug.",
        )

        collector = SensorySystem(tmp_path / "s.jsonl")
        collector.append(_make_signal("fasti_list_events"))

        substrate = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=tmp_path / "c.md",
            collector=collector,
        )
        sensed = substrate.sense()
        cands = substrate.candidates(sensed)
        assert cands[0]["action"] == "program"
        assert cands[0]["priority"] == "high (signal evidence)"

    def test_candidates_project_is_migration(self, tmp_path):
        """Project-type memory is a migration candidate."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        _write_memory(mem_dir, "project_v.md", "Vivesca", "MCP project", "project")

        constitution_path = tmp_path / "c.md"
        constitution_path.write_text("# Empty\n")

        substrate = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=constitution_path,
            collector=SensorySystem(tmp_path / "s.jsonl"),
        )
        sensed = substrate.sense()
        cands = substrate.candidates(sensed)
        assert cands[0]["action"] == "migrate"

    def test_candidates_dead_memory(self, tmp_path):
        """Memory with no overlap and no signal is marked dead."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        _write_memory(
            mem_dir,
            "finding_obscure.md",
            "Obscure",
            "xyzzy",
            "finding",
            body="xyzzy plugh thud wumpus.",
        )

        constitution_path = tmp_path / "c.md"
        constitution_path.write_text("# Empty\n")

        substrate = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=constitution_path,
            collector=SensorySystem(tmp_path / "s.jsonl"),
        )
        sensed = substrate.sense()
        cands = substrate.candidates(sensed)
        assert cands[0].get("dead") is True

    def test_act_prune(self, tmp_path):
        """Act on dead memory returns prune proposal."""
        substrate = ConsolidationSubstrate(
            memory_dir=tmp_path,
            constitution_path=tmp_path / "c.md",
            collector=SensorySystem(tmp_path / "s.jsonl"),
        )
        result = substrate.act(
            {
                "name": "Obsolete thing",
                "type": "finding",
                "action": "program",
                "dead": True,
                "constitution_overlap": set(),
                "signal_match": False,
            }
        )
        assert "prune candidate" in result

    def test_act_promote(self, tmp_path):
        """Act on promote candidate returns promote proposal."""
        substrate = ConsolidationSubstrate(
            memory_dir=tmp_path,
            constitution_path=tmp_path / "c.md",
            collector=SensorySystem(tmp_path / "s.jsonl"),
        )
        result = substrate.act(
            {
                "name": "Good feedback",
                "type": "feedback",
                "action": "promote",
            }
        )
        assert result == "promote to constitution: Good feedback"

    def test_act_migrate(self, tmp_path):
        """Act on migration candidate returns migrate proposal."""
        substrate = ConsolidationSubstrate(
            memory_dir=tmp_path,
            constitution_path=tmp_path / "c.md",
            collector=SensorySystem(tmp_path / "s.jsonl"),
        )
        result = substrate.act(
            {
                "name": "Project state",
                "type": "project",
                "action": "migrate",
                "target": (
                    "Vault note (~/code/epigenome/chromatin/)",
                    "Project state belongs in source of truth",
                ),
            }
        )
        assert "migrate to Vault note" in result

    def test_full_cycle(self, tmp_path):
        """Full sense -> candidates -> act -> report cycle."""
        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        _write_memory(mem_dir, "feedback_test.md", "Test feedback", "A test", "feedback")
        _write_memory(mem_dir, "finding_test.md", "Test finding", "A finding", "finding")
        _write_memory(mem_dir, "project_test.md", "Test project", "A project", "project")

        constitution_path = tmp_path / "c.md"
        constitution_path.write_text("# Empty\n")

        substrate = ConsolidationSubstrate(
            memory_dir=mem_dir,
            constitution_path=constitution_path,
            collector=SensorySystem(tmp_path / "s.jsonl"),
        )
        sensed = substrate.sense()
        cands = substrate.candidates(sensed)
        acted = [substrate.act(c) for c in cands]
        report = substrate.report(sensed, acted)

        assert "Consolidation substrate" in report
        assert "feedback" in report
        assert "finding" in report
        assert "project" in report
        assert "Summary" in report

    def test_report_empty(self, tmp_path):
        """Report on empty sense returns sensible output."""
        substrate = ConsolidationSubstrate(
            memory_dir=tmp_path,
            constitution_path=tmp_path / "c.md",
            collector=SensorySystem(tmp_path / "s.jsonl"),
        )
        report = substrate.report([], [])
        assert "Consolidation substrate: 0 file(s) sensed" in report


# ── Unified CLI Command ─────────────────────────────────────────────


@pytest.mark.slow
class TestMetabolismRunCLI:
    def test_run_tools(self, tmp_path, redirect_defaults):
        """metabolism run tools executes without error."""
        from click.testing import CliRunner

        from metabolon.pore import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["metabolism", "run", "tools"])
        assert result.exit_code == 0
        assert "Phenotype substrate" in result.output

    def test_run_constitution(self, tmp_path, redirect_defaults):
        """metabolism run constitution executes without error."""
        import unittest.mock

        from click.testing import CliRunner

        from metabolon.pore import cli

        constitution_dir = tmp_path / "fakehome" / ".local" / "share" / "vivesca"
        constitution_dir.mkdir(parents=True)
        (constitution_dir / "genome.md").write_text(SAMPLE_CONSTITUTION)

        fake_home = tmp_path / "fakehome"
        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            runner = CliRunner()
            result = runner.invoke(cli, ["metabolism", "run", "constitution"])

        assert result.exit_code == 0
        assert "Executive substrate" in result.output

    def test_run_memory_no_dir(self, tmp_path, redirect_defaults):
        """metabolism run memory with missing dir completes gracefully."""
        import unittest.mock

        from click.testing import CliRunner

        from metabolon.pore import cli

        fake_home = tmp_path / "fakehome"
        fake_home.mkdir()
        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            runner = CliRunner()
            result = runner.invoke(cli, ["metabolism", "run", "memory"])

        assert result.exit_code == 0
        assert "Consolidation substrate: 0 file(s) sensed" in result.output

    def test_run_all(self, tmp_path, redirect_defaults):
        """metabolism run all executes all three substrates."""
        import unittest.mock

        from click.testing import CliRunner

        from metabolon.pore import cli

        # Set up minimal fixtures
        fake_home = tmp_path / "fakehome"
        constitution_dir = fake_home / ".local" / "share" / "vivesca"
        constitution_dir.mkdir(parents=True)
        (constitution_dir / "genome.md").write_text(SAMPLE_CONSTITUTION)

        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            runner = CliRunner()
            result = runner.invoke(cli, ["metabolism", "run", "all"])

        assert result.exit_code == 0
        assert "Phenotype substrate" in result.output
        assert "Executive substrate" in result.output
        assert "Consolidation substrate" in result.output

    def test_run_invalid_target(self, tmp_path, redirect_defaults):
        """metabolism run with invalid target fails cleanly."""
        from click.testing import CliRunner

        from metabolon.pore import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["metabolism", "run", "invalid"])
        assert result.exit_code != 0
