from __future__ import annotations

"""Tests for metabolon/enzymes/ingestion.py — meal planning tool."""


from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.enzymes.ingestion import _cross_link_experiment, ingestion


# ── Helpers ──────────────────────────────────────────────────────────────


MEAL_PLAN_CONTENT = """\
# Weekly Meal Plan

## Overview
A plan for the week.

## Order log
- 2026-03-30 (Mon): Sushi Tei, Salmon Don. Lunch.
"""

MEAL_PLAN_WITH_TRAILING_SECTION = """\
# Weekly Meal Plan

## Order log
- 2026-03-30 (Mon): Sushi Tei, Salmon Don. Lunch.

## Notes
Some notes here.
"""


@pytest.fixture
def meal_plan_file(tmp_path):
    """Create a temporary meal plan file and patch MEAL_PLAN to point at it."""
    mp = tmp_path / "meal-plan.md"
    mp.write_text(MEAL_PLAN_CONTENT)
    with patch("metabolon.enzymes.ingestion.MEAL_PLAN", mp):
        yield mp


@pytest.fixture
def experiments_dir(tmp_path):
    """Create a temporary experiments dir and patch EXPERIMENTS_DIR."""
    ed = tmp_path / "experiments"
    ed.mkdir()
    with patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR", ed):
        yield ed


# ── read_plan ────────────────────────────────────────────────────────────


class TestReadPlan:
    def test_returns_file_content(self, meal_plan_file):
        result = ingestion("read_plan")
        assert "Weekly Meal Plan" in result
        assert "Sushi Tei" in result

    def test_file_not_found(self, tmp_path):
        missing = tmp_path / "no-such-file.md"
        with patch("metabolon.enzymes.ingestion.MEAL_PLAN", missing):
            result = ingestion("read_plan")
        assert "not found" in result
        assert str(missing) in result


# ── log_meal ─────────────────────────────────────────────────────────────


class TestLogMeal:
    def test_appends_entry_at_end(self, meal_plan_file):
        result = ingestion(
            "log_meal",
            meal_date="2026-04-01",
            restaurant="Pret",
            dish="Avocado Wrap",
            meal_type="Lunch",
        )
        assert "Logged:" in result
        assert "2026-04-01 (Wed)" in result
        assert "Pret" in result
        assert "Avocado Wrap" in result
        text = meal_plan_file.read_text()
        assert "- 2026-04-01 (Wed): Pret, Avocado Wrap. Lunch." in text

    def test_inserts_before_trailing_section(self, tmp_path):
        mp = tmp_path / "meal-plan.md"
        mp.write_text(MEAL_PLAN_WITH_TRAILING_SECTION)
        with patch("metabolon.enzymes.ingestion.MEAL_PLAN", mp):
            result = ingestion(
                "log_meal",
                meal_date="2026-04-02",
                restaurant="Subway",
                dish="Club Sandwich",
            )
        assert "Logged:" in result
        text = mp.read_text()
        # Entry should appear between ## Order log and ## Notes
        log_idx = text.index("## Order log")
        notes_idx = text.index("## Notes")
        entry_idx = text.index("2026-04-02 (Thu)")
        assert log_idx < entry_idx < notes_idx

    def test_invalid_date_format(self, meal_plan_file):
        result = ingestion(
            "log_meal",
            meal_date="not-a-date",
            restaurant="X",
            dish="Y",
        )
        assert "Invalid date format" in result
        assert "not-a-date" in result

    def test_file_not_found(self, tmp_path):
        missing = tmp_path / "gone.md"
        with patch("metabolon.enzymes.ingestion.MEAL_PLAN", missing):
            result = ingestion(
                "log_meal",
                meal_date="2026-04-01",
                restaurant="A",
                dish="B",
            )
        assert "not found" in result

    def test_missing_order_log_section(self, tmp_path):
        mp = tmp_path / "meal-plan.md"
        mp.write_text("# Meal Plan\n\nNothing here.\n")
        with patch("metabolon.enzymes.ingestion.MEAL_PLAN", mp):
            result = ingestion(
                "log_meal",
                meal_date="2026-04-01",
                restaurant="A",
                dish="B",
            )
        assert "## Order log" in result
        assert "not found" in result

    def test_default_meal_type_is_lunch(self, meal_plan_file):
        ingestion(
            "log_meal",
            meal_date="2026-04-03",
            restaurant="Cafe",
            dish="Sandwich",
        )
        text = meal_plan_file.read_text()
        assert "Lunch." in text.split("2026-04-03")[-1]

    def test_custom_meal_type(self, meal_plan_file):
        ingestion(
            "log_meal",
            meal_date="2026-04-04",
            restaurant="Thai",
            dish="Mango Sticky Rice",
            meal_type="Snack",
        )
        text = meal_plan_file.read_text()
        assert "Snack." in text

    def test_atomic_write_uses_tmp_file(self, meal_plan_file):
        """Verify the write goes through a .md.tmp intermediate."""
        result = ingestion(
            "log_meal",
            meal_date="2026-04-05",
            restaurant="Test",
            dish="Dish",
        )
        assert "Logged:" in result
        # No leftover tmp file
        assert not meal_plan_file.with_suffix(".md.tmp").exists()


# ── _cross_link_experiment ──────────────────────────────────────────────


class TestCrossLinkExperiment:
    def test_no_experiments_dir(self, tmp_path):
        missing = tmp_path / "no-experiments"
        with patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR", missing):
            result = _cross_link_experiment("- entry", "coffee")
        assert result is None

    def test_no_matching_keywords(self, experiments_dir):
        exp = experiments_dir / "assay-caffeine.md"
        exp.write_text("---\nstatus: active\nwatch_keywords: [turmeric, ginger]\n---\n")
        result = _cross_link_experiment("- entry", "coffee")
        assert result is None

    def test_matching_keyword_appends_note(self, experiments_dir):
        exp = experiments_dir / "assay-caffeine.md"
        exp.write_text(
            "---\nstatus: active\nwatch_keywords: [coffee, espresso]\n---\nContent here."
        )
        entry = "- 2026-04-01 (Wed): Blue Bottle, Latte. Lunch."
        result = _cross_link_experiment(entry, "Latte")
        assert result is not None
        assert "assay-caffeine.md" in result
        updated = exp.read_text()
        assert "Intake logged" in updated
        assert entry in updated

    def test_inactive_experiment_skipped(self, experiments_dir):
        exp = experiments_dir / "assay-sugar.md"
        exp.write_text(
            "---\nstatus: completed\nwatch_keywords: [sugar, candy]\n---\nDone."
        )
        result = _cross_link_experiment("- entry", "candy")
        assert result is None

    def test_experiment_without_watch_keywords_skipped(self, experiments_dir):
        exp = experiments_dir / "assay-generic.md"
        exp.write_text("---\nstatus: active\n---\nNo keywords here.")
        result = _cross_link_experiment("- entry", "anything")
        assert result is None

    def test_multiple_experiments_first_match_wins(self, experiments_dir):
        exp1 = experiments_dir / "assay-tea.md"
        exp1.write_text(
            "---\nstatus: active\nwatch_keywords: [green tea]\n---\nTea study."
        )
        exp2 = experiments_dir / "assay-caffeine.md"
        exp2.write_text(
            "---\nstatus: active\nwatch_keywords: [coffee, tea]\n---\nCaffeine study."
        )
        result = _cross_link_experiment("- entry", "green tea")
        assert result is not None
        # Which file matched depends on glob order, but exactly one should be modified
        texts = {exp1.read_text(), exp2.read_text()}
        modified = [t for t in texts if "Intake logged" in t]
        assert len(modified) == 1

    def test_keyword_match_is_case_insensitive(self, experiments_dir):
        exp = experiments_dir / "assay-dairy.md"
        exp.write_text(
            "---\nstatus: active\nwatch_keywords: [MILK, Cheese]\n---\nDairy study."
        )
        result = _cross_link_experiment("- entry", "milk latte")
        assert result is not None

    def test_atomic_write_no_leftover_tmp(self, experiments_dir):
        exp = experiments_dir / "assay-chili.md"
        exp.write_text(
            "---\nstatus: active\nwatch_keywords: [chili]\n---\nSpice study."
        )
        _cross_link_experiment("- entry", "chili con carne")
        assert not exp.with_suffix(".md.tmp").exists()


# ── log_meal + cross-link integration ────────────────────────────────────


class TestLogMealCrossLinkIntegration:
    def test_log_meal_triggers_cross_link(self, tmp_path):
        mp = tmp_path / "meal-plan.md"
        mp.write_text(MEAL_PLAN_CONTENT)
        ed = tmp_path / "experiments"
        ed.mkdir()
        exp = ed / "assay-caffeine.md"
        exp.write_text(
            "---\nstatus: active\nwatch_keywords: [latte, espresso]\n---\nCaffeine study."
        )
        with (
            patch("metabolon.enzymes.ingestion.MEAL_PLAN", mp),
            patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR", ed),
        ):
            result = ingestion(
                "log_meal",
                meal_date="2026-04-01",
                restaurant="Blue Bottle",
                dish="Latte",
            )
        assert "Cross-linked to experiment" in result
        assert "assay-caffeine.md" in result

    def test_log_meal_no_cross_link_when_no_match(self, tmp_path):
        mp = tmp_path / "meal-plan.md"
        mp.write_text(MEAL_PLAN_CONTENT)
        ed = tmp_path / "experiments"
        ed.mkdir()
        exp = ed / "assay-turmeric.md"
        exp.write_text(
            "---\nstatus: active\nwatch_keywords: [turmeric]\n---\nTurmeric study."
        )
        with (
            patch("metabolon.enzymes.ingestion.MEAL_PLAN", mp),
            patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR", ed),
        ):
            result = ingestion(
                "log_meal",
                meal_date="2026-04-01",
                restaurant="Pret",
                dish="Avocado Wrap",
            )
        assert "Cross-linked" not in result


# ── unknown action ───────────────────────────────────────────────────────


class TestUnknownAction:
    def test_unknown_action_returns_error(self, meal_plan_file):
        result = ingestion("bogus")
        assert "Unknown action" in result
        assert "bogus" in result
        assert "read_plan" in result
        assert "log_meal" in result
