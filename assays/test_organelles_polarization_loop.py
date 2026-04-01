from __future__ import annotations

"""Tests for metabolon.organelles.polarization_loop."""

import json
import sqlite3
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

import metabolon.organelles.polarization_loop as pl


# ---------------------------------------------------------------------------
# _channel
# ---------------------------------------------------------------------------


class TestChannel:
    """Tests for _channel()."""

    @patch.object(pl, "subprocess")
    def test_success_returns_stdout(self, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "  hello world  "
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        out = pl._channel("sonnet", "do stuff")
        assert out == "hello world"
        cmd = mock_subprocess.run.call_args[0][0]
        assert cmd == ["channel", "sonnet", "-p", "do stuff"]

    @patch.object(pl, "subprocess")
    def test_organism_flag(self, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        pl._channel("opus", "go", organism=True)
        cmd = mock_subprocess.run.call_args[0][0]
        assert "--organism" in cmd

    @patch.object(pl, "subprocess")
    def test_error_returns_error_string(self, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "bad things happened"
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        out = pl._channel("sonnet", "fail")
        assert out.startswith("(channel error: exit 1)")
        assert "bad things" in out

    @patch.object(pl, "subprocess")
    def test_timeout_returns_timeout_string(self, mock_subprocess):
        mock_subprocess.run.side_effect = subprocess.TimeoutExpired(cmd="channel", timeout=300)
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        out = pl._channel("sonnet", "slow", timeout=300)
        assert "(channel timeout after 300s)" == out

    @patch.object(pl, "subprocess")
    def test_strips_claudecode_from_env(self, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ok"
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        with patch.dict("os.environ", {"CLAUDECODE": "1"}, clear=False):
            pl._channel("sonnet", "test")
        env_arg = mock_subprocess.run.call_args[1]["env"]
        assert "CLAUDECODE" not in env_arg


# ---------------------------------------------------------------------------
# _read_file
# ---------------------------------------------------------------------------


class TestReadFile:
    """Tests for _read_file()."""

    def test_existing_file(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("hello world", encoding="utf-8")
        assert pl._read_file(f) == "hello world"

    def test_truncates_to_max_chars(self, tmp_path):
        f = tmp_path / "big.txt"
        f.write_text("x" * 5000, encoding="utf-8")
        assert len(pl._read_file(f, max_chars=1000)) == 1000

    def test_missing_file_returns_empty(self):
        assert pl._read_file(Path("/nonexistent/file.md")) == ""


# ---------------------------------------------------------------------------
# _budget_status
# ---------------------------------------------------------------------------


class TestBudgetStatus:
    """Tests for _budget_status()."""

    @patch.object(pl, "subprocess")
    def test_green_under_50(self, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"seven_day": {"utilization": 30}})
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        assert pl._budget_status() == "green"

    @patch.object(pl, "subprocess")
    def test_yellow_50_to_79(self, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"seven_day": {"utilization": 60}})
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        assert pl._budget_status() == "yellow"

    @patch.object(pl, "subprocess")
    def test_red_80_plus(self, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"seven_day": {"utilization": 85}})
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        assert pl._budget_status() == "red"

    @patch.object(pl, "subprocess")
    def test_nonzero_returncode_defaults_green(self, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        assert pl._budget_status() == "green"

    @patch.object(pl, "subprocess")
    def test_json_error_defaults_green(self, mock_subprocess):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "not json"
        mock_subprocess.run.return_value = mock_result
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        assert pl._budget_status() == "green"

    @patch.object(pl, "subprocess")
    def test_exception_defaults_green(self, mock_subprocess):
        mock_subprocess.run.side_effect = Exception("boom")
        mock_subprocess.TimeoutExpired = subprocess.TimeoutExpired

        assert pl._budget_status() == "green"


# ---------------------------------------------------------------------------
# _consumption_count
# ---------------------------------------------------------------------------


class TestConsumptionCount:
    """Tests for _consumption_count()."""

    def test_missing_dir_returns_zero(self):
        with patch.object(pl, "REPORTS_DIR", Path("/nonexistent/dir/for/test")):
            assert pl._consumption_count() == 0

    def test_counts_recent_files(self, tmp_path):
        with patch.object(pl, "REPORTS_DIR", tmp_path):
            # old file (> 7 days)
            old = tmp_path / "old.md"
            old.write_text("x")
            import os
            # set mtime to 10 days ago
            os.utime(str(old), (time.time() - 10 * 86400,) * 2)

            # recent file
            recent = tmp_path / "recent.md"
            recent.write_text("y")

            assert pl._consumption_count() == 1


# ---------------------------------------------------------------------------
# preflight
# ---------------------------------------------------------------------------


class TestPreflight:
    """Tests for preflight()."""

    @patch.object(pl, "_consumption_count", return_value=2)
    @patch.object(pl, "_budget_status", return_value="green")
    @patch.object(pl, "_read_file", return_value="file content")
    @patch.object(pl, "praxis")
    @patch.object(pl, "GUARD_FILE", MagicMock(spec=Path))
    def test_preflight_populates_context(
        self, mock_guard, mock_praxis, mock_read, mock_budget, mock_consumption,
    ):
        mock_praxis.exists.return_value = True
        mock_praxis.read_text.return_value = "line1\nline2\n" * 50

        state: pl.PolarizationState = {
            "systole_num": 0,
            "mode": "overnight",
            "budget_status": "green",
            "consumption_count": 0,
            "north_stars": "",
            "praxis_items": "",
            "shapes": "",
            "division": "",
            "now_md": "",
            "sub_goals": [],
            "dispatched_work": [],
            "archived": [],
            "follow_ons": [],
            "gate_results": {},
            "total_produced": 0,
            "total_for_review": 0,
            "should_stop": False,
            "stop_reason": "",
            "report": "",
            "errors": [],
        }

        result = pl.preflight(state)
        assert result["systole_num"] == 1
        assert result["budget_status"] == "green"
        assert result["consumption_count"] == 2

    @patch.object(pl, "_consumption_count", return_value=0)
    @patch.object(pl, "_budget_status", return_value="green")
    @patch.object(pl, "_read_file", return_value="")
    @patch.object(pl, "praxis")
    @patch.object(pl, "GUARD_FILE", MagicMock(spec=Path))
    def test_preflight_no_praxis(
        self, mock_guard, mock_praxis, mock_read, mock_budget, mock_consumption,
    ):
        mock_praxis.exists.return_value = False

        result = pl.preflight({"systole_num": 3})
        assert result["systole_num"] == 4
        assert result["praxis_items"] == ""


# ---------------------------------------------------------------------------
# brainstorm
# ---------------------------------------------------------------------------


class TestBrainstorm:
    """Tests for brainstorm()."""

    @patch.object(pl, "_channel")
    def test_parses_json_goals(self, mock_channel):
        goals = [
            {"star": "research", "goal": "write paper", "deliverable": "/tmp/paper.md", "model": "opus"},
            {"star": "code", "goal": "build tool", "deliverable": "/tmp/tool.py", "model": "sonnet"},
        ]
        mock_channel.return_value = json.dumps(goals)

        state: pl.PolarizationState = {
            "mode": "overnight",
            "systole_num": 1,
            "consumption_count": 0,
            "budget_status": "green",
            "north_stars": "star1\nstar2",
            "praxis_items": "todo1",
            "shapes": "shapes",
            "division": "division",
            "now_md": "now",
            "total_produced": 0,
            "sub_goals": [],
            "dispatched_work": [],
            "archived": [],
            "follow_ons": [],
            "gate_results": {},
            "total_for_review": 0,
            "should_stop": False,
            "stop_reason": "",
            "report": "",
            "errors": [],
        }

        result = pl.brainstorm(state)
        assert len(result["sub_goals"]) == 2
        assert result["sub_goals"][0]["star"] == "research"

    @patch.object(pl, "_channel")
    def test_extracts_json_from_surrounding_text(self, mock_channel):
        goals = [{"star": "s", "goal": "g", "deliverable": "d", "model": "sonnet"}]
        mock_channel.return_value = f"Here are the goals:\n{json.dumps(goals)}\nDone."

        state = {"mode": "overnight", "systole_num": 1, "consumption_count": 0,
                 "budget_status": "green", "north_stars": "", "praxis_items": "",
                 "shapes": "", "division": "", "now_md": "", "total_produced": 0}

        result = pl.brainstorm(state)
        assert len(result["sub_goals"]) == 1

    @patch.object(pl, "_channel")
    def test_bad_json_returns_error(self, mock_channel):
        mock_channel.return_value = "[not valid json at all]"

        state = {"mode": "overnight", "systole_num": 1, "consumption_count": 0,
                 "budget_status": "green", "north_stars": "", "praxis_items": "",
                 "shapes": "", "division": "", "now_md": "", "total_produced": 0}

        result = pl.brainstorm(state)
        assert "errors" in result
        assert "Brainstorm failed" in result["errors"][0]

    @patch.object(pl, "_channel")
    def test_overnight_caps_at_8(self, mock_channel):
        goals = [{"star": f"s{i}", "goal": f"g{i}", "deliverable": f"d{i}", "model": "sonnet"}
                 for i in range(20)]
        mock_channel.return_value = json.dumps(goals)

        state = {"mode": "overnight", "systole_num": 1, "consumption_count": 0,
                 "budget_status": "green", "north_stars": "", "praxis_items": "",
                 "shapes": "", "division": "", "now_md": "", "total_produced": 0}

        result = pl.brainstorm(state)
        assert len(result["sub_goals"]) == 8

    @patch.object(pl, "_channel")
    def test_interactive_caps_at_5(self, mock_channel):
        goals = [{"star": f"s{i}", "goal": f"g{i}", "deliverable": f"d{i}", "model": "sonnet"}
                 for i in range(20)]
        mock_channel.return_value = json.dumps(goals)

        state = {"mode": "interactive", "systole_num": 1, "consumption_count": 0,
                 "budget_status": "green", "north_stars": "", "praxis_items": "",
                 "shapes": "", "division": "", "now_md": "", "total_produced": 0}

        result = pl.brainstorm(state)
        assert len(result["sub_goals"]) == 5


# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------


class TestDispatch:
    """Tests for dispatch()."""

    @patch.object(pl, "_channel")
    @patch.object(pl, "MANIFEST_FILE")
    def test_dispatches_each_goal(self, mock_manifest, mock_channel):
        mock_manifest.exists.return_value = False
        mock_channel.return_value = "task output"

        sub_goals = [
            {"goal": "task1", "star": "research", "model": "sonnet", "deliverable": "/tmp/a.md"},
            {"goal": "task2", "star": "code", "model": "opus", "deliverable": "/tmp/b.py"},
        ]

        state: pl.PolarizationState = {
            "sub_goals": sub_goals,
            "systole_num": 1,
            "dispatched_work": [],
            "archived": [],
            "follow_ons": [],
            "gate_results": {},
            "total_produced": 0,
            "total_for_review": 0,
            "should_stop": False,
            "stop_reason": "",
            "report": "",
            "errors": [],
            "mode": "overnight",
            "consumption_count": 0,
            "budget_status": "green",
            "north_stars": "",
            "praxis_items": "",
            "shapes": "",
            "division": "",
            "now_md": "",
        }

        result = pl.dispatch(state)
        assert len(result["dispatched_work"]) == 2
        assert result["dispatched_work"][0]["success"] is True
        assert mock_channel.call_count == 2

    @patch.object(pl, "_channel")
    def test_no_goals_returns_error(self, mock_channel):
        result = pl.dispatch({"sub_goals": [], "systole_num": 1})
        assert "errors" in result
        assert "No goals to dispatch" in result["errors"]

    @patch.object(pl, "_channel")
    @patch.object(pl, "MANIFEST_FILE")
    def test_channel_failure_marked_failed(self, mock_manifest, mock_channel):
        mock_manifest.exists.return_value = False
        mock_channel.return_value = "(channel error: exit 1) something broke"

        state = {"sub_goals": [{"goal": "fail", "star": "s", "model": "sonnet", "deliverable": "d"}],
                 "systole_num": 1}

        result = pl.dispatch(state)
        assert result["dispatched_work"][0]["success"] is False

    @patch.object(pl, "_channel")
    @patch.object(pl, "MANIFEST_FILE")
    def test_appends_to_existing_manifest(self, mock_manifest, mock_channel):
        mock_manifest.exists.return_value = True
        mock_manifest.read_text.return_value = "# Existing\n"
        mock_channel.return_value = "ok"

        state = {"sub_goals": [{"goal": "g", "star": "s", "model": "sonnet", "deliverable": "d"}],
                 "systole_num": 2}

        pl.dispatch(state)
        mock_manifest.write_text.assert_called_once()
        written = mock_manifest.write_text.call_args[0][0]
        assert "# Existing" in written
        assert "systole 2" in written


# ---------------------------------------------------------------------------
# quality_gate
# ---------------------------------------------------------------------------


class TestQualityGate:
    """Tests for quality_gate()."""

    @patch.object(pl, "_channel")
    def test_classifies_self_sufficient(self, mock_channel):
        evals = [
            {"goal": "g1", "classification": "self-sufficient", "quality": "pass"},
            {"goal": "g2", "classification": "needs-review", "quality": "partial"},
        ]
        mock_channel.return_value = json.dumps(evals)

        state: pl.PolarizationState = {
            "dispatched_work": [
                {"success": True, "star": "s1", "goal": "g1", "output": "out1"},
                {"success": True, "star": "s2", "goal": "g2", "output": "out2"},
            ],
            "total_produced": 0,
            "total_for_review": 0,
            "mode": "overnight",
            "consumption_count": 0,
            "budget_status": "green",
            "north_stars": "",
            "praxis_items": "",
            "shapes": "",
            "division": "",
            "now_md": "",
            "systole_num": 1,
            "sub_goals": [],
            "archived": [],
            "follow_ons": [],
            "gate_results": {},
            "should_stop": False,
            "stop_reason": "",
            "report": "",
            "errors": [],
        }

        result = pl.quality_gate(state)
        assert result["total_produced"] == 2
        assert result["total_for_review"] == 1

    def test_no_successful_work(self):
        state: pl.PolarizationState = {
            "dispatched_work": [
                {"success": False, "star": "s", "goal": "g", "output": "(error)"},
            ],
            "total_produced": 5,
            "total_for_review": 1,
            "mode": "overnight",
            "consumption_count": 0,
            "budget_status": "green",
            "north_stars": "",
            "praxis_items": "",
            "shapes": "",
            "division": "",
            "now_md": "",
            "systole_num": 1,
            "sub_goals": [],
            "archived": [],
            "follow_ons": [],
            "gate_results": {},
            "should_stop": False,
            "stop_reason": "",
            "report": "",
            "errors": [],
        }

        result = pl.quality_gate(state)
        assert result["total_produced"] == 5
        assert result["total_for_review"] == 1

    @patch.object(pl, "_channel")
    def test_bad_eval_json_passes_through(self, mock_channel):
        mock_channel.return_value = "garbage"

        state: pl.PolarizationState = {
            "dispatched_work": [
                {"success": True, "star": "s", "goal": "g", "output": "out"},
            ],
            "total_produced": 0,
            "total_for_review": 0,
            "mode": "overnight",
            "consumption_count": 0,
            "budget_status": "green",
            "north_stars": "",
            "praxis_items": "",
            "shapes": "",
            "division": "",
            "now_md": "",
            "systole_num": 1,
            "sub_goals": [],
            "archived": [],
            "follow_ons": [],
            "gate_results": {},
            "should_stop": False,
            "stop_reason": "",
            "report": "",
            "errors": [],
        }

        result = pl.quality_gate(state)
        assert result["total_produced"] == 1
        assert result["total_for_review"] == 0


# ---------------------------------------------------------------------------
# compound_and_scout
# ---------------------------------------------------------------------------


class TestCompoundAndScout:
    """Tests for compound_and_scout()."""

    @patch.object(pl, "_channel")
    def test_returns_follow_ons(self, mock_channel):
        follow_ons = [
            {"goal": "next step", "star": "research", "deliverable": "d", "model": "sonnet", "type": "compound"},
        ]
        mock_channel.return_value = json.dumps(follow_ons)

        state: pl.PolarizationState = {
            "dispatched_work": [
                {"success": True, "star": "s", "goal": "g", "output": "out"},
            ],
            "systole_num": 1,
            "north_stars": "stars",
            "mode": "overnight",
            "consumption_count": 0,
            "budget_status": "green",
            "praxis_items": "",
            "shapes": "",
            "division": "",
            "now_md": "",
            "sub_goals": [],
            "archived": [],
            "follow_ons": [],
            "gate_results": {},
            "total_produced": 0,
            "total_for_review": 0,
            "should_stop": False,
            "stop_reason": "",
            "report": "",
            "errors": [],
        }

        result = pl.compound_and_scout(state)
        assert len(result["follow_ons"]) == 1
        assert result["follow_ons"][0]["type"] == "compound"

    def test_no_work_returns_empty(self):
        result = pl.compound_and_scout({
            "dispatched_work": [], "systole_num": 1, "north_stars": "",
        })
        assert result == {"follow_ons": []}

    @patch.object(pl, "_channel")
    def test_caps_at_6_follow_ons(self, mock_channel):
        follow_ons = [
            {"goal": f"g{i}", "star": "s", "deliverable": "d", "model": "sonnet", "type": "scout"}
            for i in range(15)
        ]
        mock_channel.return_value = json.dumps(follow_ons)

        state: pl.PolarizationState = {
            "dispatched_work": [
                {"success": True, "star": "s", "goal": "g", "output": "out"},
            ],
            "systole_num": 1,
            "north_stars": "stars",
            "mode": "overnight",
            "consumption_count": 0,
            "budget_status": "green",
            "praxis_items": "",
            "shapes": "",
            "division": "",
            "now_md": "",
            "sub_goals": [],
            "archived": [],
            "follow_ons": [],
            "gate_results": {},
            "total_produced": 0,
            "total_for_review": 0,
            "should_stop": False,
            "stop_reason": "",
            "report": "",
            "errors": [],
        }

        result = pl.compound_and_scout(state)
        assert len(result["follow_ons"]) <= 6


# ---------------------------------------------------------------------------
# stopping_gate
# ---------------------------------------------------------------------------


class TestStoppingGate:
    """Tests for stopping_gate()."""

    @patch.object(pl, "_budget_status", return_value="green")
    def test_stops_when_no_follow_ons(self, mock_budget):
        state: pl.PolarizationState = {
            "follow_ons": [],
            "budget_status": "green",
            "mode": "overnight",
            "consumption_count": 0,
            "north_stars": "",
            "praxis_items": "",
            "shapes": "",
            "division": "",
            "now_md": "",
            "systole_num": 1,
            "sub_goals": [],
            "dispatched_work": [],
            "archived": [],
            "gate_results": {},
            "total_produced": 0,
            "total_for_review": 0,
            "should_stop": False,
            "stop_reason": "",
            "report": "",
            "errors": [],
        }

        result = pl.stopping_gate(state)
        assert result["should_stop"] is True
        assert "exhausted" in result["stop_reason"]

    @patch.object(pl, "_budget_status", return_value="red")
    def test_stops_on_red_budget(self, mock_budget):
        state: pl.PolarizationState = {
            "follow_ons": [{"goal": "g"}],
            "budget_status": "green",
            "mode": "overnight",
            "consumption_count": 0,
            "north_stars": "",
            "praxis_items": "",
            "shapes": "",
            "division": "",
            "now_md": "",
            "systole_num": 1,
            "sub_goals": [],
            "dispatched_work": [],
            "archived": [],
            "gate_results": {},
            "total_produced": 0,
            "total_for_review": 0,
            "should_stop": False,
            "stop_reason": "",
            "report": "",
            "errors": [],
        }

        result = pl.stopping_gate(state)
        assert result["should_stop"] is True
        assert "Budget red" in result["stop_reason"]

    @patch.object(pl, "_budget_status", return_value="yellow")
    def test_stops_on_yellow_budget(self, mock_budget):
        state: pl.PolarizationState = {
            "follow_ons": [{"goal": "g"}],
            "budget_status": "green",
            "mode": "overnight",
            "consumption_count": 0,
            "north_stars": "",
            "praxis_items": "",
            "shapes": "",
            "division": "",
            "now_md": "",
            "systole_num": 1,
            "sub_goals": [],
            "dispatched_work": [],
            "archived": [],
            "gate_results": {},
            "total_produced": 0,
            "total_for_review": 0,
            "should_stop": False,
            "stop_reason": "",
            "report": "",
            "errors": [],
        }

        result = pl.stopping_gate(state)
        assert result["should_stop"] is True
        assert "yellow" in result["stop_reason"]

    @patch.object(pl, "_budget_status", return_value="green")
    def test_continues_with_follow_ons(self, mock_budget):
        follow_ons = [{"goal": "g", "star": "s", "deliverable": "d", "model": "sonnet"}]
        state: pl.PolarizationState = {
            "follow_ons": follow_ons,
            "budget_status": "green",
            "mode": "overnight",
            "consumption_count": 0,
            "north_stars": "",
            "praxis_items": "",
            "shapes": "",
            "division": "",
            "now_md": "",
            "systole_num": 1,
            "sub_goals": [],
            "dispatched_work": [],
            "archived": [],
            "gate_results": {},
            "total_produced": 0,
            "total_for_review": 0,
            "should_stop": False,
            "stop_reason": "",
            "report": "",
            "errors": [],
        }

        result = pl.stopping_gate(state)
        assert result["should_stop"] is False
        assert result["sub_goals"] == follow_ons


# ---------------------------------------------------------------------------
# write_report
# ---------------------------------------------------------------------------


class TestWriteReport:
    """Tests for write_report()."""

    def test_writes_report_file(self, tmp_path):
        reports_dir = tmp_path / "reports"
        with patch.object(pl, "REPORTS_DIR", reports_dir):
            state: pl.PolarizationState = {
                "systole_num": 3,
                "total_produced": 10,
                "total_for_review": 2,
                "mode": "overnight",
                "stop_reason": "exhausted",
                "dispatched_work": [
                    {"success": True, "star": "research", "goal": "write paper"},
                    {"success": False, "star": "code", "goal": "build tool"},
                ],
                "errors": ["something went wrong"],
                "consumption_count": 0,
                "budget_status": "green",
                "north_stars": "",
                "praxis_items": "",
                "shapes": "",
                "division": "",
                "now_md": "",
                "sub_goals": [],
                "archived": [],
                "follow_ons": [],
                "gate_results": {},
                "should_stop": False,
                "report": "",
            }

            result = pl.write_report(state)
            assert "report" in result
            ts = time.strftime("%Y-%m-%d")
            expected_path = reports_dir / f"{ts}.md"
            assert result["report"] == str(expected_path)
            content = expected_path.read_text()
            assert "ok" in content
            assert "FAILED" in content
            assert "something went wrong" in content


# ---------------------------------------------------------------------------
# wrap
# ---------------------------------------------------------------------------


class TestWrap:
    """Tests for wrap()."""

    @patch.object(pl, "MANIFEST_FILE")
    @patch.object(pl, "GUARD_FILE")
    def test_removes_guard(self, mock_guard, mock_manifest):
        mock_guard.exists.return_value = True
        mock_manifest.exists.return_value = False

        pl.wrap({"mode": "overnight"})
        mock_guard.unlink.assert_called_once()

    @patch.object(pl, "MANIFEST_FILE")
    @patch.object(pl, "GUARD_FILE")
    def test_archives_manifest(self, mock_guard, mock_manifest):
        mock_guard.exists.return_value = False
        mock_manifest.exists.return_value = True

        pl.wrap({"mode": "overnight"})
        mock_manifest.rename.assert_called_once()

    @patch.object(pl, "MANIFEST_FILE")
    @patch.object(pl, "GUARD_FILE")
    def test_no_guard_no_error(self, mock_guard, mock_manifest):
        mock_guard.exists.return_value = False
        mock_manifest.exists.return_value = False

        result = pl.wrap({"mode": "overnight"})
        assert result == {}


# ---------------------------------------------------------------------------
# should_continue
# ---------------------------------------------------------------------------


class TestShouldContinue:
    """Tests for should_continue()."""

    def test_stops_to_report(self):
        assert pl.should_continue({"should_stop": True}) == "report"

    def test_continues_to_preflight(self):
        assert pl.should_continue({"should_stop": False}) == "preflight"

    def test_defaults_to_preflight(self):
        assert pl.should_continue({}) == "preflight"


# ---------------------------------------------------------------------------
# build_graph
# ---------------------------------------------------------------------------


class TestBuildGraph:
    """Tests for build_graph()."""

    def test_graph_has_all_nodes(self):
        graph = pl.build_graph()
        # Graph nodes are stored internally; check it compiles
        import langgraph.graph as _lg
        assert isinstance(graph, _lg.StateGraph)


# ---------------------------------------------------------------------------
# _open_checkpointer
# ---------------------------------------------------------------------------


class TestOpenCheckpointer:
    """Tests for _open_checkpointer()."""

    def test_in_memory_when_not_persistent(self):
        from langgraph.checkpoint.memory import InMemorySaver
        cp = pl._open_checkpointer(persistent=False)
        assert isinstance(cp, InMemorySaver)

    def test_sqlite_when_persistent(self, tmp_path):
        from langgraph.checkpoint.sqlite import SqliteSaver
        db_path = tmp_path / "checkpoints.db"
        with patch.object(pl, "CHECKPOINT_DB", db_path):
            cp = pl._open_checkpointer(persistent=True)
            assert isinstance(cp, SqliteSaver)


# ---------------------------------------------------------------------------
# consumption_signal thresholds
# ---------------------------------------------------------------------------


class TestConsumptionSignal:
    """Test the consumption signal logic inside brainstorm."""

    @patch.object(pl, "_channel")
    def test_low_consumption_produce_more(self, mock_channel):
        """Consumption <= 3 should signal 'Produce more.'."""
        goals = [{"star": "s", "goal": "g", "deliverable": "d", "model": "sonnet"}]
        mock_channel.return_value = json.dumps(goals)

        state = {"mode": "overnight", "systole_num": 1, "consumption_count": 2,
                 "budget_status": "green", "north_stars": "", "praxis_items": "",
                 "shapes": "", "division": "", "now_md": "", "total_produced": 0}

        pl.brainstorm(state)
        prompt = mock_channel.call_args[1].get("prompt", mock_channel.call_args[0][1] if len(mock_channel.call_args[0]) > 1 else "")
        # The prompt is passed as positional arg
        call_args = mock_channel.call_args
        prompt_arg = call_args[0][1]
        assert "Produce more" in prompt_arg

    @patch.object(pl, "_channel")
    def test_mid_consumption_self_sufficient(self, mock_channel):
        """Consumption 4-8 should signal 'Self-sufficient outputs only.'."""
        goals = [{"star": "s", "goal": "g", "deliverable": "d", "model": "sonnet"}]
        mock_channel.return_value = json.dumps(goals)

        state = {"mode": "overnight", "systole_num": 1, "consumption_count": 5,
                 "budget_status": "green", "north_stars": "", "praxis_items": "",
                 "shapes": "", "division": "", "now_md": "", "total_produced": 0}

        pl.brainstorm(state)
        prompt_arg = mock_channel.call_args[0][1]
        assert "Self-sufficient" in prompt_arg

    @patch.object(pl, "_channel")
    def test_high_consumption_triage(self, mock_channel):
        """Consumption > 8 should signal 'Overproduction. Triage only.'."""
        goals = [{"star": "s", "goal": "g", "deliverable": "d", "model": "sonnet"}]
        mock_channel.return_value = json.dumps(goals)

        state = {"mode": "overnight", "systole_num": 1, "consumption_count": 10,
                 "budget_status": "green", "north_stars": "", "praxis_items": "",
                 "shapes": "", "division": "", "now_md": "", "total_produced": 0}

        pl.brainstorm(state)
        prompt_arg = mock_channel.call_args[0][1]
        assert "Overproduction" in prompt_arg


# ---------------------------------------------------------------------------
# CLI main
# ---------------------------------------------------------------------------


class TestMain:
    """Tests for main()."""

    @patch.object(pl, "preflight")
    def test_dry_run(self, mock_preflight, capsys):
        mock_preflight.return_value = {
            "budget_status": "green",
            "consumption_count": 3,
            "north_stars": "x" * 100,
        }

        with patch("sys.argv", ["polarization_loop", "--dry-run"]):
            pl.main()

        captured = capsys.readouterr()
        assert "Budget: green" in captured.out
        assert "Consumption: 3" in captured.out
        assert "100 chars" in captured.out

    @patch.object(pl, "polarize")
    def test_full_run(self, mock_polarize, capsys):
        mock_polarize.return_value = {
            "systole_num": 2,
            "total_produced": 5,
            "total_for_review": 1,
            "report": "/tmp/report.md",
        }

        with patch("sys.argv", ["polarization_loop", "--mode", "overnight"]):
            pl.main()

        captured = capsys.readouterr()
        assert "Systoles: 2" in captured.out
        assert "Produced: 5" in captured.out
