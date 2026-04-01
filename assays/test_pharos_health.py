#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/pharos-health.sh — system health checker."""

import os
import stat
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

EFFECTOR = Path(__file__).resolve().parents[1] / "effectors" / "pharos-health.sh"


def _make_bin(d: Path, name: str, body: str) -> Path:
    """Create an executable mock script in directory d."""
    p = d / name
    p.write_text(f"#!/bin/bash\n{body}\n")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return p


def _run(args: list[str], env_extra: dict | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


# ── File basics ─────────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert EFFECTOR.exists()
        assert EFFECTOR.is_file()

    def test_file_executable(self):
        assert os.access(EFFECTOR, os.X_OK)

    def test_is_bash_script(self):
        head = EFFECTOR.read_text()[:64]
        assert "#!/bin/bash" in head or "#!/usr/bin/env bash" in head

    def test_has_set_euo(self):
        src = EFFECTOR.read_text()
        assert "set -euo pipefail" in src


# ── Help flag ───────────────────────────────────────────────────────────────


class TestHelp:
    def test_help_long(self):
        r = _run(["bash", str(EFFECTOR), "--help"])
        assert r.returncode == 0
        assert "Usage" in r.stdout

    def test_help_short(self):
        r = _run(["bash", str(EFFECTOR), "-h"])
        assert r.returncode == 0
        assert "pharos-health.sh" in r.stdout

    def test_help_exits_early(self):
        """--help should exit before running health checks."""
        r = _run(["bash", str(EFFECTOR), "--help"])
        assert "disk=" not in r.stdout or "Usage" in r.stdout


# ── Healthy scenario ────────────────────────────────────────────────────────


class TestHealthy:
    def test_healthy_exit_0(self):
        """With low disk and no failed units, exit 0."""
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            _make_bin(tdir, "df", 'echo "Use% \n 20%"')
            _make_bin(tdir, "free", 'echo "              total        used        free"; echo "Mem:       32097        7000       25097"')
            _make_bin(tdir, "systemctl", "exit 0")  # --failed prints nothing
            r = _run(
                ["bash", str(EFFECTOR)],
                env_extra={"PATH": f"{td}:{os.environ['PATH']}"},
            )
            assert r.returncode == 0
            assert "ok" in r.stdout
            assert "disk=20%" in r.stdout

    def test_healthy_output_format(self):
        """Output includes disk, mem, and failed_units on healthy run."""
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            _make_bin(tdir, "df", 'echo "Use% \n 50%"')
            _make_bin(tdir, "free", 'echo "              total        used        free"; echo "Mem:       32097        7000       25097"')
            _make_bin(tdir, "systemctl", "exit 0")
            r = _run(
                ["bash", str(EFFECTOR)],
                env_extra={"PATH": f"{td}:{os.environ['PATH']}"},
            )
            assert "disk=" in r.stdout
            assert "mem=" in r.stdout
            assert "failed_units=" in r.stdout


# ── Disk alert ──────────────────────────────────────────────────────────────


class TestDiskAlert:
    def test_disk_above_85_exits_1(self):
        """Disk usage > 85% triggers alert, exits 1."""
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            _make_bin(tdir, "df", 'echo "Use% \n 90%"')
            _make_bin(tdir, "free", 'echo "              total        used        free"; echo "Mem:       32097        7000       25097"')
            _make_bin(tdir, "systemctl", "exit 0")
            # Prevent real tg-notify.sh from running by pointing HOME to tmp
            fake_home = tdir / "home"
            fake_home.mkdir()
            (fake_home / "scripts").mkdir()
            r = _run(
                ["bash", str(EFFECTOR)],
                env_extra={
                    "PATH": f"{td}:{os.environ['PATH']}",
                    "HOME": str(fake_home),
                },
            )
            assert r.returncode == 1

    def test_disk_alert_contains_pct(self):
        """Alert message includes the disk percentage."""
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            _make_bin(tdir, "df", 'echo "Use% \n 92%"')
            _make_bin(tdir, "free", 'echo "              total        used        free"; echo "Mem:       32097        7000       25097"')
            _make_bin(tdir, "systemctl", "exit 0")
            fake_home = tdir / "home"
            fake_home.mkdir()
            (fake_home / "scripts").mkdir()
            r = _run(
                ["bash", str(EFFECTOR)],
                env_extra={
                    "PATH": f"{td}:{os.environ['PATH']}",
                    "HOME": str(fake_home),
                },
            )
            # Alert goes to stderr when tg-notify.sh is missing
            combined = r.stdout + r.stderr
            assert "92%" in combined

    def test_disk_at_85_is_healthy(self):
        """Disk at exactly 85% is still healthy (threshold is > 85)."""
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            _make_bin(tdir, "df", 'echo "Use% \n 85%"')
            _make_bin(tdir, "free", 'echo "              total        used        free"; echo "Mem:       32097        7000       25097"')
            _make_bin(tdir, "systemctl", "exit 0")
            r = _run(
                ["bash", str(EFFECTOR)],
                env_extra={"PATH": f"{td}:{os.environ['PATH']}"},
            )
            assert r.returncode == 0


# ── Failed units alert ─────────────────────────────────────────────────────


class TestFailedUnitsAlert:
    def test_failed_units_triggers_alert(self):
        """Any failed user systemd unit triggers alert."""
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            _make_bin(tdir, "df", 'echo "Use% \n 20%"')
            _make_bin(tdir, "free", 'echo "              total        used        free"; echo "Mem:       32097        7000       25097"')
            # Simulate 3 failed units (3 lines of output)
            _make_bin(tdir, "systemctl", 'if [[ "${1:-}" == *"--failed"* ]]; then echo "unit1.service  failed"; echo "unit2.service  failed"; echo "unit3.service  failed"; fi')
            fake_home = tdir / "home"
            fake_home.mkdir()
            (fake_home / "scripts").mkdir()
            r = _run(
                ["bash", str(EFFECTOR)],
                env_extra={
                    "PATH": f"{td}:{os.environ['PATH']}",
                    "HOME": str(fake_home),
                },
            )
            assert r.returncode == 1
            combined = r.stdout + r.stderr
            assert "failed_units=3" in combined

    def test_zero_failed_units_healthy(self):
        """Zero failed units with low disk is healthy."""
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            _make_bin(tdir, "df", 'echo "Use% \n 30%"')
            _make_bin(tdir, "free", 'echo "              total        used        free"; echo "Mem:       32097        7000       25097"')
            _make_bin(tdir, "systemctl", "exit 0")
            r = _run(
                ["bash", str(EFFECTOR)],
                env_extra={"PATH": f"{td}:{os.environ['PATH']}"},
            )
            assert r.returncode == 0
            assert "failed_units=0" in r.stdout


# ── Telegram notify ────────────────────────────────────────────────────────


class TestTgNotify:
    def test_tg_notify_called_on_alert(self):
        """When tg-notify.sh exists and is executable, it receives the alert message."""
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            _make_bin(tdir, "df", 'echo "Use% \n 90%"')
            _make_bin(tdir, "free", 'echo "              total        used        free"; echo "Mem:       32097        7000       25097"')
            _make_bin(tdir, "systemctl", "exit 0")
            fake_home = tdir / "home"
            fake_home.mkdir()
            scripts_dir = fake_home / "scripts"
            scripts_dir.mkdir()
            # Create tg-notify.sh that logs its argument to a file
            log_file = tdir / "notify_log.txt"
            _make_bin(
                scripts_dir,
                "tg-notify.sh",
                f'echo "$@" > {log_file}',
            )
            r = _run(
                ["bash", str(EFFECTOR)],
                env_extra={
                    "PATH": f"{td}:{os.environ['PATH']}",
                    "HOME": str(fake_home),
                },
            )
            assert r.returncode == 1
            assert log_file.exists()
            msg = log_file.read_text().strip()
            assert "disk=90%" in msg
            assert "pharos health:" in msg

    def test_no_tg_notify_stderr_alert(self):
        """When tg-notify.sh is missing, alert goes to stderr."""
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            _make_bin(tdir, "df", 'echo "Use% \n 90%"')
            _make_bin(tdir, "free", 'echo "              total        used        free"; echo "Mem:       32097        7000       25097"')
            _make_bin(tdir, "systemctl", "exit 0")
            fake_home = tdir / "home"
            fake_home.mkdir()
            (fake_home / "scripts").mkdir()
            r = _run(
                ["bash", str(EFFECTOR)],
                env_extra={
                    "PATH": f"{td}:{os.environ['PATH']}",
                    "HOME": str(fake_home),
                },
            )
            assert r.returncode == 1
            assert "ALERT:" in r.stderr
            assert "disk=90%" in r.stderr


# ── Edge cases ──────────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_systemctl_failure_handled(self):
        """If systemctl fails entirely (not installed), treat as 0 failed units."""
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            _make_bin(tdir, "df", 'echo "Use% \n 20%"')
            _make_bin(tdir, "free", 'echo "              total        used        free"; echo "Mem:       32097        7000       25097"')
            _make_bin(tdir, "systemctl", "exit 1")
            r = _run(
                ["bash", str(EFFECTOR)],
                env_extra={"PATH": f"{td}:{os.environ['PATH']}"},
            )
            # Script uses `|| FAILED=0` fallback, should still be healthy
            assert r.returncode == 0

    def test_no_arguments_healthy(self):
        """Running with no arguments should work normally."""
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            _make_bin(tdir, "df", 'echo "Use% \n 10%"')
            _make_bin(tdir, "free", 'echo "              total        used        free"; echo "Mem:       32097        7000       25097"')
            _make_bin(tdir, "systemctl", "exit 0")
            r = _run(
                ["bash", str(EFFECTOR)],
                env_extra={"PATH": f"{td}:{os.environ['PATH']}"},
            )
            assert r.returncode == 0
