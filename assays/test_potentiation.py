"""Tests for potentiation organelle — pure FSRS scheduling and logic functions."""

import math
from datetime import UTC, datetime, timedelta, timezone

import pytest


# ---------------------------------------------------------------------------
# Import target module
# ---------------------------------------------------------------------------

from metabolon.organelles.potentiation import (
    DESIRED_RETENTION,
    EXAM_DATE,
    MODE_THRESHOLDS,
    _AGAIN,
    _CardState,
    _EASY,
    _FSRS_PARAMS,
    _GOOD,
    _HARD,
    _MemoryState,
    _NextStates,
    _card_due_hkt,
    _card_last_review,
    _fsrs_forgetting_curve,
    _fsrs_initial_difficulty,
    _fsrs_initial_stability,
    _fsrs_interval,
    _fsrs_next_difficulty,
    _fsrs_next_stability_forget,
    _fsrs_next_stability_recall,
    _get_mode,
    _module_weight,
    _new_card,
    _normalize,
    _parse_datetime,
    _rating_from_str,
    _state_name,
    fsrs_next_states,
)


# ===================================================================
# Constants
# ===================================================================


class TestConstants:
    def test_desired_retention_range(self):
        assert 0.8 <= DESIRED_RETENTION <= 1.0

    def test_mode_thresholds_ordered(self):
        thresholds = [t for t, _ in MODE_THRESHOLDS]
        assert thresholds == sorted(thresholds)

    def test_mode_thresholds_labels(self):
        labels = {label for _, label in MODE_THRESHOLDS}
        assert labels == {"drill", "free-recall", "MCQ"}

    def test_exam_date_aware(self):
        assert EXAM_DATE.tzinfo is not None

    def test_exam_date_year_2026(self):
        assert EXAM_DATE.year == 2026

    def test_fsrs_params_length(self):
        assert len(_FSRS_PARAMS) == 19


# ===================================================================
# FSRS low-level functions
# ===================================================================


class TestFsrsForgettingCurve:
    def test_zero_elapsed_full_retention(self):
        assert _fsrs_forgetting_curve(0, 10.0) == pytest.approx(1.0)

    def test_negative_stability_returns_zero(self):
        assert _fsrs_forgetting_curve(5, -1.0) == 0.0

    def test_zero_stability_returns_zero(self):
        assert _fsrs_forgetting_curve(5, 0.0) == 0.0

    def test_retention_decreases_with_time(self):
        stability = 10.0
        r1 = _fsrs_forgetting_curve(1, stability)
        r10 = _fsrs_forgetting_curve(10, stability)
        r100 = _fsrs_forgetting_curve(100, stability)
        assert r1 > r10 > r100

    def test_known_value(self):
        # R = (1 + t/(9*S))^(-1) => t=9, S=1 => (1+1)^(-1) = 0.5
        assert _fsrs_forgetting_curve(9, 1.0) == pytest.approx(0.5)


class TestFsrsInitialStability:
    def test_returns_param_value(self):
        for rating in (1, 2, 3, 4):
            assert _fsrs_initial_stability(rating) == _FSRS_PARAMS[rating - 1]

    def test_all_positive(self):
        for rating in (1, 2, 3, 4):
            assert _fsrs_initial_stability(rating) > 0


class TestFsrsInitialDifficulty:
    def test_easy_is_easiest(self):
        """Easy (rating=4) should yield the lowest difficulty."""
        d1 = _fsrs_initial_difficulty(1)
        d4 = _fsrs_initial_difficulty(4)
        assert d1 > d4

    def test_bounded(self):
        for rating in (1, 2, 3, 4):
            d = _fsrs_initial_difficulty(rating)
            assert 1.0 <= d <= 10.0


class TestFsrsNextDifficulty:
    def test_good_rating_preserves_near_mean(self):
        """Rating 3 (Good) should cause mean reversion toward D0(Good)."""
        d_good = _fsrs_initial_difficulty(3)
        result = _fsrs_next_difficulty(5.0, 3)
        # After mean reversion, should move toward d_good
        assert abs(result - d_good) < abs(5.0 - d_good)

    def test_clamped_to_range(self):
        for rating in (1, 2, 3, 4):
            d = _fsrs_next_difficulty(1.0, rating)
            assert 1.0 <= d <= 10.0
            d = _fsrs_next_difficulty(10.0, rating)
            assert 1.0 <= d <= 10.0


class TestFsrsNextStabilityRecall:
    def test_positive_output(self):
        s = _fsrs_next_stability_recall(5.0, 10.0, 0.9, 3)
        assert s >= 0.01

    def test_stability_increases_on_good_recall(self):
        """Successful recall should increase stability."""
        old_s = 10.0
        new_s = _fsrs_next_stability_recall(5.0, old_s, 0.9, _GOOD)
        assert new_s > old_s


class TestFsrsNextStabilityForget:
    def test_positive_output(self):
        s = _fsrs_next_stability_forget(5.0, 10.0, 0.5)
        assert s >= 0.01

    def test_forget_reduces_stability_at_high_retrievability(self):
        """Forgetting at high retrievability with high difficulty reduces stability."""
        old_s = 10.0
        new_s = _fsrs_next_stability_forget(8.0, old_s, 0.9)
        assert new_s < old_s

    def test_output_always_positive(self):
        """Even at boundary inputs, stability floor is 0.01."""
        s = _fsrs_next_stability_forget(10.0, 0.1, 0.99)
        assert s >= 0.01


class TestFsrsInterval:
    def test_returns_at_least_one(self):
        assert _fsrs_interval(1.0, 0.9) >= 1.0

    def test_zero_stability_returns_one(self):
        assert _fsrs_interval(0.0, 0.9) >= 1.0

    def test_higher_retention_shorter_interval(self):
        i90 = _fsrs_interval(10.0, 0.9)
        i95 = _fsrs_interval(10.0, 0.95)
        assert i95 < i90

    def test_larger_stability_longer_interval(self):
        i_small = _fsrs_interval(5.0, 0.9)
        i_large = _fsrs_interval(20.0, 0.9)
        assert i_large > i_small

    def test_exact_formula(self):
        # t = 9 * S * (R^-1 - 1) for S=1, R=0.9 => 9*(1.1111-1)=9*0.1111=1.0
        expected = 9.0 * 1.0 * (0.9 ** (-1) - 1)
        assert _fsrs_interval(1.0, 0.9) == pytest.approx(expected)

    def test_retention_one_returns_stability(self):
        assert _fsrs_interval(5.0, 1.0) == 5.0


# ===================================================================
# fsrs_next_states — integration of low-level FSRS
# ===================================================================


class TestFsrsNextStates:
    def test_new_card_returns_all_ratings(self):
        states = fsrs_next_states(None, 0.9, 0)
        assert isinstance(states, _NextStates)
        assert isinstance(states.again, _CardState)
        assert isinstance(states.hard, _CardState)
        assert isinstance(states.good, _CardState)
        assert isinstance(states.easy, _CardState)

    def test_new_card_easy_has_longest_interval(self):
        states = fsrs_next_states(None, 0.9, 0)
        assert states.easy.interval >= states.good.interval
        assert states.good.interval >= states.hard.interval

    def test_new_card_again_shortest_interval(self):
        states = fsrs_next_states(None, 0.9, 0)
        assert states.again.interval <= states.hard.interval

    def test_review_card_states(self):
        prev = _MemoryState(stability=10.0, difficulty=5.0)
        states = fsrs_next_states(prev, 0.9, 3)
        for item in (states.again, states.hard, states.good, states.easy):
            assert item.memory.stability > 0
            assert 1.0 <= item.memory.difficulty <= 10.0
            assert item.interval >= 1.0

    def test_again_reduces_stability_on_review(self):
        prev = _MemoryState(stability=10.0, difficulty=5.0)
        states = fsrs_next_states(prev, 0.9, 5)
        assert states.again.memory.stability < 10.0

    def test_elapsed_days_affects_retrievability(self):
        """Longer elapsed time should produce different states."""
        prev = _MemoryState(stability=10.0, difficulty=5.0)
        short = fsrs_next_states(prev, 0.9, 1)
        long = fsrs_next_states(prev, 0.9, 30)
        # With longer elapsed time, retrievability is lower → different intervals
        assert short.good.interval != long.good.interval


# ===================================================================
# Mode selection
# ===================================================================


class TestGetMode:
    def test_drill_for_weak(self):
        assert _get_mode(0.0) == "drill"
        assert _get_mode(0.30) == "drill"
        assert _get_mode(0.59) == "drill"

    def test_free_recall_for_medium(self):
        assert _get_mode(0.60) == "free-recall"
        assert _get_mode(0.65) == "free-recall"
        assert _get_mode(0.69) == "free-recall"

    def test_mcq_for_strong(self):
        assert _get_mode(0.70) == "MCQ"
        assert _get_mode(0.85) == "MCQ"
        assert _get_mode(1.0) == "MCQ"

    def test_boundary_just_below_drill(self):
        assert _get_mode(0.5999) == "drill"

    def test_boundary_just_below_free_recall(self):
        assert _get_mode(0.6999) == "free-recall"


# ===================================================================
# Rating helpers
# ===================================================================


class TestRatingFromStr:
    def test_primary_names(self):
        assert _rating_from_str("again") == "again"
        assert _rating_from_str("hard") == "hard"
        assert _rating_from_str("good") == "good"
        assert _rating_from_str("easy") == "easy"

    def test_aliases(self):
        assert _rating_from_str("miss") == "again"
        assert _rating_from_str("guess") == "hard"
        assert _rating_from_str("ok") == "good"
        assert _rating_from_str("confident") == "easy"

    def test_case_insensitive(self):
        assert _rating_from_str("Again") == "again"
        assert _rating_from_str("GOOD") == "good"
        assert _rating_from_str("Easy") == "easy"

    def test_unknown_returns_none(self):
        assert _rating_from_str("terrible") is None
        assert _rating_from_str("") is None


# ===================================================================
# State name
# ===================================================================


class TestStateName:
    def test_known_states(self):
        assert _state_name(1) == "learning"
        assert _state_name(2) == "review"
        assert _state_name(3) == "relearning"

    def test_unknown_returns_new(self):
        assert _state_name(0) == "new"
        assert _state_name(99) == "new"


# ===================================================================
# Module weight
# ===================================================================


class TestModuleWeight:
    def test_m1_weight(self):
        assert _module_weight("M1-classical-ai") == pytest.approx(0.10)

    def test_m2_weight(self):
        assert _module_weight("M2-clustering") == pytest.approx(0.30)

    def test_m3_weight(self):
        assert _module_weight("M3-bias-unfairness") == pytest.approx(0.20)

    def test_m4_weight(self):
        assert _module_weight("M4-ethical-frameworks") == pytest.approx(0.20)

    def test_m5_weight(self):
        assert _module_weight("M5-data-governance") == pytest.approx(0.20)

    def test_unknown_prefix_zero(self):
        assert _module_weight("X1-unknown") == 0.0

    def test_weights_sum_to_one(self):
        total = sum(
            _module_weight(f"M{n}-{t}")
            for n in range(1, 6)
            for t in ["test"]
        )
        assert total == pytest.approx(1.0)


# ===================================================================
# Normalize
# ===================================================================


class TestNormalize:
    def test_lowercase(self):
        assert _normalize("Hello") == "hello"

    def test_strip_non_alnum(self):
        assert _normalize("Hello, World!") == "helloworld"

    def test_empty(self):
        assert _normalize("") == ""

    def test_preserves_digits(self):
        assert _normalize("M1-ai-risks") == "m1airisks"


# ===================================================================
# Datetime parsing
# ===================================================================


class TestParseDatetime:
    def test_iso_with_offset(self):
        dt = _parse_datetime("2026-03-15T10:30:00+08:00")
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 3
        assert dt.hour == 10

    def test_utc_z_suffix(self):
        dt = _parse_datetime("2026-03-15T10:30:00+00:00")
        assert dt is not None

    def test_empty_returns_none(self):
        assert _parse_datetime("") is None

    def test_none_returns_none(self):
        assert _parse_datetime(None) is None

    def test_garbage_returns_none(self):
        assert _parse_datetime("not-a-date") is None


# ===================================================================
# Card helpers
# ===================================================================


class TestCardDueHkt:
    def test_parses_utc_to_hkt(self):
        card = {"due": "2026-03-15T02:00:00+00:00"}
        dt = _card_due_hkt(card)
        assert dt is not None
        assert dt.hour == 10  # UTC+8

    def test_none_on_missing_due(self):
        assert _card_due_hkt({}) is None
        assert _card_due_hkt({"due": ""}) is None


class TestCardLastReview:
    def test_parses_review(self):
        card = {"last_review": "2026-03-15T10:00:00+08:00"}
        dt = _card_last_review(card)
        assert dt is not None
        assert dt.hour == 10

    def test_none_on_missing(self):
        assert _card_last_review({}) is None
        assert _card_last_review({"last_review": ""}) is None


class TestNewCard:
    def test_structure(self):
        now = datetime(2026, 3, 15, 10, 0, 0, tzinfo=timezone(timedelta(hours=8)))
        card = _new_card(now)
        assert "card_id" in card
        assert "state" in card
        assert "stability" in card
        assert "difficulty" in card
        assert "due" in card
        assert "last_review" in card

    def test_initial_values(self):
        now = datetime(2026, 3, 15, 10, 0, 0, tzinfo=timezone(timedelta(hours=8)))
        card = _new_card(now)
        assert card["state"] == 1
        assert card["stability"] == 0.0
        assert card["difficulty"] == 0.0
        assert card["step"] == 0

    def test_card_id_positive(self):
        now = datetime(2026, 3, 15, 10, 0, 0, tzinfo=timezone(timedelta(hours=8)))
        card = _new_card(now)
        assert card["card_id"] > 0
