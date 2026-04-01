from __future__ import annotations

"""Tests for polarization_loop — overnight flywheel via LangGraph."""

import json
import sqlite3
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.polarization_loop import (
    CHECKPOINT_DB,
    DIVISION_FILE,
    GUARD_FILE,
    MANIFEST_FILE,
    NOW_FILE,
    NORTH_STAR_FILE,
    REPORTS_DIR,
    SHAPES_FILE,
    PolarizationState,
    _budget_status,
    _channel,
    _consumption_count,
    _open_checkpointer,
    _read_file,
    brainstorm,
    build_graph,
    compound_and_scout,
    dispatch,
    main,
    polarize,
    preflight,
    quality_gate,
    review_and_continue,
    should_continue,
    stopping_gate,
    wrap,
    write_report,
)


# ── fixtures ────────────────────────────────────────────────────────


def _base_state(**overrides) -> dict:
    """Return a minimal valid PolarizationState with sensible defaults."""
    state = {
        "mode": "overnight",
        "consumption_count": 0,
        "budget_status": "green",
        "north_stars": "Star A: do things\nStar B: more things",
        "praxis_items": "- [ ] task 1\n- [ ] task 2",
        "shapes": "Star A: flywheel",
        "division": "Star A: automated",
        "now_md": "# NOW",
        "systole_num": 1,
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
    state.update(overrides)
    return state


@pytest.fixture(autouse=True)
def _tmp_paths(tmp_path, monkeypatch):
    """Redirect all path constants to tmp_path so tests never touch real FS."""
    monkeypatch.setattr(
        "metabolon.organelles.polarization_loop.CHECKPOINT_DB",
        tmp_path / "checkpoints.db",
    )
    monkeypatch.setattr(
        "metabolon.organelles.polarization_loop.GUARD_FILE",
        tmp_path / "guard",
    )
    monkeypatch.setattr(
        "metabolon.organelles.polarization_loop.MANIFEST_FILE",
        tmp_path / "session.md",
    )
    monkeypatch.setattr(
        "metabolon.organelles.polarization_loop.REPORTS_DIR",
        tmp_path / "reports",
    )
    monkeypatch.setattr(
        "metabolon.organelles.polarization_loop.NORTH_STAR_FILE",
        tmp_path / "north_star.md",
    )
    monkeypatch.setattr(
        "metabolon.organelles.polarization_loop.SHAPES_FILE",
        tmp_path / "shapes.md",
    )
    monkeypatch.setattr(
        "metabolon.organelles.polarization_loop.DIVISION_FILE",
        tmp_path / "division.md",
    )
    monkeypatch.setattr(
        "metabolon.organelles.polarization_loop.NOW_FILE",
        tmp_path / "NOW.md",
    )


# ── _channel ────────────────────────────────────────────────────────


class TestChannel:
    """Tests for _channel subprocess wrapper."""

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_success_returns_stdout(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="hello world", stderr="")
        result = _channel("sonnet", "prompt text")
        assert result == "hello world"
        mock_run.assert_called_once()

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_error_returns_error_string(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="bad error")
        result = _channel("sonnet", "prompt")
        assert result.startswith("(channel error: exit 1)")
        assert "bad error" in result

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_timeout_returns_timeout_string(self, mock_run):
        import subprocess as sp
        mock_run.side_effect = sp.TimeoutExpired(cmd="channel", timeout=300)
        result = _channel("sonnet", "prompt", timeout=300)
        assert "(channel timeout after 300s)" == result

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_organism_flag(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        _channel("opus", "do it", organism=True)
        cmd = mock_run.call_args[0][0]
        assert "--organism" in cmd

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_no_organism_flag(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        _channel("opus", "do it", organism=False)
        cmd = mock_run.call_args[0][0]
        assert "--organism" not in cmd

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_custom_timeout(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        _channel("sonnet", "prompt", timeout=600)
        _, kwargs = mock_run.call_args
        assert kwargs["timeout"] == 600

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_strips_claudecode_env(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        with patch.dict("os.environ", {"CLAUDECODE": "1"}, clear=False):
            _channel("sonnet", "prompt")
        _, kwargs = mock_run.call_args
        assert "CLAUDECODE" not in kwargs["env"]

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_stderr_truncated_to_500(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="x" * 1000
        )
        result = _channel("sonnet", "prompt")
        # Error string contains truncated stderr
        assert len(result) < 600  # prefix + 500 chars max

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_stdout_is_stripped(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="  hello  \n", stderr="")
        assert _channel("sonnet", "prompt") == "hello"


# ── _read_file ──────────────────────────────────────────────────────


class TestReadFile:
    """Tests for _read_file helper."""

    def test_returns_file_contents(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world", encoding="utf-8")
        assert _read_file(f) == "hello world"

    def test_returns_empty_for_missing_file(self):
        assert _read_file(Path("/nonexistent/file.txt")) == ""

    def test_truncates_to_max_chars(self, tmp_path):
        f = tmp_path / "long.txt"
        f.write_text("x" * 5000, encoding="utf-8")
        assert len(_read_file(f, max_chars=1000)) == 1000

    def test_default_max_chars(self, tmp_path):
        f = tmp_path / "default.txt"
        f.write_text("y" * 5000, encoding="utf-8")
        assert len(_read_file(f)) == 3000

    def test_empty_file_returns_empty(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        assert _read_file(f) == ""


# ── _budget_status ──────────────────────────────────────────────────


class TestBudgetStatus:
    """Tests for _budget_status helper."""

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_green_under_50(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({"seven_day": {"utilization": 30}}), stderr=""
        )
        assert _budget_status() == "green"

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_yellow_50_to_79(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({"seven_day": {"utilization": 60}}), stderr=""
        )
        assert _budget_status() == "yellow"

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_red_over_80(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({"seven_day": {"utilization": 85}}), stderr=""
        )
        assert _budget_status() == "red"

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_exact_50_is_yellow(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({"seven_day": {"utilization": 50}}), stderr=""
        )
        assert _budget_status() == "yellow"

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_exact_80_is_red(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({"seven_day": {"utilization": 80}}), stderr=""
        )
        assert _budget_status() == "red"

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_nonzero_returncode_defaults_green(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        assert _budget_status() == "green"

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_exception_defaults_green(self, mock_run):
        mock_run.side_effect = Exception("boom")
        assert _budget_status() == "green"

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_missing_utilization_key_defaults_green(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({}), stderr=""
        )
        assert _budget_status() == "green"


# ── _consumption_count ──────────────────────────────────────────────


class TestConsumptionCount:
    """Tests for _consumption_count helper."""

    def test_no_reports_dir_returns_zero(self, tmp_path):
        assert _consumption_count() == 0

    def test_counts_recent_files(self, tmp_path, monkeypatch):
        reports = tmp_path / "reports"
        monkeypatch.setattr(
            "metabolon.organelles.polarization_loop.REPORTS_DIR", reports
        )
        reports.mkdir()
        (reports / "a.md").write_text("r1")
        (reports / "b.md").write_text("r2")
        assert _consumption_count() == 2

    def test_ignores_old_files(self, tmp_path, monkeypatch):
        reports = tmp_path / "reports"
        monkeypatch.setattr(
            "metabolon.organelles.polarization_loop.REPORTS_DIR", reports
        )
        reports.mkdir()
        old = reports / "old.md"
        old.write_text("old")
        # Set mtime to 8 days ago
        old.stat()
        import os
        old_time = time.time() - 8 * 24 * 3600
        os.utime(old, (old_time, old_time))
        assert _consumption_count() == 0

    def test_counts_mixed_old_and_new(self, tmp_path, monkeypatch):
        reports = tmp_path / "reports"
        monkeypatch.setattr(
            "metabolon.organelles.polarization_loop.REPORTS_DIR", reports
        )
        reports.mkdir()
        import os
        # Recent file
        (reports / "new.md").write_text("new")
        # Old file
        old = reports / "old.md"
        old.write_text("old")
        old_time = time.time() - 8 * 24 * 3600
        os.utime(old, (old_time, old_time))
        assert _consumption_count() == 1


# ── preflight ───────────────────────────────────────────────────────


class TestPreflight:
    """Tests for preflight node."""

    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="green")
    @patch("metabolon.organelles.polarization_loop._consumption_count", return_value=3)
    def test_reads_files_and_returns_state(self, mock_cc, mock_bs, tmp_path):
        (tmp_path / "north_star.md").write_text("my star", encoding="utf-8")
        (tmp_path / "shapes.md").write_text("shapes text", encoding="utf-8")
        (tmp_path / "division.md").write_text("division text", encoding="utf-8")
        (tmp_path / "NOW.md").write_text("now text", encoding="utf-8")

        result = preflight(_base_state(systole_num=0))
        assert result["north_stars"] == "my star"
        assert result["shapes"] == "shapes text"
        assert result["division"] == "division text"
        assert result["now_md"] == "now text"
        assert result["budget_status"] == "green"
        assert result["consumption_count"] == 3
        assert result["systole_num"] == 1

    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="red")
    @patch("metabolon.organelles.polarization_loop._consumption_count", return_value=0)
    def test_creates_guard_file(self, mock_bs, mock_cc, tmp_path):
        guard = tmp_path / "guard"
        preflight(_base_state())
        assert guard.exists()

    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="green")
    @patch("metabolon.organelles.polarization_loop._consumption_count", return_value=0)
    def test_missing_files_return_empty(self, mock_bs, mock_cc):
        result = preflight(_base_state())
        assert result["north_stars"] == ""
        assert result["shapes"] == ""

    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="green")
    @patch("metabolon.organelles.polarization_loop._consumption_count", return_value=0)
    def test_systole_increments(self, mock_bs, mock_cc):
        result = preflight(_base_state(systole_num=5))
        assert result["systole_num"] == 6

    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="green")
    @patch("metabolon.organelles.polarization_loop._consumption_count", return_value=0)
    def test_defaults_systole_to_1_when_missing(self, mock_bs, mock_cc):
        result = preflight({"mode": "overnight"})
        assert result["systole_num"] == 1


# ── brainstorm ──────────────────────────────────────────────────────


class TestBrainstorm:
    """Tests for brainstorm node."""

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_parses_json_goals(self, mock_ch):
        goals = [{"star": "A", "goal": "write X", "deliverable": "x.md", "model": "sonnet"}]
        mock_ch.return_value = json.dumps(goals)
        result = brainstorm(_base_state(systole_num=1))
        assert len(result["sub_goals"]) == 1
        assert result["sub_goals"][0]["star"] == "A"

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_truncates_to_max_goals_overnight(self, mock_ch):
        goals = [{"star": "A", "goal": f"g{i}", "deliverable": f"f{i}.md", "model": "sonnet"} for i in range(20)]
        mock_ch.return_value = json.dumps(goals)
        result = brainstorm(_base_state(mode="overnight", systole_num=1))
        assert len(result["sub_goals"]) == 8

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_truncates_to_max_goals_interactive(self, mock_ch):
        goals = [{"star": "A", "goal": f"g{i}", "deliverable": f"f{i}.md", "model": "sonnet"} for i in range(20)]
        mock_ch.return_value = json.dumps(goals)
        result = brainstorm(_base_state(mode="interactive", systole_num=1))
        assert len(result["sub_goals"]) == 5

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_bad_json_returns_error(self, mock_ch):
        # Must contain [ and ] to trigger parse attempt
        mock_ch.return_value = "Here it is: [not valid json] done"
        result = brainstorm(_base_state(systole_num=1))
        assert "errors" in result
        assert len(result["errors"]) == 1
        assert "Brainstorm failed to parse" in result["errors"][0]

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_no_brackets_returns_empty(self, mock_ch):
        mock_ch.return_value = "no brackets at all"
        result = brainstorm(_base_state(systole_num=1))
        assert result["sub_goals"] == []

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_json_embedded_in_text(self, mock_ch):
        goals = [{"star": "A", "goal": "write X", "deliverable": "x.md", "model": "sonnet"}]
        mock_ch.return_value = f"Here are the goals:\n{json.dumps(goals)}\nDone."
        result = brainstorm(_base_state(systole_num=1))
        assert len(result["sub_goals"]) == 1

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_calls_sonnet(self, mock_ch):
        mock_ch.return_value = "[]"
        brainstorm(_base_state(systole_num=1))
        mock_ch.assert_called_once()
        assert mock_ch.call_args[0][0] == "sonnet"

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_consumption_signal_low(self, mock_ch):
        mock_ch.return_value = "[]"
        brainstorm(_base_state(consumption_count=2, systole_num=1))
        prompt = mock_ch.call_args[0][1]
        assert "Produce more" in prompt

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_consumption_signal_medium(self, mock_ch):
        mock_ch.return_value = "[]"
        brainstorm(_base_state(consumption_count=5, systole_num=1))
        prompt = mock_ch.call_args[0][1]
        assert "Self-sufficient" in prompt

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_consumption_signal_high(self, mock_ch):
        mock_ch.return_value = "[]"
        brainstorm(_base_state(consumption_count=10, systole_num=1))
        prompt = mock_ch.call_args[0][1]
        assert "Overproduction" in prompt


# ── dispatch ────────────────────────────────────────────────────────


class TestDispatch:
    """Tests for dispatch node."""

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_dispatches_goals(self, mock_ch):
        mock_ch.return_value = "output text"
        goals = [{"star": "A", "goal": "write X", "deliverable": "x.md", "model": "sonnet"}]
        result = dispatch(_base_state(sub_goals=goals, systole_num=1))
        assert len(result["dispatched_work"]) == 1
        assert result["dispatched_work"][0]["success"] is True
        assert result["dispatched_work"][0]["output"] == "output text"

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_empty_goals_returns_error(self, mock_ch):
        result = dispatch(_base_state(sub_goals=[], systole_num=1))
        assert "errors" in result
        assert "No goals to dispatch" in result["errors"][0]
        mock_ch.assert_not_called()

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_channel_error_marks_failed(self, mock_ch):
        mock_ch.return_value = "(channel error: exit 1) something"
        goals = [{"star": "A", "goal": "write X", "deliverable": "x.md", "model": "sonnet"}]
        result = dispatch(_base_state(sub_goals=goals, systole_num=1))
        assert result["dispatched_work"][0]["success"] is False

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_multiple_goals(self, mock_ch):
        mock_ch.return_value = "done"
        goals = [
            {"star": "A", "goal": "g1", "deliverable": "f1.md", "model": "sonnet"},
            {"star": "B", "goal": "g2", "deliverable": "f2.md", "model": "opus"},
        ]
        result = dispatch(_base_state(sub_goals=goals, systole_num=1))
        assert len(result["dispatched_work"]) == 2

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_appends_to_manifest(self, mock_ch, tmp_path):
        mock_ch.return_value = "done"
        manifest = tmp_path / "session.md"
        manifest.write_text("# Existing\n", encoding="utf-8")
        goals = [{"star": "A", "goal": "write X", "deliverable": "x.md", "model": "sonnet"}]
        dispatch(_base_state(sub_goals=goals, systole_num=1))
        content = manifest.read_text(encoding="utf-8")
        assert "## Wave" in content
        assert "[ok]" in content

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_uses_correct_model_per_goal(self, mock_ch):
        mock_ch.return_value = "done"
        goals = [
            {"star": "A", "goal": "g1", "deliverable": "f1.md", "model": "opus"},
        ]
        dispatch(_base_state(sub_goals=goals, systole_num=1))
        assert mock_ch.call_args[0][0] == "opus"

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_organism_flag_true(self, mock_ch):
        mock_ch.return_value = "done"
        goals = [{"star": "A", "goal": "g1", "deliverable": "f1.md", "model": "sonnet"}]
        dispatch(_base_state(sub_goals=goals, systole_num=1))
        assert mock_ch.call_args[1].get("organism") is True


# ── quality_gate ────────────────────────────────────────────────────


class TestQualityGate:
    """Tests for quality_gate node."""

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_classifies_self_sufficient(self, mock_ch):
        evals = [{"goal": "g1", "classification": "self-sufficient", "quality": "pass"}]
        mock_ch.return_value = json.dumps(evals)
        work = [{"star": "A", "goal": "g1", "output": "output", "success": True}]
        result = quality_gate(_base_state(dispatched_work=work))
        assert result["total_produced"] == 1
        assert result["total_for_review"] == 0

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_classifies_needs_review(self, mock_ch):
        evals = [{"goal": "g1", "classification": "needs-review", "quality": "partial"}]
        mock_ch.return_value = json.dumps(evals)
        work = [{"star": "A", "goal": "g1", "output": "output", "success": True}]
        result = quality_gate(_base_state(dispatched_work=work))
        assert result["total_for_review"] == 1

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_no_successful_work(self, mock_ch):
        work = [{"star": "A", "goal": "g1", "output": "(channel error)", "success": False}]
        result = quality_gate(_base_state(dispatched_work=work))
        assert result["total_produced"] == 0
        mock_ch.assert_not_called()

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_empty_work(self, mock_ch):
        result = quality_gate(_base_state(dispatched_work=[]))
        assert result["total_produced"] == 0
        mock_ch.assert_not_called()

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_bad_json_defaults_to_counted(self, mock_ch):
        mock_ch.return_value = "not json"
        work = [{"star": "A", "goal": "g1", "output": "output", "success": True}]
        result = quality_gate(_base_state(dispatched_work=work))
        # Still counts produced but review = 0
        assert result["total_produced"] == 1
        assert result["total_for_review"] == 0

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_accumulates_totals(self, mock_ch):
        evals = [{"goal": "g1", "classification": "self-sufficient", "quality": "pass"}]
        mock_ch.return_value = json.dumps(evals)
        work = [{"star": "A", "goal": "g1", "output": "output", "success": True}]
        result = quality_gate(_base_state(dispatched_work=work, total_produced=5, total_for_review=2))
        assert result["total_produced"] == 6
        assert result["total_for_review"] == 2

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_limits_to_recent_8(self, mock_ch):
        evals = [{"goal": f"g{i}", "classification": "self-sufficient", "quality": "pass"} for i in range(10)]
        mock_ch.return_value = json.dumps(evals)
        work = [{"star": "A", "goal": f"g{i}", "output": f"output {i}", "success": True} for i in range(10)]
        result = quality_gate(_base_state(dispatched_work=work))
        assert result["total_produced"] == 10


# ── compound_and_scout ──────────────────────────────────────────────


class TestCompoundAndScout:
    """Tests for compound_and_scout node."""

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_returns_follow_ons(self, mock_ch):
        follow = [{"goal": "next step", "star": "A", "deliverable": "f.md", "model": "sonnet", "type": "compound"}]
        mock_ch.return_value = json.dumps(follow)
        work = [{"star": "A", "goal": "g1", "output": "done", "success": True}]
        result = compound_and_scout(_base_state(dispatched_work=work))
        assert len(result["follow_ons"]) == 1

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_no_successful_work(self, mock_ch):
        result = compound_and_scout(_base_state(dispatched_work=[]))
        assert result["follow_ons"] == []
        mock_ch.assert_not_called()

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_bad_json_returns_empty(self, mock_ch):
        mock_ch.return_value = "not json"
        work = [{"star": "A", "goal": "g1", "output": "done", "success": True}]
        result = compound_and_scout(_base_state(dispatched_work=work))
        assert result["follow_ons"] == []

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_limits_to_6_follow_ons(self, mock_ch):
        follow = [{"goal": f"step {i}", "star": "A", "deliverable": f"f{i}.md", "model": "sonnet", "type": "compound"} for i in range(10)]
        mock_ch.return_value = json.dumps(follow)
        work = [{"star": "A", "goal": "g1", "output": "done", "success": True}]
        result = compound_and_scout(_base_state(dispatched_work=work))
        assert len(result["follow_ons"]) <= 6


# ── stopping_gate ───────────────────────────────────────────────────


class TestStoppingGate:
    """Tests for stopping_gate node."""

    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="green")
    def test_continues_with_follow_ons(self, mock_bs):
        follow = [{"goal": "next", "star": "A", "deliverable": "f.md", "model": "sonnet"}]
        result = stopping_gate(_base_state(follow_ons=follow))
        assert result["should_stop"] is False
        assert result["sub_goals"] == follow

    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="green")
    def test_stops_when_no_follow_ons(self, mock_bs):
        result = stopping_gate(_base_state(follow_ons=[]))
        assert result["should_stop"] is True
        assert result["sub_goals"] == []

    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="red")
    def test_stops_on_red_budget(self, mock_bs):
        follow = [{"goal": "next", "star": "A", "deliverable": "f.md", "model": "sonnet"}]
        result = stopping_gate(_base_state(follow_ons=follow))
        assert result["should_stop"] is True
        assert "Budget red" in result["stop_reason"]

    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="yellow")
    def test_stops_on_yellow_budget(self, mock_bs):
        follow = [{"goal": "next", "star": "A", "deliverable": "f.md", "model": "sonnet"}]
        result = stopping_gate(_base_state(follow_ons=follow))
        assert result["should_stop"] is True
        assert "yellow" in result["stop_reason"]

    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="green")
    def test_gate_results_populated(self, mock_bs):
        result = stopping_gate(_base_state(follow_ons=[]))
        assert "gate_results" in result
        checks = result["gate_results"]
        assert "budget_not_green" in checks
        assert "follow_ons_exhausted" in checks

    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="green")
    def test_updates_budget_status(self, mock_bs):
        result = stopping_gate(_base_state(follow_ons=[]))
        assert result["budget_status"] == "green"


# ── write_report ────────────────────────────────────────────────────


class TestWriteReport:
    """Tests for write_report node."""

    def test_writes_report_file(self, tmp_path, monkeypatch):
        reports = tmp_path / "reports"
        monkeypatch.setattr(
            "metabolon.organelles.polarization_loop.REPORTS_DIR", reports
        )
        result = write_report(_base_state(
            systole_num=3, total_produced=5, total_for_review=1,
            mode="overnight", stop_reason="done",
            dispatched_work=[{"star": "A", "goal": "g1", "success": True}],
        ))
        assert "report" in result
        ts = time.strftime("%Y-%m-%d")
        expected_path = str(reports / f"{ts}.md")
        assert result["report"] == expected_path
        content = Path(result["report"]).read_text(encoding="utf-8")
        assert "Poiesis Report" in content
        assert "systoles: 3" in content

    def test_report_contains_work(self, tmp_path, monkeypatch):
        reports = tmp_path / "reports"
        monkeypatch.setattr(
            "metabolon.organelles.polarization_loop.REPORTS_DIR", reports
        )
        write_report(_base_state(
            systole_num=1,
            dispatched_work=[
                {"star": "A", "goal": "goal A", "success": True},
                {"star": "B", "goal": "goal B", "success": False},
            ],
        ))
        ts = time.strftime("%Y-%m-%d")
        content = (reports / f"{ts}.md").read_text(encoding="utf-8")
        assert "[ok]" in content
        assert "[FAILED]" in content

    def test_report_contains_errors(self, tmp_path, monkeypatch):
        reports = tmp_path / "reports"
        monkeypatch.setattr(
            "metabolon.organelles.polarization_loop.REPORTS_DIR", reports
        )
        write_report(_base_state(
            systole_num=1,
            errors=["something went wrong"],
        ))
        ts = time.strftime("%Y-%m-%d")
        content = (reports / f"{ts}.md").read_text(encoding="utf-8")
        assert "something went wrong" in content
        assert "Errors" in content

    def test_creates_reports_dir(self, tmp_path, monkeypatch):
        reports = tmp_path / "new_reports"
        monkeypatch.setattr(
            "metabolon.organelles.polarization_loop.REPORTS_DIR", reports
        )
        write_report(_base_state(systole_num=1))
        assert reports.exists()


# ── wrap ────────────────────────────────────────────────────────────


class TestWrap:
    """Tests for wrap node."""

    def test_removes_guard_file(self, tmp_path):
        guard = tmp_path / "guard"
        guard.touch()
        assert guard.exists()
        wrap(_base_state())
        assert not guard.exists()

    def test_no_error_if_guard_missing(self, tmp_path):
        # Guard file doesn't exist, should not raise
        wrap(_base_state())

    def test_archives_manifest(self, tmp_path):
        manifest = tmp_path / "session.md"
        manifest.write_text("# Session\n", encoding="utf-8")
        wrap(_base_state())
        ts = time.strftime("%Y-%m-%d")
        archive = tmp_path / f"polarization-session-{ts}.md"
        assert archive.exists()
        assert not manifest.exists()

    def test_no_error_if_manifest_missing(self, tmp_path):
        wrap(_base_state())  # Should not raise

    def test_returns_empty_dict(self, tmp_path):
        result = wrap(_base_state())
        assert result == {}


# ── should_continue ─────────────────────────────────────────────────


class TestShouldContinue:
    """Tests for should_continue routing function."""

    def test_returns_report_when_should_stop(self):
        assert should_continue(_base_state(should_stop=True)) == "report"

    def test_returns_preflight_when_continuing(self):
        assert should_continue(_base_state(should_stop=False)) == "preflight"

    def test_defaults_to_preflight(self):
        assert should_continue({}) == "preflight"


# ── build_graph ─────────────────────────────────────────────────────


class TestBuildGraph:
    """Tests for build_graph graph assembly."""

    def test_returns_state_graph(self):
        from langgraph.graph import StateGraph
        graph = build_graph()
        assert isinstance(graph, StateGraph)

    def test_has_all_nodes(self):
        graph = build_graph()
        node_names = set(graph.nodes.keys())
        expected = {
            "preflight", "brainstorm", "dispatch", "quality_gate",
            "compound_and_scout", "stopping_gate", "report", "wrap",
        }
        assert expected == node_names


# ── _open_checkpointer ──────────────────────────────────────────────


class TestOpenCheckpointer:
    """Tests for _open_checkpointer helper."""

    def test_in_memory_saver(self):
        from langgraph.checkpoint.memory import InMemorySaver
        cp = _open_checkpointer(persistent=False)
        assert isinstance(cp, InMemorySaver)

    def test_sqlite_saver(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "metabolon.organelles.polarization_loop.CHECKPOINT_DB",
            tmp_path / "checkpoints.db",
        )
        from langgraph.checkpoint.sqlite import SqliteSaver
        cp = _open_checkpointer(persistent=True)
        assert isinstance(cp, SqliteSaver)


# ── main (CLI) ──────────────────────────────────────────────────────


class TestMain:
    """Tests for CLI main function."""

    @patch("metabolon.organelles.polarization_loop.preflight")
    def test_dry_run_calls_preflight(self, mock_pf, capsys):
        mock_pf.return_value = {
            "budget_status": "green",
            "consumption_count": 3,
            "north_stars": "some stars" * 10,
        }
        with patch("sys.argv", ["polarization_loop", "--dry-run"]):
            main()
        captured = capsys.readouterr()
        assert "Budget: green" in captured.out
        assert "Consumption: 3" in captured.out

    @patch("metabolon.organelles.polarization_loop.polarize")
    def test_default_mode_overnight(self, mock_pol, capsys):
        mock_pol.return_value = {
            "systole_num": 2,
            "total_produced": 5,
            "total_for_review": 1,
            "report": "/tmp/report.md",
        }
        with patch("sys.argv", ["polarization_loop"]):
            main()
        mock_pol.assert_called_once_with(mode="overnight", thread_id="default")

    @patch("metabolon.organelles.polarization_loop.polarize")
    def test_interactive_mode(self, mock_pol, capsys):
        mock_pol.return_value = {
            "systole_num": 1,
            "total_produced": 0,
            "total_for_review": 0,
        }
        with patch("sys.argv", ["polarization_loop", "--mode", "interactive"]):
            main()
        mock_pol.assert_called_once_with(mode="interactive", thread_id="default")

    @patch("metabolon.organelles.polarization_loop.polarize")
    def test_custom_thread(self, mock_pol, capsys):
        mock_pol.return_value = {"systole_num": 1, "total_produced": 0, "total_for_review": 0}
        with patch("sys.argv", ["polarization_loop", "--thread", "my-thread"]):
            main()
        mock_pol.assert_called_once_with(mode="overnight", thread_id="my-thread")

    @patch("metabolon.organelles.polarization_loop.polarize")
    def test_output_shows_results(self, mock_pol, capsys):
        mock_pol.return_value = {
            "systole_num": 3,
            "total_produced": 10,
            "total_for_review": 2,
            "report": "/path/report.md",
        }
        with patch("sys.argv", ["polarization_loop"]):
            main()
        captured = capsys.readouterr()
        assert "Systoles: 3" in captured.out
        assert "Produced: 10" in captured.out
        assert "For review: 2" in captured.out
        assert "Report: /path/report.md" in captured.out
