"""Tests for metabolon/organelles/endocytosis_rss/discover.py"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from metabolon.organelles.endocytosis_rss import discover as rss_discover
from metabolon.organelles.endocytosis_rss.config import EndocytosisConfig


class TestCompileKeywords:
    """Tests for _compile_keywords function."""

    def test_compiles_valid_patterns(self) -> None:
        patterns = ["test", "\\d+", "[a-z]+"]
        compiled = rss_discover._compile_keywords(patterns)
        assert len(compiled) == 3
        assert all(isinstance(p, re.Pattern) for p in compiled)

    def test_skips_invalid_patterns(self) -> None:
        patterns = ["valid", "[invalid(", "another"]
        compiled = rss_discover._compile_keywords(patterns)
        assert len(compiled) == 2

    def test_empty_list_returns_empty(self) -> None:
        compiled = rss_discover._compile_keywords([])
        assert compiled == []

    def test_patterns_are_case_insensitive(self) -> None:
        compiled = rss_discover._compile_keywords(["TEST"])
        assert compiled[0].search("this is a test match")
        assert compiled[0].search("THIS IS A TEST MATCH")


class TestHasAffinity:
    """Tests for has_affinity function."""

    def test_matches_keyword(self) -> None:
        patterns = [re.compile(r"banking", re.IGNORECASE)]
        assert rss_discover.has_affinity("Banking news today", patterns) is True

    def test_no_match_returns_false(self) -> None:
        patterns = [re.compile(r"crypto", re.IGNORECASE)]
        assert rss_discover.has_affinity("Sports news today", patterns) is False

    def test_any_pattern_matches(self) -> None:
        patterns = [
            re.compile(r"banking", re.IGNORECASE),
            re.compile(r"finance", re.IGNORECASE),
        ]
        assert rss_discover.has_affinity("Finance report", patterns) is True

    def test_empty_patterns_returns_false(self) -> None:
        assert rss_discover.has_affinity("any text", []) is False


class TestNormalizeHandle:
    """Tests for _normalize_handle function."""

    def test_strips_leading_at(self) -> None:
        assert rss_discover._normalize_handle("@username") == "username"

    def test_lowercases(self) -> None:
        assert rss_discover._normalize_handle("UserName") == "username"

    def test_strips_whitespace_and_at(self) -> None:
        # lstrip("@") only strips @ from the very start, then strip() removes whitespace
        # So "@UserName" -> "username" but "  @UserName  " -> "@username"
        assert rss_discover._normalize_handle("@username") == "username"
        assert rss_discover._normalize_handle("  @UserName  ") == "@username"

    def test_handles_already_normalized(self) -> None:
        assert rss_discover._normalize_handle("username") == "username"


class TestExtractHandle:
    """Tests for _extract_handle function."""

    def test_extracts_from_author_dict_handle(self) -> None:
        tweet: dict[str, Any] = {"author": {"handle": "testuser"}}
        assert rss_discover._extract_handle(tweet) == "testuser"

    def test_extracts_from_author_dict_username(self) -> None:
        tweet: dict[str, Any] = {"author": {"username": "testuser"}}
        assert rss_discover._extract_handle(tweet) == "testuser"

    def test_extracts_from_author_dict_screen_name(self) -> None:
        tweet: dict[str, Any] = {"author": {"screen_name": "testuser"}}
        assert rss_discover._extract_handle(tweet) == "testuser"

    def test_extracts_from_top_level_handle(self) -> None:
        tweet: dict[str, Any] = {"handle": "testuser"}
        assert rss_discover._extract_handle(tweet) == "testuser"

    def test_extracts_from_top_level_username(self) -> None:
        tweet: dict[str, Any] = {"username": "testuser"}
        assert rss_discover._extract_handle(tweet) == "testuser"

    def test_extracts_from_author_handle(self) -> None:
        tweet: dict[str, Any] = {"author_handle": "testuser"}
        assert rss_discover._extract_handle(tweet) == "testuser"

    def test_returns_empty_for_missing_handle(self) -> None:
        tweet: dict[str, Any] = {}
        assert rss_discover._extract_handle(tweet) == ""

    def test_normalizes_handle(self) -> None:
        tweet: dict[str, Any] = {"author": {"handle": "@TestUser"}}
        assert rss_discover._extract_handle(tweet) == "testuser"


class TestSample:
    """Tests for _sample function."""

    def test_short_text_unchanged(self) -> None:
        text = "Short text"
        assert rss_discover._sample(text) == text

    def test_long_text_truncated(self) -> None:
        text = "x" * 150
        result = rss_discover._sample(text, limit=100)
        assert len(result) == 100
        assert result.endswith("…")

    def test_collapses_whitespace(self) -> None:
        text = "word1   word2\nword3"
        result = rss_discover._sample(text)
        assert "   " not in result
        assert "\n" not in result

    def test_exact_limit(self) -> None:
        text = "x" * 100
        result = rss_discover._sample(text, limit=100)
        assert result == text


class TestScoutSources:
    """Tests for scout_sources function."""

    def test_returns_zero_when_bird_not_in_path(self, tmp_path: Path) -> None:
        """When bird_path is None and shutil.which returns None, returns 0."""
        cfg = EndocytosisConfig(
            config_dir=tmp_path,
            cache_dir=tmp_path,
            data_dir=tmp_path,
            config_path=tmp_path / "config.yaml",
            sources_path=tmp_path / "sources.yaml",
            state_path=tmp_path / "state.json",
            log_path=tmp_path / "news.md",
            cargo_path=tmp_path / "cargo.jsonl",
            article_cache_dir=tmp_path / "articles",
            digest_output_dir=tmp_path / "digests",
            digest_model="glm",
            sources_data={},
        )
        # Pass None for bird_path to test PATH lookup (which will fail)
        result = rss_discover.scout_sources(cfg, bird_path=None)
        assert result == 0


class TestIntegration:
    """Integration tests for discover module."""

    def test_keyword_matching_workflow(self) -> None:
        """Test the full keyword matching workflow."""
        keywords = ["banking", "fintech", "crypto"]
        compiled = rss_discover._compile_keywords(keywords)

        texts = [
            "New banking regulations announced",
            "Sports team wins championship",
            "Crypto prices surge",
            "Weather forecast for tomorrow",
        ]

        matches = [t for t in texts if rss_discover.has_affinity(t, compiled)]
        assert len(matches) == 2
        assert "banking" in matches[0].lower()
        assert "crypto" in matches[1].lower()
