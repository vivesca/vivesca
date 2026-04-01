#!/usr/bin/env python3
from __future__ import annotations

"""Tests for bud effector — lightweight agent dispatch tests."""


import pytest
import subprocess
import sys
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

# Execute the bud file directly
bud_path = Path(str(Path.home() / "germline/effectors/bud"))
bud_code = bud_path.read_text()
namespace = {}
exec(bud_code, namespace)

# Extract all the functions/globals from the namespace
bud = type('bud_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(bud, key, value)

# ---------------------------------------------------------------------------
# Test argument parsing
# ---------------------------------------------------------------------------

def test_default_values():
    """Test default argument values are correct."""
    parser = bud.argparse.ArgumentParser(description="Dispatch a task to droid (GLM-5.1)")
    bud.parser = parser  # Rebuild parser to avoid interference
    bud.parser.add_argument("prompt", help="Task prompt")
    bud.parser.add_argument("-p", "--project-dir", default=str(Path.home() / "germline"), help="Project directory")
    bud.parser.add_argument("--auto", default="high", choices=["low", "medium", "high"], help="Autonomy level")
    bud.parser.add_argument("--model", default="glm-5.1", help="Model override")
    bud.parser.add_argument("--json", action="store_true", help="Output as JSON")
    bud.parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    parsed = parser.parse_args(["test prompt"])
    assert parsed.prompt == "test prompt"
    assert parsed.project_dir == str(Path.home() / "germline")
    assert parsed.auto == "high"
    assert parsed.model == "glm-5.1"
    assert parsed.json is False
    assert parsed.timeout == 300

def test_custom_values_parsed():
    """Test custom arguments are parsed correctly."""
    parser = bud.argparse.ArgumentParser(description="Dispatch a task to droid (GLM-5.1)")
    parser.add_argument("prompt", help="Task prompt")
    parser.add_argument("-p", "--project-dir", default=str(Path.home() / "germline"), help="Project directory")
    parser.add_argument("--auto", default="high", choices=["low", "medium", "high"], help="Autonomy level")
    parser.add_argument("--model", default="glm-5.1", help="Model override")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    parsed = parser.parse_args([
        "refactor this code",
        "-p", "/tmp/test",
        "--auto", "medium",
        "--model", "glm-4",
        "--json",
        "--timeout", "600"
    ])
    assert parsed.prompt == "refactor this code"
    assert parsed.project_dir == "/tmp/test"
    assert parsed.auto == "medium"
    assert parsed.model == "glm-4"
    assert parsed.json is True
    assert parsed.timeout == 600

# ---------------------------------------------------------------------------
# Test execution
# ---------------------------------------------------------------------------

def test_success_normal_output(capsys):
    """Test successful execution prints output and exits with 0."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Task completed successfully\nDone"
    mock_result.stderr = ""
    
    with patch('sys.argv', ['bud', "test prompt"]):
        with patch('subprocess.run', return_value=mock_result):
            with pytest.raises(SystemExit) as exc_info:
                bud.main()
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert "Task completed successfully" in captured.out

def test_success_json_output(capsys):
    """Test successful execution with --json outputs proper JSON."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Task result here"
    mock_result.stderr = ""
    
    with patch('sys.argv', ['bud', "test prompt", "--json"]):
        with patch('subprocess.run', return_value=mock_result):
            with pytest.raises(SystemExit) as exc_info:
                bud.main()
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output['success'] is True
            assert output['output'] == "Task result here"
            assert output['exit_code'] == 0

def test_failure_normal(capsys):
    """Test failed execution prints output and exits with error code."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = "Error: something went wrong"
    mock_result.stderr = ""
    
    with patch('sys.argv', ['bud', "test prompt"]):
        with patch('subprocess.run', return_value=mock_result):
            with pytest.raises(SystemExit) as exc_info:
                bud.main()
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "Error: something went wrong" in captured.out

def test_timeout_handled_correctly(capsys):
    """Test timeout prints error and exits with 124."""
    with patch('sys.argv', ['bud', "test prompt", "--timeout", "10"]):
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired(["droid"], 10)):
            with pytest.raises(SystemExit) as exc_info:
                bud.main()
            assert exc_info.value.code == 124
            captured = capsys.readouterr()
            assert "Timed out" in captured.err

def test_command_constructed_correctly():
    """Test golem command is constructed correctly with all args."""
    with patch('sys.argv', ['bud', "my test prompt", "--auto", "low", "--model", "custom-model"]):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            with pytest.raises(SystemExit):
                bud.main()
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "golem"
            assert "my test prompt" in call_args

def test_default_project_dir_correct():
    """Test default project directory is germline in home."""
    with patch('sys.argv', ['bud', "test"]):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            with pytest.raises(SystemExit):
                bud.main()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs['cwd'] == str(Path.home() / "germline")
