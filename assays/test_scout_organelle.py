"""Tests for scout organelle + MCP enzyme.

TDD red→green cycle:
  1. These tests import from metabolon.organelles.scout (does not exist yet).
  2. First run = red (ImportError).
  3. Implement organelle + enzyme, second run = green.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Organelle tests — dispatch()
# ---------------------------------------------------------------------------


class TestDispatchExploreReturnsStructured:
    """dispatch() returns {success, output, backend, duration_s}."""

    @patch("metabolon.organelles.scout._direct_api")
    @patch("metabolon.organelles.scout._inject_coaching", side_effect=lambda p: p)
    @patch("metabolon.organelles.scout._read_dir_context", return_value="")
    def test_explore_mode_direct_api_success(self, mock_ctx, mock_coach, mock_api):
        from metabolon.organelles.scout import dispatch

        mock_api.return_value = {"success": True, "output": "hello world", "returncode": 0}
        result = dispatch("say hello", mode="explore")
        assert isinstance(result, dict)
        assert "success" in result
        assert "output" in result
        assert "backend" in result
        assert "duration_s" in result
        assert result["success"] is True
        assert result["backend"] == "direct"

    @patch("metabolon.organelles.scout._run_captured")
    @patch("metabolon.organelles.scout._inject_coaching", side_effect=lambda p: p)
    @patch("metabolon.organelles.scout._read_dir_context", return_value="")
    @patch("metabolon.organelles.scout._direct_api")
    def test_explore_falls_back_to_goose(self, mock_api, mock_ctx, mock_coach, mock_run):
        from metabolon.organelles.scout import dispatch

        mock_api.return_value = {"success": False, "output": "", "returncode": 1}
        mock_run.return_value = (0, "goose output")
        result = dispatch("say hello", mode="explore")
        assert result["success"] is True
        assert result["output"] == "goose output"
        assert result["backend"] == "goose"


class TestDispatchSkillLoadsRecipe:
    """dispatch(skill='etiology') loads recipe and passes to goose."""

    @patch("metabolon.organelles.scout.Path")
    @patch("metabolon.organelles.scout._inject_coaching", side_effect=lambda p: p)
    def test_skill_not_found_returns_error(self, mock_coach, mock_path_cls):
        from metabolon.organelles.scout import dispatch

        # Make Path.home() / "germline/membrane/receptors/etiology/recipe.yaml"
        # resolve to a non-existent file
        mock_recipe = MagicMock()
        mock_recipe.exists.return_value = False
        mock_path_home = MagicMock()
        mock_path_home.__truediv__ = lambda self, other: (
            mock_recipe if other == "germline/membrane/receptors/etiology/recipe.yaml"
            else MagicMock()
        )
        mock_path_cls.home.return_value = mock_path_home
        # Fallback: patch via pathlib.Path directly
        import pathlib
        with patch.object(pathlib.Path, "home", return_value=mock_path_home):
            result = dispatch("do a thing", mode="skill", skill="nonexistent_skill")
        assert result["success"] is False
        assert "not found" in result["output"].lower()

    @patch("metabolon.organelles.scout.subprocess")
    @patch("metabolon.organelles.scout._inject_coaching", side_effect=lambda p: p)
    def test_skill_routes_to_goose(self, mock_coach, mock_subprocess):
        from metabolon.organelles.scout import dispatch

        # Recipe file exists
        import pathlib
        mock_recipe = MagicMock()
        mock_recipe.exists.return_value = True
        mock_recipe.__str__ = lambda self: "/fake/recipe.yaml"

        original_home = pathlib.Path.home
        def fake_home(self):
            result = original_home()
            # We need the / operator to produce our mock for the recipe path
            return _FakePathHome(result, mock_recipe)

        with patch.object(pathlib.Path, "home", fake_home):
            mock_subprocess.run.return_value = MagicMock(returncode=0, stdout="skill output\n")
            result = dispatch(
                "diagnose the bug", mode="skill", skill="etiology"
            )
        assert result["success"] is True
        assert result["backend"] == "goose"


class TestDispatchMcpUsesDroid:
    """dispatch(mode='mcp') routes to droid with --auto high."""

    @patch("metabolon.organelles.scout.subprocess")
    @patch("metabolon.organelles.scout._inject_coaching", side_effect=lambda p: p)
    def test_mcp_routes_to_droid(self, mock_coach, mock_subprocess):
        from metabolon.organelles.scout import dispatch

        mock_subprocess.run.return_value = MagicMock(returncode=0, stdout="mcp output\n")
        result = dispatch("build a tool", mode="mcp")
        assert result["success"] is True
        assert result["backend"] == "droid"
        # Verify --auto high was in the command
        call_args = mock_subprocess.run.call_args
        cmd = call_args[0][0]
        assert "--auto" in cmd
        assert "high" in cmd

    @patch("metabolon.organelles.scout.subprocess")
    @patch("metabolon.organelles.scout._inject_coaching", side_effect=lambda p: p)
    def test_safe_mode_routes_to_droid(self, mock_coach, mock_subprocess):
        from metabolon.organelles.scout import dispatch

        mock_subprocess.run.return_value = MagicMock(returncode=0, stdout="audit done\n")
        result = dispatch("audit this", mode="safe")
        assert result["success"] is True
        assert result["backend"] == "droid"


class TestDispatchBuildMode:
    """dispatch(mode='build') routes to goose with GLM-5.1."""

    @patch("metabolon.organelles.scout.subprocess")
    @patch("metabolon.organelles.scout._inject_coaching", side_effect=lambda p: p)
    def test_build_uses_goose(self, mock_coach, mock_subprocess):
        from metabolon.organelles.scout import dispatch

        mock_subprocess.run.return_value = MagicMock(returncode=0, stdout="built it\n")
        result = dispatch("implement feature X", mode="build")
        assert result["success"] is True
        assert result["backend"] == "goose"
        call_args = mock_subprocess.run.call_args
        cmd = call_args[0][0]
        # GLM-5.1 for build mode
        assert "GLM-5.1" in cmd


# ---------------------------------------------------------------------------
# MCP enzyme test — scout_dispatch wraps organelle
# ---------------------------------------------------------------------------


class TestMcpToolWrapsOrganelle:
    """scout_dispatch MCP tool delegates to organelle and returns EffectorResult."""

    @patch("metabolon.organelles.scout.dispatch")
    def test_returns_effector_result(self, mock_dispatch):
        from metabolon.morphology.base import EffectorResult
        from metabolon.enzymes.pseudopod import scout_dispatch

        mock_dispatch.return_value = {
            "success": True,
            "output": "test output",
            "backend": "direct",
            "duration_s": 1.2,
        }
        result = scout_dispatch(prompt="hello")
        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert result.data["backend"] == "direct"
        assert result.data["duration_s"] == 1.2

    @patch("metabolon.organelles.scout.dispatch")
    def test_failure_propagates(self, mock_dispatch):
        from metabolon.morphology.base import EffectorResult
        from metabolon.enzymes.pseudopod import scout_dispatch

        mock_dispatch.return_value = {
            "success": False,
            "output": "skill not found",
            "backend": "goose",
            "duration_s": 0.5,
        }
        result = scout_dispatch(prompt="bad skill", mode="skill", skill="nope")
        assert isinstance(result, EffectorResult)
        assert result.success is False


# ---------------------------------------------------------------------------
# Helper tests — coaching injection, eval
# ---------------------------------------------------------------------------


class TestInjectCoaching:
    """Coaching notes prepended when file exists."""

    def test_no_coaching_file(self):
        from metabolon.organelles.scout import _inject_coaching

        with patch("metabolon.organelles.scout.COACHING_NOTES") as mock_path:
            mock_path.exists.return_value = False
            result = _inject_coaching("do stuff")
        assert result == "do stuff"

    def test_coaching_prepended(self):
        from metabolon.organelles.scout import _inject_coaching

        with patch("metabolon.organelles.scout.COACHING_NOTES") as mock_path:
            mock_path.exists.return_value = True
            mock_path.read_text.return_value = "---\nfrontmatter\n---\nCoaching notes here"
            result = _inject_coaching("do stuff")
        assert "Coaching notes here" in result
        assert "do stuff" in result


class TestRunEval:
    """run_eval reads sortase traces and returns structured summary."""

    def test_no_log_returns_error(self):
        from metabolon.organelles.scout import run_eval

        with patch("metabolon.organelles.scout.Path") as mock_path_cls:
            mock_log = MagicMock()
            mock_log.exists.return_value = False
            mock_home = MagicMock()
            mock_home.__truediv__ = lambda s, o: mock_log
            mock_path_cls.home.return_value = mock_home
            import pathlib
            with patch.object(pathlib.Path, "home", return_value=mock_home):
                result = run_eval()
        assert result["success"] is False
        assert "no sortase log" in result["output"].lower()

    def test_eval_returns_summary(self):
        from metabolon.organelles.scout import run_eval

        import json
        traces = [
            json.dumps({"tool": "scout", "success": True, "duration_s": 5.0}),
            json.dumps({"tool": "scout", "success": False, "duration_s": 10.0, "failure_reason": "timeout"}),
        ]
        fake_file = "\n".join(traces)
        mock_log = MagicMock()
        mock_log.exists.return_value = True

        mock_home = MagicMock()
        # Need the / operator chain: home() / ".local/..." / "log.jsonl"
        def home_div(other):
            if "local" in other or "log" in other:
                return mock_log
            return MagicMock()
        mock_home.__truediv__ = home_div

        import pathlib
        with patch.object(pathlib.Path, "home", return_value=mock_home):
            with patch("builtins.open", MagicMock(return_value=iter(fake_file.splitlines()))):
                result = run_eval(count=20, failures_only=False)

        assert result["success"] is True
        assert "output" in result
        assert "2" in result["output"]  # total traces


# ---------------------------------------------------------------------------
# Helper for fake Path.home
# ---------------------------------------------------------------------------


class _FakePathHome:
    """Fake Path that intercepts / operator for recipe path detection."""
    def __init__(self, real_home, mock_recipe):
        self._real = real_home
        self._mock_recipe = mock_recipe

    def __truediv__(self, other):
        if "recipe.yaml" in str(other) or "receptors" in str(other):
            # Chain: germline -> membrane -> receptors -> skill -> recipe.yaml
            return _FakePathHome(self._real, self._mock_recipe)
        if str(other).endswith("recipe.yaml"):
            return self._mock_recipe
        return self._real / other

    def __str__(self):
        return str(self._real)
