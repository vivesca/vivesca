#!/usr/bin/env python3
"""Test for pharos-env.sh effector script."""

import subprocess
import os
from pathlib import Path


def test_pharos_env_sets_home_and_path():
    """Test that pharos-env sets correct HOME and PATH, executes command."""
    script_path = Path(__file__).parent.parent / "effectors" / "pharos-env.sh"
    assert script_path.exists()
    
    # Run env command through pharos-env and check output
    result = subprocess.run(
        [str(script_path), "env"],
        capture_output=True,
        text=True,
        check=True
    )
    
    # Parse output
    env_lines = result.stdout.strip().split('\n')
    env_dict = {}
    for line in env_lines:
        if '=' in line:
            key, value = line.split('=', 1)
            env_dict[key] = value
    
    # Check HOME is set correctly
    assert env_dict['HOME'] == '/home/terry'
    
    # Check PATH contains key directories
    path = env_dict['PATH']
    assert '/home/terry/.local/bin' in path
    assert '/home/terry/.cargo/bin' in path
    assert '/home/terry/.bun/bin' in path
    assert '/home/terry/go/bin' in path
    assert '/usr/local/bin' in path
    assert '/usr/bin' in path
    
    # Verify script is executable
    assert os.access(script_path, os.X_OK), "Script should be executable"


def test_pharos_env_executes_command_successfully():
    """Test that pharos-env successfully executes arbitrary commands."""
    script_path = Path(__file__).parent.parent / "effectors" / "pharos-env.sh"
    
    # Test echo command
    result = subprocess.run(
        [str(script_path), "echo", "hello", "world"],
        capture_output=True,
        text=True,
        check=True
    )
    
    assert result.stdout.strip() == "hello world"
    assert result.stderr == ''


def test_pharos_env_returns_exit_code_correctly():
    """Test that exit code of command is propagated correctly."""
    script_path = Path(__file__).parent.parent / "effectors" / "pharos-env.sh"
    
    # Test successful command (exit 0)
    result = subprocess.run(
        [str(script_path), "true"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    
    # Test failing command (exit 1)
    result = subprocess.run(
        [str(script_path), "false"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 1


def test_zshenv_local_sourced_if_exists():
    """Test that .zshenv.local is sourced when it exists."""
    script_path = Path(__file__).parent.parent / "effectors" / "pharos-env.sh"
    
    # The script already has conditional logic that handles existing/non-existing
    # Verify the conditional logic exists in the script
    with open(script_path) as f:
        content = f.read()
    
    assert 'if [ -f "$HOME/.zshenv.local" ];' in content
    assert 'source "$HOME/.zshenv.local"' in content
    assert 'set -a' in content
    assert 'set +a' in content


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
