from __future__ import annotations

"""Tests for perplexity.sh — Perplexity API CLI wrapper."""

import subprocess
from pathlib import Path
import os

SCRIPT_PATH = Path.home() / "germline/effectors/perplexity.sh"


def run_script(args: list[str] = None, env: dict = None) -> subprocess.CompletedProcess:
    """Run perplexity.sh with optional args and custom env."""
    cmd = [str(SCRIPT_PATH)] + (args or [])
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(cmd, capture_output=True, text=True, env=run_env)


# ── Help flag tests ─────────────────────────────────────────────────


def test_help_flag_exits_zero():
    """--help flag should exit with code 0."""
    result = run_script(["--help"])
    assert result.returncode == 0


def test_help_flag_shows_usage():
    """--help should show usage information with modes."""
    result = run_script(["--help"])
    assert "Usage:" in result.stdout
    assert "search" in result.stdout
    assert "ask" in result.stdout
    assert "research" in result.stdout
    assert "reason" in result.stdout


def test_help_flag_short():
    """-h should work the same as --help."""
    result = run_script(["-h"])
    assert result.returncode == 0
    assert "Usage:" in result.stdout


# ── Error handling tests ──────────────────────────────────────────────


def test_no_args_shows_usage():
    """No arguments should show usage and exit 1."""
    result = run_script()
    assert result.returncode == 1
    assert "Usage:" in result.stderr


def test_missing_query_exits_error():
    """Mode without query should exit with error."""
    result = run_script(["search"])
    assert result.returncode != 0
    assert "query" in result.stderr.lower() or "Missing" in result.stderr


def test_invalid_mode_exits_error():
    """Invalid mode should exit with error message."""
    result = run_script(["invalid_mode", "test query"])
    assert result.returncode != 0
    assert "Unknown mode" in result.stderr


# ── API key requirement tests ─────────────────────────────────────────


def test_api_key_required():
    """Script should fail without PERPLEXITY_API_KEY."""
    # Create env without PERPLEXITY_API_KEY and without ~/.secrets
    env = os.environ.copy()
    env.pop("PERPLEXITY_API_KEY", None)
    env["HOME"] = "/nonexistent/home/no/secrets"

    result = run_script(["search", "test query"], env=env)
    assert result.returncode != 0
    assert "PERPLEXITY_API_KEY" in result.stderr


# ── Mode validation tests ─────────────────────────────────────────────


def test_mode_search_is_valid():
    """search mode should be recognized (fails at API key check, not mode)."""
    env = os.environ.copy()
    env.pop("PERPLEXITY_API_KEY", None)
    env["HOME"] = "/nonexistent/home/no/secrets"

    result = run_script(["search", "test"], env=env)
    # Should fail on API key, not on invalid mode
    assert "Unknown mode" not in result.stderr


def test_mode_ask_is_valid():
    """ask mode should be recognized."""
    env = os.environ.copy()
    env.pop("PERPLEXITY_API_KEY", None)
    env["HOME"] = "/nonexistent/home/no/secrets"

    result = run_script(["ask", "test"], env=env)
    assert "Unknown mode" not in result.stderr


def test_mode_research_is_valid():
    """research mode should be recognized."""
    env = os.environ.copy()
    env.pop("PERPLEXITY_API_KEY", None)
    env["HOME"] = "/nonexistent/home/no/secrets"

    result = run_script(["research", "test"], env=env)
    assert "Unknown mode" not in result.stderr


def test_mode_reason_is_valid():
    """reason mode should be recognized."""
    env = os.environ.copy()
    env.pop("PERPLEXITY_API_KEY", None)
    env["HOME"] = "/nonexistent/home/no/secrets"

    result = run_script(["reason", "test"], env=env)
    assert "Unknown mode" not in result.stderr
