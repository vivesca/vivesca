"""Tests for metabolon.pinocytosis.ultradian — stub contract and CLI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from metabolon.pinocytosis.ultradian import intake, main

MODULE_PATH = Path(__file__).resolve().parent.parent / "metabolon" / "pinocytosis" / "ultradian.py"


# ── module contract ───────────────────────────────────────────────────


def test_intake_is_callable():
    """intake exists and is callable."""
    assert callable(intake)


def test_intake_default_as_json_is_true():
    """intake() default parameter as_json defaults to True."""
    import inspect

    sig = inspect.signature(intake)
    assert sig.parameters["as_json"].default is True


def test_intake_raises_not_implemented():
    """intake() raises NotImplementedError with descriptive message."""
    with pytest.raises(NotImplementedError, match="ultradian gather not yet implemented"):
        intake()


def test_intake_error_message_mentions_stub():
    """The NotImplementedError message mentions 'stub' so callers know it is not ready."""
    with pytest.raises(NotImplementedError) as exc_info:
        intake()
    assert "stub" in str(exc_info.value).lower()


# ── CLI tests ─────────────────────────────────────────────────────────


def test_cli_help_describes_situational_snapshot():
    """Running with --help mentions situational snapshot."""
    result = subprocess.run(
        [sys.executable, str(MODULE_PATH), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "situational snapshot" in result.stdout.lower()


def test_cli_without_flags_calls_intake(monkeypatch, capsys):
    """main() without flags invokes intake and prints its return value."""
    monkeypatch.setattr(sys, "argv", ["ultradian"])
    monkeypatch.setattr(
        "metabolon.pinocytosis.ultradian.intake",
        lambda as_json=True: "snapshot-result",
    )
    main()
    assert "snapshot-result" in capsys.readouterr().out


def test_main_exits_cleanly_when_intake_succeeds(monkeypatch):
    """main() returns None (no exception) when intake succeeds."""
    monkeypatch.setattr(sys, "argv", ["ultradian"])
    monkeypatch.setattr(
        "metabolon.pinocytosis.ultradian.intake",
        lambda as_json=True: "ok",
    )
    assert main() is None
