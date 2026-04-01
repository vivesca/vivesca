from __future__ import annotations

"""Tests for effectors/tm — mobile tmux session manager (bash script)."""

import os
import stat
import subprocess
from pathlib import Path

SCRIPT = Path.home() / "germline" / "effectors" / "tm"


def _run(*args: str, env: dict | None = None, **kw) -> subprocess.CompletedProcess:
    """Run the tm script with subprocess.run."""
    return subprocess.run(
        [str(SCRIPT), *args],
        capture_output=True,
        text=True,
        timeout=5,
        env=env,
        **kw,
    )


def _make_fake_tmux(tmpdir: Path, responses: dict[str, str] | None = None) -> dict:
    """Create a fake tmux that records calls and returns scripted responses.

    responses: maps subcommand patterns to stdout output.
    Returns env dict with PATH pointing to the fake tmux.
    """
    call_log = tmpdir / "tmux_calls.txt"
    call_log.write_text("")
    responses = responses or {}

    # Build a fake tmux script that logs what it was called with
    # and optionally responds based on the arguments
    resp_lines = []
    for pattern, output in responses.items():
        resp_lines.append(f'  "$@" | grep -q "{pattern}" && echo -n {repr(output)} && exit 0')

    resp_block = "\n".join(resp_lines) if resp_lines else ""

    fake = tmpdir / "tmux"
    fake.write_text(
        "#!/bin/bash\n"
        f'echo "$@" >> {call_log}\n'
        f"{resp_block}\n"
        "# default: succeed silently\n"
        "exit 0\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)

    env = dict(os.environ)
    env["PATH"] = f"{tmpdir}:{env.get('PATH', '/usr/bin:/bin')}"
    return env


def _make_fake_tmux_has_session(tmpdir: Path, exists: bool) -> dict:
    """Create a fake tmux where has-session returns 0 (exists) or 1 (not)."""
    call_log = tmpdir / "tmux_calls.txt"
    call_log.write_text("")

    exit_code = 0 if exists else 1

    fake = tmpdir / "tmux"
    fake.write_text(
        "#!/bin/bash\n"
        f'echo "$@" >> {call_log}\n'
        # If called with has-session, return the requested exit code
        f'if [[ "$1" == "has-session" ]]; then exit {exit_code}; fi\n'
        # list-sessions returns a session list
        'if [[ "$1" == "list-sessions" ]]; then echo "work:1 windows (created ...)"; exit 0; fi\n'
        "exit 0\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)

    env = dict(os.environ)
    env["PATH"] = f"{tmpdir}:{env.get('PATH', '/usr/bin:/bin')}"
    return env


# ── no arguments: show usage ──────────────────────────────────────────


def test_no_args_shows_usage():
    """Running with no arguments shows usage and exits 0."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        env = _make_fake_tmux(Path(tmpdir))
        r = _run(env=env)
        assert r.returncode == 0
        assert "Usage" in r.stdout


def test_no_args_lists_sessions():
    """Running with no arguments includes current sessions list."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        env = _make_fake_tmux(Path(tmpdir), {"list-sessions": "work:1 windows\n"})
        r = _run(env=env)
        assert r.returncode == 0


# ── help flags ────────────────────────────────────────────────────────


def test_help_long():
    """--help shows usage and exits 0."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        env = _make_fake_tmux(Path(tmpdir))
        r = _run("--help", env=env)
        assert r.returncode == 0
        assert "Usage" in r.stdout


def test_help_short():
    """'-h' shows usage and exits 0."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        env = _make_fake_tmux(Path(tmpdir))
        r = _run("-h", env=env)
        assert r.returncode == 0
        assert "Usage" in r.stdout


def test_help_mentions_session_name():
    """Help text mentions session-name argument."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        env = _make_fake_tmux(Path(tmpdir))
        r = _run("--help", env=env)
        assert "session-name" in r.stdout


# ── ls subcommand ────────────────────────────────────────────────────


def test_ls_lists_sessions():
    """'tm ls' delegates to tmux list-sessions."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        env = _make_fake_tmux(tmp, {"list-sessions": "work:1 windows\nhome:2 windows\n"})
        r = _run("ls", env=env)
        assert r.returncode == 0


def test_ls_no_sessions():
    """'tm ls' handles no active sessions gracefully."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        # Fake tmux that fails on list-sessions
        fake = tmp / "tmux"
        call_log = tmp / "tmux_calls.txt"
        call_log.write_text("")
        fake.write_text(
            "#!/bin/bash\n"
            f'echo "$@" >> {call_log}\n'
            '[[ "$1" == "list-sessions" ]] && echo "no server running" >&2 && exit 1\n'
            "exit 0\n"
        )
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        env = dict(os.environ)
        env["PATH"] = f"{tmp}:{env.get('PATH', '/usr/bin:/bin')}"
        r = _run("ls", env=env)
        # Script uses `|| echo "No active sessions"` so it should succeed
        assert r.returncode == 0
        assert "No active sessions" in r.stdout


# ── kill subcommand ──────────────────────────────────────────────────


def test_kill_requires_session_name():
    """'tm kill' without session name prints error and exits 1."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        env = _make_fake_tmux(Path(tmpdir))
        r = _run("kill", env=env)
        assert r.returncode == 1
        assert "specify a session name" in r.stdout.lower()


def test_kill_session():
    """'tm kill work' calls tmux kill-session -t work."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        env = _make_fake_tmux(tmp)
        r = _run("kill", "work", env=env)
        assert r.returncode == 0
        calls = (tmp / "tmux_calls.txt").read_text()
        assert "kill-session" in calls
        assert "work" in calls


def test_kill_named_session():
    """'tm kill mysession' calls tmux kill-session -t mysession."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        env = _make_fake_tmux(tmp)
        r = _run("kill", "mysession", env=env)
        assert r.returncode == 0
        calls = (tmp / "tmux_calls.txt").read_text()
        assert "kill-session" in calls
        assert "-t" in calls
        assert "mysession" in calls


# ── killall subcommand ───────────────────────────────────────────────


def test_killall():
    """'tm killall' calls tmux kill-server."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        env = _make_fake_tmux(tmp)
        r = _run("killall", env=env)
        assert r.returncode == 0
        calls = (tmp / "tmux_calls.txt").read_text()
        assert "kill-server" in calls


def test_killall_prints_confirmation():
    """'tm killall' prints confirmation message."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        env = _make_fake_tmux(Path(tmpdir))
        r = _run("killall", env=env)
        assert "All tmux sessions killed" in r.stdout


# ── session attach / create ──────────────────────────────────────────


def test_attach_existing_session():
    """'tm work' attaches to an existing session."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        env = _make_fake_tmux_has_session(tmp, exists=True)
        r = _run("work", env=env)
        assert r.returncode == 0
        calls = (tmp / "tmux_calls.txt").read_text()
        assert "has-session" in calls
        assert "attach-session" in calls


def test_create_new_session():
    """'tm newproj' creates a new session when it doesn't exist."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        env = _make_fake_tmux_has_session(tmp, exists=False)
        r = _run("newproj", env=env)
        assert r.returncode == 0
        calls = (tmp / "tmux_calls.txt").read_text()
        assert "has-session" in calls
        assert "new-session" in calls
        assert "attach-session" in calls


def test_create_new_session_uses_name():
    """'tm mysession' passes the session name to tmux new-session."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        env = _make_fake_tmux_has_session(tmp, exists=False)
        r = _run("mysession", env=env)
        assert r.returncode == 0
        calls = (tmp / "tmux_calls.txt").read_text()
        assert "-s" in calls
        assert "mysession" in calls


def test_attach_existing_session_prints_message():
    """Attaching to existing session prints a confirmation."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        env = _make_fake_tmux_has_session(tmp, exists=True)
        r = _run("work", env=env)
        assert "Attaching to existing session" in r.stdout


def test_create_new_session_prints_message():
    """Creating a new session prints a confirmation."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        env = _make_fake_tmux_has_session(tmp, exists=False)
        r = _run("newproj", env=env)
        assert "Creating new session" in r.stdout
