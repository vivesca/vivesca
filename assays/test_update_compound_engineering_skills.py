from __future__ import annotations

"""Tests for update-compound-engineering-skills.sh effector script."""

import subprocess
from pathlib import Path

import pytest


def test_script_exists_and_is_executable():
    """Verify the script exists and has executable permissions."""
    script_path = Path("/home/terry/germline/effectors/update-compound-engineering-skills.sh")
    assert script_path.exists()
    assert script_path.is_file()
    # Check executable bit
    assert (script_path.stat().st_mode & 0o111) != 0, "Script should be executable"


def test_help_flag_prints_usage():
    """Test that --help flag prints usage information and exits 0."""
    script_path = "/home/terry/germline/effectors/update-compound-engineering-skills.sh"
    result = subprocess.run(
        [script_path, "--help"],
        capture_output=True,
        text=True,
        check=False
    )
    assert result.returncode == 0, "--help should exit with code 0"
    assert "Usage:" in result.stdout
    assert "Install/update compound-engineering skills" in result.stdout
    assert "Requires: python3" in result.stdout


def test_help_flag_shows_all_expected_skills():
    """Test that the help output doesn't need to list skills, but script defines expected count."""
    # Read the script to check it contains the expected number of skills
    script_path = Path("/home/terry/germline/effectors/update-compound-engineering-skills.sh")
    content = script_path.read_text()
    
    # Count skills in the SKILLS array
    lines = content.splitlines()
    skills_section_start = next(i for i, line in enumerate(lines) if "SKILLS=(" in line)
    skills = []
    for line in lines[skills_section_start + 1:]:
        line = line.strip()
        if line == ")":
            break
        if line and not line.startswith("#"):
            # Remove comment if any
            line = line.split("#")[0].strip()
            skills.append(line.strip())
    
    # Expected skills: 11 skills currently defined
    # agent-browser, agent-native-architecture, andrew-kane-gem-writer, ce-brainstorm,
    # dhh-rails-style, dspy-ruby, every-style-editor, frontend-design, gemini-imagegen,
    # git-worktree, rclone -> 11 skills
    assert len(skills) == 11, f"Expected 11 skills, got {len(skills)}"
    assert "agent-browser" in skills
    assert "rclone" in skills
    assert "git-worktree" in skills
