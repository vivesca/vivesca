"""Tests for metabolon/organelles/endocytosis_rss/log.py — log utilities."""

from __future__ import annotations

from datetime import UTC, datetime

from metabolon.organelles.endocytosis_rss.log import (
    _sanitize_text,
    _title_prefix,
    cycle_log,
    is_noise,
    recall_title_prefixes,
    record_cargo,
    serialize_markdown,
)

# ---------------------------------------------------------------------------
# _title_prefix
# ---------------------------------------------------------------------------


class TestTitlePrefix:
    def test_basic(self):
        result = _title_prefix("HSBC Reports Strong Q3 Results")
        assert "hsbc" in result
        assert "reports" in result

    def test_strips_punctuation(self):
        result = _title_prefix("Banking: The 'Future' of Finance")
        assert ":" not in result
        assert "'" not in result

    def test_truncates_to_six(self):
        words = " ".join(f"word{i}" for i in range(10))
        result = _title_prefix(words)
        assert len(result.split()) == 6

    def test_short_words_filtered(self):
        result = _title_prefix("to a an in on at bank")
        # Words with len > 2 are kept; "bank" (len=4) passes, "to" (len=2) does not
        assert "bank" in result
        assert "to" not in result


# ---------------------------------------------------------------------------
# is_noise
# ---------------------------------------------------------------------------


class TestIsNoise:
    def test_short_title(self):
        assert is_noise("short") is True

    def test_junk_phrase(self):
        assert is_noise("subscribe") is True
        assert is_noise("read more") is True
        assert is_noise("current accounts") is True

    def test_valid_title(self):
        assert is_noise("HSBC Posts Record Profit in Third Quarter") is False

    def test_chinese_junk(self):
        assert is_noise("量子位编辑something") is True

    def test_exact_boundary(self):
        # 14 chars after normalization = noise, 15+ = ok
        assert is_noise("a" * 14) is True
        assert is_noise("a" * 15) is False


# ---------------------------------------------------------------------------
# _sanitize_text
# ---------------------------------------------------------------------------


class TestSanitizeText:
    def test_strips_newlines(self):
        assert "\n" not in _sanitize_text("line1\nline2")

    def test_escapes_leading_hash(self):
        result = _sanitize_text("# heading")
        assert result.startswith("\\#")

    def test_escapes_leading_dash(self):
        result = _sanitize_text("- item")
        assert result.startswith("\\-")

    def test_normal_text_unchanged(self):
        assert _sanitize_text("hello world") == "hello world"

    def test_escapes_leading_greater(self):
        result = _sanitize_text("> quote")
        assert result.startswith("\\>")


# ---------------------------------------------------------------------------
# serialize_markdown
# ---------------------------------------------------------------------------


class TestSerializeMarkdown:
    def test_basic(self):
        results = {
            "RSS Feed": [
                {
                    "title": "Test Article",
                    "link": "https://example.com",
                    "date": "2025-01-15",
                    "summary": "A test summary",
                    "score": 8,
                    "banking_angle": "Relevant to banking",
                }
            ]
        }
        md = serialize_markdown(results, "2025-01-15")
        assert "## 2025-01-15 (Automated Daily Scan)" in md
        assert "### RSS Feed" in md
        assert "Test Article" in md
        assert "A test summary" in md
        assert "[★]" in md  # score >= 7
        assert "banking_angle" in md

    def test_no_star_for_low_score(self):
        results = {"Feed": [{"title": "Low", "link": "", "date": "", "summary": "", "score": 3}]}
        md = serialize_markdown(results, "2025-01-15")
        assert "[★]" not in md

    def test_empty_articles_skipped(self):
        results = {"Empty Feed": []}
        md = serialize_markdown(results, "2025-01-15")
        assert "Empty Feed" not in md


# ---------------------------------------------------------------------------
# record_cargo
# ---------------------------------------------------------------------------


class TestRecordCargo:
    def test_creates_new_file(self, tmp_path):
        log = tmp_path / "news.md"
        record_cargo(log, "## 2025-01-15\nHello")
        assert log.exists()
        assert "Hello" in log.read_text()

    def test_appends_after_marker(self, tmp_path):
        log = tmp_path / "news.md"
        log.write_text("# News\n\n<!-- News entries below, added by /endocytosis -->\nold entry\n")
        record_cargo(log, "## 2025-01-15\nnew entry")
        content = log.read_text()
        assert "new entry" in content
        assert "old entry" in content

    def test_appends_without_marker(self, tmp_path):
        log = tmp_path / "news.md"
        log.write_text("# News\nexisting\n")
        record_cargo(log, "## new section\nadded")
        content = log.read_text()
        assert "existing" in content
        assert "added" in content


# ---------------------------------------------------------------------------
# recall_title_prefixes
# ---------------------------------------------------------------------------


class TestRecallTitlePrefixes:
    def test_nonexistent(self, tmp_path):
        assert recall_title_prefixes(tmp_path / "nope.md") == set()

    def test_extracts_bold_titles(self, tmp_path):
        log = tmp_path / "news.md"
        log.write_text('Some intro\n- **"HSBC Posts Strong Results"**\nMore text\n')
        prefixes = recall_title_prefixes(log)
        assert any("hsbc" in p for p in prefixes)


# ---------------------------------------------------------------------------
# cycle_log
# ---------------------------------------------------------------------------


class TestCycleLog:
    def test_no_rotation_when_small(self, tmp_path):
        log = tmp_path / "news.md"
        log.write_text("## 2025-01-01\nshort\n")
        cycle_log(log, tmp_path / "archive", max_lines=100)
        assert log.read_text() == "## 2025-01-01\nshort\n"

    def test_rotates_old_entries(self, tmp_path):
        log = tmp_path / "news.md"
        old_date = "2024-01-01"
        content = f"# News\n\n<!-- News entries below -->\n## {old_date}\nold entry\n"
        # Pad to exceed max_lines
        for i in range(20):
            content += f"line {i}\n"
        log.write_text(content)
        now = datetime(2025, 3, 1, tzinfo=UTC)
        archive_dir = tmp_path / "archive"
        cycle_log(log, archive_dir, max_lines=5, now=now)
        # Archive should have been created
        assert archive_dir.exists()

    def test_nonexistent_file(self, tmp_path):
        # Should not raise
        cycle_log(tmp_path / "nope.md", tmp_path / "archive", max_lines=5)
