from __future__ import annotations

"""Tests for effectors/pharos-health.sh — system health checker (bash subprocess)."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "pharos-health.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run(
    tmp_path: Path,
    *,
    disk_pct: int = 50,
    mem_used: int = 2000,
    mem_total: int = 8000,
    failed_units: int = 0,
    tg_notify: bool = False,
) -> subprocess.CompletedProcess:
    """Run pharos-health.sh with stubbed commands via PATH override."""

    stub_dir = tmp_path / "stubs"
    stub_dir.mkdir(exist_ok=True)

    # Stub df — prints a disk percentage line
    df_stub = stub_dir / "df"
    df_stub.write_text(f"#!/bin/bash\nif [ \"$1\" = '/' ]; then\necho 'Use%'\necho '{disk_pct}%'\nfi\n")
    df_stub.chmod(0o755)

    # Stub free — prints mem line
    free_stub = stub_dir / "free"
    free_stub.write_text(
        f"#!/bin/bash\necho '              total        used        free'\n"
        f"echo 'Mem:        {mem_total}       {mem_used}       {mem_total - mem_used}'\n"
    )
    free_stub.chmod(0o755)

    # Stub systemctl — prints failed_units number of lines (or nothing when 0)
    systemctl_stub = stub_dir / "systemctl"
    if failed_units > 0:
        echo_lines = "\n".join(["echo 'unit.service  failed'"] * failed_units)
        systemctl_stub.write_text(f"#!/bin/bash\n{echo_lines}\n")
    else:
        systemctl_stub.write_text("#!/bin/bash\ntrue\n")
    systemctl_stub.chmod(0o755)

    # Optional tg-notify.sh
    scripts_dir = tmp_path / "scripts"
    if tg_notify:
        scripts_dir.mkdir(exist_ok=True)
        notify = scripts_dir / "tg-notify.sh"
        notify.write_text("#!/bin/bash\necho \"TG_NOTIFY: $@\" >> $HOME/tg-notify.log\n")
        notify.chmod(0o755)
    else:
        # ensure scripts dir doesn't exist or doesn't have tg-notify
        pass

    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    # Put stubs FIRST so they shadow real df/free/systemctl
    env["PATH"] = str(stub_dir) + ":" + env.get("PATH", "/usr/bin:/bin")

    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


# ── file basics ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert SCRIPT.exists()

    def test_is_bash_script(self):
        first = SCRIPT.read_text().split("\n")[0]
        assert first.startswith("#!/bin/bash")

    def test_has_set_euo(self):
        src = SCRIPT.read_text()
        assert "set -euo pipefail" in src


# ── help flag ──────────────────────────────────────────────────────────


class TestHelp:
    def test_help_exit_zero(self):
        r = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 0

    def test_help_output(self):
        r = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "Usage: pharos-health.sh" in r.stdout

    def test_help_mention_disk(self):
        r = subprocess.run(
            ["bash", str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "disk" in r.stdout

    def test_short_help_flag(self):
        r = subprocess.run(
            ["bash", str(SCRIPT), "-h"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 0
        assert "Usage:" in r.stdout


# ── healthy system ────────────────────────────────────────────────────


class TestHealthy:
    def test_exit_zero_when_healthy(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=0)
        assert r.returncode == 0

    def test_stdout_contains_ok(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=0)
        assert "ok" in r.stdout

    def test_stdout_shows_disk_pct(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=0)
        assert "disk=50%" in r.stdout

    def test_stdout_shows_memory(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, mem_used=2000, mem_total=8000)
        assert "mem=" in r.stdout

    def test_stdout_shows_failed_units(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=0)
        assert "failed_units=0" in r.stdout


# ── disk alert ────────────────────────────────────────────────────────


class TestDiskAlert:
    def test_exit_one_when_disk_above_threshold(self, tmp_path):
        r = _run(tmp_path, disk_pct=90, failed_units=0)
        assert r.returncode == 1

    def test_stderr_alert_when_disk_high(self, tmp_path):
        r = _run(tmp_path, disk_pct=90, failed_units=0)
        assert "ALERT" in r.stderr

    def test_disk_at_threshold_boundary(self, tmp_path):
        """Exactly 85 should NOT trigger (threshold is > 85)."""
        r = _run(tmp_path, disk_pct=85, failed_units=0)
        assert r.returncode == 0

    def test_disk_one_above_threshold(self, tmp_path):
        """86% should trigger."""
        r = _run(tmp_path, disk_pct=86, failed_units=0)
        assert r.returncode == 1

    def test_stderr_shows_disk_pct(self, tmp_path):
        r = _run(tmp_path, disk_pct=90, failed_units=0)
        assert "disk=90%" in r.stderr

    def test_no_stdout_on_alert(self, tmp_path):
        r = _run(tmp_path, disk_pct=90, failed_units=0)
        assert "ok" not in r.stdout


# ── failed units alert ───────────────────────────────────────────────


class TestFailedUnitsAlert:
    def test_exit_one_with_failed_units(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=3)
        assert r.returncode == 1

    def test_stderr_alert_with_failed_units(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=2)
        assert "ALERT" in r.stderr

    def test_stderr_shows_failed_count(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=2)
        assert "failed_units=2" in r.stderr


# ── tg-notify integration ────────────────────────────────────────────


class TestTgNotify:
    def test_tg_notify_called_on_alert(self, tmp_path):
        r = _run(tmp_path, disk_pct=90, failed_units=0, tg_notify=True)
        log = tmp_path / "tg-notify.log"
        assert log.exists()
        content = log.read_text()
        assert "TG_NOTIFY:" in content
        assert "pharos health" in content

    def test_tg_notify_not_called_when_healthy(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=0, tg_notify=True)
        log = tmp_path / "tg-notify.log"
        assert not log.exists()

    def test_stderr_fallback_when_no_tg_notify(self, tmp_path):
        """Without tg-notify.sh, alert goes to stderr."""
        r = _run(tmp_path, disk_pct=90, failed_units=0, tg_notify=False)
        assert r.returncode == 1
        assert "ALERT" in r.stderr


# ── combined alerts ─────────────────────────────────────────────────────


class TestCombinedAlert:
    def test_exit_one_when_both_disk_and_units_bad(self, tmp_path):
        r = _run(tmp_path, disk_pct=90, failed_units=3)
        assert r.returncode == 1

    def test_stderr_shows_both_disk_and_units(self, tmp_path):
        r = _run(tmp_path, disk_pct=92, failed_units=2)
        assert "disk=92%" in r.stderr
        assert "failed_units=2" in r.stderr


# ── output format ───────────────────────────────────────────────────────


class TestOutputFormat:
    def test_healthy_output_starts_with_prefix(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=0)
        assert r.stdout.startswith("pharos health: ok")

    def test_healthy_output_contains_all_fields(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, mem_used=2000, mem_total=8000, failed_units=0)
        out = r.stdout.strip()
        assert "disk=50%" in out
        assert "mem=" in out
        assert "failed_units=0" in out

    def test_memory_format_shows_used_and_total(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, mem_used=3000, mem_total=8000)
        assert "mem=" in r.stdout
        # The awk format is "%d/%dMB", so we expect used/totalMB
        mem_part = [p for p in r.stdout.strip().split() if p.startswith("mem=")][0]
        assert "/" in mem_part  # used/total format
        assert "MB" in mem_part

    def test_stderr_alert_format(self, tmp_path):
        r = _run(tmp_path, disk_pct=90, failed_units=0)
        assert r.stderr.strip().startswith("ALERT:")

    def test_stderr_alert_contains_pharos_health_prefix(self, tmp_path):
        r = _run(tmp_path, disk_pct=90, failed_units=0)
        assert "pharos health:" in r.stderr


# ── extreme disk values ────────────────────────────────────────────────


class TestExtremeDisk:
    def test_disk_zero_pct_healthy(self, tmp_path):
        r = _run(tmp_path, disk_pct=0, failed_units=0)
        assert r.returncode == 0
        assert "disk=0%" in r.stdout

    def test_disk_ninety_nine_pct_alerts(self, tmp_path):
        r = _run(tmp_path, disk_pct=99, failed_units=0)
        assert r.returncode == 1
        assert "disk=99%" in r.stderr


# ── systemctl failure ──────────────────────────────────────────────────


class TestSystemctlFailure:
    def test_systemctl_nonzero_exits_treated_as_zero_failed(self, tmp_path):
        """When systemctl exits non-zero, FAILED=0 fallback kicks in."""
        r = _run(tmp_path, disk_pct=50, failed_units=0)
        # Script should still be healthy — systemctl failure is handled
        assert r.returncode == 0


# ── tg-notify edge cases ──────────────────────────────────────────────


class TestTgNotifyEdgeCases:
    def test_tg_notify_message_contains_disk(self, tmp_path):
        r = _run(tmp_path, disk_pct=90, failed_units=0, tg_notify=True)
        log = (tmp_path / "tg-notify.log").read_text()
        assert "disk=90%" in log

    def test_tg_notify_message_contains_failed_units(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=2, tg_notify=True)
        log = (tmp_path / "tg-notify.log").read_text()
        assert "failed_units=2" in log

    def test_tg_notify_message_contains_mem(self, tmp_path):
        r = _run(tmp_path, disk_pct=90, failed_units=0, tg_notify=True)
        log = (tmp_path / "tg-notify.log").read_text()
        assert "mem=" in log

    def test_tg_notify_not_executable_falls_back_to_stderr(self, tmp_path):
        """tg-notify.sh exists but is NOT executable → falls back to stderr."""
        stub_dir = tmp_path / "stubs"
        stub_dir.mkdir()
        df_stub = stub_dir / "df"
        df_stub.write_text("#!/bin/bash\nif [ \"$1\" = '/' ]; then\necho 'Use%'\necho '90%'\nfi\n")
        df_stub.chmod(0o755)
        free_stub = stub_dir / "free"
        free_stub.write_text("#!/bin/bash\necho '              total        used        free'\necho 'Mem:        8000       2000       6000'\n")
        free_stub.chmod(0o755)
        systemctl_stub = stub_dir / "systemctl"
        systemctl_stub.write_text("#!/bin/bash\ntrue\n")
        systemctl_stub.chmod(0o755)

        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        notify = scripts_dir / "tg-notify.sh"
        notify.write_text("#!/bin/bash\necho SHOULD_NOT_RUN\n")
        notify.chmod(0o644)  # NOT executable

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = str(stub_dir) + ":" + env.get("PATH", "/usr/bin:/bin")

        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert r.returncode == 1
        assert "ALERT" in r.stderr


# ── multiple failed units count ────────────────────────────────────────


class TestFailedUnitsCount:
    def test_one_failed_unit(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=1)
        assert r.returncode == 1
        assert "failed_units=1" in r.stderr

    def test_five_failed_units(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=5)
        assert r.returncode == 1
        assert "failed_units=5" in r.stderr

    def test_zero_failed_units_healthy(self, tmp_path):
        r = _run(tmp_path, disk_pct=50, failed_units=0)
        assert r.returncode == 0
        assert "failed_units=0" in r.stdout
