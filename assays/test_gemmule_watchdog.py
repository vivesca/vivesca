from __future__ import annotations

"""Tests for gemmule-watchdog — system health monitor."""

import os
import shutil
import signal
import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


def _load():
    """Load gemmule-watchdog by exec-ing its source."""
    src = open("/home/terry/germline/effectors/gemmule-watchdog").read()
    ns: dict = {"__name__": "gemmule_watchdog"}
    exec(src, ns)
    return ns


_mod = _load()

log = _mod["log"]
free_gb = _mod["free_gb"]
free_mb = _mod["free_mb"]
clean_temps = _mod["clean_temps"]
rotate_log = _mod["rotate_log"]
kill_runaway_golems = _mod["kill_runaway_golems"]
check_cycle = _mod["check_cycle"]
main = _mod["main"]

POLL = _mod["POLL"]
HOME = _mod["HOME"]
LOG = _mod["LOG"]
GERMLINE = _mod["GERMLINE"]
DISK_WARN_GB = _mod["DISK_WARN_GB"]
DISK_CRIT_GB = _mod["DISK_CRIT_GB"]
ROOT_WARN_MB = _mod["ROOT_WARN_MB"]
LOG_MAX_MB = _mod["LOG_MAX_MB"]
GOLEM_MAX_SECONDS = _mod["GOLEM_MAX_SECONDS"]
GOLEM_MAX_RSS_MB = _mod["GOLEM_MAX_RSS_MB"]


class _PatchMod:
    """Context manager to temporarily replace a name in the exec'd module dict."""

    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.orig = None

    def __enter__(self):
        self.orig = _mod[self.name]
        _mod[self.name] = self.value
        return self.value

    def __exit__(self, *exc):
        _mod[self.name] = self.orig


# ── Constant verification ──────────────────────────────────────────────


def test_constants_have_expected_values():
    """All threshold constants have expected values."""
    assert POLL == 60
    assert DISK_WARN_GB == 2.0
    assert DISK_CRIT_GB == 1.0
    assert ROOT_WARN_MB == 500
    assert LOG_MAX_MB == 10
    assert GOLEM_MAX_SECONDS == 2400
    assert GOLEM_MAX_RSS_MB == 2048


def test_home_is_path_home():
    """HOME is Path.home()."""
    assert HOME == Path.home()


def test_germline_is_home_germline():
    """GERMLINE is HOME / 'germline'."""
    assert GERMLINE == HOME / "germline"


def test_log_path_under_home_tmp():
    """LOG path is ~/tmp/gemmule-watchdog.log."""
    assert LOG == HOME / "tmp" / "gemmule-watchdog.log"


# ── log() tests ────────────────────────────────────────────────────────


def test_log_writes_with_timestamp(tmp_path):
    """log() writes [timestamp] msg to LOG file."""
    logpath = tmp_path / "test.log"
    with _PatchMod("LOG", logpath):
        log("hello world")
        content = logpath.read_text()
        assert content.startswith("[")
        assert "] hello world\n" in content


def test_log_appends_multiple_messages(tmp_path):
    """log() appends messages rather than overwriting."""
    logpath = tmp_path / "test.log"
    with _PatchMod("LOG", logpath):
        log("first")
        log("second")
        lines = logpath.read_text().strip().splitlines()
        assert len(lines) == 2
        assert "first" in lines[0]
        assert "second" in lines[1]


def test_log_creates_parent_directory(tmp_path):
    """log() creates parent directory if it does not exist."""
    logpath = tmp_path / "deep" / "nested" / "test.log"
    with _PatchMod("LOG", logpath):
        log("created dirs")
        assert logpath.exists()
        assert "created dirs" in logpath.read_text()


def test_log_timestamp_format(tmp_path):
    """log() timestamp matches YYYY-MM-DD HH:MM:SS format."""
    logpath = tmp_path / "test.log"
    with _PatchMod("LOG", logpath):
        log("check format")
        line = logpath.read_text().strip()
        ts = line.split("] ")[0].lstrip("[")
        datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")


# ── free_gb() / free_mb() tests ───────────────────────────────────────


def test_free_gb_returns_positive_float():
    """free_gb returns a positive float for a valid path."""
    result = free_gb(Path("/"))
    assert isinstance(result, float)
    assert result > 0


def test_free_gb_returns_999_on_error():
    """free_gb returns 999.0 when disk_usage raises."""
    with patch("shutil.disk_usage", side_effect=OSError("nope")):
        assert free_gb(Path("/nonexistent")) == 999.0


def test_free_mb_converts_gb_to_mb():
    """free_mb returns free_gb * 1024."""
    with patch("shutil.disk_usage") as mock_du:
        usage = MagicMock()
        usage.free = 2 * 1024**3  # 2 GB in bytes
        mock_du.return_value = usage
        result = free_mb(Path("/"))
    assert result == pytest.approx(2048.0)


def test_free_mb_nonexistent_returns_large():
    """free_mb returns 999.0*1024 for nonexistent path."""
    with patch("shutil.disk_usage", side_effect=FileNotFoundError):
        result = free_mb(Path("/no/such/mount"))
    assert result == pytest.approx(999.0 * 1024)


# ── rotate_log() tests ────────────────────────────────────────────────


def test_rotate_log_skips_nonexistent(tmp_path):
    """rotate_log does nothing when file does not exist."""
    f = tmp_path / "nope.log"
    with _PatchMod("LOG", tmp_path / "other.log"):
        rotate_log(f)
    assert not f.exists()
    assert not (tmp_path / "nope.log.1").exists()


def test_rotate_log_small_file_not_rotated(tmp_path):
    """rotate_log does not rotate file under max_mb."""
    f = tmp_path / "small.log"
    f.write_bytes(b"x" * 100)
    with _PatchMod("LOG", tmp_path / "other.log"):
        rotate_log(f, max_mb=10)
    assert f.exists()
    assert not (tmp_path / "small.log.1").exists()


def test_rotate_log_large_file_rotated(tmp_path):
    """rotate_log renames file to .1 when over threshold."""
    f = tmp_path / "big.log"
    f.write_bytes(b"x" * (11 * 1024 * 1024))  # 11 MB
    with _PatchMod("LOG", tmp_path / "other.log"):
        rotate_log(f, max_mb=10)
    assert not f.exists()
    assert (tmp_path / "big.log.1").exists()


def test_rotate_log_overwrites_existing_dot1(tmp_path):
    """rotate_log removes existing .1 file before renaming."""
    f = tmp_path / "big.log"
    old_dot1 = tmp_path / "big.log.1"
    old_dot1.write_text("old content\n")
    f.write_bytes(b"x" * (11 * 1024 * 1024))
    with _PatchMod("LOG", tmp_path / "other.log"):
        rotate_log(f, max_mb=10)
    assert not f.exists()
    assert old_dot1.exists()
    assert old_dot1.stat().st_size == 11 * 1024 * 1024


def test_rotate_log_exact_threshold_not_rotated(tmp_path):
    """rotate_log does not rotate file exactly at threshold (must exceed)."""
    f = tmp_path / "exact.log"
    f.write_bytes(b"x" * (10 * 1024 * 1024))  # exactly 10 MB
    with _PatchMod("LOG", tmp_path / "other.log"):
        rotate_log(f, max_mb=10)
    assert f.exists()
    assert not (tmp_path / "exact.log.1").exists()


def test_rotate_log_custom_max_mb(tmp_path):
    """rotate_log respects custom max_mb parameter."""
    f = tmp_path / "tiny.log"
    f.write_bytes(b"x" * 100)
    with _PatchMod("LOG", tmp_path / "other.log"):
        rotate_log(f, max_mb=0.00001)  # ~10 bytes threshold
    assert not f.exists()
    assert (tmp_path / "tiny.log.1").exists()


def test_rotate_log_writes_log_message(tmp_path):
    """rotate_log writes a log message when rotating."""
    f = tmp_path / "big.log"
    logpath = tmp_path / "watchdog.log"
    f.write_bytes(b"x" * (11 * 1024 * 1024))
    with _PatchMod("LOG", logpath):
        rotate_log(f, max_mb=10)
    content = logpath.read_text()
    assert "Rotated big.log" in content


def test_rotate_log_empty_file_not_rotated(tmp_path):
    """rotate_log does not rotate an empty file."""
    f = tmp_path / "empty.log"
    f.write_bytes(b"")
    with _PatchMod("LOG", tmp_path / "other.log"):
        rotate_log(f, max_mb=10)
    assert f.exists()
    assert not (tmp_path / "empty.log.1").exists()


# ── clean_temps() tests ───────────────────────────────────────────────


def test_clean_temps_removes_pytest_of_terry(tmp_path):
    """clean_temps removes pytest-of-terry directories."""
    pytest_dir = tmp_path / "pytest-of-terry"
    pytest_dir.mkdir()
    (pytest_dir / "test_foo.py").write_text("# test")
    with _PatchMod("GERMLINE", tmp_path):
        with patch("subprocess.run"):
            with patch.object(Path, "glob", return_value=iter([])):
                cleaned = clean_temps()
    assert not pytest_dir.exists()
    assert cleaned >= 1


def test_clean_temps_no_dirs_returns_zero(tmp_path):
    """clean_temps returns 0 when no temp dirs exist."""
    with _PatchMod("GERMLINE", tmp_path):
        with patch("subprocess.run"):
            with patch.object(Path, "glob", return_value=iter([])):
                cleaned = clean_temps()
    assert cleaned == 0


def test_clean_temps_runs_find_pycache(tmp_path):
    """clean_temps runs find command to remove __pycache__ dirs."""
    with _PatchMod("GERMLINE", tmp_path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with patch.object(Path, "glob", return_value=iter([])):
                clean_temps()
            calls = mock_run.call_args_list
            assert any("find" in str(c) and "__pycache__" in str(c) for c in calls)


def test_clean_temps_removes_claude_tmp(tmp_path):
    """clean_temps removes /tmp/claude-* directories."""
    claude_dir = tmp_path / "claude-session-abc"
    claude_dir.mkdir()
    (claude_dir / "data.json").write_text("{}")

    with _PatchMod("GERMLINE", tmp_path):
        with patch("subprocess.run"):
            with patch.object(Path, "glob", return_value=iter([claude_dir])):
                cleaned = clean_temps()
    assert cleaned >= 1


# ── kill_runaway_golems() tests ───────────────────────────────────────


def _ps_output(procs):
    """Build fake ps output. Each proc: (pid, elapsed_s, rss_kb)."""
    return "\n".join(f"{p} {e} {r} claude" for p, e, r in procs)


def test_kill_runaway_no_processes():
    """kill_runaway_golems returns 0 when no processes found."""
    mr = MagicMock(stdout="", returncode=0)
    with patch("subprocess.run", return_value=mr):
        assert kill_runaway_golems() == 0


def test_kill_runaway_healthy_process_not_killed():
    """kill_runaway_golems does not kill processes within limits."""
    mr = MagicMock(stdout=_ps_output([(12345, 100, 512000)]), returncode=0)
    with patch("subprocess.run", return_value=mr):
        with patch("os.kill") as mock_kill:
            assert kill_runaway_golems() == 0
    mock_kill.assert_not_called()


def test_kill_runaway_time_violation():
    """kill_runaway_golems kills processes exceeding time limit."""
    elapsed = GOLEM_MAX_SECONDS + 100
    mr = MagicMock(stdout=_ps_output([(12345, elapsed, 512000)]), returncode=0)
    with patch("subprocess.run", return_value=mr):
        with patch("os.kill") as mock_kill:
            assert kill_runaway_golems() == 1
    mock_kill.assert_called_once_with(12345, signal.SIGTERM)


def test_kill_runaway_memory_violation():
    """kill_runaway_golems kills processes exceeding RSS limit."""
    rss_kb = (GOLEM_MAX_RSS_MB + 100) * 1024
    mr = MagicMock(stdout=_ps_output([(12346, 100, rss_kb)]), returncode=0)
    with patch("subprocess.run", return_value=mr):
        with patch("os.kill") as mock_kill:
            assert kill_runaway_golems() == 1
    mock_kill.assert_called_once_with(12346, signal.SIGTERM)


def test_kill_runaway_time_priority_over_memory():
    """If both thresholds exceeded, time branch fires first (if/elif)."""
    elapsed = GOLEM_MAX_SECONDS + 100
    rss_kb = (GOLEM_MAX_RSS_MB + 100) * 1024
    mr = MagicMock(stdout=_ps_output([(12345, elapsed, rss_kb)]), returncode=0)
    with patch("subprocess.run", return_value=mr):
        with patch("os.kill") as mock_kill:
            assert kill_runaway_golems() == 1
    mock_kill.assert_called_once_with(12345, signal.SIGTERM)


def test_kill_runaway_multiple_processes():
    """kill_runaway_golems processes multiple lines, kills only violators."""
    procs = [
        (111, GOLEM_MAX_SECONDS + 10, 512000),         # time violation
        (222, 100, (GOLEM_MAX_RSS_MB + 100) * 1024),   # memory violation
        (333, 50, 256000),                               # healthy
        (444, GOLEM_MAX_SECONDS + 500, 256000),         # time violation
    ]
    mr = MagicMock(stdout=_ps_output(procs), returncode=0)
    with patch("subprocess.run", return_value=mr):
        with patch("os.kill") as mock_kill:
            killed = kill_runaway_golems()
    assert killed == 3
    killed_pids = [c.args[0] for c in mock_kill.call_args_list]
    assert 111 in killed_pids
    assert 222 in killed_pids
    assert 444 in killed_pids
    assert 333 not in killed_pids


def test_kill_runaway_skips_malformed_lines():
    """kill_runaway_golems skips lines with fewer than 4 parts."""
    mr = MagicMock(stdout="123 45\n\n  \n12345 99999 999999 claude", returncode=0)
    with patch("subprocess.run", return_value=mr):
        with patch("os.kill") as mock_kill:
            killed = kill_runaway_golems()
    assert killed == 1


def test_kill_runaway_handles_subprocess_exception():
    """kill_runaway_golems handles subprocess exception gracefully."""
    with _PatchMod("LOG", Path("/dev/null")):
        with patch("subprocess.run", side_effect=OSError("boom")):
            assert kill_runaway_golems() == 0


def test_kill_runaway_exact_threshold_not_killed():
    """At exactly the threshold, process is NOT killed (> not >=)."""
    rss_kb = GOLEM_MAX_RSS_MB * 1024
    mr = MagicMock(
        stdout=_ps_output([(12345, GOLEM_MAX_SECONDS, rss_kb)]),
        returncode=0,
    )
    with patch("subprocess.run", return_value=mr):
        with patch("os.kill") as mock_kill:
            assert kill_runaway_golems() == 0
    mock_kill.assert_not_called()


def test_kill_runaway_one_over_threshold_killed():
    """Just 1 second over the threshold triggers kill."""
    mr = MagicMock(
        stdout=_ps_output([(12345, GOLEM_MAX_SECONDS + 1, 512000)]),
        returncode=0,
    )
    with patch("subprocess.run", return_value=mr):
        with patch("os.kill") as mock_kill:
            assert kill_runaway_golems() == 1


def test_kill_runaway_logs_messages(tmp_path):
    """kill_runaway_golems writes log messages for killed processes."""
    logpath = tmp_path / "test.log"
    with _PatchMod("LOG", logpath):
        elapsed = GOLEM_MAX_SECONDS + 100
        mr = MagicMock(stdout=_ps_output([(12348, elapsed, 512000)]), returncode=0)
        with patch("subprocess.run", return_value=mr):
            with patch("os.kill"):
                kill_runaway_golems()
        content = logpath.read_text()
        assert "KILLED runaway PID 12348" in content


def test_kill_runaway_logs_memory_hog(tmp_path):
    """kill_runaway_golems writes 'memory hog' log for RSS violation."""
    logpath = tmp_path / "test.log"
    with _PatchMod("LOG", logpath):
        rss_kb = (GOLEM_MAX_RSS_MB + 100) * 1024
        mr = MagicMock(stdout=_ps_output([(12349, 100, rss_kb)]), returncode=0)
        with patch("subprocess.run", return_value=mr):
            with patch("os.kill"):
                kill_runaway_golems()
        content = logpath.read_text()
        assert "KILLED memory hog PID 12349" in content


# ── check_cycle() tests ───────────────────────────────────────────────


def test_check_cycle_healthy_no_action(tmp_path):
    """check_cycle does not clean when disk is healthy."""
    logpath = tmp_path / "wd.log"
    mock_clean = MagicMock(return_value=0)
    mock_kill = MagicMock(return_value=0)
    with _PatchMod("LOG", logpath), \
         _PatchMod("free_gb", MagicMock(return_value=50.0)), \
         _PatchMod("free_mb", MagicMock(return_value=10000.0)), \
         _PatchMod("clean_temps", mock_clean), \
         _PatchMod("kill_runaway_golems", mock_kill):
        with patch("subprocess.run"):
            check_cycle()
    mock_clean.assert_not_called()


def test_check_cycle_disk_warn_triggers_clean(tmp_path):
    """check_cycle calls clean_temps when volume free < DISK_WARN_GB."""
    logpath = tmp_path / "wd.log"
    mock_clean = MagicMock(return_value=3)
    with _PatchMod("LOG", logpath), \
         _PatchMod("free_gb", MagicMock(side_effect=[1.5, 1.5])), \
         _PatchMod("free_mb", MagicMock(return_value=10000.0)), \
         _PatchMod("clean_temps", mock_clean), \
         _PatchMod("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            check_cycle()
    mock_clean.assert_called()


def test_check_cycle_disk_critical_triggers_pkill(tmp_path):
    """check_cycle kills golems when volume < DISK_CRIT_GB after cleaning."""
    logpath = tmp_path / "wd.log"
    with _PatchMod("LOG", logpath), \
         _PatchMod("free_gb", MagicMock(side_effect=[0.5, 0.5])), \
         _PatchMod("free_mb", MagicMock(return_value=10000.0)), \
         _PatchMod("clean_temps", MagicMock(return_value=0)), \
         _PatchMod("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run") as mock_run:
            check_cycle()
    pkill_calls = [c for c in mock_run.call_args_list if "pkill" in str(c)]
    assert len(pkill_calls) >= 1


def test_check_cycle_root_warn_triggers_clean(tmp_path):
    """check_cycle cleans temps when root free < ROOT_WARN_MB."""
    logpath = tmp_path / "wd.log"
    mock_clean = MagicMock(return_value=0)
    with _PatchMod("LOG", logpath), \
         _PatchMod("free_gb", MagicMock(return_value=50.0)), \
         _PatchMod("free_mb", MagicMock(return_value=300.0)), \
         _PatchMod("clean_temps", mock_clean), \
         _PatchMod("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            check_cycle()
    mock_clean.assert_called()


def test_check_cycle_rotates_all_logs(tmp_path):
    """check_cycle calls rotate_log for every configured log file."""
    logpath = tmp_path / "wd.log"
    mock_rotate = MagicMock()
    with _PatchMod("LOG", logpath), \
         _PatchMod("free_gb", MagicMock(return_value=50.0)), \
         _PatchMod("free_mb", MagicMock(return_value=10000.0)), \
         _PatchMod("rotate_log", mock_rotate), \
         _PatchMod("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            check_cycle()
    assert mock_rotate.call_count == 8


def test_check_cycle_calls_kill_runaway(tmp_path):
    """check_cycle calls kill_runaway_golems."""
    logpath = tmp_path / "wd.log"
    mock_kill = MagicMock(return_value=0)
    with _PatchMod("LOG", logpath), \
         _PatchMod("free_gb", MagicMock(return_value=50.0)), \
         _PatchMod("free_mb", MagicMock(return_value=10000.0)), \
         _PatchMod("kill_runaway_golems", mock_kill):
        with patch("subprocess.run"):
            check_cycle()
    mock_kill.assert_called_once()


def test_check_cycle_logs_disk_warning(tmp_path):
    """check_cycle logs a warning when disk is below DISK_WARN_GB."""
    logpath = tmp_path / "wd.log"
    with _PatchMod("LOG", logpath), \
         _PatchMod("free_gb", MagicMock(side_effect=[1.5, 1.5])), \
         _PatchMod("free_mb", MagicMock(return_value=10000.0)), \
         _PatchMod("clean_temps", MagicMock(return_value=3)), \
         _PatchMod("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            check_cycle()
    content = logpath.read_text()
    assert "DISK WARN" in content
    assert "cleaned 3" in content


def test_check_cycle_logs_root_warning(tmp_path):
    """check_cycle logs a warning when /tmp free is below ROOT_WARN_MB."""
    logpath = tmp_path / "wd.log"
    with _PatchMod("LOG", logpath), \
         _PatchMod("free_gb", MagicMock(return_value=50.0)), \
         _PatchMod("free_mb", MagicMock(return_value=200.0)), \
         _PatchMod("clean_temps", MagicMock(return_value=0)), \
         _PatchMod("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            check_cycle()
    content = logpath.read_text()
    assert "ROOT WARN" in content


# ── main() tests ──────────────────────────────────────────────────────


def test_main_help_flag(capsys):
    """main() with --help prints docstring and returns 0."""
    with patch.object(_mod["sys"], "argv", ["watchdog", "--help"]):
        rc = main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "system health monitor" in out.lower() or "gemmule-watchdog" in out


def test_main_h_flag(capsys):
    """main() with -h prints docstring and returns 0."""
    with patch.object(_mod["sys"], "argv", ["watchdog", "-h"]):
        rc = main()
    assert rc == 0
    assert len(capsys.readouterr().out) > 0


def test_main_loop_interrupts_cleanly():
    """KeyboardInterrupt stops the loop and returns 0."""
    mock_sleep = MagicMock(side_effect=KeyboardInterrupt())
    with _PatchMod("LOG", Path("/dev/null")), \
         _PatchMod("check_cycle", MagicMock()):
        with patch.object(_mod["sys"], "argv", ["watchdog"]):
            with patch.object(_mod["time"], "sleep", mock_sleep):
                rc = main()
    assert rc == 0


def test_main_runs_check_cycle_then_sleeps():
    """check_cycle called at least once before sleep."""
    calls = []

    def fake_cycle():
        calls.append(1)
        raise KeyboardInterrupt

    with _PatchMod("LOG", Path("/dev/null")), \
         _PatchMod("check_cycle", fake_cycle):
        with patch.object(_mod["sys"], "argv", ["watchdog"]):
            main()
    assert len(calls) >= 1


def test_main_logs_start_and_stop(tmp_path):
    """main() logs 'Watchdog started' and 'Watchdog stopped'."""
    logpath = tmp_path / "wd.log"
    with _PatchMod("LOG", logpath), \
         _PatchMod("check_cycle", MagicMock(side_effect=KeyboardInterrupt)):
        with patch.object(_mod["sys"], "argv", ["watchdog"]):
            with patch.object(_mod["time"], "sleep", MagicMock()):
                main()
    content = logpath.read_text()
    assert "Watchdog started" in content
    assert "Watchdog stopped" in content


def test_main_multiple_cycles(tmp_path):
    """main() runs multiple cycles before KeyboardInterrupt."""
    logpath = tmp_path / "wd.log"
    count = 0

    def count_cycle():
        nonlocal count
        count += 1
        if count >= 3:
            raise KeyboardInterrupt

    with _PatchMod("LOG", logpath), \
         _PatchMod("check_cycle", count_cycle):
        with patch.object(_mod["sys"], "argv", ["watchdog"]):
            with patch.object(_mod["time"], "sleep", MagicMock()):
                main()
    assert count == 3
