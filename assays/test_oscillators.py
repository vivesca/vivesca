"""Tests for metabolon.resources.oscillators — pacemaker LaunchAgent status."""

from __future__ import annotations

import plistlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.resources.oscillators import (
    _format_calendar_interval,
    _launchctl_status,
    _parse_schedule,
    _plist_type,
    _scan_pacemaker_plists,
    _status_label,
    express_pacemaker_status,
)


# ---------------------------------------------------------------------------
# _format_calendar_interval
# ---------------------------------------------------------------------------
class TestFormatCalendarInterval:
    def test_weekday_only(self):
        assert _format_calendar_interval({"Weekday": 1}) == "Mon"

    def test_weekday_sunday(self):
        assert _format_calendar_interval({"Weekday": 0}) == "Sun"

    def test_weekday_saturday(self):
        assert _format_calendar_interval({"Weekday": 6}) == "Sat"

    def test_weekday_out_of_range(self):
        assert _format_calendar_interval({"Weekday": 9}) == "wd9"

    def test_hour_and_minute(self):
        assert _format_calendar_interval({"Hour": 8, "Minute": 30}) == "08:30"

    def test_hour_only(self):
        assert _format_calendar_interval({"Hour": 14}) == "14:xx"

    def test_minute_only(self):
        assert _format_calendar_interval({"Minute": 5}) == "xx:05"

    def test_day_only(self):
        assert _format_calendar_interval({"Day": 15}) == "day 15"

    def test_full_combination(self):
        result = _format_calendar_interval({"Weekday": 3, "Hour": 9, "Minute": 0})
        assert result == "Wed 09:00"

    def test_empty_dict(self):
        assert _format_calendar_interval({}) == "scheduled"


# ---------------------------------------------------------------------------
# _parse_schedule
# ---------------------------------------------------------------------------
class TestParseSchedule:
    def test_start_calendar_interval_single(self):
        sci = {"Hour": 7, "Minute": 0}
        assert _parse_schedule({"StartCalendarInterval": sci}) == "07:00"

    def test_start_calendar_interval_list(self):
        sci_list = [{"Hour": 7, "Minute": 0}, {"Hour": 19, "Minute": 30}]
        result = _parse_schedule({"StartCalendarInterval": sci_list})
        assert result == "07:00; 19:30"

    def test_start_interval_seconds(self):
        assert _parse_schedule({"StartInterval": 30}) == "every 30s"

    def test_start_interval_minutes(self):
        assert _parse_schedule({"StartInterval": 300}) == "every 5m"

    def test_start_interval_hours_whole(self):
        assert _parse_schedule({"StartInterval": 7200}) == "every 2h"

    def test_start_interval_hours_fractional(self):
        assert _parse_schedule({"StartInterval": 5400}) == "every 1.5h"

    def test_start_interval_days_whole(self):
        assert _parse_schedule({"StartInterval": 172800}) == "every 2d"

    def test_start_interval_days_fractional(self):
        assert _parse_schedule({"StartInterval": 129600}) == "every 1.5d"

    def test_run_at_load_only(self):
        assert _parse_schedule({"RunAtLoad": True}) == "on-load only"

    def test_run_at_load_with_interval_is_not_on_load(self):
        """If StartInterval is also present, the interval wins."""
        result = _parse_schedule({"RunAtLoad": True, "StartInterval": 60})
        assert result == "every 1m"

    def test_empty_plist(self):
        assert _parse_schedule({}) == "on-demand"


# ---------------------------------------------------------------------------
# _status_label
# ---------------------------------------------------------------------------
class TestStatusLabel:
    def test_unloaded(self):
        assert _status_label({"loaded": False, "running": False, "pid": None, "last_exit": None}) == "unloaded"

    def test_running(self):
        assert _status_label({"loaded": True, "running": True, "pid": 123, "last_exit": None}) == "running"

    def test_idle_exit_zero(self):
        assert _status_label({"loaded": True, "running": False, "pid": None, "last_exit": 0}) == "idle"

    def test_idle_no_exit(self):
        assert _status_label({"loaded": True, "running": False, "pid": None, "last_exit": None}) == "idle"

    def test_error_nonzero_exit(self):
        assert _status_label({"loaded": True, "running": False, "pid": None, "last_exit": 1}) == "error"

    def test_error_negative_exit(self):
        assert _status_label({"loaded": True, "running": False, "pid": None, "last_exit": -2}) == "error"


# ---------------------------------------------------------------------------
# _plist_type
# ---------------------------------------------------------------------------
class TestPlistType:
    def test_symlink(self, tmp_path: Path):
        target = tmp_path / "real.plist"
        target.write_bytes(b"dummy")
        link = tmp_path / "link.plist"
        link.symlink_to(target)
        assert _plist_type(link) == "symlink"

    def test_regular_file(self, tmp_path: Path):
        regular = tmp_path / "regular.plist"
        regular.write_bytes(b"dummy")
        assert _plist_type(regular) == "copy"


# ---------------------------------------------------------------------------
# _launchctl_status
# ---------------------------------------------------------------------------
class TestLaunchctlStatus:
    @patch("metabolon.resources.oscillators.subprocess.run")
    def test_running_with_pid(self, mock_run: MagicMock):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='"PID" = 4242;\n"LastExitStatus" = 0;',
        )
        result = _launchctl_status("com.vivesca.sync")
        assert result == {"running": True, "pid": 4242, "last_exit": 0, "loaded": True}

    @patch("metabolon.resources.oscillators.subprocess.run")
    def test_loaded_idle(self, mock_run: MagicMock):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='"LastExitStatus" = 0;',
        )
        result = _launchctl_status("com.vivesca.sync")
        assert result == {"running": False, "pid": None, "last_exit": 0, "loaded": True}

    @patch("metabolon.resources.oscillators.subprocess.run")
    def test_nonzero_returncode(self, mock_run: MagicMock):
        mock_run.returnvalue = MagicMock(returncode=1, stdout="")
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = _launchctl_status("com.vivesca.nope")
        assert result == {"running": False, "pid": None, "last_exit": None, "loaded": False}

    @patch("metabolon.resources.oscillators.subprocess.run")
    def test_negative_exit_status(self, mock_run: MagicMock):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='"LastExitStatus" = -9;',
        )
        result = _launchctl_status("com.vivesca.oops")
        assert result == {"running": False, "pid": None, "last_exit": -9, "loaded": True}

    @patch("metabolon.resources.oscillators.subprocess.run", side_effect=OSError("boom"))
    def test_os_error(self, mock_run: MagicMock):
        result = _launchctl_status("com.vivesca.broken")
        assert result == {"running": False, "pid": None, "last_exit": None, "loaded": False}


# ---------------------------------------------------------------------------
# _scan_pacemaker_plists
# ---------------------------------------------------------------------------
class TestScanPacemakerPlists:
    @patch("metabolon.resources.oscillators._LAUNCH_AGENTS", Path("/fake/agents"))
    def test_finds_matching_plists(self, tmp_path: Path, monkeypatch):
        """Glob in the real LaunchAgents won't find our files; patch the path."""
        agents = tmp_path / "agents"
        agents.mkdir()
        (agents / "com.vivesca.sync.plist").write_bytes(b"")
        (agents / "com.vivesca.poll.plist").write_bytes(b"")
        (agents / "com.other.app.plist").write_bytes(b"")
        monkeypatch.setattr("metabolon.resources.oscillators._LAUNCH_AGENTS", agents)
        result = _scan_pacemaker_plists()
        names = [p.name for p in result]
        assert "com.vivesca.sync.plist" in names
        assert "com.vivesca.poll.plist" in names
        assert "com.other.app.plist" not in names

    @patch("metabolon.resources.oscillators._LAUNCH_AGENTS", Path("/fake/agents"))
    def test_empty_directory(self, tmp_path: Path, monkeypatch):
        agents = tmp_path / "agents"
        agents.mkdir()
        monkeypatch.setattr("metabolon.resources.oscillators._LAUNCH_AGENTS", agents)
        assert _scan_pacemaker_plists() == []

    def test_deduplicates_and_sorts(self, tmp_path: Path, monkeypatch):
        agents = tmp_path / "agents"
        agents.mkdir()
        (agents / "com.vivesca.b.plist").write_bytes(b"")
        (agents / "com.vivesca.a.plist").write_bytes(b"")
        monkeypatch.setattr("metabolon.resources.oscillators._LAUNCH_AGENTS", agents)
        result = _scan_pacemaker_plists()
        assert result[0].name < result[1].name

    def test_finds_terry_pattern(self, tmp_path: Path, monkeypatch):
        agents = tmp_path / "agents"
        agents.mkdir()
        (agents / "com.terry.cron.plist").write_bytes(b"")
        monkeypatch.setattr("metabolon.resources.oscillators._LAUNCH_AGENTS", agents)
        result = _scan_pacemaker_plists()
        assert len(result) == 1
        assert result[0].name == "com.terry.cron.plist"


# ---------------------------------------------------------------------------
# express_pacemaker_status (integration of all pieces)
# ---------------------------------------------------------------------------
class TestExpressPacemakerStatus:
    def test_no_plists_found(self, tmp_path: Path, monkeypatch):
        monkeypatch.setattr(
            "metabolon.resources.oscillators._LAUNCH_AGENTS", tmp_path / "empty"
        )
        output = express_pacemaker_status()
        assert "no com.vivesca.* or com.terry.* plists found" in output

    def test_full_table(self, tmp_path: Path, monkeypatch):
        agents = tmp_path / "agents"
        agents.mkdir()

        # Create a real plist
        plist_data = {
            "Label": "com.vivesca.sync",
            "StartInterval": 300,
            "RunAtLoad": True,
        }
        plist_path = agents / "com.vivesca.sync.plist"
        with plist_path.open("wb") as fh:
            plistlib.dump(plist_data, fh)

        monkeypatch.setattr("metabolon.resources.oscillators._LAUNCH_AGENTS", agents)

        mock_lc_result = {"running": True, "pid": 99, "last_exit": 0, "loaded": True}
        with patch(
            "metabolon.resources.oscillators._launchctl_status",
            return_value=mock_lc_result,
        ):
            output = express_pacemaker_status()

        assert "com.vivesca.sync" in output
        assert "every 5m" in output
        assert "running" in output
        assert "pid 99" in output
        assert "1 agents" in output
        assert "1 running" in output
        # Header row present
        assert "| Label |" in output

    def test_error_agent_counted(self, tmp_path: Path, monkeypatch):
        agents = tmp_path / "agents"
        agents.mkdir()

        plist_data = {"Label": "com.vivesca.fail", "StartInterval": 60}
        plist_path = agents / "com.vivesca.fail.plist"
        with plist_path.open("wb") as fh:
            plistlib.dump(plist_data, fh)

        monkeypatch.setattr("metabolon.resources.oscillators._LAUNCH_AGENTS", agents)

        mock_lc_result = {
            "running": False,
            "pid": None,
            "last_exit": 1,
            "loaded": True,
        }
        with patch(
            "metabolon.resources.oscillators._launchctl_status",
            return_value=mock_lc_result,
        ):
            output = express_pacemaker_status()

        assert "1 errors" in output
        assert "error" in output

    def test_unloaded_agent_counted(self, tmp_path: Path, monkeypatch):
        agents = tmp_path / "agents"
        agents.mkdir()

        plist_data = {"Label": "com.vivesca.off"}
        plist_path = agents / "com.vivesca.off.plist"
        with plist_path.open("wb") as fh:
            plistlib.dump(plist_data, fh)

        monkeypatch.setattr("metabolon.resources.oscillators._LAUNCH_AGENTS", agents)

        mock_lc_result = {
            "running": False,
            "pid": None,
            "last_exit": None,
            "loaded": False,
        }
        with patch(
            "metabolon.resources.oscillators._launchctl_status",
            return_value=mock_lc_result,
        ):
            output = express_pacemaker_status()

        assert "1 unloaded" in output
        assert "unloaded" in output

    def test_corrupt_plist_uses_filename_as_label(self, tmp_path: Path, monkeypatch):
        agents = tmp_path / "agents"
        agents.mkdir()

        # Write invalid plist content
        plist_path = agents / "com.vivesca.corrupt.plist"
        plist_path.write_bytes(b"not a plist")

        monkeypatch.setattr("metabolon.resources.oscillators._LAUNCH_AGENTS", agents)

        mock_lc_result = {
            "running": False,
            "pid": None,
            "last_exit": None,
            "loaded": True,
        }
        with patch(
            "metabolon.resources.oscillators._launchctl_status",
            return_value=mock_lc_result,
        ):
            output = express_pacemaker_status()

        # Falls back to stem name (filename without .plist)
        assert "com.vivesca.corrupt" in output
        assert "parse error" in output

    def test_multiple_agents(self, tmp_path: Path, monkeypatch):
        agents = tmp_path / "agents"
        agents.mkdir()

        for name in ["com.vivesca.alpha", "com.vivesca.beta"]:
            plist_data = {"Label": name, "StartInterval": 60}
            with (agents / f"{name}.plist").open("wb") as fh:
                plistlib.dump(plist_data, fh)

        monkeypatch.setattr("metabolon.resources.oscillators._LAUNCH_AGENTS", agents)

        mock_lc_result = {
            "running": False,
            "pid": None,
            "last_exit": 0,
            "loaded": True,
        }
        with patch(
            "metabolon.resources.oscillators._launchctl_status",
            return_value=mock_lc_result,
        ):
            output = express_pacemaker_status()

        assert "2 agents" in output
        assert "com.vivesca.alpha" in output
        assert "com.vivesca.beta" in output

    def test_symlink_type_shown(self, tmp_path: Path, monkeypatch):
        agents = tmp_path / "agents"
        agents.mkdir()

        plist_data = {"Label": "com.vivesca.linked", "StartInterval": 60}
        real = agents / "real.plist"
        with real.open("wb") as fh:
            plistlib.dump(plist_data, fh)

        link = agents / "com.vivesca.linked.plist"
        link.symlink_to(real)

        monkeypatch.setattr("metabolon.resources.oscillators._LAUNCH_AGENTS", agents)

        mock_lc_result = {
            "running": False,
            "pid": None,
            "last_exit": 0,
            "loaded": True,
        }
        with patch(
            "metabolon.resources.oscillators._launchctl_status",
            return_value=mock_lc_result,
        ):
            output = express_pacemaker_status()

        assert "symlink" in output

    def test_dash_for_none_exit(self, tmp_path: Path, monkeypatch):
        agents = tmp_path / "agents"
        agents.mkdir()

        plist_data = {"Label": "com.vivesca.fresh"}
        with (agents / "com.vivesca.fresh.plist").open("wb") as fh:
            plistlib.dump(plist_data, fh)

        monkeypatch.setattr("metabolon.resources.oscillators._LAUNCH_AGENTS", agents)

        mock_lc_result = {
            "running": False,
            "pid": None,
            "last_exit": None,
            "loaded": True,
        }
        with patch(
            "metabolon.resources.oscillators._launchctl_status",
            return_value=mock_lc_result,
        ):
            output = express_pacemaker_status()

        # Em-dash used for missing exit code
        assert "—" in output
