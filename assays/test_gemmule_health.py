#!/usr/bin/env python3
"""Tests for effectors/gemmule-health — gemmule system health monitor."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest import mock

import pytest

EFFECTOR_PATH = Path(__file__).resolve().parents[1] / "effectors" / "gemmule-health"


@pytest.fixture
def gh(tmp_path):
    """Load gemmule-health effector into an isolated namespace."""
    source = EFFECTOR_PATH.read_text()
    ns = {"__name__": "test_gemmule_health", "__file__": str(EFFECTOR_PATH)}
    exec(source, ns)
    # Redirect all paths to tmp for isolation
    ns["HOME"] = tmp_path
    ns["GERMLINE"] = tmp_path / "germline"
    ns["SESSION_DIR"] = tmp_path / "sessions"
    ns["VIVESCA_DIR"] = tmp_path / "vivesca"
    ns["PIDFILE"] = tmp_path / "golem-daemon.pid"
    # Ensure dirs exist
    ns["GERMLINE"].mkdir(parents=True, exist_ok=True)
    ns["SESSION_DIR"].mkdir(parents=True, exist_ok=True)
    ns["VIVESCA_DIR"].mkdir(parents=True, exist_ok=True)
    return ns


# ── Script structure ─────────────────────────────────────────────────────────


class TestScriptStructure:
    def test_exists(self):
        assert EFFECTOR_PATH.exists()

    def test_shebang(self):
        assert EFFECTOR_PATH.read_text().splitlines()[0].startswith("#!")


# ── Data classes ─────────────────────────────────────────────────────────────


class TestCheck:
    def test_defaults(self, gh):
        c = gh["Check"](name="x", status="ok", value="y")
        assert c.name == "x"
        assert c.status == "ok"
        assert c.value == "y"
        assert c.detail == ""
        assert c.fixed is False

    def test_with_detail(self, gh):
        c = gh["Check"](name="d", status="warn", value="85%", detail="15GB free")
        assert c.detail == "15GB free"
        assert c.status == "warn"


class TestHealthReport:
    def test_starts_ok(self, gh):
        r = gh["HealthReport"]()
        assert r.overall == "ok"
        assert r.checks == []
        assert r.fixes_applied == []

    def test_add_warn(self, gh):
        r = gh["HealthReport"]()
        r.add(gh["Check"](name="a", status="warn", value="w"))
        assert r.overall == "warn"

    def test_crit_trumps_warn(self, gh):
        r = gh["HealthReport"]()
        r.add(gh["Check"](name="a", status="warn", value="w"))
        r.add(gh["Check"](name="b", status="crit", value="c"))
        assert r.overall == "crit"

    def test_warn_does_not_downgrade_crit(self, gh):
        r = gh["HealthReport"]()
        r.add(gh["Check"](name="a", status="crit", value="c"))
        r.add(gh["Check"](name="b", status="warn", value="w"))
        assert r.overall == "crit"

    def test_ok_does_not_downgrade_warn(self, gh):
        r = gh["HealthReport"]()
        r.add(gh["Check"](name="a", status="warn", value="w"))
        r.add(gh["Check"](name="b", status="ok", value="o"))
        assert r.overall == "warn"


# ── check_disk ───────────────────────────────────────────────────────────────


class TestCheckDisk:
    def _usage(self, used, total):
        return mock.Mock(used=used, total=total, free=total - used)

    def test_ok(self, gh):
        with mock.patch("shutil.disk_usage", return_value=self._usage(40, 100)):
            c = gh["check_disk"]()
        assert c.status == "ok"
        assert c.name == "disk"
        assert "40%" in c.value

    def test_warn_at_threshold(self, gh):
        with mock.patch("shutil.disk_usage", return_value=self._usage(80, 100)):
            c = gh["check_disk"]()
        assert c.status == "warn"

    def test_crit_at_threshold(self, gh):
        with mock.patch("shutil.disk_usage", return_value=self._usage(90, 100)):
            c = gh["check_disk"]()
        assert c.status == "crit"

    def test_error_on_exception(self, gh):
        with mock.patch("shutil.disk_usage", side_effect=OSError("no disk")):
            c = gh["check_disk"]()
        assert c.status == "error"
        assert "no disk" in c.detail


# ── check_memory ─────────────────────────────────────────────────────────────


class TestCheckMemory:
    def _meminfo(self, total_kb, avail_kb):
        return f"MemTotal: {total_kb} kB\nMemAvailable: {avail_kb} kB\n"

    def test_ok(self, gh):
        data = self._meminfo(8192000, 4096000)
        with mock.patch("builtins.open", mock.mock_open(read_data=data)):
            c = gh["check_memory"]()
        assert c.status == "ok"
        assert c.name == "memory"
        assert "%" in c.value

    def test_warn_high_usage(self, gh):
        data = self._meminfo(8192000, 819200)  # ~90% used
        with mock.patch("builtins.open", mock.mock_open(read_data=data)):
            c = gh["check_memory"]()
        assert c.status == "warn"

    def test_error(self, gh):
        with mock.patch("builtins.open", side_effect=FileNotFoundError()):
            c = gh["check_memory"]()
        assert c.status == "error"


# ── check_daemon ─────────────────────────────────────────────────────────────


class TestCheckDaemon:
    def test_no_pidfile(self, gh):
        gh["PIDFILE"] = gh["HOME"] / "no-such-file.pid"
        c = gh["check_daemon"]()
        assert c.status == "warn"
        assert c.value == "stopped"
        assert "PID file not found" in c.detail

    def test_running(self, gh, tmp_path):
        pf = tmp_path / "d.pid"
        pf.write_text(str(os.getpid()))
        gh["PIDFILE"] = pf
        c = gh["check_daemon"]()
        assert c.status == "ok"
        assert c.value == "running"

    def test_stale_pid(self, gh, tmp_path):
        pf = tmp_path / "d.pid"
        pf.write_text("999999999")
        gh["PIDFILE"] = pf
        c = gh["check_daemon"]()
        assert c.status == "warn"
        assert c.value == "stale"

    def test_permission_error_means_alive(self, gh, tmp_path):
        pf = tmp_path / "d.pid"
        pf.write_text(str(os.getpid()))
        gh["PIDFILE"] = pf
        with mock.patch("os.kill", side_effect=PermissionError):
            c = gh["check_daemon"]()
        assert c.status == "ok"
        assert c.value == "running"


# ── check_git ────────────────────────────────────────────────────────────────


class TestCheckGit:
    def _runs(self, fsck_rc=0, fsck_err="", status_out=""):
        return [
            mock.Mock(returncode=fsck_rc, stderr=fsck_err, stdout=""),
            mock.Mock(returncode=0, stdout=status_out, stderr=""),
        ]

    def test_clean(self, gh):
        with mock.patch("subprocess.run", side_effect=self._runs()):
            c = gh["check_git"]()
        assert c.status == "ok"
        assert c.value == "clean"

    def test_dirty_few(self, gh):
        dirty = "M a.py\n?? b.py\n"
        with mock.patch("subprocess.run", side_effect=self._runs(status_out=dirty)):
            c = gh["check_git"]()
        assert c.status == "ok"
        assert "2 dirty" in c.value

    def test_dirty_many(self, gh):
        dirty = "\n".join(f"M f{i}.py" for i in range(55))
        with mock.patch("subprocess.run", side_effect=self._runs(status_out=dirty)):
            c = gh["check_git"]()
        assert c.status == "warn"
        assert "55 dirty" in c.value

    def test_corrupt(self, gh):
        with mock.patch(
            "subprocess.run",
            side_effect=self._runs(fsck_rc=1, fsck_err="fatal: bad object HEAD"),
        ):
            c = gh["check_git"]()
        assert c.status == "crit"
        assert c.value == "corrupt"

    def test_error(self, gh):
        with mock.patch("subprocess.run", side_effect=Exception("git not found")):
            c = gh["check_git"]()
        assert c.status == "error"


# ── check_venv ───────────────────────────────────────────────────────────────


class TestCheckVenv:
    def test_missing_venv(self, gh, tmp_path):
        g = tmp_path / "germline"
        g.mkdir(parents=True, exist_ok=True)
        venv = g / ".venv"
        if venv.exists():
            import shutil
            shutil.rmtree(venv)
        c = gh["check_venv"]()
        assert c.status == "crit"
        assert c.value == "missing"

    def test_no_python_binary(self, gh, tmp_path):
        venv = tmp_path / "germline" / ".venv"
        venv.mkdir(parents=True, exist_ok=True)
        c = gh["check_venv"]()
        assert c.status == "crit"
        assert c.value == "broken"

    def test_incomplete(self, gh, tmp_path):
        venv = tmp_path / "germline" / ".venv" / "bin"
        venv.mkdir(parents=True, exist_ok=True)
        (venv / "python").touch()
        with mock.patch(
            "subprocess.run", return_value=mock.Mock(returncode=1, stderr="ModuleNotFoundError")
        ):
            c = gh["check_venv"]()
        assert c.status == "warn"
        assert c.value == "incomplete"

    def test_healthy(self, gh, tmp_path):
        venv = tmp_path / "germline" / ".venv" / "bin"
        venv.mkdir(parents=True, exist_ok=True)
        (venv / "python").touch()
        with mock.patch(
            "subprocess.run", return_value=mock.Mock(returncode=0, stdout="ok\n")
        ):
            c = gh["check_venv"]()
        assert c.status == "ok"
        assert c.value == "healthy"


# ── check_tests ──────────────────────────────────────────────────────────────


class TestCheckTests:
    def test_ok(self, gh):
        with mock.patch(
            "subprocess.run",
            return_value=mock.Mock(returncode=0, stdout="150 tests collected\n", stderr=""),
        ):
            c = gh["check_tests"]()
        assert c.status == "ok"
        assert "150 tests collected" in c.value

    def test_timeout(self, gh):
        with mock.patch(
            "subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="pytest", timeout=60)
        ):
            c = gh["check_tests"]()
        assert c.status == "warn"
        assert c.value == "timeout"

    def test_error(self, gh):
        with mock.patch("subprocess.run", side_effect=Exception("boom")):
            c = gh["check_tests"]()
        assert c.status == "error"


# ── check_stale_files ────────────────────────────────────────────────────────


class TestCheckStaleFiles:
    def test_clean(self, gh):
        c = gh["check_stale_files"]()
        assert c.status == "ok"
        assert c.value == "clean"

    def test_excess_sessions(self, gh, tmp_path):
        sdir = tmp_path / "sessions"
        sdir.mkdir(parents=True, exist_ok=True)
        gh["SESSION_KEEP"] = 5
        for i in range(12):
            (sdir / f"s{i}.jsonl").write_text("{}")
        c = gh["check_stale_files"]()
        assert c.status == "warn"
        assert "excess sessions" in c.detail

    def test_stale_lock(self, gh, tmp_path):
        lock = tmp_path / "test.lock"
        lock.write_text("")
        old = time.time() - 7200
        os.utime(lock, (old, old))
        c = gh["check_stale_files"]()
        assert c.status == "warn"
        assert "stale lock" in c.detail

    def test_large_log(self, gh, tmp_path):
        vdir = tmp_path / "vivesca"
        vdir.mkdir(parents=True, exist_ok=True)
        gh["LOG_MAX_MB"] = 0.0  # anything is "large"
        (vdir / "app.log").write_text("hello")
        c = gh["check_stale_files"]()
        assert c.status == "warn"
        assert "app.log" in c.detail


# ── fix_disk ─────────────────────────────────────────────────────────────────


class TestFixDisk:
    def test_prunes_old_sessions(self, gh, tmp_path):
        sdir = tmp_path / "sessions"
        sdir.mkdir(parents=True, exist_ok=True)
        gh["SESSION_KEEP"] = 5
        for i in range(12):
            (sdir / f"s{i}.jsonl").write_text("{}")
        report = gh["HealthReport"]()
        with mock.patch("subprocess.run"):
            gh["fix_disk"](report)
        remaining = list(sdir.glob("*.jsonl"))
        assert len(remaining) <= 5
        assert any("pruned" in f for f in report.fixes_applied)

    def test_truncates_large_log(self, gh, tmp_path):
        vdir = tmp_path / "vivesca"
        vdir.mkdir(parents=True, exist_ok=True)
        big = vdir / "app.log"
        big.write_text("line\n" * 50000)
        gh["LOG_MAX_MB"] = 0.0
        report = gh["HealthReport"]()
        with mock.patch("subprocess.run"):
            gh["fix_disk"](report)
        assert big.stat().st_size < 50000
        assert any("truncated" in f for f in report.fixes_applied)

    def test_truncates_large_jsonl(self, gh, tmp_path):
        vdir = tmp_path / "vivesca"
        vdir.mkdir(parents=True, exist_ok=True)
        big = vdir / "events.jsonl"
        big.write_text("line\n" * 10)  # small real file
        # Mock stat so the file appears > 20MB (inline threshold)
        original_stat = Path.stat

        def fake_stat(self, *, follow_symlinks=True):
            if "events.jsonl" in str(self):
                return mock.Mock(st_size=21 * 1024 * 1024, st_mode=0o100644)
            return original_stat(self, follow_symlinks=follow_symlinks)

        report = gh["HealthReport"]()
        with mock.patch.object(Path, "stat", fake_stat):
            with mock.patch("subprocess.run"):
                gh["fix_disk"](report)
        assert any("truncated" in f for f in report.fixes_applied)


# ── fix_stale ────────────────────────────────────────────────────────────────


class TestFixStale:
    def test_removes_stale_lock(self, gh, tmp_path):
        lock = tmp_path / "old.lock"
        lock.write_text("")
        old = time.time() - 7200
        os.utime(lock, (old, old))
        report = gh["HealthReport"]()
        gh["fix_stale"](report)
        assert not lock.exists()
        assert any("stale lock" in f for f in report.fixes_applied)

    def test_keeps_recent_lock(self, gh, tmp_path):
        lock = tmp_path / "fresh.lock"
        lock.write_text("")
        report = gh["HealthReport"]()
        gh["fix_stale"](report)
        assert lock.exists()


# ── fix_daemon ───────────────────────────────────────────────────────────────


class TestFixDaemon:
    def test_removes_stale_pidfile(self, gh, tmp_path):
        pf = tmp_path / "d.pid"
        pf.write_text("999999999")
        gh["PIDFILE"] = pf
        report = gh["HealthReport"]()
        gh["fix_daemon"](report)
        assert not pf.exists()
        assert any("stale" in f for f in report.fixes_applied)

    def test_keeps_live_pidfile(self, gh, tmp_path):
        pf = tmp_path / "d.pid"
        pf.write_text(str(os.getpid()))
        gh["PIDFILE"] = pf
        report = gh["HealthReport"]()
        gh["fix_daemon"](report)
        assert pf.exists()

    def test_no_pidfile_no_error(self, gh, tmp_path):
        gh["PIDFILE"] = tmp_path / "nope.pid"
        report = gh["HealthReport"]()
        gh["fix_daemon"](report)  # should not raise
        assert report.fixes_applied == []


# ── run_health ───────────────────────────────────────────────────────────────


class TestRunHealth:
    def test_runs_all_checks(self, gh):
        mock_run = mock.Mock(return_value=mock.Mock(returncode=0, stdout="", stderr=""))
        with mock.patch("subprocess.run", mock_run):
            with mock.patch("shutil.disk_usage", return_value=mock.Mock(used=40, total=100, free=60)):
                with mock.patch("builtins.open", mock.mock_open(read_data="MemTotal: 8000000 kB\nMemAvailable: 4000000 kB\n")):
                    report = gh["run_health"](fix=False)
        names = [c.name for c in report.checks]
        assert "disk" in names
        assert "memory" in names
        assert "daemon" in names
        assert "git" in names
        assert "venv" in names
        assert "stale" in names
        assert "tests" in names

    def test_daemon_mode_skips_tests(self, gh):
        mock_run = mock.Mock(return_value=mock.Mock(returncode=0, stdout="", stderr=""))
        with mock.patch("subprocess.run", mock_run):
            with mock.patch("shutil.disk_usage", return_value=mock.Mock(used=40, total=100, free=60)):
                with mock.patch("builtins.open", mock.mock_open(read_data="MemTotal: 8000000 kB\nMemAvailable: 4000000 kB\n")):
                    report = gh["run_health"](daemon_mode=True)
        names = [c.name for c in report.checks]
        assert "tests" not in names

    def test_fix_mode_applies_disk_fix(self, gh, tmp_path):
        mock_run = mock.Mock(return_value=mock.Mock(returncode=0, stdout="", stderr=""))
        with mock.patch("subprocess.run", mock_run):
            with mock.patch("shutil.disk_usage", return_value=mock.Mock(used=92, total=100, free=8)):
                with mock.patch("builtins.open", mock.mock_open(read_data="MemTotal: 8000000 kB\nMemAvailable: 4000000 kB\n")):
                    report = gh["run_health"](fix=True)
        disk = next(c for c in report.checks if c.name == "disk")
        assert disk.fixed is True


# ── print_report ─────────────────────────────────────────────────────────────


class TestPrintReport:
    def test_json_output(self, gh, capsys):
        report = gh["HealthReport"](timestamp="2025-01-01")
        report.add(gh["Check"](name="disk", status="ok", value="50%"))
        gh["print_report"](report, as_json=True)
        data = json.loads(capsys.readouterr().out)
        assert data["overall"] == "ok"
        assert len(data["checks"]) == 1
        assert data["checks"][0]["name"] == "disk"

    def test_compact_output(self, gh, capsys):
        report = gh["HealthReport"](timestamp="2025-01-01")
        report.add(gh["Check"](name="disk", status="ok", value="50%"))
        report.fixes_applied.append("pruned cache")
        gh["print_report"](report, compact=True)
        out = capsys.readouterr().out
        assert "[OK]" in out
        assert "disk=50%" in out
        assert "pruned cache" in out

    def test_human_output(self, gh, capsys):
        report = gh["HealthReport"](timestamp="2025-01-01")
        report.add(gh["Check"](name="disk", status="ok", value="50%", detail="10GB free"))
        gh["print_report"](report)
        out = capsys.readouterr().out
        assert "Health Report" in out
        assert "[+]" in out
        assert "10GB free" in out

    def test_human_warn_icon(self, gh, capsys):
        report = gh["HealthReport"](timestamp="2025-01-01")
        report.add(gh["Check"](name="disk", status="warn", value="85%"))
        gh["print_report"](report)
        out = capsys.readouterr().out
        assert "[!]" in out

    def test_human_crit_icon(self, gh, capsys):
        report = gh["HealthReport"](timestamp="2025-01-01")
        report.add(gh["Check"](name="disk", status="crit", value="95%"))
        gh["print_report"](report)
        out = capsys.readouterr().out
        assert "[X]" in out

    def test_human_fixed_marker(self, gh, capsys):
        report = gh["HealthReport"](timestamp="2025-01-01")
        report.add(gh["Check"](name="disk", status="ok", value="50%", fixed=True))
        gh["print_report"](report)
        out = capsys.readouterr().out
        assert "FIXED" in out


# ── main ─────────────────────────────────────────────────────────────────────


class TestMain:
    def test_exit_zero_on_ok(self, gh):
        report = gh["HealthReport"]()
        gh["run_health"] = mock.Mock(return_value=report)
        with pytest.raises(SystemExit) as exc:
            gh["main"]()
        assert exc.value.code == 0

    def test_exit_one_on_warn(self, gh):
        report = gh["HealthReport"]()
        report.overall = "warn"
        gh["run_health"] = mock.Mock(return_value=report)
        with pytest.raises(SystemExit) as exc:
            gh["main"]()
        assert exc.value.code == 1

    def test_exit_two_on_crit(self, gh):
        report = gh["HealthReport"]()
        report.overall = "crit"
        gh["run_health"] = mock.Mock(return_value=report)
        with pytest.raises(SystemExit) as exc:
            gh["main"]()
        assert exc.value.code == 2

    def test_json_flag(self, gh, capsys):
        report = gh["HealthReport"](timestamp="2025-01-01")
        report.add(gh["Check"](name="disk", status="ok", value="50%"))
        gh["run_health"] = mock.Mock(return_value=report)
        with mock.patch.object(sys, "argv", ["gemmule-health", "--json"]):
            with pytest.raises(SystemExit):
                gh["main"]()
        data = json.loads(capsys.readouterr().out)
        assert data["overall"] == "ok"

    def test_daemon_flag_compact(self, gh, capsys):
        report = gh["HealthReport"]()
        gh["run_health"] = mock.Mock(return_value=report)
        with mock.patch.object(sys, "argv", ["gemmule-health", "--daemon"]):
            with pytest.raises(SystemExit):
                gh["main"]()
        out = capsys.readouterr().out
        assert "[OK]" in out

    def test_fix_flag_passed(self, gh):
        report = gh["HealthReport"]()
        gh["run_health"] = mock.Mock(return_value=report)
        with mock.patch.object(sys, "argv", ["gemmule-health", "--fix"]):
            with pytest.raises(SystemExit):
                gh["main"]()
        gh["run_health"].assert_called_once()
        call_kwargs = gh["run_health"].call_args
        assert call_kwargs.kwargs.get("fix") is True or call_kwargs[0][0] if call_kwargs[0] else call_kwargs.kwargs.get("fix") is True

    def test_default_no_fix_no_json(self, gh):
        report = gh["HealthReport"]()
        gh["run_health"] = mock.Mock(return_value=report)
        with mock.patch.object(sys, "argv", ["gemmule-health"]):
            with pytest.raises(SystemExit):
                gh["main"]()
        kw = gh["run_health"].call_args.kwargs
        assert kw["fix"] is False
        assert kw["as_json"] is False
        assert kw["daemon_mode"] is False


# ── HealthReport.add extended ─────────────────────────────────────────────────


class TestHealthReportExtended:
    def test_add_error_status(self, gh):
        r = gh["HealthReport"]()
        r.add(gh["Check"](name="x", status="error", value="?"))
        assert r.overall == "ok"  # error does not change overall

    def test_add_multiple_same_crit(self, gh):
        r = gh["HealthReport"]()
        r.add(gh["Check"](name="a", status="crit", value="c1"))
        r.add(gh["Check"](name="b", status="crit", value="c2"))
        assert r.overall == "crit"
        assert len(r.checks) == 2

    def test_add_error_after_warn(self, gh):
        r = gh["HealthReport"]()
        r.add(gh["Check"](name="a", status="warn", value="w"))
        r.add(gh["Check"](name="b", status="error", value="?"))
        assert r.overall == "warn"  # error doesn't downgrade warn


# ── check_disk extended ───────────────────────────────────────────────────────


class TestCheckDiskExtended:
    def _usage(self, used, total):
        return mock.Mock(used=used, total=total, free=total - used)

    def test_value_format(self, gh):
        with mock.patch("shutil.disk_usage", return_value=self._usage(42, 100)):
            c = gh["check_disk"]()
        assert c.value.endswith("%")
        assert "42%" in c.value

    def test_detail_format(self, gh):
        with mock.patch("shutil.disk_usage", return_value=self._usage(30, 100)):
            c = gh["check_disk"]()
        assert "free" in c.detail
        assert "total" in c.detail

    def test_just_below_warn(self, gh):
        with mock.patch("shutil.disk_usage", return_value=self._usage(79, 100)):
            c = gh["check_disk"]()
        assert c.status == "ok"

    def test_just_below_crit(self, gh):
        with mock.patch("shutil.disk_usage", return_value=self._usage(89, 100)):
            c = gh["check_disk"]()
        assert c.status == "warn"

    def test_very_high_usage(self, gh):
        with mock.patch("shutil.disk_usage", return_value=self._usage(99, 100)):
            c = gh["check_disk"]()
        assert c.status == "crit"


# ── check_memory extended ─────────────────────────────────────────────────────


class TestCheckMemoryExtended:
    def _meminfo(self, total_kb, avail_kb):
        return f"MemTotal: {total_kb} kB\nMemAvailable: {avail_kb} kB\n"

    def test_just_below_warn(self, gh):
        total = 8192000
        avail = int(total * 0.20)  # 80% used, well below 85% warn
        data = self._meminfo(total, avail)
        with mock.patch("builtins.open", mock.mock_open(read_data=data)):
            c = gh["check_memory"]()
        assert c.status == "ok"

    def test_exact_warn_boundary(self, gh):
        # 85% used = warn
        total = 8192000
        avail = int(total * 0.15)  # 15% available = 85% used
        data = self._meminfo(total, avail)
        with mock.patch("builtins.open", mock.mock_open(read_data=data)):
            c = gh["check_memory"]()
        assert c.status == "warn"

    def test_detail_format(self, gh):
        data = self._meminfo(8192000, 4096000)
        with mock.patch("builtins.open", mock.mock_open(read_data=data)):
            c = gh["check_memory"]()
        assert "MB available" in c.detail
        assert "MB total" in c.detail

    def test_value_format_pct(self, gh):
        data = self._meminfo(8192000, 4096000)
        with mock.patch("builtins.open", mock.mock_open(read_data=data)):
            c = gh["check_memory"]()
        assert "%" in c.value


# ── check_daemon extended ─────────────────────────────────────────────────────


class TestCheckDaemonExtended:
    def test_bad_pid_content(self, gh, tmp_path):
        pf = tmp_path / "d.pid"
        pf.write_text("not-a-number")
        gh["PIDFILE"] = pf
        c = gh["check_daemon"]()
        assert c.status == "error"

    def test_empty_pidfile(self, gh, tmp_path):
        pf = tmp_path / "d.pid"
        pf.write_text("")
        gh["PIDFILE"] = pf
        c = gh["check_daemon"]()
        assert c.status == "error"

    def test_general_exception(self, gh, tmp_path):
        pf = tmp_path / "d.pid"
        pf.write_text(str(os.getpid()))
        gh["PIDFILE"] = pf
        with mock.patch("pathlib.Path.read_text", side_effect=RuntimeError("unexpected")):
            c = gh["check_daemon"]()
        assert c.status == "error"


# ── check_git extended ────────────────────────────────────────────────────────


class TestCheckGitExtended:
    def _runs(self, fsck_rc=0, fsck_err="", status_out=""):
        return [
            mock.Mock(returncode=fsck_rc, stderr=fsck_err, stdout=""),
            mock.Mock(returncode=0, stdout=status_out, stderr=""),
        ]

    def test_exactly_50_dirty_is_ok(self, gh):
        dirty = "\n".join(f"M f{i}.py" for i in range(50))
        with mock.patch("subprocess.run", side_effect=self._runs(status_out=dirty)):
            c = gh["check_git"]()
        assert c.status == "ok"
        assert "50 dirty" in c.value

    def test_exactly_51_dirty_is_warn(self, gh):
        dirty = "\n".join(f"M f{i}.py" for i in range(51))
        with mock.patch("subprocess.run", side_effect=self._runs(status_out=dirty)):
            c = gh["check_git"]()
        assert c.status == "warn"

    def test_corrupt_detail_truncated(self, gh):
        long_err = "fatal: " + "x" * 300
        with mock.patch(
            "subprocess.run",
            side_effect=self._runs(fsck_rc=1, fsck_err=long_err),
        ):
            c = gh["check_git"]()
        assert c.status == "crit"
        assert len(c.detail) <= 200


# ── check_venv extended ──────────────────────────────────────────────────────


class TestCheckVenvExtended:
    def test_subprocess_error(self, gh, tmp_path):
        venv = tmp_path / "germline" / ".venv" / "bin"
        venv.mkdir(parents=True, exist_ok=True)
        (venv / "python").touch()
        with mock.patch("subprocess.run", side_effect=Exception("spawn fail")):
            c = gh["check_venv"]()
        assert c.status == "error"
        assert "spawn fail" in c.detail


# ── check_tests extended ──────────────────────────────────────────────────────


class TestCheckTestsExtended:
    def test_collection_error_line(self, gh):
        with mock.patch(
            "subprocess.run",
            return_value=mock.Mock(returncode=1, stdout="", stderr="collection error found\n"),
        ):
            c = gh["check_tests"]()
        assert c.status == "warn"

    def test_fallback_no_collected_line(self, gh):
        with mock.patch(
            "subprocess.run",
            return_value=mock.Mock(returncode=0, stdout="some random output\n", stderr=""),
        ):
            c = gh["check_tests"]()
        assert c.status == "ok"
        assert "some random output" in c.value

    def test_empty_output(self, gh):
        with mock.patch(
            "subprocess.run",
            return_value=mock.Mock(returncode=0, stdout="", stderr=""),
        ):
            c = gh["check_tests"]()
        assert c.status == "ok"
        assert c.value == "no output"


# ── check_stale_files extended ────────────────────────────────────────────────


class TestCheckStaleFilesExtended:
    def test_multiple_issues(self, gh, tmp_path):
        sdir = tmp_path / "sessions"
        sdir.mkdir(parents=True, exist_ok=True)
        gh["SESSION_KEEP"] = 2
        for i in range(5):
            (sdir / f"s{i}.jsonl").write_text("{}")
        lock = tmp_path / "test.lock"
        lock.write_text("")
        old = time.time() - 7200
        os.utime(lock, (old, old))
        c = gh["check_stale_files"]()
        assert c.status == "warn"
        assert "2 issues" in c.value

    def test_log_stat_oserror(self, gh, tmp_path):
        vdir = tmp_path / "vivesca"
        vdir.mkdir(parents=True, exist_ok=True)
        gh["LOG_MAX_MB"] = 0.0
        log_file = vdir / "app.log"
        log_file.write_text("x")
        original_stat = Path.stat

        def selective_stat(self, *, follow_symlinks=True):
            if "app.log" in str(self):
                raise OSError("permission denied")
            return original_stat(self, follow_symlinks=follow_symlinks)

        with mock.patch.object(Path, "stat", selective_stat):
            c = gh["check_stale_files"]()
        # Should not crash, may or may not report log issue
        assert c.name == "stale"


# ── fix_disk extended ─────────────────────────────────────────────────────────


class TestFixDiskExtended:
    def test_prunes_go_build_cache(self, gh, tmp_path):
        go_cache = tmp_path / ".cache" / "go-build"
        go_cache.mkdir(parents=True, exist_ok=True)
        (go_cache / "testfile").write_text("data")
        report = gh["HealthReport"]()
        with mock.patch("subprocess.run"):
            gh["fix_disk"](report)
        assert not go_cache.exists()
        assert any("go-build" in f for f in report.fixes_applied)

    def test_uv_cache_prune_called(self, gh, tmp_path):
        report = gh["HealthReport"]()
        with mock.patch("subprocess.run") as mr:
            gh["fix_disk"](report)
        cmd_strs = [" ".join(str(a) for a in call[0][0]) if call[0][0] else "" for call in mr.call_args_list]
        assert any("uv" in c and "cache" in c for c in cmd_strs)

    def test_session_unlink_oserror(self, gh, tmp_path):
        sdir = tmp_path / "sessions"
        sdir.mkdir(parents=True, exist_ok=True)
        gh["SESSION_KEEP"] = 0
        (sdir / "s0.jsonl").write_text("{}")
        report = gh["HealthReport"]()
        with mock.patch.object(Path, "unlink", side_effect=OSError("busy")):
            with mock.patch("subprocess.run"):
                gh["fix_disk"](report)
        # Should not crash
        assert report is not None

    def test_truncates_large_jsonl_content(self, gh, tmp_path):
        vdir = tmp_path / "vivesca"
        vdir.mkdir(parents=True, exist_ok=True)
        big = vdir / "events.jsonl"
        lines = [f'{{"i": {i}}}' for i in range(6000)]
        big.write_text("\n".join(lines) + "\n")
        original_stat = Path.stat

        def fake_stat(self, *, follow_symlinks=True):
            if "events.jsonl" in str(self):
                return mock.Mock(st_size=21 * 1024 * 1024, st_mode=0o100644)
            return original_stat(self, follow_symlinks=follow_symlinks)

        report = gh["HealthReport"]()
        with mock.patch.object(Path, "stat", fake_stat):
            with mock.patch("subprocess.run"):
                gh["fix_disk"](report)
        # After truncation should keep last 5000 lines
        remaining = big.read_text().strip().splitlines()
        assert len(remaining) <= 5000

    def test_no_sessions_dir(self, gh, tmp_path):
        gh["SESSION_DIR"] = tmp_path / "nonexistent"
        report = gh["HealthReport"]()
        with mock.patch("subprocess.run"):
            gh["fix_disk"](report)
        # Should not crash


# ── fix_stale extended ────────────────────────────────────────────────────────


class TestFixStaleExtended:
    def test_unlink_oserror(self, gh, tmp_path):
        lock = tmp_path / "stuck.lock"
        lock.write_text("")
        old = time.time() - 7200
        os.utime(lock, (old, old))
        report = gh["HealthReport"]()
        with mock.patch.object(Path, "unlink", side_effect=OSError("permission")):
            gh["fix_stale"](report)
        # Should not crash, fix should not be recorded
        assert not any("stuck.lock" in f for f in report.fixes_applied)

    def test_stat_oserror_skips(self, gh, tmp_path):
        lock = tmp_path / "bad.lock"
        lock.write_text("")
        old = time.time() - 7200
        os.utime(lock, (old, old))
        report = gh["HealthReport"]()
        with mock.patch.object(Path, "stat", side_effect=OSError("no access")):
            gh["fix_stale"](report)
        # Should not crash


# ── fix_daemon extended ───────────────────────────────────────────────────────


class TestFixDaemonExtended:
    def test_bad_pid_value(self, gh, tmp_path):
        pf = tmp_path / "d.pid"
        pf.write_text("not-a-pid")
        gh["PIDFILE"] = pf
        report = gh["HealthReport"]()
        gh["fix_daemon"](report)
        assert not pf.exists()
        assert any("stale" in f for f in report.fixes_applied)

    def test_permission_error_keeps_pidfile(self, gh, tmp_path):
        pf = tmp_path / "d.pid"
        pf.write_text(str(os.getpid()))
        gh["PIDFILE"] = pf
        report = gh["HealthReport"]()
        with mock.patch("os.kill", side_effect=PermissionError):
            gh["fix_daemon"](report)
        assert pf.exists()
        assert report.fixes_applied == []


# ── run_health extended ───────────────────────────────────────────────────────


class TestRunHealthExtended:
    def test_fix_mode_stale_files(self, gh, tmp_path):
        lock = tmp_path / "test.lock"
        lock.write_text("")
        old = time.time() - 7200
        os.utime(lock, (old, old))
        mock_run = mock.Mock(return_value=mock.Mock(returncode=0, stdout="", stderr=""))
        with mock.patch("subprocess.run", mock_run):
            with mock.patch("shutil.disk_usage", return_value=mock.Mock(used=40, total=100, free=60)):
                with mock.patch("builtins.open", mock.mock_open(read_data="MemTotal: 8000000 kB\nMemAvailable: 4000000 kB\n")):
                    report = gh["run_health"](fix=True)
        assert any("stale lock" in f for f in report.fixes_applied)

    def test_daemon_mode_implies_fix(self, gh, tmp_path):
        pf = tmp_path / "d.pid"
        pf.write_text("999999999")
        gh["PIDFILE"] = pf
        mock_run = mock.Mock(return_value=mock.Mock(returncode=0, stdout="", stderr=""))
        with mock.patch("subprocess.run", mock_run):
            with mock.patch("shutil.disk_usage", return_value=mock.Mock(used=40, total=100, free=60)):
                with mock.patch("builtins.open", mock.mock_open(read_data="MemTotal: 8000000 kB\nMemAvailable: 4000000 kB\n")):
                    report = gh["run_health"](daemon_mode=True)
        assert any("stale" in f for f in report.fixes_applied)

    def test_overall_reflects_worst(self, gh):
        mock_run = mock.Mock(return_value=mock.Mock(returncode=0, stdout="", stderr=""))
        with mock.patch("subprocess.run", mock_run):
            with mock.patch("shutil.disk_usage", return_value=mock.Mock(used=92, total=100, free=8)):
                with mock.patch("builtins.open", mock.mock_open(read_data="MemTotal: 8000000 kB\nMemAvailable: 4000000 kB\n")):
                    report = gh["run_health"](fix=False)
        assert report.overall == "crit"

    def test_no_fix_by_default(self, gh):
        mock_run = mock.Mock(return_value=mock.Mock(returncode=0, stdout="", stderr=""))
        with mock.patch("subprocess.run", mock_run):
            with mock.patch("shutil.disk_usage", return_value=mock.Mock(used=40, total=100, free=60)):
                with mock.patch("builtins.open", mock.mock_open(read_data="MemTotal: 8000000 kB\nMemAvailable: 4000000 kB\n")):
                    report = gh["run_health"](fix=False)
        assert report.fixes_applied == []

    def test_timestamp_set(self, gh):
        mock_run = mock.Mock(return_value=mock.Mock(returncode=0, stdout="", stderr=""))
        with mock.patch("subprocess.run", mock_run):
            with mock.patch("shutil.disk_usage", return_value=mock.Mock(used=40, total=100, free=60)):
                with mock.patch("builtins.open", mock.mock_open(read_data="MemTotal: 8000000 kB\nMemAvailable: 4000000 kB\n")):
                    report = gh["run_health"]()
        assert report.timestamp  # non-empty string


# ── print_report extended ─────────────────────────────────────────────────────


class TestPrintReportExtended:
    def test_error_icon(self, gh, capsys):
        report = gh["HealthReport"](timestamp="2025-01-01")
        report.add(gh["Check"](name="tests", status="error", value="?"))
        gh["print_report"](report)
        out = capsys.readouterr().out
        assert "[?]" in out

    def test_fixes_section(self, gh, capsys):
        report = gh["HealthReport"](timestamp="2025-01-01")
        report.add(gh["Check"](name="disk", status="ok", value="50%"))
        report.fixes_applied.append("pruned cache")
        report.fixes_applied.append("cleared go-build")
        gh["print_report"](report)
        out = capsys.readouterr().out
        assert "Fixes applied" in out
        assert "pruned cache" in out
        assert "cleared go-build" in out

    def test_json_has_timestamp(self, gh, capsys):
        report = gh["HealthReport"](timestamp="2025-04-01 12:00:00")
        gh["print_report"](report, as_json=True)
        data = json.loads(capsys.readouterr().out)
        assert data["timestamp"] == "2025-04-01 12:00:00"

    def test_json_has_fixes(self, gh, capsys):
        report = gh["HealthReport"](timestamp="2025-01-01")
        report.fixes_applied.append("pruned cache")
        gh["print_report"](report, as_json=True)
        data = json.loads(capsys.readouterr().out)
        assert data["fixes"] == ["pruned cache"]

    def test_compact_no_fixes(self, gh, capsys):
        report = gh["HealthReport"]()
        report.add(gh["Check"](name="disk", status="ok", value="50%"))
        gh["print_report"](report, compact=True)
        out = capsys.readouterr().out
        assert "fixes=" not in out

    def test_human_output_overall_line(self, gh, capsys):
        report = gh["HealthReport"](timestamp="2025-01-01")
        report.add(gh["Check"](name="disk", status="warn", value="85%"))
        gh["print_report"](report)
        out = capsys.readouterr().out
        assert "Overall: WARN" in out


# ── main extended ─────────────────────────────────────────────────────────────


class TestMainExtended:
    def test_combined_fix_and_json(self, gh, capsys):
        report = gh["HealthReport"](timestamp="2025-01-01")
        gh["run_health"] = mock.Mock(return_value=report)
        with mock.patch.object(sys, "argv", ["gemmule-health", "--fix", "--json"]):
            with pytest.raises(SystemExit):
                gh["main"]()
        data = json.loads(capsys.readouterr().out)
        assert data["overall"] == "ok"

    def test_daemon_passes_flags(self, gh):
        report = gh["HealthReport"]()
        gh["run_health"] = mock.Mock(return_value=report)
        with mock.patch.object(sys, "argv", ["gemmule-health", "--daemon"]):
            with pytest.raises(SystemExit):
                gh["main"]()
        kw = gh["run_health"].call_args.kwargs
        assert kw["daemon_mode"] is True
