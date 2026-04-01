from __future__ import annotations

"""Tests for pharos-health.sh — system health checker with alerts."""

import os
import stat
import subprocess
import textwrap
from pathlib import Path

SCRIPT = Path.home() / "germline" / "effectors" / "pharos-health.sh"


def _run(args: list[str] | None = None, **kwargs) -> subprocess.CompletedProcess:
    """Run the script with optional args, capturing output."""
    cmd = ["bash", str(SCRIPT)]
    if args:
        cmd.extend(args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=10,
        **kwargs,
    )


# ── Basic script structure tests ─────────────────────────────────────────


def test_script_exists():
    """Script file exists."""
    assert SCRIPT.exists()


def test_script_is_executable():
    """Script file is executable."""
    assert os.access(SCRIPT, os.X_OK)


def test_script_has_shebang():
    """Script starts with #!/bin/bash."""
    first_line = SCRIPT.read_text().splitlines()[0]
    assert first_line == "#!/bin/bash"


def test_script_uses_strict_mode():
    """Script uses set -euo pipefail."""
    content = SCRIPT.read_text()
    assert "set -euo pipefail" in content


# ── Help / usage tests ─────────────────────────────────────────────────


def test_help_long_flag():
    """--help prints usage and exits 0."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout
    assert "Check system health" in r.stdout
    assert "disk" in r.stdout
    assert "Telegram" in r.stdout


def test_help_short_flag():
    """-h prints usage and exits 0."""
    r = _run(["-h"])
    assert r.returncode == 0
    assert "Usage:" in r.stdout


# ── Exit code documentation ─────────────────────────────────────────────


def test_help_mentions_exit_codes():
    """Help text documents exit codes."""
    r = _run(["--help"])
    assert r.returncode == 0
    assert "Exit 0 = healthy" in r.stdout
    assert "exit 1 = alert sent" in r.stdout


# ── Mocked health check tests ───────────────────────────────────────────


def test_all_healthy_exits_zero(tmp_path):
    """When disk <85% and 0 failed units, exits 0 with ok message."""
    # Create fake df, free, systemctl commands
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)

    # Fake df: disk usage at 50%
    df = bindir / "df"
    df.write_text(textwrap.dedent("""\
        #!/bin/bash
        if [ "$1" = "/" ] && [ "$2" = "--output=pcent" ]; then
            echo "pcent"
            echo " 50 "
        fi
    """))
    df.chmod(df.stat().st_mode | stat.S_IEXEC)

    # Fake free
    free = bindir / "free"
    free.write_text(textwrap.dedent("""\
        #!/bin/bash
        echo "               total        used        free      shared  buff/cache   available"
        echo "Mem:        1234567      789012      445555       1234      123456      567890"
        echo "Swap:         1024          0       1024"
    """))
    free.chmod(free.stat().st_mode | stat.S_IEXEC)

    # Fake systemctl: 0 failed units
    systemctl = bindir / "systemctl"
    systemctl.write_text(textwrap.dedent("""\
        #!/bin/bash
        # No failed units -> output is empty
        exit 0
    """))
    systemctl.chmod(systemctl.stat().st_mode | stat.S_IEXEC)

    # We also need to intercept tg-notify.sh even though it won't be called
    tg_notify = bindir / "tg-notify.sh"
    tg_notify.write_text("#!/bin/bash\necho fake-tg-notify-called $1\nexit 0\n")
    tg_notify.chmod(tg_notify.stat().st_mode | stat.S_IEXEC)

    env = os.environ.copy()
    env["PATH"] = f"{bindir}:{env.get('PATH', '')}"
    env["HOME"] = str(tmp_path)  # prevent finding real ~/scripts/tg-notify.sh

    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )

    assert r.returncode == 0
    assert "pharos health: ok" in r.stdout
    assert "disk=50%" in r.stdout
    assert "failed_units=0" in r.stdout


def test_disk_over_85_exits_one(tmp_path):
    """When disk >85%, exits 1 with alert."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)

    # Fake df: disk usage at 90%
    df = bindir / "df"
    df.write_text(textwrap.dedent("""\
        #!/bin/bash
        if [ "$1" = "/" ] && [ "$2" = "--output=pcent" ]; then
            echo "pcent"
            echo " 90 "
        fi
    """))
    df.chmod(df.stat().st_mode | stat.S_IEXEC)

    free = bindir / "free"
    free.write_text(textwrap.dedent("""\
        #!/bin/bash
        echo "               total        used        free      shared  buff/cache   available"
        echo "Mem:        1234567      789012      445555       1234      123456      567890"
    """))
    free.chmod(free.stat().st_mode | stat.S_IEXEC)

    systemctl = bindir / "systemctl"
    systemctl.write_text(textwrap.dedent("""\
        #!/bin/bash
        exit 0
    """))
    systemctl.chmod(systemctl.stat().st_mode | stat.S_IEXEC)

    # Fake tg-notify that just outputs the message
    tg_notify = bindir / "tg-notify.sh"
    tg_notify.write_text("#!/bin/bash\necho \"fake-tg: $1\"\n exit 0\n")
    tg_notify.chmod(tg_notify.stat().st_mode | stat.S_IEXEC)

    env = os.environ.copy()
    env["PATH"] = f"{bindir}:{env.get('PATH', '')}"
    env["HOME"] = str(tmp_path)

    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )

    # Since ~/scripts won't exist in our fake HOME, it will echo ALERT to stderr
    assert r.returncode == 1
    # The message contains disk=90% either via fake tg or the echo fallback
    if "disk=90%" in r.stdout:
        assert "disk=90%" in r.stdout
    else:
        assert "disk=90%" in r.stderr
        assert "ALERT:" in r.stderr


def test_failed_units_exits_one(tmp_path):
    """When >0 failed systemd units, exits 1 with alert."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)

    # Fake df: healthy
    df = bindir / "df"
    df.write_text(textwrap.dedent("""\
        #!/bin/bash
        if [ "$1" = "/" ] && [ "$2" = "--output=pcent" ]; then
            echo "pcent"
            echo " 50 "
        fi
    """))
    df.chmod(df.stat().st_mode | stat.S_IEXEC)

    free = bindir / "free"
    free.write_text(textwrap.dedent("""\
        #!/bin/bash
        echo "               total        used        free      shared  buff/cache   available"
        echo "Mem:        1234567      789012      445555       1234      123456      567890"
    """))
    free.chmod(free.stat().st_mode | stat.S_IEXEC)

    # Fake systemctl: 2 failed units
    systemctl = bindir / "systemctl"
    systemctl.write_text(textwrap.dedent("""\
        #!/bin/bash
        echo "  unit1.service failed"
        echo "  unit2.service failed"
    """))
    systemctl.chmod(systemctl.stat().st_mode | stat.S_IEXEC)

    # Fake tg-notify
    tg_notify = bindir / "tg-notify.sh"
    tg_notify.write_text("#!/bin/bash\necho \"fake-tg: $1\"\n exit 0\n")
    tg_notify.chmod(tg_notify.stat().st_mode | stat.S_IEXEC)

    env = os.environ.copy()
    env["PATH"] = f"{bindir}:{env.get('PATH', '')}"
    env["HOME"] = str(tmp_path)

    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )

    assert r.returncode == 1
    # wc -l will count 2 lines → FAILED=2
    assert "failed_units=2" in (r.stdout + r.stderr)


def test_both_problems_exits_one(tmp_path):
    """When both disk over 85% and failed units, exits 1."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)

    df = bindir / "df"
    df.write_text(textwrap.dedent("""\
        #!/bin/bash
        echo "pcent"
        echo " 92 "
    """))
    df.chmod(df.stat().st_mode | stat.S_IEXEC)

    free = bindir / "free"
    free.write_text(textwrap.dedent("""\
        #!/bin/bash
        echo "Mem:        1234567      789012      445555"
    """))
    free.chmod(free.stat().st_mode | stat.S_IEXEC)

    systemctl = bindir / "systemctl"
    systemctl.write_text(textwrap.dedent("""\
        #!/bin/bash
        echo "  bad.service failed"
    """))
    systemctl.chmod(systemctl.stat().st_mode | stat.S_IEXEC)

    # Fake tg-notify
    tg_notify = bindir / "tg-notify.sh"
    tg_notify.write_text("#!/bin/bash\necho \"fake-tg: $1\"\n exit 0\n")
    tg_notify.chmod(tg_notify.stat().st_mode | stat.S_IEXEC)

    env = os.environ.copy()
    env["PATH"] = f"{bindir}:{env.get('PATH', '')}"
    env["HOME"] = str(tmp_path)

    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )

    assert r.returncode == 1
    assert "disk=92%" in (r.stdout + r.stderr)
    assert "failed_units=1" in (r.stdout + r.stderr)


def test_systemctl_fail_handled_gracefully(tmp_path):
    """When systemctl fails (not on systemd), FAILED=0 is set."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)

    df = bindir / "df"
    df.write_text(textwrap.dedent("""\
        #!/bin/bash
        echo "pcent"
        echo " 50 "
    """))
    df.chmod(df.stat().st_mode | stat.S_IEXEC)

    free = bindir / "free"
    free.write_text(textwrap.dedent("""\
        #!/bin/bash
        echo "Mem:        1234567      789012      445555"
    """))
    free.chmod(free.stat().st_mode | stat.S_IEXEC)

    # Fake systemctl that fails (non-zero exit)
    systemctl = bindir / "systemctl"
    systemctl.write_text(textwrap.dedent("""\
        #!/bin/bash
        echo "command not found" >&2
        exit 1
    """))
    systemctl.chmod(systemctl.stat().st_mode | stat.S_IEXEC)

    # Fake tg-notify
    tg_notify = bindir / "tg-notify.sh"
    tg_notify.write_text("#!/bin/bash\necho \"fake-tg: $1\"\n exit 0\n")
    tg_notify.chmod(tg_notify.stat().st_mode | stat.S_IEXEC)

    env = os.environ.copy()
    env["PATH"] = f"{bindir}:{env.get('PATH', '')}"
    env["HOME"] = str(tmp_path)

    r = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )

    # Should default to FAILED=0 and exit 0 if disk is ok
    assert r.returncode == 0
    assert "failed_units=0" in r.stdout
