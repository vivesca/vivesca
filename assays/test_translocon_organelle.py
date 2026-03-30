"""Tests for translocon organelle + MCP enzyme.

TDD red→green cycle:
  1. These tests import from metabolon.organelles.translocon.
  2. All backend calls are mocked — no real goose/droid/API calls.
  3. Tests verify structured dict returns and routing logic.
"""
from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest


# ---------------------------------------------------------------------------
# Organelle tests — dispatch()
# ---------------------------------------------------------------------------


class TestDispatchExploreReturnsStructured:
    """dispatch() returns {success, output, backend, duration_s}."""

    @patch("metabolon.organelles.translocon._direct_api")
    @patch("metabolon.organelles.translocon._inject_coaching", side_effect=lambda p: p)
    @patch("metabolon.organelles.translocon._read_dir_context", return_value="")
    def test_explore_mode_direct_api_success(self, mock_ctx, mock_coach, mock_api):
        from metabolon.organelles.translocon import dispatch

        mock_api.return_value = {"success": True, "output": "hello world", "returncode": 0}
        result = dispatch("say hello", mode="explore")
        assert isinstance(result, dict)
        assert "success" in result
        assert "output" in result
        assert "backend" in result
        assert "duration_s" in result
        assert result["success"] is True
        assert result["backend"] == "direct"

    @patch("metabolon.organelles.translocon._run_captured")
    @patch("metabolon.organelles.translocon._inject_coaching", side_effect=lambda p: p)
    @patch("metabolon.organelles.translocon._read_dir_context", return_value="")
    @patch("metabolon.organelles.translocon._direct_api")
    def test_explore_falls_back_to_goose(self, mock_api, mock_ctx, mock_coach, mock_run):
        from metabolon.organelles.translocon import dispatch

        mock_api.return_value = {"success": False, "output": "", "returncode": 1}
        mock_run.return_value = (0, "goose output")
        result = dispatch("say hello", mode="explore")
        assert result["success"] is True
        assert result["output"] == "goose output"
        assert result["backend"] == "goose"


class TestDispatchSkillLoadsRecipe:
    """dispatch(skill='etiology') loads recipe and passes to goose."""

    @patch("metabolon.organelles.translocon._inject_coaching", side_effect=lambda p: p)
    def test_skill_not_found_returns_error(self, mock_coach):
        from metabolon.organelles.translocon import dispatch

        # Patch Path.home to return a fake home where no recipe exists
        fake_home = Path("/tmp/nonexistent_home_for_test")
        with patch.object(Path, "home", return_value=fake_home):
            result = dispatch("do a thing", mode="skill", skill="nonexistent_skill")
        assert result["success"] is False
        assert "not found" in result["output"].lower()

    @patch("metabolon.organelles.translocon._run_captured")
    @patch("metabolon.organelles.translocon._inject_coaching", side_effect=lambda p: p)
    def test_skill_routes_to_goose(self, mock_coach, mock_run):
        from metabolon.organelles.translocon import dispatch

        # Create a fake recipe file so the skill validation passes
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "germline" / "membrane" / "receptors" / "etiology"
            skill_dir.mkdir(parents=True)
            recipe = skill_dir / "recipe.yaml"
            recipe.write_text("name: etiology\n")

            fake_home = Path(tmpdir)
            mock_run.return_value = (0, "skill output")

            with patch.object(Path, "home", return_value=fake_home):
                result = dispatch(
                    "diagnose the bug", mode="skill", skill="etiology"
                )

        assert result["success"] is True
        assert result["backend"] == "goose"


class TestDispatchMcpUsesDroid:
    """dispatch(mode='mcp') routes to droid with --auto high."""

    @patch("metabolon.organelles.translocon._run_captured")
    @patch("metabolon.organelles.translocon._inject_coaching", side_effect=lambda p: p)
    def test_mcp_routes_to_droid(self, mock_coach, mock_run):
        from metabolon.organelles.translocon import dispatch

        mock_run.return_value = (0, "mcp output")
        result = dispatch("build a tool", mode="mcp")
        assert result["success"] is True
        assert result["backend"] == "droid"
        # Verify --auto high was in the command
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "--auto" in cmd
        assert "high" in cmd

    @patch("metabolon.organelles.translocon._run_captured")
    @patch("metabolon.organelles.translocon._inject_coaching", side_effect=lambda p: p)
    def test_safe_mode_routes_to_droid(self, mock_coach, mock_run):
        from metabolon.organelles.translocon import dispatch

        mock_run.return_value = (0, "audit done")
        result = dispatch("audit this", mode="safe")
        assert result["success"] is True
        assert result["backend"] == "droid"


class TestDispatchBuildMode:
    """dispatch(mode='build') routes to goose with GLM-5.1."""

    @patch("metabolon.organelles.translocon._run_captured")
    @patch("metabolon.organelles.translocon._inject_coaching", side_effect=lambda p: p)
    def test_build_uses_goose(self, mock_coach, mock_run):
        from metabolon.organelles.translocon import dispatch

        mock_run.return_value = (0, "built it")
        result = dispatch("implement feature X", mode="build")
        assert result["success"] is True
        assert result["backend"] == "goose"
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        # GLM-5.1 for build mode
        assert "GLM-5.1" in cmd


# ---------------------------------------------------------------------------
# MCP enzyme test — translocon_dispatch wraps organelle
# ---------------------------------------------------------------------------


class TestMcpToolWrapsOrganelle:
    """translocon_dispatch MCP tool delegates to organelle and returns EffectorResult."""

    @patch("metabolon.organelles.translocon.dispatch")
    def test_returns_effector_result(self, mock_dispatch):
        from metabolon.enzymes.pseudopod import translocon_dispatch
        from metabolon.morphology.base import EffectorResult

        mock_dispatch.return_value = {
            "success": True,
            "output": "test output",
            "backend": "direct",
            "duration_s": 1.2,
        }
        result = translocon_dispatch(prompt="hello")
        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert result.data["backend"] == "direct"
        assert result.data["duration_s"] == 1.2

    @patch("metabolon.organelles.translocon.dispatch")
    def test_failure_propagates(self, mock_dispatch):
        from metabolon.enzymes.pseudopod import translocon_dispatch
        from metabolon.morphology.base import EffectorResult

        mock_dispatch.return_value = {
            "success": False,
            "output": "skill not found",
            "backend": "goose",
            "duration_s": 0.5,
        }
        result = translocon_dispatch(prompt="bad skill", mode="skill", skill="nope")
        assert isinstance(result, EffectorResult)
        assert result.success is False


# ---------------------------------------------------------------------------
# Helper tests — coaching injection, eval
# ---------------------------------------------------------------------------


class TestInjectCoaching:
    """Coaching notes prepended when file exists."""

    def test_no_coaching_file(self):
        from metabolon.organelles.translocon import _inject_coaching

        with patch("metabolon.organelles.translocon.COACHING_NOTES") as mock_path:
            mock_path.exists.return_value = False
            result = _inject_coaching("do stuff")
        assert result == "do stuff"

    def test_coaching_prepended(self):
        from metabolon.organelles.translocon import _inject_coaching

        with patch("metabolon.organelles.translocon.COACHING_NOTES") as mock_path:
            mock_path.exists.return_value = True
            mock_path.read_text.return_value = "---\nfrontmatter\n---\nCoaching notes here"
            result = _inject_coaching("do stuff")
        assert "Coaching notes here" in result
        assert "do stuff" in result


class TestRunEval:
    """run_eval reads sortase traces and returns structured summary."""

    def test_no_log_returns_error(self):
        import metabolon.organelles.translocon as translocon_mod
        from metabolon.organelles.translocon import run_eval

        # Patch the module-level SORTASE_LOG to a non-existent path
        fake_log = Path("/tmp/nonexistent_sortase_log_for_test.jsonl")
        with patch.object(translocon_mod, "SORTASE_LOG", fake_log):
            result = run_eval()
        assert result["success"] is False
        assert "no sortase log" in result["output"].lower()

    def test_eval_returns_summary(self):
        import metabolon.organelles.translocon as translocon_mod
        from metabolon.organelles.translocon import run_eval

        traces = [
            json.dumps({"tool": "scout", "success": True, "duration_s": 5.0}),
            json.dumps({"tool": "scout", "success": False, "duration_s": 10.0,
                        "failure_reason": "timeout"}),
        ]
        fake_file = "\n".join(traces)

        # Use a real temp file so open() works naturally
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write(fake_file)
            f.flush()
            fake_log_path = Path(f.name)

        try:
            with patch.object(translocon_mod, "SORTASE_LOG", fake_log_path):
                result = run_eval(count=20, failures_only=False)
        finally:
            fake_log_path.unlink(missing_ok=True)

        assert result["success"] is True
        assert "output" in result
        assert "2" in result["output"]  # total traces
