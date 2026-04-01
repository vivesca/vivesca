from __future__ import annotations

"""Tests for pharos-health.sh — system health checker (disk, memory, systemd).

Effectors are scripts — tested via subprocess.run, never imported.
Fake df/free/systemctl binaries are placed on a temp PATH to control inputs.
"""

import os
import stat
import subprocess
from pathlib import Path

SCRIPT = Path.home() / "germline" / "effectors" / "pharos-health.sh"


# ── helpers ────────────────────────────────────────────────────────────────


def _run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run pharos-health.sh with optional env overrides."""
    kw: dict = dict(capture_output=True, text=True, timeout=5)
    if env is not None:
        kw["env"] = env
    return subprocess.run([str(SCRIPT), *args], **kw)


def _make_bin(tmpdir: Path, name: str, body: str) -> Path:
    """Write a fake executable into tmpdir and return its path."""
    p = tmpdir / name
    p.write_text(f"#!/bin/bash\n{body}\n")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return p


def _env_with_path(tmpdir: Path) -> dict:
    """Base env with tmpdir prepended to PATH so fakes take priority."""
    e = os.environ.copy()
    e["PATH"] = str(tmpdir) + ":" + e.get("PATH", "/usr/bin:/bin")
    # Prevent real tg-notify.sh from being found
    e["HOME"] = "/nonexistent/home"
    return e


# ── help / usage ───────────────────────────────────────────────────────────


def test_help_long():
    """--help prints usage and exits 0."""
    r = _run("--help")
    assert r.returncode == 0
    assert "Usage: pharos-health.sh" in r.stdout
    assert "disk" in r.stdout.lower() or "health" in r.stdout.lower()


def test_help_short():
    """-h prints usage and exits 0."""
    r = _run("-h")
    assert r.returncode == 0
    assert "Usage: pharos-health.sh" in r.stdout


def test_help_mentions_exit_codes():
    """--help output mentions exit codes 0 and 1."""
    r = _run("--help")
    assert "exit 0" in r.stdout.lower() or "exit 1" in r.stdout.lower()


# ── healthy system ─────────────────────────────────────────────────────────


def test_healthy_disk_below_threshold(tmp_path):
    """Disk at 40% with no failed units → exit 0, 'ok' in output."""
    _make_bin(tmp_path, "df", 'echo "Use%"; echo " 40%"')
    _make_bin(tmp_path, "free", 'echo "Mem: 1024 512 512"')
    _make_bin(tmp_path, "systemctl", "exit 0")
    env = _env_with_path(tmp_path)

    r = _run(env=env)
    assert r.returncode == 0
    assert "ok" in r.stdout.lower()
    assert "disk=40%" in r.stdout


def test_healthy_output_format(tmp_path):
    """Healthy output includes disk, mem, and failed_units fields."""
    _make_bin(tmp_path, "df", 'echo "Use%"; echo " 25%"')
    _make_bin(tmp_path, "free", 'echo "              total        used"; echo "Mem:       8192       4096"')
    _make_bin(tmp_path, "systemctl", "exit 0")
    env = _env_with_path(tmp_path)

    r = _run(env=env)
    assert r.returncode == 0
    assert "disk=25%" in r.stdout
    assert "failed_units=0" in r.stdout


def test_healthy_exactly_at_85(tmp_path):
    """Disk at exactly 85% is still healthy (threshold is > 85)."""
    _make_bin(tmp_path, "df", 'echo "Use%"; echo " 85%"')
    _make_bin(tmp_path, "free", 'echo "Mem: 2048 1024 1024"')
    _make_bin(tmp_path, "systemctl", "exit 0")
    env = _env_with_path(tmp_path)

    r = _run(env=env)
    assert r.returncode == 0
    assert "ok" in r.stdout.lower()


# ── disk alert ─────────────────────────────────────────────────────────────


def test_disk_alert_above_85(tmp_path):
    """Disk at 90% triggers alert → exit 1."""
    _make_bin(tmp_path, "df", 'echo "Use%"; echo " 90%"')
    _make_bin(tmp_path, "free", 'echo "Mem: 2048 512 1536"')
    _make_bin(tmp_path, "systemctl", "exit 0")
    env = _env_with_path(tmp_path)

    r = _run(env=env)
    assert r.returncode == 1


def test_disk_alert_stderr_message(tmp_path):
    """Alert when tg-notify.sh is absent prints ALERT to stderr."""
    _make_bin(tmp_path, "df", 'echo "Use%"; echo " 92%"')
    _make_bin(tmp_path, "free", 'echo "Mem: 4096 2048 2048"')
    _make_bin(tmp_path, "systemctl", "exit 0")
    env = _env_with_path(tmp_path)

    r = _run(env=env)
    assert r.returncode == 1
    assert "ALERT" in r.stderr
    assert "disk=92%" in r.stderr


def test_disk_alert_includes_memory_info(tmp_path):
    """Alert message includes memory info."""
    _make_bin(tmp_path, "df", 'echo "Use%"; echo " 99%"')
    _make_bin(tmp_path, "free", 'echo "              total        used"; echo "Mem:       4096       2048"')
    _make_bin(tmp_path, "systemctl", "exit 0")
    env = _env_with_path(tmp_path)

    r = _run(env=env)
    assert r.returncode == 1
    assert "mem=" in r.stderr


# ── failed systemd units ──────────────────────────────────────────────────


def test_failed_units_alert(tmp_path):
    """Failed systemd units > 0 triggers alert even with low disk."""
    _make_bin(tmp_path, "df", 'echo "Use%"; echo " 30%"')
    _make_bin(tmp_path, "free", 'echo "Mem: 8192 1024 7168"')
    # systemctl --user --failed --no-legend returns 2 lines = 2 failed units
    _make_bin(tmp_path, "systemctl", 'if [ "$1" = "--user" ]; then echo "unit1 failed"; echo "unit2 failed"; fi')
    env = _env_with_path(tmp_path)

    r = _run(env=env)
    assert r.returncode == 1
    assert "failed_units=2" in r.stderr


def test_single_failed_unit_alert(tmp_path):
    """Even 1 failed unit triggers alert."""
    _make_bin(tmp_path, "df", 'echo "Use%"; echo " 10%"')
    _make_bin(tmp_path, "free", 'echo "Mem: 4096 512 3584"')
    _make_bin(tmp_path, "systemctl", 'if [ "$1" = "--user" ]; then echo "bad.service failed"; fi')
    env = _env_with_path(tmp_path)

    r = _run(env=env)
    assert r.returncode == 1
    assert "failed_units=1" in r.stderr


def test_systemctl_failure_treated_as_zero(tmp_path):
    """If systemctl exits non-zero, FAILED falls back to 0 (no alert from units)."""
    _make_bin(tmp_path, "df", 'echo "Use%"; echo " 50%"')
    _make_bin(tmp_path, "free", 'echo "Mem: 4096 1024 3072"')
    _make_bin(tmp_path, "systemctl", "exit 1")
    env = _env_with_path(tmp_path)

    # set -e would cause the script to fail; the `|| FAILED=0` handles this
    # But the script uses set -e, so the `|| FAILED=0` should catch it.
    # Actually, with set -e, `cmd || fallback` does NOT trigger exit.
    r = _run(env=env)
    assert r.returncode == 0
    assert "ok" in r.stdout.lower()


# ── combined alerts ────────────────────────────────────────────────────────


def test_both_disk_and_units_alert(tmp_path):
    """Both high disk and failed units → single alert with both values."""
    _make_bin(tmp_path, "df", 'echo "Use%"; echo " 95%"')
    _make_bin(tmp_path, "free", 'echo "Mem: 2048 1024 1024"')
    _make_bin(tmp_path, "systemctl", 'if [ "$1" = "--user" ]; then echo "x failed"; echo "y failed"; echo "z failed"; fi')
    env = _env_with_path(tmp_path)

    r = _run(env=env)
    assert r.returncode == 1
    assert "disk=95%" in r.stderr
    assert "failed_units=3" in r.stderr


# ── tg-notify integration ─────────────────────────────────────────────────


def test_tg_notify_called_when_present(tmp_path):
    """When ~/scripts/tg-notify.sh exists and is executable, it receives the alert msg."""
    # Set up a real-ish HOME so the script can find tg-notify.sh
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    scripts_dir = fake_home / "scripts"
    scripts_dir.mkdir()

    # tg-notify that records the message
    msg_file = tmp_path / "tg_msg.txt"
    tg = scripts_dir / "tg-notify.sh"
    tg.write_text(f"#!/bin/bash\necho \"$1\" > {msg_file}\n")
    tg.chmod(tg.stat().st_mode | stat.S_IEXEC)

    _make_bin(tmp_path, "df", 'echo "Use%"; echo " 90%"')
    _make_bin(tmp_path, "free", 'echo "Mem: 2048 1024 1024"')
    _make_bin(tmp_path, "systemctl", "exit 0")

    env = os.environ.copy()
    env["PATH"] = str(tmp_path) + ":" + env.get("PATH", "/usr/bin:/bin")
    env["HOME"] = str(fake_home)

    r = _run(env=env)
    assert r.returncode == 1
    assert msg_file.exists()
    msg = msg_file.read_text().strip()
    assert "disk=90%" in msg
    assert "pharos health" in msg


def test_no_stderr_when_tg_notify_available(tmp_path):
    """When tg-notify.sh handles the alert, no ALERT line on stderr."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    scripts_dir = fake_home / "scripts"
    scripts_dir.mkdir()

    tg = scripts_dir / "tg-notify.sh"
    tg.write_text("#!/bin/bash\ntrue\n")
    tg.chmod(tg.stat().st_mode | stat.S_IEXEC)

    _make_bin(tmp_path, "df", 'echo "Use%"; echo " 90%"')
    _make_bin(tmp_path, "free", 'echo "Mem: 2048 1024 1024"')
    _make_bin(tmp_path, "systemctl", "exit 0")

    env = os.environ.copy()
    env["PATH"] = str(tmp_path) + ":" + env.get("PATH", "/usr/bin:/bin")
    env["HOME"] = str(fake_home)

    r = _run(env=env)
    assert r.returncode == 1
    assert "ALERT" not in r.stderr


# ── edge cases ─────────────────────────────────────────────────────────────


def test_disk_at_86_percent(tmp_path):
    """Disk at 86% is over 85 threshold → alert."""
    _make_bin(tmp_path, "df", 'echo "Use%"; echo " 86%"')
    _make_bin(tmp_path, "free", 'echo "Mem: 4096 2048 2048"')
    _make_bin(tmp_path, "systemctl", "exit 0")
    env = _env_with_path(tmp_path)

    r = _run(env=env)
    assert r.returncode == 1


def test_no_args_is_default_run(tmp_path):
    """Running with no args performs a health check (not an error)."""
    _make_bin(tmp_path, "df", 'echo "Use%"; echo " 20%"')
    _make_bin(tmp_path, "free", 'echo "Mem: 8192 1024 7168"')
    _make_bin(tmp_path, "systemctl", "exit 0")
    env = _env_with_path(tmp_path)

    r = _run(env=env)
    assert r.returncode == 0
    assert "pharos health" in r.stdout


def test_disk_parsing_strips_spaces_and_percent(tmp_path):
    """df output with extra spaces is parsed correctly."""
    _make_bin(tmp_path, "df", 'echo "Use%"; echo "   42 % "')
    _make_bin(tmp_path, "free", 'echo "Mem: 4096 1024 3072"')
    _make_bin(tmp_path, "systemctl", "exit 0")
    env = _env_with_path(tmp_path)

    r = _run(env=env)
    assert r.returncode == 0
    assert "disk=42%" in r.stdout


def test_zero_disk_usage(tmp_path):
    """Disk at 0% is healthy."""
    _make_bin(tmp_path, "df", 'echo "Use%"; echo " 0%"')
    _make_bin(tmp_path, "free", 'echo "Mem: 4096 0 4096"')
    _make_bin(tmp_path, "systemctl", "exit 0")
    env = _env_with_path(tmp_path)

    r = _run(env=env)
    assert r.returncode == 0
    assert "disk=0%" in r.stdout
