"""Tests for the mitosis-sync effector (ssh-based worker git sync).

These tests verify CLI argument handling and exit codes without hitting a real
remote. Integration tests against real ganglion are a separate smoke test.
"""

import os
import subprocess
from pathlib import Path

EFFECTOR = Path(__file__).resolve().parents[1] / "effectors" / "mitosis-sync"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(EFFECTOR), *args],
        capture_output=True,
        text=True,
        timeout=15,
    )


def test_effector_exists_and_is_executable() -> None:
    assert EFFECTOR.exists(), f"effector not found: {EFFECTOR}"
    assert EFFECTOR.is_file(), f"effector is not a file: {EFFECTOR}"
    assert os.access(EFFECTOR, os.X_OK), f"effector is not executable: {EFFECTOR}"


def test_help_exits_zero_and_prints_usage() -> None:
    result = _run("--help")
    assert result.returncode == 0, f"stderr: {result.stderr}"
    combined = (result.stdout + result.stderr).lower()
    assert "usage" in combined or "mitosis-sync" in combined
    # Must document at least one real host alias
    assert "ganglion" in combined or "<host>" in combined


def test_no_args_exits_nonzero() -> None:
    """Running with no arguments should print usage and fail."""
    result = _run()
    assert result.returncode != 0


def test_unknown_host_exits_one() -> None:
    """A host that doesn't exist in ssh config (or is unreachable) exits 1."""
    result = _run("not-a-real-host-aaaaa-12345")
    assert result.returncode == 1
    combined = (result.stdout + result.stderr).lower()
    assert any(
        word in combined
        for word in ("unknown", "not found", "unreachable", "could not resolve", "no such")
    ), f"expected host-error message, got: {combined!r}"


def test_status_flag_with_unknown_host_exits_one() -> None:
    """--status flag is recognized; host lookup still fails cleanly."""
    result = _run("--status", "not-a-real-host-aaaaa-12345")
    assert result.returncode == 1


def test_no_fly_references() -> None:
    """Regression: effector must not reference fly CLI (the whole point of this rewrite)."""
    content = EFFECTOR.read_text()
    lower = content.lower()
    # Guard against fly ssh console, fly apps, fly.io references
    forbidden = ["fly ssh", "fly status", "fly apps", "lucerna_app", "/.fly"]
    for token in forbidden:
        assert token.lower() not in lower, (
            f"effector still references {token!r} — fly dependency not removed"
        )


def test_deleted_modules_are_gone() -> None:
    """The old MCP-based mitosis modules must be deleted."""
    repo = Path(__file__).resolve().parents[1]
    for relpath in (
        "src/metabolon/enzymes/mitosis.py",
        "src/metabolon/organelles/mitosis.py",
    ):
        assert not (repo / relpath).exists(), (
            f"{relpath} must be deleted as part of the retire-mitosis-mcp refactor"
        )
