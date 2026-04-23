from pathlib import Path

import pytest

from epsin.extractors.generic import GenericExtractor, _is_safe_url, _parse_datetime
from epsin.models import Source


RSS_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Test Feed</title>
  <entry>
    <title>First Post</title>
    <link href="https://example.com/first" rel="alternate"/>
    <published>2026-04-10T10:00:00Z</published>
    <summary>This is the first post summary.</summary>
  </entry>
  <entry>
    <title>Second Post</title>
    <link href="https://example.com/second" rel="alternate"/>
    <published>2026-04-07T08:00:00Z</published>
    <summary>Second post content here.</summary>
  </entry>
</feed>
"""


def test_is_safe_url_blocks_private():
    assert not _is_safe_url("http://192.168.1.1/test")
    assert not _is_safe_url("http://10.0.0.1/test")
    assert not _is_safe_url("http://127.0.0.1/test")


def test_is_safe_url_allows_public():
    assert _is_safe_url("https://simonwillison.net/atom/everything/")
    assert _is_safe_url("https://example.com/feed")


def test_is_safe_url_blocks_non_http():
    assert not _is_safe_url("ftp://example.com/file")
    assert not _is_safe_url("javascript:alert(1)")


class TestGenericExtractorOffline:
    def test_fetch_rss_from_fixture(self):
        import feedparser
        from epsin.models import Item

        source = Source(name="Test Feed", url="https://example.com/", rss="https://example.com/feed", tags=["test"])
        feed = feedparser.parse(RSS_FIXTURE)
        # Verify fixture parses correctly
        assert len(feed.entries) == 2
        assert feed.entries[0].title == "First Post"

    def test_generic_extractor_no_rss_returns_empty(self):
        source = Source(name="No RSS", url="http://127.0.0.1/", tags=["test"])
        extractor = GenericExtractor()
        # _is_safe_url blocks 127.0.0.1
        items = extractor.fetch(source)
        assert items == []

    def test_parse_datetime_struct_time(self):
        import calendar
        from datetime import UTC, datetime

        class FakeEntry:
            published_parsed = datetime(2026, 4, 10, 10, 0, tzinfo=UTC).timetuple()

        result = _parse_datetime(FakeEntry())
        assert "2026" in result
        assert "04" in result


@pytest.fixture
def fixture_path(tmp_path: Path) -> Path:
    rss_file = tmp_path / "feed.xml"
    rss_file.write_text(RSS_FIXTURE)
    return rss_file
