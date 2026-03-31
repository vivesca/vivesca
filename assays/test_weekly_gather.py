"""Tests for effectors/weekly-gather — deterministic session-close gathering.

All filesystem and subprocess calls are mocked.  Because the module is loaded
via exec(), every function shares a single __globals__ dict (the exec
namespace).  We access it through ``wg.gather_quarterly.__globals__`` and use
``patch.dict`` / direct assignment to override NOTES, _gather, time, etc.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "effectors" / "weekly-gather"


@pytest.fixture()
def wg():
    """Load weekly-gather via exec into an isolated namespace."""
    ns: dict = {"__name__": "wg_module"}
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    exec(source, ns)
    mod = type("wg_module", (), {})()
    for k, v in ns.items():
        if not k.startswith("__"):
            setattr(mod, k, v)
    return mod


@pytest.fixture()
def g(wg):
    """Return the shared exec-namespace globals dict for patching."""
    return wg.gather_quarterly.__globals__


# ── Module basics ────────────────────────────────────────────────────────────


class TestScriptBasics:
    def test_script_exists(self):
        assert SCRIPT_PATH.exists()
        assert SCRIPT_PATH.is_file()

    def test_has_main_function(self, wg):
        assert callable(wg.main)

    def test_has_run_all(self, wg):
        assert callable(wg.run_all)

    def test_has_render_text(self, wg):
        assert callable(wg.render_text)

    def test_constants(self, wg):
        assert wg.HOME == Path.home()
        assert wg.NOTES == Path.home() / "notes"


# ── CLI / argparse ──────────────────────────────────────────────────────────


class TestCLIArgparse:
    def test_help_exits_0(self, wg, capsys):
        with patch("sys.argv", ["weekly-gather", "--help"]):
            with pytest.raises(SystemExit) as exc:
                wg.main()
        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert "weekly" in out.lower()

    def test_unknown_flag_exits_2(self, wg, capsys):
        with patch("sys.argv", ["weekly-gather", "--nonexistent"]):
            with pytest.raises(SystemExit) as exc:
                wg.main()
        assert exc.value.code == 2

    def test_default_runs_run_all(self, wg, g, capsys):
        fake_results = {
            "calendar": {"summary": "0 events"},
            "todo": {"summary": "0 due"},
            "now": {"summary": "0 open"},
            "quarterly": {"summary": "Q1 note"},
            "daily": {"summary": "7/7 notes"},
            "oura": {"summary": "Sleep N/A"},
            "job_alerts": {"summary": "0 unchecked"},
            "garden": {"summary": "0 posts"},
        }
        with patch.dict(g, {"run_all": MagicMock(return_value=fake_results)}), \
             patch("sys.argv", ["weekly-gather"]):
            wg.main()
        out = capsys.readouterr().out
        assert "Weekly Context" in out
        assert "0 events" in out

    def test_json_flag_outputs_json(self, wg, g, capsys):
        fake_results = {
            "calendar": {"summary": "cal", "total": 0, "raw": {}},
            "todo": {"summary": "todo"},
            "now": {"summary": "now"},
            "quarterly": {"summary": "q"},
            "daily": {"summary": "d"},
            "oura": {"summary": "o"},
            "job_alerts": {"summary": "j"},
            "garden": {"summary": "g"},
        }
        with patch.dict(g, {"run_all": MagicMock(return_value=fake_results)}), \
             patch("sys.argv", ["weekly-gather", "--json"]):
            wg.main()
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["calendar"]["summary"] == "cal"
        assert data["garden"]["summary"] == "g"


# ── Lazy gather-lib import ──────────────────────────────────────────────────


class TestLazyGatherImport:
    def test_load_gather_returns_false_when_missing(self, wg, g):
        """When ~/code/vivesca/lib/gather.py doesn't exist, _load_gather returns False."""
        g["_gather"] = None
        with patch.dict("sys.modules", {}, clear=False):
            result = wg._load_gather()
        assert result is False

    def test_load_gather_caches_result(self, wg, g):
        """Second call should return the cached result without re-importing."""
        g["_gather"] = False  # pre-set cache
        assert wg._load_gather() is False

    def test_load_gather_returns_module_when_present(self, wg, g):
        """When the gather module is importable, return it."""
        g["_gather"] = None
        fake_mod = MagicMock()
        with patch.dict("sys.modules", {"gather": fake_mod}):
            result = wg._load_gather()
        assert result is fake_mod


# ── gather_calendar ─────────────────────────────────────────────────────────


class TestGatherCalendar:
    def test_unavailable_when_no_gather_lib(self, wg, g):
        g["_gather"] = False
        result = wg.gather_calendar()
        assert result["total"] == 0
        assert "unavailable" in result["summary"].lower()

    def test_returns_events_from_gather_lib(self, wg, g):
        fake_lib = MagicMock()
        fake_lib.get_calendar.return_value = {
            "available": True,
            "events": [
                {"date": "2026-04-06", "title": "standup"},
                {"date": "2026-04-07", "title": "review"},
                {"date": "2026-04-06", "title": "lunch"},
            ],
        }
        g["_gather"] = fake_lib
        result = wg.gather_calendar()
        assert result["total"] == 3
        assert "3 events" in result["summary"]

    def test_no_events(self, wg, g):
        fake_lib = MagicMock()
        fake_lib.get_calendar.return_value = {"available": True, "events": []}
        g["_gather"] = fake_lib
        result = wg.gather_calendar()
        assert result["total"] == 0
        assert "0 events" in result["summary"]

    def test_unavailable_calendar(self, wg, g):
        fake_lib = MagicMock()
        fake_lib.get_calendar.return_value = {"available": False}
        g["_gather"] = fake_lib
        result = wg.gather_calendar()
        assert result["total"] == 0


# ── gather_todo ─────────────────────────────────────────────────────────────


class TestGatherTodo:
    def test_unavailable_when_no_gather_lib(self, wg, g):
        g["_gather"] = False
        result = wg.gather_todo()
        assert result["due_this_week"] == 0
        assert "unavailable" in result["summary"].lower()

    def test_counts_items(self, wg, g):
        fake_lib = MagicMock()
        fake_lib.read_todo.return_value = {
            "available": True,
            "items": [
                {"done": True},
                {"done": False, "due": None, "when": "someday"},
                {"done": False, "due": None, "when": None},
            ],
        }
        g["_gather"] = fake_lib
        result = wg.gather_todo()
        assert result["completed"] == 1
        assert result["someday"] == 1

    def test_overdue_items(self, wg, g):
        fake_lib = MagicMock()
        fake_lib.read_todo.return_value = {
            "available": True,
            "items": [
                {"done": False, "due": "2020-01-01", "when": None},
            ],
        }
        g["_gather"] = fake_lib
        result = wg.gather_todo()
        assert result["overdue"] == 1
        assert "1 overdue" in result["summary"]

    def test_not_available(self, wg, g):
        fake_lib = MagicMock()
        fake_lib.read_todo.return_value = {"available": False, "items": []}
        g["_gather"] = fake_lib
        result = wg.gather_todo()
        assert result["due_this_week"] == 0


# ── gather_now ──────────────────────────────────────────────────────────────


class TestGatherNow:
    def test_unavailable_when_no_gather_lib(self, wg, g):
        g["_gather"] = False
        result = wg.gather_now()
        assert result["open_items"] == 0
        assert "unavailable" in result["summary"].lower()

    def test_counts_open_items(self, wg, g):
        fake_lib = MagicMock()
        fake_lib.read_now.return_value = {"progress": ["a", "b", "c"]}
        g["_gather"] = fake_lib
        result = wg.gather_now()
        assert result["open_items"] == 3
        assert "3 open items" in result["summary"]


# ── gather_quarterly ────────────────────────────────────────────────────────


class TestGatherQuarterly:
    def test_found(self, wg, g, tmp_path):
        q_dir = tmp_path / "Quarterly"
        q_dir.mkdir()
        (q_dir / "2026-Q1.md").write_text("# Q1 Goals")
        with patch.dict(g, {"NOTES": tmp_path}):
            result = wg.gather_quarterly()
        assert result["found"] is True
        assert "Q1 2026" in result["summary"]
        assert result["content"] == "# Q1 Goals"

    def test_not_found(self, wg, g, tmp_path):
        with patch.dict(g, {"NOTES": tmp_path}):
            result = wg.gather_quarterly()
        assert result["found"] is False
        assert "NOT found" in result["summary"]

    def test_correct_quarter_calculation(self, wg, g, tmp_path):
        """Verify quarter is calculated from current month."""
        now = datetime.now()
        expected_q = (now.month - 1) // 3 + 1
        with patch.dict(g, {"NOTES": tmp_path}):
            result = wg.gather_quarterly()
        assert result["quarter"] == f"Q{expected_q} {now.year}"


# ── gather_daily ────────────────────────────────────────────────────────────


class TestGatherDaily:
    def test_no_daily_notes(self, wg, g, tmp_path):
        with patch.dict(g, {"NOTES": tmp_path}):
            result = wg.gather_daily()
        assert result["notes_found"] == 0
        assert result["commute_closes"] == 0
        assert "0/7 daily notes" in result["summary"]

    def test_counts_notes_and_commute_closes(self, wg, g, tmp_path):
        daily_dir = tmp_path / "Daily"
        daily_dir.mkdir()
        today = datetime.now().date()
        # Write a daily note from yesterday with a Commute Close section
        yesterday = today - timedelta(days=1)
        note = daily_dir / f"{yesterday.strftime('%Y-%m-%d')}.md"
        note.write_text(
            "## Commute Close\n- Did stuff\n- More stuff\n## Other Section\n"
        )
        with patch.dict(g, {"NOTES": tmp_path}):
            result = wg.gather_daily()
        assert result["notes_found"] == 1
        assert result["commute_closes"] == 1
        assert "1/7" in result["summary"]

    def test_extracts_session_headers(self, wg, g, tmp_path):
        daily_dir = tmp_path / "Daily"
        daily_dir.mkdir()
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        note = daily_dir / f"{yesterday.strftime('%Y-%m-%d')}.md"
        note.write_text("### 09:00 Morning session\n### 14:30 Afternoon\n### Not a session\n")
        with patch.dict(g, {"NOTES": tmp_path}):
            result = wg.gather_daily()
        # Should have extracted 2 time-stamped headers
        day_data = [d for d in result["daily_data"]
                    if d["date"] == yesterday.strftime("%Y-%m-%d")][0]
        assert len(day_data["session_headers"]) == 2


# ── gather_oura ─────────────────────────────────────────────────────────────


class TestGatherOura:
    def test_no_sopor_command(self, wg, g):
        """When sopor is not installed, returns N/A values."""
        mock_run = MagicMock(return_value=(-1, "", "not found"))
        with patch.dict(g, {"run_cmd": mock_run}):
            result = wg.gather_oura()
        assert result["sleep_avg"] == "N/A"
        assert result["hrv_avg"] == "N/A"
        assert result["readiness_avg"] == "N/A"

    def test_parses_sopor_week_output(self, wg, g):
        output = (
            "Readiness  │ 82\n"
            "Sleep Duration │ 7.5h\n"
            "Avg HRV     │ 45ms\n"
        )
        mock_run = MagicMock(return_value=(0, output, ""))
        with patch.dict(g, {"run_cmd": mock_run}):
            result = wg.gather_oura()
        assert result["sleep_avg"] == "7.5h"
        assert result["hrv_avg"] == "45ms"
        assert result["readiness_avg"] == "82"

    def test_fallback_trend_output(self, wg, g):
        """When 'sopor trend' fails, falls back to 'sopor week'."""
        week_output = "Sleep Duration │ 6.0h\n"
        call_count = 0

        def mock_run_cmd(cmd, timeout=15):
            nonlocal call_count
            call_count += 1
            if "trend" in cmd:
                return (1, "", "no trend data")
            return (0, week_output, "")

        mock_run = MagicMock(side_effect=mock_run_cmd)
        with patch.dict(g, {"run_cmd": mock_run}):
            result = wg.gather_oura()
        assert call_count == 2
        assert result["sleep_avg"] == "6.0h"


# ── gather_job_alerts ───────────────────────────────────────────────────────


class TestGatherJobAlerts:
    def test_no_job_hunting_dir(self, wg, g, tmp_path):
        with patch.dict(g, {"NOTES": tmp_path}):
            result = wg.gather_job_alerts()
        assert result["unchecked"] == 0

    def test_counts_unchecked(self, wg, g, tmp_path):
        jh_dir = tmp_path / "Job Hunting"
        jh_dir.mkdir()
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        note = jh_dir / f"Job Alerts {yesterday.strftime('%Y-%m-%d')}.md"
        note.write_text("- [ ] Apply to Foo\n- [x] Applied to Bar\n- [ ] Apply to Baz\n")
        with patch.dict(g, {"NOTES": tmp_path}):
            result = wg.gather_job_alerts()
        assert result["unchecked"] == 2
        assert "2 unchecked" in result["summary"]


# ── gather_garden ───────────────────────────────────────────────────────────


class TestGatherGarden:
    def test_no_published_dir(self, wg, g, tmp_path):
        fake_time = MagicMock()
        fake_time.time.return_value = 1000000.0
        fake_time.return_value = 1000000.0
        with patch.dict(g, {"NOTES": tmp_path, "time": fake_time}):
            result = wg.gather_garden()
        assert result["count"] == 0

    def test_counts_recent_posts(self, wg, g, tmp_path):
        garden = tmp_path / "Writing" / "Blog" / "Published"
        garden.mkdir(parents=True)
        now_ts = 1000000.0
        (garden / "old.md").write_text("old")
        os.utime(garden / "old.md", (now_ts - 8 * 86400, now_ts - 8 * 86400))
        (garden / "recent.md").write_text("new")
        os.utime(garden / "recent.md", (now_ts, now_ts))
        (garden / "also_new.md").write_text("also new")
        os.utime(garden / "also_new.md", (now_ts, now_ts))
        # non-md file should be ignored
        (garden / "image.png").write_bytes(b"png")
        os.utime(garden / "image.png", (now_ts, now_ts))

        fake_time = MagicMock()
        fake_time.time.return_value = now_ts
        fake_time.return_value = now_ts
        with patch.dict(g, {"NOTES": tmp_path, "time": fake_time}):
            result = wg.gather_garden()
        assert result["count"] == 2
        assert "recent" in result["posts"]
        assert "also_new" in result["posts"]
        assert "old" not in result["posts"]


# ── run_all ─────────────────────────────────────────────────────────────────


class TestRunAll:
    def test_run_all_returns_all_keys(self, wg, g):
        # Ensure _gather is False so gather-lib functions degrade gracefully
        g["_gather"] = False
        result = wg.run_all()
        expected_keys = {
            "calendar", "todo", "now", "quarterly",
            "daily", "oura", "job_alerts", "garden",
        }
        assert set(result.keys()) == expected_keys

    def test_run_all_each_has_summary(self, wg, g):
        g["_gather"] = False
        result = wg.run_all()
        for key, val in result.items():
            assert "summary" in val, f"Missing 'summary' in gatherer '{key}'"

    def test_run_all_catches_exceptions(self, wg, g):
        """If a gatherer raises, run_all should catch it and store an error."""
        def bad_gatherer():
            raise RuntimeError("boom")

        g["_gather"] = False
        with patch.dict(g, {"gather_calendar": bad_gatherer}):
            result = wg.run_all()
        assert "error" in result["calendar"]
        assert "boom" in result["calendar"]["error"]


# ── render_text ─────────────────────────────────────────────────────────────


class TestRenderText:
    def test_renders_all_sections(self, wg):
        results = {
            "calendar": {"summary": "5 events"},
            "todo": {"summary": "3 due"},
            "now": {"summary": "1 open"},
            "quarterly": {"summary": "Q1 found"},
            "daily": {"summary": "7/7 notes"},
            "oura": {"summary": "Sleep 7h"},
            "job_alerts": {"summary": "2 unchecked"},
            "garden": {"summary": "1 post"},
        }
        text = wg.render_text(results)
        assert "Weekly Context" in text
        assert "5 events" in text
        assert "3 due" in text
        assert "1 open" in text
        assert "Q1 found" in text
        assert "7/7 notes" in text
        assert "Sleep 7h" in text
        assert "2 unchecked" in text
        assert "1 post" in text

    def test_render_text_has_decorators(self, wg):
        results = {k: {"summary": "x"} for k in
                   ["calendar", "todo", "now", "quarterly", "daily", "oura", "job_alerts", "garden"]}
        text = wg.render_text(results)
        assert "───" in text
        assert "────" in text  # closing line


# ── run_cmd helper ──────────────────────────────────────────────────────────


class TestRunCmd:
    def test_success(self, wg):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "out"
        mock_result.stderr = "err"
        with patch("subprocess.run", return_value=mock_result):
            rc, out, err = wg.run_cmd(["echo", "hi"])
        assert rc == 0
        assert out == "out"

    def test_timeout(self, wg):
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 15)):
            rc, out, err = wg.run_cmd(["slow"], timeout=15)
        assert rc == -1
        assert out == ""

    def test_generic_exception(self, wg):
        with patch("subprocess.run", side_effect=OSError("nope")):
            rc, out, err = wg.run_cmd(["bad"])
        assert rc == -1
        assert "nope" in err
