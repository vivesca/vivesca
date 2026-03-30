"""Tests for ingestion action-dispatch consolidation."""
from unittest.mock import patch, MagicMock
import pytest

def test_unknown_action():
    from metabolon.enzymes.ingestion import ingestion
    result = ingestion(action="nonexistent")
    assert isinstance(result, str)
    assert "unknown" in result.lower() or "nonexistent" in result.lower()

@patch("metabolon.enzymes.ingestion.MEAL_PLAN")
def test_read_plan_action(mock_meal_plan):
    from metabolon.enzymes.ingestion import ingestion
    mock_meal_plan.exists.return_value = True
    mock_meal_plan.read_text.return_value = "meal plan content"
    result = ingestion(action="read_plan")
    assert isinstance(result, str)

@patch("metabolon.enzymes.ingestion.MEAL_PLAN")
@patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR")
def test_log_meal_action(mock_experiments, mock_meal_plan):
    from metabolon.enzymes.ingestion import ingestion
    mock_meal_plan.exists.return_value = True
    mock_meal_plan.read_text.return_value = "## Order log\n"
    mock_experiments.exists.return_value = False
    result = ingestion(action="log_meal", meal_date="2026-03-30", restaurant="Test", dish="Pizza", meal_type="Lunch")
    assert isinstance(result, str)
