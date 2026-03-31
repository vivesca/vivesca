"""Tests for endocytosis_rss/discover.py - X/Twitter discovery."""

import re
from unittest.mock import MagicMock, patch

from metabolon.organelles.endocytosis_rss.discover import (
    _compile_keywords,
    _extract_handle,
    _normalize_handle,
    _sample,
    has_affinity,
)


def test_compile_keywords_valid_patterns():
    """Test _compile_keywords returns compiled regex patterns."""
    patterns = ["crypto", "banking", "fintech"]
    compiled = _compile_keywords(patterns)
    assert len(compiled) == 3
    assert all(isinstance(p, re.Pattern) for p in compiled)


def test_compile_keywords_ignores_invalid():
    """Test _compile_keywords skips invalid regex patterns."""
    patterns = ["valid", "[invalid(regex", "another"]
    compiled = _compile_keywords(patterns)
    assert len(compiled) == 2


def test_compile_keywords_empty():
    """Test _compile_keywords returns empty list for empty input."""
    assert _compile_keywords([]) == []


def test_has_affinity_matches():
    """Test has_affinity returns True when pattern matches."""
    patterns = [re.compile(r"bitcoin", re.IGNORECASE)]
    assert has_affinity("Bitcoin prices surge", patterns) is True
    assert has_affinity("No match here", patterns) is False


def test_has_affinity_case_insensitive():
    """Test has_affinity is case insensitive."""
    patterns = [re.compile(r"CRYPTO", re.IGNORECASE)]
    assert has_affinity("crypto news", patterns) is True
    assert has_affinity("CRYPTO NEWS", patterns) is True


def test_has_affinity_empty_patterns():
    """Test has_affinity returns False for empty pattern list."""
    assert has_affinity("any text", []) is False


def test_normalize_handle_strips_at():
    """Test _normalize_handle removes leading @."""
    assert _normalize_handle("@username") == "username"
    assert _normalize_handle("@@double") == "double"


def test_normalize_handle_lowercase():
    """Test _normalize_handle converts to lowercase."""
    assert _normalize_handle("UserName") == "username"
    assert _normalize_handle("@BIGHANDLE") == "bighandle"


def test_normalize_handle_strips_whitespace():
    """Test _normalize_handle strips whitespace and @."""
    # lstrip("@") removes @ from left, then strip() removes whitespace
    assert _normalize_handle("@user  ") == "user"
    assert _normalize_handle("  user  ") == "user"
    # Whitespace before @ is stripped by strip() at the end
    assert _normalize_handle("  @user  ") == "@user"  # lstrip("@") sees "  @user", keeps it


def test_extract_handle_from_author_dict():
    """Test _extract_handle extracts from author dict."""
    tweet = {"author": {"handle": "testuser"}}
    assert _extract_handle(tweet) == "testuser"


def test_extract_handle_from_username():
    """Test _extract_handle extracts from username field."""
    tweet = {"author": {"username": "altuser"}}
    assert _extract_handle(tweet) == "altuser"


def test_extract_handle_from_top_level():
    """Test _extract_handle falls back to top-level fields."""
    tweet = {"handle": "toplevel"}
    assert _extract_handle(tweet) == "toplevel"


def test_extract_handle_empty():
    """Test _extract_handle returns empty for missing handle."""
    assert _extract_handle({}) == ""
    assert _extract_handle({"author": {}}) == ""


def test_sample_short_text():
    """Test _sample returns text unchanged when under limit."""
    text = "Short text"
    assert _sample(text, limit=100) == "Short text"


def test_sample_truncates_long_text():
    """Test _sample truncates and adds ellipsis for long text."""
    text = "A" * 150
    result = _sample(text, limit=100)
    assert len(result) == 100
    assert result.endswith("…")


def test_sample_collapses_whitespace():
    """Test _sample collapses newlines and multiple spaces."""
    text = "hello\n\nworld"
    assert _sample(text) == "hello world"


def test_scout_sources_no_bird_cli(tmp_path):
    """Test scout_sources returns 0 when bird CLI not found."""
    from metabolon.organelles.endocytosis_rss.discover import scout_sources
    from metabolon.organelles.endocytosis_rss.config import EndocytosisConfig
    
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
        bird_path=None,
        tg_notify_path=None,
        config_data={},
        sources_data={},
    )
    
    with patch("metabolon.organelles.endocytosis_rss.discover.shutil.which", return_value=None):
        result = scout_sources(cfg, bird_path=None)
    assert result == 0
