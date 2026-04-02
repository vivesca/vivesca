from __future__ import annotations

"""Tests for soma-watchdog observability: log_resources, alert_on_crit."""

import json
import subprocess
import time
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

log_resources = _mod["log_resources"]
alert_on_crit = _mod["alert_on_crit"]
check_cycle = _mod["check_cycle"]
main = _mod["main"]

HOME = _mod["HOME"]
JSONL_PATH = _mod["JSONL_PATH"]
ALERT_STAMP = _mod["ALERT_STAMP"]


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


def test_jsonl_path_constant():
    assert JSONL_PATH == HOME / "epigenome" / "chromatin" / "telemetry" / "soma-resources.jsonl"


def test_alert_stamp_constant():
    assert ALERT_STAMP == HOME / "tmp" / "soma-alert-last.txt"


# ── log_resources ──────────────────────────────────────────────────────


def test_log_resources_writes_jsonl(tmp_path):
    jsonl = tmp_path / "soma-resources.jsonl"
    with _P("JSONL_PATH", jsonl), \
         patch("shutil.disk_usage", return_value=MagicMock(used=50, total=100, free=50)):
        log_resources()
    assert jsonl.exists()
    data = json.loads(jsonl.read_text().strip())
    assert "ts" in data
    assert "cpu_1m" in data
    assert "mem_pct" in data
    assert "disk_pct" in data
    assert "disk_free_gb" in data
    assert "golem_count" in data


def test_log_resources_ts_is_iso(tmp_path):
    jsonl = tmp_path / "soma-resources.jsonl"
    with _P("JSONL_PATH", jsonl), \
         patch("shutil.disk_usage", return_value=MagicMock(used=50, total=100, free=50)):
        log_resources()
    data = json.loads(jsonl.read_text().strip())
    # Should parse as ISO format
    datetime.fromisoformat(data["ts"])


def test_log_resources_cpu_from_loadavg(tmp_path):
    jsonl = tmp_path / "soma-resources.jsonl"
    fake_loadavg = MagicMock()
    fake_loadavg.read_text.return_value = "2.60 12.20 22.78 5/1129 20994"
    with _P("JSONL_PATH", jsonl), \
         patch("shutil.disk_usage", return_value=MagicMock(used=50, total=100, free=50)), \
         patch.object(Path, "read_text", fake_loadavg.read_text):
        # Path("/proc/loadavg") will use mocked read_text
        log_resources()
    # If /proc/loadavg is readable, cpu_1m is a float; exact value depends on mock
    data = json.loads(jsonl.read_text().strip())
    assert isinstance(data["cpu_1m"], float)


def test_log_resources_disk_fields(tmp_path):
    jsonl = tmp_path / "soma-resources.jsonl"
    u = MagicMock(used=30 * 1024 ** 3, total=100 * 1024 ** 3, free=70 * 1024 ** 3)
    with _P("JSONL_PATH", jsonl), \
         patch("shutil.disk_usage", return_value=u), \
         patch("subprocess.run", return_value=MagicMock(stdout="3\n", returncode=0)):
        log_resources()
    data = json.loads(jsonl.read_text().strip())
    assert data["disk_pct"] == pytest.approx(30.0)
    assert data["disk_free_gb"] == pytest.approx(70.0)


def test_log_resources_golem_count(tmp_path):
    jsonl = tmp_path / "soma-resources.jsonl"
    with _P("JSONL_PATH", jsonl), \
         patch("shutil.disk_usage", return_value=MagicMock(used=50, total=100, free=50)), \
         patch("subprocess.run", return_value=MagicMock(stdout="5\n", returncode=0)):
        log_resources()
    data = json.loads(jsonl.read_text().strip())
    assert data["golem_count"] == 5


def test_log_resources_golem_count_zero_on_fail(tmp_path):
    jsonl = tmp_path / "soma-resources.jsonl"
    with _P("JSONL_PATH", jsonl), \
         patch("shutil.disk_usage", return_value=MagicMock(used=50, total=100, free=50)), \
         patch("subprocess.run", return_value=MagicMock(stdout="", returncode=1)):
        log_resources()
    data = json.loads(jsonl.read_text().strip())
    assert data["golem_count"] == 0


def test_log_resources_creates_dir(tmp_path):
    jsonl = tmp_path / "deep" / "nested" / "soma-resources.jsonl"
    with _P("JSONL_PATH", jsonl), \
         patch("shutil.disk_usage", return_value=MagicMock(used=50, total=100, free=50)):
        log_resources()
    assert jsonl.exists()


def test_log_resources_appends(tmp_path):
    jsonl = tmp_path / "soma-resources.jsonl"
    with _P("JSONL_PATH", jsonl), \
         patch("shutil.disk_usage", return_value=MagicMock(used=50, total=100, free=50)):
        log_resources()
        log_resources()
    lines = jsonl.read_text().strip().splitlines()
    assert len(lines) == 2


# ── alert_on_crit ──────────────────────────────────────────────────────


def test_alert_no_crit_no_call(tmp_path):
    stamp = tmp_path / "alert-stamp.txt"
    health = {"disk_volume": {"status": "ok", "free_gb": 50.0}}
    with _P("ALERT_STAMP", stamp), \
         patch("subprocess.run") as mr:
        alert_on_crit(health)
    mr.assert_not_called()


def test_alert_crit_sends_deltos(tmp_path):
    stamp = tmp_path / "alert-stamp.txt"
    health = {"disk_volume": {"status": "crit", "free_gb": 0.5}}
    with _P("ALERT_STAMP", stamp), \
         patch("shutil.which", return_value="deltos"), \
         patch("subprocess.run") as mr:
        alert_on_crit(health)
    mr.assert_called_once()
    args = mr.call_args[0][0]
    assert args[0] == "deltos"
    assert "disk_volume" in args[1]


def test_alert_writes_stamp(tmp_path):
    stamp = tmp_path / "alert-stamp.txt"
    health = {"disk_volume": {"status": "crit", "free_gb": 0.5}}
    with _P("ALERT_STAMP", stamp), \
         patch("shutil.which", return_value="deltos"), \
         patch("subprocess.run"):
        alert_on_crit(health)
    assert stamp.exists()
    datetime.fromisoformat(stamp.read_text().strip())


def test_alert_dedup_skips_within_15min(tmp_path):
    stamp = tmp_path / "alert-stamp.txt"
    stamp.write_text("recent")
    # Set mtime to 5 minutes ago
    recent = time.time() - 5 * 60
    import os
    os.utime(str(stamp), (recent, recent))
    health = {"disk_volume": {"status": "crit", "free_gb": 0.5}}
    with _P("ALERT_STAMP", stamp), \
         patch("subprocess.run") as mr:
        alert_on_crit(health)
    mr.assert_not_called()


def test_alert_dedup_sends_after_15min(tmp_path):
    stamp = tmp_path / "alert-stamp.txt"
    stamp.write_text("old")
    # Set mtime to 20 minutes ago
    old = time.time() - 20 * 60
    import os
    os.utime(str(stamp), (old, old))
    health = {"disk_volume": {"status": "crit", "free_gb": 0.5}}
    with _P("ALERT_STAMP", stamp), \
         patch("shutil.which", return_value="deltos"), \
         patch("subprocess.run") as mr:
        alert_on_crit(health)
    mr.assert_called_once()


def test_alert_multiple_crit_names(tmp_path):
    stamp = tmp_path / "alert-stamp.txt"
    health = {
        "disk_volume": {"status": "crit", "free_gb": 0.5},
        "root_fs": {"status": "ok", "free_mb": 600},
        "mem": {"status": "crit", "pct": 99},
    }
    with _P("ALERT_STAMP", stamp), \
         patch("shutil.which", return_value="deltos"), \
         patch("subprocess.run") as mr:
        alert_on_crit(health)
    msg = mr.call_args[0][0][1]
    assert "disk_volume" in msg
    assert "mem" in msg


def test_alert_creates_stamp_dir(tmp_path):
    stamp = tmp_path / "deep" / "stamp.txt"
    health = {"disk_volume": {"status": "crit", "free_gb": 0.5}}
    with _P("ALERT_STAMP", stamp), \
         patch("subprocess.run"):
        alert_on_crit(health)
    assert stamp.exists()


def test_alert_empty_dict_no_call(tmp_path):
    stamp = tmp_path / "alert-stamp.txt"
    with _P("ALERT_STAMP", stamp), \
         patch("subprocess.run") as mr:
        alert_on_crit({})
    mr.assert_not_called()


# ── check_cycle returns health ─────────────────────────────────────────


def test_check_cycle_returns_health_ok(tmp_path):
    lp = tmp_path / "w.log"
    with _P("LOG", lp), \
         _P("free_gb", MagicMock(return_value=50.0)), \
         _P("free_mb", MagicMock(return_value=10000.0)), \
         _P("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            health = check_cycle()
    assert isinstance(health, dict)
    assert health["disk_volume"]["status"] == "ok"
    assert health["root_fs"]["status"] == "ok"


def test_check_cycle_returns_health_crit(tmp_path):
    lp = tmp_path / "w.log"
    with _P("LOG", lp), \
         _P("free_gb", MagicMock(side_effect=[0.5, 0.5])), \
         _P("free_mb", MagicMock(return_value=10000.0)), \
         _P("clean_temps", MagicMock(return_value=0)), \
         _P("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            health = check_cycle()
    assert health["disk_volume"]["status"] == "crit"


def test_check_cycle_returns_health_warn(tmp_path):
    lp = tmp_path / "w.log"
    with _P("LOG", lp), \
         _P("free_gb", MagicMock(side_effect=[1.5, 1.5])), \
         _P("free_mb", MagicMock(return_value=10000.0)), \
         _P("clean_temps", MagicMock(return_value=0)), \
         _P("kill_runaway_golems", MagicMock(return_value=0)):
        with patch("subprocess.run"):
            health = check_cycle()
    assert health["disk_volume"]["status"] == "warn"


# ── main loop integration ──────────────────────────────────────────────


def test_main_calls_log_resources_and_alert(tmp_path):
    lp = tmp_path / "w.log"
    jsonl = tmp_path / "soma-resources.jsonl"
    stamp = tmp_path / "stamp.txt"
    lr_called = []
    ac_called = []

    def fake_log_resources():
        lr_called.append(1)

    def fake_alert_on_crit(h):
        ac_called.append(h)

    def boom():
        raise KeyboardInterrupt

    with _P("LOG", lp), \
         _P("JSONL_PATH", jsonl), \
         _P("ALERT_STAMP", stamp), \
         _P("check_cycle", lambda: {"disk_volume": {"status": "ok"}}), \
         _P("log_resources", fake_log_resources), \
         _P("alert_on_crit", fake_alert_on_crit):
        with patch.object(_mod["sys"], "argv", ["w"]):
            main()
    assert len(lr_called) >= 1
    assert len(ac_called) >= 1
    assert ac_called[0]["disk_volume"]["status"] == "ok"
