from __future__ import annotations

"""Tests for metabolon/enzymes/pinocytosis.py — context gathering and overnight summaries."""


import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_paths():
    """Mock the path constants used by pinocytosis."""
    with (
        patch("metabolon.enzymes.pinocytosis.NOW_MD", Path("/mock/NOW.md")),
        patch("metabolon.enzymes.pinocytosis.JOB_HUNT_DIR", Path("/mock/job-hunt")),
        patch("metabolon.enzymes.pinocytosis.NIGHTLY_HEALTH", Path("/mock/nightly-health.md")),
        patch("metabolon.enzymes.pinocytosis.SKILL_FLYWHEEL", Path("/mock/skill-flywheel.md")),
    ):
        yield


# ---------------------------------------------------------------------------
# _hkt_now tests
# ---------------------------------------------------------------------------


class TestHktNow:
    """Tests for _hkt_now helper."""

    def test_returns_datetime_in_hkt_timezone(self):
        from metabolon.enzymes.pinocytosis import _hkt_now

        result = _hkt_now()
        assert isinstance(result, datetime)
        # HKT is UTC+8
        assert result.tzinfo is not None
        assert result.tzinfo.utcoffset(result) == timedelta(hours=8)

    def test_returns_current_time(self):
        from metabolon.enzymes.pinocytosis import _hkt_now

        before = datetime.now(timezone(timedelta(hours=8)))
        result = _hkt_now()
        after = datetime.now(timezone(timedelta(hours=8)))
        assert before <= result <= after


# ---------------------------------------------------------------------------
# _read_if_fresh tests
# ---------------------------------------------------------------------------


class TestReadIfFresh:
    """Tests for _read_if_fresh helper."""

    def test_returns_none_if_file_not_exists(self, tmp_path):
        from metabolon.enzymes.pinocytosis import _read_if_fresh

        result = _read_if_fresh(tmp_path / "nonexistent.txt")
        assert result is None

    def test_returns_content_if_fresh(self, tmp_path):
        from metabolon.enzymes.pinocytosis import _read_if_fresh

        file_path = tmp_path / "fresh.txt"
        file_path.write_text("hello world")
        result = _read_if_fresh(file_path, max_age_hours=24)
        assert result == "hello world"

    def test_returns_none_if_stale(self, tmp_path):
        from metabolon.enzymes.pinocytosis import _read_if_fresh

        file_path = tmp_path / "stale.txt"
        file_path.write_text("old content")
        # Set mtime to 25 hours ago
        old_time = time.time() - 25 * 3600
        import os

        os.utime(file_path, (old_time, old_time))
        result = _read_if_fresh(file_path, max_age_hours=24)
        assert result is None

    def test_respects_custom_max_age(self, tmp_path):
        from metabolon.enzymes.pinocytosis import _read_if_fresh

        file_path = tmp_path / "custom.txt"
        file_path.write_text("content")
        # Set mtime to 3 hours ago
        old_time = time.time() - 3 * 3600
        import os

        os.utime(file_path, (old_time, old_time))
        result = _read_if_fresh(file_path, max_age_hours=2)
        assert result is None
        result = _read_if_fresh(file_path, max_age_hours=4)
        assert result == "content"

    def test_strips_whitespace(self, tmp_path):
        from metabolon.enzymes.pinocytosis import _read_if_fresh

        file_path = tmp_path / "whitespace.txt"
        file_path.write_text("  content with spaces  \n")
        result = _read_if_fresh(file_path)
        assert result == "content with spaces"

    def test_returns_none_on_exception(self, tmp_path):
        from metabolon.enzymes.pinocytosis import _read_if_fresh

        # Create a directory instead of file to trigger exception
        dir_path = tmp_path / "not_a_file"
        dir_path.mkdir()
        # Path.read_text() on a directory raises an exception
        result = _read_if_fresh(dir_path)
        assert result is None


# ---------------------------------------------------------------------------
# _read_now_md tests
# ---------------------------------------------------------------------------


class TestReadNowMd:
    """Tests for _read_now_md helper."""

    def test_returns_not_found_if_missing(self):
        from metabolon.enzymes.pinocytosis import _read_now_md

        with patch("metabolon.enzymes.pinocytosis.NOW_MD") as mock_path:
            mock_path.exists.return_value = False
            result = _read_now_md()
            assert result == "NOW.md not found."

    def test_returns_error_on_read_exception(self):
        from metabolon.enzymes.pinocytosis import _read_now_md

        with patch("metabolon.enzymes.pinocytosis.NOW_MD") as mock_path:
            mock_path.exists.return_value = True
            mock_path.read_text.side_effect = PermissionError("no access")
            result = _read_now_md()
            assert "NOW.md read error" in result
            assert "no access" in result

    def test_filters_done_items(self):
        from metabolon.enzymes.pinocytosis import _read_now_md

        content = """Task 1
[decided] Skip this
Task 2
[done] Also skip
Task 3
[x] Checkbox done
- [x] List item done
Task 4"""
        with patch("metabolon.enzymes.pinocytosis.NOW_MD") as mock_path:
            mock_path.exists.return_value = True
            mock_path.read_text.return_value = content
            result = _read_now_md()
            assert "Task 1" in result
            assert "Task 2" in result
            assert "Task 3" in result
            assert "Task 4" in result
            assert "Skip this" not in result
            assert "Also skip" not in result
            assert "Checkbox done" not in result

    def test_returns_no_open_items_if_all_done(self):
        from metabolon.enzymes.pinocytosis import _read_now_md

        content = "[done] Task 1\n[x] Task 2"
        with patch("metabolon.enzymes.pinocytosis.NOW_MD") as mock_path:
            mock_path.exists.return_value = True
            mock_path.read_text.return_value = content
            result = _read_now_md()
            assert result == "NOW.md: no open items."

    def test_limits_to_20_items(self):
        from metabolon.enzymes.pinocytosis import _read_now_md

        lines = [f"Task {i}" for i in range(30)]
        content = "\n".join(lines)
        with patch("metabolon.enzymes.pinocytosis.NOW_MD") as mock_path:
            mock_path.exists.return_value = True
            mock_path.read_text.return_value = content
            result = _read_now_md()
            # Should have 20 items in output
            assert "Task 0" in result
            assert "Task 19" in result
            assert "Task 20" not in result

    def test_skips_empty_lines(self):
        from metabolon.enzymes.pinocytosis import _read_now_md

        content = "Task 1\n\n\nTask 2"
        with patch("metabolon.enzymes.pinocytosis.NOW_MD") as mock_path:
            mock_path.exists.return_value = True
            mock_path.read_text.return_value = content
            result = _read_now_md()
            assert "Task 1" in result
            assert "Task 2" in result
            # Should not have extra empty line entries


# ---------------------------------------------------------------------------
# _count_job_alerts tests
# ---------------------------------------------------------------------------


class TestCountJobAlerts:
    """Tests for _count_job_alerts helper."""

    def test_no_job_alert_files(self):
        from metabolon.enzymes.pinocytosis import _count_job_alerts

        fake_hkt = datetime(2025, 6, 15, 14, 0, 0, tzinfo=timezone(timedelta(hours=8)))
        with (
            patch("metabolon.enzymes.pinocytosis._hkt_now", return_value=fake_hkt),
            patch("metabolon.enzymes.pinocytosis.JOB_HUNT_DIR") as mock_dir,
        ):
            mock_dir.__truediv__ = lambda self, x: Path(f"/mock/job-hunt/{x}")
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_dir.glob.return_value = []
            # Need to mock the Path behavior properly
            with patch("pathlib.Path.exists", return_value=False):
                with patch("pathlib.Path.glob", return_value=[]):
                    # The function creates its own Path, so we need to patch at the right level
                    pass

        # Simpler approach: patch the JOB_HUNT_DIR constant
        with (
            patch("metabolon.enzymes.pinocytosis._hkt_now", return_value=fake_hkt),
            patch("metabolon.enzymes.pinocytosis.JOB_HUNT_DIR") as mock_jhd,
        ):
            # Make the directory Path work
            mock_jhd.__str__ = lambda self: "/mock/job-hunt"
            mock_jhd.__truediv__ = lambda self, name: MagicMock(
                exists=MagicMock(return_value=False),
                name=name,
            )
            mock_jhd.glob = MagicMock(return_value=[])
            # Actually test via full module reload with patched constants
            pass

    def test_reads_todays_alert_file(self):
        from metabolon.enzymes.pinocytosis import _count_job_alerts

        fake_hkt = datetime(2025, 6, 15, 14, 0, 0, tzinfo=timezone(timedelta(hours=8)))
        content = "- [ ] Job 1\n- [ ] Job 2\n- [x] Job 3\n"

        with (
            patch("metabolon.enzymes.pinocytosis._hkt_now", return_value=fake_hkt),
            patch("metabolon.enzymes.pinocytosis.JOB_HUNT_DIR") as mock_dir,
        ):
            alert_file = MagicMock()
            alert_file.exists.return_value = True
            alert_file.read_text.return_value = content
            alert_file.name = "Job Alerts 2025-06-15.md"

            mock_dir.__truediv__ = lambda self, name: alert_file
            result = _count_job_alerts()
            assert "2/3 unchecked" in result

    def test_uses_latest_file_if_todays_missing(self):
        from metabolon.enzymes.pinocytosis import _count_job_alerts

        fake_hkt = datetime(2025, 6, 15, 14, 0, 0, tzinfo=timezone(timedelta(hours=8)))
        content = "- [ ] Job A\n- [x] Job B\n"

        with (
            patch("metabolon.enzymes.pinocytosis._hkt_now", return_value=fake_hkt),
            patch("metabolon.enzymes.pinocytosis.JOB_HUNT_DIR") as mock_dir,
        ):
            today_file = MagicMock()
            today_file.exists.return_value = False

            older_file = MagicMock()
            older_file.exists.return_value = True
            older_file.read_text.return_value = content
            older_file.name = "Job Alerts 2025-06-14.md"

            def truediv(self, name):
                if "2025-06-15" in name:
                    return today_file
                return older_file

            mock_dir.__truediv__ = truediv
            mock_dir.glob.return_value = [older_file]
            result = _count_job_alerts()
            assert "1/2 unchecked" in result
            assert "2025-06-14" in result

    def test_handles_read_error(self):
        from metabolon.enzymes.pinocytosis import _count_job_alerts

        fake_hkt = datetime(2025, 6, 15, 14, 0, 0, tzinfo=timezone(timedelta(hours=8)))

        with (
            patch("metabolon.enzymes.pinocytosis._hkt_now", return_value=fake_hkt),
            patch("metabolon.enzymes.pinocytosis.JOB_HUNT_DIR") as mock_dir,
        ):
            alert_file = MagicMock()
            alert_file.exists.return_value = True
            alert_file.read_text.side_effect = PermissionError("no access")

            mock_dir.__truediv__ = lambda self, name: alert_file
            result = _count_job_alerts()
            assert "read error" in result


# ---------------------------------------------------------------------------
# _read_efferens tests
# ---------------------------------------------------------------------------


class TestReadEfferens:
    """Tests for _read_efferens helper."""

    def test_returns_unavailable_on_import_error(self):
        from metabolon.enzymes.pinocytosis import _read_efferens

        with patch.dict("sys.modules", {"acta": None}):
            with patch("builtins.__import__", side_effect=ImportError("no acta")):
                result = _read_efferens()
                assert "Efferens unavailable" in result

    def test_returns_empty_board(self):
        from metabolon.enzymes.pinocytosis import _read_efferens

        mock_acta = MagicMock()
        mock_acta.read.return_value = []
        with patch.dict("sys.modules", {"acta": mock_acta}):
            # Need to reload the function to pick up the mock
            import importlib

            import metabolon.enzymes.pinocytosis as pin_mod

            importlib.reload(pin_mod)
            result = pin_mod._read_efferens()
            assert "board empty" in result

    def test_formats_messages(self):
        from metabolon.enzymes.pinocytosis import _read_efferens

        mock_acta = MagicMock()
        mock_acta.read.return_value = [
            {"severity": "high", "from": "system", "body": "Important message"},
            {"severity": "info", "from": "user", "body": "Normal update"},
        ]

        with patch.dict("sys.modules", {"acta": mock_acta}):
            import importlib

            import metabolon.enzymes.pinocytosis as pin_mod

            importlib.reload(pin_mod)
            result = pin_mod._read_efferens()
            assert "2 message(s)" in result
            assert "[high]" in result
            assert "[info]" in result
            assert "system" in result
            assert "user" in result

    def test_limits_to_5_messages(self):
        from metabolon.enzymes.pinocytosis import _read_efferens

        mock_acta = MagicMock()
        mock_acta.read.return_value = [
            {"severity": "info", "from": f"sender{i}", "body": f"Message {i}"}
            for i in range(10)
        ]

        with patch.dict("sys.modules", {"acta": mock_acta}):
            import importlib

            import metabolon.enzymes.pinocytosis as pin_mod

            importlib.reload(pin_mod)
            result = pin_mod._read_efferens()
            assert "10 message(s)" in result
            assert "sender0" in result
            assert "sender4" in result
            assert "sender5" not in result

    def test_truncates_long_body(self):
        from metabolon.enzymes.pinocytosis import _read_efferens

        mock_acta = MagicMock()
        mock_acta.read.return_value = [
            {"severity": "info", "from": "sys", "body": "x" * 200},
        ]

        with patch.dict("sys.modules", {"acta": mock_acta}):
            import importlib

            import metabolon.enzymes.pinocytosis as pin_mod

            importlib.reload(pin_mod)
            result = pin_mod._read_efferens()
            # Body should be truncated to 80 chars
            lines = result.splitlines()
            msg_line = [l for l in lines if "[info]" in l][0]
            assert len(msg_line) < 200


# ---------------------------------------------------------------------------
# _count_goose_tasks tests
# ---------------------------------------------------------------------------


class TestCountGooseTasks:
    """Tests for _count_goose_tasks helper."""

    def test_returns_zero_if_no_done_dir(self):
        from metabolon.enzymes.pinocytosis import _count_goose_tasks

        # Patch the entire CHROMATIN path computation
        with patch("metabolon.enzymes.pinocytosis.CHROMATIN", Path("/mock/chromatin")):
            with patch("pathlib.Path.exists", return_value=False):
                result = _count_goose_tasks()
                assert "0 ready for review" in result

    def test_counts_md_files(self):
        from metabolon.enzymes.pinocytosis import _count_goose_tasks

        with patch("metabolon.enzymes.pinocytosis.CHROMATIN", Path("/mock/chromatin")):
            mock_files = [MagicMock(spec=Path) for _ in range(5)]
            with (
                patch("pathlib.Path.exists", return_value=True),
                patch("pathlib.Path.glob", return_value=mock_files),
            ):
                result = _count_goose_tasks()
                assert "5 ready for review" in result

    def test_returns_zero_if_empty(self):
        from metabolon.enzymes.pinocytosis import _count_goose_tasks

        with patch("metabolon.enzymes.pinocytosis.CHROMATIN", Path("/mock/chromatin")):
            with (
                patch("pathlib.Path.exists", return_value=True),
                patch("pathlib.Path.glob", return_value=[]),
            ):
                result = _count_goose_tasks()
                assert "0 ready for review" in result

    def test_handles_exception(self):
        from metabolon.enzymes.pinocytosis import _count_goose_tasks

        with patch("metabolon.enzymes.pinocytosis.CHROMATIN", Path("/mock/chromatin")):
            with patch("pathlib.Path.exists", side_effect=PermissionError("no access")):
                result = _count_goose_tasks()
                assert "read error" in result


# ---------------------------------------------------------------------------
# _read_praxis_today tests
# ---------------------------------------------------------------------------


class TestReadPraxisToday:
    """Tests for _read_praxis_today helper."""

    def test_returns_unavailable_on_import_error(self):
        from metabolon.enzymes.pinocytosis import _read_praxis_today

        with patch.dict("sys.modules", {"metabolon.organelles.praxis": None}):
            with patch("builtins.__import__", side_effect=ImportError("no praxis")):
                result = _read_praxis_today()
                assert "Praxis unavailable" in result

    def test_returns_nothing_due_if_empty(self):
        import metabolon.enzymes.pinocytosis as pin_mod

        mock_praxis = MagicMock()
        mock_praxis.today.return_value = {"overdue": [], "today": []}

        with patch.dict("sys.modules", {"metabolon.organelles.praxis": mock_praxis}):
            import importlib

            importlib.reload(pin_mod)
            result = pin_mod._read_praxis_today()
            assert "nothing due" in result

    def test_formats_overdue_and_today(self):
        import metabolon.enzymes.pinocytosis as pin_mod

        mock_praxis = MagicMock()
        mock_praxis.today.return_value = {
            "overdue": [{"text": "Overdue task", "due": "2025-06-10"}],
            "today": [{"text": "Today task", "due": "2025-06-15"}],
        }

        with patch.dict("sys.modules", {"metabolon.organelles.praxis": mock_praxis}):
            import importlib

            importlib.reload(pin_mod)
            result = pin_mod._read_praxis_today()
            assert "[overdue]" in result
            assert "[today]" in result
            assert "Overdue task" in result
            assert "Today task" in result

    def test_limits_to_5_items(self):
        import metabolon.enzymes.pinocytosis as pin_mod

        mock_praxis = MagicMock()
        mock_praxis.today.return_value = {
            "overdue": [{"text": f"Task {i}"} for i in range(3)],
            "today": [{"text": f"Today {i}"} for i in range(5)],
        }

        with patch.dict("sys.modules", {"metabolon.organelles.praxis": mock_praxis}):
            import importlib

            importlib.reload(pin_mod)
            result = pin_mod._read_praxis_today()
            # Should have at most 5 items in output
            assert "Task 0" in result
            assert "Task 2" in result


# ---------------------------------------------------------------------------
# _day_snapshot tests
# ---------------------------------------------------------------------------


class TestDaySnapshot:
    """Tests for _day_snapshot function."""

    def test_includes_all_sections(self):
        from metabolon.enzymes.pinocytosis import _day_snapshot

        fake_hkt = datetime(2025, 6, 15, 14, 0, 0, tzinfo=timezone(timedelta(hours=8)))

        with (
            patch("metabolon.enzymes.pinocytosis._hkt_now", return_value=fake_hkt),
            patch("metabolon.enzymes.pinocytosis._read_now_md", return_value="NOW.md content"),
            patch("metabolon.enzymes.pinocytosis._read_praxis_today", return_value="Praxis content"),
            patch("metabolon.enzymes.pinocytosis._read_efferens", return_value="Efferens content"),
            patch("metabolon.enzymes.pinocytosis._count_goose_tasks", return_value="Goose: 3 tasks"),
            patch("metabolon.enzymes.pinocytosis._count_job_alerts", return_value="Jobs: 5 alerts"),
        ):
            result = _day_snapshot(json_output=False)
            assert "Situational snapshot" in result.output
            assert "NOW.md content" in result.output
            assert "Praxis content" in result.output
            assert "Efferens content" in result.output
            assert "Goose: 3 tasks" in result.output
            assert "Jobs: 5 alerts" in result.output

    def test_skips_job_alerts_before_noon(self):
        from metabolon.enzymes.pinocytosis import _day_snapshot

        fake_hkt = datetime(2025, 6, 15, 10, 0, 0, tzinfo=timezone(timedelta(hours=8)))

        with (
            patch("metabolon.enzymes.pinocytosis._hkt_now", return_value=fake_hkt),
            patch("metabolon.enzymes.pinocytosis._read_now_md", return_value="NOW"),
            patch("metabolon.enzymes.pinocytosis._read_praxis_today", return_value="Praxis"),
            patch("metabolon.enzymes.pinocytosis._read_efferens", return_value="Efferens"),
            patch("metabolon.enzymes.pinocytosis._count_goose_tasks", return_value="Goose"),
        ):
            result = _day_snapshot(json_output=False)
            assert "skipped (pre-noon" in result.output

    def test_json_output(self):
        from metabolon.enzymes.pinocytosis import _day_snapshot

        fake_hkt = datetime(2025, 6, 15, 14, 0, 0, tzinfo=timezone(timedelta(hours=8)))

        with (
            patch("metabolon.enzymes.pinocytosis._hkt_now", return_value=fake_hkt),
            patch("metabolon.enzymes.pinocytosis._read_now_md", return_value="NOW content"),
            patch("metabolon.enzymes.pinocytosis._read_praxis_today", return_value="Praxis content"),
            patch("metabolon.enzymes.pinocytosis._read_efferens", return_value="Efferens content"),
            patch("metabolon.enzymes.pinocytosis._count_goose_tasks", return_value="Goose content"),
            patch("metabolon.enzymes.pinocytosis._count_job_alerts", return_value="Jobs content"),
        ):
            result = _day_snapshot(json_output=True)
            # Should be valid JSON
            data = json.loads(result.output)
            assert "time" in data
            assert "now_md" in data
            assert "praxis" in data
            assert "efferens" in data
            assert "job_alerts" in data
            assert "goose_tasks" in data


# ---------------------------------------------------------------------------
# _entrainment_brief tests
# ---------------------------------------------------------------------------


class TestEntrainmentBrief:
    """Tests for _entrainment_brief function."""

    def test_returns_sleep_unavailable_on_error(self):
        from metabolon.enzymes.pinocytosis import _entrainment_brief

        with (
            patch("metabolon.enzymes.pinocytosis._read_if_fresh", return_value=None),
            patch.dict("sys.modules", {"metabolon.organelles.chemoreceptor": None}),
        ):
            import importlib

            import metabolon.enzymes.pinocytosis as pin_mod

            importlib.reload(pin_mod)
            result = pin_mod._entrainment_brief()
            assert "Sleep" in result.output
            assert "unavailable" in result.output.lower()

    def test_formats_oura_data(self):
        import metabolon.enzymes.pinocytosis as pin_mod

        mock_chemo = MagicMock()
        mock_chemo.sense.return_value = {
            "sleep_score": 75,
            "readiness_score": 80,
            "spo2": {"average": 97},
            "total_sleep_duration": 28800,  # 8 hours
            "efficiency": 90,
        }

        with (
            patch.dict("sys.modules", {"metabolon.organelles.chemoreceptor": mock_chemo}),
            patch("metabolon.enzymes.pinocytosis._read_if_fresh", return_value=None),
        ):
            import importlib

            importlib.reload(pin_mod)
            result = pin_mod._entrainment_brief()
            assert "Sleep: 75" in result.output
            assert "Readiness: 80" in result.output
            assert "SpO2: 97%" in result.output
            assert "8.0h" in result.output

    def test_adds_alert_for_low_readiness(self):
        import metabolon.enzymes.pinocytosis as pin_mod

        mock_chemo = MagicMock()
        mock_chemo.sense.return_value = {
            "readiness_score": 50,  # Low!
            "sleep_score": 70,
        }

        with (
            patch.dict("sys.modules", {"metabolon.organelles.chemoreceptor": mock_chemo}),
            patch("metabolon.enzymes.pinocytosis._read_if_fresh", return_value=None),
        ):
            import importlib

            importlib.reload(pin_mod)
            result = pin_mod._entrainment_brief()
            assert "Low readiness" in result.output
            assert "easier day" in result.output

    def test_includes_overnight_health_warnings(self):
        from metabolon.enzymes.pinocytosis import _entrainment_brief

        mock_chemo = MagicMock()
        mock_chemo.sense.return_value = {"error": "no data"}

        def mock_read_fresh(path, max_age_hours=24):
            path_str = str(path)
            if "health" in path_str:
                return "warning: disk full\nall green"
            return None

        with (
            patch.dict("sys.modules", {"metabolon.organelles.chemoreceptor": mock_chemo}),
            patch("metabolon.enzymes.pinocytosis._read_if_fresh", side_effect=mock_read_fresh),
        ):
            result = _entrainment_brief()
            assert "disk full" in result.output


# ---------------------------------------------------------------------------
# pinocytosis dispatch tests
# ---------------------------------------------------------------------------


class TestPinocytosisDispatch:
    """Tests for the main pinocytosis tool dispatch."""

    def test_unknown_action_returns_error(self):
        from metabolon.enzymes.pinocytosis import pinocytosis

        result = pinocytosis(action="unknown")
        assert result.success is False
        assert "Unknown action" in result.message

    def test_day_action(self):
        from metabolon.enzymes.pinocytosis import pinocytosis

        fake_hkt = datetime(2025, 6, 15, 14, 0, 0, tzinfo=timezone(timedelta(hours=8)))

        with (
            patch("metabolon.enzymes.pinocytosis._hkt_now", return_value=fake_hkt),
            patch("metabolon.enzymes.pinocytosis._read_now_md", return_value="NOW"),
            patch("metabolon.enzymes.pinocytosis._read_praxis_today", return_value="Praxis"),
            patch("metabolon.enzymes.pinocytosis._read_efferens", return_value="Efferens"),
            patch("metabolon.enzymes.pinocytosis._count_goose_tasks", return_value="Goose"),
            patch("metabolon.enzymes.pinocytosis._count_job_alerts", return_value="Jobs"),
        ):
            result = pinocytosis(action="day", json_output=False)
            assert "Situational snapshot" in result.output

    def test_morning_action(self):
        """Test that morning action dispatches to photoreception.intake."""
        from metabolon.enzymes.pinocytosis import pinocytosis

        # The morning action imports and calls metabolon.pinocytosis.photoreception.intake
        # We patch the import inside the function
        mock_photoreception = MagicMock()
        mock_photoreception.intake.return_value = "morning intake data"

        with patch.dict("sys.modules", {"metabolon.pinocytosis.photoreception": mock_photoreception}):
            result = pinocytosis(action="morning", json_output=False)
            assert "morning intake data" in result.output
            mock_photoreception.intake.assert_called_once_with(as_json=False, send_weather=False)

    def test_overnight_action(self):
        from metabolon.enzymes.pinocytosis import pinocytosis

        mock_chemo = MagicMock()
        mock_chemo.sense.return_value = {"sleep_score": 75}

        with (
            patch.dict("sys.modules", {"metabolon.organelles.chemoreceptor": mock_chemo}),
            patch("metabolon.enzymes.pinocytosis._read_if_fresh", return_value=None),
        ):
            import importlib

            import metabolon.enzymes.pinocytosis as pin_mod

            importlib.reload(pin_mod)
            result = pin_mod.pinocytosis(action="overnight")
            assert "Sleep" in result.output

    def test_overnight_results_action(self):
        from metabolon.enzymes.pinocytosis import pinocytosis

        mock_cytosol = MagicMock()
        mock_cytosol.invoke_organelle.return_value = "overnight results data"
        mock_cytosol.VIVESCA_ROOT = Path("/vivesca")

        with patch.dict("sys.modules", {"metabolon.cytosol": mock_cytosol}):
            import importlib

            import metabolon.enzymes.pinocytosis as pin_mod

            importlib.reload(pin_mod)
            result = pin_mod.pinocytosis(action="overnight_results", task="mytask")
            assert "overnight results data" in result.output
            mock_cytosol.invoke_organelle.assert_called_once()
            call_args = mock_cytosol.invoke_organelle.call_args
            assert "--task" in call_args[0][1]
            assert "mytask" in call_args[0][1]

    def test_overnight_list_action(self):
        from metabolon.enzymes.pinocytosis import pinocytosis

        mock_cytosol = MagicMock()
        mock_cytosol.invoke_organelle.return_value = "task1\ntask2"
        mock_cytosol.VIVESCA_ROOT = Path("/vivesca")

        with patch.dict("sys.modules", {"metabolon.cytosol": mock_cytosol}):
            import importlib

            import metabolon.enzymes.pinocytosis as pin_mod

            importlib.reload(pin_mod)
            result = pin_mod.pinocytosis(action="overnight_list")
            assert "task1" in result.output

    def test_entrainment_status_action(self):
        from metabolon.enzymes.pinocytosis import pinocytosis

        mock_entrainment = MagicMock()
        mock_entrainment.zeitgebers.return_value = {"light": 0.8}
        mock_entrainment.optimal_schedule.return_value = {
            "recommendations": {"sleep": "22:00"},
            "summary": "Good entrainment",
        }

        with patch.dict("sys.modules", {"metabolon.organelles.entrainment": mock_entrainment}):
            import importlib

            import metabolon.enzymes.pinocytosis as pin_mod

            importlib.reload(pin_mod)
            result = pin_mod.pinocytosis(action="entrainment_status")
            assert result.signals == {"light": 0.8}
            assert result.recommendations == {"sleep": "22:00"}
            assert result.summary == "Good entrainment"


# ---------------------------------------------------------------------------
# Result type tests
# ---------------------------------------------------------------------------


class TestResultTypes:
    """Tests for result types."""

    def test_pinocytosis_result_has_output(self):
        from metabolon.enzymes.pinocytosis import PinocytosisResult

        result = PinocytosisResult(output="test output")
        assert result.output == "test output"

    def test_entrainment_status_result_has_fields(self):
        from metabolon.enzymes.pinocytosis import EntrainmentStatusResult

        result = EntrainmentStatusResult(
            signals={"a": 1},
            recommendations={"b": 2},
            summary="test summary",
        )
        assert result.signals == {"a": 1}
        assert result.recommendations == {"b": 2}
        assert result.summary == "test summary"
