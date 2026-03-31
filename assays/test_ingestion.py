"""Tests for metabolon/enzymes/ingestion.py — meal planning."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fn():
    """Return the raw function behind the @tool decorator."""
    from metabolon.enzymes import ingestion as mod

    return mod.ingestion


def _cross_link_fn():
    """Return the _cross_link_experiment helper."""
    from metabolon.enzymes import ingestion as mod

    return mod._cross_link_experiment


# ---------------------------------------------------------------------------
# read_plan action tests
# ---------------------------------------------------------------------------


class TestReadPlan:
    """Tests for read_plan action."""

    def test_returns_content_when_file_exists(self, tmp_path: Path):
        """Return file contents when meal plan exists."""
        meal_plan = tmp_path / "meal.md"
        meal_plan.write_text("# Meal Plan\nPasta on Monday")

        fn = _fn()
        with patch("metabolon.enzymes.ingestion.MEAL_PLAN", meal_plan):
            result = fn(action="read_plan")

        assert result == "# Meal Plan\nPasta on Monday"

    def test_returns_error_when_file_missing(self, tmp_path: Path):
        """Return error message when meal plan doesn't exist."""
        missing = tmp_path / "nonexistent.md"

        fn = _fn()
        with patch("metabolon.enzymes.ingestion.MEAL_PLAN", missing):
            result = fn(action="read_plan")

        assert "not found" in result
        assert str(missing) in result


# ---------------------------------------------------------------------------
# log_meal action tests
# ---------------------------------------------------------------------------


class TestLogMeal:
    """Tests for log_meal action."""

    def test_invalid_date_format_returns_error(self):
        """Invalid date strings return an error message."""
        fn = _fn()
        result = fn(action="log_meal", meal_date="not-a-date")

        assert "Invalid date format" in result
        assert "not-a-date" in result
        assert "YYYY-MM-DD" in result

    def test_missing_meal_plan_returns_error(self, tmp_path: Path):
        """Return error when meal plan file doesn't exist."""
        missing = tmp_path / "nonexistent.md"

        fn = _fn()
        with patch("metabolon.enzymes.ingestion.MEAL_PLAN", missing):
            result = fn(
                action="log_meal",
                meal_date="2025-06-15",
                restaurant="Pizza Place",
                dish="Margherita",
            )

        assert "not found" in result

    def test_missing_order_log_section_returns_error(self, tmp_path: Path):
        """Return error when ## Order log section is missing."""
        meal_plan = tmp_path / "meal.md"
        meal_plan.write_text("# Meal Plan\nNo order log here")

        fn = _fn()
        with patch("metabolon.enzymes.ingestion.MEAL_PLAN", meal_plan):
            result = fn(
                action="log_meal",
                meal_date="2025-06-15",
                restaurant="Pizza Place",
                dish="Margherita",
            )

        assert "'## Order log' section not found" in result

    def test_appends_entry_at_end(self, tmp_path: Path):
        """Append entry at end when no subsequent section."""
        meal_plan = tmp_path / "meal.md"
        meal_plan.write_text("# Meal Plan\n## Order log\n- Existing entry\n")

        fn = _fn()
        with patch("metabolon.enzymes.ingestion.MEAL_PLAN", meal_plan):
            result = fn(
                action="log_meal",
                meal_date="2025-06-15",
                restaurant="Pizza Place",
                dish="Margherita",
                meal_type="Lunch",
            )

        assert "Logged:" in result
        assert "2025-06-15" in result
        assert "Pizza Place" in result
        assert "Margherita" in result

        # Verify file was updated
        text = meal_plan.read_text()
        assert "- 2025-06-15 (Sun): Pizza Place, Margherita. Lunch." in text

    def test_inserts_before_next_section(self, tmp_path: Path):
        """Insert entry before next ## section."""
        meal_plan = tmp_path / "meal.md"
        meal_plan.write_text(
            "# Meal Plan\n## Order log\n- Existing\n\n## Notes\nSome notes\n"
        )

        fn = _fn()
        with patch("metabolon.enzymes.ingestion.MEAL_PLAN", meal_plan):
            result = fn(
                action="log_meal",
                meal_date="2025-06-16",
                restaurant="Sushi Bar",
                dish="Salmon Roll",
                meal_type="Snack",
            )

        text = meal_plan.read_text()
        # Entry should be before ## Notes
        log_idx = text.index("## Order log")
        notes_idx = text.index("## Notes")
        entry_idx = text.index("2025-06-16")

        assert log_idx < entry_idx < notes_idx

    def test_day_name_calculated_correctly(self, tmp_path: Path):
        """The day abbreviation is calculated from the date."""
        meal_plan = tmp_path / "meal.md"
        meal_plan.write_text("# Meal Plan\n## Order log\n")

        fn = _fn()
        with patch("metabolon.enzymes.ingestion.MEAL_PLAN", meal_plan):
            # 2025-06-15 is a Sunday
            fn(
                action="log_meal",
                meal_date="2025-06-15",
                restaurant="Test",
                dish="Test Dish",
            )

        text = meal_plan.read_text()
        assert "(Sun)" in text

    def test_default_meal_type_is_lunch(self, tmp_path: Path):
        """Default meal_type is Lunch when not specified."""
        meal_plan = tmp_path / "meal.md"
        meal_plan.write_text("# Meal Plan\n## Order log\n")

        fn = _fn()
        with patch("metabolon.enzymes.ingestion.MEAL_PLAN", meal_plan):
            fn(
                action="log_meal",
                meal_date="2025-06-15",
                restaurant="Test",
                dish="Test Dish",
            )

        text = meal_plan.read_text()
        assert ". Lunch." in text


# ---------------------------------------------------------------------------
# _cross_link_experiment tests
# ---------------------------------------------------------------------------


class TestCrossLinkExperiment:
    """Tests for _cross_link_experiment helper."""

    def test_returns_none_when_experiments_dir_missing(self, tmp_path: Path):
        """Return None if experiments directory doesn't exist."""
        missing = tmp_path / "no-experiments"

        fn = _cross_link_fn()
        with patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR", missing):
            result = fn("entry text", "sushi")

        assert result is None

    def test_returns_none_when_no_active_experiments(self, tmp_path: Path):
        """Return None if no active experiments match."""
        exp_dir = tmp_path / "experiments"
        exp_dir.mkdir()
        # Inactive experiment
        exp_file = exp_dir / "assay-test.md"
        exp_file.write_text("---\nstatus: completed\nwatch_keywords: [sushi]\n---\n")

        fn = _cross_link_fn()
        with patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR", exp_dir):
            result = fn("entry text", "sushi")

        assert result is None

    def test_returns_none_when_no_matching_keywords(self, tmp_path: Path):
        """Return None if no keywords match the dish."""
        exp_dir = tmp_path / "experiments"
        exp_dir.mkdir()
        exp_file = exp_dir / "assay-test.md"
        exp_file.write_text(
            "---\nstatus: active\nwatch_keywords: [pizza, pasta]\n---\nContent\n"
        )

        fn = _cross_link_fn()
        with patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR", exp_dir):
            result = fn("entry text", "sushi")

        assert result is None

    def test_cross_links_when_keyword_matches(self, tmp_path: Path):
        """Append intake note to experiment file when keyword matches."""
        exp_dir = tmp_path / "experiments"
        exp_dir.mkdir()
        exp_file = exp_dir / "assay-test.md"
        exp_file.write_text(
            "---\nstatus: active\nwatch_keywords: [salmon, ramen]\n---\nExperiment content\n"
        )

        fn = _cross_link_fn()
        with patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR", exp_dir):
            result = fn("- 2025-06-15 (Sun): Sushi Bar, Salmon Roll. Lunch.", "Salmon Roll")

        assert result is not None
        assert "Cross-linked to experiment" in result
        assert "assay-test.md" in result

        # Verify file was updated
        text = exp_file.read_text()
        assert "**Intake logged:**" in text
        assert "Salmon Roll" in text

    def test_keyword_matching_is_case_insensitive(self, tmp_path: Path):
        """Keyword matching ignores case."""
        exp_dir = tmp_path / "experiments"
        exp_dir.mkdir()
        exp_file = exp_dir / "assay-test.md"
        exp_file.write_text(
            "---\nstatus: active\nwatch_keywords: [SUSHI]\n---\nContent\n"
        )

        fn = _cross_link_fn()
        with patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR", exp_dir):
            result = fn("entry", "sushi roll")

        assert result is not None

    def test_skips_files_without_watch_keywords(self, tmp_path: Path):
        """Skip experiment files that don't have watch_keywords."""
        exp_dir = tmp_path / "experiments"
        exp_dir.mkdir()
        exp_file = exp_dir / "assay-test.md"
        exp_file.write_text("---\nstatus: active\n---\nNo keywords\n")

        fn = _cross_link_fn()
        with patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR", exp_dir):
            result = fn("entry", "anything")

        assert result is None

    def test_only_processes_assay_files(self, tmp_path: Path):
        """Only process files matching assay-*.md pattern."""
        exp_dir = tmp_path / "experiments"
        exp_dir.mkdir()
        # Wrong filename pattern
        exp_file = exp_dir / "experiment-test.md"
        exp_file.write_text(
            "---\nstatus: active\nwatch_keywords: [sushi]\n---\nContent\n"
        )

        fn = _cross_link_fn()
        with patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR", exp_dir):
            result = fn("entry", "sushi")

        assert result is None


# ---------------------------------------------------------------------------
# Integration: log_meal with cross-linking
# ---------------------------------------------------------------------------


class TestLogMealWithCrossLink:
    """Tests for log_meal with experiment cross-linking."""

    def test_log_meal_cross_links_to_experiment(self, tmp_path: Path):
        """log_meal cross-links to matching active experiment."""
        meal_plan = tmp_path / "meal.md"
        meal_plan.write_text("# Meal Plan\n## Order log\n")

        exp_dir = tmp_path / "experiments"
        exp_dir.mkdir()
        exp_file = exp_dir / "assay-diet.md"
        exp_file.write_text(
            "---\nstatus: active\nwatch_keywords: [pizza]\n---\nDiet experiment\n"
        )

        fn = _fn()
        with (
            patch("metabolon.enzymes.ingestion.MEAL_PLAN", meal_plan),
            patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR", exp_dir),
        ):
            result = fn(
                action="log_meal",
                meal_date="2025-06-15",
                restaurant="Pizza Place",
                dish="Margherita Pizza",
            )

        assert "Logged:" in result
        assert "Cross-linked to experiment" in result

    def test_log_meal_no_cross_link_when_no_match(self, tmp_path: Path):
        """log_meal returns just the logged message when no experiment matches."""
        meal_plan = tmp_path / "meal.md"
        meal_plan.write_text("# Meal Plan\n## Order log\n")

        exp_dir = tmp_path / "experiments"
        exp_dir.mkdir()
        exp_file = exp_dir / "assay-diet.md"
        exp_file.write_text(
            "---\nstatus: active\nwatch_keywords: [kale]\n---\nDiet experiment\n"
        )

        fn = _fn()
        with (
            patch("metabolon.enzymes.ingestion.MEAL_PLAN", meal_plan),
            patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR", exp_dir),
        ):
            result = fn(
                action="log_meal",
                meal_date="2025-06-15",
                restaurant="Pizza Place",
                dish="Margherita Pizza",
            )

        assert "Logged:" in result
        assert "Cross-linked" not in result


# ---------------------------------------------------------------------------
# Unknown action
# ---------------------------------------------------------------------------


class TestUnknownAction:
    """Tests for unknown action handling."""

    def test_unknown_action_returns_error(self):
        """Unknown action returns helpful error message."""
        fn = _fn()
        result = fn(action="delete_everything")

        assert "Unknown action" in result
        assert "delete_everything" in result
        assert "read_plan" in result or "log_meal" in result
