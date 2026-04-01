from __future__ import annotations

"""Tests for effectors/pharos-health.sh — system health checker."""

import os
import stat
import subprocess
from pathlib import Path

SCRIPT = Path("/home/terry/germline/effectors/pharos-health.sh")


def _run(args: list[str] | None = None, *, env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run pharos-health.sh with optional extra env vars."""
    env = os.environ.copy()
    env["LANG"] = "C"
    if env_extra:
        env.update(env_extra)
    cmd = [str(SCRIPT)] + (args or [])
    return subprocess.run(cmd, capture_output=True, text=True, timeout=10, env=env)


def _env_for(tmp: Path, bin_dir: Path) -> dict[str, str]:
    """Build env dict: mocked PATH + HOME pointing to tmp (no real tg-notify.sh)."""
    return {"PATH": f"{bin_dir}:{os.environ['PATH']}", "HOME": str(tmp)}


def _make_mock_dir(tmp: Path, *, disk_pct: int = 20, mem_used: int = 512, mem_total: int = 2048, failed_units: int = 0) -> Path:
    """Create a temp bin/ with mock df, free, systemctl and return it."""
    bin_dir = tmp / "bin"
    bin_dir.mkdir(exist_ok=True)

    # mock df
    df = bin_dir / "df"
    df.write_text(f'#!/bin/bash\nif [ "$1" = "/" ] && [ "$2" = "--output=pcent" ]; then\n    echo "Use%"\n    echo "  {disk_pct}%"\nelse\n    /usr/bin/df "$@"\nfi\n')
    df.chmod(df.stat().st_mode | stat.S_IEXEC)

    # mock free
    free = bin_dir / "free"
    free.write_text(f'#!/bin/bash\nif [ "$1" = "-m" ]; then\n    echo "              total        used        free"\n    echo "Mem:          {mem_total}        {mem_used}        {mem_total - mem_used}"\nelse\n    /usr/bin/free "$@"\nfi\n')
    free.chmod(free.stat().st_mode | stat.S_IEXEC)

    # mock systemctl — output nothing when 0 failed units (wc -l must see 0 lines)
    sc = bin_dir / "systemctl"
    if failed_units > 0:
        lines = "\n".join(["unit1.service  failed"] * failed_units)
        sc.write_text(f'#!/bin/bash\nif [ "$1" = "--user" ]; then\nprintf "%s\\n" {repr(lines)}\nexit 0\nelse\n/usr/bin/systemctl "$@"\nfi\n')
    else:
        sc.write_text('#!/bin/bash\nif [ "$1" = "--user" ]; then\n    exit 0\nelse\n    /usr/bin/systemctl "$@"\nfi\n')
    sc.chmod(sc.stat().st_mode | stat.S_IEXEC)

    return bin_dir


# ── --help tests ──────────────────────────────────────────────────────


def test_help_long_flag_exits_zero():
    """--help prints usage and exits 0."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "Usage: pharos-health.sh" in r.stdout


def test_help_short_flag_exits_zero():
    """-h prints usage and exits 0."""
    r = _run(["-h"])
    assert r.returncode == 0
    assert "Check system health" in r.stdout


def test_help_mentions_disk_threshold():
    """Help text mentions the 85% disk threshold."""
    r = _run(["--help"])
    assert "85%" in r.stdout


def test_help_mentions_exit_codes():
    """Help text documents exit codes."""
    r = _run(["--help"])
    assert "exit 0" in r.stdout.lower() or "Exit 0" in r.stdout


# ── healthy system tests ──────────────────────────────────────────────


def test_healthy_system_exits_zero(tmp_path):
    """Low disk + no failed units → exit 0."""
    bin_dir = _make_mock_dir(tmp_path, disk_pct=20, failed_units=0)
    r = _run(env_extra=_env_for(tmp_path, bin_dir))
    assert r.returncode == 0
    assert "ok" in r.stdout


def test_healthy_output_contains_disk_pct(tmp_path):
    """Healthy output includes disk percentage."""
    bin_dir = _make_mock_dir(tmp_path, disk_pct=42)
    r = _run(env_extra=_env_for(tmp_path, bin_dir))
    assert r.returncode == 0
    assert "disk=42%" in r.stdout


def test_healthy_output_contains_mem_info(tmp_path):
    """Healthy output includes memory info in MB."""
    bin_dir = _make_mock_dir(tmp_path, mem_used=512, mem_total=2048)
    r = _run(env_extra=_env_for(tmp_path, bin_dir))
    assert r.returncode == 0
    assert "512/2048MB" in r.stdout


def test_healthy_output_contains_failed_units(tmp_path):
    """Healthy output includes failed_units=0."""
    bin_dir = _make_mock_dir(tmp_path, failed_units=0)
    r = _run(env_extra=_env_for(tmp_path, bin_dir))
    assert r.returncode == 0
    assert "failed_units=0" in r.stdout


# ── disk alert tests ──────────────────────────────────────────────────


def test_high_disk_exits_one(tmp_path):
    """Disk > 85% triggers alert and exit 1."""
    bin_dir = _make_mock_dir(tmp_path, disk_pct=92, failed_units=0)
    r = _run(env_extra={"PATH": f"{bin_dir}:{os.environ['PATH']}", "HOME": str(tmp_path)})
    assert r.returncode == 1


def test_high_disk_alert_message(tmp_path):
    """Alert message contains disk percentage."""
    bin_dir = _make_mock_dir(tmp_path, disk_pct=92, failed_units=0)
    r = _run(env_extra={"PATH": f"{bin_dir}:{os.environ['PATH']}", "HOME": str(tmp_path)})
    assert "disk=92%" in (r.stdout + r.stderr)


def test_disk_exactly_85_no_alert(tmp_path):
    """Disk exactly at 85% is NOT over threshold (needs > 85)."""
    bin_dir = _make_mock_dir(tmp_path, disk_pct=85, failed_units=0)
    r = _run(env_extra={"PATH": f"{bin_dir}:{os.environ['PATH']}"})
    assert r.returncode == 0


def test_disk_at_86_triggers_alert(tmp_path):
    """Disk at 86% triggers alert."""
    bin_dir = _make_mock_dir(tmp_path, disk_pct=86, failed_units=0)
    r = _run(env_extra={"PATH": f"{bin_dir}:{os.environ['PATH']}", "HOME": str(tmp_path)})
    assert r.returncode == 1


def test_disk_at_threshold_boundary_84(tmp_path):
    """Disk at 84% is healthy."""
    bin_dir = _make_mock_dir(tmp_path, disk_pct=84, failed_units=0)
    r = _run(env_extra={"PATH": f"{bin_dir}:{os.environ['PATH']}"})
    assert r.returncode == 0


# ── failed units alert tests ──────────────────────────────────────────


def test_failed_units_exits_one(tmp_path):
    """Any failed systemd units trigger alert and exit 1."""
    bin_dir = _make_mock_dir(tmp_path, disk_pct=20, failed_units=1)
    r = _run(env_extra={"PATH": f"{bin_dir}:{os.environ['PATH']}", "HOME": str(tmp_path)})
    assert r.returncode == 1


def test_failed_units_in_alert_message(tmp_path):
    """Alert message includes failed unit count."""
    bin_dir = _make_mock_dir(tmp_path, disk_pct=20, failed_units=3)
    r = _run(env_extra={"PATH": f"{bin_dir}:{os.environ['PATH']}", "HOME": str(tmp_path)})
    combined = r.stdout + r.stderr
    assert "failed_units=3" in combined


# ── combined alert tests ──────────────────────────────────────────────


def test_both_disk_and_failed_units(tmp_path):
    """Both high disk AND failed units → alert with both values."""
    bin_dir = _make_mock_dir(tmp_path, disk_pct=95, failed_units=2)
    r = _run(env_extra={"PATH": f"{bin_dir}:{os.environ['PATH']}", "HOME": str(tmp_path)})
    assert r.returncode == 1
    combined = r.stdout + r.stderr
    assert "disk=95%" in combined
    assert "failed_units=2" in combined


# ── no tg-notify fallback ─────────────────────────────────────────────


def test_alert_without_tg_notify_goes_to_stderr(tmp_path):
    """Alert goes to stderr when tg-notify.sh is absent."""
    bin_dir = _make_mock_dir(tmp_path, disk_pct=90, failed_units=0)
    # HOME points to tmp_path which has no scripts/tg-notify.sh
    r = _run(env_extra={"PATH": f"{bin_dir}:{os.environ['PATH']}", "HOME": str(tmp_path)})
    assert r.returncode == 1
    assert "ALERT:" in r.stderr


def test_healthy_no_stderr(tmp_path):
    """Healthy system produces no stderr output."""
    bin_dir = _make_mock_dir(tmp_path, disk_pct=20, failed_units=0)
    r = _run(env_extra={"PATH": f"{bin_dir}:{os.environ['PATH']}"})
    assert r.returncode == 0
    assert r.stderr.strip() == ""


# ── output format tests ───────────────────────────────────────────────


def test_healthy_output_starts_with_prefix(tmp_path):
    """Healthy output starts with 'pharos health: ok'."""
    bin_dir = _make_mock_dir(tmp_path, disk_pct=10, failed_units=0)
    r = _run(env_extra={"PATH": f"{bin_dir}:{os.environ['PATH']}"})
    assert r.returncode == 0
    assert "pharos health: ok" in r.stdout


def test_no_args_runs_normally(tmp_path):
    """Running with no arguments executes the health check."""
    bin_dir = _make_mock_dir(tmp_path, disk_pct=30, failed_units=0)
    r = _run(env_extra={"PATH": f"{bin_dir}:{os.environ['PATH']}"})
    assert r.returncode == 0
    assert "pharos health:" in r.stdout
