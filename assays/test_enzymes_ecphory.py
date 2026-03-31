from __future__ import annotations
"""Tests for metabolon/enzymes/ecphory.py"""


import textwrap
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Minimal stubs for TraceFragment (mirrors engram.TraceFragment)
# ---------------------------------------------------------------------------

@dataclass
class _TraceFragment:
    date: str
    time_str: str
    timestamp_ms: int
    session: str
    role: str
    snippet: str
    tool: str
    match_line: str = ""
    context_before: list[str] | None = None
    context_after: list[str] | None = None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_locus(tmp_path):
    """Provide a fake locus so the logs action doesn't touch real files."""
    fake_locus = MagicMock()
    fake_locus.meal_plan = tmp_path / "meal_plan.md"
    fake_locus.symptom_log = tmp_path / "symptom_log.md"
    fake_locus.experiments = tmp_path / "experiments"
    fake_locus.experiments.mkdir(parents=True, exist_ok=True)
    with patch("metabolon.enzymes.ecphory.locus", fake_locus):
        yield fake_locus


@pytest.fixture()
def fn():
    """Return the raw ecphory function (bypass FastMCP @tool decorator)."""
    from metabolon.enzymes.ecphory import ecphory

    return ecphory


# ---------------------------------------------------------------------------
# Action dispatch
# ---------------------------------------------------------------------------

class TestDispatch:
    def test_unknown_action(self, fn):
        res = fn(action="bogus", query="x")
        assert "Unknown action" in res.results
        assert "bogus" in res.results

    def test_case_insensitive_action(self, fn):
        """Action should be matched case-insensitively."""
        with patch("metabolon.enzymes.ecphory.locus"):
            # engram branch — will fail validation but proves dispatch
            with patch(
                "metabolon.organelles.engram.search",
                return_value=[_TraceFragment(
                    date="2025-01-01", time_str="12:00", timestamp_ms=0,
                    session="s", role="user", snippet="hi", tool="t",
                )],
            ):
                res = fn(action="Engram", query="hi")
                assert "1 match(es)" in res.results


# ---------------------------------------------------------------------------
# Engram action
# ---------------------------------------------------------------------------

class TestEngram:
    def test_missing_query(self, fn):
        res = fn(action="engram", query="")
        assert "engram requires: query" in res.results

    @patch("metabolon.organelles.engram.search")
    def test_no_matches(self, mock_search, fn):
        mock_search.return_value = []
        res = fn(action="engram", query="nothing")
        assert "No matches" in res.results
        mock_search.assert_called_once_with("nothing", days=7, deep=True, role=None)

    @patch("metabolon.organelles.engram.search")
    def test_with_results(self, mock_search, fn):
        frag = _TraceFragment(
            date="2025-06-01",
            time_str="14:30",
            timestamp_ms=1000,
            session="sess-1",
            role="assistant",
            snippet="Here is some text",
            tool="read",
        )
        mock_search.return_value = [frag]
        res = fn(action="engram", query="text")
        assert "1 match(es)" in res.results
        assert "[2025-06-01 14:30]" in res.results
        assert "[assistant]" in res.results
        assert "Here is some text" in res.results

    @patch("metabolon.organelles.engram.search")
    def test_forward_role_param(self, mock_search, fn):
        mock_search.return_value = []
        fn(action="engram", query="q", role="user", days=30, deep=False)
        mock_search.assert_called_once_with("q", days=30, deep=False, role="user")

    @patch("metabolon.organelles.engram.search")
    def test_multiple_fragments(self, mock_search, fn):
        frags = [
            _TraceFragment(date="2025-01-01", time_str="10:00", timestamp_ms=i * 1000,
                           session="s", role="user", snippet=f"snippet {i}", tool="t")
            for i in range(3)
        ]
        mock_search.return_value = frags
        res = fn(action="engram", query="test")
        assert "3 match(es)" in res.results


# ---------------------------------------------------------------------------
# Chromatin action
# ---------------------------------------------------------------------------

class TestChromatin:
    def test_missing_query(self, fn):
        res = fn(action="chromatin", query="")
        assert "chromatin requires: query" in res.results

    @patch("metabolon.organelles.chromatin.search")
    def test_no_matches(self, mock_search, fn):
        mock_search.return_value = []
        res = fn(action="chromatin", query="void")
        assert "No memories found" in res.results

    @patch("metabolon.organelles.chromatin.search")
    def test_with_results(self, mock_search, fn):
        mock_search.return_value = [
            {"name": "mark-1", "file": "/path/to/mark-1.md", "content": "some content here"},
        ]
        res = fn(action="chromatin", query="test")
        assert "1 memory result(s)" in res.results
        assert "[mark-1]" in res.results
        assert "some content here" in res.results

    @patch("metabolon.organelles.chromatin.search")
    def test_forward_params(self, mock_search, fn):
        mock_search.return_value = []
        fn(
            action="chromatin",
            query="q",
            category="gotcha",
            limit=5,
            mode="semantic",
            accessibility="closed",
        )
        mock_search.assert_called_once_with(
            "q", category="gotcha", limit=5, mode="semantic", chromatin="closed",
        )

    @patch("metabolon.organelles.chromatin.search")
    def test_snippet_truncated(self, mock_search, fn):
        long_content = "x" * 200
        mock_search.return_value = [
            {"name": "big", "file": "/p.md", "content": long_content},
        ]
        res = fn(action="chromatin", query="q")
        # snippet should be at most 120 chars of content
        for line in res.results.splitlines():
            if line.startswith("    "):
                assert len(line.strip()) <= 120


# ---------------------------------------------------------------------------
# Logs action
# ---------------------------------------------------------------------------

class TestLogs:
    def test_missing_query(self, fn):
        res = fn(action="logs", query="")
        assert "logs requires: query" in res.results

    def test_no_files_exist(self, fn, _patch_locus, tmp_path):
        res = fn(action="logs", query="anything")
        assert "No matches" in res.results

    def test_match_in_meal_plan(self, fn, _patch_locus, tmp_path):
        meal = tmp_path / "meal_plan.md"
        meal.write_text("line one\nbuy eggs for lunch\nline three\n", encoding="utf-8")
        res = fn(action="logs", query="eggs")
        assert "1 match(es)" in res.results
        assert "buy eggs for lunch" in res.results
        assert "meal_plan:2" in res.results

    def test_match_in_symptom_log(self, fn, _patch_locus, tmp_path):
        slog = tmp_path / "symptom_log.md"
        slog.write_text("feeling fine\nhad a headache today\nok now\n", encoding="utf-8")
        res = fn(action="logs", query="headache")
        assert "1 match(es)" in res.results
        assert "symptom_log:2" in res.results

    def test_match_in_experiment_file(self, fn, _patch_locus, tmp_path):
        exp_dir = tmp_path / "experiments"
        exp_dir.mkdir(parents=True, exist_ok=True)
        exp_file = exp_dir / "assay-test.md"
        exp_file.write_text("no match here\nFOUND IT yay\n", encoding="utf-8")
        res = fn(action="logs", query="FOUND")
        assert "1 match(es)" in res.results
        assert "experiments/assay-test.md:2" in res.results

    def test_case_insensitive_regex(self, fn, _patch_locus, tmp_path):
        meal = tmp_path / "meal_plan.md"
        meal.write_text("UPPERCASE word\n", encoding="utf-8")
        res = fn(action="logs", query="uppercase")
        assert "1 match(es)" in res.results

    def test_invalid_regex_handled(self, fn, _patch_locus, tmp_path):
        """Invalid regex should raise, not crash with unhandled exception."""
        meal = tmp_path / "meal_plan.md"
        meal.write_text("some text\n", encoding="utf-8")
        with pytest.raises(Exception):
            fn(action="logs", query="[invalid")

    def test_multiple_matches(self, fn, _patch_locus, tmp_path):
        meal = tmp_path / "meal_plan.md"
        meal.write_text("alpha line\nbeta line\nalpha again\n", encoding="utf-8")
        res = fn(action="logs", query="alpha")
        assert "2 match(es)" in res.results

    def test_experiments_dir_missing(self, fn, _patch_locus, tmp_path):
        """If experiments dir doesn't exist, only meal_plan and symptom_log are checked."""
        import shutil
        exp_dir = tmp_path / "experiments"
        if exp_dir.exists():
            shutil.rmtree(exp_dir)
        meal = tmp_path / "meal_plan.md"
        meal.write_text("target string\n", encoding="utf-8")
        res = fn(action="logs", query="target")
        assert "1 match(es)" in res.results


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

class TestReturnType:
    def test_returns_ecphory_result(self, fn):
        from metabolon.enzymes.ecphory import EcphoryResult
        res = fn(action="bogus", query="x")
        assert isinstance(res, EcphoryResult)

    def test_results_field_is_string(self, fn):
        res = fn(action="bogus", query="x")
        assert isinstance(res.results, str)
