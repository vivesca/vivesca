from __future__ import annotations

"""Tests for effectors/pharos-health.sh — bash script tested via subprocess."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "pharos-health.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _mock_bin(tmp_path: Path, df_pcent: int = 80, failed_units: int = 0):
    """Create mock commands in tmp_path/mock-bin."""
    mock_bin = tmp_path / "mock-bin"
    mock_bin.mkdir(parents=True, exist_ok=True)

    # Mock df
    df = mock_bin / "df"
    df.write_text(f"""#!/bin/bash
echo "Use%"
echo "{df_pcent}%"
""")
    df.chmod(0o755)

    # Mock free
    free = mock_bin / "free"
    free.write_text("""#!/bin/bash
echo "              total        used        free      shared  buff/cache   available"
echo "Mem:           16000        8000        8000           0           0        8000"
""")
    free.chmod(0o755)

    # Mock systemctl
    systemctl = mock_bin / "systemctl"
    if failed_units > 0:
        lines = "\n".join([f"unit{i}.service loaded failed failed unit{i}" for i in range(failed_units)])
        systemctl.write_text(f"""#!/bin/bash
cat <<'EOF'
{lines}
EOF
""")
    else:
        systemctl.write_text("""#!/bin/bash
exit 0
""")
    systemctl.chmod(0o755)

    return mock_bin


def _run(tmp_path: Path, df_pcent: int = 80, failed_units: int = 0):
    mock_bin = _mock_bin(tmp_path, df_pcent, failed_units)
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    env["PATH"] = f"{mock_bin}:{env['PATH']}"
    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


# ── help flag ───────────────────────────────────────────────────────────


class TestHelp:
    def _run_help(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_help_exits_zero(self):
        r = self._run_help("--help")
        assert r.returncode == 0

    def test_help_short_flag_exits_zero(self):
        r = self._run_help("-h")
        assert r.returncode == 0

    def test_help_shows_usage(self):
        r = self._run_help("--help")
        assert "Usage:" in r.stdout

    def test_help_mentions_disk(self):
        r = self._run_help("--help")
        assert "disk" in r.stdout

    def test_help_mentions_systemd(self):
        r = self._run_help("--help")
        assert "systemd" in r.stdout or "units" in r.stdout

    def test_help_no_stderr(self):
        r = self._run_help("--help")
        assert r.stderr == ""


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


# ── healthy case ───────────────────────────────────────────────────────


class TestHealthyCase:
    def test_exits_zero(self, tmp_path):
        r = _run(tmp_path, df_pcent=80, failed_units=0)
        assert r.returncode == 0

    def test_prints_ok(self, tmp_path):
        r = _run(tmp_path, df_pcent=80, failed_units=0)
        assert "pharos health: ok" in r.stdout

    def test_includes_disk(self, tmp_path):
        r = _run(tmp_path, df_pcent=80, failed_units=0)
        assert "disk=80%" in r.stdout

    def test_includes_mem(self, tmp_path):
        r = _run(tmp_path, df_pcent=80, failed_units=0)
        assert "mem=" in r.stdout

    def test_includes_failed_units(self, tmp_path):
        r = _run(tmp_path, df_pcent=80, failed_units=0)
        assert "failed_units=0" in r.stdout

    def test_no_stderr(self, tmp_path):
        r = _run(tmp_path, df_pcent=80, failed_units=0)
        assert r.stderr == ""


# ── alert cases ─────────────────────────────────────────────────────────


class TestAlertCases:
    def test_disk_over_85_exits_1(self, tmp_path):
        r = _run(tmp_path, df_pcent=86, failed_units=0)
        assert r.returncode == 1

    def test_disk_over_85_prints_alert(self, tmp_path):
        r = _run(tmp_path, df_pcent=86, failed_units=0)
        assert "ALERT:" in r.stderr

    def test_failed_units_exits_1(self, tmp_path):
        r = _run(tmp_path, df_pcent=80, failed_units=1)
        assert r.returncode == 1

    def test_failed_units_prints_alert(self, tmp_path):
        r = _run(tmp_path, df_pcent=80, failed_units=1)
        assert "ALERT:" in r.stderr

    def test_both_disk_and_failed_exits_1(self, tmp_path):
        r = _run(tmp_path, df_pcent=90, failed_units=2)
        assert r.returncode == 1

    def test_disk_exactly_85_ok(self, tmp_path):
        r = _run(tmp_path, df_pcent=85, failed_units=0)
        assert r.returncode == 0


# ── script permissions ──────────────────────────────────────────────────


class TestTgNotify:
    """Tests for the tg-notify.sh alert path."""

    def _run_with_notify(self, tmp_path, df_pcent=90, failed_units=0):
        """Run with a fake HOME so tg-notify.sh lives under ~/scripts/."""
        mock_bin = _mock_bin(tmp_path, df_pcent, failed_units)
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        scripts_dir = fake_home / "scripts"
        scripts_dir.mkdir()
        alert_file = tmp_path / "alert.txt"
        notify = scripts_dir / "tg-notify.sh"
        notify.write_text(f"#!/bin/bash\necho \"$@\" > {alert_file}\n")
        notify.chmod(0o755)

        env = os.environ.copy()
        env["HOME"] = str(fake_home)
        env["PATH"] = f"{mock_bin}:{env['PATH']}"
        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        return r, alert_file

    def test_tg_notify_called_on_disk_alert(self, tmp_path):
        r, alert_file = self._run_with_notify(tmp_path, df_pcent=90)
        assert r.returncode == 1
        assert alert_file.exists()
        msg = alert_file.read_text().strip()
        assert "pharos health:" in msg
        assert "disk=90%" in msg

    def test_tg_notify_called_on_failed_units(self, tmp_path):
        r, alert_file = self._run_with_notify(tmp_path, df_pcent=50, failed_units=2)
        assert r.returncode == 1
        msg = alert_file.read_text().strip()
        assert "failed_units=2" in msg

    def test_tg_notify_not_called_when_healthy(self, tmp_path):
        r, alert_file = self._run_with_notify(tmp_path, df_pcent=50, failed_units=0)
        assert r.returncode == 0
        assert not alert_file.exists()

    def test_tg_notify_stderr_empty(self, tmp_path):
        """When tg-notify.sh exists, alert goes there — not stderr."""
        r, _ = self._run_with_notify(tmp_path, df_pcent=90)
        assert r.stderr == ""

    def test_no_tg_notify_stderr_has_alert(self, tmp_path):
        """Without tg-notify.sh, alert goes to stderr."""
        r = _run(tmp_path, df_pcent=90)
        assert r.returncode == 1
        assert "ALERT:" in r.stderr


# ── script permissions ──────────────────────────────────────────────────


class TestMemoryFormat:
    """Validate memory output format matches N/NMB."""

    def test_mem_format(self, tmp_path):
        r = _run(tmp_path, df_pcent=50, failed_units=0)
        import re

        match = re.search(r"mem=\d+/\d+MB", r.stdout)
        assert match is not None, f"mem format not found in: {r.stdout!r}"


class TestSystemctlFailure:
    """When systemctl fails entirely, script falls back to FAILED=0."""

    def test_systemctl_error_still_healthy(self, tmp_path):
        """systemctl exits non-zero → FAILED=0 fallback → still healthy."""
        mock_bin = _mock_bin(tmp_path, df_pcent=50, failed_units=0)
        # Override systemctl to exit with error
        bad_ctl = mock_bin / "systemctl"
        bad_ctl.write_text("#!/bin/bash\nexit 1\n")
        bad_ctl.chmod(0o755)
        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{mock_bin}:{env['PATH']}"
        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert r.returncode == 0
        assert "failed_units=0" in r.stdout


class TestAlertMessageDetail:
    """Alert messages contain all three fields."""

    def test_disk_alert_contains_all_fields(self, tmp_path):
        r = _run(tmp_path, df_pcent=90, failed_units=0)
        assert r.returncode == 1
        output = r.stderr
        assert "disk=90%" in output
        assert "mem=" in output
        assert "failed_units=0" in output

    def test_failed_units_alert_contains_all_fields(self, tmp_path):
        r = _run(tmp_path, df_pcent=50, failed_units=3)
        assert r.returncode == 1
        output = r.stderr
        assert "disk=50%" in output
        assert "mem=" in output
        assert "failed_units=3" in output


class TestDiskBoundary:
    """Edge-case disk percentages."""

    def test_disk_99_alert(self, tmp_path):
        r = _run(tmp_path, df_pcent=99, failed_units=0)
        assert r.returncode == 1
        assert "disk=99%" in r.stderr

    def test_disk_100_alert(self, tmp_path):
        r = _run(tmp_path, df_pcent=100, failed_units=0)
        assert r.returncode == 1
        assert "disk=100%" in r.stderr

    def test_disk_0_ok(self, tmp_path):
        r = _run(tmp_path, df_pcent=0, failed_units=0)
        assert r.returncode == 0
        assert "disk=0%" in r.stdout


class TestTgNotifyNotExecutable:
    """tg-notify.sh exists but is not executable → stderr fallback."""

    def test_tg_notify_not_executable_falls_back_to_stderr(self, tmp_path):
        mock_bin = _mock_bin(tmp_path, df_pcent=90, failed_units=0)
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        scripts_dir = fake_home / "scripts"
        scripts_dir.mkdir()
        notify = scripts_dir / "tg-notify.sh"
        notify.write_text("#!/bin/bash\necho should not run\n")
        notify.chmod(0o644)  # not executable
        env = os.environ.copy()
        env["HOME"] = str(fake_home)
        env["PATH"] = f"{mock_bin}:{env['PATH']}"
        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        assert r.returncode == 1
        assert "ALERT:" in r.stderr


class TestScriptPermissions:
    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)

    def test_script_file_not_directory(self):
        assert SCRIPT.is_file()
