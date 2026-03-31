"""Tests for effectors/assay — life experiment tracker (effector script)."""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_assay_effector():
    """Load the assay effector by exec-ing its Python body."""
    source = open(Path.home() / "germline" / "effectors" / "assay").read()
    ns: dict = {"__name__": "assay_effector"}
    exec(source, ns)
    return ns


# Load the module and extract functions
_mod = _load_assay_effector()
slugify = _mod["slugify"]
_extract_keywords = _mod["_extract_keywords"]
summarise_period = _mod["summarise_period"]
pull_intake = _mod["pull_intake"]
_is_active = _mod["_is_active"]
find_experiment = _mod["find_experiment"]
list_experiments = _mod["list_experiments"]
_extract_float = _mod["_extract_float"]
EXPERIMENT_DIR = _mod["EXPERIMENT_DIR"]
_STOP_WORDS = _mod["_STOP_WORDS"]
_DOMAIN_SYNONYMS = _mod["_DOMAIN_SYNONYMS"]


# ── slugify tests ──────────────────────────────────────────────────────────


def test_slugify_basic():
    """slugify converts spaces to hyphens and lowercases."""
    assert slugify("Caffeine Cut") == "caffeine-cut"


def test_slugify_removes_special_chars():
    """slugify removes non-alphanumeric characters."""
    assert slugify("Test!@#$%Experiment") == "test-experiment"


def test_slugify_multiple_spaces():
    """slugify collapses multiple spaces into single hyphen."""
    assert slugify("multiple   spaces   here") == "multiple-spaces-here"


def test_slugify_strips_hyphens():
    """slugify strips leading and trailing hyphens."""
    assert slugify("---test---") == "test"


def test_slugify_empty_string():
    """slugify handles empty string."""
    assert slugify("") == ""


def test_slugify_numbers_preserved():
    """slugify preserves numbers."""
    assert slugify("Test 123 Experiment") == "test-123-experiment"


# ── _extract_keywords tests ────────────────────────────────────────────────


def test_extract_keywords_basic():
    """_extract_keywords extracts meaningful keywords from name and hypothesis."""
    keywords = _extract_keywords("caffeine cut", "cutting caffeine improves sleep")
    assert "caffeine" in keywords
    assert "cutting" in keywords
    assert "improves" not in keywords  # stop word


def test_extract_keywords_filters_stop_words():
    """_extract_keywords filters out stop words."""
    # "the", "and", "with", "from" should be filtered
    keywords = _extract_keywords("test", "the experiment with the subject")
    assert "the" not in keywords
    assert "with" not in keywords
    assert "experiment" in keywords
    assert "subject" in keywords


def test_extract_keywords_min_length():
    """_extract_keywords filters words shorter than 4 characters."""
    keywords = _extract_keywords("abc defg", "test hypo")
    assert "abc" not in keywords  # too short (3 chars)
    assert "defg" in keywords  # 4 chars, passes
    assert "test" in keywords  # 4 chars, passes
    assert "hypo" in keywords  # 4 chars, passes (exactly meets minimum)


def test_extract_keywords_synonym_expansion_caffeine():
    """_extract_keywords expands caffeine synonyms."""
    keywords = _extract_keywords("caffeine reduction", "less coffee better sleep")
    assert "caffeine" in keywords
    # Synonyms should be added
    assert "coffee" in keywords or "espresso" in keywords


def test_extract_keywords_synonym_expansion_exercise():
    """_extract_keywords expands exercise synonyms."""
    keywords = _extract_keywords("exercise routine", "daily workout improves readiness")
    assert "exercise" in keywords
    # At least some exercise synonyms should be present
    synonyms = _DOMAIN_SYNONYMS.get("exercise", [])
    assert any(s in keywords for s in synonyms)


def test_extract_keywords_synonym_expansion_sleep():
    """_extract_keywords expands sleep synonyms."""
    keywords = _extract_keywords("sleep optimization", "better bedtime habits")
    assert "sleep" in keywords
    # Sleep synonyms should be added
    assert "bedtime" in keywords or "nap" in keywords


def test_extract_keywords_deduplicates():
    """_extract_keywords does not include duplicates."""
    keywords = _extract_keywords("sleep sleep sleep", "sleep sleep sleep")
    # Should only appear once
    assert keywords.count("sleep") == 1


# ── summarise_period tests ─────────────────────────────────────────────────


def test_summarise_period_basic():
    """summarise_period computes averages from Oura data."""
    data = {
        "2024-01-01": {"sleep_score": 80, "readiness_score": 70, "readiness_contributors": {"hrv_balance": 50}},
        "2024-01-02": {"sleep_score": 82, "readiness_score": 72, "readiness_contributors": {"hrv_balance": 55}},
        "2024-01-03": {"sleep_score": 78, "readiness_score": 68, "readiness_contributors": {"hrv_balance": 45}},
    }
    summary = summarise_period(data)

    assert summary["days"] == 3
    assert summary["sleep_avg"] == 80.0  # (80+82+78)/3
    assert summary["sleep_range"] == "78-82"
    assert summary["readiness_avg"] == 70.0
    assert summary["readiness_range"] == "68-72"
    assert summary["hrv_balance_avg"] == 50.0
    assert summary["hrv_balance_range"] == "45-55"


def test_summarise_period_empty_data():
    """summarise_period handles empty data gracefully."""
    summary = summarise_period({})

    assert summary["days"] == 0
    assert summary["sleep_avg"] is None
    assert summary["sleep_range"] is None
    assert summary["readiness_avg"] is None
    assert summary["readiness_range"] is None
    assert summary["hrv_balance_avg"] is None
    assert summary["hrv_balance_range"] is None


def test_summarise_period_missing_scores():
    """summarise_period handles entries with missing scores."""
    data = {
        "2024-01-01": {"sleep_score": 80},  # missing readiness
        "2024-01-02": {"readiness_score": 70},  # missing sleep
        "2024-01-03": {},  # missing both
    }
    summary = summarise_period(data)

    assert summary["days"] == 3
    assert summary["sleep_avg"] == 80.0
    assert summary["readiness_avg"] == 70.0


def test_summarise_period_none_contributors():
    """summarise_period handles None contributors gracefully."""
    data = {
        "2024-01-01": {
            "sleep_score": 80,
            "readiness_score": 70,
            "readiness_contributors": None,
        },
    }
    summary = summarise_period(data)

    assert summary["hrv_balance_avg"] is None
    assert summary["hrv_balance_range"] is None


def test_summarise_period_single_day():
    """summarise_period handles single day of data."""
    data = {
        "2024-01-01": {
            "sleep_score": 85,
            "readiness_score": 75,
            "readiness_contributors": {"hrv_balance": 60},
        },
    }
    summary = summarise_period(data)

    assert summary["days"] == 1
    assert summary["sleep_avg"] == 85.0
    assert summary["sleep_range"] == "85-85"


# ── _extract_float tests ───────────────────────────────────────────────────


def test_extract_float_basic():
    """_extract_float extracts float from text pattern."""
    text = "Sleep: avg 78.5, range 70-85"
    result = _extract_float(text, r"Sleep: avg ([\d.]+)")
    assert result == 78.5


def test_extract_float_integer():
    """_extract_float handles integer values."""
    text = "Readiness: avg 80"
    result = _extract_float(text, r"Readiness: avg ([\d.]+)")
    assert result == 80.0


def test_extract_float_not_found():
    """_extract_float returns None when pattern not found."""
    text = "No matching pattern here"
    result = _extract_float(text, r"Sleep: avg ([\d.]+)")
    assert result is None


def test_extract_float_invalid_number():
    """_extract_float returns None for non-numeric match."""
    text = "Sleep: avg notanumber"
    result = _extract_float(text, r"Sleep: avg ([\w]+)")
    assert result is None


# ── _is_active tests ───────────────────────────────────────────────────────


def test_is_active_true(tmp_path):
    """_is_active returns True for active experiments."""
    exp_file = tmp_path / "assay-test.md"
    exp_file.write_text("---\nstatus: active\n---\n# Test")
    assert _is_active(exp_file) is True


def test_is_active_false_closed(tmp_path):
    """_is_active returns False for closed experiments."""
    exp_file = tmp_path / "assay-test.md"
    exp_file.write_text("---\nstatus: closed\n---\n# Test")
    assert _is_active(exp_file) is False


def test_is_active_false_no_status(tmp_path):
    """_is_active returns False when no status in file."""
    exp_file = tmp_path / "assay-test.md"
    exp_file.write_text("---\nname: test\n---\n# Test")
    assert _is_active(exp_file) is False


# ── find_experiment tests ──────────────────────────────────────────────────


def test_find_experiment_by_name(tmp_path, monkeypatch):
    """find_experiment finds experiment by fuzzy name match."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()
    exp_file = exp_dir / "assay-2024-01-01-caffeine-cut.md"
    exp_file.write_text("---\nstatus: active\n---\n# Test")

    monkeypatch.setattr(_mod["Path"], "home", lambda: tmp_path)
    # Update EXPERIMENT_DIR in the module
    original_dir = _mod["EXPERIMENT_DIR"]
    _mod["EXPERIMENT_DIR"] = exp_dir
    try:
        result = find_experiment("caffeine cut")
    finally:
        _mod["EXPERIMENT_DIR"] = original_dir

    assert result == exp_file


def test_find_experiment_no_match_returns_none(tmp_path, monkeypatch):
    """find_experiment returns None when no match found."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()

    original_dir = _mod["EXPERIMENT_DIR"]
    _mod["EXPERIMENT_DIR"] = exp_dir
    try:
        result = find_experiment("nonexistent")
    finally:
        _mod["EXPERIMENT_DIR"] = original_dir

    assert result is None


def test_find_experiment_empty_dir_returns_none(tmp_path):
    """find_experiment returns None for empty experiment directory."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()

    original_dir = _mod["EXPERIMENT_DIR"]
    _mod["EXPERIMENT_DIR"] = exp_dir
    try:
        result = find_experiment(None)
    finally:
        _mod["EXPERIMENT_DIR"] = original_dir

    assert result is None


def test_find_experiment_single_active_returns_it(tmp_path):
    """find_experiment returns the only active experiment when no name given."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()
    exp_file = exp_dir / "assay-2024-01-01-test.md"
    exp_file.write_text("---\nstatus: active\n---\n# Test")

    original_dir = _mod["EXPERIMENT_DIR"]
    _mod["EXPERIMENT_DIR"] = exp_dir
    try:
        result = find_experiment(None)
    finally:
        _mod["EXPERIMENT_DIR"] = original_dir

    assert result == exp_file


def test_find_experiment_multiple_active_no_name_returns_none(tmp_path):
    """find_experiment returns None when multiple active and no name given."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()
    (exp_dir / "assay-2024-01-01-test1.md").write_text("---\nstatus: active\n---\n# Test1")
    (exp_dir / "assay-2024-01-02-test2.md").write_text("---\nstatus: active\n---\n# Test2")

    original_dir = _mod["EXPERIMENT_DIR"]
    _mod["EXPERIMENT_DIR"] = exp_dir
    try:
        result = find_experiment(None)
    finally:
        _mod["EXPERIMENT_DIR"] = original_dir

    assert result is None


# ── list_experiments tests ─────────────────────────────────────────────────


def test_list_experiments_returns_sorted(tmp_path):
    """list_experiments returns sorted list of experiment files."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()
    exp1 = exp_dir / "assay-2024-01-02-later.md"
    exp2 = exp_dir / "assay-2024-01-01-earlier.md"
    exp1.write_text("content")
    exp2.write_text("content")

    original_dir = _mod["EXPERIMENT_DIR"]
    _mod["EXPERIMENT_DIR"] = exp_dir
    try:
        result = list_experiments()
    finally:
        _mod["EXPERIMENT_DIR"] = original_dir

    assert len(result) == 2
    assert result[0] == exp2  # earlier comes first (sorted)


def test_list_experiments_empty_dir(tmp_path):
    """list_experiments returns empty list for empty directory."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()

    original_dir = _mod["EXPERIMENT_DIR"]
    _mod["EXPERIMENT_DIR"] = exp_dir
    try:
        result = list_experiments()
    finally:
        _mod["EXPERIMENT_DIR"] = original_dir

    assert result == []


def test_list_experiments_filters_by_prefix(tmp_path):
    """list_experiments only returns files matching assay-*.md pattern."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()
    (exp_dir / "assay-2024-01-01-valid.md").write_text("content")
    (exp_dir / "other-file.md").write_text("content")
    (exp_dir / "assay-no-date.md").write_text("content")

    original_dir = _mod["EXPERIMENT_DIR"]
    _mod["EXPERIMENT_DIR"] = exp_dir
    try:
        result = list_experiments()
    finally:
        _mod["EXPERIMENT_DIR"] = original_dir

    assert len(result) == 2  # only assay-*.md files


# ── pull_intake tests ──────────────────────────────────────────────────────


def test_pull_intake_no_meal_plan(tmp_path, monkeypatch):
    """pull_intake returns empty list when meal plan doesn't exist."""
    # Mock MEAL_PLAN to non-existent path
    monkeypatch.setattr(_mod, "MEAL_PLAN", tmp_path / "nonexistent.md")
    result = pull_intake("2024-01-01", ["caffeine"])
    assert result == []


def test_pull_intake_no_order_log(tmp_path, monkeypatch):
    """pull_intake returns empty list when no Order log section."""
    meal_plan = tmp_path / "meal-plan.md"
    meal_plan.write_text("# Meal Plan\n\nNo log here.\n")
    monkeypatch.setattr(_mod, "MEAL_PLAN", meal_plan)

    result = pull_intake("2024-01-01", ["coffee"])
    assert result == []


def test_pull_intake_matches_keywords(tmp_path, monkeypatch):
    """pull_intake returns entries matching keywords."""
    meal_plan = tmp_path / "meal-plan.md"
    meal_plan.write_text(
        "# Meal Plan\n\n"
        "## Order log\n"
        "- 2024-01-15 (Day): Morning coffee\n"
        "- 2024-01-16 (Day): Tea instead\n"
        "- 2024-01-17 (Day): Afternoon espresso\n"
        "\n## Other section\n"
    )
    monkeypatch.setattr(_mod, "MEAL_PLAN", meal_plan)

    result = pull_intake("2024-01-01", ["coffee", "espresso"])
    assert len(result) == 2
    assert any("coffee" in r.lower() for r in result)
    assert any("espresso" in r.lower() for r in result)


def test_pull_intake_filters_by_date(tmp_path, monkeypatch):
    """pull_intake filters entries before start date."""
    meal_plan = tmp_path / "meal-plan.md"
    meal_plan.write_text(
        "## Order log\n"
        "- 2024-01-01 (Day): Old entry\n"
        "- 2024-01-15 (Day): New entry\n"
    )
    monkeypatch.setattr(_mod, "MEAL_PLAN", meal_plan)

    result = pull_intake("2024-01-10", ["entry"])
    assert len(result) == 1
    assert "New entry" in result[0]


def test_pull_intake_strips_prefix(tmp_path, monkeypatch):
    """pull_intake strips the '- ' prefix from entries."""
    meal_plan = tmp_path / "meal-plan.md"
    meal_plan.write_text("## Order log\n- 2024-01-15 (Day): Test entry\n")
    monkeypatch.setattr(_mod, "MEAL_PLAN", meal_plan)

    result = pull_intake("2024-01-01", ["test"])
    assert result[0].startswith("2024-01-15")


# ── cmd_list tests ─────────────────────────────────────────────────────────


cmd_list = _mod["cmd_list"]


def test_cmd_list_no_experiments(capsys, tmp_path):
    """cmd_list prints message when no experiments exist."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()

    original_dir = _mod["EXPERIMENT_DIR"]
    _mod["EXPERIMENT_DIR"] = exp_dir
    try:
        cmd_list(MagicMock())
    finally:
        _mod["EXPERIMENT_DIR"] = original_dir

    out = capsys.readouterr().out
    assert "No experiments found" in out


def test_cmd_list_shows_status(capsys, tmp_path):
    """cmd_list shows status for each experiment."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()
    (exp_dir / "assay-2024-01-01-test1.md").write_text(
        '---\nstatus: active\nname: "Test 1"\n---\n'
    )
    (exp_dir / "assay-2024-01-02-test2.md").write_text(
        '---\nstatus: closed\nname: "Test 2"\n---\n'
    )

    original_dir = _mod["EXPERIMENT_DIR"]
    _mod["EXPERIMENT_DIR"] = exp_dir
    try:
        cmd_list(MagicMock())
    finally:
        _mod["EXPERIMENT_DIR"] = original_dir

    out = capsys.readouterr().out
    assert "[active]" in out
    assert "[closed]" in out


# ── cmd_new tests ──────────────────────────────────────────────────────────


cmd_new = _mod["cmd_new"]


def test_cmd_new_creates_experiment(capsys, tmp_path, monkeypatch):
    """cmd_new creates a new experiment file with correct frontmatter."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()

    # Mock pull_oura and summarise_period
    def mock_pull_oura(start, end):
        return {
            "2024-01-01": {
                "sleep_score": 80,
                "readiness_score": 70,
                "readiness_contributors": {"hrv_balance": 50},
            }
        }

    monkeypatch.setattr(_mod, "EXPERIMENT_DIR", exp_dir)
    monkeypatch.setattr(_mod, "pull_oura", mock_pull_oura)
    monkeypatch.setattr(_mod["date"], "today", lambda: date(2024, 1, 15))

    args = MagicMock()
    args.name = "Test Experiment"
    args.hypothesis = "Testing hypothesis"
    args.intervention = "Test intervention"
    args.days = 7

    cmd_new(args)

    # Check file was created
    files = list(exp_dir.glob("assay-*.md"))
    assert len(files) == 1

    content = files[0].read_text()
    assert "status: active" in content
    assert "Test Experiment" in content
    assert "Testing hypothesis" in content
    assert "Test intervention" in content


def test_cmd_new_pulls_baseline(capsys, tmp_path, monkeypatch):
    """cmd_new pulls baseline data for the correct period."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()

    pull_calls = []

    def mock_pull_oura(start, end):
        pull_calls.append((start, end))
        return {"2024-01-01": {"sleep_score": 80, "readiness_score": 70, "readiness_contributors": {}}}

    monkeypatch.setattr(_mod, "EXPERIMENT_DIR", exp_dir)
    monkeypatch.setattr(_mod, "pull_oura", mock_pull_oura)
    monkeypatch.setattr(_mod["date"], "today", lambda: date(2024, 1, 15))

    args = MagicMock()
    args.name = "Test"
    args.hypothesis = None
    args.intervention = None
    args.days = 7

    cmd_new(args)

    # Baseline should be 7 days before start
    assert len(pull_calls) == 1
    assert pull_calls[0][0] == "2024-01-08"  # 7 days before 2024-01-15
    assert pull_calls[0][1] == "2024-01-14"


# ── cmd_check tests ────────────────────────────────────────────────────────


cmd_check = _mod["cmd_check"]


def test_cmd_check_no_experiment_exits(capsys, tmp_path):
    """cmd_check exits with error when no active experiment found."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()

    original_dir = _mod["EXPERIMENT_DIR"]
    _mod["EXPERIMENT_DIR"] = exp_dir
    try:
        with pytest.raises(SystemExit) as exc_info:
            cmd_check(MagicMock())
        assert exc_info.value.code == 1
    finally:
        _mod["EXPERIMENT_DIR"] = original_dir

    err = capsys.readouterr().err
    assert "No active experiment" in err


def test_cmd_check_appends_to_file(capsys, tmp_path, monkeypatch):
    """cmd_check appends check-in data to experiment file."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()
    exp_file = exp_dir / "assay-2024-01-15-test.md"
    exp_file.write_text(
        "---\n"
        "status: active\n"
        "start_date: 2024-01-15\n"
        "watch_keywords: [test]\n"
        "---\n"
        "## Baseline (2024-01-08 to 2024-01-14)\n"
        "- Sleep: avg 75.0, range 70-80\n"
        "- Readiness: avg 70.0, range 65-75\n"
        "- HRV balance: avg 50.0, range 45-55\n"
        "## Check-ins\n"
    )

    def mock_pull_oura(start, end):
        return {
            "2024-01-15": {
                "sleep_score": 80,
                "readiness_score": 75,
                "readiness_contributors": {"hrv_balance": 55},
            }
        }

    monkeypatch.setattr(_mod, "EXPERIMENT_DIR", exp_dir)
    monkeypatch.setattr(_mod, "pull_oura", mock_pull_oura)
    monkeypatch.setattr(_mod, "pull_intake", lambda s, k: [])
    monkeypatch.setattr(_mod["date"], "today", lambda: date(2024, 1, 15))

    args = MagicMock()
    args.name = None

    cmd_check(args)

    content = exp_file.read_text()
    assert "### Day 1" in content
    assert "Sleep:" in content
    assert "Readiness:" in content


# ── cmd_close tests ────────────────────────────────────────────────────────


cmd_close = _mod["cmd_close"]


def test_cmd_close_no_experiment_exits(capsys, tmp_path):
    """cmd_close exits with error when no active experiment found."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()

    original_dir = _mod["EXPERIMENT_DIR"]
    _mod["EXPERIMENT_DIR"] = exp_dir
    try:
        with pytest.raises(SystemExit) as exc_info:
            cmd_close(MagicMock())
        assert exc_info.value.code == 1
    finally:
        _mod["EXPERIMENT_DIR"] = original_dir

    err = capsys.readouterr().err
    assert "No active experiment" in err


def test_cmd_close_flips_status(capsys, tmp_path, monkeypatch):
    """cmd_close changes status from active to closed."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()
    exp_file = exp_dir / "assay-2024-01-15-test.md"
    exp_file.write_text(
        "---\n"
        "status: active\n"
        "start_date: 2024-01-15\n"
        "end_date: 2024-01-22\n"
        "---\n"
        "## Baseline\n"
        "- Sleep: avg 75.0, range 70-80\n"
        "- Readiness: avg 70.0, range 65-75\n"
        "- HRV balance: avg 50.0, range 45-55\n"
    )

    def mock_pull_oura(start, end):
        return {"2024-01-15": {"sleep_score": 80, "readiness_score": 75, "readiness_contributors": {"hrv_balance": 55}}}

    monkeypatch.setattr(_mod, "EXPERIMENT_DIR", exp_dir)
    monkeypatch.setattr(_mod, "pull_oura", mock_pull_oura)
    monkeypatch.setattr(_mod["date"], "today", lambda: date(2024, 1, 22))

    args = MagicMock()
    args.name = None

    cmd_close(args)

    content = exp_file.read_text()
    assert "status: closed" in content
    assert "status: active" not in content
    assert "## Results" in content
    assert "## Verdict" in content


def test_cmd_close_appends_results(capsys, tmp_path, monkeypatch):
    """cmd_close appends results section with delta calculations."""
    exp_dir = tmp_path / "experiments"
    exp_dir.mkdir()
    exp_file = exp_dir / "assay-2024-01-15-test.md"
    exp_file.write_text(
        "---\n"
        "status: active\n"
        "start_date: 2024-01-15\n"
        "---\n"
        "## Baseline\n"
        "- Sleep: avg 70.0, range 65-75\n"
        "- Readiness: avg 65.0, range 60-70\n"
        "- HRV balance: avg 45.0, range 40-50\n"
    )

    def mock_pull_oura(start, end):
        return {
            "2024-01-15": {"sleep_score": 80, "readiness_score": 75, "readiness_contributors": {"hrv_balance": 55}},
            "2024-01-16": {"sleep_score": 82, "readiness_score": 77, "readiness_contributors": {"hrv_balance": 57}},
        }

    monkeypatch.setattr(_mod, "EXPERIMENT_DIR", exp_dir)
    monkeypatch.setattr(_mod, "pull_oura", mock_pull_oura)
    monkeypatch.setattr(_mod["date"], "today", lambda: date(2024, 1, 17))

    args = MagicMock()
    args.name = None

    cmd_close(args)

    content = exp_file.read_text()
    # Check for delta in results (improvement from baseline)
    assert "70 -> 81" in content or "81" in content  # sleep avg
    assert "65 -> 76" in content or "76" in content  # readiness avg


# ── pull_oura integration test (mocked API) ─────────────────────────────────


pull_oura = _mod["pull_oura"]


def test_pull_oura_fetches_data(monkeypatch):
    """pull_oura fetches and combines sleep and readiness data."""
    mock_sleep = [{"day": "2024-01-01", "score": 80, "contributors": {"deep_sleep": 20}}]
    mock_readiness = [{"day": "2024-01-01", "score": 70, "contributors": {"hrv_balance": 50}}]

    def mock_fetch(endpoint, start, end, token):
        if endpoint == "daily_sleep":
            return mock_sleep
        elif endpoint == "daily_readiness":
            return mock_readiness
        return []

    monkeypatch.setattr(_mod, "_fetch", mock_fetch)
    monkeypatch.setattr(_mod, "_get_token", lambda: "test-token")

    result = pull_oura("2024-01-01", "2024-01-02")

    assert "2024-01-01" in result
    assert result["2024-01-01"]["sleep_score"] == 80
    assert result["2024-01-01"]["readiness_score"] == 70
    assert result["2024-01-01"]["sleep_contributors"]["deep_sleep"] == 20
    assert result["2024-01-01"]["readiness_contributors"]["hrv_balance"] == 50


def test_pull_oura_sorts_by_date(monkeypatch):
    """pull_oura returns data sorted by date."""
    mock_sleep = [
        {"day": "2024-01-03", "score": 85},
        {"day": "2024-01-01", "score": 80},
        {"day": "2024-01-02", "score": 82},
    ]
    mock_readiness = []

    def mock_fetch(endpoint, start, end, token):
        return mock_sleep if endpoint == "daily_sleep" else []

    monkeypatch.setattr(_mod, "_fetch", mock_fetch)
    monkeypatch.setattr(_mod, "_get_token", lambda: "test-token")

    result = pull_oura("2024-01-01", "2024-01-03")

    dates = list(result.keys())
    assert dates == ["2024-01-01", "2024-01-02", "2024-01-03"]


# ── Constants and helpers tests ─────────────────────────────────────────────


def test_stop_words_contains_expected():
    """_STOP_WORDS contains expected stop words."""
    assert "the" in _STOP_WORDS
    assert "and" in _STOP_WORDS
    assert "with" in _STOP_WORDS
    assert "improves" in _STOP_WORDS


def test_domain_synonyms_structure():
    """_DOMAIN_SYNONYMS has expected structure."""
    assert "caffeine" in _DOMAIN_SYNONYMS
    assert "coffee" in _DOMAIN_SYNONYMS["caffeine"]
    assert "sleep" in _DOMAIN_SYNONYMS
    assert "exercise" in _DOMAIN_SYNONYMS


def test_experiment_dir_path():
    """EXPERIMENT_DIR is under vault/chromatin."""
    assert "experiments" in str(EXPERIMENT_DIR)
    assert "chromatin" in str(EXPERIMENT_DIR)
