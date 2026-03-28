"""Tests for the metabolism dissolve CLI command."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from click.testing import CliRunner

from metabolon.metabolism.signals import Outcome, SensorySystem, Stimulus


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
    dir: Path, filename: str, name: str, description: str, type: str, body: str = ""
) -> Path:
    """Write a memory file with YAML frontmatter."""
    fp = dir / filename
    fp.write_text(f"---\nname: {name}\ndescription: {description}\ntype: {type}\n---\n\n{body}\n")
    return fp


@pytest.fixture
def redirect_defaults(tmp_path):
    """Redirect SensorySystem defaults to tmp_path."""
    sig_defaults = SensorySystem.__init__.__defaults__
    SensorySystem.__init__.__defaults__ = (tmp_path / "signals.jsonl",)
    yield tmp_path
    SensorySystem.__init__.__defaults__ = sig_defaults


SAMPLE_CONSTITUTION = """\
# Constitution

## Core Rules

**Opus default.** Sonnet when weekly % > 70% or parallel subagents. Haiku for lookups.

**Token-conscious.** Every token that doesn't improve the output is wasted.

**Route by role, not cost.** Use fasti for calendar, rheotaxis for search, oghma for memory.

**Lean toward doing.** Reversible + in scope = act and report.

**Debate, don't defer.** State your view, push back on disagreements.

**Gather before responding.** Collect all data first, then synthesise.

**Scope narrowly.** NEVER unconstrained grep on /Users/terry.
"""


class TestDissolveCommand:
    def test_no_memory_directory(self, tmp_path, redirect_defaults):
        """Dissolve prints graceful message when memory directory doesn't exist."""
        from metabolon.pore import cli

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["metabolism", "dissolve", "--memory-dir", str(tmp_path / "nonexistent")],
        )
        assert result.exit_code == 0
        assert "Memory directory not found" in result.output

    def test_empty_memory_directory(self, tmp_path, redirect_defaults):
        """Dissolve prints graceful message when memory directory is empty."""
        from metabolon.pore import cli

        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()

        runner = CliRunner()
        result = runner.invoke(cli, ["metabolism", "dissolve", "--memory-dir", str(mem_dir)])
        assert result.exit_code == 0
        assert "No memory files found" in result.output

    def test_mixed_memory_types(self, tmp_path, redirect_defaults):
        """Dissolve correctly classifies memories by type."""
        from metabolon.pore import cli

        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()

        _write_memory(
            mem_dir,
            "feedback_lean.md",
            "Lean toward doing",
            "Act and report",
            "feedback",
        )
        _write_memory(
            mem_dir,
            "finding_hook.md",
            "Hook breaks files",
            "Post-commit hook issue",
            "finding",
        )
        _write_memory(mem_dir, "user_prefs.md", "User preferences", "Some preferences", "user")
        _write_memory(
            mem_dir,
            "project_vivesca.md",
            "Vivesca system",
            "MCP server project",
            "project",
        )
        _write_memory(
            mem_dir,
            "reference_auth.md",
            "Auth reference",
            "How to authenticate",
            "reference",
        )

        # Set up constitution
        constitution_dir = tmp_path / "fakehome" / ".local" / "share" / "vivesca"
        constitution_dir.mkdir(parents=True)
        (constitution_dir / "genome.md").write_text("# Empty constitution\n")

        import unittest.mock

        fake_home = tmp_path / "fakehome"
        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            runner = CliRunner()
            result = runner.invoke(cli, ["metabolism", "dissolve", "--memory-dir", str(mem_dir)])

        assert result.exit_code == 0
        assert "feedback: 1" in result.output
        assert "finding: 1" in result.output
        assert "user: 1" in result.output
        assert "project: 1" in result.output
        assert "reference: 1" in result.output
        assert "Constitution" in result.output
        assert "Program (hook/guard/linter)" in result.output
        assert "Chromatin note" in result.output
        assert "tool-index.md" in result.output

    def test_feedback_already_in_constitution(self, tmp_path, redirect_defaults):
        """Feedback memory with strong constitution overlap is flagged as already promoted."""
        from metabolon.pore import cli

        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()

        # Create a feedback memory whose content overlaps heavily with the constitution
        _write_memory(
            mem_dir,
            "feedback_lean.md",
            "Lean toward doing",
            "Reversible actions should be taken without asking",
            "feedback",
            body="Lean toward doing. Reversible + in scope = act and report. "
            "Debate, don't defer. State your view. Token-conscious. "
            "Gather before responding. Collect all data first. "
            "Scope narrowly. Route by role.",
        )

        constitution_dir = tmp_path / "fakehome" / ".local" / "share" / "vivesca"
        constitution_dir.mkdir(parents=True)
        (constitution_dir / "genome.md").write_text(SAMPLE_CONSTITUTION)

        import unittest.mock

        fake_home = tmp_path / "fakehome"
        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            runner = CliRunner()
            result = runner.invoke(cli, ["metabolism", "dissolve", "--memory-dir", str(mem_dir)])

        assert result.exit_code == 0
        assert "Already promoted" in result.output
        assert "Lean toward doing" in result.output
        assert "overlap:" in result.output

    def test_finding_with_signal_evidence(self, tmp_path, redirect_defaults):
        """Finding memory with signal match is flagged as high-priority."""
        from metabolon.pore import cli

        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()

        _write_memory(
            mem_dir,
            "finding_fasti.md",
            "Fasti timezone issue",
            "fasti_create_event ignores timezone",
            "finding",
            body="The fasti tool ignores timezone when creating events.",
        )

        # Add signals for fasti
        collector = SensorySystem()
        collector.append(_make_signal("fasti_create_event"))
        collector.append(_make_signal("fasti_list_events"))

        constitution_dir = tmp_path / "fakehome" / ".local" / "share" / "vivesca"
        constitution_dir.mkdir(parents=True)
        (constitution_dir / "genome.md").write_text("# Empty constitution\n")

        import unittest.mock

        fake_home = tmp_path / "fakehome"
        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            runner = CliRunner()
            result = runner.invoke(cli, ["metabolism", "dissolve", "--memory-dir", str(mem_dir)])

        assert result.exit_code == 0
        assert "Program candidates" in result.output
        assert "high (signal evidence)" in result.output
        assert "Fasti timezone issue" in result.output

    def test_memory_md_skipped(self, tmp_path, redirect_defaults):
        """MEMORY.md is skipped — it's an index, not a memory."""
        from metabolon.pore import cli

        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()

        # Write the index file
        (mem_dir / "MEMORY.md").write_text(
            "# Claude Code Auto-Memory\n\nHigh-frequency gotchas only.\n"
        )
        # Write one real memory
        _write_memory(mem_dir, "feedback_test.md", "Test feedback", "A test", "feedback")

        constitution_dir = tmp_path / "fakehome" / ".local" / "share" / "vivesca"
        constitution_dir.mkdir(parents=True)
        (constitution_dir / "genome.md").write_text("# Empty constitution\n")

        import unittest.mock

        fake_home = tmp_path / "fakehome"
        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            runner = CliRunner()
            result = runner.invoke(cli, ["metabolism", "dissolve", "--memory-dir", str(mem_dir)])

        assert result.exit_code == 0
        assert "Memory files: 1" in result.output
        # MEMORY.md should not appear as a classified memory
        assert "Auto-Memory" not in result.output

    def test_custom_memory_dir(self, tmp_path, redirect_defaults):
        """Custom --memory-dir flag is respected."""
        from metabolon.pore import cli

        custom_dir = tmp_path / "custom_memories"
        custom_dir.mkdir()
        _write_memory(
            custom_dir,
            "feedback_one.md",
            "Custom feedback",
            "From custom dir",
            "feedback",
        )

        constitution_dir = tmp_path / "fakehome" / ".local" / "share" / "vivesca"
        constitution_dir.mkdir(parents=True)
        (constitution_dir / "genome.md").write_text("# Empty constitution\n")

        import unittest.mock

        fake_home = tmp_path / "fakehome"
        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            runner = CliRunner()
            result = runner.invoke(
                cli, ["metabolism", "dissolve", "--memory-dir", str(custom_dir)]
            )

        assert result.exit_code == 0
        assert "Memory files: 1" in result.output
        assert str(custom_dir) in result.output

    def test_custom_days_flag(self, tmp_path, redirect_defaults):
        """Custom --days flag controls the signal window."""
        from metabolon.pore import cli

        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        _write_memory(
            mem_dir,
            "finding_fasti.md",
            "Fasti issue",
            "A fasti problem",
            "finding",
            body="The fasti tool has a problem.",
        )

        # Stimulus from 10 days ago
        collector = SensorySystem()
        collector.append(_make_signal("fasti_list_events", days_ago=10))

        constitution_dir = tmp_path / "fakehome" / ".local" / "share" / "vivesca"
        constitution_dir.mkdir(parents=True)
        (constitution_dir / "genome.md").write_text("# Empty constitution\n")

        import unittest.mock

        fake_home = tmp_path / "fakehome"
        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            runner = CliRunner()

            # With --days=7, the 10-day-old signal is excluded
            result7 = runner.invoke(
                cli,
                ["metabolism", "dissolve", "--memory-dir", str(mem_dir), "--days", "7"],
            )
            assert "Signals (last 7 days): 0" in result7.output

            # With --days=30, the signal is included
            result30 = runner.invoke(
                cli,
                [
                    "metabolism",
                    "dissolve",
                    "--memory-dir",
                    str(mem_dir),
                    "--days",
                    "30",
                ],
            )
            assert "Signals (last 30 days): 1" in result30.output

    def test_dead_candidates(self, tmp_path, redirect_defaults):
        """Memories with no constitution overlap and no signal evidence are flagged dead."""
        from metabolon.pore import cli

        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()

        _write_memory(
            mem_dir,
            "finding_obscure.md",
            "Obscure quirk",
            "Some totally obscure thing nobody uses",
            "finding",
            body="xyzzy plugh thud wumpus.",
        )

        constitution_dir = tmp_path / "fakehome" / ".local" / "share" / "vivesca"
        constitution_dir.mkdir(parents=True)
        (constitution_dir / "genome.md").write_text("# Empty constitution\n")

        import unittest.mock

        fake_home = tmp_path / "fakehome"
        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            runner = CliRunner()
            result = runner.invoke(cli, ["metabolism", "dissolve", "--memory-dir", str(mem_dir)])

        assert result.exit_code == 0
        assert "Dead candidates" in result.output
        assert "Obscure quirk" in result.output
        assert "no signal or constitution evidence" in result.output

    def test_summary_line(self, tmp_path, redirect_defaults):
        """Dissolve always ends with a summary line."""
        from metabolon.pore import cli

        mem_dir = tmp_path / "memory"
        mem_dir.mkdir()
        _write_memory(mem_dir, "feedback_test.md", "Test", "A test", "feedback")
        _write_memory(mem_dir, "finding_test.md", "Test finding", "A test", "finding")

        constitution_dir = tmp_path / "fakehome" / ".local" / "share" / "vivesca"
        constitution_dir.mkdir(parents=True)
        (constitution_dir / "genome.md").write_text("# Empty constitution\n")

        import unittest.mock

        fake_home = tmp_path / "fakehome"
        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            runner = CliRunner()
            result = runner.invoke(cli, ["metabolism", "dissolve", "--memory-dir", str(mem_dir)])

        assert result.exit_code == 0
        assert "Summary:" in result.output
        assert "to promote" in result.output
        assert "already promoted" in result.output
        assert "to program" in result.output
        assert "to migrate" in result.output
        assert "dead" in result.output
