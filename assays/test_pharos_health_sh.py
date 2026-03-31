from __future__ import annotations

"""Tests for effectors/pharos-health.sh — bash script tested via subprocess."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "pharos-health.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _make_mock(mock_dir: Path, name: str, stdout: str = "", exit_code: int = 0):
    """Write a mock script that prints stdout and exits with exit_code."""
    script = mock_dir / name
    script.write_text(
        "#!/bin/bash\n"
        f"printf '%s' '{stdout}'\n"
        f"exit {exit_code}\n"
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)


def _run(
    tmp_path: Path,
    disk_pct: int = 50,
    mem_line: str = "Mem: 4096 8192",
    failed_units: int = 0,
    args: list[str] | None = None,
    tg_notify: bool = False,
) -> subprocess.CompletedProcess:
    """Run pharos-health.sh with mocked df/free/systemctl."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)

    mock_dir = tmp_path / "mock-bin"
    mock_dir.mkdir(exist_ok=True)

    # Mock df — outputs the given disk percentage
    _make_mock(mock_dir, "df", f"Use%\n  {disk_pct}%")

    # Mock free — outputs Mem: line with given numbers
    _make_mock(mock_dir, "free", f"              total       used\n{mem_line}")

    # Mock systemctl — outputs failed_units number of lines (trailing newline for wc -l)
    if failed_units > 0:
        failed_lines = "\n".join(["unit.service  loaded  failed"] * failed_units) + "\n"
    else:
        failed_lines = ""
    _make_mock(mock_dir, "systemctl", failed_lines)

    # Optionally create a real tg-notify.sh mock that records calls
    if tg_notify:
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        tg = scripts_dir / "tg-notify.sh"
        tg.write_text(f"#!/bin/bash\nprintf '%s' \"$@\" > {tmp_path / 'tg.log'}\n")
        tg.chmod(tg.stat().st_mode | stat.S_IEXEC)

    env["PATH"] = str(mock_dir) + os.pathsep + env.get("PATH", "")

    cmd = ["bash", str(SCRIPT)] + (args or [])
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


# ── --help ──────────────────────────────────────────────────────────────


class TestHelp:
    def test_help_flag(self, tmp_path):
        r = _run(tmp_path, args=["--help"])
        assert r.returncode == 0
        assert "Usage: pharos-health.sh" in r.stdout

    def test_h_flag(self, tmp_path):
        r = _run(tmp_path, args=["-h"])
        assert r.returncode == 0
        assert "Usage: pharos-health.sh" in r.stdout


# ── healthy state ───────────────────────────────────────────────────────


class TestHealthy:
    def test_healthy_exits_zero(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=0)
        assert r.returncode == 0

    def test_healthy_prints_ok(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=0)
        assert "pharos health: ok" in r.stdout

    def test_healthy_includes_disk_pct(self, tmp_path):
        r = _run(tmp_path, disk_pct=42, failed_units=0)
        assert "disk=42%" in r.stdout

    def test_healthy_includes_memory(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, mem_line="Mem: 2048 4096", failed_units=0)
        assert "mem=" in r.stdout

    def test_healthy_includes_failed_units(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=0)
        assert "failed_units=0" in r.stdout

    def test_disk_at_85_is_healthy(self, tmp_path):
        """85% is the boundary — should NOT trigger alert."""
        r = _run(tmp_path, disk_pct=85, failed_units=0)
        assert r.returncode == 0
        assert "pharos health: ok" in r.stdout


# ── high disk alert ─────────────────────────────────────────────────────


class TestHighDisk:
    def test_high_disk_exits_one(self, tmp_path):
        r = _run(tmp_path, disk_pct=90, failed_units=0)
        assert r.returncode == 1

    def test_high_disk_no_tg_notify_prints_stderr(self, tmp_path):
        """No tg-notify.sh → ALERT printed to stderr."""
        r = _run(tmp_path, disk_pct=90, failed_units=0, tg_notify=False)
        assert "ALERT:" in r.stderr
        assert "disk=90%" in r.stderr

    def test_high_disk_calls_tg_notify(self, tmp_path):
        """tg-notify.sh exists → called with alert message."""
        r = _run(tmp_path, disk_pct=92, failed_units=0, tg_notify=True)
        assert r.returncode == 1
        log = (tmp_path / "tg.log").read_text()
        assert "disk=92%" in log

    def test_disk_86_triggers_alert(self, tmp_path):
        """Just above threshold."""
        r = _run(tmp_path, disk_pct=86, failed_units=0)
        assert r.returncode == 1


# ── failed systemd units ───────────────────────────────────────────────


class TestFailedUnits:
    def test_failed_units_exits_one(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=1)
        assert r.returncode == 1

    def test_failed_units_prints_stderr(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=2, tg_notify=False)
        assert "ALERT:" in r.stderr
        assert "failed_units=2" in r.stderr

    def test_failed_units_calls_tg_notify(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=1, tg_notify=True)
        assert r.returncode == 1
        log = (tmp_path / "tg.log").read_text()
        assert "failed_units=1" in log

    def test_failed_units_includes_disk_in_msg(self, tmp_path):
        """Alert message should contain all metrics."""
        r = _run(tmp_path, disk_pct=73, failed_units=1, tg_notify=False)
        assert "disk=73%" in r.stderr
        assert "failed_units=1" in r.stderr


# ── combined conditions ────────────────────────────────────────────────


class TestCombined:
    def test_both_high_disk_and_failed(self, tmp_path):
        """Both triggers → single alert with all metrics."""
        r = _run(tmp_path, disk_pct=90, failed_units=3, tg_notify=False)
        assert r.returncode == 1
        assert "disk=90%" in r.stderr
        assert "failed_units=3" in r.stderr


# ── edge cases ──────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_tg_notify_not_executable(self, tmp_path):
        """tg-notify.sh exists but is not executable → falls through to stderr."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        tg = scripts_dir / "tg-notify.sh"
        tg.write_text("#!/bin/bash\nexit 0\n")
        # deliberately do NOT chmod +x
        r = _run(tmp_path, disk_pct=90, failed_units=0, tg_notify=False)
        assert r.returncode == 1
        assert "ALERT:" in r.stderr
        # tg-notify.sh should NOT have been called
        assert not (tmp_path / "tg.log").exists()

    def test_systemctl_nonzero_falls_back_to_zero(self, tmp_path):
        """systemctl exits non-zero → FAILED defaults to 0, still healthy."""
        mock_dir = tmp_path / "mock-bin"
        mock_dir.mkdir()
        _make_mock(mock_dir, "df", "Use%\n  50%")
        _make_mock(mock_dir, "free", "              total       used\nMem: 4096 8192")
        # systemctl that exits 1 (non-zero)
        _make_mock(mock_dir, "systemctl", "", exit_code=1)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = str(mock_dir) + os.pathsep + env.get("PATH", "")

        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True, text=True, env=env, timeout=10,
        )
        assert r.returncode == 0
        assert "pharos health: ok" in r.stdout

    def test_memory_format_in_healthy_output(self, tmp_path):
        """Memory should appear as used/totalMB in healthy output."""
        # mem_line "Mem: 2048 1024" → awk prints $3/$2MB = "1024/2048MB"
        r = _run(tmp_path, disk_pct=50, mem_line="Mem: 2048 1024", failed_units=0)
        assert r.returncode == 0
        assert "1024/2048MB" in r.stdout

    def test_memory_format_in_alert(self, tmp_path):
        """Memory should appear as used/totalMB in alert output."""
        r = _run(tmp_path, disk_pct=90, mem_line="Mem: 4096 2048", failed_units=0, tg_notify=False)
        assert r.returncode == 1
        assert "2048/4096MB" in r.stderr

    def test_disk_100_percent(self, tmp_path):
        """Extreme disk value triggers alert."""
        r = _run(tmp_path, disk_pct=100, failed_units=0)
        assert r.returncode == 1
        assert "disk=100%" in r.stderr

    def test_help_mentions_threshold(self, tmp_path):
        """--help output mentions the 85% threshold."""
        r = _run(tmp_path, args=["--help"])
        assert "85%" in r.stdout
