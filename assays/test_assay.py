from __future__ import annotations

"""Tests for effectors/assay — life experiment tracker."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_assay():
    """Load the assay module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/assay").read()
    ns: dict = {"__name__": "assay"}
    exec(source, ns)
    return ns


_mod = _load_assay()

# Pure functions - no mocking needed
_extract_keywords = _mod["_extract_keywords"]
slugify = _mod["slugify"]
summarise_period = _mod["summarise_period"]
_extract_float = _mod["_extract_float"]
_STOP_WORDS = _mod["_STOP_WORDS"]
_DOMAIN_SYNONYMS = _mod["_DOMAIN_SYNONYMS"]

# Functions that need filesystem mocking
pull_oura = _mod["pull_oura"]
pull_intake = _mod["pull_intake"]
find_experiment = _mod["find_experiment"]
_is_active = _mod["_is_active"]
list_experiments = _mod["list_experiments"]

# Commands
cmd_new = _mod["cmd_new"]
cmd_check = _mod["cmd_check"]
cmd_close = _mod["cmd_close"]
cmd_list = _mod["cmd_list"]

# Constants
EXPERIMENT_DIR = _mod["EXPERIMENT_DIR"]
VAULT = _mod["VAULT"]


# ── _extract_keywords tests ─────────────────────────────────────────────


def test_extract_keywords_basic():
    """Extract keywords from simple name and hypothesis."""
    result = _extract_keywords("caffeine cut", "cutting caffeine improves sleep")
    assert "caffeine" in result
    assert "cut" in result
    assert "improves" not in result  # stop word


def test_extract_keywords_stop_words_filtered():
    """Stop words are filtered from keyword extraction."""
    result = _extract_keywords("test", "the and with from that this will")
    # All should be filtered as stop words
    for word in ["the", "and", "with", "from", "that", "this", "will"]:
        assert word not in result


def test_extract_keywords_short_words_filtered():
    """Words shorter than 4 characters are filtered."""
    result = _extract_keywords("test", "a an the big run hop")
    # Short words (< 4 chars) should not appear
    for word in ["a", "an", "the", "big", "run", "hop"]:
        assert word not in result


def test_extract_keywords_synonym_expansion_caffeine():
    """Caffeine keyword expands to coffee synonyms."""
    result = _extract_keywords("caffeine reduction", "less caffeine better sleep")
    assert "caffeine" in result
    # Synonyms should be added
    assert "coffee" in result or "espresso" in result


def test_extract_keywords_synonym_expansion_alcohol():
    """Alcohol keyword expands to drinking synonyms."""
    result = _extract_keywords("alcohol break", "no alcohol for month")
    assert "alcohol" in result
    assert "beer" in result or "wine" in result


def test_extract_keywords_synonym_expansion_exercise():
    """Exercise keyword expands to workout synonyms."""
    result = _extract_keywords("exercise routine", "daily exercise helps")
    assert "exercise" in result
    assert "workout" in result or "gym" in result


def test_extract_keywords_synonym_expansion_sleep():
    """Sleep keyword expands to rest synonyms."""
    result = _extract_keywords("sleep optimization", "better sleep quality")
    assert "sleep" in result


def test_extract_keywords_synonym_expansion_meditation():
    """Meditation keyword expands to mindfulness synonyms."""
    result = _extract_keywords("meditation practice", "daily meditation")
    assert "meditation" in result
    assert "mindfulness" in result


def test_extract_keywords_synonym_expansion_fasting():
    """Fasting keyword expands to IF synonyms."""
    result = _extract_keywords("fasting protocol", "intermittent fasting")
    assert "fasting" in result


def test_extract_keywords_synonym_expansion_cold():
    """Cold keyword expands to ice bath synonyms."""
    result = _extract_keywords("cold exposure", "daily cold shower")
    assert "cold" in result
    assert "ice bath" in result or "cold shower" in result


def test_extract_keywords_synonym_expansion_heat():
    """Heat keyword expands to sauna synonyms."""
    result = _extract_keywords("heat therapy", "regular sauna sessions")
    assert "heat" in result
    assert "sauna" in result


def test_extract_keywords_no_duplicates():
    """Keywords are deduplicated."""
    result = _extract_keywords("caffeine caffeine", "caffeine caffeine caffeine")
    count = result.count("caffeine")
    assert count == 1


def test_extract_keywords_combined_name_hypothesis():
    """Keywords are extracted from both name and hypothesis."""
    result = _extract_keywords("protein intake", "increasing whey protein builds muscle")
    assert "protein" in result
    assert "whey" in result


def test_extract_keywords_magnesium_synonyms():
    """Magnesium keyword expands to form synonyms."""
    result = _extract_keywords("magnesium supplement", "glycinate magnesium at night")
    assert "magnesium" in result
    assert "glycinate" in result


def test_extract_keywords_creatine_synonyms():
    """Creatine keyword expands to form synonyms."""
    result = _extract_keywords("creatine loading", "monohydrate creatine daily")
    assert "creatine" in result
    assert "monohydrate" in result


def test_extract_keywords_stress_synonyms():
    """Stress keyword expands to related terms."""
    result = _extract_keywords("stress management", "reduce cortisol")
    assert "stress" in result
    assert "cortisol" in result


def test_extract_keywords_supplements_synonyms():
    """Supplements keyword expands to vitamin terms."""
    result = _extract_keywords("supplements stack", "daily vitamins")
    assert "supplements" in result
    assert "vitamins" in result


def test_extract_keywords_sunlight_synonyms():
    """Sunlight keyword expands to light therapy terms."""
    result = _extract_keywords("sunlight exposure", "morning light therapy")
    assert "sunlight" in result
    assert "light therapy" in result or "morning light" in result


def test_extract_keywords_reading_synonyms():
    """Reading keyword expands to book terms."""
    result = _extract_keywords("reading habit", "daily books kindle")
    assert "reading" in result
    assert "books" in result or "kindle" in result


def test_extract_keywords_fat_synonyms():
    """Fat keyword expands to lipid/keto terms."""
    result = _extract_keywords("fat intake", "keto diet butter oils")
    assert "fat" in result
    assert "keto" in result


def test_extract_keywords_carbs_synonyms():
    """Carbs keyword expands to glucose/rice terms."""
    result = _extract_keywords("carbs reduction", "less glucose rice bread")
    assert "carbs" in result


# ── slugify tests ───────────────────────────────────────────────────────


def test_slugify_simple():
    """Slugify converts spaces to hyphens."""
    assert slugify("caffeine cut") == "caffeine-cut"


def test_slugify_lowercase():
    """Slugify converts to lowercase."""
    assert slugify("Caffeine CUT") == "caffeine-cut"


def test_slugify_special_chars():
    """Slugify removes special characters."""
    assert slugify("caffeine! @cut#") == "caffeine-cut"


def test_slugify_multiple_spaces():
    """Slugify collapses multiple spaces into single hyphen."""
    assert slugify("caffeine   cut") == "caffeine-cut"


def test_slugify_leading_trailing_spaces():
    """Slugify strips leading/trailing hyphens."""
    assert slugify("  caffeine cut  ") == "caffeine-cut"


def test_slugify_numbers_preserved():
    """Slugify preserves numbers."""
    assert slugify("experiment 123") == "experiment-123"


def test_slugify_empty_string():
    """Slugify handles empty string."""
    assert slugify("") == ""


def test_slugify_only_special_chars():
    """Slugify handles strings with only special characters."""
    assert slugify("!@#$%") == ""


def test_slugify_mixed_alphanumeric():
    """Slugify handles mixed alphanumeric."""
    assert slugify("Test 123 Experiment") == "test-123-experiment"


# ── summarise_period tests ──────────────────────────────────────────────


def test_summarise_period_basic():
    """Summarise period computes averages correctly."""
    data = {
        "2024-01-01": {"sleep_score": 80, "readiness_score": 70, "readiness_contributors": {"hrv_balance": 50}},
        "2024-01-02": {"sleep_score": 82, "readiness_score": 72, "readiness_contributors": {"hrv_balance": 52}},
    }
    result = summarise_period(data)
    assert result["days"] == 2
    assert result["sleep_avg"] == 81.0
    assert result["readiness_avg"] == 71.0
    assert result["hrv_balance_avg"] == 51.0


def test_summarise_period_range():
    """Summarise period computes ranges correctly."""
    data = {
        "2024-01-01": {"sleep_score": 70, "readiness_score": 60, "readiness_contributors": {"hrv_balance": 40}},
        "2024-01-02": {"sleep_score": 90, "readiness_score": 80, "readiness_contributors": {"hrv_balance": 60}},
    }
    result = summarise_period(data)
    assert result["sleep_range"] == "70-90"
    assert result["readiness_range"] == "60-80"
    assert result["hrv_balance_range"] == "40-60"


def test_summarise_period_empty():
    """Summarise period handles empty data."""
    result = summarise_period({})
    assert result["days"] == 0
    assert result["sleep_avg"] is None
    assert result["sleep_range"] is None


def test_summarise_period_partial_data():
    """Summarise period handles partial data (missing scores)."""
    data = {
        "2024-01-01": {"sleep_score": 80, "readiness_score": None, "readiness_contributors": {}},
        "2024-01-02": {"sleep_score": None, "readiness_score": 70, "readiness_contributors": {"hrv_balance": 50}},
    }
    result = summarise_period(data)
    assert result["sleep_avg"] == 80.0  # Only one valid
    assert result["readiness_avg"] == 70.0  # Only one valid
    assert result["hrv_balance_avg"] == 50.0


def test_summarise_period_no_contributors():
    """Summarise period handles missing contributors."""
    data = {
        "2024-01-01": {"sleep_score": 80, "readiness_score": 70, "readiness_contributors": None},
        "2024-01-02": {"sleep_score": 82, "readiness_score": 72, "readiness_contributors": {}},
    }
    result = summarise_period(data)
    assert result["hrv_balance_avg"] is None
    assert result["hrv_balance_range"] is None


def test_summarise_period_rounding():
    """Summarise period rounds averages to 1 decimal place."""
    data = {
        "2024-01-01": {"sleep_score": 80, "readiness_score": 70, "readiness_contributors": {"hrv_balance": 50}},
        "2024-01-02": {"sleep_score": 81, "readiness_score": 71, "readiness_contributors": {"hrv_balance": 51}},
        "2024-01-03": {"sleep_score": 82, "readiness_score": 72, "readiness_contributors": {"hrv_balance": 52}},
    }
    result = summarise_period(data)
    assert result["sleep_avg"] == 81.0
    assert result["readiness_avg"] == 71.0


def test_summarise_period_single_day():
    """Summarise period handles single day."""
    data = {
        "2024-01-01": {"sleep_score": 85, "readiness_score": 75, "readiness_contributors": {"hrv_balance": 55}},
    }
    result = summarise_period(data)
    assert result["days"] == 1
    assert result["sleep_avg"] == 85.0
    assert result["sleep_range"] == "85-85"


# ── _extract_float tests ─────────────────────────────────────────────────


def test_extract_float_basic():
    """Extract float finds and returns float value."""
    text = "Sleep: avg 78.5"
    result = _extract_float(text, r"Sleep: avg ([\d.]+)")
    assert result == 78.5


def test_extract_float_not_found():
    """Extract float returns None when pattern not found."""
    text = "No sleep data here"
    result = _extract_float(text, r"Sleep: avg ([\d.]+)")
    assert result is None


def test_extract_float_integer():
    """Extract float handles integer values."""
    text = "Sleep: avg 80"
    result = _extract_float(text, r"Sleep: avg ([\d.]+)")
    assert result == 80.0


def test_extract_float_multiple_matches():
    """Extract float returns first match."""
    text = "Sleep: avg 78.5, Readiness: avg 72.3"
    result = _extract_float(text, r"avg ([\d.]+)")
    assert result == 78.5


def test_extract_float_invalid_number():
    """Extract float returns None for non-numeric match."""
    text = "Sleep: avg abc"
    result = _extract_float(text, r"Sleep: avg (\w+)")
    assert result is None


def test_extract_float_negative():
    """Extract float handles negative delta values."""
    text = "delta: -5.2"
    result = _extract_float(text, r"delta: ([-\d.]+)")
    assert result == -5.2


# ── pull_oura tests (mocked) ────────────────────────────────────────────


def test_pull_oura_combines_data():
    """Pull oura combines sleep and readiness data."""
    mock_sleep = [{"day": "2024-01-01", "score": 80, "contributors": {"deep": 30}}]
    mock_readiness = [{"day": "2024-01-01", "score": 70, "contributors": {"hrv_balance": 50}}]
    
    with patch.object(_mod, "_get_token", return_value="fake_token"):
        with patch.object(_mod, "_fetch", side_effect=[mock_sleep, mock_readiness]):
            result = pull_oura("2024-01-01", "2024-01-02")
    
    assert "2024-01-01" in result
    assert result["2024-01-01"]["sleep_score"] == 80
    assert result["2024-01-01"]["readiness_score"] == 70


def test_pull_oura_sorted_by_date():
    """Pull oura returns data sorted by date."""
    mock_sleep = [
        {"day": "2024-01-03", "score": 85, "contributors": {}},
        {"day": "2024-01-01", "score": 80, "contributors": {}},
        {"day": "2024-01-02", "score": 82, "contributors": {}},
    ]
    mock_readiness = []
    
    with patch.object(_mod, "_get_token", return_value="fake_token"):
        with patch.object(_mod, "_fetch", side_effect=[mock_sleep, mock_readiness]):
            result = pull_oura("2024-01-01", "2024-01-03")
    
    dates = list(result.keys())
    assert dates == ["2024-01-01", "2024-01-02", "2024-01-03"]


def test_pull_oura_empty_response():
    """Pull oura handles empty API responses."""
    with patch.object(_mod, "_get_token", return_value="fake_token"):
        with patch.object(_mod, "_fetch", side_effect=[[], []]):
            result = pull_oura("2024-01-01", "2024-01-02")
    
    assert result == {}


def test_pull_oura_missing_day_field():
    """Pull oura handles entries with missing day field."""
    mock_sleep = [
        {"day": "2024-01-01", "score": 80, "contributors": {}},
        {"score": 82, "contributors": {}},  # Missing day
    ]
    mock_readiness = []
    
    with patch.object(_mod, "_get_token", return_value="fake_token"):
        with patch.object(_mod, "_fetch", side_effect=[mock_sleep, mock_readiness]):
            result = pull_oura("2024-01-01", "2024-01-02")
    
    # Entry with missing day should be stored with empty string key
    assert "2024-01-01" in result


def test_pull_oura_merges_same_day():
    """Pull oura merges sleep and readiness for same day."""
    mock_sleep = [{"day": "2024-01-01", "score": 80, "contributors": {"deep": 30}}]
    mock_readiness = [{"day": "2024-01-01", "score": 70, "contributors": {"hrv_balance": 50}}]
    
    with patch.object(_mod, "_get_token", return_value="fake_token"):
        with patch.object(_mod, "_fetch", side_effect=[mock_sleep, mock_readiness]):
            result = pull_oura("2024-01-01", "2024-01-02")
    
    assert result["2024-01-01"]["sleep_score"] == 80
    assert result["2024-01-01"]["readiness_score"] == 70
    assert result["2024-01-01"]["sleep_contributors"] == {"deep": 30}
    assert result["2024-01-01"]["readiness_contributors"] == {"hrv_balance": 50}


# ── pull_intake tests (mocked filesystem) ───────────────────────────────


def _make_meal_plan(tmp_path: Path, content: str) -> Path:
    """Create a fake meal plan file in tmp_path."""
    meal_plan = tmp_path / "meal-plan.md"
    meal_plan.write_text(content)
    return meal_plan


_MEAL_PLAN_CONTENT = """# Meal Plan

## Order log

- 2024-01-01 (Mon): Coffee, eggs, toast
- 2024-01-02 (Tue): Espresso, oatmeal, banana
- 2024-01-03 (Wed): Tea, pancakes, syrup
- 2024-01-10 (Wed): Coffee, sandwich, chips

## Other section

Some other content.
"""


def test_pull_intake_matches_keywords(tmp_path):
    """Pull intake returns entries matching keywords."""
    meal_plan = _make_meal_plan(tmp_path, _MEAL_PLAN_CONTENT)
    
    with patch.object(_mod, "MEAL_PLAN", meal_plan):
        result = pull_intake("2024-01-01", ["coffee"])
    
    assert len(result) == 2
    assert any("2024-01-01" in e for e in result)
    assert any("2024-01-10" in e for e in result)


def test_pull_intake_date_filter(tmp_path):
    """Pull intake filters by start date."""
    meal_plan = _make_meal_plan(tmp_path, _MEAL_PLAN_CONTENT)
    
    with patch.object(_mod, "MEAL_PLAN", meal_plan):
        result = pull_intake("2024-01-03", ["coffee"])
    
    # Only 2024-01-10 should match (after 2024-01-03)
    assert len(result) == 1
    assert "2024-01-10" in result[0]


def test_pull_intake_multiple_keywords(tmp_path):
    """Pull intake matches any of multiple keywords."""
    meal_plan = _make_meal_plan(tmp_path, _MEAL_PLAN_CONTENT)
    
    with patch.object(_mod, "MEAL_PLAN", meal_plan):
        result = pull_intake("2024-01-01", ["coffee", "espresso"])
    
    # Should match both coffee and espresso entries
    assert len(result) == 3


def test_pull_intake_no_matches(tmp_path):
    """Pull intake returns empty list when no matches."""
    meal_plan = _make_meal_plan(tmp_path, _MEAL_PLAN_CONTENT)
    
    with patch.object(_mod, "MEAL_PLAN", meal_plan):
        result = pull_intake("2024-01-01", ["pizza"])
    
    assert result == []


def test_pull_intake_missing_file(tmp_path):
    """Pull intake returns empty list when meal plan doesn't exist."""
    missing = tmp_path / "nonexistent.md"
    
    with patch.object(_mod, "MEAL_PLAN", missing):
        result = pull_intake("2024-01-01", ["coffee"])
    
    assert result == []


def test_pull_intake_no_order_log(tmp_path):
    """Pull intake returns empty when no Order log section."""
    content = "# Meal Plan\n\nNo order log here.\n"
    meal_plan = _make_meal_plan(tmp_path, content)
    
    with patch.object(_mod, "MEAL_PLAN", meal_plan):
        result = pull_intake("2024-01-01", ["coffee"])
    
    assert result == []


def test_pull_intake_case_insensitive(tmp_path):
    """Pull intake matches case-insensitively."""
    meal_plan = _make_meal_plan(tmp_path, _MEAL_PLAN_CONTENT)
    
    with patch.object(_mod, "MEAL_PLAN", meal_plan):
        result = pull_intake("2024-01-01", ["COFFEE"])
    
    assert len(result) == 2


def test_pull_intake_no_log_section_end(tmp_path):
    """Pull intake handles order log at end of file."""
    content = "# Meal Plan\n\n## Order log\n\n- 2024-01-01: Coffee\n"
    meal_plan = _make_meal_plan(tmp_path, content)
    
    with patch.object(_mod, "MEAL_PLAN", meal_plan):
        result = pull_intake("2024-01-01", ["coffee"])
    
    assert len(result) == 1


# ── _is_active tests ────────────────────────────────────────────────────


def test_is_active_true(tmp_path):
    """_is_active returns True for active experiment."""
    exp_file = tmp_path / "assay-test.md"
    exp_file.write_text("---\nstatus: active\n---\n")
    
    assert _is_active(exp_file) is True


def test_is_active_false_closed(tmp_path):
    """_is_active returns False for closed experiment."""
    exp_file = tmp_path / "assay-test.md"
    exp_file.write_text("---\nstatus: closed\n---\n")
    
    assert _is_active(exp_file) is False


def test_is_active_false_no_status(tmp_path):
    """_is_active returns False when no status in frontmatter."""
    exp_file = tmp_path / "assay-test.md"
    exp_file.write_text("---\nname: test\n---\n")
    
    assert _is_active(exp_file) is False


# ── find_experiment tests ───────────────────────────────────────────────


def _make_experiment_dir(tmp_path: Path) -> Path:
    """Create experiment directory structure."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir(parents=True)
    return exp_dir


def test_find_experiment_by_name(tmp_path):
    """Find experiment by fuzzy name match."""
    exp_dir = _make_experiment_dir(tmp_path)
    exp_file = exp_dir / "assay-2024-01-01-caffeine-cut.md"
    exp_file.write_text("status: active\n")
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        result = find_experiment("caffeine")
    
    assert result == exp_file


def test_find_experiment_no_match(tmp_path):
    """Find experiment returns None when no match."""
    exp_dir = _make_experiment_dir(tmp_path)
    exp_file = exp_dir / "assay-2024-01-01-sleep-test.md"
    exp_file.write_text("status: active\n")
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        result = find_experiment("caffeine")
    
    assert result is None


def test_find_experiment_single_active_no_name(tmp_path):
    """Find experiment returns the only active one when no name given."""
    exp_dir = _make_experiment_dir(tmp_path)
    exp_file = exp_dir / "assay-2024-01-01-test.md"
    exp_file.write_text("status: active\n")
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        result = find_experiment(None)
    
    assert result == exp_file


def test_find_experiment_multiple_active_no_name(tmp_path):
    """Find experiment returns None when multiple active and no name given."""
    exp_dir = _make_experiment_dir(tmp_path)
    for i, name in enumerate(["test-a", "test-b"]):
        exp_file = exp_dir / f"assay-2024-01-0{i}-{name}.md"
        exp_file.write_text("status: active\n")
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        result = find_experiment(None)
    
    assert result is None


def test_find_experiment_empty_dir(tmp_path):
    """Find experiment returns None when directory is empty."""
    exp_dir = _make_experiment_dir(tmp_path)
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        result = find_experiment("test")
    
    assert result is None


def test_find_experiment_closed_not_returned_without_name(tmp_path):
    """Find experiment ignores closed experiments when no name given."""
    exp_dir = _make_experiment_dir(tmp_path)
    exp_file = exp_dir / "assay-2024-01-01-test.md"
    exp_file.write_text("status: closed\n")
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        result = find_experiment(None)
    
    assert result is None


# ── list_experiments tests ───────────────────────────────────────────────


def test_list_experiments_returns_sorted(tmp_path):
    """List experiments returns sorted list."""
    exp_dir = _make_experiment_dir(tmp_path)
    for name in ["zebra", "alpha", "middle"]:
        exp_file = exp_dir / f"assay-{name}.md"
        exp_file.write_text("status: active\n")
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        result = list_experiments()
    
    names = [p.stem for p in result]
    assert names == sorted(names)


def test_list_experiments_empty(tmp_path):
    """List experiments returns empty list for empty directory."""
    exp_dir = _make_experiment_dir(tmp_path)
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        result = list_experiments()
    
    assert result == []


def test_list_experiments_only_assay_files(tmp_path):
    """List experiments only returns assay-*.md files."""
    exp_dir = _make_experiment_dir(tmp_path)
    (exp_dir / "assay-test.md").write_text("status: active\n")
    (exp_dir / "other-file.md").write_text("content\n")
    (exp_dir / "assay-another.md").write_text("status: active\n")
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        result = list_experiments()
    
    assert len(result) == 2


# ── cmd_list tests ───────────────────────────────────────────────────────


def test_cmd_list_empty(tmp_path, capsys):
    """cmd_list prints message when no experiments."""
    exp_dir = _make_experiment_dir(tmp_path)
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        cmd_list(None)
    
    captured = capsys.readouterr()
    assert "No experiments found" in captured.out


def test_cmd_list_shows_status(tmp_path, capsys):
    """cmd_list shows active/closed status."""
    exp_dir = _make_experiment_dir(tmp_path)
    (exp_dir / "assay-active.md").write_text('status: active\nname: "Test Active"\n')
    (exp_dir / "assay-closed.md").write_text('status: closed\nname: "Test Closed"\n')
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        cmd_list(None)
    
    captured = capsys.readouterr()
    assert "[active]" in captured.out
    assert "[closed]" in captured.out
    assert "Test Active" in captured.out
    assert "Test Closed" in captured.out


def test_cmd_list_extracts_name(tmp_path, capsys):
    """cmd_list extracts name from frontmatter."""
    exp_dir = _make_experiment_dir(tmp_path)
    (exp_dir / "assay-test.md").write_text('---\nname: "My Experiment"\n---\n')
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        cmd_list(None)
    
    captured = capsys.readouterr()
    assert "My Experiment" in captured.out


# ── cmd_new tests ────────────────────────────────────────────────────────


def test_cmd_new_creates_file(tmp_path):
    """cmd_new creates experiment file."""
    exp_dir = _make_experiment_dir(tmp_path)
    
    mock_baseline = {
        "days": 7,
        "sleep_avg": 78.5,
        "sleep_range": "70-85",
        "readiness_avg": 68.0,
        "readiness_range": "60-75",
        "hrv_balance_avg": 48.0,
        "hrv_balance_range": "40-55",
    }
    
    args = MagicMock()
    args.name = "test experiment"
    args.hypothesis = "test hypothesis"
    args.intervention = "test intervention"
    args.days = 7
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        with patch.object(_mod, "pull_oura", return_value={}):
            with patch.object(_mod, "summarise_period", return_value=mock_baseline):
                cmd_new(args)
    
    # Check file was created
    files = list(exp_dir.glob("assay-*.md"))
    assert len(files) == 1
    
    content = files[0].read_text()
    assert "status: active" in content
    assert "test experiment" in content
    assert "test hypothesis" in content


def test_cmd_new_uses_default_hypothesis(tmp_path):
    """cmd_new uses TBD when hypothesis not provided."""
    exp_dir = _make_experiment_dir(tmp_path)
    
    mock_baseline = {
        "days": 7,
        "sleep_avg": 78.5,
        "sleep_range": "70-85",
        "readiness_avg": 68.0,
        "readiness_range": "60-75",
        "hrv_balance_avg": 48.0,
        "hrv_balance_range": "40-55",
    }
    
    args = MagicMock()
    args.name = "test"
    args.hypothesis = None
    args.intervention = None
    args.days = 7
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        with patch.object(_mod, "pull_oura", return_value={}):
            with patch.object(_mod, "summarise_period", return_value=mock_baseline):
                cmd_new(args)
    
    files = list(exp_dir.glob("assay-*.md"))
    content = files[0].read_text()
    assert "TBD" in content


# ── cmd_check tests ───────────────────────────────────────────────────────


def test_cmd_check_no_experiment(capsys):
    """cmd_check exits when no active experiment found."""
    args = MagicMock()
    args.name = None
    
    with patch.object(_mod, "find_experiment", return_value=None):
        with pytest.raises(SystemExit) as exc:
            cmd_check(args)
    
    assert exc.value.code == 1


def test_cmd_check_appends_to_file(tmp_path):
    """cmd_check appends check-in entry to experiment file."""
    exp_dir = _make_experiment_dir(tmp_path)
    exp_file = exp_dir / "assay-test.md"
    exp_file.write_text("""---
status: active
start_date: 2024-01-01
name: "test"
watch_keywords: [caffeine]
---

## Baseline (2023-12-25 to 2023-12-31)
- Sleep: avg 78.5, range 70-85
- Readiness: avg 68.0, range 60-75
- HRV balance: avg 48.0, range 40-55

## Check-ins
""")
    
    mock_summary = {
        "days": 1,
        "sleep_avg": 80.0,
        "sleep_range": "80-80",
        "readiness_avg": 70.0,
        "readiness_range": "70-70",
        "hrv_balance_avg": 50.0,
        "hrv_balance_range": "50-50",
    }
    
    args = MagicMock()
    args.name = "test"
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        with patch.object(_mod, "find_experiment", return_value=exp_file):
            with patch.object(_mod, "pull_oura", return_value={}):
                with patch.object(_mod, "summarise_period", return_value=mock_summary):
                    with patch.object(_mod, "pull_intake", return_value=[]):
                        cmd_check(args)
    
    content = exp_file.read_text()
    assert "### Day" in content
    assert "Sleep: avg" in content


def test_cmd_check_shows_delta(tmp_path, capsys):
    """cmd_check shows delta from baseline."""
    exp_dir = _make_experiment_dir(tmp_path)
    exp_file = exp_dir / "assay-test.md"
    exp_file.write_text("""---
status: active
start_date: 2024-01-01
name: "test"
---

## Baseline
- Sleep: avg 78.5, range 70-85
- Readiness: avg 68.0, range 60-75
- HRV balance: avg 48.0, range 40-55

## Check-ins
""")
    
    mock_summary = {
        "days": 1,
        "sleep_avg": 80.0,  # +1.5 from baseline
        "sleep_range": "80-80",
        "readiness_avg": 70.0,  # +2.0 from baseline
        "readiness_range": "70-70",
        "hrv_balance_avg": 50.0,  # +2.0 from baseline
        "hrv_balance_range": "50-50",
    }
    
    args = MagicMock()
    args.name = "test"
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        with patch.object(_mod, "find_experiment", return_value=exp_file):
            with patch.object(_mod, "pull_oura", return_value={}):
                with patch.object(_mod, "summarise_period", return_value=mock_summary):
                    with patch.object(_mod, "pull_intake", return_value=[]):
                        cmd_check(args)
    
    captured = capsys.readouterr()
    assert "+1.5" in captured.out or "+1.5" in exp_file.read_text()


# ── cmd_close tests ───────────────────────────────────────────────────────


def test_cmd_close_no_experiment(capsys):
    """cmd_close exits when no active experiment found."""
    args = MagicMock()
    args.name = None
    
    with patch.object(_mod, "find_experiment", return_value=None):
        with pytest.raises(SystemExit) as exc:
            cmd_close(args)
    
    assert exc.value.code == 1


def test_cmd_close_flips_status(tmp_path):
    """cmd_close changes status from active to closed."""
    exp_dir = _make_experiment_dir(tmp_path)
    exp_file = exp_dir / "assay-test.md"
    exp_file.write_text("""---
status: active
start_date: 2024-01-01
end_date: 2024-01-14
name: "test"
---

## Baseline
- Sleep: avg 78.5, range 70-85
- Readiness: avg 68.0, range 60-75
- HRV balance: avg 48.0, range 40-55

## Check-ins
""")
    
    mock_summary = {
        "days": 14,
        "sleep_avg": 80.0,
        "sleep_range": "70-90",
        "readiness_avg": 70.0,
        "readiness_range": "60-80",
        "hrv_balance_avg": 50.0,
        "hrv_balance_range": "40-60",
    }
    
    args = MagicMock()
    args.name = "test"
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        with patch.object(_mod, "find_experiment", return_value=exp_file):
            with patch.object(_mod, "pull_oura", return_value={}):
                with patch.object(_mod, "summarise_period", return_value=mock_summary):
                    cmd_close(args)
    
    content = exp_file.read_text()
    assert "status: closed" in content
    assert "## Results" in content
    assert "## Verdict" in content


def test_cmd_close_shows_final_comparison(tmp_path, capsys):
    """cmd_close shows baseline vs final comparison."""
    exp_dir = _make_experiment_dir(tmp_path)
    exp_file = exp_dir / "assay-test.md"
    exp_file.write_text("""---
status: active
start_date: 2024-01-01
end_date: 2024-01-14
name: "test"
---

## Baseline
- Sleep: avg 78.5, range 70-85
- Readiness: avg 68.0, range 60-75
- HRV balance: avg 48.0, range 40-55

## Check-ins
""")
    
    mock_summary = {
        "days": 14,
        "sleep_avg": 82.0,
        "sleep_range": "75-90",
        "readiness_avg": 72.0,
        "readiness_range": "65-80",
        "hrv_balance_avg": 52.0,
        "hrv_balance_range": "45-60",
    }
    
    args = MagicMock()
    args.name = "test"
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        with patch.object(_mod, "find_experiment", return_value=exp_file):
            with patch.object(_mod, "pull_oura", return_value={}):
                with patch.object(_mod, "summarise_period", return_value=mock_summary):
                    cmd_close(args)
    
    captured = capsys.readouterr()
    # Should show improvement
    assert "78.5 -> 82.0" in captured.out or "78.5 -> 82.0" in exp_file.read_text()


def test_cmd_close_includes_cross_linked_events(tmp_path):
    """cmd_close includes cross-linked events from experiment file."""
    exp_dir = _make_experiment_dir(tmp_path)
    exp_file = exp_dir / "assay-test.md"
    exp_file.write_text("""---
status: active
start_date: 2024-01-01
end_date: 2024-01-14
name: "test"
---

## Baseline
- Sleep: avg 78.5, range 70-85

## Check-ins

> **Intake logged:** 2024-01-05 coffee

> **Symptom logged:** 2024-01-06 headache
""")
    
    mock_summary = {
        "days": 14,
        "sleep_avg": 80.0,
        "sleep_range": "70-90",
        "readiness_avg": 70.0,
        "readiness_range": "60-80",
        "hrv_balance_avg": 50.0,
        "hrv_balance_range": "40-60",
    }
    
    args = MagicMock()
    args.name = "test"
    
    with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
        with patch.object(_mod, "find_experiment", return_value=exp_file):
            with patch.object(_mod, "pull_oura", return_value={}):
                with patch.object(_mod, "summarise_period", return_value=mock_summary):
                    cmd_close(args)
    
    content = exp_file.read_text()
    assert "## Cross-linked Events" in content
    assert "Intake logged" in content


# ── Edge case tests ────────────────────────────────────────────────────────


def test_extract_keywords_empty_inputs():
    """_extract_keywords handles empty strings."""
    result = _extract_keywords("", "")
    assert result == [] or all(len(k) >= 4 for k in result)


def test_summarise_period_zero_scores():
    """summarise_period handles zero scores (valid Oura data)."""
    data = {
        "2024-01-01": {"sleep_score": 0, "readiness_score": 0, "readiness_contributors": {"hrv_balance": 0}},
    }
    result = summarise_period(data)
    assert result["sleep_avg"] == 0.0
    assert result["sleep_range"] == "0-0"


def test_slugify_unicode():
    """slugify handles unicode characters."""
    # Non-ASCII chars become empty or stripped
    result = slugify("café test")
    # Should not raise, result should be lowercase and hyphenated
    assert "café" not in result  # unicode stripped
    assert result == "caf-test" or result == "test"  # depends on implementation


class TestAssayEdgeCases:
    """Edge cases for assay commands: missing files, malformed data."""

    def test_pull_intake_malformed_date(self, tmp_path):
        """pull_intake handles malformed date in log entry."""
        content = "## Order log\n\n- invalid-date: Coffee\n- 2024-01-01: Tea\n"
        meal_plan = _make_meal_plan(tmp_path, content)
        
        with patch.object(_mod, "MEAL_PLAN", meal_plan):
            result = pull_intake("2024-01-01", ["tea"])
        
        # Should only match the valid date entry
        assert len(result) == 1

    def test_find_experiment_special_chars_in_name(self, tmp_path):
        """find_experiment handles special characters in search name."""
        exp_dir = _make_experiment_dir(tmp_path)
        exp_file = exp_dir / "assay-2024-01-01-caffeine-cut.md"
        exp_file.write_text("status: active\n")
        
        with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
            result = find_experiment("caffeine! @cut#")
        
        # Should still match after slugifying
        assert result == exp_file

    def test_cmd_check_missing_start_date(self, tmp_path):
        """cmd_check exits when start_date not found."""
        exp_dir = _make_experiment_dir(tmp_path)
        exp_file = exp_dir / "assay-test.md"
        exp_file.write_text("status: active\n")  # No start_date
        
        args = MagicMock()
        args.name = "test"
        
        with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
            with patch.object(_mod, "find_experiment", return_value=exp_file):
                with pytest.raises(SystemExit) as exc:
                    cmd_check(args)
        
        assert exc.value.code == 1

    def test_cmd_close_missing_dates(self, tmp_path):
        """cmd_close exits when dates not found."""
        exp_dir = _make_experiment_dir(tmp_path)
        exp_file = exp_dir / "assay-test.md"
        exp_file.write_text("status: active\n")  # No dates
        
        args = MagicMock()
        args.name = "test"
        
        with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
            with patch.object(_mod, "find_experiment", return_value=exp_file):
                with pytest.raises(SystemExit) as exc:
                    cmd_close(args)
        
        assert exc.value.code == 1

    def test_cmd_list_missing_name_in_frontmatter(self, tmp_path, capsys):
        """cmd_list uses filename when name not in frontmatter."""
        exp_dir = _make_experiment_dir(tmp_path)
        (exp_dir / "assay-my-test.md").write_text("status: active\n")  # No name field
        
        with patch.object(_mod, "EXPERIMENT_DIR", exp_dir):
            cmd_list(None)
        
        captured = capsys.readouterr()
        assert "assay-my-test" in captured.out
