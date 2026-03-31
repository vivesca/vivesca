"""Tests for fetcher.py"""
from datetime import UTC, datetime, timedelta
from pathlib import Path
import tempfile
import json
import time

import pytest

from metabolon.organelles.endocytosis_rss.fetcher import (
    _is_safe_url,
    _parse_feed_datetime,
    _parse_feed_date,
    _extract_summary,
    archive_cargo,
    _slug,
    _title_hash,
)


class TestIsSafeUrl:
    """Tests for SSRF protection URL checking"""

    def test_http_url_ok(self):
        """Valid public HTTP URL is safe"""
        assert _is_safe_url("http://example.com/feed") is True

    def test_https_url_ok(self):
        """Valid public HTTPS URL is safe"""
        assert _is_safe_url("https://example.com/feed") is True

    def test_private_ip_blocked(self):
        """Private IP addresses are blocked"""
        assert _is_safe_url("http://192.168.1.1:8080") is False
        assert _is_safe_url("http://10.0.0.1") is False
        assert _is_safe_url("http://172.16.0.1") is False

    def test_loopback_blocked(self):
        """Loopback is blocked"""
        assert _is_safe_url("http://localhost") is False
        assert _is_safe_url("http://127.0.0.1") is False

    def test_non_http_scheme_blocked(self):
        """Non-HTTP schemes are blocked"""
        assert _is_safe_url("file:///etc/passwd") is False
        assert _is_safe_url("ftp://example.com") is False

    def test_invalid_url_returns_false(self):
        """Invalid URLs return False rather than throwing"""
        assert _is_safe_url("not-a-url") is False


class TestParseFeedDate:
    """Tests for date parsing from RSS entries"""

    def test_parses_struct_date(self):
        """Structured tm_year/tm_mon/tm_mday is parsed"""
        from types import SimpleNamespace
        entry = SimpleNamespace(published_parsed=type(
            'obj', (), {'tm_year': 2024, 'tm_mon': 3, 'tm_mday': 15})())
        assert _parse_feed_date(entry) == "2024-03-15"

    def test_falls_back_to_updated_parsed(self):
        """Uses updated_parsed if published_parsed missing"""
        from types import SimpleNamespace
        entry = SimpleNamespace(updated_parsed=type(
            'obj', (), {'tm_year': 2024, 'tm_mon': 3, 'tm_mday': 15})())
        assert _parse_feed_date(entry) == "2024-03-15"

    def test_returns_empty_string_when_no_date(self):
        """No date fields → empty string"""
        from types import SimpleNamespace
        entry = SimpleNamespace()
        assert _parse_feed_date(entry) == ""


class TestParseFeedDatetime:
    """Tests for datetime parsing from RSS entries"""

    def test_parses_struct_datetime(self):
        """Structured parsed struct_time is converted to ISO 8601 UTC"""
        import calendar
        from types import SimpleNamespace
        # 2024-03-15 10:30:00 UTC → timestamp
        dt = datetime(2024, 3, 15, 10, 30, 0, tzinfo=UTC)
        ts = dt.timestamp()
        tm = time.gmtime(ts)
        entry = SimpleNamespace(published_parsed=tm)
        result = _parse_feed_datetime(entry)
        # Result should be ISO 8601
        parsed_result = datetime.fromisoformat(result)
        assert parsed_result.year == 2024
        assert parsed_result.month == 3
        assert parsed_result.day == 15
        assert parsed_result.hour == 10

    def test_returns_empty_string_when_no_datetime(self):
        """No datetime → empty string"""
        from types import SimpleNamespace
        entry = SimpleNamespace()
        assert _parse_feed_datetime(entry) == ""


class TestExtractSummary:
    """Tests for HTML summary extraction"""

    def test_extracts_first_sentence(self):
        """Strips HTML and takes first sentence"""
        html = "<p>OpenAI launches new GPT-4o model. It's faster and cheaper.</p>"
        result = _extract_summary(type('entry', (), {'summary': html})())
        assert "OpenAI launches new GPT-4o model" in result
        assert "." not in result  # only first sentence

    def test_handles_empty_summary(self):
        """Empty summary → empty output"""
        result = _extract_summary(type('entry', (), {'summary': ''})())
        assert result == ""

    def test_truncates_long_summary(self):
        """Truncates to 120 chars"""
        long_text = "x" * 200
        html = f"<p>{long_text}</p>"
        result = _extract_summary(type('entry', (), {'summary': html})())
        assert len(result) <= 120


class TestSlug:
    """Tests for slugification"""

    def test_slugifies_title(self):
        """Converts title to safe slug"""
        assert _slug("OpenAI GPT-4o Launch!") == "openai-gpt-4o-launch"

    def test_truncates_long_slug(self):
        """Truncates to 60 chars"""
        long_title = "a" * 100
        slug = _slug(long_title)
        assert len(slug) == 60


class TestTitleHash:
    """Tests for title hashing"""

    def test_title_hash_is_consistent(self):
        """Same title produces same hash"""
        h1 = _title_hash("OpenAI launches new model")
        h2 = _title_hash("OpenAI launches new model")
        assert h1 == h2

    def test_title_hash_length_8(self):
        """Returns 8-character hash"""
        h = _title_hash("test")
        assert len(h) == 8
        assert all(c in "0123456789abcdef" for c in h)


class TestArchiveCargo:
    """Tests for article archiving"""

    def test_archive_cargo_creates_file(self):
        """Archiving a valid article creates a JSON file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            article = {
                "title": "Test Article",
                "date": "2024-03-15",
                "link": "https://example.com/test",
                "summary": "A test article",
                "text": "This is some test content that's long enough." * 10,
            }
            now = datetime(2024, 3, 15, 10, 30, 0, tzinfo=UTC)
            archive_cargo(article, "Test Source", tier=1, cache_dir=cache_dir, now=now)
            # Should find one file
            files = list(cache_dir.glob("*.json"))
            assert len(files) == 1
            # Check content
            data = json.loads(files[0].read_text())
            assert data["title"] == "Test Article"
            assert data["source"] == "Test Source"

    def test_archive_skips_non_tier1(self):
        """Doesn't archive non-tier 1 sources"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            article = {
                "title": "Test Article",
                "date": "2024-03-15",
                "link": "https://example.com/test",
            }
            archive_cargo(article, "Test Source", tier=2, cache_dir=cache_dir)
            files = list(cache_dir.glob("*.json"))
            assert len(files) == 0

    def test_archive_skips_no_link(self):
        """Skips articles without link"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            article = {
                "title": "Test Article",
                "date": "2024-03-15",
                "link": "",
            }
            archive_cargo(article, "Test Source", tier=1, cache_dir=cache_dir)
            files = list(cache_dir.glob("*.json"))
            assert len(files) == 0

    def test_archive_skips_too_short_text(self):
        """Skips when article has too little text after extraction"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            article = {
                "title": "Test Article",
                "date": "2024-03-15",
                "link": "https://example.com/test",
                "text": "short",  # less than 100 chars
            }
            archive_cargo(article, "Test Source", tier=1, cache_dir=cache_dir)
            files = list(cache_dir.glob("*.json"))
            assert len(files) == 0
