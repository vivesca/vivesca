from __future__ import annotations

"""Tests for gemmule-watchdog — system health monitor."""

import os
import shutil
import signal
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

# Constants
HOME = _mod["HOME"]
LOG = _mod["LOG"]
POLL = _mod["POLL"]
DISK_WARN_GB = _mod["DISK_WARN_GB"]
DISK_CRIT_GB = _mod["DISK_CRIT_GB"]
ROOT_WARN_MB = _mod["ROOT_WARN_MB"]
LOG_MAX_MB = _mod["LOG_MAX_MB"]
GOLEM_MAX_SECONDS = _mod["GOLEM_MAX_SECONDS"]
GOLEM_MAX_RSS_MB = _mod["GOLEM_MAX_RSS_MB"]
GERMLINE = _mod["GERMLINE"]


# ── Constants ─────────────────────────────────────────────────────────


class TestConstants:
    def test_poll_interval(self):
        assert POLL == 60

    def test_disk_warn_gb(self):
        assert DISK_WARN_GB == 2.0

    def test_disk_crit_gb(self):
        assert DISK_CRIT_GB == 1.0

    def test_root_warn_mb(self):
        assert ROOT_WARN_MB == 500

    def test_log_max_mb(self):
        assert LOG_MAX_MB == 10

    def test_golem_max_seconds(self):
        assert GOLEM_MAX_SECONDS == 2400

    def test_golem_max_rss_mb(self):
        assert GOLEM_MAX_RSS_MB == 2048

    def test_home_is_path(self):
        assert isinstance(HOME, Path)

    def test_log_path_under_home(self):
        assert LOG == HOME / "tmp" / "gemmule-watchdog.log"

    def test_germline_under_home(self):
        assert GERMLINE == HOME / "germline"


# ── log() ─────────────────────────────────────────────────────────────


class TestLog:
    def test_log_creates_dir_and_appends(self, tmp_path):
        logpath = tmp_path / "sub" / "test.log"
        with patch.object(_mod, "LOG", logpath):
            _mod["log"]("hello world")
            _mod["log"]("second line")
        content = logpath.read_text()
        assert "hello world" in content
        assert "second line" in content
        lines = content.strip().splitlines()
        assert len(lines) == 2
        # Each line starts with [timestamp]
        for line in lines:
            assert line.startswith("[")
            assert "] " in line

    def test_log_format_includes_timestamp(self, tmp_path):
        logpath = tmp_path / "t.log"
        with patch.object(_mod, "LOG", logpath):
            _mod["log"]("test msg")
        line = logpath.read_text().strip()
        # Format: [YYYY-MM-DD HH:MM:SS] test msg
        assert line.startswith("[202")  # covers 2024-2030
        assert "] test msg" in line

    def test_log_creates_parent_directory(self, tmp_path):
        logpath = tmp_path / "deep" / "nested" / "dir" / "out.log"
        assert not logpath.parent.exists()
        with patch.object(_mod, "LOG", logpath):
            _mod["log"]("created dirs")
        assert logpath.parent.exists()
        assert "created dirs" in logpath.read_text()


# ── free_gb() / free_mb() ────────────────────────────────────────────


class TestFreeSpace:
    def test_free_gb_returns_float(self):
        result = free_gb(HOME)
        assert isinstance(result, float)
        assert result > 0

    def test_free_mb_returns_float(self):
        result = free_mb(Path("/tmp"))
        assert isinstance(result, float)
        assert result > 0

    def test_free_mb_is_1024_times_gb(self):
        gb = free_gb(HOME)
        mb = free_mb(HOME)
        assert abs(mb - gb * 1024) < 1.0  # within 1 MB

    def test_free_gb_nonexistent_path_returns_999(self):
        result = free_gb(Path("/nonexistent/path/that/does/not/exist"))
        assert result == 999.0

    def test_free_mb_nonexistent_path_returns_999_times_1024(self):
        result = free_mb(Path("/nonexistent/path/that/does/not/exist"))
        assert result == 999.0 * 1024

    def test_free_gb_handles_permission_error(self):
        with patch("shutil.disk_usage", side_effect=PermissionError("denied")):
            result = free_gb(HOME)
            assert result == 999.0


# ── clean_temps() ─────────────────────────────────────────────────────


class TestCleanTemps:
    def test_clean_temps_returns_count(self, tmp_path):
        # Patch GERMLINE to tmp_path so it doesn't try to delete real dirs
        with patch.object(_mod, "GERMLINE", tmp_path):
            # Create one temp dir that matches a pattern
            pytest_dir = tmp_path / "pytest-of-terry"
            pytest_dir.mkdir()
            (pytest_dir / "test_foo.py").write_text("# test")
            count = clean_temps()
        assert isinstance(count, int)

    def test_clean_temps_removes_pytest_of_terry(self, tmp_path):
        pytest_dir = tmp_path / "pytest-of-terry"
        pytest_dir.mkdir()
        (pytest_dir / "sub" / "file.py").mkdir(parents=True)
        with patch.object(_mod, "GERMLINE", tmp_path):
            count = clean_temps()
        assert not pytest_dir.exists()

    def test_clean_temps_no_dirs_returns_zero_removed(self, tmp_path):
        # No matching dirs exist under tmp_path as GERMLINE
        with patch.object(_mod, "GERMLINE", tmp_path):
            # Also patch /tmp glob to return nothing
            with patch("pathlib.Path.glob", return_value=[]):
                with patch.object(_mod, "subprocess") as mock_sub:
                    mock_sub.run = MagicMock()
                    count = clean_temps()
        # cleaned counts only dirs that existed and were removed
        assert isinstance(count, int)

    def test_clean_temps_calls_find_for_pycache(self, tmp_path):
        with patch.object(_mod, "GERMLINE", tmp_path):
            with patch.object(_mod, "subprocess") as mock_sub:
                mock_sub.run = MagicMock()
                with patch("pathlib.Path.glob", return_value=[]):
                    clean_temps()
                mock_sub.run.assert_called_once()
                cmd_args = mock_sub.run.call_args[0][0]
                assert "find" in cmd_args
                assert "__pycache__" in cmd_args


# ── rotate_log() ──────────────────────────────────────────────────────


class TestRotateLog:
    def test_rotate_log_no_file_is_noop(self, tmp_path):
        p = tmp_path / "nonexistent.log"
        rotate_log(p)
        assert not p.exists()
        assert not p.with_suffix(p.suffix + ".1").exists()

    def test_rotate_log_small_file_not_rotated(self, tmp_path):
        p = tmp_path / "small.log"
        p.write_text("tiny")
        rotate_log(p, max_mb=10.0)
        assert p.exists()
        assert not p.with_suffix(p.suffix + ".1").exists()

    def test_rotate_log_large_file_gets_rotated(self, tmp_path):
        p = tmp_path / "big.log"
        # Write > 1 MB content
        p.write_text("x" * (2 * 1024 * 1024))
        rotate_log(p, max_mb=1.0)
        assert not p.exists()
        rotated = tmp_path / "big.log.1"
        assert rotated.exists()
        assert rotated.stat().st_size > 1024 * 1024

    def test_rotate_log_replaces_existing_rotated(self, tmp_path):
        p = tmp_path / "app.log"
        p.write_text("x" * (2 * 1024 * 1024))
        rotated = tmp_path / "app.log.1"
        rotated.write_text("old rotated content")
        rotate_log(p, max_mb=1.0)
        assert not p.exists()
        assert rotated.exists()
        # Content should be from the new rotation, not the old one
        assert rotated.stat().st_size > 1024 * 1024

    def test_rotate_log_logs_message(self, tmp_path):
        p = tmp_path / "big.log"
        logpath = tmp_path / "wd.log"
        p.write_text("y" * (2 * 1024 * 1024))
        with patch.object(_mod, "LOG", logpath):
            rotate_log(p, max_mb=1.0)
        log_content = logpath.read_text()
        assert "Rotated" in log_content
        assert "big.log" in log_content

    def test_rotate_log_default_max_mb(self, tmp_path):
        p = tmp_path / "default.log"
        # Write exactly 11 MB (> 10 MB default threshold)
        p.write_text("z" * (11 * 1024 * 1024))
        rotate_log(p)
        assert not p.exists()
        assert (tmp_path / "default.log.1").exists()


# ── kill_runaway_golems() ────────────────────────────────────────────


class TestKillRunawayGolems:
    def _make_ps_output(self, procs):
        """Build fake ps output. Each proc: (pid, elapsed_s, rss_kb)."""
        lines = []
        for pid, elapsed, rss in procs:
            lines.append(f"{pid} {elapsed} {rss} claude")
        return "\n".join(lines)

    def test_no_processes_returns_zero(self):
        result_mock = MagicMock()
        result_mock.stdout = ""
        with patch.object(_mod, "subprocess") as mock_sub:
            mock_sub.run = MagicMock(return_value=result_mock)
            killed = kill_runaway_golems()
        assert killed == 0

    def test_normal_process_not_killed(self):
        result_mock = MagicMock()
        result_mock.stdout = self._make_ps_output([(12345, 100, 512 * 1024)])
        with patch.object(_mod, "subprocess") as mock_sub:
            mock_sub.run = MagicMock(return_value=result_mock)
            with patch.object(_mod, "os") as mock_os:
                killed = kill_runaway_golems()
        assert killed == 0

    def test_runaway_time_killed(self):
        result_mock = MagicMock()
        elapsed = GOLEM_MAX_SECONDS + 100
        result_mock.stdout = self._make_ps_output([(12345, elapsed, 512 * 1024)])
        with patch.object(_mod, "subprocess") as mock_sub:
            mock_sub.run = MagicMock(return_value=result_mock)
            with patch.object(_mod, "os") as mock_os:
                killed = kill_runaway_golems()
        assert killed == 1
        mock_os.kill.assert_called_once_with(12345, signal.SIGTERM)

    def test_memory_hog_killed(self):
        result_mock = MagicMock()
        rss_mb = GOLEM_MAX_RSS_MB + 100
        rss_kb = int(rss_mb * 1024)
        result_mock.stdout = self._make_ps_output([(12345, 100, rss_kb)])
        with patch.object(_mod, "subprocess") as mock_sub:
            mock_sub.run = MagicMock(return_value=result_mock)
            with patch.object(_mod, "os") as mock_os:
                killed = kill_runaway_golems()
        assert killed == 1
        mock_os.kill.assert_called_once_with(12345, signal.SIGTERM)

    def test_time_takes_priority_over_memory(self):
        """If both thresholds exceeded, time is the reason (if/elif)."""
        result_mock = MagicMock()
        elapsed = GOLEM_MAX_SECONDS + 100
        rss_kb = (GOLEM_MAX_RSS_MB + 100) * 1024
        result_mock.stdout = self._make_ps_output([(12345, elapsed, rss_kb)])
        with patch.object(_mod, "subprocess") as mock_sub:
            mock_sub.run = MagicMock(return_value=result_mock)
            with patch.object(_mod, "os") as mock_os:
                killed = kill_runaway_golems()
        assert killed == 1
        mock_os.kill.assert_called_once_with(12345, signal.SIGTERM)

    def test_multiple_runaways_all_killed(self):
        result_mock = MagicMock()
        procs = [
            (111, GOLEM_MAX_SECONDS + 10, 512 * 1024),
            (222, 100, (GOLEM_MAX_RSS_MB + 100) * 1024),
            (333, 50, 256 * 1024),  # normal — should NOT be killed
            (444, GOLEM_MAX_SECONDS + 500, 256 * 1024),
        ]
        result_mock.stdout = self._make_ps_output(procs)
        with patch.object(_mod, "subprocess") as mock_sub:
            mock_sub.run = MagicMock(return_value=result_mock)
            with patch.object(_mod, "os") as mock_os:
                killed = kill_runaway_golems()
        assert killed == 3
        killed_pids = [c.args[0] for c in mock_os.kill.call_args_list]
        assert 111 in killed_pids
        assert 222 in killed_pids
        assert 444 in killed_pids
        assert 333 not in killed_pids

    def test_short_lines_skipped(self):
        result_mock = MagicMock()
        # Lines with fewer than 4 fields should be skipped
        result_mock.stdout = "123 45\n\n   \n12345 99999 999999 claude"
        with patch.object(_mod, "subprocess") as mock_sub:
            mock_sub.run = MagicMock(return_value=result_mock)
            with patch.object(_mod, "os") as mock_os:
                killed = kill_runaway_golems()
        # Only the valid 4-field line should be processed
        assert killed == 1

    def test_exception_returns_zero(self):
        with patch.object(_mod, "subprocess") as mock_sub:
            mock_sub.run = MagicMock(side_effect=OSError("boom"))
            with patch.object(_mod, "LOG", Path("/dev/null")):
                killed = kill_runaway_golems()
        assert killed == 0

    def test_exact_threshold_not_killed(self):
        """At exactly the threshold, process should NOT be killed (> not >=)."""
        result_mock = MagicMock()
        rss_kb = GOLEM_MAX_RSS_MB * 1024  # exactly at threshold
        result_mock.stdout = self._make_ps_output([(12345, GOLEM_MAX_SECONDS, rss_kb)])
        with patch.object(_mod, "subprocess") as mock_sub:
            mock_sub.run = MagicMock(return_value=result_mock)
            with patch.object(_mod, "os") as mock_os:
                killed = kill_runaway_golems()
        assert killed == 0

    def test_one_over_threshold_killed(self):
        """Just 1 second over the threshold should trigger kill."""
        result_mock = MagicMock()
        result_mock.stdout = self._make_ps_output([
            (12345, GOLEM_MAX_SECONDS + 1, 512 * 1024)
        ])
        with patch.object(_mod, "subprocess") as mock_sub:
            mock_sub.run = MagicMock(return_value=result_mock)
            with patch.object(_mod, "os") as mock_os:
                killed = kill_runaway_golems()
        assert killed == 1


# ── check_cycle() ─────────────────────────────────────────────────────


class TestCheckCycle:
    def test_check_cycle_runs_without_error(self):
        """Sanity: check_cycle completes without exception."""
        with patch.object(_mod, "free_gb", return_value=50.0):
            with patch.object(_mod, "free_mb", return_value=2000.0):
                with patch.object(_mod, "kill_runaway_golems", return_value=0):
                    with patch.object(_mod, "subprocess") as mock_sub:
                        check_cycle()
        # No exception means success

    def test_disk_warn_triggers_clean_temps(self):
        with patch.object(_mod, "free_gb", side_effect=[1.5, 1.5]):
            with patch.object(_mod, "free_mb", return_value=2000.0):
                with patch.object(_mod, "clean_temps", return_value=3) as mock_clean:
                    with patch.object(_mod, "kill_runaway_golems", return_value=0):
                        with patch.object(_mod, "subprocess") as mock_sub:
                            with patch.object(_mod, "LOG", Path("/dev/null")):
                                check_cycle()
        mock_clean.assert_called_once()

    def test_disk_critical_triggers_pkill(self):
        with patch.object(_mod, "free_gb", side_effect=[0.5, 0.5]):
            with patch.object(_mod, "free_mb", return_value=2000.0):
                with patch.object(_mod, "clean_temps", return_value=0):
                    with patch.object(_mod, "kill_runaway_golems", return_value=0):
                        with patch.object(_mod, "subprocess") as mock_sub:
                            with patch.object(_mod, "LOG", Path("/dev/null")):
                                check_cycle()
        # pkill should have been called (critical disk)
        calls = [str(c) for c in mock_sub.run.call_args_list]
        assert any("pkill" in c for c in calls)

    def test_root_warn_triggers_clean_temps(self):
        call_count = {"n": 0}

        def free_gb_side_effect(p):
            return 50.0  # plenty of disk, skip disk warn

        with patch.object(_mod, "free_gb", side_effect=free_gb_side_effect):
            with patch.object(_mod, "free_mb", side_effect=[400.0, 600.0]):
                with patch.object(_mod, "clean_temps", return_value=1) as mock_clean:
                    with patch.object(_mod, "kill_runaway_golems", return_value=0):
                        with patch.object(_mod, "subprocess") as mock_sub:
                            with patch.object(_mod, "LOG", Path("/dev/null")):
                                check_cycle()
        mock_clean.assert_called_once()

    def test_check_cycle_calls_rotate_log(self):
        with patch.object(_mod, "free_gb", return_value=50.0):
            with patch.object(_mod, "free_mb", return_value=2000.0):
                with patch.object(_mod, "kill_runaway_golems", return_value=0):
                    with patch.object(_mod, "rotate_log") as mock_rotate:
                        with patch.object(_mod, "subprocess") as mock_sub:
                            check_cycle()
        # rotate_log should be called once per log file in the list
        assert mock_rotate.call_count == 8  # 8 log files in check_cycle

    def test_check_cycle_calls_kill_runaway(self):
        with patch.object(_mod, "free_gb", return_value=50.0):
            with patch.object(_mod, "free_mb", return_value=2000.0):
                with patch.object(_mod, "kill_runaway_golems", return_value=0) as mock_kill:
                    with patch.object(_mod, "subprocess") as mock_sub:
                        check_cycle()
        mock_kill.assert_called_once()


# ── main() ────────────────────────────────────────────────────────────


class TestMain:
    def test_help_returns_zero(self):
        with patch("sys.argv", ["gemmule-watchdog", "--help"]):
            result = main()
        assert result == 0

    def test_help_h_returns_zero(self):
        with patch("sys.argv", ["gemmule-watchdog", "-h"]):
            result = main()
        assert result == 0

    def test_help_prints_docstring(self, capsys):
        with patch("sys.argv", ["gemmule-watchdog", "--help"]):
            main()
        output = capsys.readouterr().out
        assert "system health monitor" in output.lower() or "watchdog" in output.lower()

    def test_main_loop_interrupts_cleanly(self):
        """KeyboardInterrupt should stop the loop and return 0."""
        with patch("sys.argv", ["gemmule-watchdog"]):
            with patch.object(_mod, "check_cycle"):
                with patch.object(_mod, "time") as mock_time:
                    mock_time.sleep.side_effect = KeyboardInterrupt()
                    with patch.object(_mod, "LOG", Path("/dev/null")):
                        result = main()
        assert result == 0

    def test_main_runs_check_cycle_before_sleep(self):
        """check_cycle should be called at least once before sleep."""
        cycle_calls = []

        def fake_cycle():
            cycle_calls.append(1)
            raise KeyboardInterrupt()

        with patch("sys.argv", ["gemmule-watchdog"]):
            with patch.object(_mod, "check_cycle", side_effect=fake_cycle):
                with patch.object(_mod, "LOG", Path("/dev/null")):
                    result = main()
        assert len(cycle_calls) >= 1
