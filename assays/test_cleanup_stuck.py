from __future__ import annotations

"""Tests for effectors/cleanup-stuck — stuck process killer (bash script)."""

import subprocess
from pathlib import Path

import pytest

EFFECTOR = Path.home() / "germline" / "effectors" / "cleanup-stuck"


def _fake_bin(tmp_path: Path, *, pkill_exit: int = 0, process_count: str = "42") -> Path:
    """Create a temp bin/ with stub pkill, ps, wc, tr that log behaviour."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    # pkill logs every invocation
    (bin_dir / "pkill").write_text(
        f"#!/bin/bash\necho \"$@\" >> {tmp_path / 'pkill.log'}\nexit {pkill_exit}\n"
    )
    (bin_dir / "pkill").chmod(0o755)
    # ps + wc + tr produce a deterministic process count
    (bin_dir / "ps").write_text("#!/bin/bash\nexit 0\n")
    (bin_dir / "ps").chmod(0o755)
    (bin_dir / "wc").write_text(f"#!/bin/bash\necho ' {process_count}'\n")
    (bin_dir / "wc").chmod(0o755)
    (bin_dir / "tr").write_text("#!/bin/bash\ncat\n")
    (bin_dir / "tr").chmod(0o755)
    return bin_dir


def _run(tmp_path: Path, *, pkill_exit: int = 0, process_count: str = "42") -> subprocess.CompletedProcess:
    """Run cleanup-stuck with a fake PATH."""
    bin_dir = _fake_bin(tmp_path, pkill_exit=pkill_exit, process_count=process_count)
    env = {"PATH": str(bin_dir) + ":/usr/bin:/bin"}
    return subprocess.run(
        [str(EFFECTOR)],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


# ── Structural tests ──────────────────────────────────────────────────────


class TestScriptProperties:
    """Static checks on the cleanup-stuck script."""

    def test_file_exists(self):
        assert EFFECTOR.exists()

    def test_is_executable(self):
        assert EFFECTOR.stat().st_mode & 0o111

    def test_has_bash_shebang(self):
        first = EFFECTOR.read_text().splitlines()[0]
        assert "bash" in first


# ── Output message tests ─────────────────────────────────────────────────


class TestOutputMessages:
    """Verify cleanup-stuck prints the expected diagnostic messages."""

    def test_pyenv_message(self, tmp_path):
        r = _run(tmp_path)
        assert "Killing stuck pyenv processes..." in r.stdout

    def test_claude_message(self, tmp_path):
        r = _run(tmp_path)
        assert "Killing orphan Claude agents..." in r.stdout

    def test_playwright_message(self, tmp_path):
        r = _run(tmp_path)
        assert "Killing stuck playwright..." in r.stdout

    def test_process_count_line(self, tmp_path):
        r = _run(tmp_path, process_count="37")
        assert "Process count: 37" in r.stdout

    def test_done_message(self, tmp_path):
        r = _run(tmp_path)
        assert "Done." in r.stdout
        assert "fresh environment" in r.stdout


# ── pkill invocation tests ────────────────────────────────────────────────


class TestPkillCalls:
    """Verify pkill is invoked with the correct patterns."""

    @staticmethod
    def _pkill_log(tmp_path: Path) -> str:
        return (tmp_path / "pkill.log").read_text()

    def test_pkill_pyenv(self, tmp_path):
        _run(tmp_path)
        assert "-f pyenv" in self._pkill_log(tmp_path)

    def test_pkill_node_claude(self, tmp_path):
        _run(tmp_path)
        log = self._pkill_log(tmp_path)
        assert "node.*claude" in log

    def test_pkill_python_agent(self, tmp_path):
        _run(tmp_path)
        log = self._pkill_log(tmp_path)
        assert "python.*agent" in log

    def test_pkill_playwright(self, tmp_path):
        _run(tmp_path)
        log = self._pkill_log(tmp_path)
        assert "-f playwright" in log

    def test_pkill_chromium(self, tmp_path):
        _run(tmp_path)
        log = self._pkill_log(tmp_path)
        assert "-f chromium" in log

    def test_pkill_uses_sigkill(self, tmp_path):
        """Every pkill call uses -9 (SIGKILL)."""
        _run(tmp_path)
        log = self._pkill_log(tmp_path)
        for line in log.splitlines():
            assert "-9" in line

    def test_pkill_call_count(self, tmp_path):
        """Script makes exactly 5 pkill calls."""
        _run(tmp_path)
        log = self._pkill_log(tmp_path)
        lines = [l for l in log.splitlines() if l.strip()]
        assert len(lines) == 5


# ── Resilience tests ─────────────────────────────────────────────────────


class TestResilience:
    """Verify script handles edge cases gracefully."""

    def test_exits_0_when_no_matching_processes(self, tmp_path):
        """pkill returns 1 when nothing matches — script still exits 0."""
        r = _run(tmp_path, pkill_exit=1)
        assert r.returncode == 0

    def test_exits_0_on_success(self, tmp_path):
        r = _run(tmp_path, pkill_exit=0)
        assert r.returncode == 0

    def test_stderr_suppressed_on_pkill(self):
        """Every pkill line in the source redirects stderr to /dev/null."""
        content = EFFECTOR.read_text()
        for line in content.splitlines():
            if "pkill" in line:
                assert "2>/dev/null" in line, f"Missing stderr redirect: {line}"
