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
        result = run_cli("primary", "-q", "alt1", "-q", "alt2")
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
# Error handling
# ---------------------------------------------------------------------------


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
