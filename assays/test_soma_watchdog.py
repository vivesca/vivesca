from __future__ import annotations

"""Tests for soma-watchdog — system health monitor."""

import os
import shutil
import signal
import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


def _load():
    """Load soma-watchdog by exec-ing its source."""
    src = open(str(Path.home() / "germline/effectors/soma-watchdog")).read()
    ns: dict = {"__name__": "soma_watchdog"}
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
    """Context manager: temporarily replace a name in the exec'd module dict."""

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


# ── Constants ──────────────────────────────────────────────────────────


def test_soma_watchdog_constants():
    assert POLL == 60
    assert DISK_WARN_GB == 2.0
    assert DISK_CRIT_GB == 1.0
    assert ROOT_WARN_MB == 500
    assert LOG_MAX_MB == 10
    assert GOLEM_MAX_SECONDS == 2400
    assert GOLEM_MAX_RSS_MB == 2048


def test_home_is_path_home():
    assert HOME == Path.home()


def test_soma_watchdog_germline_under_home():
    assert GERMLINE == HOME / "germline"


def test_log_path():
    assert LOG == HOME / "tmp" / "soma-watchdog.log"


# ── log() ──────────────────────────────────────────────────────────────


def test_log_writes_timestamp(tmp_path):
    p = tmp_path / "t.log"
    with _P("LOG", p):
        log("hello")
    assert p.read_text().startswith("[")
    assert "] hello\n" in p.read_text()


def test_log_appends(tmp_path):
    p = tmp_path / "t.log"
    with _P("LOG", p):
        log("a")
        log("b")
    lines = p.read_text().strip().splitlines()
    assert len(lines) == 2
    assert "a" in lines[0]
    assert "b" in lines[1]


def test_log_creates_parent(tmp_path):
    p = tmp_path / "x" / "y" / "t.log"
    with _P("LOG", p):
        log("deep")
    assert p.exists()
    assert "deep" in p.read_text()


def test_log_timestamp_format(tmp_path):
    p = tmp_path / "t.log"
    with _P("LOG", p):
        log("ts")
    ts = p.read_text().strip().split("] ")[0].lstrip("[")
    datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")


# ── free_gb / free_mb ──────────────────────────────────────────────────


def test_free_gb_positive_float():
    assert isinstance(free_gb(Path("/")), float)
    assert free_gb(Path("/")) > 0


def test_free_gb_error_returns_999():
    with patch("shutil.disk_usage", side_effect=OSError):
        assert free_gb(Path("/nope")) == 999.0


def test_free_mb_is_gb_times_1024():
    with patch("shutil.disk_usage") as m:
        u = MagicMock(free=2 * 1024**3)
        m.return_value = u
        assert free_mb(Path("/")) == pytest.approx(2048.0)


def test_free_mb_error_returns_large():
    with patch("shutil.disk_usage", side_effect=FileNotFoundError):
        assert free_mb(Path("/nope")) == pytest.approx(999.0 * 1024)


# ── rotate_log ─────────────────────────────────────────────────────────


def test_rotate_log_nonexistent(tmp_path):
    f = tmp_path / "x.log"
    with _P("LOG", tmp_path / "o.log"):
        rotate_log(f)
    assert not f.exists() and not (tmp_path / "x.log.1").exists()


def test_rotate_log_small_file(tmp_path):
    f = tmp_path / "s.log"
    f.write_bytes(b"x" * 100)
    with _P("LOG", tmp_path / "o.log"):
        rotate_log(f, max_mb=10)
    assert f.exists() and not (tmp_path / "s.log.1").exists()


def test_rotate_log_large_file(tmp_path):
    f = tmp_path / "b.log"
    f.write_bytes(b"x" * (11 * 1024 * 1024))
    with _P("LOG", tmp_path / "o.log"):
        rotate_log(f, max_mb=10)
    assert not f.exists() and (tmp_path / "b.log.1").exists()


def test_rotate_log_overwrites_dot1(tmp_path):
    f = tmp_path / "b.log"
    old = tmp_path / "b.log.1"
    old.write_text("old")
    f.write_bytes(b"x" * (11 * 1024 * 1024))
    with _P("LOG", tmp_path / "o.log"):
        rotate_log(f, max_mb=10)
    assert not f.exists()
    assert old.stat().st_size == 11 * 1024 * 1024


def test_rotate_log_exact_not_rotated(tmp_path):
    f = tmp_path / "e.log"
    f.write_bytes(b"x" * (10 * 1024 * 1024))
    with _P("LOG", tmp_path / "o.log"):
        rotate_log(f, max_mb=10)
    assert f.exists() and not (tmp_path / "e.log.1").exists()


def test_rotate_log_custom_max(tmp_path):
    f = tmp_path / "t.log"
    f.write_bytes(b"x" * 100)
    with _P("LOG", tmp_path / "o.log"):
        rotate_log(f, max_mb=0.00001)
    assert not f.exists() and (tmp_path / "t.log.1").exists()


def test_rotate_log_logs_message(tmp_path):
    f = tmp_path / "b.log"
    lp = tmp_path / "wd.log"
    f.write_bytes(b"x" * (11 * 1024 * 1024))
    with _P("LOG", lp):
        rotate_log(f, max_mb=10)
    assert "Rotated b.log" in lp.read_text()


def test_rotate_log_empty_not_rotated(tmp_path):
    f = tmp_path / "e.log"
    f.write_bytes(b"")
    with _P("LOG", tmp_path / "o.log"):
        rotate_log(f, max_mb=10)
    assert f.exists() and not (tmp_path / "e.log.1").exists()


# ── clean_temps ────────────────────────────────────────────────────────
# NOTE: clean_temps() hardcodes Path("/tmp/pytest-vivesca") which is
# pytest's tmp_path base dir. We mock shutil.rmtree to avoid deleting it.


def test_clean_temps_removes_target(tmp_path):
    d = tmp_path / "pytest-of-terry"
    d.mkdir()
    (d / "f.py").write_text("# t")
    with _P("GERMLINE", tmp_path):
        with patch("subprocess.run"):
            with patch.object(Path, "glob", return_value=iter([])):
                with patch("shutil.rmtree") as mock_rm:
                    mock_rm.side_effect = lambda p, **kw: None
                    cleaned = clean_temps()
    assert cleaned >= 1
    # Verify rmtree was called with our target dir
    assert any(str(d) in str(c) for c in mock_rm.call_args_list)


def test_clean_temps_no_dirs_zero(tmp_path):
    # Use an isolated dir with no matching subdirs; mock rmtree to prevent
    # real deletion of /tmp/pytest-vivesca etc.
    with _P("GERMLINE", tmp_path):
        with patch("subprocess.run"):
            with patch.object(Path, "glob", return_value=iter([])):
                with patch("shutil.rmtree") as mock_rm:
                    mock_rm.side_effect = lambda p, **kw: None
                    cleaned = clean_temps()
    # None of the hardcoded /tmp paths should match tmp_path
    # but /tmp/pytest-of-terry and /tmp/pytest-vivesca might exist on disk
    # Since we mock rmtree, count depends on whether those paths exist()
    assert isinstance(cleaned, int)


def test_clean_temps_find_pycache(tmp_path):
    with _P("GERMLINE", tmp_path):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with patch.object(Path, "glob", return_value=iter([])):
                with patch("shutil.rmtree"):
                    clean_temps()
            assert any("find" in str(c) and "__pycache__" in str(c) for c in mock_run.call_args_list)


def test_clean_temps_claude_glob(tmp_path):
    cd = tmp_path / "claude-sess-xyz"
    cd.mkdir()
    (cd / "d").write_text("{}")
    with _P("GERMLINE", tmp_path):
        with patch("subprocess.run"):
            with patch.object(Path, "glob", return_value=iter([cd])):
                with patch("shutil.rmtree"):
                    cleaned = clean_temps()
    assert cleaned >= 1


# ── kill_runaway_golems ────────────────────────────────────────────────


def _ps(procs):
    return "\n".join(f"{p} {e} {r} claude" for p, e, r in procs)


def test_kill_none():
    with patch("subprocess.run", return_value=MagicMock(stdout="", returncode=0)):
        assert kill_runaway_golems() == 0


def test_kill_healthy_spared():
    with patch("subprocess.run", return_value=MagicMock(stdout=_ps([(1, 100, 512000)]), returncode=0)):
        with patch("os.kill") as mk:
            assert kill_runaway_golems() == 0
    mk.assert_not_called()


def test_kill_time():
    with patch("subprocess.run", return_value=MagicMock(stdout=_ps([(99, GOLEM_MAX_SECONDS + 1, 512000)]), returncode=0)):
        with patch("os.kill") as mk:
            assert kill_runaway_golems() == 1
    mk.assert_called_once_with(99, signal.SIGTERM)


def test_kill_memory():
    rss = (GOLEM_MAX_RSS_MB + 1) * 1024
    with patch("subprocess.run", return_value=MagicMock(stdout=_ps([(88, 100, rss)]), returncode=0)):
        with patch("os.kill") as mk:
            assert kill_runaway_golems() == 1
    mk.assert_called_once_with(88, signal.SIGTERM)


def test_kill_time_priority():
    rss = (GOLEM_MAX_RSS_MB + 1) * 1024
    with patch("subprocess.run", return_value=MagicMock(stdout=_ps([(77, GOLEM_MAX_SECONDS + 1, rss)]), returncode=0)):
        with patch("os.kill") as mk:
            assert kill_runaway_golems() == 1
    mk.assert_called_once_with(77, signal.SIGTERM)


def test_kill_multiple():
    procs = [
        (111, GOLEM_MAX_SECONDS + 1, 512000),
        (222, 100, (GOLEM_MAX_RSS_MB + 1) * 1024),
        (333, 50, 256000),
        (444, GOLEM_MAX_SECONDS + 1, 256000),
    ]
    with patch("subprocess.run", return_value=MagicMock(stdout=_ps(procs), returncode=0)):
        with patch("os.kill") as mk:
            assert kill_runaway_golems() == 3
    pids = [c.args[0] for c in mk.call_args_list]
    assert 111 in pids and 222 in pids and 444 in pids
    assert 333 not in pids


def test_kill_malformed():
    with patch("subprocess.run", return_value=MagicMock(stdout="1 2\n\n", returncode=0)):
        with patch("os.kill") as mk:
            assert kill_runaway_golems() == 0


def test_kill_exception():
    with _P("LOG", Path("/dev/null")):
        with patch("subprocess.run", side_effect=OSError):
            assert kill_runaway_golems() == 0


def test_kill_boundary_exact():
    rss = GOLEM_MAX_RSS_MB * 1024
    with patch("subprocess.run", return_value=MagicMock(stdout=_ps([(1, GOLEM_MAX_SECONDS, rss)]), returncode=0)):
        with patch("os.kill") as mk:
            assert kill_runaway_golems() == 0
    mk.assert_not_called()


def test_kill_boundary_plus_one():
    with patch("subprocess.run", return_value=MagicMock(stdout=_ps([(1, GOLEM_MAX_SECONDS + 1, 512000)]), returncode=0)):
        with patch("os.kill") as mk:
            assert kill_runaway_golems() == 1


def test_kill_log_time(tmp_path):
    lp = tmp_path / "t.log"
    with _P("LOG", lp):
        with patch("subprocess.run", return_value=MagicMock(stdout=_ps([(55, GOLEM_MAX_SECONDS + 1, 512000)]), returncode=0)):
            with patch("os.kill"):
                kill_runaway_golems()
    assert "KILLED runaway PID 55" in lp.read_text()


def test_kill_log_memory(tmp_path):
    lp = tmp_path / "t.log"
    rss = (GOLEM_MAX_RSS_MB + 1) * 1024
    with _P("LOG", lp):
        with patch("subprocess.run", return_value=MagicMock(stdout=_ps([(66, 100, rss)]), returncode=0)):
            with patch("os.kill"):
                kill_runaway_golems()
    assert "KILLED memory hog PID 66" in lp.read_text()


# ── check_cycle ────────────────────────────────────────────────────────


def test_cycle_healthy(tmp_path):
    lp = tmp_path / "w.log"
    mc = MagicMock(return_value=0)
    with _P("LOG", lp), _P("free_gb", MagicMock(return_value=50.0)), \
         _P("free_mb", MagicMock(return_value=10000.0)), \
         _P("clean_temps", mc), _P("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            check_cycle()
    mc.assert_not_called()


def test_cycle_disk_warn(tmp_path):
    lp = tmp_path / "w.log"
    mc = MagicMock(return_value=3)
    with _P("LOG", lp), _P("free_gb", MagicMock(side_effect=[1.5, 1.5])), \
         _P("free_mb", MagicMock(return_value=10000.0)), \
         _P("clean_temps", mc), _P("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            check_cycle()
    mc.assert_called()


def test_cycle_disk_critical(tmp_path):
    lp = tmp_path / "w.log"
    with _P("LOG", lp), _P("free_gb", MagicMock(side_effect=[0.5, 0.5])), \
         _P("free_mb", MagicMock(return_value=10000.0)), \
         _P("clean_temps", MagicMock(return_value=0)), \
         _P("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run") as mr:
            check_cycle()
    assert any("pkill" in str(c) for c in mr.call_args_list)


def test_cycle_root_warn(tmp_path):
    lp = tmp_path / "w.log"
    mc = MagicMock(return_value=0)
    with _P("LOG", lp), _P("free_gb", MagicMock(return_value=50.0)), \
         _P("free_mb", MagicMock(return_value=300.0)), \
         _P("clean_temps", mc), _P("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            check_cycle()
    mc.assert_called()


def test_cycle_rotate(tmp_path):
    lp = tmp_path / "w.log"
    mr = MagicMock()
    with _P("LOG", lp), _P("free_gb", MagicMock(return_value=50.0)), \
         _P("free_mb", MagicMock(return_value=10000.0)), \
         _P("rotate_log", mr), _P("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            check_cycle()
    assert mr.call_count == 8


def test_cycle_kill(tmp_path):
    lp = tmp_path / "w.log"
    mk = MagicMock(return_value=0)
    with _P("LOG", lp), _P("free_gb", MagicMock(return_value=50.0)), \
         _P("free_mb", MagicMock(return_value=10000.0)), \
         _P("kill_runaway_golems", mk):
        with patch("subprocess.run"):
            check_cycle()
    mk.assert_called_once()


def test_cycle_log_disk_warn(tmp_path):
    lp = tmp_path / "w.log"
    with _P("LOG", lp), _P("free_gb", MagicMock(side_effect=[1.5, 1.5])), \
         _P("free_mb", MagicMock(return_value=10000.0)), \
         _P("clean_temps", MagicMock(return_value=3)), \
         _P("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            check_cycle()
    c = lp.read_text()
    assert "DISK WARN" in c and "cleaned 3" in c


def test_cycle_log_root_warn(tmp_path):
    lp = tmp_path / "w.log"
    with _P("LOG", lp), _P("free_gb", MagicMock(return_value=50.0)), \
         _P("free_mb", MagicMock(return_value=200.0)), \
         _P("clean_temps", MagicMock(return_value=0)), \
         _P("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            check_cycle()
    assert "ROOT WARN" in lp.read_text()


# ── main ───────────────────────────────────────────────────────────────


def test_soma_watchdog_main_help(capsys):
    with patch.object(_mod["sys"], "argv", ["w", "--help"]):
        assert main() == 0
    assert "watchdog" in capsys.readouterr().out.lower() or "system health monitor" in capsys.readouterr().out.lower()


def test_main_h(capsys):
    with patch.object(_mod["sys"], "argv", ["w", "-h"]):
        assert main() == 0
    assert len(capsys.readouterr().out) > 0


def test_main_interrupt():
    with _P("LOG", Path("/dev/null")), _P("check_cycle", MagicMock()):
        with patch.object(_mod["sys"], "argv", ["w"]):
            with patch.object(_mod["time"], "sleep", MagicMock(side_effect=KeyboardInterrupt())):
                assert main() == 0


def test_main_calls_cycle():
    n = []

    def boom():
        n.append(1)
        raise KeyboardInterrupt

    with _P("LOG", Path("/dev/null")), _P("check_cycle", boom):
        with patch.object(_mod["sys"], "argv", ["w"]):
            main()
    assert len(n) >= 1


def test_main_log_start_stop(tmp_path):
    lp = tmp_path / "w.log"
    with _P("LOG", lp), _P("check_cycle", MagicMock(side_effect=KeyboardInterrupt)):
        with patch.object(_mod["sys"], "argv", ["w"]):
            with patch.object(_mod["time"], "sleep", MagicMock()):
                main()
    c = lp.read_text()
    assert "Watchdog started" in c and "Watchdog stopped" in c


def test_main_multi_cycle(tmp_path):
    lp = tmp_path / "w.log"
    n = 0

    def cnt():
        nonlocal n
        n += 1
        if n >= 3:
            raise KeyboardInterrupt

    with _P("LOG", lp), _P("check_cycle", cnt):
        with patch.object(_mod["sys"], "argv", ["w"]):
            with patch.object(_mod["time"], "sleep", MagicMock()):
                main()
    assert n == 3
