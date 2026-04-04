"""Tests for metabolon.enzymes.ecphory."""

from __future__ import annotations

import textwrap
from unittest.mock import MagicMock, patch

from metabolon.enzymes.ecphory import EcphoryResult, ecphory

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_trace(date="2025-01-01", time_str="12:00", role="user", snippet="hello"):
    """Build a lightweight TraceFragment-like object."""
    frag = MagicMock()
    frag.date = date
    frag.time_str = time_str
    frag.role = role
    frag.snippet = snippet
    return frag


# ---------------------------------------------------------------------------
# Dispatch / validation
# ---------------------------------------------------------------------------


class TestUnknownAction:
    def test_unknown_action_returns_error(self):
        result = ecphory(action="bogus")
        assert isinstance(result, EcphoryResult)
        assert "Unknown action" in result.results
        assert "bogus" in result.results


class TestEngramValidation:
    def test_engram_requires_query(self):
        result = ecphory(action="engram", query="")
        assert "engram requires: query" in result.results


class TestChromatinValidation:
    def test_chromatin_requires_query(self):
        result = ecphory(action="chromatin", query="")
        assert "chromatin requires: query" in result.results


class TestLogsValidation:
    def test_logs_requires_query(self):
        result = ecphory(action="logs", query="")
        assert "logs requires: query" in result.results


# ---------------------------------------------------------------------------
# Engram action
# ---------------------------------------------------------------------------


class TestEngramAction:
    @patch("metabolon.enzymes.ecphory._engram_search", create=True)
    def test_engram_no_matches(self, mock_search):
        """Import is lazy; patch the module-level name after import."""
        # The function does `from metabolon.organelles.engram import search as _engram_search`
        # inside its body. We patch sys.modules so the lazy import resolves to our mock.
        with patch.dict("sys.modules", {}):
            with patch("metabolon.organelles.engram.search", return_value=[]):
                result = ecphory(action="engram", query="nothing")
        assert "No matches" in result.results
        assert "nothing" in result.results

    def test_engram_returns_formatted_results(self):
        fragments = [
            _make_trace(
                date="2025-03-10", time_str="09:15", role="assistant", snippet="deployed v2"
            ),
            _make_trace(date="2025-03-11", time_str="14:30", role="user", snippet="check logs"),
        ]
        with patch("metabolon.organelles.engram.search", return_value=fragments):
            result = ecphory(action="engram", query="deploy")
        assert "2 match(es)" in result.results
        assert "[2025-03-10 09:15] [assistant] deployed v2" in result.results
        assert "[2025-03-11 14:30] [user] check logs" in result.results


# ---------------------------------------------------------------------------
# Chromatin action
# ---------------------------------------------------------------------------


class TestChromatinAction:
    def test_chromatin_no_results(self):
        with patch("metabolon.organelles.chromatin.search", return_value=[]):
            result = ecphory(action="chromatin", query="obscure topic")
        assert "No memories found" in result.results
        assert "obscure topic" in result.results

    def test_chromatin_returns_formatted_results(self):
        results = [
            {"name": "note-1", "file": "/path/note1.md", "content": "Some content here"},
            {"name": "note-2", "file": "/path/note2.md", "content": ""},
        ]
        with patch("metabolon.organelles.chromatin.search", return_value=results):
            result = ecphory(action="chromatin", query="note")
        assert "2 memory result(s)" in result.results
        assert "[note-1] /path/note1.md" in result.results
        assert "Some content here" in result.results
        assert "[note-2] /path/note2.md" in result.results


# ---------------------------------------------------------------------------
# Logs action
# ---------------------------------------------------------------------------


class TestLogsAction:
    def test_logs_no_matches(self, tmp_path):
        """When all log files exist but contain no match."""
        meal_plan = tmp_path / "meal.md"
        meal_plan.write_text("nothing relevant here\n")
        symptom_log = tmp_path / "symptom.md"
        symptom_log.write_text("all good\n")
        mock_locus = MagicMock()
        mock_locus.meal_plan = meal_plan
        mock_locus.symptom_log = symptom_log
        mock_locus.experiments = tmp_path / "nonexistent"
        with patch("metabolon.enzymes.ecphory.locus", mock_locus):
            result = ecphory(action="logs", query="xyzzy_unlikely_string")
        assert "No matches" in result.results

    def test_logs_finds_matches_in_meal_plan(self, tmp_path):
        meal_plan = tmp_path / "meal.md"
        meal_plan.write_text(
            textwrap.dedent("""\
            Week 1 Plan
            Monday: avocado toast
            Tuesday: salmon bowl
        """)
        )
        symptom_log = tmp_path / "symptom.md"
        symptom_log.write_text("all good\n")
        mock_locus = MagicMock()
        mock_locus.meal_plan = meal_plan
        mock_locus.symptom_log = symptom_log
        mock_locus.experiments = tmp_path / "nonexistent"
        with patch("metabolon.enzymes.ecphory.locus", mock_locus):
            result = ecphory(action="logs", query="salmon")
        assert "1 match(es)" in result.results
        assert "salmon bowl" in result.results

    def test_logs_searches_experiments_dir(self, tmp_path):
        meal_plan = tmp_path / "meal.md"
        meal_plan.write_text("nothing\n")
        symptom_log = tmp_path / "symptom.md"
        symptom_log.write_text("nothing\n")
        exp_dir = tmp_path / "experiments"
        exp_dir.mkdir()
        (exp_dir / "assay-001.md").write_text("tested RNA extraction\n")
        (exp_dir / "assay-002.md").write_text("control group\n")
        (exp_dir / "notes.txt").write_text("should be ignored — not assay-*.md\n")
        mock_locus = MagicMock()
        mock_locus.meal_plan = meal_plan
        mock_locus.symptom_log = symptom_log
        mock_locus.experiments = exp_dir
        with patch("metabolon.enzymes.ecphory.locus", mock_locus):
            result = ecphory(action="logs", query="RNA")
        assert "1 match(es)" in result.results
        assert "tested RNA extraction" in result.results

    def test_logs_regex_case_insensitive(self, tmp_path):
        meal_plan = tmp_path / "meal.md"
        meal_plan.write_text("URGENT: call doctor\n")
        symptom_log = tmp_path / "symptom.md"
        symptom_log.write_text("nothing\n")
        mock_locus = MagicMock()
        mock_locus.meal_plan = meal_plan
        mock_locus.symptom_log = symptom_log
        mock_locus.experiments = tmp_path / "nonexistent"
        with patch("metabolon.enzymes.ecphory.locus", mock_locus):
            result = ecphory(action="logs", query="urgent")
        assert "1 match(es)" in result.results


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


class TestEcphoryResult:
    def test_result_has_results_field(self):
        r = EcphoryResult(results="hello")
        assert r.results == "hello"

    def test_result_allows_extra_fields(self):
        r = EcphoryResult(results="ok", extra="data")
        assert r.extra == "data"
