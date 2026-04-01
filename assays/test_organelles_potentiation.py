from __future__ import annotations

"""Tests for metabolon/organelles/potentiation.py - FSRS spaced repetition engine."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def mock_chromatin(tmp_path):
    """Mock chromatin directory for file operations."""
    chromatin_dir = tmp_path / "chromatin"
    chromatin_dir.mkdir(parents=True, exist_ok=True)
    with patch("metabolon.organelles.potentiation._chromatin", chromatin_dir):
        yield chromatin_dir


@pytest.fixture
def mock_now():
    """Fixed datetime for deterministic testing."""
    fixed_dt = datetime(2026, 3, 25, 12, 0, 0, tzinfo=timezone(timedelta(hours=8)))
    with patch("metabolon.organelles.potentiation._now_hkt", return_value=fixed_dt):
        yield fixed_dt


@pytest.fixture
def potentiation_module(mock_chromatin):
    """Import potentiation module with mocked chromatin path."""
    from metabolon.organelles import potentiation
    return potentiation


# ── FSRS Algorithm Tests ────────────────────────────────────────────────────


def test_fsrs_forgetting_curve_zero_stability(potentiation_module):
    """Forgetting curve returns 0 for zero/negative stability."""
    assert potentiation_module._fsrs_forgetting_curve(0, 0) == 0.0
    assert potentiation_module._fsrs_forgetting_curve(10, -5) == 0.0


def test_fsrs_forgetting_curve_normal(potentiation_module):
    """Forgetting curve decreases with elapsed days."""
    # At day 0, retrievability should be 1.0
    r0 = potentiation_module._fsrs_forgetting_curve(0, 10)
    assert abs(r0 - 1.0) < 0.01
    
    # After 10 days with stability 10, R should be < 1.0
    r10 = potentiation_module._fsrs_forgetting_curve(10, 10)
    assert 0.5 < r10 < 1.0
    
    # More elapsed days = lower retrievability
    r20 = potentiation_module._fsrs_forgetting_curve(20, 10)
    assert r20 < r10


def test_fsrs_initial_stability_range(potentiation_module):
    """Initial stability values are positive for all ratings."""
    for rating in [1, 2, 3, 4]:
        s = potentiation_module._fsrs_initial_stability(rating)
        assert s > 0, f"Initial stability for rating {rating} should be positive"


def test_fsrs_initial_difficulty_range(potentiation_module):
    """Initial difficulty is in valid range [1, 10]."""
    for rating in [1, 2, 3, 4]:
        d = potentiation_module._fsrs_initial_difficulty(rating)
        assert 1.0 <= d <= 10.0, f"Initial difficulty {d} out of range for rating {rating}"


def test_fsrs_initial_difficulty_again_hardest(potentiation_module):
    """Again rating (1) produces highest difficulty."""
    d_again = potentiation_module._fsrs_initial_difficulty(1)
    d_easy = potentiation_module._fsrs_initial_difficulty(4)
    assert d_again > d_easy, "Again should produce higher difficulty than Easy"


def test_fsrs_next_difficulty_bounds(potentiation_module):
    """Next difficulty stays within bounds [1, 10]."""
    for rating in [1, 2, 3, 4]:
        for d0 in [1.0, 5.0, 10.0]:
            d = potentiation_module._fsrs_next_difficulty(d0, rating)
            assert 1.0 <= d <= 10.0, f"Difficulty {d} out of bounds"


def test_fsrs_next_stability_recall_positive(potentiation_module):
    """Next stability for recall is always positive."""
    for rating in [2, 3, 4]:  # Hard, Good, Easy
        s = potentiation_module._fsrs_next_stability_recall(
            difficulty=5.0, stability=10.0, retrievability=0.8, rating=rating
        )
        assert s > 0, f"Next stability for rating {rating} should be positive"


def test_fsrs_next_stability_forget_positive(potentiation_module):
    """Next stability for forget (Again) is always positive."""
    s = potentiation_module._fsrs_next_stability_forget(
        difficulty=5.0, stability=10.0, retrievability=0.5
    )
    assert s > 0, "Next stability for forget should be positive"


def test_fsrs_interval_positive(potentiation_module):
    """Interval is always at least 1 day."""
    # Very high retention
    assert potentiation_module._fsrs_interval(10, 0.99) >= 1.0
    # Normal retention
    assert potentiation_module._fsrs_interval(5, 0.9) >= 1.0
    # Zero stability edge case
    assert potentiation_module._fsrs_interval(0, 0.9) >= 1.0


def test_fsrs_interval_higher_stability_longer(potentiation_module):
    """Higher stability produces longer intervals."""
    i_low = potentiation_module._fsrs_interval(5, 0.9)
    i_high = potentiation_module._fsrs_interval(20, 0.9)
    assert i_high > i_low


def test_fsrs_next_states_returns_all_ratings(potentiation_module):
    """fsrs_next_states returns states for all 4 ratings."""
    states = potentiation_module.fsrs_next_states(None, 0.9, 0)
    assert hasattr(states, 'again')
    assert hasattr(states, 'hard')
    assert hasattr(states, 'good')
    assert hasattr(states, 'easy')
    assert states.again.memory.stability > 0
    assert states.good.memory.stability > 0


def test_fsrs_next_states_new_card(potentiation_module):
    """New card (prev=None) gets initial stability and difficulty."""
    states = potentiation_module.fsrs_next_states(None, 0.9, 0)
    
    # Easy rating should have lower difficulty than Again
    assert states.again.memory.difficulty > states.easy.memory.difficulty


def test_fsrs_next_states_review_card(potentiation_module):
    """Review card uses elapsed days for retrievability."""
    from metabolon.organelles.potentiation import _MemoryState
    
    prev = _MemoryState(stability=10.0, difficulty=5.0)
    states = potentiation_module.fsrs_next_states(prev, 0.9, 5)
    
    # All states should have valid memory
    assert states.again.memory.stability > 0
    assert states.good.memory.stability > 0


# ── Timezone Helper Tests ───────────────────────────────────────────────────


def test_hkt_timezone(potentiation_module):
    """HKT timezone is UTC+8."""
    assert potentiation_module.HKT.utcoffset(None) == timedelta(hours=8)


def test_parse_datetime_iso8601(potentiation_module):
    """Parse ISO8601 datetime strings."""
    dt = potentiation_module._parse_datetime("2026-03-25T12:00:00+08:00")
    assert dt is not None
    assert dt.year == 2026
    assert dt.month == 3
    assert dt.day == 25


def test_parse_datetime_rfc3339(potentiation_module):
    """Parse RFC3339 datetime strings."""
    dt = potentiation_module._parse_datetime("2026-03-25T12:00:00.123456+08:00")
    assert dt is not None
    assert dt.year == 2026


def test_parse_datetime_empty(potentiation_module):
    """Parse empty string returns None."""
    assert potentiation_module._parse_datetime("") is None
    assert potentiation_module._parse_datetime(None) is None


def test_parse_datetime_invalid(potentiation_module):
    """Parse invalid string returns None."""
    assert potentiation_module._parse_datetime("not-a-date") is None


def test_today_hkt(potentiation_module, mock_now):
    """_today_hkt returns current date in HKT."""
    today = potentiation_module._today_hkt()
    assert today.year == 2026
    assert today.month == 3
    assert today.day == 25


# ── Rating Helper Tests ─────────────────────────────────────────────────────


def test_rating_from_str_valid(potentiation_module):
    """Valid rating strings are recognized."""
    assert potentiation_module._rating_from_str("again") == "again"
    assert potentiation_module._rating_from_str("miss") == "again"
    assert potentiation_module._rating_from_str("hard") == "hard"
    assert potentiation_module._rating_from_str("guess") == "hard"
    assert potentiation_module._rating_from_str("good") == "good"
    assert potentiation_module._rating_from_str("ok") == "good"
    assert potentiation_module._rating_from_str("easy") == "easy"
    assert potentiation_module._rating_from_str("confident") == "easy"


def test_rating_from_str_case_insensitive(potentiation_module):
    """Rating strings are case-insensitive."""
    assert potentiation_module._rating_from_str("AGAIN") == "again"
    assert potentiation_module._rating_from_str("Good") == "good"
    assert potentiation_module._rating_from_str("EASY") == "easy"


def test_rating_from_str_invalid(potentiation_module):
    """Invalid rating strings return None."""
    assert potentiation_module._rating_from_str("unknown") is None
    assert potentiation_module._rating_from_str("") is None


def test_state_name(potentiation_module):
    """State names are correctly mapped."""
    assert potentiation_module._state_name(1) == "learning"
    assert potentiation_module._state_name(2) == "review"
    assert potentiation_module._state_name(3) == "relearning"
    assert potentiation_module._state_name(0) == "new"
    assert potentiation_module._state_name(99) == "new"


# ── Mode/Phase/Quota Tests ───────────────────────────────────────────────────


def test_get_mode_drill(potentiation_module):
    """Rate < 60% returns drill mode."""
    assert potentiation_module._get_mode(0.0) == "drill"
    assert potentiation_module._get_mode(0.50) == "drill"
    assert potentiation_module._get_mode(0.59) == "drill"


def test_get_mode_free_recall(potentiation_module):
    """Rate 60-70% returns free-recall mode."""
    assert potentiation_module._get_mode(0.60) == "free-recall"
    assert potentiation_module._get_mode(0.65) == "free-recall"
    assert potentiation_module._get_mode(0.69) == "free-recall"


def test_get_mode_mcq(potentiation_module):
    """Rate >= 70% returns MCQ mode."""
    assert potentiation_module._get_mode(0.70) == "MCQ"
    assert potentiation_module._get_mode(0.85) == "MCQ"
    assert potentiation_module._get_mode(1.0) == "MCQ"


def test_module_weight(potentiation_module):
    """Module weights are correctly assigned."""
    assert potentiation_module._module_weight("M1-ai-risks") == 0.10
    assert potentiation_module._module_weight("M2-clustering") == 0.30
    assert potentiation_module._module_weight("M3-bias-unfairness") == 0.20
    assert potentiation_module._module_weight("M4-ethical-frameworks") == 0.20
    assert potentiation_module._module_weight("M5-data-governance") == 0.20
    assert potentiation_module._module_weight("M6-unknown") == 0.0


def test_get_phase_dates(potentiation_module):
    """Phase determination based on date."""
    from datetime import date
    
    # Cruise phase (until March 13)
    with patch("metabolon.organelles.potentiation._today_hkt", return_value=date(2026, 3, 10)):
        phase, name = potentiation_module._get_phase()
        assert phase == 1
        assert name == "Cruise"
    
    # Ramp phase (March 14-28)
    with patch("metabolon.organelles.potentiation._today_hkt", return_value=date(2026, 3, 20)):
        phase, name = potentiation_module._get_phase()
        assert phase == 2
        assert name == "Ramp"
    
    # Peak phase (after March 28)
    with patch("metabolon.organelles.potentiation._today_hkt", return_value=date(2026, 4, 1)):
        phase, name = potentiation_module._get_phase()
        assert phase == 3
        assert name == "Peak"


def test_daily_quota(potentiation_module):
    """Daily quota depends on phase."""
    from datetime import date
    
    # Phase 1 (Cruise): 10
    with patch("metabolon.organelles.potentiation._today_hkt", return_value=date(2026, 3, 10)):
        assert potentiation_module._daily_quota() == 10
    
    # Phase 2 (Ramp): 15
    with patch("metabolon.organelles.potentiation._today_hkt", return_value=date(2026, 3, 20)):
        assert potentiation_module._daily_quota() == 15
    
    # Phase 3 (Peak): 20
    with patch("metabolon.organelles.potentiation._today_hkt", return_value=date(2026, 4, 1)):
        assert potentiation_module._daily_quota() == 20


# ── Card Helper Tests ────────────────────────────────────────────────────────


def test_new_card(potentiation_module, mock_now):
    """New card has required fields."""
    card = potentiation_module._new_card(mock_now)
    
    assert "card_id" in card
    assert card["state"] == 1
    assert card["step"] == 0
    assert card["stability"] == 0.0
    assert card["difficulty"] == 0.0
    assert "due" in card
    assert "last_review" in card


def test_schedule_card_new_again(potentiation_module, mock_now):
    """Scheduling new card with Again rating."""
    card = potentiation_module._new_card(mock_now)
    result = potentiation_module._schedule_card(card, "again", mock_now)
    
    assert result["state"] == 1  # Learning
    assert result["step"] == 0
    assert result["stability"] > 0
    assert result["difficulty"] > 0


def test_schedule_card_new_good(potentiation_module, mock_now):
    """Scheduling new card with Good rating."""
    card = potentiation_module._new_card(mock_now)
    result = potentiation_module._schedule_card(card, "good", mock_now)
    
    assert result["state"] == 2  # Review
    assert result["stability"] > 0
    assert result["difficulty"] > 0


def test_schedule_card_review(potentiation_module, mock_now):
    """Scheduling a review card."""
    card = {
        "card_id": 12345,
        "state": 2,
        "stability": 10.0,
        "difficulty": 5.0,
        "due": "2026-03-20T12:00:00+00:00",
        "last_review": "2026-03-15T12:00:00+00:00",
    }
    result = potentiation_module._schedule_card(card, "good", mock_now)
    
    assert result["state"] == 2  # Still review
    assert result["card_id"] == 12345


def test_schedule_card_caps_at_exam(potentiation_module, mock_now):
    """Scheduled due date is capped at 2 days before exam."""
    card = potentiation_module._new_card(mock_now)
    result = potentiation_module._schedule_card(card, "easy", mock_now)
    
    # Parse the due date
    due = potentiation_module._parse_datetime(result["due"])
    exam_cutoff = potentiation_module.EXAM_DATE - timedelta(days=2)
    
    assert due <= exam_cutoff


def test_card_due_hkt(potentiation_module):
    """_card_due_hkt converts due string to HKT datetime."""
    card = {"due": "2026-03-25T12:00:00+00:00"}
    due_hkt = potentiation_module._card_due_hkt(card)
    
    assert due_hkt is not None
    assert due_hkt.tzinfo == potentiation_module.HKT


def test_card_due_hkt_missing(potentiation_module):
    """_card_due_hkt returns None for missing due."""
    assert potentiation_module._card_due_hkt({}) is None
    assert potentiation_module._card_due_hkt({"due": ""}) is None


# ── State I/O Tests ──────────────────────────────────────────────────────────


def test_load_state_missing_file(potentiation_module, mock_chromatin):
    """Loading state when file doesn't exist returns empty state."""
    state = potentiation_module._load_state()
    
    assert state == {"cards": {}, "review_log": []}


def test_load_state_existing_file(potentiation_module, mock_chromatin):
    """Loading state from existing file."""
    state_data = {
        "cards": {
            "M1-ai-risks": json.dumps({
                "card_id": 1,
                "stability": 5.0,
                "difficulty": 3.0,
                "due": "2026-03-25T12:00:00+00:00",
                "last_review": "2026-03-20T12:00:00+00:00",
            })
        },
        "review_log": []
    }
    state_file = mock_chromatin / ".garp-fsrs-state.json"
    state_file.write_text(json.dumps(state_data))
    
    state = potentiation_module._load_state()
    
    assert "M1-ai-risks" in state["cards"]
    assert state["cards"]["M1-ai-risks"]["stability"] == 5.0


def test_load_state_corrupt_file(potentiation_module, mock_chromatin):
    """Loading state from corrupt file returns empty state."""
    state_file = mock_chromatin / ".garp-fsrs-state.json"
    state_file.write_text("not valid json{{{")
    
    state = potentiation_module._load_state()
    
    assert state == {"cards": {}, "review_log": []}


def test_save_state(potentiation_module, mock_chromatin, mock_now):
    """Saving state writes to file."""
    state = {
        "cards": {
            "M1-ai-risks": {
                "card_id": 1,
                "stability": 5.0,
                "difficulty": 3.0,
            }
        },
        "review_log": []
    }
    
    potentiation_module._save_state(state)
    
    state_file = mock_chromatin / ".garp-fsrs-state.json"
    assert state_file.exists()
    
    loaded = json.loads(state_file.read_text())
    assert "M1-ai-risks" in loaded["cards"]


def test_save_state_prunes_old_log(potentiation_module, mock_chromatin, mock_now):
    """Saving state prunes review_log entries older than 90 days."""
    old_date = (mock_now - timedelta(days=100)).isoformat()
    recent_date = (mock_now - timedelta(days=10)).isoformat()
    
    state = {
        "cards": {},
        "review_log": [
            {"topic": "old", "date": old_date},
            {"topic": "recent", "date": recent_date},
        ]
    }
    
    potentiation_module._save_state(state)
    
    state_file = mock_chromatin / ".garp-fsrs-state.json"
    loaded = json.loads(state_file.read_text())
    
    assert len(loaded["review_log"]) == 1
    assert loaded["review_log"][0]["topic"] == "recent"


# ── Tracker Parsing Tests ────────────────────────────────────────────────────


def test_parse_tracker_missing_file(potentiation_module, mock_chromatin):
    """Parsing tracker when file doesn't exist returns empty."""
    result = potentiation_module._parse_tracker()
    
    assert result == {"summary": {}, "topics": {}, "recent_misses": []}


def test_parse_tracker_with_content(potentiation_module, mock_chromatin):
    """Parsing tracker with valid content."""
    tracker_content = '''
# GARP RAI Quiz Tracker

## Summary

| Metric | Value |
|--------|-------|
| Total Questions | 42 |
| Correct | 35 |
| Rate | 83% |
| Sessions | 5 |

## Topics

| Topic | Attempts | Correct | Rate |
|-------|----------|---------|------|
| M1-ai-risks | 5 | 4 | 80% |
| M2-clustering | 3 | 2 | 67% |
| M3-bias-unfairness | 4 | 1 | 25% |

## Recent Misses

| Date | Topic | Concept |
|------|-------|---------|
| 2026-03-24 | M1-ai-risks | GOFAI limitations |
| 2026-03-23 | M2-clustering | K-means initialization |
'''
    tracker_file = mock_chromatin / "GARP RAI Quiz Tracker.md"
    tracker_file.write_text(tracker_content)
    
    result = potentiation_module._parse_tracker()
    
    assert result["summary"]["total"] == 42
    assert result["summary"]["correct"] == 35
    assert result["summary"]["rate"] == 83
    assert result["summary"]["sessions"] == 5
    
    assert "M1-ai-risks" in result["topics"]
    assert result["topics"]["M1-ai-risks"]["attempts"] == 5
    assert result["topics"]["M1-ai-risks"]["correct"] == 4
    assert abs(result["topics"]["M1-ai-risks"]["rate"] - 0.8) < 0.01
    
    assert len(result["recent_misses"]) == 2
    assert result["recent_misses"][0]["topic"] == "M1-ai-risks"


def test_parse_tracker_dash_rate(potentiation_module, mock_chromatin):
    """Parsing tracker handles dash (—) for no attempts."""
    tracker_content = '''
| Topic | Attempts | Correct | Rate |
|-------|----------|---------|------|
| M4-ethics-principles | 0 | 0 | — |
'''
    tracker_file = mock_chromatin / "GARP RAI Quiz Tracker.md"
    tracker_file.write_text(tracker_content)
    
    result = potentiation_module._parse_tracker()
    
    assert result["topics"]["M4-ethics-principles"]["rate"] == 0.0


# ── Topic Resolution Tests ────────────────────────────────────────────────────


def test_resolve_topic_exact_match(potentiation_module):
    """Resolve topic with exact match."""
    tracker = {"topics": {"M1-ai-risks": {"attempts": 5}}}
    
    result = potentiation_module._resolve_topic("M1-ai-risks", tracker)
    assert result == "M1-ai-risks"


def test_resolve_topic_case_insensitive(potentiation_module, capsys):
    """Resolve topic case-insensitively."""
    tracker = {"topics": {"M1-ai-risks": {"attempts": 5}}}
    
    result = potentiation_module._resolve_topic("m1-ai-risks", tracker)
    assert result == "M1-ai-risks"


def test_resolve_topic_partial_match(potentiation_module, capsys):
    """Resolve topic with partial match."""
    tracker = {"topics": {"M1-ai-risks": {"attempts": 5}}}
    
    result = potentiation_module._resolve_topic("ai-risks", tracker)
    assert result == "M1-ai-risks"


def test_resolve_topic_not_found(potentiation_module, capsys):
    """Resolve topic not found returns None."""
    tracker = {"topics": {"M1-ai-risks": {"attempts": 5}}}
    
    result = potentiation_module._resolve_topic("nonexistent", tracker)
    assert result is None


def test_resolve_topic_ambiguous(potentiation_module, capsys):
    """Ambiguous topic prints options and returns None."""
    tracker = {"topics": {
        "M2-clustering": {},
        "M2-classification": {},
    }}
    
    result = potentiation_module._resolve_topic("cluster", tracker)
    # Should match M2-clustering uniquely
    assert result == "M2-clustering" or result is None


# ── Normalize Helper Tests ────────────────────────────────────────────────────


def test_normalize(potentiation_module):
    """_normalize removes non-alphanumeric and lowercases."""
    assert potentiation_module._normalize("M1-AI-Risks") == "m1airisks"
    assert potentiation_module._normalize("Hello World!") == "helloworld"
    assert potentiation_module._normalize("") == ""


# ── Topics with Drills Tests ──────────────────────────────────────────────────


def test_topics_with_drills_missing_file(potentiation_module, mock_chromatin):
    """Topics with drills returns empty set if file missing."""
    result = potentiation_module._topics_with_drills()
    assert result == set()


def test_topics_with_drills(potentiation_module, mock_chromatin):
    """Topics with drills parses drill file."""
    drill_content = '''
## M1-ai-risks Definition Drills
Some content

## M2-clustering Definition Drills
More content
'''
    drill_file = mock_chromatin / "GARP RAI Definition Drills.md"
    drill_file.write_text(drill_content)
    
    result = potentiation_module._topics_with_drills()
    
    assert "M1-ai-risks" in result
    assert "M2-clustering" in result


# ── TTY/Display Helper Tests ────────────────────────────────────────────────


def test_is_tty(potentiation_module):
    """_is_tty returns False in test environment."""
    # In pytest, stdout is typically not a TTY
    result = potentiation_module._is_tty()
    assert isinstance(result, bool)


def test_color_when_tty(potentiation_module):
    """_color adds ANSI codes when TTY."""
    with patch("metabolon.organelles.potentiation._is_tty", return_value=True):
        result = potentiation_module._color("test", "31")
        assert result == "\033[31mtest\033[0m"


def test_color_when_not_tty(potentiation_module):
    """_color returns plain text when not TTY."""
    with patch("metabolon.organelles.potentiation._is_tty", return_value=False):
        result = potentiation_module._color("test", "31")
        assert result == "test"


def test_color_helpers(potentiation_module):
    """Color helper functions work correctly."""
    with patch("metabolon.organelles.potentiation._is_tty", return_value=True):
        assert "\033[31m" in potentiation_module._red("error")
        assert "\033[32m" in potentiation_module._green("ok")
        assert "\033[33m" in potentiation_module._yellow("warn")
        assert "\033[36m" in potentiation_module._cyan("info")
        assert "\033[1m" in potentiation_module._bold("strong")
        assert "\033[2m" in potentiation_module._dim("faint")


# ── Today's Reviews Tests ─────────────────────────────────────────────────────


def test_get_today_reviews(potentiation_module, mock_now):
    """_get_today_reviews filters by today's date."""
    today_str = mock_now.strftime("%Y-%m-%d")
    yesterday_str = (mock_now - timedelta(days=1)).strftime("%Y-%m-%d")
    
    state = {
        "review_log": [
            {"topic": "M1-ai-risks", "date": today_str + "T10:00:00+08:00"},
            {"topic": "M2-clustering", "date": yesterday_str + "T10:00:00+08:00"},
        ]
    }
    
    result = potentiation_module._get_today_reviews(state)
    
    assert len(result) == 1
    assert result[0]["topic"] == "M1-ai-risks"


# ── Atomic Write Tests ───────────────────────────────────────────────────────


def test_atomic_write(potentiation_module, mock_chromatin):
    """_atomic_write creates file atomically."""
    target = mock_chromatin / "test.txt"
    potentiation_module._atomic_write(target, "test content")
    
    assert target.exists()
    assert target.read_text() == "test content"


# ── Command Tests ─────────────────────────────────────────────────────────────


def test_cmd_today_no_reviews(potentiation_module, mock_chromatin, mock_now, capsys):
    """cmd_today handles no reviews."""
    with patch("metabolon.organelles.potentiation._load_state", return_value={"cards": {}, "review_log": []}):
        with patch("metabolon.organelles.potentiation._parse_tracker", return_value={"summary": {}, "topics": {}}):
            potentiation_module.cmd_today()
    
    captured = capsys.readouterr()
    assert "No reviews today" in captured.out or "Today" in captured.out


def test_cmd_stats(potentiation_module, mock_chromatin, mock_now, capsys):
    """cmd_stats outputs stats."""
    with patch("metabolon.organelles.potentiation._parse_tracker", return_value={
        "summary": {"total": 10, "correct": 8, "rate": 80, "sessions": 2},
        "topics": {}
    }):
        with patch("metabolon.organelles.potentiation._load_state", return_value={"cards": {}, "review_log": []}):
            with patch("metabolon.organelles.potentiation._topics_with_drills", return_value=set()):
                potentiation_module.cmd_stats()
    
    captured = capsys.readouterr()
    assert "Stats" in captured.out


def test_cmd_topics_empty(potentiation_module, mock_chromatin, mock_now, capsys):
    """cmd_topics handles empty state."""
    with patch("metabolon.organelles.potentiation._load_state", return_value={"cards": {}, "review_log": []}):
        with patch("metabolon.organelles.potentiation._parse_tracker", return_value={"summary": {}, "topics": {}}):
            with patch("metabolon.organelles.potentiation._topics_with_drills", return_value=set()):
                potentiation_module.cmd_topics()
    
    captured = capsys.readouterr()
    assert "All topics" in captured.out


def test_cmd_due_no_due(potentiation_module, mock_chromatin, mock_now, capsys):
    """cmd_due handles no due topics."""
    with patch("metabolon.organelles.potentiation._load_state", return_value={"cards": {}, "review_log": []}):
        potentiation_module.cmd_due()
    
    captured = capsys.readouterr()
    assert "due" in captured.out.lower()


def test_cmd_record_invalid_rating(potentiation_module, mock_chromatin, mock_now, capsys):
    """cmd_record handles invalid rating."""
    with patch("metabolon.organelles.potentiation._load_state", return_value={"cards": {}, "review_log": []}):
        with patch("metabolon.organelles.potentiation._parse_tracker", return_value={"summary": {}, "topics": {}}):
            potentiation_module.cmd_record("M1-ai-risks", "invalid")
    
    captured = capsys.readouterr()
    assert "Unknown rating" in captured.out


def test_cmd_record_unknown_topic(potentiation_module, mock_chromatin, mock_now, capsys):
    """cmd_record handles unknown topic."""
    with patch("metabolon.organelles.potentiation._load_state", return_value={"cards": {}, "review_log": []}):
        with patch("metabolon.organelles.potentiation._parse_tracker", return_value={"summary": {}, "topics": {}}):
            with patch("metabolon.organelles.potentiation._resolve_topic", return_value=None):
                potentiation_module.cmd_record("nonexistent", "good")
    
    # Should exit early due to unresolved topic


def test_cmd_void_no_history(potentiation_module, mock_chromatin, mock_now):
    """cmd_void exits when no review history."""
    with patch("metabolon.organelles.potentiation._load_state", return_value={"cards": {}, "review_log": []}):
        with pytest.raises(SystemExit):
            potentiation_module.cmd_void("M1-ai-risks")


def test_cmd_end(potentiation_module, mock_chromatin, mock_now, capsys):
    """cmd_end increments session count."""
    tracker_content = '''
| Sessions |
|----------|
| 5 |
'''
    tracker_file = mock_chromatin / "GARP RAI Quiz Tracker.md"
    tracker_file.write_text(tracker_content)
    
    with patch("metabolon.organelles.potentiation._load_state", return_value={"cards": {}, "review_log": []}):
        potentiation_module.cmd_end()
    
    captured = capsys.readouterr()
    # Session count should be incremented
    assert "Session" in captured.out


def test_cmd_coverage(potentiation_module, mock_chromatin, mock_now, capsys):
    """cmd_coverage outputs coverage info."""
    with patch("metabolon.organelles.potentiation._parse_tracker", return_value={
        "summary": {},
        "topics": {
            "M1-ai-risks": {"attempts": 5, "correct": 4, "rate": 0.8},
            "M2-clustering": {"attempts": 2, "correct": 2, "rate": 1.0},
        }
    }):
        potentiation_module.cmd_coverage()
    
    captured = capsys.readouterr()
    assert "Coverage" in captured.out


def test_cmd_reconcile_in_sync(potentiation_module, mock_chromatin, mock_now, capsys):
    """cmd_reconcile reports in-sync."""
    tracker_content = '''
| Total Questions | 10 |
| Correct | 8 |
| Rate | 80% |

| Topic | Attempts | Correct | Rate |
|-------|----------|---------|------|
| M1-ai-risks | 5 | 4 | 80% |
| M2-clustering | 5 | 4 | 80% |
'''
    tracker_file = mock_chromatin / "GARP RAI Quiz Tracker.md"
    tracker_file.write_text(tracker_content)
    
    potentiation_module.cmd_reconcile()
    
    captured = capsys.readouterr()
    assert "in sync" in captured.out.lower() or "no changes" in captured.out.lower()


# ── CLI Tests ─────────────────────────────────────────────────────────────────


def test_cli_no_args(potentiation_module, capsys):
    """CLI with no args prints help."""
    with patch("sys.argv", ["melete"]):
        potentiation_module._cli()
    
    captured = capsys.readouterr()
    assert "melete" in captured.out


def test_cli_unknown_command(potentiation_module, capsys):
    """CLI with unknown command exits."""
    with patch("sys.argv", ["melete", "unknown"]):
        with pytest.raises(SystemExit):
            potentiation_module._cli()


def test_cli_session(potentiation_module, mock_chromatin, mock_now, capsys):
    """CLI session command works."""
    with patch("sys.argv", ["melete", "session", "5"]):
        with patch("metabolon.organelles.potentiation._load_state", return_value={"cards": {}, "review_log": []}):
            with patch("metabolon.organelles.potentiation._parse_tracker", return_value={"summary": {}, "topics": {}}):
                potentiation_module._cli()
    
    captured = capsys.readouterr()
    # Should output session plan
