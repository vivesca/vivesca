from __future__ import annotations

"""Tests for pharos-health.sh — system health checker (disk, memory, failed units)."""

import os
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT = Path("/home/terry/germline/effectors/pharos-health.sh")


def _make_mock_bin(tmpdir: Path, name: str, content: str) -> Path:
    """Create an executable mock script in tmpdir."""
    path = tmpdir / name
    path.write_text(f"#!/bin/bash\n{content}\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


def _run(tmpdir: Path, args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run pharos-health.sh with PATH pointing to mock binaries."""
    env = os.environ.copy()
    # Prepend tmpdir to PATH so mock binaries take priority
    env["PATH"] = f"{tmpdir}:{env.get('PATH', '/usr/bin:/bin')}"
    env["HOME"] = str(tmpdir)  # Redirect ~ to tmpdir so tg-notify.sh not found
    cmd = [str(SCRIPT)] + (args or [])
    return subprocess.run(
        cmd, capture_output=True, text=True, env=env, timeout=10
    )


def _mock_df(tmpdir: Path, pct: int) -> Path:
    """Mock df to output pcent format: 'Use%\\n XX%'."""
    _make_mock_bin(tmpdir, "df", f'printf "Use%\\n {pct}%\\n"')
    return tmpdir


def _mock_free(tmpdir: Path) -> Path:
    """Mock free -m with realistic output for awk parsing."""
    _make_mock_bin(
        tmpdir,
        "free",
        'printf "               total        used        free      shared  buff/cache   available\\n'
        'Mem:           8000        2000        4000         128        2000        5000\\n'
        'Swap:          2048           0        2048\\n"',
    )
    return tmpdir


def _mock_systemctl(tmpdir: Path, failed_lines: int = 0) -> Path:
    """Mock systemctl --user --failed --no-legend with N failed units."""
    lines = "\\n".join([f"unit{i}.service  loaded  failed  failed  desc" for i in range(failed_lines)])
    _make_mock_bin(tmpdir, "systemctl", f'printf "{lines}\\n"')
    return tmpdir


def _setup_healthy(tmpdir: Path) -> Path:
    """Set up mocks for a healthy system (disk=40%, no failed units)."""
    _mock_df(tmpdir, 40)
    _mock_free(tmpdir)
    _mock_systemctl(tmpdir, 0)
    return tmpdir


def _setup_high_disk(tmpdir: Path, pct: int = 90) -> Path:
    """Set up mocks for high disk usage."""
    _mock_df(tmpdir, pct)
    _mock_free(tmpdir)
    _mock_systemctl(tmpdir, 0)
    return tmpdir


def _setup_failed_units(tmpdir: Path, count: int = 3) -> Path:
    """Set up mocks with failed systemd units."""
    _mock_df(tmpdir, 40)
    _mock_free(tmpdir)
    _mock_systemctl(tmpdir, count)
    return tmpdir


# ── Help flag tests ───────────────────────────────────────────────────


def test_help_flag_exits_zero():
    """--help exits 0 and shows usage."""
    with tempfile.TemporaryDirectory() as td:
        r = _run(Path(td), ["--help"])
        assert r.returncode == 0
        assert "Usage:" in r.stdout


def test_h_short_flag_exits_zero():
    """Short -h flag exits 0 and shows usage."""
    with tempfile.TemporaryDirectory() as td:
        r = _run(Path(td), ["-h"])
        assert r.returncode == 0
        assert "Usage:" in r.stdout


def test_help_mentions_disk():
    """Help text mentions disk checking."""
    with tempfile.TemporaryDirectory() as td:
        r = _run(Path(td), ["--help"])
        assert "disk" in r.stdout.lower()


def test_help_mentions_systemd():
    """Help text mentions systemd units."""
    with tempfile.TemporaryDirectory() as td:
        r = _run(Path(td), ["--help"])
        assert "systemd" in r.stdout.lower()


def test_help_exit_codes_documented():
    """Help text documents exit codes."""
    with tempfile.TemporaryDirectory() as td:
        r = _run(Path(td), ["--help"])
        assert "exit 0" in r.stdout.lower() or "Exit 0" in r.stdout


# ── Healthy system tests ─────────────────────────────────────────────


def test_healthy_exits_zero():
    """Healthy system (disk=40%, no failed units) exits 0."""
    with tempfile.TemporaryDirectory() as td:
        _setup_healthy(Path(td))
        r = _run(Path(td))
        assert r.returncode == 0


def test_healthy_outputs_ok():
    """Healthy system output contains 'ok'."""
    with tempfile.TemporaryDirectory() as td:
        _setup_healthy(Path(td))
        r = _run(Path(td))
        assert "ok" in r.stdout.lower()


def test_healthy_output_has_disk_field():
    """Healthy output includes disk percentage."""
    with tempfile.TemporaryDirectory() as td:
        _setup_healthy(Path(td))
        r = _run(Path(td))
        assert "disk=" in r.stdout


def test_healthy_output_has_mem_field():
    """Healthy output includes memory info."""
    with tempfile.TemporaryDirectory() as td:
        _setup_healthy(Path(td))
        r = _run(Path(td))
        assert "mem=" in r.stdout.lower()


def test_healthy_output_has_failed_units():
    """Healthy output includes failed_units count."""
    with tempfile.TemporaryDirectory() as td:
        _setup_healthy(Path(td))
        r = _run(Path(td))
        assert "failed_units=" in r.stdout


def test_healthy_stderr_empty():
    """Healthy system produces no stderr output."""
    with tempfile.TemporaryDirectory() as td:
        _setup_healthy(Path(td))
        r = _run(Path(td))
        assert r.stderr.strip() == ""


# ── High disk alert tests ────────────────────────────────────────────


def test_high_disk_exits_nonzero():
    """Disk usage > 85% triggers exit 1."""
    with tempfile.TemporaryDirectory() as td:
        _setup_high_disk(Path(td), 90)
        r = _run(Path(td))
        assert r.returncode != 0


def test_disk_at_85_is_healthy():
    """Disk exactly at 85% is still healthy (threshold is > 85)."""
    with tempfile.TemporaryDirectory() as td:
        _setup_high_disk(Path(td), 85)
        r = _run(Path(td))
        assert r.returncode == 0


def test_disk_at_86_is_unhealthy():
    """Disk at 86% triggers alert."""
    with tempfile.TemporaryDirectory() as td:
        _setup_high_disk(Path(td), 86)
        r = _run(Path(td))
        assert r.returncode != 0


def test_high_disk_alert_contains_disk_pct():
    """Alert message contains the disk percentage."""
    with tempfile.TemporaryDirectory() as td:
        _setup_high_disk(Path(td), 92)
        r = _run(Path(td))
        output = r.stdout + r.stderr
        assert "92" in output


def test_high_disk_stderr_alert_when_no_notify():
    """Without tg-notify.sh, alert goes to stderr."""
    with tempfile.TemporaryDirectory() as td:
        _setup_high_disk(Path(td), 90)
        r = _run(Path(td))
        assert "ALERT" in r.stderr or "ALERT" in r.stdout


# ── Failed systemd units tests ───────────────────────────────────────


def test_failed_units_exits_nonzero():
    """Failed systemd units trigger exit 1."""
    with tempfile.TemporaryDirectory() as td:
        _setup_failed_units(Path(td), 2)
        r = _run(Path(td))
        assert r.returncode != 0


def test_failed_units_count_in_output():
    """Alert message includes the count of failed units."""
    with tempfile.TemporaryDirectory() as td:
        _setup_failed_units(Path(td), 3)
        r = _run(Path(td))
        output = r.stdout + r.stderr
        assert "failed_units=3" in output


def test_zero_failed_units_healthy():
    """Zero failed units with normal disk is healthy."""
    with tempfile.TemporaryDirectory() as td:
        _setup_healthy(Path(td))
        r = _run(Path(td))
        assert r.returncode == 0


# ── Combined alert tests ─────────────────────────────────────────────


def test_both_disk_and_failed_alerts():
    """Both high disk and failed units trigger alert (exit 1)."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _make_mock_bin(tmp, "df", 'echo "Use  Mount\n 90%  /"')
        _make_mock_bin(tmp, "free", 'echo "              total        used        free\nMem:       8000       2000       6000"')
        _make_mock_bin(tmp, "systemctl", 'echo "unit.service failed failed"')
        _make_mock_bin(tmp, "wc", 'echo "1"')
        _make_mock_bin(tmp, "awk", 'echo "2000/8000MB"')
        _make_mock_bin(tmp, "tr", 'cat')
        r = _run(tmp)
        assert r.returncode != 0


def test_combined_alert_has_both_fields():
    """Combined alert output contains both disk and failed_units."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _make_mock_bin(tmp, "df", 'echo "Use  Mount\n 90%  /"')
        _make_mock_bin(tmp, "free", 'echo "              total        used        free\nMem:       8000       2000       6000"')
        _make_mock_bin(tmp, "systemctl", 'echo "unit.service failed failed"')
        _make_mock_bin(tmp, "wc", 'echo "1"')
        _make_mock_bin(tmp, "awk", 'echo "2000/8000MB"')
        _make_mock_bin(tmp, "tr", 'cat')
        r = _run(tmp)
        output = r.stdout + r.stderr
        assert "disk=" in output
        assert "failed_units=" in output


# ── Telegram notify path tests ───────────────────────────────────────


def test_tg_notify_called_when_exists():
    """When tg-notify.sh exists and is executable, it receives the alert message."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _setup_high_disk(tmp, 90)
        # Create scripts dir with tg-notify.sh that records its input
        notify_log = tmp / "notify_called.txt"
        scripts_dir = tmp / "scripts"
        scripts_dir.mkdir()
        tg_script = scripts_dir / "tg-notify.sh"
        tg_script.write_text(f'#!/bin/bash\necho "$1" > {notify_log}\n')
        tg_script.chmod(tg_script.stat().st_mode | stat.S_IEXEC)
        r = _run(tmp)
        assert r.returncode != 0
        assert notify_log.exists()
        msg = notify_log.read_text().strip()
        assert "pharos health" in msg
        assert "disk=" in msg


def test_tg_notify_not_called_when_healthy():
    """When healthy, tg-notify.sh is never invoked."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _setup_healthy(tmp)
        # Create scripts dir with tg-notify that would fail if called
        scripts_dir = tmp / "scripts"
        scripts_dir.mkdir()
        tg_script = scripts_dir / "tg-notify.sh"
        tg_script.write_text('#!/bin/bash\necho "SHOULD NOT BE CALLED" > /tmp/pharos_test_bug\nexit 99\n')
        tg_script.chmod(tg_script.stat().st_mode | stat.S_IEXEC)
        r = _run(tmp)
        assert r.returncode == 0
        assert not (Path("/tmp/pharos_test_bug")).exists()


def test_non_executable_tg_notify_falls_back():
    """When tg-notify.sh exists but is not executable, falls back to stderr."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _setup_high_disk(tmp, 90)
        scripts_dir = tmp / "scripts"
        scripts_dir.mkdir()
        tg_script = scripts_dir / "tg-notify.sh"
        tg_script.write_text('#!/bin/bash\nexit 0\n')
        # Deliberately NOT making it executable
        r = _run(tmp)
        assert r.returncode != 0
        assert "ALERT" in r.stderr or "ALERT" in r.stdout


# ── Output format tests ──────────────────────────────────────────────


def test_output_starts_with_pharos():
    """Output line starts with 'pharos health'."""
    with tempfile.TemporaryDirectory() as td:
        _setup_healthy(Path(td))
        r = _run(Path(td))
        assert "pharos health" in r.stdout


def test_output_format_field_order():
    """Output has consistent field order: disk, mem, failed_units."""
    with tempfile.TemporaryDirectory() as td:
        _setup_healthy(Path(td))
        r = _run(Path(td))
        out = r.stdout
        disk_idx = out.index("disk=")
        mem_idx = out.index("mem=")
        failed_idx = out.index("failed_units=")
        assert disk_idx < mem_idx < failed_idx


# ── Edge case tests ──────────────────────────────────────────────────


def test_disk_exactly_100_alerts():
    """Disk at 100% triggers alert."""
    with tempfile.TemporaryDirectory() as td:
        _setup_high_disk(Path(td), 100)
        r = _run(Path(td))
        assert r.returncode != 0


def test_disk_exactly_0_healthy():
    """Disk at 0% is healthy."""
    with tempfile.TemporaryDirectory() as td:
        _setup_high_disk(Path(td), 0)
        r = _run(Path(td))
        assert r.returncode == 0
