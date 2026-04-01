from __future__ import annotations

"""Tests for effectors/pharos-health.sh — system health checker.

Uses subprocess.run with mocked system commands (df, free, systemctl)
placed first on PATH to simulate healthy and unhealthy states.
"""

import os
import stat
import subprocess
from pathlib import Path

SCRIPT = Path.home() / "germline" / "effectors" / "pharos-health.sh"


def _run(
    *,
    disk_pct: int = 50,
    mem_used: int = 1024,
    mem_total: int = 4096,
    failed_units: int = 0,
    has_tg_notify: bool = False,
    args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run pharos-health.sh with mocked system commands on PATH."""
    import tempfile

    tmpdir = tempfile.mkdtemp(prefix="pharos_test_")

    # Mock df — outputs only the pcent column (matches --output=pcent)
    df_mock = Path(tmpdir) / "df"
    df_mock.write_text(f"""#!/bin/bash
echo "Use%"
echo " {disk_pct}%"
""")
    df_mock.chmod(df_mock.stat().st_mode | stat.S_IEXEC)

    # Mock free — outputs the requested memory values
    free_mock = Path(tmpdir) / "free"
    free_mock.write_text(f"""#!/bin/bash
echo "              total        used        free"
echo "Mem:       {mem_total}       {mem_used}       {mem_total - mem_used}"
""")
    free_mock.chmod(free_mock.stat().st_mode | stat.S_IEXEC)

    # Mock systemctl — outputs N failed unit lines (empty for 0)
    systemctl_mock = Path(tmpdir) / "systemctl"
    lines = "\n".join(["unit.service  failed"] * failed_units)
    # When no failed units, output nothing so wc -l returns 0
    body = f'echo "{lines}"' if failed_units > 0 else "true"
    systemctl_mock.write_text(f"""#!/bin/bash
{body}
""")
    systemctl_mock.chmod(systemctl_mock.stat().st_mode | stat.S_IEXEC)

    # Optionally mock tg-notify.sh
    home_bin = Path(tmpdir) / "scripts"
    if has_tg_notify:
        home_bin.mkdir()
        tg = home_bin / "tg-notify.sh"
        tg.write_text("#!/bin/bash\necho \"TG_NOTIFY: $1\"\n")
        tg.chmod(tg.stat().st_mode | stat.S_IEXEC)

    env = os.environ.copy()
    # Put our mock dir first on PATH, override HOME so tg-notify path resolves
    env["PATH"] = f"{tmpdir}:{env.get('PATH', '')}"
    env["HOME"] = tmpdir

    cmd = ["bash", str(SCRIPT)] + (args or [])
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
    )


# ── Help flags ──────────────────────────────────────────────────


def test_help_flag_exits_zero():
    r = _run(args=["--help"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout
    assert "pharos-health.sh" in r.stdout


def test_h_flag_exits_zero():
    r = _run(args=["-h"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout


def test_help_mentions_disk_threshold():
    r = _run(args=["--help"])
    assert "85%" in r.stdout


def test_help_explains_exit_codes():
    r = _run(args=["--help"])
    assert "Exit 0" in r.stdout
    assert "exit 1" in r.stdout


# ── Healthy state ───────────────────────────────────────────────


def test_healthy_exits_zero():
    r = _run(disk_pct=50, failed_units=0)
    assert r.returncode == 0


def test_healthy_stdout_contains_ok():
    r = _run(disk_pct=50, failed_units=0)
    assert "ok" in r.stdout


def test_healthy_output_contains_disk():
    r = _run(disk_pct=42, failed_units=0)
    assert "disk=42%" in r.stdout


def test_healthy_output_contains_mem():
    r = _run(mem_used=1024, mem_total=4096)
    assert "mem=" in r.stdout


def test_healthy_output_contains_failed_units():
    r = _run(failed_units=0)
    assert "failed_units=0" in r.stdout


def test_disk_exactly_85_is_healthy():
    """Boundary: disk == 85% should NOT trigger alert."""
    r = _run(disk_pct=85, failed_units=0)
    assert r.returncode == 0
    assert "ok" in r.stdout


# ── Disk alert ──────────────────────────────────────────────────


def test_disk_over_85_exits_one():
    r = _run(disk_pct=90, failed_units=0)
    assert r.returncode == 1


def test_disk_over_85_stderr_has_alert():
    r = _run(disk_pct=90, failed_units=0, has_tg_notify=False)
    assert "ALERT" in r.stderr


def test_disk_86_exits_one():
    """Boundary: disk == 86% should trigger alert."""
    r = _run(disk_pct=86, failed_units=0)
    assert r.returncode == 1


def test_disk_alert_contains_disk_pct():
    r = _run(disk_pct=93, failed_units=0, has_tg_notify=False)
    combined = r.stderr + r.stdout
    assert "disk=93%" in combined


# ── Failed units alert ──────────────────────────────────────────


def test_failed_units_exits_one():
    r = _run(disk_pct=50, failed_units=1)
    assert r.returncode == 1


def test_failed_units_stderr_has_alert():
    r = _run(disk_pct=50, failed_units=2, has_tg_notify=False)
    assert "ALERT" in r.stderr


def test_multiple_failed_units_exits_one():
    r = _run(disk_pct=50, failed_units=5)
    assert r.returncode == 1


def test_failed_units_alert_shows_count():
    r = _run(disk_pct=50, failed_units=3, has_tg_notify=False)
    combined = r.stderr + r.stdout
    assert "failed_units=3" in combined


# ── Combined alerts ─────────────────────────────────────────────


def test_disk_and_failed_units_exits_one():
    r = _run(disk_pct=90, failed_units=2)
    assert r.returncode == 1


def test_disk_and_failed_units_stderr_has_alert():
    r = _run(disk_pct=90, failed_units=2, has_tg_notify=False)
    assert "ALERT" in r.stderr


# ── Telegram notify ─────────────────────────────────────────────


def test_tg_notify_called_when_unhealthy():
    r = _run(disk_pct=90, failed_units=0, has_tg_notify=True)
    assert r.returncode == 1
    combined = r.stdout + r.stderr
    assert "TG_NOTIFY:" in combined


def test_tg_not_called_when_healthy():
    r = _run(disk_pct=50, failed_units=0, has_tg_notify=True)
    assert r.returncode == 0
    combined = r.stdout + r.stderr
    assert "TG_NOTIFY:" not in combined


def test_tg_notify_receives_message():
    r = _run(disk_pct=91, failed_units=0, has_tg_notify=True)
    combined = r.stdout + r.stderr
    # The tg-notify mock prints: TG_NOTIFY: <msg>
    assert "TG_NOTIFY:" in combined
    assert "disk=91%" in combined


# ── Output format ───────────────────────────────────────────────


def test_healthy_format_prefix():
    r = _run(disk_pct=50, failed_units=0)
    assert r.stdout.strip().startswith("pharos health:")


def test_alert_format_stderr_contains_alert_line():
    r = _run(disk_pct=90, failed_units=0, has_tg_notify=False)
    assert any(
        line.startswith("ALERT:") for line in r.stderr.strip().splitlines()
    )
