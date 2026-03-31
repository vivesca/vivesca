#!/usr/bin/env python3
"""Tests for effectors/x-feed-to-lustro — Fetch X feed via bird CLI and save to lustro cache.

X-feed-to-lustro is a script, not an importable module.
It is loaded via exec() into isolated namespaces.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

X_FEED_PATH = Path(__file__).resolve().parents[1] / "effectors" / "x-feed-to-lustro"


# ── Fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def xfeed(tmp_path):
    """Load x-feed-to-lustro via exec into an isolated namespace, redirect cache dir."""
    ns: dict = {"__name__": "test_x_feed_to_lustro", "__doc__": ""}
    source = X_FEED_PATH.read_text(encoding="utf-8")
    exec(source, ns)

    # Redirect cache directory to tmp_path
    cache_dir = tmp_path / ".cache" / "lustro-articles"
    ns["CACHE_DIR"] = cache_dir
    return ns


# ── Constants ───────────────────────────────────────────────────────────────


class TestConstants:
    def test_cache_dir_default(self):
        """Default cache dir should be under ~/.cache/lustro-articles."""
        ns: dict = {"__name__": "test"}
        exec(X_FEED_PATH.read_text(), ns)
        assert str(ns["CACHE_DIR"]).endswith("lustro-articles")

    def test_count_default(self, xfeed):
        """Default count should be 20."""
        assert xfeed["COUNT"] == 20

    def test_min_text_length(self, xfeed):
        """Minimum text length should be 100."""
        assert xfeed["MIN_TEXT_LENGTH"] == 100


# ── main: bird CLI failure ──────────────────────────────────────────────────


class TestBirdFailure:
    def test_bird_nonzero_exits(self, xfeed):
        """Should exit 1 when bird home returns nonzero."""
        mock_result = MagicMock(returncode=1, stderr="bird: command not found")
        with patch.object(subprocess, "run", return_value=mock_result):
            with pytest.raises(SystemExit) as exc_info:
                xfeed["main"]()
        assert exc_info.value.code == 1

    def test_bird_timeout_exits(self, xfeed):
        """Should handle bird timeout."""
        with patch.object(
            subprocess, "run", side_effect=subprocess.TimeoutExpired("bird", 60)
        ):
            with pytest.raises(SystemExit):
                xfeed["main"]()


# ── main: tweet processing ─────────────────────────────────────────────────


class TestTweetProcessing:
    def _make_tweet(self, text="x" * 150, handle="user1", name="User One",
                    url="https://x.com/user1/status/1", date="Mon Jan 01 12:00:00 +0000 2026",
                    quoted_tweet=None):
        tweet = {
            "text": text,
            "author": {"handle": handle, "name": name},
            "url": url,
            "date": date,
        }
        if quoted_tweet:
            tweet["quoted_tweet"] = quoted_tweet
        return tweet

    def test_saves_long_tweet(self, xfeed, capsys):
        """Should save tweets with text >= MIN_TEXT_LENGTH."""
        tweets = [self._make_tweet(text="a" * 200)]
        mock_result = MagicMock(returncode=0, stdout=json.dumps(tweets))
        with patch.object(subprocess, "run", return_value=mock_result):
            xfeed["main"]()

        cache_files = list(xfeed["CACHE_DIR"].glob("*.json"))
        assert len(cache_files) == 1
        record = json.loads(cache_files[0].read_text())
        assert record["source"] == "X Feed (For You)"
        assert "user1" in record["title"]

    def test_skips_short_tweets(self, xfeed, capsys):
        """Should skip tweets with text < MIN_TEXT_LENGTH."""
        tweets = [self._make_tweet(text="short")]
        mock_result = MagicMock(returncode=0, stdout=json.dumps(tweets))
        with patch.object(subprocess, "run", return_value=mock_result):
            xfeed["main"]()

        cache_files = list(xfeed["CACHE_DIR"].glob("*.json"))
        assert len(cache_files) == 0
        err = capsys.readouterr().err
        assert "skipped" in err.lower()

    def test_deduplicates_by_hash(self, xfeed, capsys):
        """Should not overwrite existing files with same hash."""
        tweets = [self._make_tweet(text="b" * 200)]
        mock_result = MagicMock(returncode=0, stdout=json.dumps(tweets))

        # First call: saves the file
        with patch.object(subprocess, "run", return_value=mock_result):
            xfeed["main"]()

        cache_files = list(xfeed["CACHE_DIR"].glob("*.json"))
        assert len(cache_files) == 1
        first_content = cache_files[0].read_text()

        # Second call: should skip since file already exists
        with patch.object(subprocess, "run", return_value=mock_result):
            xfeed["main"]()

        cache_files = list(xfeed["CACHE_DIR"].glob("*.json"))
        assert len(cache_files) == 1
        assert cache_files[0].read_text() == first_content

    def test_includes_quoted_tweet_text(self, xfeed, capsys):
        """Should append quoted tweet text to the body."""
        tweet = self._make_tweet(
            text="a" * 80,
            quoted_tweet={"text": "b" * 80},
        )
        tweets = [tweet]
        mock_result = MagicMock(returncode=0, stdout=json.dumps(tweets))
        with patch.object(subprocess, "run", return_value=mock_result):
            xfeed["main"]()

        cache_files = list(xfeed["CACHE_DIR"].glob("*.json"))
        assert len(cache_files) == 1
        record = json.loads(cache_files[0].read_text())
        # Combined length >= 100
        assert "a" in record["text"]
        assert "b" in record["text"]

    def test_filename_contains_date_and_hash(self, xfeed, capsys):
        """Filename should be YYYY-MM-DD_x-feed_HASH.json."""
        tweets = [self._make_tweet(text="c" * 200)]
        mock_result = MagicMock(returncode=0, stdout=json.dumps(tweets))
        with patch.object(subprocess, "run", return_value=mock_result):
            xfeed["main"]()

        cache_files = list(xfeed["CACHE_DIR"].glob("*.json"))
        assert len(cache_files) == 1
        name = cache_files[0].name
        assert name.startswith("2026-01-01") or "_x-feed_" in name
        assert "_x-feed_" in name
        assert name.endswith(".json")

    def test_record_has_required_fields(self, xfeed, capsys):
        """Saved records should have all required fields."""
        tweets = [self._make_tweet(text="d" * 200)]
        mock_result = MagicMock(returncode=0, stdout=json.dumps(tweets))
        with patch.object(subprocess, "run", return_value=mock_result):
            xfeed["main"]()

        cache_files = list(xfeed["CACHE_DIR"].glob("*.json"))
        record = json.loads(cache_files[0].read_text())
        for field in ["title", "date", "source", "tier", "link", "summary", "text", "fetched_at"]:
            assert field in record, f"Missing field: {field}"
        assert record["tier"] == 1

    def test_handles_single_tweet_not_list(self, xfeed, capsys):
        """Should handle when bird returns a single object instead of a list."""
        tweet = self._make_tweet(text="e" * 200)
        mock_result = MagicMock(returncode=0, stdout=json.dumps(tweet))  # single object
        with patch.object(subprocess, "run", return_value=mock_result):
            xfeed["main"]()

        cache_files = list(xfeed["CACHE_DIR"].glob("*.json"))
        assert len(cache_files) == 1

    def test_handles_invalid_date_gracefully(self, xfeed, capsys):
        """Should use current date when date parsing fails."""
        tweet = self._make_tweet(text="f" * 200, date="not-a-date")
        tweets = [tweet]
        mock_result = MagicMock(returncode=0, stdout=json.dumps(tweets))
        with patch.object(subprocess, "run", return_value=mock_result):
            xfeed["main"]()

        cache_files = list(xfeed["CACHE_DIR"].glob("*.json"))
        assert len(cache_files) == 1
        record = json.loads(cache_files[0].read_text())
        # Should default to today's date
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        assert record["date"] == today

    def test_multiple_tweets_saved(self, xfeed, capsys):
        """Should save multiple qualifying tweets."""
        tweets = [
            self._make_tweet(text=f"tweet{i}_" + "x" * 200, handle=f"user{i}")
            for i in range(3)
        ]
        mock_result = MagicMock(returncode=0, stdout=json.dumps(tweets))
        with patch.object(subprocess, "run", return_value=mock_result):
            xfeed["main"]()

        cache_files = list(xfeed["CACHE_DIR"].glob("*.json"))
        assert len(cache_files) == 3

    def test_mixed_short_and_long_tweets(self, xfeed, capsys):
        """Should save long tweets and skip short ones."""
        tweets = [
            self._make_tweet(text="short", handle="short_user"),
            self._make_tweet(text="l" * 200, handle="long_user"),
        ]
        mock_result = MagicMock(returncode=0, stdout=json.dumps(tweets))
        with patch.object(subprocess, "run", return_value=mock_result):
            xfeed["main"]()

        cache_files = list(xfeed["CACHE_DIR"].glob("*.json"))
        assert len(cache_files) == 1
        err = capsys.readouterr().err
        assert "1 saved" in err
        assert "1 skipped" in err

    def test_summary_printed_to_stderr(self, xfeed, capsys):
        """Should print summary stats to stderr."""
        tweets = [self._make_tweet(text="g" * 200)]
        mock_result = MagicMock(returncode=0, stdout=json.dumps(tweets))
        with patch.object(subprocess, "run", return_value=mock_result):
            xfeed["main"]()

        err = capsys.readouterr().err
        assert "x-feed-to-lustro:" in err
        assert "1 saved" in err
        assert "1 total" in err

    def test_creates_cache_dir(self, xfeed, capsys):
        """Should create cache directory if it doesn't exist."""
        assert not xfeed["CACHE_DIR"].exists()
        tweets = [self._make_tweet(text="h" * 200)]
        mock_result = MagicMock(returncode=0, stdout=json.dumps(tweets))
        with patch.object(subprocess, "run", return_value=mock_result):
            xfeed["main"]()

        assert xfeed["CACHE_DIR"].exists()

    def test_default_author_on_missing_fields(self, xfeed, capsys):
        """Should use default values when author fields are missing."""
        tweet = {"text": "x" * 200, "url": "https://x.com/u/s/1", "date": ""}
        tweets = [tweet]
        mock_result = MagicMock(returncode=0, stdout=json.dumps(tweets))
        with patch.object(subprocess, "run", return_value=mock_result):
            xfeed["main"]()

        cache_files = list(xfeed["CACHE_DIR"].glob("*.json"))
        assert len(cache_files) == 1
        record = json.loads(cache_files[0].read_text())
        assert "unknown" in record["title"]


# ── CLI subprocess ──────────────────────────────────────────────────────────


class TestCLISubprocess:
    def test_no_bird_exits_nonzero(self):
        """Running x-feed-to-lustro without bird should exit nonzero."""
        r = subprocess.run(
            [str(X_FEED_PATH)],
            capture_output=True, text=True, timeout=30,
        )
        assert r.returncode != 0
