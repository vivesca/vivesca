from __future__ import annotations

"""Tests for breaking.py"""


from datetime import UTC, datetime, timedelta
from pathlib import Path
import tempfile
import json

import pytest

from metabolon.organelles.endocytosis_rss.breaking import (
    is_breaking,
    _article_is_fresh,
    article_hash,
    title_fingerprint,
    restore_breaking_state,
    persist_breaking_state,
    refractory_daily_counter,
    can_alert,
    _age_minutes,
)


class TestIsBreaking:
    """Tests for breaking news detection"""

    def test_breaking_match(self):
        """Matching entity + action, no negative → True"""
        assert is_breaking("OpenAI launches GPT-5") is True
        assert is_breaking("Anthropic releases Claude 4 Opus") is True
        assert is_breaking("Google DeepMind unveils Gemini 3") is True
        assert is_breaking("SEC bans crypto trading for AI companies") is True

    def test_no_entity_returns_false(self):
        """No known entity → False"""
        assert is_breaking("Local bakery launches new bread") is False

    def test_no_action_returns_false(self):
        """No action word → False"""
        assert is_breaking("OpenAI and the future of AI") is False

    def test_negative_returns_false(self):
        """Negative keyword kills it"""
        assert is_breaking("OpenAI hiring senior research scientist") is False
        assert is_breaking("Anthropic podcast discusses safety") is False
        assert is_breaking("Meta AI raises new funding round") is False


class TestArticleIsFresh:
    """Tests for freshness check"""

    def test_fresh_within_window(self):
        """Article published recently is fresh"""
        now = datetime.now(UTC)
        hour_ago = (now - timedelta(hours=1)).isoformat()
        article = {"published_at": hour_ago}
        assert _article_is_fresh(article, now) is True

    def test_stale_outside_window(self):
        """Article older than 2 hours is stale"""
        now = datetime.now(UTC)
        three_hours_ago = (now - timedelta(hours=3)).isoformat()
        article = {"published_at": three_hours_ago}
        assert _article_is_fresh(article, now) is False

    def test_no_date_fails_open(self):
        """No published_at → treated as fresh"""
        now = datetime.now(UTC)
        article = {}
        assert _article_is_fresh(article, now) is True

    def test_bad_date_fails_open(self):
        """Bad date format → treated as fresh"""
        now = datetime.now(UTC)
        article = {"published_at": "not-a-date"}
        assert _article_is_fresh(article, now) is True


class TestArticleHash:
    """Tests for article hash"""

    def test_article_hash_consistent(self):
        """Same inputs produce same hash"""
        h1 = article_hash("Title", "https://link", "Source")
        h2 = article_hash("Title", "https://link", "Source")
        assert h1 == h2

    def test_article_hash_changes_with_content(self):
        """Different content produces different hash"""
        h1 = article_hash("Title", "https://link", "Source")
        h2 = article_hash("Different", "https://link", "Source")
        assert h1 != h2

    def test_hash_length_16(self):
        """Output is 16 hex chars"""
        h = article_hash("test", "test", "test")
        assert len(h) == 16


class TestTitleFingerprint:
    """Tests for title fingerprinting (cross-source dedup)"""

    def test_same_title_different_case_punctuation_same_fingerprint(self):
        """Normalizes case, punctuation, whitespace → same fingerprint"""
        fp1 = title_fingerprint("OpenAI launches GPT-4o!")
        fp2 = title_fingerprint("openai launches gpt 4o")
        assert fp1 == fp2

    def test_different_titles_different_fingerprint(self):
        """Different titles → different fingerprint"""
        fp1 = title_fingerprint("OpenAI launches GPT-4o")
        fp2 = title_fingerprint("Google launches Gemini")
        assert fp1 != fp2


class TestStatePersistence:
    """Tests for state save/restore"""

    def test_restore_creates_default_on_missing_file(self):
        """Missing file creates default state"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state.json"
            now = datetime(2024, 3, 15, 10, 30, 0, tzinfo=UTC)
            state = restore_breaking_state(path, now)
            assert state["alerts_today"] == 0
            assert state["today_date"] == "2024-03-15"
            assert "seen_ids" in state

    def test_persist_and_restore(self):
        """Persisted state restores correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state.json"
            now = datetime(2024, 3, 15, 10, 30, 0, tzinfo=UTC)
            original = {
                "last_check": now.isoformat(),
                "seen_ids": ["abc123", "def456"],
                "alerts_today": 2,
                "today_date": "2024-03-15",
                "last_alert_time": now.isoformat(),
            }
            persist_breaking_state(path, original)
            restored = restore_breaking_state(path, now)
            assert restored["alerts_today"] == 2
            assert restored["seen_ids"] == ["abc123", "def456"]

    def test_corrupt_file_returns_default(self):
        """Corrupt JSON → returns default"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state.json"
            path.write_text("not valid json {{{{", encoding="utf-8")
            now = datetime(2024, 3, 15, tzinfo=UTC)
            state = restore_breaking_state(path, now)
            assert "alerts_today" in state


class TestRefractoryDailyCounter:
    """Tests for daily counter reset"""

    def test_resets_on_new_day(self):
        """Counter resets when date changes"""
        state = {"alerts_today": 3, "today_date": "2024-03-14"}
        now = datetime(2024, 3, 15, 10, 0, 0, tzinfo=UTC)
        refractory_daily_counter(state, now)
        assert state["alerts_today"] == 0
        assert state["today_date"] == "2024-03-15"

    def test_keeps_count_same_day(self):
        """Keeps current count on same day"""
        state = {"alerts_today": 2, "today_date": "2024-03-15"}
        now = datetime(2024, 3, 15, 10, 0, 0, tzinfo=UTC)
        refractory_daily_counter(state, now)
        assert state["alerts_today"] == 2


class TestCanAlert:
    """Tests for throttling / cooldown check"""

    def test_allows_first_alert(self):
        """No prior alerts → can alert"""
        state = {"alerts_today": 0, "last_alert_time": None}
        now = datetime.now(UTC)
        assert can_alert(state, now) is True

    def test_blocks_when_daily_cap_reached(self):
        """Daily cap reached → blocks"""
        state = {"alerts_today": 3, "last_alert_time": None}  # MAX_ALERTS_PER_DAY = 3
        now = datetime.now(UTC)
        assert can_alert(state, now) is False

    def test_allows_after_cooldown(self):
        """Cooldown elapsed → allows alert"""
        two_hours_ago = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
        state = {"alerts_today": 1, "last_alert_time": two_hours_ago}
        assert can_alert(state, datetime.now(UTC)) is True

    def test_blocks_before_cooldown(self):
        """Cooldown not elapsed → blocks"""
        thirty_mins_ago = (datetime.now(UTC) - timedelta(minutes=30)).isoformat()
        state = {"alerts_today": 1, "last_alert_time": thirty_mins_ago}
        assert can_alert(state, datetime.now(UTC)) is False


class TestAgeMinutes:
    """Tests for age calculation in minutes"""

    def test_calculates_correct_age(self):
        """Correctly calculates age from ISO string"""
        now = datetime.now(UTC)
        published = (now - timedelta(minutes=90)).isoformat()
        age = _age_minutes(published, now)
        assert age == 90.0

    def test_returns_none_for_empty(self):
        """Empty string → None"""
        now = datetime.now(UTC)
        assert _age_minutes("", now) is None

    def test_returns_none_for_bad_date(self):
        """Bad date → None"""
        now = datetime.now(UTC)
        assert _age_minutes("not-a-date", now) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
