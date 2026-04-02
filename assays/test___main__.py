"""Tests for metabolon.__main__ — the `python -m metabolon` entry point.

metabolon/__main__.py unconditionally calls membrane.main() on import,
so all tests use subprocess or sys.modules mocking to avoid starting
the MCP server inside the test process.
"""

from __future__ import annotations

import subprocess
import sys
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Subprocess tests (safe — no import side-effects in the test process)
# ---------------------------------------------------------------------------


def test_help_flag_exits_zero():
    """`python -m metabolon --help` exits 0 and describes the vivesca server."""
    result = subprocess.run(
        [sys.executable, "-m", "metabolon", "--help"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0
    assert "vivesca" in result.stdout.lower()
    assert "--http" in result.stdout


def test_http_host_port_flags_recognized():
    """`python -m metabolon --http --host 127.0.0.1 --port 9999 --help` parses without error."""
    result = subprocess.run(
        [sys.executable, "-m", "metabolon", "--http", "--host", "127.0.0.1",
         "--port", "9999", "--help"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0
    assert "9999" in result.stdout or "port" in result.stdout.lower()


def test_invalid_flag_exits_nonzero():
    """`python -m metabolon --bogus` exits with error code."""
    result = subprocess.run(
        [sys.executable, "-m", "metabolon", "--bogus"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode != 0


def test_no_args_starts_server():
    """`python -m metabolon` with no args starts the stdio MCP server (FastMCP banner)."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "metabolon"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        _, stderr = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        _, stderr = proc.communicate()
    # The server prints a FastMCP banner before blocking on stdio.
    assert "FastMCP" in stderr or "vivesca" in stderr
    assert proc.returncode is None or proc.returncode == 0


def test_http_mode_starts_server():
    """`python -m metabolon --http --port 19876` starts the HTTP MCP server."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "metabolon", "--http", "--port", "19876"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        _, stderr = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        _, stderr = proc.communicate()
    # HTTP mode should also print the FastMCP banner.
    assert "FastMCP" in stderr or "vivesca" in stderr


# ---------------------------------------------------------------------------
# Import-guard tests (mock membrane.main to prevent server launch)
# ---------------------------------------------------------------------------


def test_import_calls_membrane_main():
    """Importing metabolon.__main__ invokes membrane.main()."""
    with patch.dict(sys.modules, {}):
        with patch("metabolon.membrane.main") as mock_main:
            # Remove cached module so it re-imports
            sys.modules.pop("metabolon.__main__", None)
            import metabolon.__main__  # noqa: F401
            mock_main.assert_called_once()


def test_module_docstring_present():
    """metabolon.__main__ has a module docstring."""
    with patch("metabolon.membrane.main"):
        sys.modules.pop("metabolon.__main__", None)
        import metabolon.__main__ as mod
        assert mod.__doc__ is not None
        assert "vivesca" in mod.__doc__.lower()
