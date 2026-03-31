"""Tests for metabolon/organelles/endocytosis_rss/migration.py"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from metabolon.organelles.endocytosis_rss import cargo as rss_cargo
from metabolon.organelles.endocytosis_rss import migration as rss_migration


class TestMigrateMarkdownToJsonl:
    """Tests for migrate_markdown_to_jsonl function."""

    def test_nonexistent_file_returns_zero(self, tmp_path: Path) -> None:
        md_path = tmp_path / "nonexistent.md"
        cargo_path = tmp_path / "cargo.jsonl"
        result = rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)
        assert result == 0

    def test_empty_file_returns_zero(self, tmp_path: Path) -> None:
        md_path = tmp_path / "empty.md"
        md_path.write_text("", encoding="utf-8")
        cargo_path = tmp_path / "cargo.jsonl"
        result = rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)
        assert result == 0

    def test_migrates_date_header(self, tmp_path: Path) -> None:
        md_path = tmp_path / "news.md"
        cargo_path = tmp_path / "cargo.jsonl"
        md_path.write_text("## 2024-01-15\n", encoding="utf-8")

        result = rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)
        assert result == 0  # No articles, just date header

    def test_migrates_source_header(self, tmp_path: Path) -> None:
        md_path = tmp_path / "news.md"
        cargo_path = tmp_path / "cargo.jsonl"
        md_path.write_text("## 2024-01-15\n### TechNews\n", encoding="utf-8")

        result = rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)
        assert result == 0  # No articles, just headers

    def test_migrates_simple_article(self, tmp_path: Path) -> None:
        md_path = tmp_path / "news.md"
        cargo_path = tmp_path / "cargo.jsonl"
        content = """## 2024-01-15
### TechNews
- **[Test Article](https://example.com)**
"""
        md_path.write_text(content, encoding="utf-8")

        result = rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)
        assert result == 1

        # Verify cargo content
        entries = rss_cargo.recall_cargo(cargo_path)
        assert len(entries) == 1
        assert entries[0]["title"] == "Test Article"
        assert entries[0]["source"] == "TechNews"
        assert entries[0]["link"] == "https://example.com"

    def test_migrates_starred_article(self, tmp_path: Path) -> None:
        md_path = tmp_path / "news.md"
        cargo_path = tmp_path / "cargo.jsonl"
        content = """## 2024-01-15
### TechNews
- [★] **[Important Article](https://example.com)**
"""
        md_path.write_text(content, encoding="utf-8")

        result = rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)
        assert result == 1

        entries = rss_cargo.recall_cargo(cargo_path)
        assert entries[0]["score"] == 7  # Starred articles get score 7
        assert entries[0]["fate"] == "transcytose"

    def test_migrates_unstarred_article(self, tmp_path: Path) -> None:
        md_path = tmp_path / "news.md"
        cargo_path = tmp_path / "cargo.jsonl"
        content = """## 2024-01-15
### TechNews
- **[Regular Article](https://example.com)**
"""
        md_path.write_text(content, encoding="utf-8")

        result = rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)
        entries = rss_cargo.recall_cargo(cargo_path)
        assert entries[0]["score"] == 5  # Unstarred articles get score 5
        assert entries[0]["fate"] == "store"

    def test_migrates_article_with_date(self, tmp_path: Path) -> None:
        md_path = tmp_path / "news.md"
        cargo_path = tmp_path / "cargo.jsonl"
        content = """## 2024-01-15
### TechNews
- **[Article](https://example.com)** (2024-01-10)
"""
        md_path.write_text(content, encoding="utf-8")

        result = rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)
        entries = rss_cargo.recall_cargo(cargo_path)
        assert entries[0]["date"] == "2024-01-10"

    def test_migrates_article_with_summary(self, tmp_path: Path) -> None:
        md_path = tmp_path / "news.md"
        cargo_path = tmp_path / "cargo.jsonl"
        content = """## 2024-01-15
### TechNews
- **[Article](https://example.com)** — This is a summary.
"""
        md_path.write_text(content, encoding="utf-8")

        result = rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)
        entries = rss_cargo.recall_cargo(cargo_path)
        assert entries[0]["summary"] == "This is a summary."

    def test_migrates_article_with_banking_angle(self, tmp_path: Path) -> None:
        md_path = tmp_path / "news.md"
        cargo_path = tmp_path / "cargo.jsonl"
        content = """## 2024-01-15
### TechNews
- **[Article](https://example.com)** (banking_angle: High relevance)
"""
        md_path.write_text(content, encoding="utf-8")

        result = rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)
        entries = rss_cargo.recall_cargo(cargo_path)
        assert entries[0]["banking_angle"] == "High relevance"

    def test_migrates_multiple_articles(self, tmp_path: Path) -> None:
        md_path = tmp_path / "news.md"
        cargo_path = tmp_path / "cargo.jsonl"
        content = """## 2024-01-15
### TechNews
- **[Article One](https://example.com/1)**
- **[Article Two](https://example.com/2)**

### FinNews
- **[Article Three](https://example.com/3)**
"""
        md_path.write_text(content, encoding="utf-8")

        result = rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)
        assert result == 3

        entries = rss_cargo.recall_cargo(cargo_path)
        assert len(entries) == 3
        sources = {e["source"] for e in entries}
        assert sources == {"TechNews", "FinNews"}

    def test_migrates_multiple_dates(self, tmp_path: Path) -> None:
        md_path = tmp_path / "news.md"
        cargo_path = tmp_path / "cargo.jsonl"
        content = """## 2024-01-10
### News
- **[Old Article](https://example.com/old)**

## 2024-01-15
### News
- **[New Article](https://example.com/new)**
"""
        md_path.write_text(content, encoding="utf-8")

        result = rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)
        assert result == 2

        entries = rss_cargo.recall_cargo(cargo_path)
        dates = [e["date"] for e in entries]
        assert "2024-01-10" in dates
        assert "2024-01-15" in dates

    def test_article_without_link(self, tmp_path: Path) -> None:
        md_path = tmp_path / "news.md"
        cargo_path = tmp_path / "cargo.jsonl"
        content = """## 2024-01-15
### News
- **Plain Title Article**
"""
        md_path.write_text(content, encoding="utf-8")

        result = rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)
        assert result == 1

        entries = rss_cargo.recall_cargo(cargo_path)
        assert entries[0]["title"] == "Plain Title Article"
        assert entries[0]["link"] == ""

    def test_sets_default_fields(self, tmp_path: Path) -> None:
        md_path = tmp_path / "news.md"
        cargo_path = tmp_path / "cargo.jsonl"
        content = """## 2024-01-15
### News
- **[Article](https://example.com)**
"""
        md_path.write_text(content, encoding="utf-8")

        rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)
        entries = rss_cargo.recall_cargo(cargo_path)

        entry = entries[0]
        assert "timestamp" in entry
        assert entry["banking_angle"] == "N/A"
        assert entry["talking_point"] == "N/A"

    def test_skips_empty_title(self, tmp_path: Path) -> None:
        md_path = tmp_path / "news.md"
        cargo_path = tmp_path / "cargo.jsonl"
        content = """## 2024-01-15
### News
- **[]()**
- **[Valid Article](https://example.com)**
"""
        md_path.write_text(content, encoding="utf-8")

        result = rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)
        # Empty titles should be skipped
        assert result == 1


class TestMigrationIntegration:
    """Integration tests for migration with cargo module."""

    def test_migrated_data_readable_by_cargo(self, tmp_path: Path) -> None:
        md_path = tmp_path / "news.md"
        cargo_path = tmp_path / "cargo.jsonl"
        content = """## 2024-01-15
### TechNews
- [★] **[Important](https://example.com/1)** (banking_angle: Critical) — Summary here
- **[Normal](https://example.com/2)** — Regular summary

### FinNews
- **[Finance Article](https://example.com/3)**
"""
        md_path.write_text(content, encoding="utf-8")

        result = rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)
        assert result == 3

        # Test recall_cargo works with migrated data
        all_entries = rss_cargo.recall_cargo(cargo_path)
        assert len(all_entries) == 3

        # Test filtering by date
        jan_entries = rss_cargo.recall_cargo(cargo_path, month="2024-01")
        assert len(jan_entries) == 3

        # Test title prefix extraction
        prefixes = rss_cargo.recall_title_prefixes(cargo_path)
        assert isinstance(prefixes, set)

    def test_idempotent_migration(self, tmp_path: Path) -> None:
        """Running migration twice should append duplicates (caller's responsibility to handle)."""
        md_path = tmp_path / "news.md"
        cargo_path = tmp_path / "cargo.jsonl"
        content = """## 2024-01-15
### News
- **[Article](https://example.com)**
"""
        md_path.write_text(content, encoding="utf-8")

        rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)
        rss_migration.migrate_markdown_to_jsonl(md_path, cargo_path)

        entries = rss_cargo.recall_cargo(cargo_path)
        # Migration appends, so running twice doubles entries
        assert len(entries) == 2
