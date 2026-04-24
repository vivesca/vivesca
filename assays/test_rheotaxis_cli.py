"""Tests for rheotaxis CLI — contract for ribosome build.

Tests the effectors/rheotaxis CLI interface, output format, and argument handling.

Two test modes:
- Unit: argument parsing, command tree, output format (no API keys needed)
- Integration: actual backend calls (needs API keys, marked with pytest.mark.integration)
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

RHEOTAXIS = str(Path.home() / "germline" / "effectors" / "rheotaxis")


def run_cli(*args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run rheotaxis CLI and return completed process."""
    return subprocess.run(
        [sys.executable, RHEOTAXIS, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Bare invocation -> porin command tree
# ---------------------------------------------------------------------------


class TestBareInvocation:
    def test_bare_returns_json(self):
        result = run_cli()
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["ok"] is True

    def test_command_tree_has_required_commands(self):
        result = run_cli()
        data = json.loads(result.stdout)
        command_names = [cmd["name"] for cmd in data["result"]["commands"]]
        # Must have search, research, and backends subcommands
        assert any("search" in name for name in command_names)
        assert any("research" in name for name in command_names)
        assert any("backends" in name for name in command_names)

    def test_command_tree_has_params(self):
        result = run_cli()
        data = json.loads(result.stdout)
        for cmd in data["result"]["commands"]:
            assert "params" in cmd


# ---------------------------------------------------------------------------
# --backends flag
# ---------------------------------------------------------------------------


class TestBackendsList:
    def test_backends_returns_json(self):
        result = run_cli("--backends")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["ok"] is True

    def test_backends_lists_seven(self):
        result = run_cli("--backends")
        data = json.loads(result.stdout)
        # Result should reference all 7 backends
        result_str = json.dumps(data["result"])
        for backend in ("grok", "exa", "perplexity", "tavily", "serper", "zhipu", "jina"):
            assert backend in result_str, f"Backend '{backend}' missing from --backends output"


# ---------------------------------------------------------------------------
# Argument validation (no API calls needed)
# ---------------------------------------------------------------------------


class TestArguments:
    def test_exclude_and_b_mutual_exclusion(self):
        """--exclude and -b cannot be used together."""
        result = run_cli("test", "--exclude", "grok", "-b", "exa,serper")
        # Should fail with usage error or porin error envelope
        assert result.returncode != 0

    def test_research_flag_accepted(self):
        """--research flag parses without error (may fail on missing API key, not on parsing)."""
        result = run_cli("test query", "--research")
        # Exit 2 = argparse error, which should NOT happen
        assert result.returncode != 2

    def test_text_flag_accepted(self):
        result = run_cli("test query", "--text")
        assert result.returncode != 2

    def test_multi_query_flag_accepted(self):
        # Multi-query with default fan-out = 7 backends * 3 queries = 21 parallel calls.
        # Slow backends (perplexity ~5s) dominate; bump timeout vs the 30s default.
        result = run_cli("primary", "-q", "alt1", "-q", "alt2", timeout=120)
        assert result.returncode != 2

    def test_exclude_flag_accepted(self):
        result = run_cli("test query", "--exclude", "grok,zhipu")
        assert result.returncode != 2

    def test_b_flag_accepted(self):
        result = run_cli("test query", "-b", "exa,serper")
        assert result.returncode != 2


# ---------------------------------------------------------------------------
# Output format contract
# ---------------------------------------------------------------------------


class TestOutputFormat:
    """These tests need at least one backend to succeed. Mark as integration."""

    @pytest.mark.integration
    def test_default_output_is_porin_json(self):
        """Default output (no --text) must be valid porin JSON envelope."""
        result = run_cli("test query python asyncio")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert data["command"] == "rheotaxis search"
        assert "backends" in data["result"]
        assert "health" in data["result"]
        assert "cost_usd" in data["result"]

    @pytest.mark.integration
    def test_text_output_is_not_json(self):
        """--text output must be human-readable markdown, not JSON."""
        result = run_cli("test query python asyncio", "--text")
        assert result.returncode == 0
        with pytest.raises(json.JSONDecodeError):
            json.loads(result.stdout)
        # Should contain backend names as markdown headers
        assert "##" in result.stdout

    @pytest.mark.integration
    def test_backend_results_have_required_fields(self):
        """Each backend result in JSON output must have name, latency_s, error."""
        result = run_cli("test query python asyncio")
        data = json.loads(result.stdout)
        for backend in data["result"]["backends"]:
            assert "name" in backend
            assert "latency_s" in backend
            assert "error" in backend  # null for success, string for failure

    @pytest.mark.integration
    def test_research_mode_output(self):
        """Research mode returns answer + citations."""
        result = run_cli("what is rheotaxis in cell biology", "--research")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["ok"] is True
        assert "answer" in data["result"]

    @pytest.mark.integration
    def test_multi_query_output(self):
        """Multi-query returns per-query results."""
        result = run_cli("JINS Hong Kong", "-q", "JINS Wan Chai", "--text")
        assert result.returncode == 0
        # Should contain both queries in output
        assert "JINS" in result.stdout


# ---------------------------------------------------------------------------
# Default backend selection — fan out to all 7
# ---------------------------------------------------------------------------


class TestDefaultBackends:
    """Default behaviour: no auto-routing; every search runs all 7 backends."""

    @pytest.fixture
    def mod(self):
        """Load rheotaxis as a module (not __main__) for unit testing."""
        ns = {"__name__": "rheotaxis_test", "__file__": RHEOTAXIS}
        exec(open(RHEOTAXIS).read(), ns)
        return ns

    def test_no_classifier_remains(self, mod):
        """The query-classifier was removed — defaults must fan out."""
        assert "classify_query" not in mod
        assert "route_backends" not in mod

    def test_resolve_exclude_default_empty(self, mod):
        """Default (no flags) returns empty exclude set => all backends run."""
        assert mod["_resolve_exclude"](None, None) == set()

    def test_resolve_exclude_with_exclude_flag(self, mod):
        assert mod["_resolve_exclude"]("grok,zhipu", None) == {"grok", "zhipu"}

    def test_resolve_exclude_with_b_flag(self, mod):
        excluded = mod["_resolve_exclude"](None, "exa,perplexity")
        assert excluded == set(mod["ALL_BACKENDS"]) - {"exa", "perplexity"}


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Signal filtering and source weighting
# ---------------------------------------------------------------------------


class TestQualityFilter:
    """Unit tests for --quality flag: signal density filtering."""

    @pytest.fixture
    def mod(self):
        """Load rheotaxis as a module (not __main__) for unit testing."""
        ns = {"__name__": "rheotaxis_test", "__file__": RHEOTAXIS}
        exec(open(RHEOTAXIS).read(), ns)
        return ns

    # --- signal_density ---

    def test_signal_density_high_for_factual(self, mod):
        text = "Python 3.12 was released on October 2, 2023. It includes better error messages and f-string improvements."
        assert mod["signal_density"](text) > 0.5

    def test_signal_density_low_for_padding(self, mod):
        text = "It looks like your query needs more context. I'll break this down for you. Feel free to clarify what you mean and I'll be happy to help."
        assert mod["signal_density"](text) < 0.3

    def test_signal_density_mixed(self, mod):
        text = "It seems like you're asking about Python. Python is a high-level programming language. Let me know if you need more details."
        density = mod["signal_density"](text)
        assert 0.2 < density < 0.8

    def test_signal_density_empty_string(self, mod):
        assert mod["signal_density"]("") == 0.0

    # --- is_low_signal ---

    def test_is_low_signal_true_for_padding(self, mod):
        text = "It looks like your message is just 'query', but I'm not sure what you're referring to. Could you please provide more details? Feel free to clarify!"
        assert mod["is_low_signal"](text) is True

    def test_is_low_signal_false_for_substantive(self, mod):
        text = "The Python asyncio module provides infrastructure for writing concurrent code using the async/await syntax. It was added in Python 3.4."
        assert mod["is_low_signal"](text) is False

    # --- --quality flag accepted ---

    def test_quality_flag_accepted(self):
        result = run_cli("test query", "--quality")
        assert result.returncode != 2

    def test_quality_with_text_flag_accepted(self):
        result = run_cli("test query", "--quality", "--text")
        assert result.returncode != 2


class TestSourceWeighting:
    """Unit tests for BACKEND_WEIGHTS and order_backends."""

    @pytest.fixture
    def mod(self):
        ns = {"__name__": "rheotaxis_test", "__file__": RHEOTAXIS}
        exec(open(RHEOTAXIS).read(), ns)
        return ns

    def test_perplexity_weighted_highest(self, mod):
        weights = mod["BACKEND_WEIGHTS"]
        assert weights["perplexity"] >= weights["grok"]
        assert weights["perplexity"] > weights["serper"]

    def test_exa_weighted_above_grok(self, mod):
        weights = mod["BACKEND_WEIGHTS"]
        assert weights["exa"] > weights["grok"]

    def test_all_backends_have_weights(self, mod):
        weights = mod["BACKEND_WEIGHTS"]
        for b in ("grok", "exa", "perplexity", "tavily", "serper", "zhipu", "jina"):
            assert b in weights

    def test_order_backends_perplexity_first(self, mod):
        ordered = mod["order_backends"](["grok", "serper", "perplexity", "exa", "tavily"])
        assert ordered[0] == "perplexity"

    def test_order_backends_exa_second_when_no_perplexity(self, mod):
        ordered = mod["order_backends"](["grok", "serper", "exa", "tavily"])
        assert ordered[0] == "exa"

    def test_order_backends_preserves_all(self, mod):
        backends = ["grok", "exa", "perplexity", "tavily", "serper", "jina"]
        ordered = mod["order_backends"](backends)
        assert set(ordered) == set(backends)

    def test_order_backends_weight_sort(self, mod):
        """Backends are sorted by weight descending."""
        ordered = mod["order_backends"](["grok", "serper", "jina"])
        weights = mod["BACKEND_WEIGHTS"]
        for i in range(len(ordered) - 1):
            assert weights[ordered[i]] >= weights[ordered[i + 1]]


class TestErrors:
    def test_all_backends_fail_returns_error_envelope(self):
        """If all backends fail, output is a porin error envelope with fix suggestion."""
        # Exclude all backends to force failure
        result = run_cli("test", "--exclude", "grok,exa,perplexity,tavily,serper,zhipu,jina")
        # Should return error (either exit 1 or porin error envelope)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            assert data.get("ok") is False or len(data.get("result", {}).get("backends", [])) == 0
        else:
            # Error envelope
            data = json.loads(result.stdout)
            assert data["ok"] is False
            assert "fix" in data
