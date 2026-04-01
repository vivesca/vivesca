from __future__ import annotations

"""Tests for effectors/qmd-reindex.sh — bash script tested via subprocess."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "qmd-reindex.sh"


def _run(
    tmp_path: Path,
    extra_args: list[str] | None = None,
    env_extra: dict | None = None,
) -> subprocess.CompletedProcess:
    """Run qmd-reindex.sh with HOME=tmp_path."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    if env_extra:
        env.update(env_extra)
    cmd = ["bash", str(SCRIPT)] + (extra_args or [])
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


def _make_fake_qmd(tmp_path: Path, body: str = "exit 0") -> Path:
    """Create a fake qmd binary in ~/.bun/bin/."""
    bun_bin = tmp_path / ".bun" / "bin"
    bun_bin.mkdir(parents=True, exist_ok=True)
    qmd = bun_bin / "qmd"
    qmd.write_text(f"#!/bin/bash\n{body}\n")
    qmd.chmod(0o755)
    return qmd


def _make_fake_pgrep(tmp_path: Path, body: str = "exit 1") -> Path:
    """Create a fake pgrep that exits with given code (1=no match, 0=match)."""
    bin_dir = tmp_path / "fake-bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    pgrep = bin_dir / "pgrep"
    pgrep.write_text(f"#!/bin/bash\n{body}\n")
    pgrep.chmod(0o755)
    return pgrep


def _path_with_fake(tmp_path: Path) -> str:
    """Build a PATH string that includes fake-bin for pgrep and .bun/bin for qmd."""
    return (
        str(tmp_path / "fake-bin")
        + ":"
        + str(tmp_path / ".bun" / "bin")
        + ":/usr/bin:/bin"
    )


# ── Script structure tests ───────────────────────────────────────────────


class TestScriptExists:
    def test_script_is_executable(self):
        assert SCRIPT.exists(), "qmd-reindex.sh must exist"
        assert SCRIPT.stat().st_mode & 0o111, "qmd-reindex.sh must have exec bit"

    def test_script_has_shebang(self):
        first_line = SCRIPT.read_text().splitlines()[0]
        assert first_line.startswith("#!/bin/bash") or first_line.startswith("#!/usr/bin/env bash")

    def test_uses_strict_mode(self):
        content = SCRIPT.read_text()
        assert "set -euo pipefail" in content


class TestScriptContent:
    def test_sets_bun_path(self):
        content = SCRIPT.read_text()
        assert '.bun/bin' in content
        assert 'PATH' in content

    def test_runs_qmd_update(self):
        assert 'qmd update' in SCRIPT.read_text()

    def test_runs_qmd_embed(self):
        assert 'qmd embed' in SCRIPT.read_text()

    def test_checks_for_existing_process(self):
        assert 'pgrep' in SCRIPT.read_text()

    def test_pgrep_uses_full_match(self):
        """pgrep -f matches the full command line, not just the process name."""
        content = SCRIPT.read_text()
        assert 'pgrep -f' in content

    def test_pgrep_pattern_is_qmd_embed(self):
        """The pgrep pattern must be 'qmd embed', not just 'qmd'."""
        assert 'pgrep -f "qmd embed"' in SCRIPT.read_text()


# ── Help flag ────────────────────────────────────────────────────────────


class TestHelpFlag:
    def test_help_long_flag(self):
        r = subprocess.run(
            [str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 0
        assert "Usage:" in r.stdout
        assert "Re-index vault notes" in r.stdout

    def test_help_short_flag(self):
        r = subprocess.run(
            [str(SCRIPT), "-h"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 0
        assert "Usage:" in r.stdout

    def test_help_mentions_commands(self):
        r = subprocess.run(
            [str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "qmd update" in r.stdout
        assert "qmd embed" in r.stdout


# ── Behavior: already running ────────────────────────────────────────────


class TestAlreadyRunning:
    def test_exits_zero_when_embed_already_running(self, tmp_path):
        """When pgrep matches 'qmd embed', script exits 0 immediately."""
        _make_fake_qmd(tmp_path)
        _make_fake_pgrep(tmp_path, body="exit 0")
        r = _run(tmp_path, env_extra={"PATH": _path_with_fake(tmp_path)})
        assert r.returncode == 0

    def test_does_not_run_qmd_when_already_running(self, tmp_path):
        """When qmd embed is already running, qmd update/embed are NOT called."""
        log = tmp_path / "qmd.log"
        _make_fake_qmd(tmp_path, body=f"echo \"$@\" >> {log}")
        _make_fake_pgrep(tmp_path, body="exit 0")
        r = _run(tmp_path, env_extra={"PATH": _path_with_fake(tmp_path)})
        assert r.returncode == 0
        if log.exists():
            assert log.read_text().strip() == "", (
                f"qmd was called when it shouldn't have been: {log.read_text()}"
            )


# ── Behavior: normal run ─────────────────────────────────────────────────


class TestNormalRun:
    def test_exits_zero_on_success(self, tmp_path):
        """When no existing process and qmd succeeds, exit 0."""
        _make_fake_qmd(tmp_path, body="exit 0")
        _make_fake_pgrep(tmp_path, body="exit 1")
        r = _run(tmp_path, env_extra={"PATH": _path_with_fake(tmp_path)})
        assert r.returncode == 0

    def test_calls_qmd_update_then_embed(self, tmp_path):
        """Script calls 'qmd update' then 'qmd embed' in order."""
        log = tmp_path / "qmd.log"
        _make_fake_qmd(tmp_path, body=f"echo \"$@\" >> {log}")
        _make_fake_pgrep(tmp_path, body="exit 1")
        r = _run(tmp_path, env_extra={"PATH": _path_with_fake(tmp_path)})
        assert r.returncode == 0
        calls = log.read_text().strip().splitlines()
        assert calls == ["update", "embed"]

    def test_suppresses_qmd_stderr(self, tmp_path):
        """Script redirects qmd stderr to /dev/null so errors don't leak."""
        _make_fake_qmd(tmp_path, body="echo error-msg >&2; exit 0")
        _make_fake_pgrep(tmp_path, body="exit 1")
        r = _run(tmp_path, env_extra={"PATH": _path_with_fake(tmp_path)})
        assert r.returncode == 0
        assert "error-msg" not in r.stderr

    def test_exits_on_qmd_update_failure(self, tmp_path):
        """With set -e, script exits immediately when qmd update fails."""
        log = tmp_path / "qmd.log"
        _make_fake_qmd(
            tmp_path,
            body=f"""
if [ "$1" = "update" ]; then
    echo "$@" >> {log}
    exit 1
fi
echo "$@" >> {log}
exit 0
""",
        )
        _make_fake_pgrep(tmp_path, body="exit 1")
        r = _run(tmp_path, env_extra={"PATH": _path_with_fake(tmp_path)})
        assert r.returncode != 0
        calls = log.read_text().strip().splitlines()
        assert calls == ["update"], "embed should not run after update failure"

    def test_exits_on_qmd_embed_failure(self, tmp_path):
        """With set -e, script exits when qmd embed fails (update succeeded)."""
        log = tmp_path / "qmd.log"
        _make_fake_qmd(
            tmp_path,
            body=f"""
if [ "$1" = "embed" ]; then
    echo "$@" >> {log}
    exit 1
fi
echo "$@" >> {log}
exit 0
""",
        )
        _make_fake_pgrep(tmp_path, body="exit 1")
        r = _run(tmp_path, env_extra={"PATH": _path_with_fake(tmp_path)})
        assert r.returncode != 0
        calls = log.read_text().strip().splitlines()
        assert calls == ["update", "embed"], "both update and embed should run"

    def test_prepends_bun_to_path(self, tmp_path):
        """Script prepends $HOME/.bun/bin to PATH so qmd is found there."""
        path_log = tmp_path / "path.log"
        _make_fake_qmd(tmp_path, body=f"echo \"$PATH\" > {path_log}")
        _make_fake_pgrep(tmp_path, body="exit 1")
        r = _run(tmp_path, env_extra={"PATH": _path_with_fake(tmp_path)})
        assert r.returncode == 0
        recorded_path = path_log.read_text().strip().splitlines()[0]
        bun_dir = str(tmp_path / ".bun" / "bin")
        assert recorded_path.startswith(bun_dir), (
            f"PATH should start with {bun_dir}, got: {recorded_path}"
        )


# ── Behavior: missing tools ──────────────────────────────────────────────


class TestMissingQmd:
    def test_exits_nonzero_when_qmd_missing(self, tmp_path):
        """Without qmd on PATH, script fails (bash 'command not found' = 127)."""
        _make_fake_pgrep(tmp_path, body="exit 1")
        r = _run(tmp_path, env_extra={"PATH": str(tmp_path / "fake-bin") + ":/usr/bin:/bin"})
        assert r.returncode == 127
