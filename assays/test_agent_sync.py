#!/usr/bin/env python3
"""Test agent-sync.sh effector script."""
import subprocess
import os
from pathlib import Path


def test_script_exists_and_executable():
    script_path = Path(__file__).parent.parent / "effectors" / "agent-sync.sh"
    assert script_path.exists()
    assert os.access(script_path, os.X_OK), "Script should be executable"


def test_help_output():
    script_path = Path(__file__).parent.parent / "effectors" / "agent-sync.sh"
    result = subprocess.run(
        [str(script_path), "--help"],
        capture_output=True,
        text=True,
        check=True
    )
    assert result.returncode == 0
    assert "Usage: agent-sync.sh" in result.stdout
    assert "Pull agent config repos" in result.stdout
    assert "Options:" in result.stdout
    assert "--help" in result.stdout


def test_repos_list_correct():
    script_path = Path(__file__).parent.parent / "effectors" / "agent-sync.sh"
    content = script_path.read_text()
    # Check expected repos are in the list
    assert "$HOME/agent-config" in content
    assert "$HOME/skills" in content
    assert "$HOME/code/epigenome/chromatin" in content


def test_memory_sync_logic():
    script_path = Path(__file__).parent.parent / "effectors" / "agent-sync.sh"
    content = script_path.read_text()
    assert "MEMORY.md" in content
    assert "mkdir -p \"$(dirname \"$DST\")\"" in content
    assert "cp \"$SRC\" \"$DST\"" in content
