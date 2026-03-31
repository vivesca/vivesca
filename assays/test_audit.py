from __future__ import annotations
"""Tests for the metabolism audit CLI command."""


from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from click.testing import CliRunner

from metabolon.metabolism.signals import Outcome, SensorySystem, Stimulus
from metabolon.metabolism.variants import Genome


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


SAMPLE_CONSTITUTION = """\
# Constitution

## Core Rules

**Opus default.** Sonnet when weekly % > 70% or parallel subagents. Haiku for lookups.

**Token-conscious.** Every token that doesn't improve the output is wasted.

**Route by role, not cost.** Use fasti for calendar, rheotaxis for search, oghma for memory.

**Lean toward doing.** Reversible + in scope = act and report.

**Debate, don't defer.** State your view, push back on disagreements.

## Context Hygiene

**Scope narrowly.** NEVER unconstrained grep on /Users/terry.

**Parallelize independent tasks.** Background only >5 min tasks.
"""


class TestAuditCommand:
    def test_audit_no_constitution(self, tmp_path, redirect_defaults):
        """Audit exits with error when no constitution file exists."""
        from metabolon.pore import cli

        # Ensure constitution path points to nonexistent file
        runner = CliRunner()
        # The command reads from Path.home() / ".local/share/vivesca/genome.md"
        # We monkeypatch Path.home to redirect
        import unittest.mock

        fake_home = tmp_path / "fakehome"
        fake_home.mkdir()
        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            result = runner.invoke(cli, ["metabolism", "audit"])
        assert result.exit_code != 0
        assert "No constitution found" in result.output

    def test_audit_with_signals(self, tmp_path, redirect_defaults):
        """Audit cross-references rules with signal data."""
        from metabolon.pore import cli

        # Write fixture constitution
        constitution_dir = tmp_path / "fakehome" / ".local" / "share" / "vivesca"
        constitution_dir.mkdir(parents=True)
        (constitution_dir / "genome.md").write_text(SAMPLE_CONSTITUTION)

        # Write signals matching some tools mentioned in rules
        collector = SensorySystem()
        collector.append(_make_signal("fasti_list_events"))
        collector.append(_make_signal("fasti_create_event"))
        collector.append(_make_signal("rheotaxis_search"))
        # No oghma signals — so rules mentioning only oghma will show differently

        import unittest.mock

        fake_home = tmp_path / "fakehome"
        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            runner = CliRunner()
            result = runner.invoke(cli, ["metabolism", "audit"])

        assert result.exit_code == 0
        assert "constitutional rule(s)" in result.output
        assert "Rules with signal evidence" in result.output
        assert "Rules without signal evidence" in result.output

        # "Route by role, not cost" mentions fasti and rheotaxis — should have evidence
        assert "Route by role, not cost" in result.output

    def test_audit_no_signals(self, tmp_path, redirect_defaults):
        """Audit with no signals marks all tool-mentioning rules as without evidence."""
        from metabolon.pore import cli

        constitution_dir = tmp_path / "fakehome" / ".local" / "share" / "vivesca"
        constitution_dir.mkdir(parents=True)
        (constitution_dir / "genome.md").write_text(SAMPLE_CONSTITUTION)

        import unittest.mock

        fake_home = tmp_path / "fakehome"
        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            runner = CliRunner()
            result = runner.invoke(cli, ["metabolism", "audit"])

        assert result.exit_code == 0
        assert "Signals (last 30 days): 0" in result.output

    def test_audit_custom_days(self, tmp_path, redirect_defaults):
        """Audit respects --days flag for signal window."""
        from metabolon.pore import cli

        constitution_dir = tmp_path / "fakehome" / ".local" / "share" / "vivesca"
        constitution_dir.mkdir(parents=True)
        (constitution_dir / "genome.md").write_text(SAMPLE_CONSTITUTION)

        # Write a signal from 10 days ago
        collector = SensorySystem()
        collector.append(_make_signal("fasti_list_events", days_ago=10))

        import unittest.mock

        fake_home = tmp_path / "fakehome"
        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            runner = CliRunner()

            # With --days=7, the 10-day-old signal should be excluded
            result7 = runner.invoke(cli, ["metabolism", "audit", "--days", "7"])
            assert "Signals (last 7 days): 0" in result7.output

            # With --days=30, it should be included
            result30 = runner.invoke(cli, ["metabolism", "audit", "--days", "30"])
            assert "Signals (last 30 days): 1" in result30.output

    def test_audit_conflict_detection(self, tmp_path, redirect_defaults):
        """Audit detects potential conflicts when rules share tool references."""
        from metabolon.pore import cli

        # Constitution where two rules both mention "fasti"
        conflict_constitution = """\
# Constitution

**Calendar first.** Always check fasti before scheduling.

**Schedule via fasti.** Use fasti_create_event for all new events.
"""
        constitution_dir = tmp_path / "fakehome" / ".local" / "share" / "vivesca"
        constitution_dir.mkdir(parents=True)
        (constitution_dir / "genome.md").write_text(conflict_constitution)

        collector = SensorySystem()
        collector.append(_make_signal("fasti_list_events"))
        collector.append(_make_signal("fasti_create_event"))

        import unittest.mock

        fake_home = tmp_path / "fakehome"
        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            runner = CliRunner()
            result = runner.invoke(cli, ["metabolism", "audit"])

        assert result.exit_code == 0
        assert "Potential conflicts" in result.output

    def test_audit_summary_line(self, tmp_path, redirect_defaults):
        """Audit always ends with a summary line."""
        from metabolon.pore import cli

        constitution_dir = tmp_path / "fakehome" / ".local" / "share" / "vivesca"
        constitution_dir.mkdir(parents=True)
        (constitution_dir / "genome.md").write_text(SAMPLE_CONSTITUTION)

        import unittest.mock

        fake_home = tmp_path / "fakehome"
        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            runner = CliRunner()
            result = runner.invoke(cli, ["metabolism", "audit"])

        assert result.exit_code == 0
        assert "Summary:" in result.output
        assert "evidenced" in result.output
        assert "without evidence" in result.output

    def test_audit_no_rules_in_constitution(self, tmp_path, redirect_defaults):
        """Audit handles constitution with no bold-prefixed rules."""
        from metabolon.pore import cli

        constitution_dir = tmp_path / "fakehome" / ".local" / "share" / "vivesca"
        constitution_dir.mkdir(parents=True)
        (constitution_dir / "genome.md").write_text("# Constitution\n\nJust some text.\n")

        import unittest.mock

        fake_home = tmp_path / "fakehome"
        with unittest.mock.patch.object(Path, "home", return_value=fake_home):
            runner = CliRunner()
            result = runner.invoke(cli, ["metabolism", "audit"])

        assert result.exit_code == 0
        assert "No bold-prefixed rules" in result.output
