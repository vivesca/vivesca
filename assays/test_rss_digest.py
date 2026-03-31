from __future__ import annotations
"""Tests for digest.py"""


from datetime import UTC, datetime, timedelta
from pathlib import Path
import tempfile
import json

import pytest

from metabolon.organelles.endocytosis_rss.digest import (
    _resolve_month,
    _resolve_week_label,
    recall_archived_articles,
    _parse_theme_json,
    _build_items,
    _build_source_tags_map,
    _filter_by_tags,
    secrete_weekly_digest,
    _build_affinity_index,
    recall_archived_articles,
)


class TestResolveMonth:
    """Tests for month resolution"""

    def test_uses_provided_month(self):
        """Uses provided month when given"""
        assert _resolve_month("2024-03") == "2024-03"

    def test_defaults_to_current_month(self):
        """Defaults to current month"""
        result = _resolve_month(None)
        expected = datetime.now().astimezone().strftime("%Y-%m")
        assert result == expected


class TestResolveWeekLabel:
    """Tests for week window calculation"""

    def test_returns_correct_window(self):
        """Calculates 7-day window correctly"""
        anchor = datetime(2024, 3, 15, 10, 0, 0, tzinfo=UTC)
        start, end, label = _resolve_week_label(anchor)
        assert start == "2024-03-08"
        assert end == "2024-03-15"
        # Check week label format
        assert "2024-W" in label

    def test_defaults_to_now(self):
        """Works with default anchor"""
        start, end, label = _resolve_week_label(None)
        assert start < end


class TestRecallArchivedArticles:
    """Tests for recalling archived articles from cache"""

    def test_finds_month_files(self):
        """Finds all articles for a given month"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            # Create two articles for March 2024, one for April
            (cache_dir / "2024-03-source-abc123.json").write_text(
                json.dumps({"title": "March Article"}), encoding="utf-8"
            )
            (cache_dir / "2024-03-another-def456.json").write_text(
                json.dumps({"title": "Another March Article"}), encoding="utf-8"
            )
            (cache_dir / "2024-04-source-ghi789.json").write_text(
                json.dumps({"title": "April Article"}), encoding="utf-8"
            )
            result = recall_archived_articles(cache_dir, "2024-03")
            assert len(result) == 2
            titles = {item["title"] for item in result}
            assert "March Article" in titles
            assert "Another March Article" in titles

    def test_skips_bad_json(self):
        """Skips files with invalid JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            (cache_dir / "2024-03-bad.json").write_text("not valid json", encoding="utf-8")
            result = recall_archived_articles(cache_dir, "2024-03")
            assert len(result) == 0

    def test_returns_empty_when_dir_missing(self):
        """Missing directory returns empty list"""
        result = recall_archived_articles(Path("/does/not/exist"), "2024-03")
        assert result == []


class TestParseThemeJson:
    """Tests for LLM theme JSON parsing"""

    def test_parses_valid_json_array(self):
        """Parses clean JSON array"""
        raw = '''
        [
          {"theme": "AI Regulation", "description": "New rules", "article_indices": [0, 1]},
          {"theme": "Model Launches", "description": "New models", "article_indices": [2, 3]}
        ]
        '''
        result = _parse_theme_json(raw)
        assert len(result) == 2
        assert result[0]["theme"] == "AI Regulation"

    def test_extracts_json_from_prose(self):
        """Extracts JSON array surrounded by text"""
        raw = '''
        Sure, here's your analysis:

        [
          {"theme": "Test", "description": "Test theme", "article_indices": [0]}
        ]

        Let me know if you need anything else!
        '''
        result = _parse_theme_json(raw)
        assert len(result) == 1
        assert result[0]["theme"] == "Test"

    def test_strips_markdown_fences(self):
        """Strips ```json fences"""
        raw = '''```json
        [
          {"theme": "Test", "description": "Test", "article_indices": []}
        ]
        ```'''
        result = _parse_theme_json(raw)
        assert len(result) == 1
        assert result[0]["theme"] == "Test"

    def test_raises_value_error_on_bad_json(self):
        """Raises ValueError for non-JSON output"""
        with pytest.raises(ValueError):
            _parse_theme_json("No JSON here, just words")

    def test_raises_when_not_a_list(self):
        """Raises when result is not a list"""
        with pytest.raises(ValueError):
            _parse_theme_json('{"theme": "not a list"}')


class TestBuildItems:
    """Tests for prompt item building"""

    def test_formats_both_articles_and_log_entries(self):
        """Builds correctly numbered items"""
        articles = [
            {"date": "2024-03-15", "source": "Source1", "title": "Article 1", "summary": "Summary 1"},
            {"date": "2024-03-14", "source": "Source2", "title": "Article 2", "summary": "Summary 2"},
        ]
        log_entries = [
            {"date": "2024-03-13", "source": "Source3", "title": "Log 1", "summary": "Summary 3"},
        ]
        items = _build_items(articles, log_entries)
        assert len(items) == 3
        # Check that it contains all titles
        assert any("Article 1" in item for item in items)
        assert any("Article 2" in item for item in items)
        assert any("Log 1" in item for item in items)
        # Check numbering is continuous
        assert "[0]" in items[0]
        assert "[1]" in items[1]
        assert "[2]" in items[2]


class TestBuildSourceTagsMap:
    """Tests for source tags map building"""

    def test_builds_correct_map(self):
        """Correctly extracts tags from config sources"""
        from types import SimpleNamespace
        cfg = SimpleNamespace()
        cfg.sources = [
            {"name": "Source1", "tags": ["ai", "regulation"]},
            {"name": "Source2", "tags": "fintech"},  # single tag as string
            {"name": "Source3"},  # no tags
        ]
        result = _build_source_tags_map(cfg)
        assert result["Source1"] == ["ai", "regulation"]
        assert result["Source2"] == ["fintech"]
        assert result["Source3"] == ["ai"]  # default


class TestFilterByTags:
    """Tests for tag filtering"""

    def test_filters_correctly(self):
        """Keeps items where any requested tag matches source tags"""
        items = [
            {"title": "Regulation News", "source": "Source1"},
            {"title": "Fintech News", "source": "Source2"},
            {"title": "General AI", "source": "Source3"},
        ]
        source_tags = {
            "Source1": ["ai", "regulation"],
            "Source2": ["ai", "fintech"],
            "Source3": ["ai"],
        }
        result = _filter_by_tags(items, ["regulation"], source_tags)
        assert len(result) == 1
        assert result[0]["title"] == "Regulation News"

    def test_multiple_tags(self):
        """Matches any of the requested tags"""
        items = [
            {"title": "Regulation News", "source": "Source1"},
            {"title": "Fintech News", "source": "Source2"},
            {"title": "General AI", "source": "Source3"},
        ]
        source_tags = {
            "Source1": ["regulation"],
            "Source2": ["fintech"],
            "Source3": ["ai"],
        }
        result = _filter_by_tags(items, ["regulation", "fintech"], source_tags)
        assert len(result) == 2


class TestBuildAffinityIndex:
    """Tests for affinity lookup index"""

    def test_builds_index_by_title(self):
        """Creates dict mapping title to entry"""
        entries = [
            {"title": "Article 1", "score": 8},
            {"title": "Article 2", "score": 5},
            {"title": "Article 1", "score": 9},  # duplicate keeps first
            {"title": "", "score": 1},  # empty title skipped
        ]
        index = _build_affinity_index(entries)
        assert len(index) == 2
        assert index["Article 1"]["score"] == 8
        assert index["Article 2"]["score"] == 5
        assert "" not in index


class TestSecreteWeeklyDigest:
    """Tests for weekly digest markdown generation"""

    def test_writes_markdown_file(self):
        """Creates a valid markdown file with expected structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "weekly-test.md"
            entries = [
                {
                    "title": "Test Article",
                    "source": "Test Source",
                    "date": "2024-03-15",
                    "link": "https://example.com",
                    "banking_angle": "Regulatory change affecting banks",
                    "_transcytose": "1",
                },
                {
                    "title": "Another Article",
                    "source": "Another Source",
                    "date": "2024-03-14",
                    "link": "https://example.com/2",
                    "_transcytose": "0",
                },
            ]
            affinity_index = {
                "Test Article": {"score": 8, "banking_angle": "Regulatory change", "talking_point": "Ask clients about this"},
                "Another Article": {"score": 6, "banking_angle": "N/A", "talking_point": "N/A"},
            }
            result_path = secrete_weekly_digest(
                output_path=output_path,
                week_label="2024-W11",
                since_date="2024-03-08",
                until_date="2024-03-15",
                entries=entries,
                affinity_index=affinity_index,
            )
            assert result_path.exists()
            content = result_path.read_text()
            assert "# Weekly AI Digest" in content
            assert "2024-W11" in content
            assert "Transcytose" in content
            assert "Test Article" in content
            assert "By Source" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
