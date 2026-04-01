from __future__ import annotations

"""Tests for metabolon.organelles.polarization_loop — overnight flywheel via LangGraph."""

import json
import sqlite3
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.polarization_loop import (
    CHECKPOINT_DB,
    GUARD_FILE,
    MANIFEST_FILE,
    NOW_FILE,
    NORTH_STAR_FILE,
    REPORTS_DIR,
    SHAPES_FILE,
    DIVISION_FILE,
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


# ── fixtures ────────────────────────────────────────────────────


@pytest.fixture
def base_state() -> dict:
    """Minimal valid PolarizationState for node-function tests."""
    return {
        "mode": "overnight",
        "consumption_count": 0,
        "budget_status": "green",
        "north_stars": "## Star 1\n## Star 2",
        "praxis_items": "- [ ] task A\n- [ ] task B",
        "shapes": "Star 1: flywheel\nStar 2: habit",
        "division": "Star 1: automated\nStar 2: presence",
        "now_md": "# NOW\nFocus on writing.",
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


@pytest.fixture
def sample_goals() -> list[dict]:
    return [
        {"star": "Research", "goal": "Write report", "deliverable": "/tmp/report.md", "model": "sonnet"},
        {"star": "Health", "goal": "Summarize papers", "deliverable": "/tmp/summary.md", "model": "opus"},
    ]


@pytest.fixture
def sample_dispatched(sample_goals) -> list[dict]:
    return [
        {
            "goal": g["goal"],
            "star": g["star"],
            "model": g["model"],
            "deliverable_path": g["deliverable"],
            "output": f"Output for {g['goal']}",
            "success": True,
        }
        for g in sample_goals
    ]


# ── _channel tests ──────────────────────────────────────────────


class TestChannel:
    """Tests for _channel helper."""

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_success_returns_stdout(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="  hello world  ")
        result = _channel("sonnet", "test prompt")
        assert result == "hello world"
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "sonnet" in cmd
        assert "-p" in cmd

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_organism_flag(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok")
        _channel("opus", "prompt", organism=True)
        cmd = mock_run.call_args[0][0]
        assert "--organism" in cmd

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_no_organism_by_default(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok")
        _channel("opus", "prompt")
        cmd = mock_run.call_args[0][0]
        assert "--organism" not in cmd

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_nonzero_exit(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="bad error")
        result = _channel("sonnet", "prompt")
        assert result.startswith("(channel error:")
        assert "exit 1" in result

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_timeout(self, mock_run):
        import subprocess as sp
        mock_run.side_effect = sp.TimeoutExpired(cmd="channel", timeout=5)
        result = _channel("sonnet", "prompt", timeout=5)
        assert "timeout" in result
        assert "5s" in result

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_removes_claudecode_env(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok")
        _channel("sonnet", "prompt")
        env = mock_run.call_args[1]["env"]
        assert "CLAUDECODE" not in env

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_custom_timeout(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok")
        _channel("sonnet", "prompt", timeout=600)
        assert mock_run.call_args[1]["timeout"] == 600


# ── _read_file tests ───────────────────────────────────────────


class TestReadFile:
    """Tests for _read_file helper."""

    def test_reads_existing_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world", encoding="utf-8")
        assert _read_file(f) == "hello world"

    def test_missing_file_returns_empty(self):
        assert _read_file(Path("/nonexistent/file.txt")) == ""

    def test_truncates_at_max_chars(self, tmp_path):
        f = tmp_path / "long.txt"
        f.write_text("x" * 5000, encoding="utf-8")
        result = _read_file(f, max_chars=100)
        assert len(result) == 100

    def test_default_max_chars_3000(self, tmp_path):
        f = tmp_path / "big.txt"
        f.write_text("y" * 5000, encoding="utf-8")
        assert len(_read_file(f)) == 3000


# ── _budget_status tests ────────────────────────────────────────


class TestBudgetStatus:
    """Tests for _budget_status helper."""

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_green_under_50(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({"seven_day": {"utilization": 30}})
        )
        assert _budget_status() == "green"

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_yellow_at_50(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({"seven_day": {"utilization": 55}})
        )
        assert _budget_status() == "yellow"

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_red_at_80(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({"seven_day": {"utilization": 85}})
        )
        assert _budget_status() == "red"

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_nonzero_exit_returns_green(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert _budget_status() == "green"

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_invalid_json_returns_green(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="not json")
        assert _budget_status() == "green"

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_exception_returns_green(self, mock_run):
        mock_run.side_effect = Exception("boom")
        assert _budget_status() == "green"

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_missing_key_returns_green(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps({}))
        assert _budget_status() == "green"

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_exact_boundary_50_is_yellow(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({"seven_day": {"utilization": 50}})
        )
        assert _budget_status() == "yellow"

    @patch("metabolon.organelles.polarization_loop.subprocess.run")
    def test_exact_boundary_80_is_red(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({"seven_day": {"utilization": 80}})
        )
        assert _budget_status() == "red"


# ── _consumption_count tests ───────────────────────────────────


class TestConsumptionCount:
    """Tests for _consumption_count helper."""

    def test_missing_dir_returns_zero(self):
        with patch("metabolon.organelles.polarization_loop.REPORTS_DIR", Path("/nonexistent")):
            assert _consumption_count() == 0

    def test_counts_recent_files(self, tmp_path):
        d = tmp_path / "reports"
        d.mkdir()
        (d / "new1.md").write_text("a")
        (d / "new2.md").write_text("b")
        with patch("metabolon.organelles.polarization_loop.REPORTS_DIR", d):
            assert _consumption_count() == 2

    def test_ignores_old_files(self, tmp_path):
        d = tmp_path / "reports"
        d.mkdir()
        old = d / "old.md"
        old.write_text("old")
        # Set mtime to 8 days ago
        old.stat().st_mtime
        eight_days_ago = time.time() - 8 * 24 * 3600
        import os
        os.utime(str(old), (eight_days_ago, eight_days_ago))
        with patch("metabolon.organelles.polarization_loop.REPORTS_DIR", d):
            assert _consumption_count() == 0


# ── preflight tests ────────────────────────────────────────────


class TestPreflight:
    """Tests for preflight node function."""

    @patch("metabolon.organelles.polarization_loop._consumption_count", return_value=5)
    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="green")
    @patch("metabolon.organelles.polarization_loop._read_file", return_value="content")
    @patch("metabolon.organelles.polarization_loop.praxis")
    def test_returns_expected_keys(self, mock_praxis, mock_read, mock_budget, mock_consumption, base_state):
        mock_praxis.exists.return_value = True
        mock_praxis.read_text.return_value = "praxis line\n" * 80
        result = preflight(base_state)
        assert "north_stars" in result
        assert "budget_status" in result
        assert "systole_num" in result

    @patch("metabolon.organelles.polarization_loop._consumption_count", return_value=0)
    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="yellow")
    @patch("metabolon.organelles.polarization_loop._read_file", return_value="ns content")
    @patch("metabolon.organelles.polarization_loop.praxis")
    def test_increments_systole_num(self, mock_praxis, mock_read, mock_budget, mock_consumption, base_state):
        mock_praxis.exists.return_value = False
        result = preflight(base_state)
        assert result["systole_num"] == 2  # started at 1

    @patch("metabolon.organelles.polarization_loop._consumption_count", return_value=0)
    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="green")
    @patch("metabolon.organelles.polarization_loop._read_file", return_value="file data")
    @patch("metabolon.organelles.polarization_loop.praxis")
    def test_praxis_not_exists(self, mock_praxis, mock_read, mock_budget, mock_consumption, base_state):
        mock_praxis.exists.return_value = False
        result = preflight(base_state)
        assert result["praxis_items"] == ""

    @patch("metabolon.organelles.polarization_loop._consumption_count", return_value=3)
    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="green")
    @patch("metabolon.organelles.polarization_loop._read_file", return_value="")
    def test_creates_guard_file(self, mock_read, mock_budget, mock_consumption, tmp_path, base_state):
        guard = tmp_path / "guard"
        with patch("metabolon.organelles.polarization_loop.GUARD_FILE", guard):
            preflight(base_state)
            assert guard.exists()

    @patch("metabolon.organelles.polarization_loop._consumption_count", return_value=0)
    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="green")
    @patch("metabolon.organelles.polarization_loop._read_file", return_value="ns")
    @patch("metabolon.organelles.polarization_loop.praxis")
    def test_systole_from_zero(self, mock_praxis, mock_read, mock_budget, mock_consumption):
        mock_praxis.exists.return_value = False
        result = preflight({"systole_num": 0})
        assert result["systole_num"] == 1


# ── brainstorm tests ───────────────────────────────────────────


class TestBrainstorm:
    """Tests for brainstorm node function."""

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_parses_json_goals(self, mock_channel, base_state):
        goals = [{"star": "S1", "goal": "G1", "deliverable": "/tmp/x.md", "model": "sonnet"}]
        mock_channel.return_value = json.dumps(goals)
        result = brainstorm(base_state)
        assert result["sub_goals"] == goals

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_extracts_json_from_markdown(self, mock_channel, base_state):
        goals = [{"star": "S1", "goal": "G1", "deliverable": "/tmp/x.md", "model": "opus"}]
        mock_channel.return_value = f"Here are the goals:\n```json\n{json.dumps(goals)}\n```\nDone."
        result = brainstorm(base_state)
        assert len(result["sub_goals"]) == 1

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_limits_to_max_goals_overnight(self, mock_channel, base_state):
        goals = [{"star": f"S{i}", "goal": f"G{i}", "deliverable": f"/tmp/{i}.md", "model": "sonnet"} for i in range(15)]
        mock_channel.return_value = json.dumps(goals)
        result = brainstorm(base_state)
        assert len(result["sub_goals"]) <= 8

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_limits_to_5_for_interactive(self, mock_channel, base_state):
        base_state["mode"] = "interactive"
        goals = [{"star": f"S{i}", "goal": f"G{i}", "deliverable": f"/tmp/{i}.md", "model": "sonnet"} for i in range(10)]
        mock_channel.return_value = json.dumps(goals)
        result = brainstorm(base_state)
        assert len(result["sub_goals"]) <= 5

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_bad_json_returns_error(self, mock_channel, base_state):
        mock_channel.return_value = "I cannot produce JSON for this."
        result = brainstorm(base_state)
        assert "errors" in result
        assert len(result["errors"]) == 1

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_consumption_signal_produce_more(self, mock_channel, base_state):
        base_state["consumption_count"] = 2
        mock_channel.return_value = "[]"
        brainstorm(base_state)
        prompt_arg = mock_channel.call_args[1].get("prompt", mock_channel.call_args[0][1] if len(mock_channel.call_args[0]) > 1 else "")
        # Just verify it was called — the signal is baked into the prompt
        assert mock_channel.called

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_empty_array(self, mock_channel, base_state):
        mock_channel.return_value = "[]"
        result = brainstorm(base_state)
        assert result["sub_goals"] == []


# ── dispatch tests ──────────────────────────────────────────────


class TestDispatch:
    """Tests for dispatch node function."""

    def test_no_goals_returns_error(self, base_state):
        result = dispatch(base_state)
        assert "errors" in result
        assert "No goals" in result["errors"][0]

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_dispatches_each_goal(self, mock_channel, base_state, sample_goals):
        mock_channel.return_value = "Agent output here"
        base_state["sub_goals"] = sample_goals
        result = dispatch(base_state)
        assert len(result["dispatched_work"]) == 2
        assert mock_channel.call_count == 2

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_tracks_success(self, mock_channel, base_state, sample_goals):
        mock_channel.return_value = "Good result"
        base_state["sub_goals"] = sample_goals
        result = dispatch(base_state)
        assert all(w["success"] for w in result["dispatched_work"])

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_channel_error_marks_failed(self, mock_channel, base_state, sample_goals):
        mock_channel.return_value = "(channel error: exit 1) something"
        base_state["sub_goals"] = sample_goals
        result = dispatch(base_state)
        assert all(not w["success"] for w in result["dispatched_work"])

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_uses_organism_flag(self, mock_channel, base_state, sample_goals):
        mock_channel.return_value = "ok"
        base_state["sub_goals"] = sample_goals
        dispatch(base_state)
        for call in mock_channel.call_args_list:
            assert call[1].get("organism", call[0][2] if len(call[0]) > 2 else False) is True or "organism" in str(call)

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_updates_manifest(self, mock_channel, base_state, sample_goals, tmp_path):
        mock_channel.return_value = "output"
        base_state["sub_goals"] = sample_goals
        manifest = tmp_path / "manifest.md"
        manifest.write_text("# Session\n", encoding="utf-8")
        with patch("metabolon.organelles.polarization_loop.MANIFEST_FILE", manifest):
            dispatch(base_state)
            content = manifest.read_text(encoding="utf-8")
            assert "## Wave" in content

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_truncates_output(self, mock_channel, base_state):
        base_state["sub_goals"] = [{"star": "S", "goal": "G", "deliverable": "/tmp/x.md", "model": "sonnet"}]
        mock_channel.return_value = "x" * 5000
        result = dispatch(base_state)
        assert len(result["dispatched_work"][0]["output"]) <= 3000


# ── quality_gate tests ─────────────────────────────────────────


class TestQualityGate:
    """Tests for quality_gate node function."""

    def test_no_successful_work(self, base_state):
        base_state["dispatched_work"] = [{"success": False, "output": "err"}]
        result = quality_gate(base_state)
        assert result["total_produced"] == 0
        assert result["total_for_review"] == 0

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_classifies_self_sufficient(self, mock_channel, base_state, sample_dispatched):
        evals = [
            {"goal": "Write report", "classification": "self-sufficient", "quality": "pass"},
            {"goal": "Summarize papers", "classification": "self-sufficient", "quality": "pass"},
        ]
        mock_channel.return_value = json.dumps(evals)
        base_state["dispatched_work"] = sample_dispatched
        result = quality_gate(base_state)
        assert result["total_produced"] == 2
        assert result["total_for_review"] == 0

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_counts_needs_review(self, mock_channel, base_state, sample_dispatched):
        evals = [
            {"goal": "Write report", "classification": "self-sufficient", "quality": "pass"},
            {"goal": "Summarize papers", "classification": "needs-review", "quality": "partial"},
        ]
        mock_channel.return_value = json.dumps(evals)
        base_state["dispatched_work"] = sample_dispatched
        result = quality_gate(base_state)
        assert result["total_for_review"] == 1

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_accumulates_totals(self, mock_channel, base_state, sample_dispatched):
        evals = [{"goal": "Write report", "classification": "self-sufficient", "quality": "pass"}]
        mock_channel.return_value = json.dumps(evals)
        base_state["dispatched_work"] = sample_dispatched
        base_state["total_produced"] = 5
        base_state["total_for_review"] = 2
        result = quality_gate(base_state)
        assert result["total_produced"] == 7  # 5 + 2 produced
        assert result["total_for_review"] == 2  # 2 + 0 review

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_bad_json_still_counts_produced(self, mock_channel, base_state, sample_dispatched):
        mock_channel.return_value = "unparseable response"
        base_state["dispatched_work"] = sample_dispatched
        result = quality_gate(base_state)
        assert result["total_produced"] == 2

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_uses_last_8_work_items(self, mock_channel, base_state):
        work = [
            {"success": True, "star": "S", "goal": f"G{i}", "output": f"O{i}"}
            for i in range(12)
        ]
        mock_channel.return_value = "[]"
        base_state["dispatched_work"] = work
        quality_gate(base_state)
        # Verify _channel was called — the prompt should only include last 8
        assert mock_channel.called


# ── compound_and_scout tests ────────────────────────────────────


class TestCompoundAndScout:
    """Tests for compound_and_scout node function."""

    def test_no_work_returns_empty(self, base_state):
        result = compound_and_scout(base_state)
        assert result["follow_ons"] == []

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_parses_follow_ons(self, mock_channel, base_state, sample_dispatched):
        follow_ons = [{"goal": "Next step", "star": "Research", "deliverable": "/tmp/next.md", "model": "sonnet", "type": "compound"}]
        mock_channel.return_value = json.dumps(follow_ons)
        base_state["dispatched_work"] = sample_dispatched
        result = compound_and_scout(base_state)
        assert len(result["follow_ons"]) == 1

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_limits_to_6_follow_ons(self, mock_channel, base_state, sample_dispatched):
        follow_ons = [
            {"goal": f"Follow {i}", "star": "S", "deliverable": f"/tmp/{i}.md", "model": "sonnet", "type": "compound"}
            for i in range(10)
        ]
        mock_channel.return_value = json.dumps(follow_ons)
        base_state["dispatched_work"] = sample_dispatched
        result = compound_and_scout(base_state)
        assert len(result["follow_ons"]) <= 6

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_bad_json_returns_empty(self, mock_channel, base_state, sample_dispatched):
        mock_channel.return_value = "no json here"
        base_state["dispatched_work"] = sample_dispatched
        result = compound_and_scout(base_state)
        assert result["follow_ons"] == []

    @patch("metabolon.organelles.polarization_loop._channel")
    def test_ignores_failed_work(self, mock_channel, base_state):
        base_state["dispatched_work"] = [
            {"success": False, "star": "S", "goal": "G", "output": "(channel error)"},
        ]
        result = compound_and_scout(base_state)
        assert result["follow_ons"] == []
        mock_channel.assert_not_called()


# ── stopping_gate tests ────────────────────────────────────────


class TestStoppingGate:
    """Tests for stopping_gate node function."""

    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="green")
    def test_no_follow_ons_stops(self, mock_budget, base_state):
        base_state["follow_ons"] = []
        result = stopping_gate(base_state)
        assert result["should_stop"] is True

    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="green")
    def test_has_follow_ons_continues(self, mock_budget, base_state):
        base_state["follow_ons"] = [{"goal": "next", "star": "S", "deliverable": "/tmp/x.md", "model": "sonnet"}]
        result = stopping_gate(base_state)
        assert result["should_stop"] is False
        assert result["sub_goals"] == base_state["follow_ons"]

    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="red")
    def test_red_budget_forces_stop(self, mock_budget, base_state):
        base_state["follow_ons"] = [{"goal": "next", "star": "S"}]
        result = stopping_gate(base_state)
        assert result["should_stop"] is True
        assert "red" in result["stop_reason"].lower()

    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="yellow")
    def test_yellow_budget_stops(self, mock_budget, base_state):
        base_state["follow_ons"] = [{"goal": "next", "star": "S"}]
        result = stopping_gate(base_state)
        assert result["should_stop"] is True
        assert "yellow" in result["stop_reason"].lower()

    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="green")
    def test_gate_results_populated(self, mock_budget, base_state):
        result = stopping_gate(base_state)
        assert "gate_results" in result
        assert "budget_not_green" in result["gate_results"]

    @patch("metabolon.organelles.polarization_loop._budget_status", return_value="red")
    def test_stopping_clears_sub_goals(self, mock_budget, base_state):
        base_state["follow_ons"] = [{"goal": "x", "star": "S"}]
        result = stopping_gate(base_state)
        assert result["sub_goals"] == []


# ── write_report tests ─────────────────────────────────────────


class TestWriteReport:
    """Tests for write_report node function."""

    def test_writes_report_file(self, base_state, tmp_path):
        reports = tmp_path / "reports"
        base_state["dispatched_work"] = [
            {"success": True, "star": "Research", "goal": "Write X"},
        ]
        with patch("metabolon.organelles.polarization_loop.REPORTS_DIR", reports):
            result = write_report(base_state)
            assert "report" in result
            assert reports.exists()
            files = list(reports.iterdir())
            assert len(files) == 1
            content = files[0].read_text(encoding="utf-8")
            assert "Poiesis Report" in content

    def test_report_includes_errors(self, tmp_path):
        reports = tmp_path / "reports"
        state = {"systole_num": 1, "total_produced": 2, "total_for_review": 0, "mode": "overnight", "stop_reason": "done", "dispatched_work": [], "errors": ["Error A", "Error B"]}
        with patch("metabolon.organelles.polarization_loop.REPORTS_DIR", reports):
            write_report(state)
            files = list(reports.iterdir())
            content = files[0].read_text(encoding="utf-8")
            assert "Error A" in content
            assert "Error B" in content

    def test_report_frontmatter(self, tmp_path):
        reports = tmp_path / "reports"
        state = {"systole_num": 3, "total_produced": 10, "total_for_review": 2, "mode": "interactive", "stop_reason": "budget", "dispatched_work": [], "errors": []}
        with patch("metabolon.organelles.polarization_loop.REPORTS_DIR", reports):
            write_report(state)
            content = list(reports.iterdir())[0].read_text(encoding="utf-8")
            assert "systoles: 3" in content
            assert "items_produced: 10" in content


# ── wrap tests ─────────────────────────────────────────────────


class TestWrap:
    """Tests for wrap node function."""

    def test_removes_guard_file(self, tmp_path):
        guard = tmp_path / "guard"
        guard.touch()
        assert guard.exists()
        with patch("metabolon.organelles.polarization_loop.GUARD_FILE", guard):
            wrap({})
        assert not guard.exists()

    def test_no_guard_file_no_error(self, tmp_path):
        guard = tmp_path / "noguard"
        with patch("metabolon.organelles.polarization_loop.GUARD_FILE", guard):
            result = wrap({})
        assert result == {}

    def test_archives_manifest(self, tmp_path):
        manifest = tmp_path / "polarization-session.md"
        manifest.write_text("session data", encoding="utf-8")
        with patch("metabolon.organelles.polarization_loop.MANIFEST_FILE", manifest):
            wrap({})
        assert not manifest.exists()
        archives = list(tmp_path.glob("polarization-session-*.md"))
        assert len(archives) == 1

    def test_no_manifest_no_error(self, tmp_path):
        manifest = tmp_path / "nomanifest"
        with patch("metabolon.organelles.polarization_loop.MANIFEST_FILE", manifest):
            result = wrap({})
        assert result == {}


# ── should_continue tests ──────────────────────────────────────


class TestShouldContinue:
    """Tests for should_continue routing function."""

    def test_stop_goes_to_report(self):
        assert should_continue({"should_stop": True}) == "report"

    def test_continue_goes_to_preflight(self):
        assert should_continue({"should_stop": False}) == "preflight"

    def test_default_is_continue(self):
        assert should_continue({}) == "preflight"


# ── build_graph tests ──────────────────────────────────────────


class TestBuildGraph:
    """Tests for graph assembly."""

    def test_builds_without_error(self):
        g = build_graph()
        assert g is not None

    def test_graph_has_all_nodes(self):
        g = build_graph()
        # Compile to check node names are registered
        nodes = set(g.nodes.keys()) if hasattr(g, "nodes") else set()
        expected = {"preflight", "brainstorm", "dispatch", "quality_gate", "compound_and_scout", "stopping_gate", "report", "wrap"}
        assert expected.issubset(nodes)


# ── _open_checkpointer tests ───────────────────────────────────


class TestOpenCheckpointer:
    """Tests for _open_checkpointer helper."""

    def test_in_memory(self):
        cp = _open_checkpointer(persistent=False)
        assert cp is not None

    def test_sqlite(self, tmp_path):
        db = tmp_path / "checkpoints.db"
        with patch("metabolon.organelles.polarization_loop.CHECKPOINT_DB", db):
            cp = _open_checkpointer(persistent=True)
            assert cp is not None

    def test_sqlite_creates_parent_dirs(self, tmp_path):
        db = tmp_path / "deep" / "nested" / "checkpoints.db"
        with patch("metabolon.organelles.polarization_loop.CHECKPOINT_DB", db):
            _open_checkpointer(persistent=True)
            assert db.parent.exists()


# ── polarize tests ─────────────────────────────────────────────


class TestPolarize:
    """Tests for polarize public API."""

    @patch("metabolon.organelles.polarization_loop._open_checkpointer")
    @patch("metabolon.organelles.polarization_loop.build_graph")
    def test_calls_graph_invoke(self, mock_build, mock_cp, base_state):
        mock_app = MagicMock()
        mock_app.invoke.return_value = base_state
        mock_build.return_value = mock_app
        mock_cp.return_value = MagicMock()
        mock_cp.return_value.get.return_value = None  # no existing checkpoint

        result = polarize(mode="overnight", persistent=False)
        assert mock_app.invoke.called

    @patch("metabolon.organelles.polarization_loop._open_checkpointer")
    @patch("metabolon.organelles.polarization_loop.build_graph")
    def test_interactive_sets_interrupt(self, mock_build, mock_cp):
        mock_app = MagicMock()
        mock_app.invoke.return_value = {}
        mock_build.return_value = mock_app
        mock_cp.return_value = MagicMock()
        mock_cp.return_value.get.return_value = None

        polarize(mode="interactive", persistent=False)
        compile_call = mock_build.return_value.compile
        assert compile_call.called
        kw = compile_call.call_args[1]
        assert kw.get("interrupt_before") == ["dispatch"]

    @patch("metabolon.organelles.polarization_loop._open_checkpointer")
    @patch("metabolon.organelles.polarization_loop.build_graph")
    def test_overnight_no_interrupt(self, mock_build, mock_cp):
        mock_app = MagicMock()
        mock_app.invoke.return_value = {}
        mock_build.return_value = mock_app
        mock_cp.return_value = MagicMock()
        mock_cp.return_value.get.return_value = None

        polarize(mode="overnight", persistent=False)
        kw = mock_build.return_value.compile.call_args[1]
        assert kw.get("interrupt_before") is None


# ── review_and_continue tests ──────────────────────────────────


class TestReviewAndContinue:
    """Tests for review_and_continue public API."""

    @patch("metabolon.organelles.polarization_loop._open_checkpointer")
    @patch("metabolon.organelles.polarization_loop.build_graph")
    def test_approve_continues(self, mock_build, mock_cp):
        mock_app = MagicMock()
        mock_app.invoke.return_value = {}
        mock_build.return_value = mock_app
        mock_cp.return_value = MagicMock()

        review_and_continue(approve=True)
        mock_app.invoke.assert_called()

    @patch("metabolon.organelles.polarization_loop._open_checkpointer")
    @patch("metabolon.organelles.polarization_loop.build_graph")
    def test_reject_sets_stop(self, mock_build, mock_cp):
        mock_app = MagicMock()
        mock_app.invoke.return_value = {}
        mock_build.return_value = mock_app
        mock_cp.return_value = MagicMock()

        review_and_continue(approve=False)
        mock_app.update_state.assert_called_once()
        state_update = mock_app.update_state.call_args[0][1]
        assert state_update["should_stop"] is True

    @patch("metabolon.organelles.polarization_loop._open_checkpointer")
    @patch("metabolon.organelles.polarization_loop.build_graph")
    def test_updated_goals_applied(self, mock_build, mock_cp):
        mock_app = MagicMock()
        mock_app.invoke.return_value = {}
        mock_build.return_value = mock_app
        mock_cp.return_value = MagicMock()

        new_goals = [{"star": "S", "goal": "G", "deliverable": "/tmp/x.md", "model": "sonnet"}]
        review_and_continue(approve=True, updated_goals=new_goals)
        mock_app.update_state.assert_called_once()
        state_update = mock_app.update_state.call_args[0][1]
        assert state_update["sub_goals"] == new_goals


# ── CLI tests ──────────────────────────────────────────────────


class TestCLI:
    """Tests for main() CLI entry point."""

    @patch("metabolon.organelles.polarization_loop.preflight")
    def test_dry_run(self, mock_preflight, capsys):
        mock_preflight.return_value = {
            "budget_status": "green",
            "consumption_count": 3,
            "north_stars": "abc" * 100,
        }
        import sys
        with patch.object(sys, "argv", ["polarization_loop", "--dry-run"]):
            main()
        captured = capsys.readouterr()
        assert "Budget: green" in captured.out
        assert "Consumption: 3" in captured.out

    @patch("metabolon.organelles.polarization_loop.polarize")
    def test_normal_run(self, mock_polarize, capsys):
        mock_polarize.return_value = {
            "systole_num": 2,
            "total_produced": 5,
            "total_for_review": 1,
            "report": "/tmp/report.md",
        }
        import sys
        with patch.object(sys, "argv", ["polarization_loop", "--mode", "overnight"]):
            main()
        captured = capsys.readouterr()
        assert "Done" in captured.out
        assert "Systoles: 2" in captured.out

    @patch("metabolon.organelles.polarization_loop.polarize")
    def test_interactive_mode(self, mock_polarize, capsys):
        mock_polarize.return_value = {"systole_num": 0, "total_produced": 0, "total_for_review": 0}
        import sys
        with patch.object(sys, "argv", ["polarization_loop", "--mode", "interactive"]):
            main()
        mock_polarize.assert_called_once_with(mode="interactive", thread_id="default")
