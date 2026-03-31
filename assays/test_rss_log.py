"""Tests for endocytosis_rss/log.py - markdown log handling."""

import tempfile
from datetime import UTC, datetime
from pathlib import Path

from metabolon.organelles.endocytosis_rss.log import (
    _sanitize_text,
    _title_prefix,
    is_noise,
    recall_title_prefixes,
    serialize_markdown,
    generate_daily_markdown,
    record_cargo,
    cycle_log,
)


def test_title_prefix_extracts_significant_words():
    """Test _title_prefix normalizes and extracts first 6 significant words."""
    prefix = _title_prefix("The Quick Brown Fox Jumps Over Lazy Dogs!")
    assert "quick" in prefix
    assert "brown" in prefix
    # "the" has len=3, so it's kept (> 2 char filter)


def test_title_prefix_filters_short_words():
    """Test _title_prefix filters words with length <= 2."""
    prefix = _title_prefix("A An The In On To Major Story Here")
    assert "major" in prefix
    assert "story" in prefix
    words = prefix.split()
    assert all(len(w) > 2 for w in words)


def test_title_prefix_limits_to_six_words():
    """Test _title_prefix returns at most 6 significant words."""
    prefix = _title_prefix("One Two Three Four Five Six Seven Eight Nine Ten")
    assert len(prefix.split()) == 6


def test_title_prefix_empty_string():
    """Test _title_prefix returns empty for empty input."""
    assert _title_prefix("") == ""


def test_is_noise_detects_short_titles():
    """Test is_noise returns True for titles under 15 chars."""
    assert is_noise("Short") is True
    assert is_noise("This is a longer title that passes") is False


def test_is_noise_detects_junk_phrases():
    """Test is_noise identifies common junk phrases."""
    assert is_noise("Subscribe") is True
    assert is_noise("Read More") is True
    assert is_noise("Current Accounts") is True
    assert is_noise("crypto investigations") is True


def test_is_noise_allows_valid_titles():
    """Test is_noise returns False for valid article titles."""
    assert is_noise("Federal Reserve Raises Interest Rates") is False
    assert is_noise("Major Bank Announces New Policy") is False


def test_sanitize_text_strips_newlines():
    """Test _sanitize_text collapses whitespace."""
    result = _sanitize_text("hello\nworld\ttest")
    assert result == "hello world test"


def test_sanitize_text_escapes_markdown_control():
    """Test _sanitize_text escapes leading markdown control chars."""
    assert _sanitize_text("# Heading").startswith("\\#")
    assert _sanitize_text("- list item").startswith("\\-")
    assert _sanitize_text("> quote").startswith("\\>")


def test_sanitize_text_preserves_normal_text():
    """Test _sanitize_text leaves normal text unchanged."""
    assert _sanitize_text("Normal text here") == "Normal text here"


def test_recall_title_prefixes_empty_file(tmp_path):
    """Test recall_title_prefixes returns empty set for nonexistent file."""
    result = recall_title_prefixes(tmp_path / "nonexistent.md")
    assert result == set()


def test_recall_title_prefixes_extracts_titles(tmp_path):
    """Test recall_title_prefixes extracts titles from markdown."""
    log_file = tmp_path / "news.md"
    log_file.write_text(
        '## 2024-01-15\n'
        '### Source\n'
        '- **[Article Title Here](https://example.com)**\n'
        '- **"Quoted Title Example"**\n'
    )
    prefixes = recall_title_prefixes(log_file)
    assert len(prefixes) >= 1


def test_serialize_markdown_basic():
    """Test serialize_markdown produces valid markdown."""
    results = {
        "FeedA": [
            {"title": "Article One", "link": "https://a.com/1", "date": "2024-01-15", "summary": "Test", "score": 5},
        ],
        "FeedB": [],
    }
    output = serialize_markdown(results, "2024-01-15")
    assert "## 2024-01-15" in output
    assert "### FeedA" in output
    assert "Article One" in output
    assert "FeedB" not in output  # empty sources not included


def test_serialize_markdown_high_score_marker():
    """Test serialize_markdown adds star marker for high scores."""
    results = {
        "Feed": [
            {"title": "Important", "link": "https://x.com", "score": 8, "date": "", "summary": ""},
        ]
    }
    output = serialize_markdown(results, "2024-01-15")
    assert "[★]" in output


def test_serialize_markdown_includes_banking_angle():
    """Test serialize_markdown includes banking_angle for starred items."""
    results = {
        "Feed": [
            {"title": "Important", "link": "https://x.com", "score": 7, "banking_angle": "Payment rails", "date": "", "summary": ""},
        ]
    }
    output = serialize_markdown(results, "2024-01-15")
    assert "banking_angle: Payment rails" in output


def test_generate_daily_markdown_empty(tmp_path):
    """Test generate_daily_markdown returns header for empty cargo."""
    from metabolon.organelles.endocytosis_rss.cargo import append_cargo
    
    cargo_path = tmp_path / "cargo.jsonl"
    output = generate_daily_markdown(cargo_path, "2024-01-15")
    assert "## 2024-01-15" in output


def test_generate_daily_markdown_with_entries(tmp_path):
    """Test generate_daily_markdown includes entries from cargo."""
    from metabolon.organelles.endocytosis_rss.cargo import append_cargo
    
    cargo_path = tmp_path / "cargo.jsonl"
    articles = [
        {"title": "Test Article", "source": "Feed", "link": "https://x.com", "date": "2024-01-15", "score": 5},
    ]
    append_cargo(cargo_path, articles)
    
    output = generate_daily_markdown(cargo_path, "2024-01-15")
    assert "Test Article" in output
    assert "### Feed" in output


def test_record_cargo_creates_file(tmp_path):
    """Test record_cargo creates new file if nonexistent."""
    log_path = tmp_path / "news.md"
    markdown = "## 2024-01-15\n\nTest content\n"
    
    record_cargo(log_path, markdown)
    assert log_path.exists()
    assert "Test content" in log_path.read_text()


def test_record_cargo_appends_after_marker(tmp_path):
    """Test record_cargo inserts content after marker."""
    log_path = tmp_path / "news.md"
    log_path.write_text("# News\n\n<!-- News entries below -->\nOld content\n")
    
    record_cargo(log_path, "## New entries\n")
    content = log_path.read_text()
    assert "## New entries" in content
    assert "Old content" in content


def test_cycle_log_no_rotation_needed(tmp_path):
    """Test cycle_log does nothing when file is small."""
    log_path = tmp_path / "news.md"
    log_path.write_text("# News\n\nContent\n")
    archive_dir = tmp_path / "archive"
    
    cycle_log(log_path, archive_dir, max_lines=100)
    assert not archive_dir.exists()


def test_cycle_log_rotates_old_content(tmp_path):
    """Test cycle_log archives old entries when file exceeds max_lines."""
    log_path = tmp_path / "news.md"
    # Create a file with old date header
    lines = ["# News", "<!-- News entries below -->"]
    lines.extend(["content"] * 20)
    lines.append("## 2024-01-01")  # Old date
    lines.extend(["old content"] * 10)
    log_path.write_text("\n".join(lines) + "\n")
    
    archive_dir = tmp_path / "archive"
    now = datetime(2024, 1, 20, tzinfo=UTC)  # 19 days later
    
    cycle_log(log_path, archive_dir, max_lines=15, now=now)
    # The rotation should have occurred
    assert log_path.read_text() != "\n".join(lines) + "\n"
