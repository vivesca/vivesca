"""Tests for ingestion action-dispatch consolidation."""

from unittest.mock import MagicMock, patch


def test_ingestion_actions_unknown_action():
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
    result = ingestion(
        action="log_meal",
        meal_date="2026-03-30",
        restaurant="Test",
        dish="Pizza",
        meal_type="Lunch",
    )
    assert isinstance(result, str)


# Additional tests for comprehensive coverage


@patch("metabolon.enzymes.ingestion.MEAL_PLAN")
def test_read_plan_not_found(mock_meal_plan):
    """read_plan returns error when meal plan file doesn't exist."""
    from metabolon.enzymes.ingestion import ingestion

    mock_meal_plan.exists.return_value = False
    result = ingestion(action="read_plan")
    assert "not found" in result.lower()


def test_log_meal_invalid_date():
    """log_meal returns error for invalid date format."""
    from metabolon.enzymes.ingestion import ingestion

    result = ingestion(action="log_meal", meal_date="not-a-date", restaurant="Test", dish="Pizza")
    assert "invalid date" in result.lower()


@patch("metabolon.enzymes.ingestion.MEAL_PLAN")
def test_log_meal_plan_not_found(mock_meal_plan):
    """log_meal returns error when meal plan file doesn't exist."""
    from metabolon.enzymes.ingestion import ingestion

    mock_meal_plan.exists.return_value = False
    result = ingestion(action="log_meal", meal_date="2026-04-01", restaurant="Test", dish="Pizza")
    assert "not found" in result.lower()


@patch("metabolon.enzymes.ingestion.MEAL_PLAN")
@patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR")
def test_log_meal_missing_order_log_section(mock_experiments, mock_meal_plan):
    """log_meal returns error when ## Order log section is missing."""
    from metabolon.enzymes.ingestion import ingestion

    mock_meal_plan.exists.return_value = True
    mock_meal_plan.read_text.return_value = (
        "# Meal Plan\n\nSome content without order log section.\n"
    )
    mock_experiments.exists.return_value = False
    result = ingestion(action="log_meal", meal_date="2026-04-01", restaurant="Test", dish="Pizza")
    assert "section not found" in result.lower()


@patch("metabolon.enzymes.ingestion.MEAL_PLAN")
@patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR")
def test_log_meal_appends_at_end(mock_experiments, mock_meal_plan):
    """log_meal appends entry at end when no following section."""
    from metabolon.enzymes.ingestion import ingestion

    mock_meal_plan.exists.return_value = True
    mock_meal_plan.read_text.return_value = "# Meal Plan\n\n## Order log\nExisting entry.\n"
    mock_experiments.exists.return_value = False

    # Mock temp file behavior
    mock_tmp = MagicMock()
    mock_meal_plan.with_suffix.return_value = mock_tmp

    result = ingestion(
        action="log_meal",
        meal_date="2026-04-01",
        restaurant="Cafe",
        dish="Salad",
        meal_type="Snack",
    )

    assert "Logged:" in result
    assert "Cafe" in result
    assert "Salad" in result
    assert "Snack" in result
    mock_tmp.write_text.assert_called_once()
    mock_tmp.replace.assert_called_once_with(mock_meal_plan)


@patch("metabolon.enzymes.ingestion.MEAL_PLAN")
@patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR")
def test_log_meal_inserts_before_next_section(mock_experiments, mock_meal_plan):
    """log_meal inserts entry before next ## section."""
    from metabolon.enzymes.ingestion import ingestion

    mock_meal_plan.exists.return_value = True
    mock_meal_plan.read_text.return_value = (
        "# Meal Plan\n\n## Order log\nEntry one.\n\n## Notes\nSome notes.\n"
    )
    mock_experiments.exists.return_value = False

    mock_tmp = MagicMock()
    mock_meal_plan.with_suffix.return_value = mock_tmp

    result = ingestion(
        action="log_meal", meal_date="2026-04-01", restaurant="Bistro", dish="Pasta"
    )

    assert "Logged:" in result
    assert "Bistro" in result
    mock_tmp.write_text.assert_called_once()
    # Verify the written text contains the entry before ## Notes
    written_content = mock_tmp.write_text.call_args[0][0]
    assert "- 2026-04-01" in written_content
    assert "## Notes" in written_content


@patch("metabolon.enzymes.ingestion.MEAL_PLAN")
@patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR")
def test_log_meal_formats_day_name(mock_experiments, mock_meal_plan):
    """log_meal includes day name in the entry."""
    from metabolon.enzymes.ingestion import ingestion

    mock_meal_plan.exists.return_value = True
    mock_meal_plan.read_text.return_value = "## Order log\n"
    mock_experiments.exists.return_value = False

    mock_tmp = MagicMock()
    mock_meal_plan.with_suffix.return_value = mock_tmp

    # 2026-04-01 is a Wednesday
    result = ingestion(
        action="log_meal", meal_date="2026-04-01", restaurant="Test", dish="Test Dish"
    )

    assert "Wed" in result


# Tests for _cross_link_experiment


@patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR")
def test_cross_link_experiments_dir_not_exists(mock_experiments_dir):
    """_cross_link_experiment returns None when experiments dir doesn't exist."""
    from metabolon.enzymes.ingestion import _cross_link_experiment

    mock_experiments_dir.exists.return_value = False
    result = _cross_link_experiment("- 2026-04-01: Test", "Pizza")
    assert result is None


@patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR")
def test_cross_link_no_matching_keywords(mock_experiments_dir):
    """_cross_link_experiment returns None when no keywords match."""
    from metabolon.enzymes.ingestion import _cross_link_experiment

    mock_experiments_dir.exists.return_value = True
    mock_exp_file = MagicMock()
    mock_exp_file.read_text.return_value = """---
status: active
watch_keywords: [sushi, ramen]
---
Content here.
"""
    mock_experiments_dir.glob.return_value = [mock_exp_file]

    result = _cross_link_experiment("- 2026-04-01: Test", "Pizza")
    assert result is None


@patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR")
def test_cross_link_matching_keyword(mock_experiments_dir):
    """_cross_link_experiment appends note when keyword matches."""
    from metabolon.enzymes.ingestion import _cross_link_experiment

    mock_experiments_dir.exists.return_value = True
    mock_exp_file = MagicMock()
    mock_exp_file.name = "assay-test.md"
    mock_exp_file.read_text.return_value = """---
status: active
watch_keywords: [pizza, burger]
---
Experiment content.
"""
    mock_tmp = MagicMock()
    mock_exp_file.with_suffix.return_value = mock_tmp
    mock_experiments_dir.glob.return_value = [mock_exp_file]

    result = _cross_link_experiment("- 2026-04-01: Entry", "Pizza Margherita")

    assert result is not None
    assert "Cross-linked" in result
    mock_tmp.write_text.assert_called_once()
    mock_tmp.replace.assert_called_once_with(mock_exp_file)


@patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR")
def test_cross_link_skips_inactive_experiments(mock_experiments_dir):
    """_cross_link_experiment skips experiments without active status."""
    from metabolon.enzymes.ingestion import _cross_link_experiment

    mock_experiments_dir.exists.return_value = True
    mock_exp_file = MagicMock()
    mock_exp_file.read_text.return_value = """---
status: completed
watch_keywords: [pizza]
---
Experiment content.
"""
    mock_experiments_dir.glob.return_value = [mock_exp_file]

    result = _cross_link_experiment("- 2026-04-01: Entry", "Pizza")
    assert result is None


@patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR")
def test_cross_link_skips_experiments_without_keywords(mock_experiments_dir):
    """_cross_link_experiment skips experiments without watch_keywords."""
    from metabolon.enzymes.ingestion import _cross_link_experiment

    mock_experiments_dir.exists.return_value = True
    mock_exp_file = MagicMock()
    mock_exp_file.read_text.return_value = """---
status: active
---
No keywords here.
"""
    mock_experiments_dir.glob.return_value = [mock_exp_file]

    result = _cross_link_experiment("- 2026-04-01: Entry", "Pizza")
    assert result is None


@patch("metabolon.enzymes.ingestion.MEAL_PLAN")
@patch("metabolon.enzymes.ingestion.EXPERIMENTS_DIR")
def test_log_meal_with_cross_link(mock_experiments, mock_meal_plan):
    """log_meal includes cross-link when experiment matches."""
    from metabolon.enzymes.ingestion import ingestion

    mock_meal_plan.exists.return_value = True
    mock_meal_plan.read_text.return_value = "## Order log\n"

    mock_tmp = MagicMock()
    mock_meal_plan.with_suffix.return_value = mock_tmp

    mock_experiments.exists.return_value = True
    mock_exp_file = MagicMock()
    mock_exp_file.name = "assay-test.md"
    mock_exp_file.read_text.return_value = """---
status: active
watch_keywords: [sushi]
---
Content.
"""
    mock_exp_tmp = MagicMock()
    mock_exp_file.with_suffix.return_value = mock_exp_tmp
    mock_experiments.glob.return_value = [mock_exp_file]

    result = ingestion(
        action="log_meal", meal_date="2026-04-01", restaurant="Sushi Bar", dish="Salmon Sushi"
    )

    assert "Logged:" in result
    assert "Cross-linked" in result
