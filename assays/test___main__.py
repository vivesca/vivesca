"""Tests for metabolon.__main__ — the `python -m metabolon` entry point."""

from __future__ import annotations

import subprocess
import sys

import pytest
from click.testing import CliRunner

from metabolon.sortase.cli import main as sortase_main


def test_main_is_sortase_cli_main():
    """metabolon.__main__ exposes the same main as sortase.cli."""
    import metabolon.__main__ as mod

    assert mod.main is sortase_main


def test_main_is_click_group():
    """The exposed main is a Click group (not a plain function)."""
    import click

    assert isinstance(sortase_main, click.BaseCommand)


def test_import_does_not_invoke_main(monkeypatch):
    """Importing metabolon.__main__ must not call main() — the __name__ guard prevents it."""
    called = False

    def _fake_main():
        nonlocal called
        called = True

    # Reload the module with main patched to detect accidental invocation.
    import importlib
    import metabolon.__main__ as mod

    monkeypatch.setattr(mod, "main", _fake_main)
    importlib.reload(mod)
    assert not called, "main() was called during import — __name__ guard is missing or broken"


def test_subprocess_help():
    """`python -m metabolon --help` exits 0 and mentions sortase."""
    result = subprocess.run(
        [sys.executable, "-m", "metabolon", "--help"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0
    assert "sortase" in result.stdout.lower()


def test_subprocess_version():
    """`python -m metabolon version` exits 0 and prints version info."""
    result = subprocess.run(
        [sys.executable, "-m", "metabolon", "version"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0
    assert "sortase" in result.stdout.lower()


def test_subprocess_no_args_shows_usage():
    """`python -m metabolon` with no arguments shows Click usage (exit 0 for groups)."""
    result = subprocess.run(
        [sys.executable, "-m", "metabolon"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    # Click groups show help and exit 0 when invoked with no subcommand.
    assert result.returncode == 0
    assert "sortase" in result.stdout.lower() or "Usage" in result.stdout
