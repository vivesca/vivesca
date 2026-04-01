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


class _P:
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


def _safe_rmtree(original_rmtree):
    """Wrap shutil.rmtree to skip /tmp/pytest-vivesca (our tmp_path base)."""
    def wrapper(path, *args, **kwargs):
        try:
            p = str(path)
        except Exception:
            p = ""
        if "pytest-vivesca" in p or "pytest-of-terry" in p and "/tmp/" in p:
            # Skip removing pytest's own base directories during tests
            if Path("/tmp/pytest-vivesca").resolve() == Path(path).resolve():
                return
        return original_rmtree(path, *args, **kwargs)
    return wrapper


@pytest.fixture(autouse=True)
def _protect_pytest_tmp():
    """Ensure pytest's tmp_path base dir survives clean_temps() calls."""
    Path("/tmp/pytest-vivesca").mkdir(parents=True, exist_ok=True)
    Path("/tmp/pytest-of-terry").mkdir(parents=True, exist_ok=True)
    yield
    Path("/tmp/pytest-vivesca").mkdir(parents=True, exist_ok=True)


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
    assert HOME == Path.home()


def test_germline_is_home_germline():
    assert GERMLINE == HOME / "germline"


def test_log_path_under_home_tmp():
    assert LOG == HOME / "tmp" / "gemmule-watchdog.log"


# ── log() tests ────────────────────────────────────────────────────────


def test_log_writes_with_timestamp(tmp_path):
    logpath = tmp_path / "test.log"
    with _P("LOG", logpath):
        log("hello world")
        content = logpath.read_text()
        assert content.startswith("[")
        assert "] hello world\n" in content


def test_log_appends_multiple_messages(tmp_path):
    logpath = tmp_path / "test.log"
    with _P("LOG", logpath):
        log("first")
        log("second")
        lines = logpath.read_text().strip().splitlines()
        assert len(lines) == 2
        assert "first" in lines[0]
        assert "second" in lines[1]


def test_log_creates_parent_directory(tmp_path):
    logpath = tmp_path / "deep" / "nested" / "test.log"
    with _P("LOG", logpath):
        log("created dirs")
        assert logpath.exists()
        assert "created dirs" in logpath.read_text()


def test_log_timestamp_format(tmp_path):
    logpath = tmp_path / "test.log"
    with _P("LOG", logpath):
        log("check format")
        line = logpath.read_text().strip()
        ts = line.split("] ")[0].lstrip("[")
        datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")


# ── free_gb() / free_mb() tests ───────────────────────────────────────


def test_free_gb_returns_positive_float():
    result = free_gb(Path("/"))
    assert isinstance(result, float)
    assert result > 0


def test_free_gb_returns_999_on_error():
    with patch("shutil.disk_usage", side_effect=OSError("nope")):
        assert free_gb(Path("/nonexistent")) == 999.0


def test_free_mb_converts_gb_to_mb():
    with patch("shutil.disk_usage") as mock_du:
        usage = MagicMock()
        usage.free = 2 * 1024**3
        mock_du.return_value = usage
        result = free_mb(Path("/"))
    assert result == pytest.approx(2048.0)


def test_free_mb_nonexistent_returns_large():
    with patch("shutil.disk_usage", side_effect=FileNotFoundError):
        result = free_mb(Path("/no/such/mount"))
    assert result == pytest.approx(999.0 * 1024)


# ── rotate_log() tests ────────────────────────────────────────────────


def test_rotate_log_skips_nonexistent(tmp_path):
    f = tmp_path / "nope.log"
    with _P("LOG", tmp_path / "other.log"):
        rotate_log(f)
    assert not f.exists()
    assert not (tmp_path / "nope.log.1").exists()


def test_rotate_log_small_file_not_rotated(tmp_path):
    f = tmp_path / "small.log"
    f.write_bytes(b"x" * 100)
    with _P("LOG", tmp_path / "other.log"):
        rotate_log(f, max_mb=10)
    assert f.exists()
    assert not (tmp_path / "small.log.1").exists()


def test_rotate_log_large_file_rotated(tmp_path):
    f = tmp_path / "big.log"
    f.write_bytes(b"x" * (11 * 1024 * 1024))
    with _P("LOG", tmp_path / "other.log"):
        rotate_log(f, max_mb=10)
    assert not f.exists()
    assert (tmp_path / "big.log.1").exists()


def test_rotate_log_overwrites_existing_dot1(tmp_path):
    f = tmp_path / "big.log"
    old_dot1 = tmp_path / "big.log.1"
    old_dot1.write_text("old content\n")
    f.write_bytes(b"x" * (11 * 1024 * 1024))
    with _P("LOG", tmp_path / "other.log"):
        rotate_log(f, max_mb=10)
    assert not f.exists()
    assert old_dot1.exists()
    assert old_dot1.stat().st_size == 11 * 1024 * 1024


def test_rotate_log_exact_threshold_not_rotated(tmp_path):
    f = tmp_path / "exact.log"
    f.write_bytes(b"x" * (10 * 1024 * 1024))
    with _P("LOG", tmp_path / "other.log"):
        rotate_log(f, max_mb=10)
    assert f.exists()
    assert not (tmp_path / "exact.log.1").exists()


def test_rotate_log_custom_max_mb(tmp_path):
    f = tmp_path / "tiny.log"
    f.write_bytes(b"x" * 100)
    with _P("LOG", tmp_path / "other.log"):
        rotate_log(f, max_mb=0.00001)
    assert not f.exists()
    assert (tmp_path / "tiny.log.1").exists()


def test_rotate_log_writes_log_message(tmp_path):
    f = tmp_path / "big.log"
    logpath = tmp_path / "watchdog.log"
    f.write_bytes(b"x" * (11 * 1024 * 1024))
    with _P("LOG", logpath):
        rotate_log(f, max_mb=10)
    content = logpath.read_text()
    assert "Rotated big.log" in content


def test_rotate_log_empty_file_not_rotated(tmp_path):
    f = tmp_path / "empty.log"
    f.write_bytes(b"")
    with _P("LOG", tmp_path / "other.log"):
        rotate_log(f, max_mb=10)
    assert f.exists()
    assert not (tmp_path / "empty.log.1").exists()


# ── clean_temps() tests ───────────────────────────────────────────────


def test_clean_temps_removes_pytest_of_terry(tmp_path):
    pytest_dir = tmp_path / "pytest-of-terry"
    pytest_dir.mkdir()
    (pytest_dir / "test_foo.py").write_text("# test")
    with _P("GERMLINE", tmp_path):
        with patch("subprocess.run"):
            with patch.object(Path, "glob", return_value=iter([])):
                cleaned = clean_temps()
    assert not pytest_dir.exists()
    assert cleaned >= 1


def test_clean_temps_no_dirs_returns_zero(tmp_path):
    with _P("GERMLINE", tmp_path):
        with patch("subprocess.run"):
            with patch.object(Path, "glob", return_value=iter([])):
                cleaned = clean_temps()
    assert cleaned == 0


def test_clean_temps_runs_find_pycache(tmp_path):
    with _P("GERMLINE", tmp_path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with patch.object(Path, "glob", return_value=iter([])):
                clean_temps()
            calls = mock_run.call_args_list
            assert any("find" in str(c) and "__pycache__" in str(c) for c in calls)


def test_clean_temps_removes_claude_tmp(tmp_path):
    claude_dir = tmp_path / "claude-session-abc"
    claude_dir.mkdir()
    (claude_dir / "data.json").write_text("{}")
    with _P("GERMLINE", tmp_path):
        with patch("subprocess.run"):
            with patch.object(Path, "glob", return_value=iter([claude_dir])):
                cleaned = clean_temps()
    assert cleaned >= 1


# ── kill_runaway_golems() tests ───────────────────────────────────────


def _ps(procs):
    """Build fake ps output. Each proc: (pid, elapsed_s, rss_kb)."""
    return "\n".join(f"{p} {e} {r} claude" for p, e, r in procs)


def test_kill_runaway_no_processes():
    mr = MagicMock(stdout="", returncode=0)
    with patch("subprocess.run", return_value=mr):
        assert kill_runaway_golems() == 0


def test_kill_runaway_healthy_not_killed():
    mr = MagicMock(stdout=_ps([(12345, 100, 512000)]), returncode=0)
    with patch("subprocess.run", return_value=mr):
        with patch("os.kill") as mock_kill:
            assert kill_runaway_golems() == 0
    mock_kill.assert_not_called()


def test_kill_runaway_time_violation():
    mr = MagicMock(stdout=_ps([(12345, GOLEM_MAX_SECONDS + 100, 512000)]), returncode=0)
    with patch("subprocess.run", return_value=mr):
        with patch("os.kill") as mock_kill:
            assert kill_runaway_golems() == 1
    mock_kill.assert_called_once_with(12345, signal.SIGTERM)


def test_kill_runaway_memory_violation():
    rss_kb = (GOLEM_MAX_RSS_MB + 100) * 1024
    mr = MagicMock(stdout=_ps([(12346, 100, rss_kb)]), returncode=0)
    with patch("subprocess.run", return_value=mr):
        with patch("os.kill") as mock_kill:
            assert kill_runaway_golems() == 1
    mock_kill.assert_called_once_with(12346, signal.SIGTERM)


def test_kill_runaway_time_priority_over_memory():
    elapsed = GOLEM_MAX_SECONDS + 100
    rss_kb = (GOLEM_MAX_RSS_MB + 100) * 1024
    mr = MagicMock(stdout=_ps([(12345, elapsed, rss_kb)]), returncode=0)
    with patch("subprocess.run", return_value=mr):
        with patch("os.kill") as mock_kill:
            assert kill_runaway_golems() == 1
    mock_kill.assert_called_once_with(12345, signal.SIGTERM)


def test_kill_runaway_multiple():
    procs = [
        (111, GOLEM_MAX_SECONDS + 10, 512000),
        (222, 100, (GOLEM_MAX_RSS_MB + 100) * 1024),
        (333, 50, 256000),
        (444, GOLEM_MAX_SECONDS + 500, 256000),
    ]
    mr = MagicMock(stdout=_ps(procs), returncode=0)
    with patch("subprocess.run", return_value=mr):
        with patch("os.kill") as mock_kill:
            killed = kill_runaway_golems()
    assert killed == 3
    pids = [c.args[0] for c in mock_kill.call_args_list]
    assert 111 in pids and 222 in pids and 444 in pids
    assert 333 not in pids


def test_kill_runaway_skips_malformed():
    mr = MagicMock(stdout="123 45\n\n  \n12345 99999 999999 claude", returncode=0)
    with patch("subprocess.run", return_value=mr):
        with patch("os.kill") as mock_kill:
            assert kill_runaway_golems() == 1


def test_kill_runaway_exception():
    with _P("LOG", Path("/dev/null")):
        with patch("subprocess.run", side_effect=OSError("boom")):
            assert kill_runaway_golems() == 0


def test_kill_runaway_exact_threshold_not_killed():
    rss_kb = GOLEM_MAX_RSS_MB * 1024
    mr = MagicMock(stdout=_ps([(12345, GOLEM_MAX_SECONDS, rss_kb)]), returncode=0)
    with patch("subprocess.run", return_value=mr):
        with patch("os.kill") as mock_kill:
            assert kill_runaway_golems() == 0
    mock_kill.assert_not_called()


def test_kill_runaway_one_over_killed():
    mr = MagicMock(stdout=_ps([(12345, GOLEM_MAX_SECONDS + 1, 512000)]), returncode=0)
    with patch("subprocess.run", return_value=mr):
        with patch("os.kill") as mock_kill:
            assert kill_runaway_golems() == 1


def test_kill_runaway_logs_time_kill(tmp_path):
    logpath = tmp_path / "test.log"
    with _P("LOG", logpath):
        mr = MagicMock(stdout=_ps([(12348, GOLEM_MAX_SECONDS + 100, 512000)]), returncode=0)
        with patch("subprocess.run", return_value=mr):
            with patch("os.kill"):
                kill_runaway_golems()
        assert "KILLED runaway PID 12348" in logpath.read_text()


def test_kill_runaway_logs_memory_hog(tmp_path):
    logpath = tmp_path / "test.log"
    with _P("LOG", logpath):
        rss_kb = (GOLEM_MAX_RSS_MB + 100) * 1024
        mr = MagicMock(stdout=_ps([(12349, 100, rss_kb)]), returncode=0)
        with patch("subprocess.run", return_value=mr):
            with patch("os.kill"):
                kill_runaway_golems()
        assert "KILLED memory hog PID 12349" in logpath.read_text()


# ── check_cycle() tests ───────────────────────────────────────────────


def test_check_cycle_healthy_no_action(tmp_path):
    logpath = tmp_path / "wd.log"
    mock_clean = MagicMock(return_value=0)
    with _P("LOG", logpath), \
         _P("free_gb", MagicMock(return_value=50.0)), \
         _P("free_mb", MagicMock(return_value=10000.0)), \
         _P("clean_temps", mock_clean), \
         _P("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            check_cycle()
    mock_clean.assert_not_called()


def test_check_cycle_disk_warn_triggers_clean(tmp_path):
    logpath = tmp_path / "wd.log"
    mock_clean = MagicMock(return_value=3)
    with _P("LOG", logpath), \
         _P("free_gb", MagicMock(side_effect=[1.5, 1.5])), \
         _P("free_mb", MagicMock(return_value=10000.0)), \
         _P("clean_temps", mock_clean), \
         _P("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            check_cycle()
    mock_clean.assert_called()


def test_check_cycle_disk_critical_triggers_pkill(tmp_path):
    logpath = tmp_path / "wd.log"
    with _P("LOG", logpath), \
         _P("free_gb", MagicMock(side_effect=[0.5, 0.5])), \
         _P("free_mb", MagicMock(return_value=10000.0)), \
         _P("clean_temps", MagicMock(return_value=0)), \
         _P("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run") as mock_run:
            check_cycle()
    assert any("pkill" in str(c) for c in mock_run.call_args_list)


def test_check_cycle_root_warn_triggers_clean(tmp_path):
    logpath = tmp_path / "wd.log"
    mock_clean = MagicMock(return_value=0)
    with _P("LOG", logpath), \
         _P("free_gb", MagicMock(return_value=50.0)), \
         _P("free_mb", MagicMock(return_value=300.0)), \
         _P("clean_temps", mock_clean), \
         _P("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            check_cycle()
    mock_clean.assert_called()


def test_check_cycle_rotates_all_logs(tmp_path):
    logpath = tmp_path / "wd.log"
    mock_rotate = MagicMock()
    with _P("LOG", logpath), \
         _P("free_gb", MagicMock(return_value=50.0)), \
         _P("free_mb", MagicMock(return_value=10000.0)), \
         _P("rotate_log", mock_rotate), \
         _P("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            check_cycle()
    assert mock_rotate.call_count == 8


def test_check_cycle_calls_kill_runaway(tmp_path):
    logpath = tmp_path / "wd.log"
    mock_kill = MagicMock(return_value=0)
    with _P("LOG", logpath), \
         _P("free_gb", MagicMock(return_value=50.0)), \
         _P("free_mb", MagicMock(return_value=10000.0)), \
         _P("kill_runaway_golems", mock_kill):
        with patch("subprocess.run"):
            check_cycle()
    mock_kill.assert_called_once()


def test_check_cycle_logs_disk_warning(tmp_path):
    logpath = tmp_path / "wd.log"
    with _P("LOG", logpath), \
         _P("free_gb", MagicMock(side_effect=[1.5, 1.5])), \
         _P("free_mb", MagicMock(return_value=10000.0)), \
         _P("clean_temps", MagicMock(return_value=3)), \
         _P("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            check_cycle()
    content = logpath.read_text()
    assert "DISK WARN" in content
    assert "cleaned 3" in content


def test_check_cycle_logs_root_warning(tmp_path):
    logpath = tmp_path / "wd.log"
    with _P("LOG", logpath), \
         _P("free_gb", MagicMock(return_value=50.0)), \
         _P("free_mb", MagicMock(return_value=200.0)), \
         _P("clean_temps", MagicMock(return_value=0)), \
         _P("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            check_cycle()
    assert "ROOT WARN" in logpath.read_text()


# ── main() tests ──────────────────────────────────────────────────────


def test_main_help_flag(capsys):
    with patch.object(_mod["sys"], "argv", ["watchdog", "--help"]):
        rc = main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "system health monitor" in out.lower() or "gemmule-watchdog" in out


def test_main_h_flag(capsys):
    with patch.object(_mod["sys"], "argv", ["watchdog", "-h"]):
        assert main() == 0
    assert len(capsys.readouterr().out) > 0


def test_main_loop_interrupts_cleanly():
    with _P("LOG", Path("/dev/null")), \
         _P("check_cycle", MagicMock()):
        with patch.object(_mod["sys"], "argv", ["watchdog"]):
            with patch.object(_mod["time"], "sleep", MagicMock(side_effect=KeyboardInterrupt())):
                rc = main()
    assert rc == 0


def test_main_runs_check_cycle():
    calls = []

    def fake_cycle():
        calls.append(1)
        raise KeyboardInterrupt

    with _P("LOG", Path("/dev/null")), \
         _P("check_cycle", fake_cycle):
        with patch.object(_mod["sys"], "argv", ["watchdog"]):
            main()
    assert len(calls) >= 1


def test_main_logs_start_and_stop(tmp_path):
    logpath = tmp_path / "wd.log"
    with _P("LOG", logpath), \
         _P("check_cycle", MagicMock(side_effect=KeyboardInterrupt)):
        with patch.object(_mod["sys"], "argv", ["watchdog"]):
            with patch.object(_mod["time"], "sleep", MagicMock()):
                main()
    content = logpath.read_text()
    assert "Watchdog started" in content
    assert "Watchdog stopped" in content


def test_main_multiple_cycles(tmp_path):
    logpath = tmp_path / "wd.log"
    count = 0

    def count_cycle():
        nonlocal count
        count += 1
        if count >= 3:
            raise KeyboardInterrupt

    with _P("LOG", logpath), \
         _P("check_cycle", count_cycle):
        with patch.object(_mod["sys"], "argv", ["watchdog"]):
            with patch.object(_mod["time"], "sleep", MagicMock()):
                main()
    assert count == 3
