"""Tests for metabolon/organelles/endocytosis_rss/cargo.py"""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from metabolon.organelles.endocytosis_rss import cargo as rss_cargo


class TestAppendCargo:
    """Tests for append_cargo function."""

    def test_creates_file_if_not_exists(self, tmp_path: Path) -> None:
        cargo_path = tmp_path / "cargo.jsonl"
        articles = [{"title": "Test Article", "score": 5}]
        rss_cargo.append_cargo(cargo_path, articles)
        assert cargo_path.exists()

    def test_appends_to_existing_file(self, tmp_path: Path) -> None:
        cargo_path = tmp_path / "cargo.jsonl"
        cargo_path.write_text('{"title": "First"}\n', encoding="utf-8")
        articles = [{"title": "Second"}]
        rss_cargo.append_cargo(cargo_path, articles)
        lines = cargo_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2

    def test_writes_valid_jsonl(self, tmp_path: Path) -> None:
        cargo_path = tmp_path / "cargo.jsonl"
        articles = [
            {"title": "Article 1", "score": 5},
            {"title": "Article 2", "score": 7},
        ]
        rss_cargo.append_cargo(cargo_path, articles)
        for line in cargo_path.read_text(encoding="utf-8").strip().split("\n"):
            parsed = json.loads(line)
            assert isinstance(parsed, dict)

    def test_handles_unicode(self, tmp_path: Path) -> None:
        cargo_path = tmp_path / "cargo.jsonl"
        articles = [{"title": "中文标题", "summary": "日本語コンテンツ"}]
        rss_cargo.append_cargo(cargo_path, articles)
        content = cargo_path.read_text(encoding="utf-8")
        assert "中文标题" in content
        assert "日本語コンテンツ" in content

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        cargo_path = tmp_path / "subdir" / "cargo.jsonl"
        articles = [{"title": "Test"}]
        rss_cargo.append_cargo(cargo_path, articles)
        assert cargo_path.exists()


class TestRecallCargo:
    """Tests for recall_cargo function."""

    def test_nonexistent_file_returns_empty(self, tmp_path: Path) -> None:
        result = rss_cargo.recall_cargo(tmp_path / "nonexistent.jsonl")
        assert result == []

    def test_reads_all_entries(self, tmp_path: Path) -> None:
        cargo_path = tmp_path / "cargo.jsonl"
        cargo_path.write_text(
            '{"title": "A", "date": "2024-01-01"}\n{"title": "B", "date": "2024-01-02"}\n',
            encoding="utf-8",
        )
        result = rss_cargo.recall_cargo(cargo_path)
        assert len(result) == 2

    def test_filters_by_since_date(self, tmp_path: Path) -> None:
        cargo_path = tmp_path / "cargo.jsonl"
        cargo_path.write_text(
            '{"title": "A", "date": "2024-01-01"}\n{"title": "B", "date": "2024-01-15"}\n',
            encoding="utf-8",
        )
        result = rss_cargo.recall_cargo(cargo_path, since="2024-01-10")
        assert len(result) == 1
        assert result[0]["title"] == "B"

    def test_filters_by_month(self, tmp_path: Path) -> None:
        cargo_path = tmp_path / "cargo.jsonl"
        cargo_path.write_text(
            '{"title": "A", "date": "2024-01-15"}\n{"title": "B", "date": "2024-02-15"}\n',
            encoding="utf-8",
        )
        result = rss_cargo.recall_cargo(cargo_path, month="2024-02")
        assert len(result) == 1
        assert result[0]["title"] == "B"

    def test_skips_invalid_json(self, tmp_path: Path) -> None:
        cargo_path = tmp_path / "cargo.jsonl"
        cargo_path.write_text(
            '{"title": "Valid"}\ninvalid json\n{"title": "Also Valid"}\n',
            encoding="utf-8",
        )
        result = rss_cargo.recall_cargo(cargo_path)
        assert len(result) == 2

    def test_skips_non_dict_entries(self, tmp_path: Path) -> None:
        cargo_path = tmp_path / "cargo.jsonl"
        cargo_path.write_text(
            '{"title": "Valid"}\n["list", "not", "dict"]\n{"title": "Also Valid"}\n',
            encoding="utf-8",
        )
        result = rss_cargo.recall_cargo(cargo_path)
        assert len(result) == 2

    def test_skips_empty_lines(self, tmp_path: Path) -> None:
        cargo_path = tmp_path / "cargo.jsonl"
        cargo_path.write_text(
            '{"title": "A"}\n\n{"title": "B"}\n   \n',
            encoding="utf-8",
        )
        result = rss_cargo.recall_cargo(cargo_path)
        assert len(result) == 2


class TestRecallTitlePrefixes:
    """Tests for recall_title_prefixes function."""

    def test_nonexistent_file_returns_empty(self, tmp_path: Path) -> None:
        result = rss_cargo.recall_title_prefixes(tmp_path / "nonexistent.jsonl")
        assert result == set()

    def test_extracts_prefixes(self, tmp_path: Path) -> None:
        cargo_path = tmp_path / "cargo.jsonl"
        cargo_path.write_text(
            '{"title": "AI Breakthrough in Banking"}\n',
            encoding="utf-8",
        )
        result = rss_cargo.recall_title_prefixes(cargo_path)
        assert isinstance(result, set)
        assert len(result) >= 1

    def test_normalizes_titles(self, tmp_path: Path) -> None:
        cargo_path = tmp_path / "cargo.jsonl"
        cargo_path.write_text(
            '{"title": "BREAKING: Major News Story!"}\n',
            encoding="utf-8",
        )
        result = rss_cargo.recall_title_prefixes(cargo_path)
        # Should be lowercase and stripped of punctuation
        for prefix in result:
            assert prefix == prefix.lower()


class TestTitlePrefix:
    """Tests for _title_prefix helper."""

    def test_normalizes_case(self) -> None:
        result = rss_cargo._title_prefix("HELLO World")
        assert result == "hello world"

    def test_removes_short_words(self) -> None:
        result = rss_cargo._title_prefix("A Big Test Article Here")
        # Words with len > 2 are kept
        words = result.split()
        for word in words:
            assert len(word) > 2

    def test_limits_to_six_words(self) -> None:
        result = rss_cargo._title_prefix(
            "One Two Three Four Five Six Seven Eight Nine Ten"
        )
        assert len(result.split()) <= 6

    def test_removes_punctuation(self) -> None:
        result = rss_cargo._title_prefix("Hello! World? Test.")
        assert "!" not in result
        assert "?" not in result
        assert "." not in result

    def test_empty_title_returns_empty(self) -> None:
        result = rss_cargo._title_prefix("")
        assert result == ""


class TestRotateCargo:
    """Tests for rotate_cargo function."""

    def test_no_rotation_if_file_not_exists(self, tmp_path: Path) -> None:
        # Should not raise
        rss_cargo.rotate_cargo(
            tmp_path / "nonexistent.jsonl",
            tmp_path / "archive",
        )

    def test_no_rotation_if_all_recent(self, tmp_path: Path) -> None:
        cargo_path = tmp_path / "cargo.jsonl"
        now = datetime(2024, 3, 15, tzinfo=UTC)
        recent_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        cargo_path.write_text(
            f'{{"title": "Recent", "date": "{recent_date}"}}\n',
            encoding="utf-8",
        )
        rss_cargo.rotate_cargo(cargo_path, tmp_path / "archive", retain_days=14, now=now)
        # File should remain unchanged
        assert len(rss_cargo.recall_cargo(cargo_path)) == 1

    def test_rotates_old_entries(self, tmp_path: Path) -> None:
        cargo_path = tmp_path / "cargo.jsonl"
        archive_dir = tmp_path / "archive"
        now = datetime(2024, 3, 15, tzinfo=UTC)
        old_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        recent_date = (now - timedelta(days=5)).strftime("%Y-%m-%d")

        cargo_path.write_text(
            f'{{"title": "Old", "date": "{old_date}"}}\n'
            f'{{"title": "Recent", "date": "{recent_date}"}}\n',
            encoding="utf-8",
        )
        rss_cargo.rotate_cargo(
            cargo_path, archive_dir, retain_days=14, now=now
        )

        # Old entry should be in archive
        recent = rss_cargo.recall_cargo(cargo_path)
        assert len(recent) == 1
        assert recent[0]["title"] == "Recent"

        # Check archive
        archive_files = list(archive_dir.glob("cargo-*.jsonl"))
        assert len(archive_files) == 1

    def test_creates_monthly_archive_buckets(self, tmp_path: Path) -> None:
        cargo_path = tmp_path / "cargo.jsonl"
        archive_dir = tmp_path / "archive"
        now = datetime(2024, 3, 15, tzinfo=UTC)

        cargo_path.write_text(
            '{"title": "Jan", "date": "2024-01-15"}\n'
            '{"title": "Feb", "date": "2024-02-15"}\n',
            encoding="utf-8",
        )
        rss_cargo.rotate_cargo(
            cargo_path, archive_dir, retain_days=14, now=now
        )

        # Should have two archive files
        archive_files = sorted(archive_dir.glob("cargo-*.jsonl"))
        assert len(archive_files) == 2
        assert "2024-01" in str(archive_files[0])
        assert "2024-02" in str(archive_files[1])


class TestAtomicWriteLines:
    """Tests for _atomic_write_lines helper."""

    def test_writes_lines_to_file(self, tmp_path: Path) -> None:
        path = tmp_path / "test.jsonl"
        lines = ['{"a": 1}', '{"b": 2}']
        rss_cargo._atomic_write_lines(path, lines)
        content = path.read_text(encoding="utf-8")
        assert content == '{"a": 1}\n{"b": 2}\n'

    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        path = tmp_path / "subdir" / "test.jsonl"
        lines = ['{"test": true}']
        rss_cargo._atomic_write_lines(path, lines)
        assert path.exists()

    def test_handles_empty_lines(self, tmp_path: Path) -> None:
        path = tmp_path / "test.jsonl"
        rss_cargo._atomic_write_lines(path, [])
        assert path.exists()
        assert path.read_text(encoding="utf-8") == ""
