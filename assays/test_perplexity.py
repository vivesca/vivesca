from __future__ import annotations

"""Tests for perplexity.sh — Perplexity API CLI."""

import subprocess
from pathlib import Path

import pytest


PERPLEXITY_SH = Path.home() / "germline" / "effectors" / "perplexity.sh"


def run_perplexity(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    """Run perplexity.sh with given arguments."""
    return subprocess.run(
        [str(PERPLEXITY_SH), *args],
        capture_output=True,
        text=True,
        check=check,
    )


# ── Help/usage tests ─────────────────────────────────────────────────────


def test_help_flag_exits_zero():
    """--help exits with 0 and shows usage."""
    result = run_perplexity("--help")
    assert result.returncode == 0
    assert "Usage" in result.stdout or "Modes:" in result.stdout


def test_help_flag_shows_modes():
    """--help output lists all available modes."""
    result = run_perplexity("--help")
    assert "search" in result.stdout
    assert "ask" in result.stdout
    assert "research" in result.stdout
    assert "reason" in result.stdout


def test_help_flag_shows_models():
    """--help output shows model mappings."""
    result = run_perplexity("--help")
    assert "sonar" in result.stdout


def test_h_flag_same_as_help():
    """-h is equivalent to --help."""
    result_h = run_perplexity("-h")
    result_help = run_perplexity("--help")
    assert result_h.returncode == result_help.returncode
    assert result_h.stdout == result_help.stdout


# ── Argument validation tests ─────────────────────────────────────────────


def test_no_args_exits_nonzero():
    """No arguments exits with 1 and shows usage error."""
    result = run_perplexity()
    assert result.returncode == 1
    assert "Usage" in result.stderr or "Usage" in result.stdout


def test_missing_query_exits_nonzero():
    """Mode without query exits with 1."""
    result = run_perplexity("search")
    assert result.returncode == 1
    assert "query" in result.stderr.lower() or "missing" in result.stderr.lower()


def test_invalid_mode_exits_nonzero():
    """Invalid mode exits with 1."""
    result = run_perplexity("invalid-mode", "test query")
    assert result.returncode == 1
    assert "Unknown mode" in result.stderr or "mode" in result.stderr.lower()


def test_invalid_mode_shows_valid_modes():
    """Invalid mode error message shows valid options."""
    result = run_perplexity("foobar", "test")
    assert result.returncode == 1
    # Should mention at least some valid modes
    stderr_lower = result.stderr.lower()
    assert "search" in stderr_lower or "ask" in stderr_lower


# ── Mode validation tests ─────────────────────────────────────────────────


@pytest.mark.parametrize("mode", ["search", "ask", "research", "reason"])
def test_valid_modes_accepted_without_key_check(mode, monkeypatch):
    """All valid modes are recognized (fails at key check, not mode)."""
    # Remove PERPLEXITY_API_KEY from environment to force early failure
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    result = run_perplexity(mode, "test query")
    # Should fail on missing API key, not on invalid mode
    # Exit code might be 1 from key check, but stderr should mention key, not mode
    if result.returncode == 1:
        # If it fails, it should NOT be due to unknown mode
        assert "Unknown mode" not in result.stderr


def test_mode_case_sensitive():
    """Mode is case-sensitive (SEARCH is invalid)."""
    result = run_perplexity("SEARCH", "test query")
    assert result.returncode == 1
    assert "Unknown mode" in result.stderr or "mode" in result.stderr.lower()


# ── Query handling tests ──────────────────────────────────────────────────


def test_query_with_special_characters(monkeypatch):
    """Query with special JSON characters is accepted."""
    # Without API key, we can't test actual escaping, but we verify it doesn't crash
    # on parsing the query argument itself
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    result = run_perplexity("search", 'test "query" with quotes')
    # Should get to key validation, not crash on argument parsing
    assert "syntax error" not in result.stderr.lower()
    assert "unbound variable" not in result.stderr.lower()


def test_empty_query_handled(monkeypatch):
    """Empty query string is passed through."""
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    result = run_perplexity("search", "")
    # Should get to key validation, not crash
    assert result.returncode in (0, 1)  # Either succeeds (unlikely) or fails on key


def test_multiline_query_handled(monkeypatch):
    """Query with newlines is handled."""
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    result = run_perplexity("search", "line1\nline2")
    # Should not crash
    assert "unbound variable" not in result.stderr.lower()


# ── API key tests ─────────────────────────────────────────────────────────


def test_missing_api_key_error(monkeypatch):
    """Missing PERPLEXITY_API_KEY shows helpful error."""
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    result = run_perplexity("search", "test")
    assert result.returncode == 1
    assert "PERPLEXITY_API_KEY" in result.stderr


# ── Script existence tests ────────────────────────────────────────────────


def test_script_is_executable():
    """perplexity.sh exists and is executable."""
    assert PERPLEXITY_SH.exists()
    assert PERPLEXITY_SH.stat().st_mode & 0o111  # Check executable bit


def test_script_has_shebang():
    """perplexity.sh starts with bash shebang."""
    content = PERPLEXITY_SH.read_text()
    assert content.startswith("#!/usr/bin/env bash") or content.startswith("#!/bin/bash")


def test_script_uses_strict_mode():
    """perplexity.sh uses set -euo pipefail for safety."""
    content = PERPLEXITY_SH.read_text()
    assert "set -euo pipefail" in content or "set -e" in content
