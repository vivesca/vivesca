"""Tests for metabolon/organelles/endocytosis_rss/cargo.py — JSONL cargo store."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from metabolon.organelles.endocytosis_rss.cargo import (
    append_cargo,
    recall_cargo,
    recall_title_prefixes,
    rotate_cargo,
    _title_prefix,
)


# ---------------------------------------------------------------------------
# append_cargo
# ---------------------------------------------------------------------------

class TestAppendCargo:
    def test_creates_file(self, tmp_path):
        cargo = tmp_path / "cargo.jsonl"
        append_cargo(cargo, [{"title": "test", "date": "2025-01-15"}])
        assert cargo.exists()
        lines = cargo.read_text().strip().splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0])["title"] == "test"

    def test_appends_multiple(self, tmp_path):
        cargo = tmp_path / "cargo.jsonl"
        append_cargo(cargo, [
            {"title": "first"},
            {"title": "second"},
        ])
        lines = cargo.read_text().strip().splitlines()
        assert len(lines) == 2

    def test_appends_to_existing(self, tmp_path):
        cargo = tmp_path / "cargo.jsonl"
        cargo.write_text('{"existing": true}\n')
        append_cargo(cargo, [{"title": "new"}])
        lines = cargo.read_text().strip().splitlines()
        assert len(lines) == 2


# ---------------------------------------------------------------------------
# recall_cargo
# ---------------------------------------------------------------------------

class TestRecallCargo:
    def test_nonexistent(self, tmp_path):
        assert recall_cargo(tmp_path / "nope.jsonl") == []

    def test_reads_all(self, tmp_path):
        cargo = tmp_path / "cargo.jsonl"
        cargo.write_text(
            '{"date": "2025-01-10", "title": "a"}\n'
            '{"date": "2025-01-15", "title": "b"}\n'
        )
        result = recall_cargo(cargo)
        assert len(result) == 2

    def test_since_filter(self, tmp_path):
        cargo = tmp_path / "cargo.jsonl"
        cargo.write_text(
            '{"date": "2025-01-10", "title": "a"}\n'
            '{"date": "2025-01-15", "title": "b"}\n'
        )
        result = recall_cargo(cargo, since="2025-01-13")
        assert len(result) == 1
        assert result[0]["title"] == "b"

    def test_month_filter(self, tmp_path):
        cargo = tmp_path / "cargo.jsonl"
        cargo.write_text(
            '{"date": "2025-01-15", "title": "jan"}\n'
            '{"date": "2025-02-15", "title": "feb"}\n'
        )
        result = recall_cargo(cargo, month="2025-02")
        assert len(result) == 1
        assert result[0]["title"] == "feb"

    def test_skips_invalid_json(self, tmp_path):
        cargo = tmp_path / "cargo.jsonl"
        cargo.write_text('{"date": "2025-01-15"}\nnot json\n')
        result = recall_cargo(cargo)
        assert len(result) == 1

    def test_skips_non_dict(self, tmp_path):
        cargo = tmp_path / "cargo.jsonl"
        cargo.write_text('{"date": "2025-01-15"}\n[1, 2, 3]\n')
        result = recall_cargo(cargo)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# _title_prefix
# ---------------------------------------------------------------------------

class TestTitlePrefix:
    def test_basic(self):
        result = _title_prefix("HSBC Reports Strong Results")
        assert "hsbc" in result

    def test_strips_punctuation(self):
        result = _title_prefix("Banking: The Future")
        assert ":" not in result


# ---------------------------------------------------------------------------
# recall_title_prefixes
# ---------------------------------------------------------------------------

class TestRecallTitlePrefixes:
    def test_nonexistent(self, tmp_path):
        assert recall_title_prefixes(tmp_path / "nope.jsonl") == set()

    def test_extracts(self, tmp_path):
        cargo = tmp_path / "cargo.jsonl"
        cargo.write_text('{"title": "HSBC Reports Strong Results"}\n')
        prefixes = recall_title_prefixes(cargo)
        assert any("hsbc" in p for p in prefixes)

    def test_skips_bad_lines(self, tmp_path):
        cargo = tmp_path / "cargo.jsonl"
        cargo.write_text('not json\n')
        assert recall_title_prefixes(cargo) == set()


# ---------------------------------------------------------------------------
# rotate_cargo
# ---------------------------------------------------------------------------

class TestRotateCargo:
    def test_no_rotation_needed(self, tmp_path):
        cargo = tmp_path / "cargo.jsonl"
        now = datetime(2025, 3, 20, tzinfo=UTC)
        cargo.write_text('{"date": "2025-03-15", "title": "recent"}\n')
        rotate_cargo(cargo, tmp_path / "archive", retain_days=14, now=now)
        assert cargo.read_text().strip() != ""

    def test_rotates_old(self, tmp_path):
        cargo = tmp_path / "cargo.jsonl"
        now = datetime(2025, 3, 15, tzinfo=UTC)
        old_date = "2025-02-01"
        recent_date = "2025-03-10"
        cargo.write_text(
            f'{{"date": "{old_date}", "title": "old"}}\n'
            f'{{"date": "{recent_date}", "title": "recent"}}\n'
        )
        archive_dir = tmp_path / "archive"
        rotate_cargo(cargo, archive_dir, retain_days=14, now=now)
        # Recent should remain
        remaining = recall_cargo(cargo)
        assert len(remaining) == 1
        assert remaining[0]["title"] == "recent"
        # Old should be in archive
        archive_files = list(archive_dir.glob("*.jsonl"))
        assert len(archive_files) == 1

    def test_nonexistent_file(self, tmp_path):
        # Should not raise
        rotate_cargo(tmp_path / "nope.jsonl", tmp_path / "archive")

    def test_preserves_non_json(self, tmp_path):
        cargo = tmp_path / "cargo.jsonl"
        now = datetime(2025, 3, 15, tzinfo=UTC)
        cargo.write_text('not json at all\n{"date": "2025-03-10", "title": "ok"}\n')
        rotate_cargo(cargo, tmp_path / "archive", retain_days=14, now=now)
        remaining = recall_cargo(cargo)
        assert len(remaining) == 1  # valid entry
        lines = cargo.read_text().strip().splitlines()
        assert any("not json" in l for l in lines)  # non-json preserved
