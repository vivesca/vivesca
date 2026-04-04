from __future__ import annotations

"""Tests for effectors/tm — mobile tmux session manager (bash script)."""

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

TM_SCRIPT = Path.home() / "germline" / "effectors" / "tm"


@pytest.fixture()
def mock_tmux(tmp_path: Path):
    """Create a fake ``tmux`` binary that logs calls and returns canned output/exit codes.

    The helper has a ``configure`` method that accepts a dict mapping
    substring patterns to ``{"stdout": str, "exitcode": int}`` objects.
    """
    log_file = tmp_path / "tmux_calls.log"
    config_file = tmp_path / "tmux_config.json"

    mock_bin = tmp_path / "bin"
    mock_bin.mkdir()
    tmux_mock = mock_bin / "tmux"
    tmux_mock.write_text(
        "#!/usr/bin/env python3\n"
        "import sys, json\n"
        f'cmd = " ".join(sys.argv[1:])\n'
        f'with open("{log_file}", "a") as f:\n'
        f'    f.write(cmd + "\\n")\n'
        f"try:\n"
        f'    cfg = json.loads(open("{config_file}").read())\n'
        f"except Exception:\n"
        f"    cfg = {{}}\n"
        f"for pattern, val in cfg.items():\n"
        f'    if pattern == "__default__":\n'
        f"        continue\n"
        f"    if pattern in cmd:\n"
        f'        sys.stdout.write(val.get("stdout", ""))\n'
        f'        sys.exit(val.get("exitcode", 0))\n'
        f'__default = cfg.get("__default__", {{"exitcode": 0, "stdout": ""}})\n'
        f'sys.stdout.write(__default.get("stdout", ""))\n'
        f"sys.exit(__default.get('exitcode', 0))\n"
    )
    tmux_mock.chmod(tmux_mock.stat().st_mode | stat.S_IEXEC)

    config_file.write_text("{}")

    class _Helper:
        def __init__(self):
            self.bin_dir = mock_bin
            self.log = log_file
            self.cfg = config_file

        def configure(self, responses: dict[str, dict], *, default: dict | None = None) -> None:
            """Set mock responses. Keys are substring patterns matched against the tmux command line.

            Values are {"stdout": "...", "exitcode": N}.
            Special key "__default__" is used when no pattern matches.
            """
            cfg = dict(responses)
            if default is not None:
                cfg["__default__"] = default
            self.cfg.write_text(json.dumps(cfg))

        def calls(self) -> list[str]:
            if not self.log.exists():
                return []
            text = self.log.read_text().strip()
            return text.splitlines() if text else []

        def reset(self) -> None:
            """Reset the call log."""
            if self.log.exists():
                self.log.unlink()

    helper = _Helper()
    return helper


def _run_tm(args: list[str], mock, **kwargs) -> subprocess.CompletedProcess:
    """Run the tm script with PATH pointing at the mock tmux binary."""
    env = os.environ.copy()
    env["PATH"] = str(mock.bin_dir) + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        ["bash", str(TM_SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=5,
        **kwargs,
    )


# ── No arguments / help ───────────────────────────────────────────────


def test_no_args_shows_usage(mock_tmux):
    """tm with no arguments shows usage and exits 0."""
    mock_tmux.configure({"list-sessions": {"stdout": "session1\nsession2", "exitcode": 0}})
    r = _run_tm([], mock_tmux)
    assert r.returncode == 0
    assert "Usage:" in r.stdout
    assert "tm ls" in r.stdout
    assert "tm kill" in r.stdout


def test_no_args_lists_sessions(mock_tmux):
    """tm with no arguments shows current sessions."""
    mock_tmux.configure({"list-sessions": {"stdout": "main\nwork", "exitcode": 0}})
    r = _run_tm([], mock_tmux)
    assert r.returncode == 0
    assert "main" in r.stdout
    assert "work" in r.stdout


def test_no_args_no_sessions(mock_tmux):
    """tm with no arguments shows 'No active sessions' when tmux has none."""
    mock_tmux.configure({"list-sessions": {"stdout": "", "exitcode": 1}})
    r = _run_tm([], mock_tmux)
    assert r.returncode == 0
    assert "No active sessions" in r.stdout


def test_tm_help_flag(mock_tmux):
    """tm --help shows usage and exits 0."""
    mock_tmux.configure({"list-sessions": {"stdout": "", "exitcode": 1}})
    r = _run_tm(["--help"], mock_tmux)
    assert r.returncode == 0
    assert "Usage:" in r.stdout


def test_h_flag(mock_tmux):
    """tm -h shows usage and exits 0."""
    mock_tmux.configure({"list-sessions": {"stdout": "", "exitcode": 1}})
    r = _run_tm(["-h"], mock_tmux)
    assert r.returncode == 0
    assert "Usage:" in r.stdout


# ── ls subcommand ─────────────────────────────────────────────────────


def test_ls_lists_sessions(mock_tmux):
    """tm ls lists active tmux sessions."""
    mock_tmux.configure({"list-sessions": {"stdout": "dev\nmain", "exitcode": 0}})
    r = _run_tm(["ls"], mock_tmux)
    assert r.returncode == 0
    assert "dev" in r.stdout
    assert "main" in r.stdout


def test_ls_no_sessions(mock_tmux):
    """tm ls shows 'No active sessions' when tmux returns nothing."""
    mock_tmux.configure({"list-sessions": {"stdout": "", "exitcode": 1}})
    r = _run_tm(["ls"], mock_tmux)
    assert r.returncode == 0
    assert "No active sessions" in r.stdout


# ── kill subcommand ───────────────────────────────────────────────────


def test_kill_without_session_name(mock_tmux):
    """tm kill without session name prints error and exits 1."""
    r = _run_tm(["kill"], mock_tmux)
    assert r.returncode == 1
    assert "Please specify a session name" in r.stdout


def test_kill_named_session(mock_tmux):
    """tm kill <name> calls tmux kill-session -t <name>."""
    mock_tmux.configure({})
    r = _run_tm(["kill", "mywork"], mock_tmux)
    assert r.returncode == 0
    calls = mock_tmux.calls()
    assert any("kill-session -t mywork" in c for c in calls)


def test_kill_session_with_special_chars(mock_tmux):
    """tm kill handles session names with dashes and dots."""
    mock_tmux.configure({})
    r = _run_tm(["kill", "my-session.v2"], mock_tmux)
    assert r.returncode == 0
    calls = mock_tmux.calls()
    assert any("kill-session -t my-session.v2" in c for c in calls)


# ── killall subcommand ────────────────────────────────────────────────


def test_killall(mock_tmux):
    """tm killall calls tmux kill-server."""
    mock_tmux.configure({})
    r = _run_tm(["killall"], mock_tmux)
    assert r.returncode == 0
    assert "All tmux sessions killed" in r.stdout
    assert any("kill-server" in c for c in mock_tmux.calls())


# ── session attach / create ───────────────────────────────────────────


def test_attach_existing_session(mock_tmux):
    """tm <name> attaches when session already exists."""
    mock_tmux.configure(
        {
            "has-session": {"stdout": "", "exitcode": 0},
        }
    )
    r = _run_tm(["work"], mock_tmux)
    assert r.returncode == 0
    calls = mock_tmux.calls()
    assert any("has-session -t work" in c for c in calls)
    assert any("attach-session -t work" in c for c in calls)
    assert "Attaching to existing session: work" in r.stdout


def test_create_new_session(mock_tmux):
    """tm <name> creates new session when it does not exist."""
    mock_tmux.configure(
        {"has-session": {"stdout": "", "exitcode": 1}},
        default={"stdout": "", "exitcode": 0},
    )
    r = _run_tm(["devproj"], mock_tmux)
    assert r.returncode == 0
    calls = mock_tmux.calls()
    assert any("has-session -t devproj" in c for c in calls)
    assert any("new-session -d -s devproj" in c for c in calls)
    assert any("attach-session -t devproj" in c for c in calls)
    assert "Creating new session: devproj" in r.stdout


def test_create_session_calls_new_before_attach(mock_tmux):
    """tm <name> calls new-session before attach-session for new sessions."""
    mock_tmux.configure(
        {"has-session": {"stdout": "", "exitcode": 1}},
        default={"stdout": "", "exitcode": 0},
    )
    mock_tmux.reset()
    r = _run_tm(["fresh"], mock_tmux)
    assert r.returncode == 0
    calls = mock_tmux.calls()
    new_idx = next(i for i, c in enumerate(calls) if "new-session" in c)
    attach_idx = next(i for i, c in enumerate(calls) if "attach-session" in c)
    assert new_idx < attach_idx, "new-session must be called before attach-session"


# ── usage text content ────────────────────────────────────────────────


def test_usage_mentions_all_subcommands(mock_tmux):
    """Usage text documents ls, kill, and killall."""
    mock_tmux.configure({"list-sessions": {"stdout": "", "exitcode": 1}})
    r = _run_tm([], mock_tmux)
    assert r.returncode == 0
    assert "tm ls" in r.stdout
    assert "tm kill" in r.stdout
    assert "tm killall" in r.stdout


# ── Integration with real tmux (skip if no server) ────────────────────


@pytest.mark.skipif(
    shutil.which("tmux") is None,
    reason="tmux not installed",
)
def test_ls_with_real_tmux():
    """tm ls works with a real tmux server (integration test)."""
    r = subprocess.run(
        ["bash", str(TM_SCRIPT), "ls"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert r.returncode == 0
