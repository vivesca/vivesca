"""Tests for circulation.py — mock external LLM calls and file operations."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.circulation import (
    CirculationState,
    _open_checkpointer,
    build_graph,
    checkpoint_node,
    compound,
    circulate,
    dispatch,
    evaluate,
    preflight,
    select_goals,
    should_continue,
    write_report,
)


def test_preflight_no_files():
    """Test preflight when no files exist — should return empty content."""
    state: CirculationState = {
        "systole_num": 0,
        "mode": "overnight",
        "north_stars": "",
        "praxis_items": "",
        "budget_status": "green",
        "selected_goals": [],
        "dispatched_work": [],
        "evaluation": "",
        "compound_ideas": [],
        "total_produced": 0,
        "total_for_review": 0,
        "errors": [],
        "should_stop": False,
        "stop_reason": "",
        "report": "",
    }

    with patch("metabolon.organelles.circulation.NORTH_STAR_PATH", Path("/nonexistent/nothing.md")):
        with patch("metabolon.organelles.circulation.praxis", Path("/nonexistent/praxis.md")):
            with patch("metabolon.organelles.circulation.Path.home") as mock_home:
                mock_home.return_value = Path("/tmp")
                result = preflight(state)

    assert result["systole_num"] == 1
    assert result["north_stars"] == ""
    assert result["praxis_items"] == ""
    assert result["budget_status"] == "green"


def test_preflight_with_budget_red():
    """Test preflight reads allostasis state and correctly detects red budget."""
    state: CirculationState = {
        "systole_num": 0,
        "mode": "overnight",
        "north_stars": "",
        "praxis_items": "",
        "budget_status": "green",
        "selected_goals": [],
        "dispatched_work": [],
        "evaluation": "",
        "compound_ideas": [],
        "total_produced": 0,
        "total_for_review": 0,
        "errors": [],
        "should_stop": False,
        "stop_reason": "",
        "report": "",
    }

    allo_data = {"tier": "autophagic-catabolic"}
    allo_path = Path("/tmp/claude/allostasis-state.json")
    allo_path.parent.mkdir(parents=True, exist_ok=True)
    allo_path.write_text(json.dumps(allo_data))

    with patch("metabolon.organelles.circulation.NORTH_STAR_PATH", Path("/nonexistent/nothing.md")):
        with patch("metabolon.organelles.circulation.praxis", Path("/nonexistent/praxis.md")):
            with patch("metabolon.organelles.circulation.Path.home") as mock_home:
                mock_home.return_value = Path("/tmp")
                result = preflight(state)

    assert result["budget_status"] == "red"
    allo_path.unlink()


def test_select_goals_parses_valid_json():
    """Test select_goals correctly parses valid JSON response."""
    mock_goals = [
        {"star": "Improve testing", "goal": "Write tests for circulation", "deliverable": "assays/test_organelles_circulation.py", "model": "claude"}
    ]

    state: CirculationState = {
        "north_stars": "Test north stars",
        "praxis_items": "Test praxis",
        "budget_status": "green",
        "mode": "overnight",
        "systole_num": 1,
        "selected_goals": [],
        "dispatched_work": [],
        "evaluation": "",
        "compound_ideas": [],
        "total_produced": 0,
        "total_for_review": 0,
        "errors": [],
        "should_stop": False,
        "stop_reason": "",
        "report": "",
    }

    with patch("metabolon.organelles.circulation.transduce", return_value=json.dumps(mock_goals)):
        result = select_goals(state)

    assert len(result["selected_goals"]) == 1
    assert result["selected_goals"][0]["star"] == "Improve testing"


def test_select_goals_handles_parse_error():
    """Test select_goals handles invalid JSON gracefully."""
    state: CirculationState = {
        "north_stars": "Test north stars",
        "praxis_items": "Test praxis",
        "budget_status": "green",
        "mode": "overnight",
        "systole_num": 1,
        "selected_goals": [],
        "dispatched_work": [],
        "evaluation": "",
        "compound_ideas": [],
        "total_produced": 0,
        "total_for_review": 0,
        "errors": [],
        "should_stop": False,
        "stop_reason": "",
        "report": "",
    }

    with patch("metabolon.organelles.circulation.transduce", return_value="Not valid JSON"):
        result = select_goals(state)

    assert len(result["errors"]) == 1
    assert "Goal selection failed to parse" in result["errors"][0]


def test_select_goals_overnight_max_goals():
    """Test overnight mode allows up to 8 goals."""
    mock_goals = [{"star": f"Star {i}", "goal": f"Goal {i}", "deliverable": f"file{i}.md", "model": "sonnet"} for i in range(10)]

    state: CirculationState = {
        "north_stars": "Test",
        "praxis_items": "Test",
        "budget_status": "green",
        "mode": "overnight",
        "systole_num": 1,
        "selected_goals": [],
        "dispatched_work": [],
        "evaluation": "",
        "compound_ideas": [],
        "total_produced": 0,
        "total_for_review": 0,
        "errors": [],
        "should_stop": False,
        "stop_reason": "",
        "report": "",
    }

    with patch("metabolon.organelles.circulation.transduce", return_value=json.dumps(mock_goals)):
        result = select_goals(state)

    assert len(result["selected_goals"]) == 8


def test_dispatch_no_selected_goals():
    """Test dispatch when no goals are selected returns error."""
    state: CirculationState = {
        "selected_goals": [],
        "dispatched_work": [],
        "north_stars": "",
        "praxis_items": "",
        "budget_status": "green",
        "mode": "overnight",
        "systole_num": 1,
        "evaluation": "",
        "compound_ideas": [],
        "total_produced": 0,
        "total_for_review": 0,
        "errors": [],
        "should_stop": False,
        "stop_reason": "",
        "report": "",
    }

    result = dispatch(state)
    assert len(result["errors"]) == 1
    assert "No goals selected" in result["errors"][0]


def test_dispatch_with_goals_mock():
    """Test dispatch executes goals and returns results."""
    mock_goals = [
        {"star": "Test", "goal": "Write test", "deliverable": "/tmp/test-output.md", "model": "claude"}
    ]

    state: CirculationState = {
        "selected_goals": mock_goals,
        "dispatched_work": [],
        "north_stars": "",
        "praxis_items": "",
        "budget_status": "green",
        "mode": "overnight",
        "systole_num": 1,
        "evaluation": "",
        "compound_ideas": [],
        "total_produced": 0,
        "total_for_review": 0,
        "errors": [],
        "should_stop": False,
        "stop_reason": "",
        "report": "",
    }

    with patch("metabolon.organelles.circulation.transduce_safe", return_value=("claude", "# Test Output")):
        result = dispatch(state)

    assert len(result["dispatched_work"]) == 1
    assert result["dispatched_work"][0]["success"] is True
    assert result["dispatched_work"][0]["deliverable_path"] == "/tmp/test-output.md"

    # Clean up
    Path("/tmp/test-output.md").unlink(missing_ok=True)


def test_dispatch_handles_write_error(caplog):
    """Test dispatch handles write errors gracefully."""
    mock_goals = [
        {"star": "Test", "goal": "Write test", "deliverable": "/root/protected.md", "model": "claude"}
    ]

    state: CirculationState = {
        "selected_goals": mock_goals,
        "dispatched_work": [],
        "north_stars": "",
        "praxis_items": "",
        "budget_status": "green",
        "mode": "overnight",
        "systole_num": 1,
        "evaluation": "",
        "compound_ideas": [],
        "total_produced": 0,
        "total_for_review": 0,
        "errors": [],
        "should_stop": False,
        "stop_reason": "",
        "report": "",
    }

    with patch("metabolon.organelles.circulation.transduce_safe", return_value=("claude", "content")):
        result = dispatch(state)

    assert "write_error" in result["dispatched_work"][0]


def test_evaluate_no_successful_work():
    """Test evaluate when no successful work returns empty stats."""
    state: CirculationState = {
        "dispatched_work": [{"success": False, "goal": "Failed"}],
        "north_stars": "",
        "praxis_items": "",
        "budget_status": "green",
        "mode": "overnight",
        "systole_num": 1,
        "selected_goals": [],
        "evaluation": "",
        "compound_ideas": [],
        "total_produced": 0,
        "total_for_review": 0,
        "errors": [],
        "should_stop": False,
        "stop_reason": "",
        "report": "",
    }

    result = evaluate(state)
    assert result["total_produced"] == 0
    assert result["total_for_review"] == 0


def test_evaluate_with_successful_work_parses_json():
    """Test evaluate parses JSON evaluation correctly."""
    mock_eval = [
        {"goal": "Write tests", "classification": "self-sufficient", "quality": "pass", "reason": "Good"}
    ]

    state: CirculationState = {
        "dispatched_work": [{"goal": "Write tests", "success": True, "output": "Test output", "star": "Testing"}],
        "total_produced": 0,
        "total_for_review": 0,
        "north_stars": "",
        "praxis_items": "",
        "budget_status": "green",
        "mode": "overnight",
        "systole_num": 1,
        "selected_goals": [],
        "evaluation": "",
        "compound_ideas": [],
        "errors": [],
        "should_stop": False,
        "stop_reason": "",
        "report": "",
    }

    with patch("metabolon.organelles.circulation.transduce", return_value=json.dumps(mock_eval)):
        result = evaluate(state)

    assert result["total_produced"] == 1
    assert result["total_for_review"] == 0


def test_compound_no_successful_work():
    """Test compound when no successful work returns empty list."""
    state: CirculationState = {
        "dispatched_work": [{"success": False}],
        "north_stars": "",
        "praxis_items": "",
        "budget_status": "green",
        "mode": "overnight",
        "systole_num": 1,
        "selected_goals": [],
        "evaluation": "",
        "compound_ideas": [],
        "total_produced": 0,
        "total_for_review": 0,
        "errors": [],
        "should_stop": False,
        "stop_reason": "",
        "report": "",
    }

    result = compound(state)
    assert result["compound_ideas"] == []


def test_compound_parses_ideas():
    """Test compound extracts ideas from JSON."""
    mock_result = [
        {"idea": "Add more tests", "star": "Testing", "type": "compound"}
    ]

    state: CirculationState = {
        "dispatched_work": [{"goal": "Write tests", "success": True, "star": "Testing"}],
        "north_stars": "",
        "praxis_items": "",
        "budget_status": "green",
        "mode": "overnight",
        "systole_num": 1,
        "selected_goals": [],
        "evaluation": "",
        "compound_ideas": [],
        "total_produced": 0,
        "total_for_review": 0,
        "errors": [],
        "should_stop": False,
        "stop_reason": "",
        "report": "",
    }

    with patch("metabolon.organelles.circulation.transduce", return_value=json.dumps(mock_result)):
        result = compound(state)

    assert len(result["compound_ideas"]) == 1
    assert "Add more tests" in result["compound_ideas"]


def test_checkpoint_node_red_budget_stops():
    """Test checkpoint stops when budget is red."""
    state: CirculationState = {
        "budget_status": "red",
        "systole_num": 3,
        "total_produced": 5,
        "total_for_review": 1,
        "dispatched_work": [],
        "selected_goals": [{}],
        "compound_ideas": [],
        "north_stars": "",
        "praxis_items": "",
        "mode": "overnight",
        "evaluation": "",
        "errors": [],
        "should_stop": False,
        "stop_reason": "",
        "report": "",
    }

    with patch("metabolon.organelles.circulation.MANIFEST_PATH", Path("/tmp/circulation-manifest-test.md")):
        result = checkpoint_node(state)

    assert result["should_stop"] is True
    assert "Budget red" in result["stop_reason"]
    Path("/tmp/circulation-manifest-test.md").unlink(missing_ok=True)


def test_checkpoint_node_green_budget_continues():
    """Test checkpoint continues when budget is green."""
    state: CirculationState = {
        "budget_status": "green",
        "systole_num": 1,
        "total_produced": 2,
        "total_for_review": 0,
        "dispatched_work": [],
        "selected_goals": [{}],
        "compound_ideas": [],
        "north_stars": "",
        "praxis_items": "",
        "mode": "overnight",
        "evaluation": "",
        "errors": [],
        "should_stop": False,
        "stop_reason": "",
        "report": "",
    }

    with patch("metabolon.organelles.circulation.MANIFEST_PATH", Path("/tmp/circulation-manifest-test.md")):
        result = checkpoint_node(state)

    assert result["should_stop"] is False
    Path("/tmp/circulation-manifest-test.md").unlink(missing_ok=True)


def test_checkpoint_node_no_goals_stops():
    """Test checkpoint stops when no goals selected."""
    state: CirculationState = {
        "budget_status": "green",
        "systole_num": 1,
        "total_produced": 0,
        "total_for_review": 0,
        "dispatched_work": [],
        "selected_goals": [],
        "compound_ideas": [],
        "north_stars": "",
        "praxis_items": "",
        "mode": "overnight",
        "evaluation": "",
        "errors": [],
        "should_stop": False,
        "stop_reason": "",
        "report": "",
    }

    with patch("metabolon.organelles.circulation.MANIFEST_PATH", Path("/tmp/circulation-manifest-test.md")):
        result = checkpoint_node(state)

    assert result["should_stop"] is True
    assert "No goals could be selected" in result["stop_reason"]
    Path("/tmp/circulation-manifest-test.md").unlink(missing_ok=True)


def test_should_continue_routing():
    """Test should_continue routes correctly."""
    assert should_continue({"should_stop": True}) == "report"
    assert should_continue({"should_stop": False}) == "preflight"


def test_write_report_creates_file():
    """Test write_report creates a report file."""
    state: CirculationState = {
        "systole_num": 3,
        "total_produced": 5,
        "total_for_review": 1,
        "mode": "overnight",
        "stop_reason": "Budget red",
        "dispatched_work": [{"success": True, "star": "Test", "goal": "Test goal"}],
        "errors": ["Some error"],
        "north_stars": "",
        "praxis_items": "",
        "budget_status": "red",
        "selected_goals": [],
        "evaluation": "",
        "compound_ideas": [],
        "should_stop": True,
        "report": "",
    }

    test_report_dir = Path("/tmp/test-vivesca-reports")
    with patch("metabolon.organelles.circulation.REPORT_DIR", test_report_dir):
        result = write_report(state)

    report_path = Path(result["report"])
    assert report_path.exists()
    content = report_path.read_text()
    assert "Poiesis Report" in content
    assert "Test goal" in content
    assert "Some error" in content

    report_path.unlink()
    test_report_dir.rmdir()


def test_build_graph():
    """Test building the graph doesn't error."""
    graph = build_graph()
    assert graph is not None


def test_open_checkpointer_inmemory():
    """Test _open_checkpointer with persistent=False returns in-memory."""
    checkpointer = _open_checkpointer(persistent=False)
    assert checkpointer.__class__.__name__ == "InMemorySaver"


def test_circulation_non_persistent():
    """Test circulate runs with non-persistent checkpointing (mocks LLM)."""
    # Patch all LLM calls
    with patch("metabolon.organelles.circulation.transduce") as mock_transduce:
        # First call for select_goals
        mock_transduce.side_effect = [
            json.dumps([{"star": "Test", "goal": "Test", "deliverable": "/tmp/test.md", "model": "claude"}]),
            json.dumps([{"goal": "Test", "classification": "self-sufficient", "quality": "pass", "reason": "OK"}]),
            json.dumps([{"idea": "Next step", "star": "Test", "type": "compound"}]),
        ]

        with patch("metabolon.organelles.circulation.transduce_safe", return_value=("claude", "Test output")):
            with patch("metabolon.organelles.circulation.CHECKPOINT_DB", Path("/tmp/test-checkpoints.db")):
                result = circulate(mode="overnight", persistent=False, resume=False)

    assert result is not None
    # Should stop because budget red in checkpoint? No, default budget green, but after one cycle,
    # it loops back to preflight → select_goals... Actually LangGraph runs until it hits END, which is after report.
    # So it should complete with a report.
    assert "systole_num" in result

    # Clean up any created files
    Path("/tmp/test.md").unlink(missing_ok=True)
    Path("/tmp/circulation-manifest.md").unlink(missing_ok=True)
