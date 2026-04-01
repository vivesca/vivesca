"""Tests for metabolon/organelles/endocytosis_rss/discover.py — X Discovery."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.endocytosis_rss.config import EndocytosisConfig
from metabolon.organelles.endocytosis_rss.discover import (
    _compile_keywords,
    _extract_handle,
    _normalize_handle,
    _sample,
    has_affinity,
    scout_sources,
)


def _make_cfg(tmp_path: Path, **overrides) -> EndocytosisConfig:
    defaults = dict(
        config_dir=tmp_path,
        cache_dir=tmp_path,
        data_dir=tmp_path,
        config_path=tmp_path / "c.yaml",
        sources_path=tmp_path / "s.yaml",
        state_path=tmp_path / "state.json",
        log_path=tmp_path / "log.md",
        cargo_path=tmp_path / "cargo.jsonl",
        article_cache_dir=tmp_path / "cache",
        digest_output_dir=tmp_path / "digest",
        digest_model="gpt-4o-mini",
        config_data={},
        sources_data={},
    )
    defaults.update(overrides)
    return EndocytosisConfig(**defaults)


# ---------------------------------------------------------------------------
# _compile_keywords
# ---------------------------------------------------------------------------

class TestCompileKeywords:
    def test_valid_pattern(self):
        result = _compile_keywords([r"banking", r"finance"])
        assert len(result) == 2

    def test_invalid_pattern_skipped(self):
        result = _compile_keywords([r"valid", r"[invalid"])
        assert len(result) == 1

    def test_empty(self):
        assert _compile_keywords([]) == []


# ---------------------------------------------------------------------------
# has_affinity
# ---------------------------------------------------------------------------

class TestHasAffinity:
    def test_match(self):
        import re
        compiled = [re.compile(r"banking", re.IGNORECASE)]
        assert has_affinity("Banking sector news", compiled) is True

    def test_no_match(self):
        import re
        compiled = [re.compile(r"quantum", re.IGNORECASE)]
        assert has_affinity("Banking sector news", compiled) is False

    def test_empty_compiled(self):
        assert has_affinity("anything", []) is False


# ---------------------------------------------------------------------------
# _normalize_handle
# ---------------------------------------------------------------------------

class TestNormalizeHandle:
    def test_strips_at(self):
        assert _normalize_handle("@user") == "user"

    def test_lowercase(self):
        assert _normalize_handle("USER") == "user"

    def test_strips_whitespace(self):
        assert _normalize_handle("  @User  ") == "user"


# ---------------------------------------------------------------------------
# _extract_handle
# ---------------------------------------------------------------------------

class TestExtractHandle:
    def test_from_author_dict(self):
        tweet = {"author": {"handle": "TestUser"}}
        assert _extract_handle(tweet) == "testuser"

    def test_from_username(self):
        tweet = {"author": {"username": "TestUser"}}
        assert _extract_handle(tweet) == "testuser"

    def test_from_top_level(self):
        tweet = {"author_handle": "TestUser"}
        assert _extract_handle(tweet) == "testuser"

    def test_empty_when_missing(self):
        assert _extract_handle({}) == ""

    def test_empty_when_empty_string(self):
        assert _extract_handle({"author": {"handle": "  "}}) == ""


# ---------------------------------------------------------------------------
# _sample
# ---------------------------------------------------------------------------

class TestSample:
    def test_short_text(self):
        assert _sample("hello") == "hello"

    def test_truncates_long_text(self):
        long = "word " * 50
        result = _sample(long, limit=50)
        assert len(result) <= 51  # limit + ellipsis char
        assert result.endswith("…")

    def test_collapses_whitespace(self):
        assert _sample("a  b\n\nc") == "a b c"


# ---------------------------------------------------------------------------
# scout_sources
# ---------------------------------------------------------------------------

class TestScoutSources:
    def test_no_bird_cli(self, tmp_path):
        cfg = _make_cfg(tmp_path)
        with patch("metabolon.organelles.endocytosis_rss.discover.shutil.which", return_value=None):
            result = scout_sources(cfg)
        assert result == 0

    def test_timeout(self, tmp_path):
        cfg = _make_cfg(tmp_path)
        with patch("metabolon.organelles.endocytosis_rss.discover.shutil.which", return_value="bird"), \
             patch("metabolon.organelles.endocytosis_rss.discover.subprocess.run", side_effect=subprocess.TimeoutExpired("bird", 45)):
            result = scout_sources(cfg)
        assert result == 1

    def test_bird_failure(self, tmp_path):
        cfg = _make_cfg(tmp_path)
        mock_proc = MagicMock(returncode=1, stderr="error")
        with patch("metabolon.organelles.endocytosis_rss.discover.shutil.which", return_value="bird"), \
             patch("metabolon.organelles.endocytosis_rss.discover.subprocess.run", return_value=mock_proc):
            result = scout_sources(cfg)
        assert result == 1

    def test_invalid_json(self, tmp_path):
        cfg = _make_cfg(tmp_path)
        mock_proc = MagicMock(returncode=0, stdout="not json", stderr="")
        with patch("metabolon.organelles.endocytosis_rss.discover.shutil.which", return_value="bird"), \
             patch("metabolon.organelles.endocytosis_rss.discover.subprocess.run", return_value=mock_proc):
            result = scout_sources(cfg)
        assert result == 1

    def test_non_list_json(self, tmp_path):
        cfg = _make_cfg(tmp_path)
        mock_proc = MagicMock(returncode=0, stdout='{"key": "value"}', stderr="")
        with patch("metabolon.organelles.endocytosis_rss.discover.shutil.which", return_value="bird"), \
             patch("metabolon.organelles.endocytosis_rss.discover.subprocess.run", return_value=mock_proc):
            result = scout_sources(cfg)
        assert result == 1

    def test_successful_scan_no_matches(self, tmp_path):
        cfg = _make_cfg(tmp_path, sources_data={"x_discovery": {"keywords": ["banking"]}})
        tweets = [{"text": "random sports tweet", "author": {"handle": "sportsfan"}}]
        mock_proc = MagicMock(returncode=0, stdout=json.dumps(tweets), stderr="")
        with patch("metabolon.organelles.endocytosis_rss.discover.shutil.which", return_value="bird"), \
             patch("metabolon.organelles.endocytosis_rss.discover.subprocess.run", return_value=mock_proc), \
             patch("metabolon.organelles.endocytosis_rss.discover.record_cargo"), \
             patch("metabolon.organelles.endocytosis_rss.discover.append_cargo"):
            result = scout_sources(cfg)
        assert result == 0

    def test_successful_scan_with_matches(self, tmp_path):
        cfg = _make_cfg(tmp_path, sources_data={
            "x_discovery": {"keywords": ["banking"]},
            "x_accounts": [],
        })
        tweets = [
            {"text": "banking sector update", "author": {"handle": "newuser"}},
            {"text": "sports score", "author": {"handle": "sportsfan"}},
        ]
        mock_proc = MagicMock(returncode=0, stdout=json.dumps(tweets), stderr="")
        with patch("metabolon.organelles.endocytosis_rss.discover.shutil.which", return_value="bird"), \
             patch("metabolon.organelles.endocytosis_rss.discover.subprocess.run", return_value=mock_proc), \
             patch("metabolon.organelles.endocytosis_rss.discover.record_cargo"), \
             patch("metabolon.organelles.endocytosis_rss.discover.append_cargo"):
            result = scout_sources(cfg)
        assert result == 0

    def test_no_keywords(self, tmp_path):
        cfg = _make_cfg(tmp_path, sources_data={"x_discovery": {}})
        tweets = [{"text": "anything", "author": {"handle": "user"}}]
        mock_proc = MagicMock(returncode=0, stdout=json.dumps(tweets), stderr="")
        with patch("metabolon.organelles.endocytosis_rss.discover.shutil.which", return_value="bird"), \
             patch("metabolon.organelles.endocytosis_rss.discover.subprocess.run", return_value=mock_proc):
            result = scout_sources(cfg)
        assert result == 0
