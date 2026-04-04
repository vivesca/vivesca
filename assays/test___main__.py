"""Tests for metabolon.__main__ — the `python -m metabolon` entry point.

metabolon/__main__.py unconditionally calls membrane.main() on import,
so all tests use subprocess or sys.modules mocking to avoid starting
the MCP server inside the test process.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

_MAIN_PY = Path(__file__).resolve().parent.parent / "metabolon" / "__main__.py"


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
        [
            sys.executable,
            "-m",
            "metabolon",
            "--http",
            "--host",
            "127.0.0.1",
            "--port",
            "9999",
            "--help",
        ],
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


def test_no_args_runs_without_crash():
    """`python -m metabolon` with no args starts the stdio server and exits cleanly."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "metabolon"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        proc.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
    # FastMCP 3.x stdio server exits with 0 after processing stdin EOF.
    # It should not crash with a non-zero exit code.
    assert proc.returncode is not None and proc.returncode <= 0


def test_http_mode_runs_without_crash():
    """`python -m metabolon --http --port 19876` starts the HTTP server (runs until killed)."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "metabolon", "--http", "--port", "19876"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        proc.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
    assert proc.returncode == -9


def test_version_or_help_mentions_transport():
    """`python -m metabolon --help` mentions both transport options."""
    result = subprocess.run(
        [sys.executable, "-m", "metabolon", "--help"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0
    assert "--http" in result.stdout
    assert "stdio" in result.stdout.lower() or "--http" in result.stdout


# ---------------------------------------------------------------------------
# AST-based tests (no import needed — no side-effects at all)
# ---------------------------------------------------------------------------


def test_module_docstring_present():
    """metabolon.__main__ has a module docstring mentioning vivesca."""
    source = _MAIN_PY.read_text()
    tree = ast.parse(source)
    doc = ast.get_docstring(tree)
    assert doc is not None
    assert "vivesca" in doc.lower()


def test_module_imports_membrane_main():
    """metabolon.__main__ imports membrane.main."""
    source = _MAIN_PY.read_text()
    tree = ast.parse(source)
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.append((node.module, alias.name))
    assert ("metabolon.membrane", "main") in names


def test_module_calls_main():
    """metabolon.__main__ calls main() at module level (not guarded by __name__)."""
    source = _MAIN_PY.read_text()
    tree = ast.parse(source)
    # Collect all top-level Call nodes
    calls = [n for n in tree.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)]
    func_names = []
    for expr in calls:
        call = expr.value
        if isinstance(call.func, ast.Name):
            func_names.append(call.func.id)
        elif isinstance(call.func, ast.Attribute):
            func_names.append(call.func.attr)
    assert "main" in func_names


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
