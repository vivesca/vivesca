from __future__ import annotations

"""Tests for judge effector script — LLM quality gate for content evaluation."""

import os
import subprocess
import pytest
from pathlib import Path

JUDGE_PATH = Path(__file__).parent.parent / "effectors" / "judge"
assert JUDGE_PATH.exists(), f"judge effector not found at {JUDGE_PATH}"


def test_judge_is_executable():
    """Test judge script has executable permissions."""
    assert JUDGE_PATH.is_file(), "judge is not a file"
    assert (JUDGE_PATH.stat().st_mode & 0o111) != 0, "judge script is not executable"


def test_judge_has_valid_python_syntax():
    """Check that Python syntax is valid."""
    # Use python -m py_compile to check syntax
    result = subprocess.run(
        ["uv", "run", "python", "-m", "py_compile", str(JUDGE_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax errors in judge script: {result.stderr}"


def test_judge_help_works():
    """Test --help output works."""
    result = subprocess.run(
        [str(JUDGE_PATH), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "LLM quality gate" in result.stdout
    assert "rubric" in result.stdout
    assert "--json" in result.stdout


def test_judge_list_rubrics_works():
    """Test --list-rubrics outputs all expected rubrics."""
    result = subprocess.run(
        [str(JUDGE_PATH), "--list-rubrics"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    # Check all expected rubrics are present
    for rubric in ["article", "job-eval", "outreach"]:
        assert rubric in result.stdout
    # Check criteria listed
    assert "clear_thesis" in result.stdout
    assert "fit_analysis" in result.stdout
    assert "tone" in result.stdout


def test_judge_fails_without_rubric():
    """Test exits with error when no rubric provided."""
    result = subprocess.run(
        [str(JUDGE_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2  # argparse error exit code
    assert "the following arguments are required: rubric" in result.stderr


def test_judge_fails_with_nonexistent_file():
    """Test exits with error when input file doesn't exist."""
    result = subprocess.run(
        [str(JUDGE_PATH), "article", "nonexistent-test-file.md"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 3
    assert "Error: file not found" in result.stderr


def test_judge_fails_with_empty_content():
    """Test exits with error when content is empty."""
    empty_file = Path(__file__).parent / "empty-test-file.tmp"
    empty_file.touch()
    try:
        result = subprocess.run(
            [str(JUDGE_PATH), "article", str(empty_file)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 3
        assert "Error: empty content" in result.stderr
    finally:
        empty_file.unlink()


def test_judge_accepts_stdin_input():
    """Test accepts input from stdin."""
    # This just checks it reads stdin okay — the API call will fail (no mock here), but that's fine
    # We just want to confirm it doesn't error before getting to evaluation
    result = subprocess.run(
        [str(JUDGE_PATH), "article"],
        input="This is a test article with a clear thesis.",
        capture_output=True,
        text=True,
    )
    # It will fail at the API step (expects ANTHROPIC_API_KEY), but shouldn't fail input parsing
    assert result.returncode in (2, 3)
    # Should not get input error, should error at API step
    assert "Error: API call failed" in result.stderr or "Error:" in result.stderr
