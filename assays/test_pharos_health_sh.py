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


# ── script metadata ─────────────────────────────────────────────────────


class TestScriptMetadata:
    def test_script_is_executable(self):
        """The script file should have execute permission."""
        assert SCRIPT.exists()
        mode = SCRIPT.stat().st_mode
        assert mode & stat.S_IXUSR, f"{SCRIPT} is not user-executable"

    def test_script_starts_with_shebang(self):
        """First line must be a bash shebang."""
        first = SCRIPT.read_text().splitlines()[0]
        assert first == "#!/bin/bash"

    def test_script_uses_strict_mode(self):
        """Script uses set -euo pipefail for safety."""
        content = SCRIPT.read_text()
        assert "set -euo pipefail" in content


# ── help content ─────────────────────────────────────────────────────────


class TestHelpContent:
    def test_help_mentions_systemd(self, tmp_path):
        """--help mentions systemd unit checking."""
        r = _run(tmp_path, args=["--help"])
        assert "systemd" in r.stdout.lower()

    def test_help_mentions_exit_codes(self, tmp_path):
        """--help explains exit 0 = healthy, exit 1 = alert."""
        r = _run(tmp_path, args=["--help"])
        assert "exit 0" in r.stdout or "Exit 0" in r.stdout

    def test_help_empty_args(self, tmp_path):
        """Running with no --help performs actual health check."""
        r = _run(tmp_path, disk_pct=50, failed_units=0)
        # Should produce health output, not usage
        assert "pharos health:" in r.stdout


# ── disk boundary values ────────────────────────────────────────────────


class TestDiskBoundary:
    def test_disk_84_is_healthy(self, tmp_path):
        """84% is safely below the 85% threshold."""
        r = _run(tmp_path, disk_pct=84, failed_units=0)
        assert r.returncode == 0

    def test_disk_87_triggers_alert(self, tmp_path):
        """87% is above threshold."""
        r = _run(tmp_path, disk_pct=87, failed_units=0, tg_notify=False)
        assert r.returncode == 1

    def test_disk_0_is_healthy(self, tmp_path):
        """0% disk usage is perfectly healthy."""
        r = _run(tmp_path, disk_pct=0, failed_units=0)
        assert r.returncode == 0
        assert "disk=0%" in r.stdout

    def test_disk_1_is_healthy(self, tmp_path):
        """1% disk usage is healthy."""
        r = _run(tmp_path, disk_pct=1, failed_units=0)
        assert r.returncode == 0


# ── alert message format ────────────────────────────────────────────────


class TestAlertFormat:
    def test_alert_starts_with_pharos_health(self, tmp_path):
        """Alert message begins with 'pharos health:'."""
        r = _run(tmp_path, disk_pct=90, failed_units=0, tg_notify=False)
        assert "pharos health:" in r.stderr

    def test_alert_includes_mem(self, tmp_path):
        """Alert message includes memory info."""
        r = _run(
            tmp_path,
            disk_pct=90,
            mem_line="Mem: 8192 4096",
            failed_units=0,
            tg_notify=False,
        )
        assert "mem=" in r.stderr
        assert "MB" in r.stderr

    def test_tg_notify_receives_pharos_prefix(self, tmp_path):
        """tg-notify.sh is called with the full 'pharos health: ...' message."""
        r = _run(tmp_path, disk_pct=95, failed_units=0, tg_notify=True)
        assert r.returncode == 1
        log = (tmp_path / "tg.log").read_text()
        assert log.startswith("pharos health:")

    def test_healthy_output_starts_with_pharos_health(self, tmp_path):
        """Healthy output contains 'pharos health: ok'."""
        r = _run(tmp_path, disk_pct=50, failed_units=0)
        assert r.stdout.strip().startswith("pharos health:")


# ── failed units edge cases ─────────────────────────────────────────────


class TestFailedUnitsEdge:
    def test_many_failed_units(self, tmp_path):
        """Large number of failed units still works."""
        r = _run(tmp_path, disk_pct=50, failed_units=50, tg_notify=False)
        assert r.returncode == 1
        assert "failed_units=50" in r.stderr

    def test_single_failed_unit_format(self, tmp_path):
        """One failed unit includes count=1."""
        r = _run(tmp_path, disk_pct=50, failed_units=1, tg_notify=False)
        assert "failed_units=1" in r.stderr


# ── combined conditions with tg-notify ──────────────────────────────────


class TestCombinedTgNotify:
    def test_both_triggers_tg_notify(self, tmp_path):
        """Both high disk and failed units → tg-notify called with all metrics."""
        r = _run(tmp_path, disk_pct=95, failed_units=2, tg_notify=True)
        assert r.returncode == 1
        log = (tmp_path / "tg.log").read_text()
        assert "disk=95%" in log
        assert "failed_units=2" in log
        assert "mem=" in log

    def test_low_disk_no_failed_tg_not_called(self, tmp_path):
        """Healthy state should not trigger tg-notify even if it exists."""
        r = _run(tmp_path, disk_pct=50, failed_units=0, tg_notify=True)
        assert r.returncode == 0
        assert not (tmp_path / "tg.log").exists()
