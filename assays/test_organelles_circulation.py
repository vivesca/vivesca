"""Tests for circulation.py — mocks all external API calls and file I/O."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from metabolon.organelles.circulation import (
    CirculationState,
    preflight,
    select_goals,
    dispatch,
    evaluate,
    compound,
    checkpoint_node,
    write_report,
    should_continue,
    build_graph,
    _open_checkpointer,
    circulate,
    review_and_continue,
    CHECKPOINT_DB,
    NORTH_STAR_PATH,
    praxis,
)


class TestPreflight:
    """Test preflight node loads context and budget."""

    def test_preflight_no_files(self):
        """Preflight returns empty strings when files don't exist."""
        with patch("metabolon.organelles.circulation.NORTH_STAR_PATH.exists") as mock_ns_exists:
            mock_ns_exists.return_value = False
            with patch("metabolon.organelles.circulation.praxis.exists") as mock_praxis_exists:
                mock_praxis_exists.return_value = False
                with patch("metabolon.organelles.circulation.Path.exists") as mock_path_exists:
                    mock_path_exists.return_value = False

                    state: CirculationState = {"systole_num": 0}
                    result = preflight(state)

                    assert result["north_stars"] == ""
                    assert result["praxis_items"] == ""
                    assert result["budget_status"] == "green"
                    assert result["systole_num"] == 1

    def test_preflight_with_files_green_budget(self):
        """Preflight loads content and reads green budget."""
        mock_ns = MagicMock()
        mock_ns.exists.return_value = True
        mock_ns.read_text.return_value = "North star 1: Improve testing\nNorth star 2: Fix bugs"

        mock_praxis_path = MagicMock()
        mock_praxis_path.exists.return_value = True
        mock_praxis_path.read_text.return_value = "- Task 1\n- Task 2\n- Task 3"

        allo_state = '{"tier": "anabolic"}'
        mock_allo_path = MagicMock()
        mock_allo_path.exists.return_value = True
        mock_allo_path.read_text.return_value = allo_state

        with patch("metabolon.organelles.circulation.NORTH_STAR_PATH", mock_ns):
            with patch("metabolon.organelles.circulation.praxis", mock_praxis_path):
                with patch("metabolon.organelles.circulation.Path") as mock_path:
                    mock_path.return_value = mock_allo_path

                    state: CirculationState = {"systole_num": 1}
                    result = preflight(state)

                    assert "Improve testing" in result["north_stars"]
                    assert "Task 1" in result["praxis_items"]
                    assert result["budget_status"] == "green"
                    assert result["systole_num"] == 2

    def test_preflight_red_budget_catabolic(self):
        """Preflight detects red budget for catabolic tier."""
        allo_state = '{"tier": "catabolic"}'
        mock_allo_path = MagicMock()
        mock_allo_path.exists.return_value = True
        mock_allo_path.read_text.return_value = allo_state

        with patch("metabolon.organelles.circulation.NORTH_STAR_PATH.exists") as mock_ns_exists:
            mock_ns_exists.return_value = False
            with patch("metabolon.organelles.circulation.praxis.exists") as mock_praxis_exists:
                mock_praxis_exists.return_value = False
                with patch("metabolon.organelles.circulation.Path") as mock_path:
                    mock_path.return_value = mock_allo_path

                    state: CirculationState = {"systole_num": 0}
                    result = preflight(state)
                    assert result["budget_status"] == "red"

    def test_preflight_yellow_budget_homeostatic(self):
        """Preflight detects yellow budget for homeostatic tier."""
        allo_state = '{"tier": "homeostatic"}'
        mock_allo_path = MagicMock()
        mock_allo_path.exists.return_value = True
        mock_allo_path.read_text.return_value = allo_state

        with patch("metabolon.organelles.circulation.NORTH_STAR_PATH.exists") as mock_ns_exists:
            mock_ns_exists.return_value = False
            with patch("metabolon.organelles.circulation.praxis.exists") as mock_praxis_exists:
                mock_praxis_exists.return_value = False
                with patch("metabolon.organelles.circulation.Path") as mock_path:
                    mock_path.return_value = mock_allo_path

                    state: CirculationState = {"systole_num": 0}
                    result = preflight(state)
                    assert result["budget_status"] == "yellow"


class TestSelectGoals:
    """Test select_goals node parses LLM output."""

    @patch("metabolon.organelles.circulation.transduce")
    def test_select_goals_success_parses_json(self, mock_transduce):
        """select_goals correctly parses JSON from transduce."""
        mock_transduce.return_value = '''[
            {"star": "Testing", "goal": "Write tests", "deliverable": "tests/circulation.py", "model": "sonnet"},
            {"star": "Quality", "goal": "Fix bugs", "deliverable": "fixes.diff", "model": "claude"}
        ]'''

        state: CirculationState = {
            "north_stars": "North stars content",
            "praxis_items": "Praxis items",
            "budget_status": "green",
            "systole_num": 1,
            "total_produced": 0,
            "mode": "overnight",
        }

        result = select_goals(state)

        assert "selected_goals" in result
        assert len(result["selected_goals"]) == 2
        assert result["selected_goals"][0]["star"] == "Testing"
        assert result["selected_goals"][0]["deliverable"] == "tests/circulation.py"
        mock_transduce.assert_called_once()

    @patch("metabolon.organelles.circulation.transduce")
    def test_select_goals_json_extraction_with_extra_text(self, mock_transduce):
        """select_goals extracts JSON from surrounding text."""
        mock_transduce.return_value = '''Here's your selection:
        [
            {"star": "Testing", "goal": "Write tests", "deliverable": "tests/circulation.py", "model": "sonnet"}
        ]
        That's it!'''

        state: CirculationState = {
            "north_stars": "North stars content",
            "praxis_items": "Praxis items",
            "budget_status": "green",
            "systole_num": 1,
            "total_produced": 0,
            "mode": "overnight",
        }

        result = select_goals(state)
        assert len(result["selected_goals"]) == 1
        assert result["selected_goals"][0]["goal"] == "Write tests"

    @patch("metabolon.organelles.circulation.transduce")
    def test_select_goals_invalid_json_adds_error(self, mock_transduce):
        """select_goals adds error on invalid JSON."""
        mock_transduce.return_value = "Not valid JSON at all"

        state: CirculationState = {
            "north_stars": "North stars content",
            "praxis_items": "Praxis items",
            "budget_status": "green",
            "systole_num": 1,
            "total_produced": 0,
            "mode": "overnight",
        }

        result = select_goals(state)
        assert "errors" in result
        assert len(result["errors"]) == 1
        assert "Goal selection failed to parse" in result["errors"][0]

    @patch("metabolon.organelles.circulation.transduce")
    def test_select_goals_respects_max_goals_overnight(self, mock_transduce):
        """Overnight mode limits to 8 goals."""
        goals = [{"star": f"S{i}", "goal": f"G{i}", "deliverable": f"path{i}", "model": "sonnet"} for i in range(10)]
        mock_transduce.return_value = json.dumps(goals)

        state: CirculationState = {
            "north_stars": "x",
            "praxis_items": "y",
            "budget_status": "green",
            "systole_num": 1,
            "total_produced": 0,
            "mode": "overnight",
        }

        result = select_goals(state)
        assert len(result["selected_goals"]) == 8

    @patch("metabolon.organelles.circulation.transduce")
    def test_select_goals_respects_max_goals_interactive(self, mock_transduce):
        """Interactive mode limits to 4 goals."""
        goals = [{"star": f"S{i}", "goal": f"G{i}", "deliverable": f"path{i}", "model": "sonnet"} for i in range(10)]
        mock_transduce.return_value = json.dumps(goals)

        state: CirculationState = {
            "north_stars": "x",
            "praxis_items": "y",
            "budget_status": "green",
            "systole_num": 1,
            "total_produced": 0,
            "mode": "interactive",
        }

        result = select_goals(state)
        assert len(result["selected_goals"]) == 4


class TestDispatch:
    """Test dispatch node executes selected goals."""

    @patch("metabolon.organelles.circulation.transduce_safe")
    def test_dispatch_no_selected_goals_adds_error(self, mock_transduce_safe):
        """No goals → error added."""
        state: CirculationState = {"selected_goals": []}
        result = dispatch(state)
        assert "errors" in result
        assert len(result["errors"]) == 1
        mock_transduce_safe.assert_not_called()

    @patch("metabolon.organelles.circulation.transduce_safe")
    def test_dispatch_executes_all_goals(self, mock_transduce_safe):
        """Dispatches each goal to transduce_safe."""
        mock_transduce_safe.side_effect = [
            ("sonnet", "Output for first task"),
            ("claude", "Output for second task"),
        ]

        state: CirculationState = {
            "selected_goals": [
                {"star": "S1", "goal": "G1", "deliverable": "/tmp/test1.txt", "model": "sonnet"},
                {"star": "S2", "goal": "G2", "deliverable": "/tmp/test2.txt", "model": "claude"},
            ]
        }

        with patch("metabolon.organelles.circulation.Path") as mock_path:
            mock_path_instance = MagicMock()
            mock_path.return_value = mock_path_instance
            mock_path_instance.replace.return_value = mock_path_instance
            mock_path_instance.parent = MagicMock()
            mock_path_instance.parent.mkdir = MagicMock()
            mock_path_instance.write_text = MagicMock()

            result = dispatch(state)

            assert len(result["dispatched_work"]) == 2
            assert result["dispatched_work"][0]["success"] is True
            assert result["dispatched_work"][1]["success"] is True
            assert mock_transduce_safe.call_count == 2
            assert mock_path_instance.write_text.called

    @patch("metabolon.organelles.circulation.transduce_safe")
    def test_dispatch_marks_failure_on_error_prefix(self, mock_transduce_safe):
        """Error output → marked as not successful."""
        mock_transduce_safe.return_value = ("sonnet", "(error: something went wrong)")

        state: CirculationState = {
            "selected_goals": [
                {"star": "S1", "goal": "G1", "deliverable": "/tmp/test1.txt", "model": "sonnet"},
            ]
        }

        result = dispatch(state)
        assert len(result["dispatched_work"]) == 1
        assert not result["dispatched_work"][0]["success"]


class TestEvaluate:
    """Test evaluate node classifies outputs."""

    @patch("metabolon.organelles.circulation.transduce")
    def test_evaluate_no_successful_work(self, mock_transduce):
        """No successful work → returns counts unchanged."""
        state: CirculationState = {
            "dispatched_work": [
                {"success": False, "goal": "Failed"},
            ],
            "total_produced": 5,
            "total_for_review": 2,
        }

        result = evaluate(state)
        assert result["total_produced"] == 5
        assert result["total_for_review"] == 2
        assert "No successful outputs" in result["evaluation"]
        mock_transduce.assert_not_called()

    @patch("metabolon.organelles.circulation.transduce")
    def test_evaluate_parses_json_counts_review(self, mock_transduce):
        """Correctly parses evaluation and counts needs-review."""
        mock_transduce.return_value = '''[
            {"goal": "G1", "classification": "self-sufficient", "quality": "pass", "reason": "Good"},
            {"goal": "G2", "classification": "needs-review", "quality": "partial", "reason": "Needs work"}
        ]'''

        state: CirculationState = {
            "dispatched_work": [
                {"goal": "G1", "success": True, "output": "output1", "star": "S1"},
                {"goal": "G2", "success": True, "output": "output2", "star": "S2"},
            ],
            "total_produced": 0,
            "total_for_review": 0,
        }

        result = evaluate(state)
        assert result["total_produced"] == 2
        assert result["total_for_review"] == 1
        mock_transduce.assert_called_once()


class TestCompound:
    """Test compound node generates follow-up ideas."""

    @patch("metabolon.organelles.circulation.transduce")
    def test_compound_no_successful_work_returns_empty(self, mock_transduce):
        """No successful work → empty list."""
        state: CirculationState = {"dispatched_work": []}
        result = compound(state)
        assert result["compound_ideas"] == []
        mock_transduce.assert_not_called()

    @patch("metabolon.organelles.circulation.transduce")
    def test_compound_extracts_ideas_from_json(self, mock_transduce):
        """Extracts idea strings from JSON response."""
        mock_transduce.return_value = '''[
            {"idea": "Extend this to other modules", "star": "Testing", "type": "compound"},
            {"idea": "Explore automation of this category", "star": "Automation", "type": "scout"}
        ]'''

        state: CirculationState = {
            "dispatched_work": [
                {"goal": "G1", "success": True, "star": "S1"},
            ]
        }

        result = compound(state)
        assert len(result["compound_ideas"]) == 2
        assert "Extend this" in result["compound_ideas"][0]


class TestCheckpointNode:
    """Test checkpoint_node writes manifest and makes stop decision."""

    def test_checkpoint_budget_red_stops(self):
        """Budget red → should_stop=True."""
        state: CirculationState = {
            "budget_status": "red",
            "systole_num": 3,
            "total_produced": 5,
            "total_for_review": 2,
            "dispatched_work": [],
        }

        with patch("metabolon.organelles.circulation.MANIFEST_PATH") as mock_manifest:
            mock_manifest.parent = MagicMock()
            mock_manifest.parent.mkdir = MagicMock()
            mock_manifest.write_text = MagicMock()

            result = checkpoint_node(state)
            assert result["should_stop"] is True
            assert "Budget red" in result["stop_reason"]

    def test_checkpoint_budget_yellow_stops(self):
        """Budget yellow → should_stop=True after systole."""
        state: CirculationState = {
            "budget_status": "yellow",
            "systole_num": 3,
            "total_produced": 5,
            "total_for_review": 2,
            "dispatched_work": [],
        }

        with patch("metabolon.organelles.circulation.MANIFEST_PATH") as mock_manifest:
            mock_manifest.parent = MagicMock()
            mock_manifest.parent.mkdir = MagicMock()
            mock_manifest.write_text = MagicMock()

            result = checkpoint_node(state)
            assert result["should_stop"] is True
            assert "Budget yellow" in result["stop_reason"]

    def test_checkpoint_no_selected_goals_stops(self):
        """No selected goals → stop."""
        state: CirculationState = {
            "budget_status": "green",
            "selected_goals": [],
            "systole_num": 3,
            "total_produced": 5,
            "total_for_review": 2,
            "dispatched_work": [],
        }

        with patch("metabolon.organelles.circulation.MANIFEST_PATH") as mock_manifest:
            mock_manifest.parent = MagicMock()
            mock_manifest.parent.mkdir = MagicMock()
            mock_manifest.write_text = MagicMock()

            result = checkpoint_node(state)
            assert result["should_stop"] is True
            assert "No goals could be selected" in result["stop_reason"]

    def test_checkpoint_budget_green_continues(self):
        """Budget green with goals → continue."""
        state: CirculationState = {
            "budget_status": "green",
            "selected_goals": [{"star": "S1", "goal": "G1"}],
            "systole_num": 3,
            "total_produced": 5,
            "total_for_review": 2,
            "dispatched_work": [],
        }

        with patch("metabolon.organelles.circulation.MANIFEST_PATH") as mock_manifest:
            mock_manifest.parent = MagicMock()
            mock_manifest.parent.mkdir = MagicMock()
            mock_manifest.write_text = MagicMock()

            result = checkpoint_node(state)
            assert not result["should_stop"]


class TestWriteReport:
    """Test write_report node outputs report file."""

    def test_write_report_creates_file(self):
        """write_report writes markdown report to REPORT_DIR."""
        state: CirculationState = {
            "systole_num": 3,
            "total_produced": 5,
            "total_for_review": 2,
            "stop_reason": "Budget exhausted",
            "mode": "overnight",
            "dispatched_work": [
                {"star": "S1", "goal": "G1", "success": True},
                {"star": "S2", "goal": "G2", "success": False},
            ],
            "errors": ["One error happened"],
        }

        with patch("metabolon.organelles.circulation.REPORT_DIR") as mock_report_dir:
            mock_report_dir.mkdir = MagicMock()
            mock_report_path = MagicMock()
            mock_report_dir.__truediv__.return_value = mock_report_path

            result = write_report(state)

            assert "report" in result
            assert mock_report_path.write_text.called
            args = mock_report_path.write_text.call_args[0][0]
            assert "Poiesis Report" in args
            assert "One error happened" in args
            assert "[FAILED] **S2**" in args


class TestRouting:
    """Test should_continue routing."""

    def test_should_continue_stops(self):
        """should_stop=True → report."""
        state: CirculationState = {"should_stop": True}
        assert should_continue(state) == "report"

    def test_should_continue_continues(self):
        """should_stop=False → preflight."""
        state: CirculationState = {"should_stop": False}
        assert should_continue(state) == "preflight"


class TestBuildGraph:
    """Test graph assembly."""

    def test_build_graph_creates_correct_structure(self):
        """build_graph adds all nodes and edges."""
        graph = build_graph()
        # Just check it compiles without errors
        assert graph is not None
        # Check entry point is set
        assert graph.entry_point == "preflight"


class TestOpenCheckpointer:
    """Test _open_checkpointer factory."""

    def test_non_persistent_returns_in_memory(self):
        """persistent=False → InMemorySaver."""
        result = _open_checkpointer(persistent=False)
        assert result.__class__.__name__ == "InMemorySaver"

    @patch("sqlite3.connect")
    def test_persistent_returns_sqlite_saver(self, mock_connect):
        """persistent=True → SqliteSaver with connection."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        with patch("metabolon.organelles.circulation.CHECKPOINT_DB") as mock_db:
            mock_db.parent = MagicMock()
            mock_db.parent.mkdir = MagicMock()

            result = _open_checkpointer(persistent=True)
            assert result.__class__.__name__ == "SqliteSaver"
            assert mock_connect.called


class TestCirculate:
    """Test main circulate entry point."""

    @patch("metabolon.organelles.circulation._open_checkpointer")
    def test_circulate_creates_initial_state_and_runs(self, mock_open_checkpointer):
        """circulate compiles graph and invokes with initial state."""
        mock_checkpointer = MagicMock()
        mock_open_checkpointer.return_value = mock_checkpointer
        mock_checkpointer.get.return_value = None  # No existing checkpoint

        # Mock the compiled app
        mock_app = MagicMock()
        mock_app.invoke.return_value = {"systole_num": 1, "total_produced": 0}

        with patch("metabolon.organelles.circulation.build_graph") as mock_build_graph:
            mock_graph = MagicMock()
            mock_graph.compile.return_value = mock_app
            mock_build_graph.return_value = mock_graph

            result = circulate(mode="overnight", persistent=False, resume=True)

            assert "systole_num" in result
            assert mock_build_graph.called
            assert mock_graph.compile.called
            assert mock_app.invoke.called


def test_ast_parse():
    """Smoke test: ensure the module parses."""
    import ast
    import os

    source = open(os.path.join(os.path.dirname(__file__), "../metabolon/organelles/circulation.py"), "r").read()
    ast.parse(source)
    # Should not raise
