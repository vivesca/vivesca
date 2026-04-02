from __future__ import annotations

"""Tests for soma-status — system health summary CLI."""

import json
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _ensure_tmp_path(tmp_path: Path) -> None:
    """Guarantee tmp_path exists on disk before each test."""
    tmp_path.mkdir(parents=True, exist_ok=True)


def _load_module() -> dict:
    """Load soma-status by exec-ing its source."""
    source = (Path.home() / "germline" / "effectors" / "soma-status").read_text()
    ns: dict = {"__name__": "soma_status"}
    exec(source, ns)
    return ns


_mod = _load_module()
collect_supervisor = _mod["collect_supervisor"]
collect_golem_stats = _mod["collect_golem_stats"]
collect_disk = _mod["collect_disk"]
collect_uptime = _mod["collect_uptime"]
collect_memory = _mod["collect_memory"]
format_human = _mod["format_human"]
format_json = _mod["format_json"]
main = _mod["main"]


def _mock_completed(stdout: str = "", returncode: int = 0) -> MagicMock:
    """Create a mock subprocess.CompletedProcess."""
    m = MagicMock()
    m.stdout = stdout
    m.returncode = returncode
    m.stderr = ""
    return m


# ── supervisor collector ─────────────────────────────────────────────


class TestCollectSupervisor:
    def test_running_program(self):
        out = "golem-daemon                    RUNNING   pid 12345, uptime 1:23:45\n"
        with patch("subprocess.run", return_value=_mock_completed(out)):
            progs = collect_supervisor()
        assert len(progs) == 1
        assert progs[0]["name"] == "golem-daemon"
        assert progs[0]["state"] == "RUNNING"
        assert progs[0]["pid"] == 12345

    def test_stopped_program(self):
        out = "my-service                     STOPPED\n"
        with patch("subprocess.run", return_value=_mock_completed(out)):
            progs = collect_supervisor()
        assert len(progs) == 1
        assert progs[0]["state"] == "STOPPED"
        assert progs[0]["pid"] is None

    def test_multiple_programs(self):
        out = (
            "golem-daemon                    RUNNING   pid 100, uptime 0:10:00\n"
            "webapp                          RUNNING   pid 200, uptime 0:05:00\n"
            "worker                          STOPPED   Not started\n"
        )
        with patch("subprocess.run", return_value=_mock_completed(out)):
            progs = collect_supervisor()
        assert len(progs) == 3
        assert progs[0]["pid"] == 100
        assert progs[2]["state"] == "STOPPED"

    def test_supervisorctl_not_found(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            progs = collect_supervisor()
        assert progs == []

    def test_supervisorctl_timeout(self):
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 10)):
            progs = collect_supervisor()
        assert progs == []

    def test_empty_output(self):
        with patch("subprocess.run", return_value=_mock_completed("")):
            progs = collect_supervisor()
        assert progs == []

    def test_exited_program(self):
        out = "worker                         EXITED    Feb 01 03:00 AM\n"
        with patch("subprocess.run", return_value=_mock_completed(out)):
            progs = collect_supervisor()
        assert progs[0]["state"] == "EXITED"
        assert progs[0]["pid"] is None


# ── golem stats collector ────────────────────────────────────────────


class TestCollectGolemStats:
    def test_success(self):
        stats_out = "Total tasks: 100 (passed: 80, failed: 20)\n"
        with patch("subprocess.run", return_value=_mock_completed(stats_out)):
            result = collect_golem_stats()
        assert "Total tasks: 100" in result

    def test_not_found(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = collect_golem_stats()
        assert "unavailable" in result

    def test_timeout(self):
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
            result = collect_golem_stats()
        assert "unavailable" in result


# ── disk collector ───────────────────────────────────────────────────


class TestCollectDisk:
    def test_normal_output(self):
        out = "Filesystem      Size  Used Avail Use% Mounted on\nnone            7.8G  5.8G  1.6G  79% /\n"
        with patch("subprocess.run", return_value=_mock_completed(out)):
            disk = collect_disk()
        assert disk["filesystem"] == "none"
        assert disk["size"] == "7.8G"
        assert disk["used"] == "5.8G"
        assert disk["avail"] == "1.6G"
        assert disk["use_pct"] == "79%"

    def test_df_not_found(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            disk = collect_disk()
        assert "error" in disk

    def test_empty_output(self):
        with patch("subprocess.run", return_value=_mock_completed("")):
            disk = collect_disk()
        assert "error" in disk

    def test_header_only(self):
        out = "Filesystem      Size  Used Avail Use% Mounted on\n"
        with patch("subprocess.run", return_value=_mock_completed(out)):
            disk = collect_disk()
        assert "error" in disk


# ── uptime collector ─────────────────────────────────────────────────


class TestCollectUptime:
    def test_normal(self):
        out = " 09:47:49 up 1 day,  1:19,  0 user,  load average: 6.16, 8.28, 11.96\n"
        with patch("subprocess.run", return_value=_mock_completed(out)):
            result = collect_uptime()
        assert "up 1 day" in result

    def test_not_found(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = collect_uptime()
        assert "unavailable" in result


# ── memory collector ─────────────────────────────────────────────────


class TestCollectMemory:
    def test_normal_output(self):
        out = (
            "               total        used        free      shared  buff/cache   available\n"
            "Mem:            31Gi       6.0Gi        17Gi        72Mi       8.6Gi        25Gi\n"
            "Swap:          4.0Gi        13Mi       4.0Gi\n"
        )
        with patch("subprocess.run", return_value=_mock_completed(out)):
            mem = collect_memory()
        assert mem["mem"]["total"] == "31Gi"
        assert mem["mem"]["used"] == "6.0Gi"
        assert mem["mem"]["available"] == "25Gi"
        assert mem["swap"]["total"] == "4.0Gi"
        assert mem["swap"]["used"] == "13Mi"

    def test_free_not_found(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            mem = collect_memory()
        assert "error" in mem

    def test_empty_output(self):
        with patch("subprocess.run", return_value=_mock_completed("")):
            mem = collect_memory()
        assert mem.get("mem", {}) == {}
        assert mem.get("swap", {}) == {}


# ── format_human ─────────────────────────────────────────────────────


class TestFormatHuman:
    def _make_data(self):
        supervisor = [{"name": "golem-daemon", "state": "RUNNING", "pid": 123, "info": "pid 123, uptime 1:00:00"}]
        golem_stats = "Total tasks: 10 (passed: 8, failed: 2)"
        disk = {"filesystem": "none", "size": "8G", "used": "5G", "avail": "3G", "use_pct": "62%", "mounted": "/"}
        uptime_str = "10:00:00 up 5 days, 2:00, 1 user, load average: 1.0, 1.5, 2.0"
        memory = {
            "mem": {"total": "16Gi", "used": "8Gi", "free": "4Gi", "shared": "0", "buff_cache": "4Gi", "available": "8Gi"},
            "swap": {"total": "4Gi", "used": "0", "free": "4Gi"},
        }
        return supervisor, golem_stats, disk, uptime_str, memory

    def test_has_section_headers(self):
        out = format_human(*self._make_data())
        assert "UPTIME" in out
        assert "SERVICES" in out
        assert "GOLEM STATS" in out
        assert "DISK" in out
        assert "MEMORY" in out

    def test_shows_supervisor_programs(self):
        out = format_human(*self._make_data())
        assert "golem-daemon" in out
        assert "RUNNING" in out

    def test_shows_disk_usage(self):
        out = format_human(*self._make_data())
        assert "8G total" in out
        assert "5G used" in out
        assert "62% full" in out

    def test_shows_memory(self):
        out = format_human(*self._make_data())
        assert "RAM:  8Gi used / 16Gi total" in out
        assert "8Gi available" in out

    def test_empty_supervisor(self):
        data = self._make_data()
        data[0].clear()  # type: ignore[index]
        out = format_human(*data)
        assert "supervisor not running" in out

    def test_disk_error(self):
        data = list(self._make_data())
        data[2] = {"error": "df not found"}
        out = format_human(*data)
        assert "df not found" in out

    def test_no_memory_info(self):
        data = list(self._make_data())
        data[4] = {"mem": {}, "swap": {}}
        out = format_human(*data)
        assert "memory info unavailable" in out


# ── format_json ──────────────────────────────────────────────────────


class TestFormatJson:
    def _make_data(self):
        supervisor = [{"name": "golem-daemon", "state": "RUNNING", "pid": 123, "info": "pid 123"}]
        golem_stats = "Total tasks: 10"
        disk = {"filesystem": "none", "size": "8G", "used": "5G", "avail": "3G", "use_pct": "62%", "mounted": "/"}
        uptime_str = "up 5 days"
        memory = {"mem": {"total": "16Gi", "used": "8Gi"}, "swap": {"total": "4Gi", "used": "0"}}
        return supervisor, golem_stats, disk, uptime_str, memory

    def test_valid_json(self):
        out = format_json(*self._make_data())
        parsed = json.loads(out)
        assert "uptime" in parsed
        assert "supervisor" in parsed
        assert "golem_stats" in parsed
        assert "disk" in parsed
        assert "memory" in parsed

    def test_json_supervisor_content(self):
        out = format_json(*self._make_data())
        parsed = json.loads(out)
        assert parsed["supervisor"][0]["name"] == "golem-daemon"

    def test_json_disk_content(self):
        out = format_json(*self._make_data())
        parsed = json.loads(out)
        assert parsed["disk"]["use_pct"] == "62%"


# ── main() integration ───────────────────────────────────────────────


class TestMain:
    def test_human_output(self):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                _mock_completed("golem-daemon  RUNNING   pid 1, uptime 0:00:01\n"),  # supervisorctl
                _mock_completed("Total tasks: 5\n"),  # golem stats
                _mock_completed("Filesystem Size Used Avail Use% Mounted\n/dev 10G 5G 5G 50% /\n"),  # df
                _mock_completed("up 1 day\n"),  # uptime
                _mock_completed("Mem: 16Gi 8Gi 4Gi 0 4Gi 8Gi\nSwap: 4Gi 0 4Gi\n"),  # free
            ]
            buf = StringIO()
            with patch("sys.stdout", buf):
                rc = main([])
        assert rc == 0
        output = buf.getvalue()
        assert "UPTIME" in output
        assert "GOLEM STATS" in output
        assert "DISK" in output

    def test_json_output(self):
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                _mock_completed(""),  # supervisorctl
                _mock_completed("Total tasks: 0\n"),  # golem stats
                _mock_completed("Filesystem Size Used Avail Use% Mounted\n/dev 10G 5G 5G 50% /\n"),  # df
                _mock_completed("up 1 day\n"),  # uptime
                _mock_completed("Mem: 16Gi 8Gi 4Gi 0 4Gi 8Gi\nSwap: 4Gi 0 4Gi\n"),  # free
            ]
            buf = StringIO()
            with patch("sys.stdout", buf):
                rc = main(["--json"])
        assert rc == 0
        parsed = json.loads(buf.getvalue())
        assert "uptime" in parsed
        assert "disk" in parsed

    def test_all_commands_fail_gracefully(self):
        """main() returns 0 even when all subprocesses fail."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            buf = StringIO()
            with patch("sys.stdout", buf):
                rc = main([])
        assert rc == 0
        output = buf.getvalue()
        assert "MEMORY" in output

    def test_all_commands_fail_json(self):
        """main() --json returns valid JSON even when all subprocesses fail."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            buf = StringIO()
            with patch("sys.stdout", buf):
                rc = main(["--json"])
        assert rc == 0
        parsed = json.loads(buf.getvalue())
        assert parsed["supervisor"] == []
        assert "error" in parsed["disk"]


# ── edge cases ───────────────────────────────────────────────────────


class TestEdgeCases:
    def test_supervisor_malformed_line_skipped(self):
        out = "not a valid line\ngood-svc  RUNNING   pid 1, uptime 0:00:01\n"
        with patch("subprocess.run", return_value=_mock_completed(out)):
            progs = collect_supervisor()
        assert len(progs) == 1
        assert progs[0]["name"] == "good-svc"

    def test_disk_malformed_second_line(self):
        out = "Filesystem Size Used Avail Use% Mounted on\noops\n"
        with patch("subprocess.run", return_value=_mock_completed(out)):
            disk = collect_disk()
        assert "error" in disk
