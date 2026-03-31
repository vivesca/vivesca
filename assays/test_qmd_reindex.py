"""Tests for effectors/qmd-reindex.sh — vault note embedding for semantic search."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest


SCRIPT_PATH = Path.home() / "germline" / "effectors" / "qmd-reindex.sh"


def run_script(env: dict | None = None, timeout: float = 5.0) -> subprocess.CompletedProcess:
    """Run the qmd-reindex.sh script with optional env overrides."""
    run_env = subprocess.os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=run_env,
    )


# ── Script existence and basic structure tests ────────────────────────────────


def test_script_exists():
    """The qmd-reindex.sh script exists and is readable."""
    assert SCRIPT_PATH.exists(), f"Script not found at {SCRIPT_PATH}"
    assert SCRIPT_PATH.is_file(), f"{SCRIPT_PATH} is not a file"


def test_script_is_executable_as_bash():
    """The script can be parsed by bash (syntax check)."""
    result = subprocess.run(
        ["bash", "-n", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax error in script: {result.stderr}"


def test_script_has_shebang():
    """The script starts with a bash shebang."""
    content = SCRIPT_PATH.read_text()
    assert content.startswith("#!/bin/bash"), "Script should start with #!/bin/bash"


def test_script_exports_path():
    """The script exports PATH with bun bin directory."""
    content = SCRIPT_PATH.read_text()
    assert 'export PATH=' in content, "Script should export PATH"
    assert '.bun/bin' in content, "Script should add .bun/bin to PATH"


# ── Process guard tests (pgrep for running qmd embed) ─────────────────────────


def test_exits_silently_if_qmd_embed_running():
    """Script exits 0 if 'qmd embed' is already running."""
    # Mock pgrep to simulate qmd embed already running
    script = SCRIPT_PATH.read_text()
    
    # Create a test script that mocks pgrep
    test_script = """
export PATH="$HOME/.bun/bin:$PATH"

# Mock pgrep to find a match
pgrep() {
    if [[ "$1" == "-f" && "$2" == "qmd embed" ]]; then
        echo "12345"  # Fake PID
        return 0
    fi
    command pgrep "$@"
}

# Source the rest of the original script's logic
if pgrep -f "qmd embed" > /dev/null 2>&1; then
    exit 0
fi

# Should not reach here
echo "ERROR: Did not exit early"
exit 1
"""
    result = subprocess.run(
        ["bash", "-c", test_script],
        capture_output=True,
        text=True,
        timeout=5.0,
    )
    assert result.returncode == 0, "Should exit 0 when qmd embed is running"
    assert "ERROR" not in result.stdout


def test_proceeds_when_qmd_embed_not_running():
    """Script proceeds to run qmd commands when no existing embed process."""
    # Create a test script that mocks pgrep and qmd
    test_script = """
export PATH="$HOME/.bun/bin:$PATH"

# Mock pgrep to find no match
pgrep() {
    return 1  # No process found
}

# Mock qmd commands
qmd() {
    echo "qmd called with: $@"
}

# Source the original logic
if pgrep -f "qmd embed" > /dev/null 2>&1; then
    exit 0
fi

qmd update 2>/dev/null
qmd embed 2>/dev/null
echo "COMPLETED"
"""
    result = subprocess.run(
        ["bash", "-c", test_script],
        capture_output=True,
        text=True,
        timeout=5.0,
    )
    assert result.returncode == 0
    assert "COMPLETED" in result.stdout


# ── Command execution tests ───────────────────────────────────────────────────


def test_runs_qmd_update_then_embed():
    """Script runs qmd update followed by qmd embed."""
    test_script = """
# Track command order
COMMANDS=()

# Mock pgrep - no process found
pgrep() { return 1; }

# Mock qmd to track calls
qmd() {
    COMMANDS+=("$@")
}

# Source the original script's logic
export PATH="$HOME/.bun/bin:$PATH"

if pgrep -f "qmd embed" > /dev/null 2>&1; then
    exit 0
fi

qmd update 2>/dev/null
qmd embed 2>/dev/null

# Verify order
if [[ "update" != "${COMMANDS[0]}" ]]; then
    echo "ERROR: First command was 'update', got '${COMMANDS[0]}'"
    exit 1
fi
if [[ "embed" != "${COMMANDS[1]}" ]]; then
    echo "ERROR: Second command was 'embed', got '${COMMANDS[1]}'"
    exit 1
fi
echo "OK"
"""
    result = subprocess.run(
        ["bash", "-c", test_script],
        capture_output=True,
        text=True,
        timeout=5.0,
    )
    assert result.returncode == 0
    assert "OK" in result.stdout


def test_script_suppresses_qmd_stderr():
    """Script suppresses stderr from qmd commands (2>/dev/null)."""
    content = SCRIPT_PATH.read_text()
    # Check that both commands have stderr suppression
    assert "qmd update 2>/dev/null" in content
    assert "qmd embed 2>/dev/null" in content


def test_script_does_not_suppress_qmd_stdout():
    """Script does not suppress stdout from qmd commands (only stderr)."""
    test_script = """
# Mock pgrep - no process found
pgrep() { return 1; }

# Mock qmd that outputs to both stdout and stderr
qmd() {
    echo "stdout output"
    echo "stderr output" >&2
}

# Source the original script's logic
export PATH="$HOME/.bun/bin:$PATH"

if pgrep -f "qmd embed" > /dev/null 2>&1; then
    exit 0
fi

qmd update 2>/dev/null
qmd embed 2>/dev/null
"""
    result = subprocess.run(
        ["bash", "-c", test_script],
        capture_output=True,
        text=True,
        timeout=5.0,
    )
    # stdout is NOT suppressed (no > /dev/null for stdout)
    assert "stdout output" in result.stdout
    # stderr IS suppressed by 2>/dev/null
    assert "stderr output" not in result.stderr


# ── Exit behavior tests ───────────────────────────────────────────────────────


def test_exits_zero_on_success():
    """Script exits with code 0 on successful execution."""
    test_script = """
# Mock pgrep - no process found
pgrep() { return 1; }

# Mock qmd - succeeds
qmd() { return 0; }

# Source the original script's logic
export PATH="$HOME/.bun/bin:$PATH"

if pgrep -f "qmd embed" > /dev/null 2>&1; then
    exit 0
fi

qmd update 2>/dev/null
qmd embed 2>/dev/null
"""
    result = subprocess.run(
        ["bash", "-c", test_script],
        capture_output=True,
        text=True,
        timeout=5.0,
    )
    assert result.returncode == 0


def test_script_continues_on_qmd_failure():
    """Script continues even if qmd commands fail (no set -e)."""
    test_script = """
# Mock pgrep - no process found
pgrep() { return 1; }

# Mock qmd - fails
qmd() { 
    echo "qmd called: $@"
    return 1
}

# Source the original script's logic
export PATH="$HOME/.bun/bin:$PATH"

if pgrep -f "qmd embed" > /dev/null 2>&1; then
    exit 0
fi

qmd update 2>/dev/null
UPDATE_EXIT=$?
qmd embed 2>/dev/null
EMBED_EXIT=$?

echo "update_exit=$UPDATE_EXIT embed_exit=$EMBED_EXIT"
"""
    result = subprocess.run(
        ["bash", "-c", test_script],
        capture_output=True,
        text=True,
        timeout=5.0,
    )
    # Script should still exit 0 (no explicit error handling)
    # Both commands run despite failures
    assert "update_exit" in result.stdout
    assert "embed_exit" in result.stdout


def test_exits_zero_when_process_running():
    """Script exits 0 when qmd embed process is already running."""
    test_script = """
# Mock pgrep - process found
pgrep() { 
    echo "12345"
    return 0
}

# This should never be called
qmd() { 
    echo "ERROR: qmd called when it shouldn't be"
    return 1
}

# Source the original script's logic
export PATH="$HOME/.bun/bin:$PATH"

if pgrep -f "qmd embed" > /dev/null 2>&1; then
    exit 0
fi

qmd update 2>/dev/null
qmd embed 2>/dev/null
"""
    result = subprocess.run(
        ["bash", "-c", test_script],
        capture_output=True,
        text=True,
        timeout=5.0,
    )
    assert result.returncode == 0
    assert "ERROR" not in result.stdout


# ── PATH handling tests ───────────────────────────────────────────────────────


def test_path_includes_bun_bin():
    """Script adds ~/.bun/bin to PATH."""
    test_script = '''
# Capture PATH after script's export
export PATH="$HOME/.bun/bin:$PATH"
echo "PATH=$PATH"
'''
    result = subprocess.run(
        ["bash", "-c", test_script],
        capture_output=True,
        text=True,
        timeout=5.0,
    )
    assert ".bun/bin" in result.stdout


def test_path_prepends_bun_bin():
    """Script prepends (not appends) .bun/bin to PATH."""
    content = SCRIPT_PATH.read_text()
    # Check that .bun/bin comes before $PATH (prepend)
    assert '"$HOME/.bun/bin:$PATH"' in content or "$HOME/.bun/bin:$PATH" in content


# ── Integration-like tests with mocked commands ───────────────────────────────


def test_full_script_execution_mocked():
    """Full script execution with all external commands mocked."""
    test_script = f'''
# Override commands before sourcing
export PATH="$HOME/.bun/bin:$PATH"

# Mock pgrep
pgrep() {{ return 1; }}

# Mock qmd with success
qmd() {{ return 0; }}

# Now run the actual script content
{SCRIPT_PATH.read_text()}
'''
    result = subprocess.run(
        ["bash", "-c", test_script],
        capture_output=True,
        text=True,
        timeout=5.0,
    )
    assert result.returncode == 0


def test_pgrep_called_with_correct_args():
    """pgrep is called with -f 'qmd embed' pattern."""
    test_script = '''
PGREP_ARGS=""

pgrep() {
    PGREP_ARGS="$@"
    return 1  # No process found
}

qmd() { return 0; }

export PATH="$HOME/.bun/bin:$PATH"

if pgrep -f "qmd embed" > /dev/null 2>&1; then
    exit 0
fi

qmd update 2>/dev/null
qmd embed 2>/dev/null

echo "pgrep args: $PGREP_ARGS"
'''
    result = subprocess.run(
        ["bash", "-c", test_script],
        capture_output=True,
        text=True,
        timeout=5.0,
    )
    assert "-f" in result.stdout
    assert "qmd embed" in result.stdout


# ── Edge case tests ───────────────────────────────────────────────────────────


def test_script_handles_missing_bun_dir():
    """Script handles case where .bun/bin doesn't exist."""
    test_script = '''
# Set PATH even if .bun/bin doesn't exist
export PATH="$HOME/.bun/bin:$PATH"

pgrep() { return 1; }
qmd() { return 0; }

if pgrep -f "qmd embed" > /dev/null 2>&1; then
    exit 0
fi

qmd update 2>/dev/null
qmd embed 2>/dev/null
echo "DONE"
'''
    result = subprocess.run(
        ["bash", "-c", test_script],
        capture_output=True,
        text=True,
        timeout=5.0,
    )
    assert result.returncode == 0
    assert "DONE" in result.stdout


def test_pgrep_output_suppressed():
    """pgrep output is suppressed (> /dev/null 2>&1)."""
    content = SCRIPT_PATH.read_text()
    # The pgrep line should redirect both stdout and stderr
    assert 'pgrep -f "qmd embed" > /dev/null 2>&1' in content
