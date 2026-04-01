from __future__ import annotations

"""Tests for effectors/pharos-health.sh — system health checker."""

import os
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT = Path.home() / "germline" / "effectors" / "pharos-health.sh"


def _make_mock_bin(tmpdir: Path, name: str, body: str) -> Path:
    """Create an executable mock script in tmpdir."""
    p = tmpdir / name
    p.write_text(f"#!/bin/bash\n{body}\n")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return p


def _run(tmpdir: Path, args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run pharos-health.sh with PATH pointing to mock binaries in tmpdir."""
    env = os.environ.copy()
    env["PATH"] = f"{tmpdir}:{env.get('PATH', '/usr/bin:/bin')}"
    env["HOME"] = str(tmpdir)
    cmd = [str(SCRIPT)] + (args or [])
    return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=10)


def _mock_df(tmpdir: Path, pct: int) -> None:
    """Mock df to output --output=pcent format: 'Use%\\n XX%'."""
    # Use two echo lines to avoid printf % escaping issues
    _make_mock_bin(tmpdir, "df", f'echo "Use%"\necho " {pct}%"')


def _mock_free(tmpdir: Path) -> None:
    """Mock free -m with realistic output for awk to parse the Mem: line."""
    _make_mock_bin(
        tmpdir,
        "free",
        'echo "               total        used        free      shared  buff/cache   available"\n'
        'echo "Mem:           8000        2000        4000         128        2000        5000"\n'
        'echo "Swap:          2048           0        2048"',
    )


def _mock_systemctl(tmpdir: Path, failed_lines: int = 0) -> None:
    """Mock systemctl --user --failed --no-legend with N failed units."""
    if failed_lines == 0:
        _make_mock_bin(tmpdir, "systemctl", "exit 0")
    else:
        lines = "\n".join(
            [f"echo 'unit{i}.service  loaded  failed  failed  desc'" for i in range(failed_lines)]
        )
        _make_mock_bin(tmpdir, "systemctl", lines)


def _setup_healthy(tmpdir: Path) -> None:
    _mock_df(tmpdir, 40)
    _mock_free(tmpdir)
    _mock_systemctl(tmpdir, 0)


def _setup_high_disk(tmpdir: Path, pct: int = 90) -> None:
    _mock_df(tmpdir, pct)
    _mock_free(tmpdir)
    _mock_systemctl(tmpdir, 0)


def _setup_failed_units(tmpdir: Path, count: int = 3) -> None:
    _mock_df(tmpdir, 40)
    _mock_free(tmpdir)
    _mock_systemctl(tmpdir, count)


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
        assert "Exit 0" in r.stdout or "exit 0" in r.stdout.lower()


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
        assert "failed_units=0" in r.stdout


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
    """Without tg-notify.sh, alert goes to stderr with ALERT prefix."""
    with tempfile.TemporaryDirectory() as td:
        _setup_high_disk(Path(td), 90)
        r = _run(Path(td))
        assert r.returncode != 0
        assert "ALERT:" in r.stderr


# ── Failed systemd units tests ───────────────────────────────────────


def test_failed_units_exits_nonzero():
    """Failed systemd units trigger exit 1."""
    with tempfile.TemporaryDirectory() as td:
        _setup_failed_units(Path(td), 2)
        r = _run(Path(td))
        assert r.returncode != 0


def test_failed_units_count_in_output():
    """Alert message includes failed_units count."""
    with tempfile.TemporaryDirectory() as td:
        _setup_failed_units(Path(td), 3)
        r = _run(Path(td))
        output = r.stdout + r.stderr
        assert "failed_units=" in output


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
        _mock_df(tmp, 90)
        _mock_free(tmp)
        _mock_systemctl(tmp, 2)
        r = _run(tmp)
        assert r.returncode != 0


def test_combined_alert_has_both_fields():
    """Combined alert output contains both disk and failed_units."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _mock_df(tmp, 90)
        _mock_free(tmp)
        _mock_systemctl(tmp, 2)
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
        scripts_dir = tmp / "scripts"
        scripts_dir.mkdir()
        tg_script = scripts_dir / "tg-notify.sh"
        tg_script.write_text('#!/bin/bash\necho "SHOULD NOT BE CALLED" > /tmp/pharos_test_bug\nexit 99\n')
        tg_script.chmod(tg_script.stat().st_mode | stat.S_IEXEC)
        r = _run(tmp)
        assert r.returncode == 0
        assert not Path("/tmp/pharos_test_bug").exists()


def test_non_executable_tg_notify_falls_back():
    """When tg-notify.sh exists but is not executable, falls back to stderr."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        _setup_high_disk(tmp, 90)
        scripts_dir = tmp / "scripts"
        scripts_dir.mkdir()
        tg_script = scripts_dir / "tg-notify.sh"
        tg_script.write_text("#!/bin/bash\nexit 0\n")
        # Deliberately NOT making it executable
        r = _run(tmp)
        assert r.returncode != 0
        assert "ALERT:" in r.stderr


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
