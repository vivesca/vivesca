"""Tests for plan-exec — deprecated plan execution effector.

plan-exec now just outputs a deprecation message pointing to sortase exec.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

SCRIPT = Path("/home/terry/germline/effectors/plan-exec")


def _run(*extra_args: str) -> subprocess.CompletedProcess:
    """Run plan-exec with given arguments."""
    return subprocess.run(
        ["sh", str(SCRIPT), *extra_args],
        capture_output=True,
        text=True,
        timeout=5,
    )


def test_help_long_flag():
    """--help shows deprecation message and exits 0."""
    r = _run("--help")
    assert r.returncode == 0
    assert "plan-exec is deprecated" in r.stdout
    assert "sortase exec <plan> -p <project>" in r.stdout
    assert not r.stderr


def test_help_short_flag():
    """-h shows deprecation message and exits 0."""
    r = _run("-h")
    assert r.returncode == 0
    assert "plan-exec is deprecated" in r.stdout
    assert "sortase exec <plan> -p <project>" in r.stdout
    assert not r.stderr


def test_no_args():
    """No arguments prints deprecation to stderr and exits 1."""
    r = _run()
    assert r.returncode == 1
    assert "plan-exec is deprecated" in r.stderr
    assert "sortase exec <plan> -p <project>" in r.stderr
    assert not r.stdout


def test_with_arguments():
    """Any arguments (other than help) prints to stderr and exits 1."""
    r = _run("some", "args", "here")
    assert r.returncode == 1
    assert "plan-exec is deprecated" in r.stderr
    assert "sortase exec <plan> -p <project>" in r.stderr
    assert not r.stdout
