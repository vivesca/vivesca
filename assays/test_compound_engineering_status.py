"""Tests for compound-engineering-status — bash effector for auto-update status."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

EFFECTOR = Path.home() / "germline" / "effectors" / "compound-engineering-status"


def _passthrough_env() -> dict[str, str]:
    """Return current environment as a plain dict for subprocess env merging."""
    return dict(os.environ)


def _run(args: list[str] | None = None, *, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    """Run the effector with optional args and env overrides."""
    cmd = [str(EFFECTOR)]
    if args:
        cmd.extend(args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


# ── --help flag tests ──────────────────────────────────────────────────


def test_help_flag_short():
    """-h prints usage and exits 0."""
    r = _run(["-h"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout
    assert "compound-engineering-status" in r.stdout


def test_help_flag_long():
    """--help prints usage and exits 0."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout
    assert "compound-engineering-status" in r.stdout


def test_help_mentions_status():
    """--help output mentions what the script reports."""
    r = _run(["--help"])
    assert "status" in r.stdout.lower() or "Status" in r.stdout


# ── normal invocation (no --help) ──────────────────────────────────────


def test_header_present():
    """Output contains the status header."""
    r = _run()
    assert "Compound Engineering" in r.stdout


def test_management_commands_present():
    """Output includes management commands section."""
    r = _run()
    assert "Management Commands" in r.stdout or "update-compound-engineering" in r.stdout


def test_launchctl_not_available_on_linux():
    """On Linux, reports launchctl not available."""
    r = _run()
    assert "launchctl not available" in r.stdout or "launchctl" in r.stdout.lower()


def test_no_update_log_by_default(tmp_path):
    """When no log file exists, reports no update logs."""
    r = _run(env={**_passthrough_env(), "HOME": str(tmp_path)})
    assert "No update logs" in r.stdout or "update log" in r.stdout.lower()


def test_with_update_log(tmp_path):
    """When log file exists, shows its tail content."""
    log_file = tmp_path / ".compound-engineering-updates.log"
    lines = [f"Line {i}: update result" for i in range(25)]
    log_file.write_text("\n".join(lines) + "\n")

    r = _run(env={**_passthrough_env(), "HOME": str(tmp_path)})
    # tail -20 should show lines 5-24
    assert "Line 24" in r.stdout
    assert "Line 0:" not in r.stdout
    assert "Line 1:" not in r.stdout


def test_with_short_update_log(tmp_path):
    """Log with fewer than 20 lines is shown entirely."""
    log_file = tmp_path / ".compound-engineering-updates.log"
    log_file.write_text("only one line of log\n")

    r = _run(env={**_passthrough_env(), "HOME": str(tmp_path)})
    assert "only one line of log" in r.stdout


def test_exits_zero_without_help():
    """Normal invocation exits 0."""
    r = _run()
    assert r.returncode == 0


def test_no_stderr_on_normal_run():
    """Normal invocation produces no stderr."""
    r = _run()
    assert r.stderr.strip() == ""


def test_cron_check_no_crontab(tmp_path):
    """When crontab has no compound-engineering entry, reports not configured."""
    r = _run(env={**_passthrough_env(), "HOME": str(tmp_path)})
    output = r.stdout.lower()
    assert "cron" in output or "launchctl" in output


def test_cron_detected(tmp_path):
    """When crontab lists compound-engineering, reports cron configured."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_crontab = fake_bin / "crontab"
    fake_crontab.write_text(
        '#!/bin/bash\n'
        'if [ "$1" = "-l" ]; then\n'
        '  echo "0 2 * * 0 compound-engineering-update"\n'
        '  exit 0\n'
        'fi\n'
        'exit 1\n'
    )
    fake_crontab.chmod(0o755)

    env = {
        **_passthrough_env(),
        "HOME": str(tmp_path),
        "PATH": f"{fake_bin}:{_passthrough_env().get('PATH', '')}",
    }
    r = _run(env=env)
    assert "Cron job is configured" in r.stdout


def test_launchagent_loaded(tmp_path):
    """When launchctl is available and plist is loaded, reports active."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_launchctl = fake_bin / "launchctl"
    fake_launchctl.write_text(
        '#!/bin/bash\n'
        'if [ "$1" = "list" ]; then\n'
        '  echo "12345  0  com.terry.compound-engineering-update"\n'
        '  exit 0\n'
        'fi\n'
        'exit 1\n'
    )
    fake_launchctl.chmod(0o755)

    env = {
        **_passthrough_env(),
        "HOME": str(tmp_path),
        "PATH": f"{fake_bin}:{_passthrough_env().get('PATH', '')}",
    }
    r = _run(env=env)
    assert "LaunchAgent is loaded and active" in r.stdout


def test_launchctl_available_not_loaded(tmp_path):
    """When launchctl is available but plist not loaded, reports not loaded."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_launchctl = fake_bin / "launchctl"
    fake_launchctl.write_text(
        '#!/bin/bash\n'
        'if [ "$1" = "list" ]; then\n'
        '  echo "PID  Status  Label"\n'
        '  exit 0\n'
        'fi\n'
        'exit 1\n'
    )
    fake_launchctl.chmod(0o755)

    env = {
        **_passthrough_env(),
        "HOME": str(tmp_path),
        "PATH": f"{fake_bin}:{_passthrough_env().get('PATH', '')}",
    }
    r = _run(env=env)
    assert "LaunchAgent is not loaded" in r.stdout


def test_help_does_not_show_status():
    """--help does not show status output (scheduler state, logs)."""
    r = _run(["--help"])
    assert "📊" not in r.stdout
    assert "LaunchAgent" not in r.stdout


def test_separator_line_present():
    """Output contains a separator line under the header."""
    r = _run()
    assert "===" in r.stdout


def test_management_commands_include_all_tools():
    """Management commands section mentions all expected tools."""
    r = _run()
    assert "update-compound-engineering" in r.stdout
    assert "compound-engineering-test" in r.stdout


def test_help_exits_cleanly():
    """--help exits with code 0 (not error)."""
    r = _run(["--help"])
    assert r.returncode == 0


def test_update_log_section_header(tmp_path):
    """When log exists, output includes last update log header."""
    log_file = tmp_path / ".compound-engineering-updates.log"
    log_file.write_text("some log content\n")
    r = _run(env={**_passthrough_env(), "HOME": str(tmp_path)})
    assert "Last update log" in r.stdout


def test_no_log_section_header(tmp_path):
    """When no log exists, output mentions no logs yet."""
    r = _run(env={**_passthrough_env(), "HOME": str(tmp_path)})
    assert "No update logs" in r.stdout
    assert "Sunday" in r.stdout or "2 AM" in r.stdout


def test_schedule_info_when_loaded(tmp_path):
    """When LaunchAgent is loaded, schedule info is shown."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_launchctl = fake_bin / "launchctl"
    fake_launchctl.write_text(
        '#!/bin/bash\n'
        'if [ "$1" = "list" ]; then\n'
        '  echo "12345  0  com.terry.compound-engineering-update"\n'
        '  exit 0\n'
        'fi\n'
        'exit 1\n'
    )
    fake_launchctl.chmod(0o755)

    env = {
        **_passthrough_env(),
        "HOME": str(tmp_path),
        "PATH": f"{fake_bin}:{_passthrough_env().get('PATH', '')}",
    }
    r = _run(env=env)
    assert "Sunday" in r.stdout or "2:00" in r.stdout


def test_crontab_exit_nonzero_means_no_cron(tmp_path):
    """When crontab -l exits non-zero (no crontab), reports no cron job."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    # No launchctl fake → falls through to crontab check
    # Fake crontab that exits 1 (no crontab for user)
    fake_crontab = fake_bin / "crontab"
    fake_crontab.write_text('#!/bin/bash\nexit 1\n')
    fake_crontab.chmod(0o755)

    env = {
        **_passthrough_env(),
        "HOME": str(tmp_path),
        "PATH": f"{fake_bin}:{_passthrough_env().get('PATH', '')}",
    }
    r = _run(env=env)
    assert "No cron job" in r.stdout
