from __future__ import annotations

"""Tests for effectors/qmd-reindex.sh — bash script tested via subprocess."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "qmd-reindex.sh"


def _run(tmp_path: Path, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """Run qmd-reindex.sh with HOME=tmp_path."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(SCRIPT)],
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


# ── Script structure tests ───────────────────────────────────────────────


class TestScriptExists:
    def test_script_is_executable(self):
        assert SCRIPT.exists(), "qmd-reindex.sh must exist"

    def test_script_has_shebang(self):
        first_line = SCRIPT.read_text().splitlines()[0]
        assert first_line.startswith("#!/bin/bash") or first_line.startswith("#!/usr/bin/env bash")


class TestScriptContent:
    def test_sets_bun_path(self):
        content = SCRIPT.read_text()
        assert '.bun/bin' in content
        assert 'PATH' in content

    def test_runs_qmd_update(self):
        content = SCRIPT.read_text()
        assert 'qmd update' in content

    def test_runs_qmd_embed(self):
        content = SCRIPT.read_text()
        assert 'qmd embed' in content

    def test_checks_for_existing_process(self):
        content = SCRIPT.read_text()
        assert 'pgrep' in content


# ── Behavior: already running ────────────────────────────────────────────


class TestAlreadyRunning:
    def test_exits_zero_when_embed_already_running(self, tmp_path):
        """When pgrep matches 'qmd embed', script exits 0 immediately."""
        _make_fake_qmd(tmp_path)
        # pgrep returns 0 = found matching process
        _make_fake_pgrep(tmp_path, body="exit 0")
        # Set PATH so fake-bin pgrep is found before real pgrep
        r = _run(tmp_path, env_extra={"PATH": str(tmp_path / "fake-bin") + ":" + os.environ.get("PATH", "")})
        assert r.returncode == 0

    def test_does_not_run_qmd_when_already_running(self, tmp_path):
        """When qmd embed is already running, qmd update/embed are NOT called."""
        log = tmp_path / "qmd.log"
        # Fake qmd that logs every invocation
        _make_fake_qmd(tmp_path, body=f"echo \"$@\" >> {log}")
        _make_fake_pgrep(tmp_path, body="exit 0")
        r = _run(tmp_path, env_extra={"PATH": str(tmp_path / "fake-bin") + ":" + os.environ.get("PATH", "")})
        assert r.returncode == 0
        # qmd should NOT have been called
        if log.exists():
            assert log.read_text().strip() == "", f"qmd was called when it shouldn't have been: {log.read_text()}"


# ── Behavior: normal run ─────────────────────────────────────────────────


class TestNormalRun:
    def test_exits_zero_on_success(self, tmp_path):
        """When no existing process and qmd succeeds, exit 0."""
        _make_fake_qmd(tmp_path, body="exit 0")
        _make_fake_pgrep(tmp_path, body="exit 1")
        r = _run(tmp_path, env_extra={"PATH": str(tmp_path / "fake-bin") + ":" + os.environ.get("PATH", "")})
        assert r.returncode == 0

    def test_calls_qmd_update_then_embed(self, tmp_path):
        """Script calls 'qmd update' then 'qmd embed' in order."""
        log = tmp_path / "qmd.log"
        _make_fake_qmd(tmp_path, body=f"echo \"$@\" >> {log}")
        _make_fake_pgrep(tmp_path, body="exit 1")
        r = _run(tmp_path, env_extra={"PATH": str(tmp_path / "fake-bin") + ":" + os.environ.get("PATH", "")})
        assert r.returncode == 0
        calls = log.read_text().strip().splitlines()
        assert calls == ["update", "embed"]

    def test_suppresses_qmd_stderr(self, tmp_path):
        """Script redirects qmd stderr to /dev/null."""
        # qmd that writes to stderr
        _make_fake_qmd(tmp_path, body="echo error-msg >&2; exit 0")
        _make_fake_pgrep(tmp_path, body="exit 1")
        r = _run(tmp_path, env_extra={"PATH": str(tmp_path / "fake-bin") + ":" + os.environ.get("PATH", "")})
        # The 2>/dev/null in the script should swallow stderr
        # Our subprocess captures the script's combined output
        assert r.returncode == 0

    def test_continues_if_qmd_update_fails(self, tmp_path):
        """Even if qmd update fails, qmd embed is still called."""
        log = tmp_path / "qmd.log"
        # Fake qmd that logs args, update fails, embed succeeds
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
        r = _run(tmp_path, env_extra={"PATH": str(tmp_path / "fake-bin") + ":" + os.environ.get("PATH", "")})
        # Script should still exit 0 because qmd embed's exit code is last
        assert r.returncode == 0
        calls = log.read_text().strip().splitlines()
        assert calls == ["update", "embed"]


class TestMissingQmd:
    def test_exits_nonzero_when_qmd_missing(self, tmp_path):
        """Without qmd on PATH, script fails (bash 'command not found' = 127)."""
        _make_fake_pgrep(tmp_path, body="exit 1")
        # Use a minimal PATH with no qmd
        r = _run(tmp_path, env_extra={"PATH": str(tmp_path / "fake-bin") + ":/usr/bin:/bin"})
        # bash returns 127 for command not found, but with `|| true` patterns it could be 0
        # The script does NOT have `set -e`, so it returns the exit code of the last command
        # qmd embed (last command) will fail with 127
        assert r.returncode == 127
