from __future__ import annotations

"""Integration tests for the wired metabolism loop."""


import asyncio
import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock

import pytest
from click.testing import CliRunner

from metabolon.metabolism.signals import Outcome, SensorySystem, Stimulus
from metabolon.metabolism.variants import Genome


def _make_signal(tool: str, outcome: Outcome = Outcome.success, tokens: int = 100) -> Stimulus:
    return Stimulus(
        tool=tool,
        outcome=outcome,
        substrate_consumed=tokens,
        product_released=tokens,
        response_latency=50,
        error="some error" if outcome == Outcome.error else None,
    )


@pytest.fixture
def mock_symbiont():
    """Inject a mock symbiont module so lazy imports find it."""
    mock_mod = ModuleType("metabolon.symbiont")
    mock_mod.transduce = MagicMock(return_value="An improved tool description for better results")
    sys.modules["metabolon.symbiont"] = mock_mod
    yield mock_mod
    del sys.modules["metabolon.symbiont"]


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


class TestSweepCLI:
    def test_sweep_no_signals(self, redirect_defaults, mock_symbiont):
        """Sweep with empty signal log returns early."""
        from metabolon.pore import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["metabolism", "sweep"])
        assert result.exit_code == 0
        assert "No stimuli found" in result.output

    def test_sweep_no_candidates(self, redirect_defaults, mock_symbiont):
        """Sweep with all-healthy tools finds no candidates."""
        from metabolon.pore import cli

        collector = SensorySystem()
        # Single tool, all successes — can't be below median of itself
        for _ in range(5):
            collector.append(_make_signal("good_tool", Outcome.success))

        runner = CliRunner()
        result = runner.invoke(cli, ["metabolism", "sweep"])
        assert result.exit_code == 0
        assert "No candidates" in result.output

    def test_sweep_promotes_variant(self, redirect_defaults, mock_symbiont):
        """Full sweep: signals → fitness → mutation → gate → promotion."""
        from metabolon.pore import cli

        collector = SensorySystem()
        store = Genome()

        store.seed_tool("bad_tool", "Original bad description for this particular tool")
        store.seed_tool("good_tool", "Good tool that works perfectly for all lookups")

        for _ in range(5):
            collector.append(_make_signal("bad_tool", Outcome.error))
            collector.append(_make_signal("good_tool", Outcome.success))

        def smart_transduce(model_name, prompt, **kw):
            if "accurately" in prompt:
                return "PASS"
            return "Improved description that fixes the issues with this tool"

        mock_symbiont.transduce = MagicMock(side_effect=smart_transduce)

        runner = CliRunner()
        result = runner.invoke(cli, ["metabolism", "sweep"])

        assert result.exit_code == 0
        assert "promoted" in result.output
        assert len(store.allele_variants("bad_tool")) >= 2


class TestHotPathRepair:
    def test_acute_immune_response_on_error(self, redirect_defaults, mock_symbiont):
        """Middleware triggers repair and promotes on tool error."""
        store = Genome()
        store.seed_tool("failing_tool", "A tool that does something useful for testing")

        repaired = "An improved description that prevents tool failures here"

        def smart_transduce(model_name, prompt, **kw):
            if "accurately" in prompt:
                return "PASS"
            return repaired

        mock_symbiont.transduce = MagicMock(side_effect=smart_transduce)

        from metabolon.membrane import SensoryMiddleware

        collector = SensorySystem()
        middleware = SensoryMiddleware(collector=collector)
        asyncio.run(middleware._acute_immune_response("failing_tool", "tool crashed"))

        variants = store.allele_variants("failing_tool")
        assert len(variants) >= 2
        assert store.active_allele("failing_tool") == repaired

    def test_acute_immune_response_skips_unknown_tool(self, redirect_defaults, mock_symbiont):
        """Repair skips tools not in variant store."""
        from metabolon.membrane import SensoryMiddleware

        collector = SensorySystem()
        middleware = SensoryMiddleware(collector=collector)
        # Should not raise
        asyncio.run(middleware._acute_immune_response("unknown_tool", "error"))

    def test_acute_immune_response_does_not_block_on_failure(
        self, redirect_defaults, mock_symbiont
    ):
        """Repair failure doesn't propagate."""
        store = Genome()
        store.seed_tool("tool", "A tool for doing some important work for users")

        mock_symbiont.transduce = MagicMock(side_effect=RuntimeError("LLM down"))

        from metabolon.membrane import SensoryMiddleware

        collector = SensorySystem()
        middleware = SensoryMiddleware(collector=collector)
        # Should not raise despite LLM failure
        asyncio.run(middleware._acute_immune_response("tool", "error"))

        assert len(store.allele_variants("tool")) == 1

    def test_acute_immune_response_judge_rejects(self, redirect_defaults, mock_symbiont):
        """Repair candidate rejected by judge is not promoted."""
        store = Genome()
        store.seed_tool("tool", "Original description that should remain active here")

        def reject_transduce(model_name, prompt, **kw):
            if "accurately" in prompt:
                return "FAIL: misleading"
            return "A changed description that differs from original content"

        mock_symbiont.transduce = MagicMock(side_effect=reject_transduce)

        from metabolon.membrane import SensoryMiddleware

        collector = SensorySystem()
        middleware = SensoryMiddleware(collector=collector)
        asyncio.run(middleware._acute_immune_response("tool", "error"))

        assert store.active_allele("tool") == "Original description that should remain active here"
