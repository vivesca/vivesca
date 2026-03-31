#!/usr/bin/env python3
"""Tests for plan-exec.deprecated effector — tests backend selection and fallback chain."""

import pytest
import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

# Execute the plan-exec.deprecated file directly
plan_exec_path = Path("/home/terry/germline/effectors/plan-exec.deprecated")
plan_exec_code = plan_exec_path.read_text()
namespace = {}
exec(plan_exec_code, namespace)

# Extract all the functions/globals from the namespace
plan_exec = type('plan_exec_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(plan_exec, key, value)

# ---------------------------------------------------------------------------
# Test BACKENDS structure
# ---------------------------------------------------------------------------

def test_backends_defined():
    """Test BACKENDS list has all expected backends."""
    backend_names = [b["name"] for b in plan_exec.BACKENDS]
    assert "gemini" in backend_names
    assert "codex" in backend_names
    assert "opencode" in backend_names
    assert len(plan_exec.BACKENDS) == 3

# ---------------------------------------------------------------------------
# Test _build_prompt
# ---------------------------------------------------------------------------

def test_build_prompt_includes_plan_content(tmp_path):
    """Test _build_prompt includes plan content and project path."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("# Test Plan\n\n- Do task one\n- Do task two")
    
    prompt = plan_exec._build_prompt("/path/to/project", str(plan_file))
    
    assert "Test Plan" in prompt
    assert "Do task one" in prompt
    assert "PROJECT DIRECTORY:" in prompt
    assert "/path/to/project" in prompt
    assert "PLAN-EXEC-DONE" in prompt
    assert "Files touched:" in prompt
    assert "Tests run:" in prompt

def test_build_prompt_includes_rules():
    """Test _build_prompt includes the execution rules."""
    plan_file = Path("/tmp/test-plan.txt")
    plan_file.write_text("Plan")
    
    prompt = plan_exec._build_prompt(".", str(plan_file))
    
    assert "Do NOT modify pyproject.toml" in prompt
    assert "Read existing code files" in prompt
    assert "Implement fully" in prompt
    assert "Run tests" in prompt
    assert "Commit your work" in prompt

# ---------------------------------------------------------------------------
# Test run_backend
# ---------------------------------------------------------------------------

def test_run_backend_succeeded_success():
    """Test run_backend returns True when backend succeeds."""
    backend = plan_exec.BACKENDS[0]  # gemini
    output_file = Path("/tmp/test-backend.log")
    output_file.write_text("some output\nPLAN-EXEC-DONE\nAll done")
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    
    with patch('subprocess.run', return_value=mock_result):
        result = plan_exec.run_backend(backend, ".", "/tmp/plan.txt", output_file)
        assert result is True

def test_run_backend_handles_timeout():
    """Test run_backend returns False on timeout."""
    backend = plan_exec.BACKENDS[0]
    output_file = Path("/tmp/test-timeout.log")
    
    with patch('subprocess.run', side_effect=TimeoutExpired("cmd", 600)):
        result = plan_exec.run_backend(backend, ".", "/tmp/plan.txt", output_file)
        assert result is False

def test_run_backend_handles_not_found():
    """Test run_backend returns False when command not found."""
    backend = plan_exec.BACKENDS[0]
    output_file = Path("/tmp/test-notfound.log")
    
    with patch('subprocess.run', side_effect=FileNotFoundError()):
        result = plan_exec.run_backend(backend, ".", "/tmp/plan.txt", output_file)
        assert result is False

# ---------------------------------------------------------------------------
# Test main argument parsing
# ---------------------------------------------------------------------------

def test_main_parses_required_plan_file():
    """Test main requires a plan file argument."""
    with patch('sys.argv', ['plan-exec']):
        with pytest.raises(SystemExit):
            plan_exec.main()

def test_main_exits_when_plan_not_found():
    """Test main exits when plan file doesn't exist."""
    with patch('sys.argv', ['plan-exec', '/nonexistent/plan.md']):
        with pytest.raises(SystemExit) as exc_info:
            plan_exec.main()
        assert exc_info.value.code == 1

def test_main_dry_run_prints_backends():
    """Test --dry-run prints what would happen and exits."""
    # Create a temporary plan file
    with open('/tmp/test-plan.txt', 'w') as f:
        f.write("test")
    
    with patch('sys.argv', ['plan-exec', '/tmp/test-plan.txt', '--dry-run']):
        with patch('builtins.print'):
            with pytest.raises(SystemExit) as exc_info:
                plan_exec.main()
            assert exc_info.value.code == 0

def test_main_filters_backend_by_name():
    """Test --backend option filters to just that backend."""
    # Create a temporary plan file
    with open('/tmp/test-plan.txt', 'w') as f:
        f.write("test")
    
    with patch('sys.argv', ['plan-exec', '/tmp/test-plan.txt', '--backend', 'codex']):
        # It will try to run codex which isn't here, but we can check the filtering
        with patch('plan_exec.run_backend', return_value=False):
            with pytest.raises(SystemExit) as exc_info:
                plan_exec.main()
            # Since we mocked run_backend to return False, it exits 1 after all fail
            assert exc_info.value.code == 1

def test_main_unknown_backend_exits():
    """Test main exits with error when unknown backend requested."""
    with open('/tmp/test-plan.txt', 'w') as f:
        f.write("test")
    
    with patch('sys.argv', ['plan-exec', '/tmp/test-plan.txt', '--backend', 'nonexistent']):
        with pytest.raises(SystemExit) as exc_info:
            plan_exec.main()
        assert exc_info.value.code == 1

# ---------------------------------------------------------------------------
# Test results directory created
# ---------------------------------------------------------------------------

def test_main_creates_results_dir():
    """Test main creates results directory if it doesn't exist."""
    with open('/tmp/test-plan.txt', 'w') as f:
        f.write("test")
    
    with patch('sys.argv', ['plan-exec', '/tmp/test-plan.txt', '--dry-run']):
        with patch('builtins.print'):
            # Dry run should exit after printing
            with pytest.raises(SystemExit):
                plan_exec.main()
    
    # RESULTS_DIR should exist
    assert plan_exec.RESULTS_DIR.parent.exists()
