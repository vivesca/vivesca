from __future__ import annotations

import plistlib
import subprocess
from unittest.mock import Mock, patch

from metabolon.resources import oscillators


def test_scan_pacemaker_plists(tmp_path):
    # Patch _LAUNCH_AGENTS to our temporary directory
    with patch.object(oscillators, "_LAUNCH_AGENTS", tmp_path):
        # Create some test plists
        (tmp_path / "com.vivesca.test1.plist").touch()
        (tmp_path / "com.terry.test2.plist").touch()
        (tmp_path / "com.other.test3.plist").touch()
        (tmp_path / "com.vivesca.testA.plist").touch()

        result = oscillators._scan_pacemaker_plists()
        # Should only match vivesca and terry plists, sorted by name
        expected_names = [
            "com.terry.test2.plist",
            "com.vivesca.test1.plist",
            "com.vivesca.testA.plist",
        ]
        assert [p.name for p in result] == expected_names


def test_launchctl_status_success():
    with patch("metabolon.resources.oscillators.subprocess.run") as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """{
            "PID" = 1234;
            "LastExitStatus" = 0;
        }"""
        mock_run.return_value = mock_result

        status = oscillators._launchctl_status("com.vivesca.test")
        assert status["running"] is True
        assert status["pid"] == 1234
        assert status["last_exit"] == 0
        assert status["loaded"] is True


def test_launchctl_status_not_loaded():
    with patch("metabolon.resources.oscillators.subprocess.run") as mock_run:
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        status = oscillators._launchctl_status("com.vivesca.test")
        assert status["running"] is False
        assert status["pid"] is None
        assert status["last_exit"] is None
        assert status["loaded"] is False


def test_launchctl_status_timeout():
    with patch("metabolon.resources.oscillators.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(["launchctl"], 5)

        status = oscillators._launchctl_status("com.vivesca.test")
        assert status == {"running": False, "pid": None, "last_exit": None, "loaded": False}


def test_launchctl_status_non_darwin():
    """On non-Darwin platforms, _launchctl_status should return unavailable dict."""
    with patch("metabolon.resources.oscillators.platform.system", return_value="Linux"):
        status = oscillators._launchctl_status("com.vivesca.test")
    assert status == {"running": False, "pid": None, "last_exit": None, "loaded": False}


def test_format_calendar_interval():
    # Test various calendar intervals
    assert oscillators._format_calendar_interval({"Weekday": 1}) == "Mon"
    assert oscillators._format_calendar_interval({"Day": 15}) == "day 15"
    assert oscillators._format_calendar_interval({"Hour": 9, "Minute": 30}) == "09:30"
    assert oscillators._format_calendar_interval({"Hour": 14}) == "14:xx"
    assert oscillators._format_calendar_interval({"Minute": 0}) == "xx:00"
    assert (
        oscillators._format_calendar_interval({"Weekday": 5, "Hour": 18, "Minute": 0})
        == "Fri 18:00"
    )
    assert oscillators._format_calendar_interval({}) == "scheduled"


def test_parse_schedule():
    # Test StartInterval
    assert oscillators._parse_schedule({"StartInterval": 30}) == "every 30s"
    assert oscillators._parse_schedule({"StartInterval": 300}) == "every 5m"
    assert oscillators._parse_schedule({"StartInterval": 7200}) == "every 2h"
    assert oscillators._parse_schedule({"StartInterval": 5400}) == "every 1.5h"
    assert oscillators._parse_schedule({"StartInterval": 86400}) == "every 1d"

    # Test StartCalendarInterval
    sci_single = {"StartCalendarInterval": {"Hour": 9, "Minute": 0}}
    assert oscillators._parse_schedule(sci_single) == "09:00"

    sci_list = {"StartCalendarInterval": [{"Hour": 9}, {"Hour": 18}]}
    assert oscillators._parse_schedule(sci_list) == "09:xx; 18:xx"

    # Test RunAtLoad
    assert oscillators._parse_schedule({"RunAtLoad": True}) == "on-load only"

    # Test on-demand
    assert oscillators._parse_schedule({}) == "on-demand"


def test_status_label():
    assert oscillators._status_label({"loaded": False}) == "unloaded"
    assert oscillators._status_label({"loaded": True, "running": True}) == "running"
    assert (
        oscillators._status_label({"loaded": True, "running": False, "last_exit": None}) == "idle"
    )
    assert oscillators._status_label({"loaded": True, "running": False, "last_exit": 0}) == "idle"
    assert oscillators._status_label({"loaded": True, "running": False, "last_exit": 1}) == "error"


def test_plist_type(tmp_path):
    normal_file = tmp_path / "normal.plist"
    normal_file.touch()
    assert oscillators._plist_type(normal_file) == "copy"

    symlink = tmp_path / "symlink.plist"
    symlink.symlink_to(normal_file)
    assert oscillators._plist_type(symlink) == "symlink"


def test_express_pacemaker_status_no_plists():
    with patch.object(oscillators, "_scan_pacemaker_plists", return_value=[]):
        result = oscillators.express_pacemaker_status()
        assert "no com.vivesca.* or com.terry.* plists found" in result


def test_express_pacemaker_status_with_plists(tmp_path):
    # Create a test plist
    plist_data = {
        "Label": "com.vivesca.test",
        "StartInterval": 300,
    }
    plist_path = tmp_path / "com.vivesca.test.plist"
    with plist_path.open("wb") as f:
        plistlib.dump(plist_data, f)

    with patch.object(oscillators, "_scan_pacemaker_plists", return_value=[plist_path]):
        with patch.object(
            oscillators,
            "_launchctl_status",
            return_value={"loaded": True, "running": False, "last_exit": 0, "pid": None},
        ):
            with patch.object(oscillators, "_plist_type", return_value="copy"):
                result = oscillators.express_pacemaker_status()
                assert "com.vivesca.test" in result
                assert "every 5m" in result
                assert "idle" in result
