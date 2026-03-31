"""Tests for metabolon.sortase.logger module."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.sortase.logger import (
    DEFAULT_LOG_PATH,
    DEFAULT_COACHING_PATH,
    resolve_log_path,
    append_log,
    read_logs,
    _parse_iso_timestamp,
    _strip_frontmatter,
    _failure_reason_terms,
    _extract_coaching_notes,
    _failure_has_relevant_coaching,
    _file_count,
    aggregate_stats,
    analyze_logs,
)


class TestResolveLogPath:
    """Tests for resolve_log_path function."""

    def test_explicit_path(self):
        """Explicit path is returned as Path."""
        result = resolve_log_path("/custom/path/log.jsonl")
        assert result == Path("/custom/path/log.jsonl")

    def test_default_path(self):
        """Default path is used when none provided."""
        with patch.dict(os.environ, {}, clear=True):
            result = resolve_log_path()
            assert result == DEFAULT_LOG_PATH

    def test_env_override(self):
        """Environment variable overrides default path."""
        with patch.dict(os.environ, {"OPIFEX_LOG_PATH": "/env/override/log.jsonl"}, clear=False):
            result = resolve_log_path()
            assert result == Path("/env/override/log.jsonl")


class TestAppendLog:
    """Tests for append_log function."""

    def test_append_creates_file(self, tmp_path):
        """Append creates log file if it doesn't exist."""
        log_file = tmp_path / "log.jsonl"
        
        entry = {"tool": "gemini", "success": True}
        result = append_log(entry, log_file)
        
        assert log_file.exists()
        assert result == log_file

    def test_append_entry(self, tmp_path):
        """Append writes entry to log file."""
        log_file = tmp_path / "log.jsonl"
        
        entry = {"tool": "gemini", "success": True, "timestamp": "2024-01-01T00:00:00"}
        append_log(entry, log_file)
        
        content = log_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 1
        
        loaded = json.loads(lines[0])
        assert loaded["tool"] == "gemini"
        assert loaded["success"] is True

    def test_append_multiple_entries(self, tmp_path):
        """Multiple appends create multiple lines."""
        log_file = tmp_path / "log.jsonl"
        
        append_log({"tool": "gemini", "success": True}, log_file)
        append_log({"tool": "codex", "success": False}, log_file)
        
        content = log_file.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2

    def test_creates_parent_directory(self, tmp_path):
        """Parent directory is created if it doesn't exist."""
        log_file = tmp_path / "nested" / "dir" / "log.jsonl"
        
        append_log({"test": "data"}, log_file)
        
        assert log_file.parent.exists()
        assert log_file.exists()


class TestReadLogs:
    """Tests for read_logs function."""

    def test_read_empty_file(self, tmp_path):
        """Reading non-existent file returns empty list."""
        log_file = tmp_path / "nonexistent.jsonl"
        result = read_logs(log_file)
        assert result == []

    def test_read_single_entry(self, tmp_path):
        """Reading single entry returns list with one dict."""
        log_file = tmp_path / "log.jsonl"
        log_file.write_text('{"tool": "gemini", "success": true}\n')
        
        result = read_logs(log_file)
        
        assert len(result) == 1
        assert result[0]["tool"] == "gemini"

    def test_read_multiple_entries(self, tmp_path):
        """Reading multiple entries returns all."""
        log_file = tmp_path / "log.jsonl"
        log_file.write_text('{"tool": "gemini"}\n{"tool": "codex"}\n')
        
        result = read_logs(log_file)
        
        assert len(result) == 2
        assert result[0]["tool"] == "gemini"
        assert result[1]["tool"] == "codex"

    def test_read_skips_empty_lines(self, tmp_path):
        """Empty lines are skipped."""
        log_file = tmp_path / "log.jsonl"
        log_file.write_text('{"tool": "gemini"}\n\n{"tool": "codex"}\n\n')
        
        result = read_logs(log_file)
        
        assert len(result) == 2


class TestParseIsoTimestamp:
    """Tests for _parse_iso_timestamp function."""

    def test_valid_timestamp(self):
        """Valid ISO timestamp is parsed."""
        result = _parse_iso_timestamp("2024-01-15T10:30:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_valid_timestamp_with_timezone(self):
        """ISO timestamp with timezone is parsed."""
        result = _parse_iso_timestamp("2024-01-15T10:30:00+00:00")
        assert result is not None

    def test_invalid_timestamp_returns_none(self):
        """Invalid timestamp returns None."""
        result = _parse_iso_timestamp("not-a-timestamp")
        assert result is None

    def test_empty_string_returns_none(self):
        """Empty string returns None."""
        result = _parse_iso_timestamp("")
        assert result is None

    def test_non_string_returns_none(self):
        """Non-string input returns None."""
        result = _parse_iso_timestamp(12345)
        assert result is None


class TestStripFrontmatter:
    """Tests for _strip_frontmatter function."""

    def test_no_frontmatter(self):
        """Text without frontmatter is unchanged."""
        text = "Some content\nMore content"
        result = _strip_frontmatter(text)
        assert result == text

    def test_strip_yaml_frontmatter(self):
        """YAML frontmatter is stripped."""
        text = "---\ntitle: Test\n---\nContent here"
        result = _strip_frontmatter(text)
        assert result.strip() == "Content here"

    def test_incomplete_frontmatter_unchanged(self):
        """Incomplete frontmatter leaves text unchanged."""
        text = "---\ntitle: Test\nContent here"
        result = _strip_frontmatter(text)
        assert result == text


class TestFailureReasonTerms:
    """Tests for _failure_reason_terms function."""

    def test_empty_reason(self):
        """Empty reason returns unknown."""
        result = _failure_reason_terms("")
        assert result == {"unknown"}

    def test_whitespace_reason(self):
        """Whitespace-only reason returns unknown."""
        result = _failure_reason_terms("   ")
        assert result == {"unknown"}

    def test_known_reason_terms(self):
        """Known reason expands to terms."""
        result = _failure_reason_terms("tests failed")
        # The function extracts terms from the reason string
        assert "tests" in result or "failed" in result

    def test_quota_reason(self):
        """Quota reason extracts terms."""
        result = _failure_reason_terms("429 quota exceeded")
        assert "429" in result or "quota" in result

    def test_auth_reason(self):
        """Auth reason extracts terms."""
        result = _failure_reason_terms("authentication failed")
        # The function extracts terms from the reason string
        assert "authentication" in result or "failed" in result


class TestExtractCoachingNotes:
    """Tests for _extract_coaching_notes function."""

    def test_missing_file_returns_empty(self, tmp_path):
        """Missing coaching file returns empty list."""
        result = _extract_coaching_notes(tmp_path / "nonexistent.md")
        assert result == []

    def test_extract_notes_with_headings(self, tmp_path):
        """Notes are extracted from headings."""
        coaching_file = tmp_path / "coaching.md"
        coaching_file.write_text("""
### Import Hallucination

GLM sometimes invents imports.

### Return Type Flattening

GLM flattens return types.
""")
        
        result = _extract_coaching_notes(coaching_file)
        
        assert len(result) == 2
        assert any("import hallucination" in note["text"] for note in result)
        assert any("return type flattening" in note["text"] for note in result)

    def test_auto_detected_timestamp(self, tmp_path):
        """Auto-detected timestamp is parsed."""
        coaching_file = tmp_path / "coaching.md"
        coaching_file.write_text("""
<!-- auto-detected 2024-01-15 10:30 -->
### Pattern Name

Some pattern description.
""")
        
        result = _extract_coaching_notes(coaching_file)
        
        assert len(result) == 1
        # The timestamp should be parsed and stored as added_at
        assert result[0]["added_at"] == datetime(2024, 1, 15, 10, 30)


class TestFailureHasRelevantCoaching:
    """Tests for _failure_has_relevant_coaching function."""

    def test_no_relevant_coaching(self):
        """No relevant coaching returns False."""
        failure_reason = "unknown error"
        failure_time = datetime.now()
        coaching_notes = [
            {"text": "import hallucination pattern", "added_at": datetime.now() - timedelta(days=1)},
        ]
        
        result = _failure_has_relevant_coaching(failure_reason, failure_time, coaching_notes)
        assert result is False

    def test_relevant_coaching_exists(self):
        """Relevant coaching returns True."""
        failure_reason = "test failure"
        failure_time = datetime.now()
        coaching_notes = [
            {"text": "tests sometimes fail due to x", "added_at": datetime.now() - timedelta(days=1)},
        ]
        
        result = _failure_has_relevant_coaching(failure_reason, failure_time, coaching_notes)
        assert result is True

    def test_coaching_after_failure_not_counted(self):
        """Coaching added after failure doesn't count."""
        failure_reason = "test failure"
        failure_time = datetime(2024, 1, 1, 12, 0)
        coaching_notes = [
            {"text": "tests pattern", "added_at": datetime(2024, 1, 2, 12, 0)},  # After failure
        ]
        
        result = _failure_has_relevant_coaching(failure_reason, failure_time, coaching_notes)
        assert result is False


class TestFileCount:
    """Tests for _file_count function."""

    def test_integer_count(self):
        """Integer files_changed returns value."""
        result = _file_count({"files_changed": 5})
        assert result == 5

    def test_list_count(self):
        """List files_changed returns length."""
        result = _file_count({"files_changed": ["a.py", "b.py", "c.py"]})
        assert result == 3

    def test_empty_list(self):
        """Empty list returns 0."""
        result = _file_count({"files_changed": []})
        assert result == 0

    def test_missing_key(self):
        """Missing files_changed returns 0."""
        result = _file_count({})
        assert result == 0

    def test_negative_value_clamped(self):
        """Negative values are clamped to 0."""
        result = _file_count({"files_changed": -5})
        assert result == 0


class TestAggregateStats:
    """Tests for aggregate_stats function."""

    def test_empty_entries(self):
        """Empty entries return default stats."""
        result = aggregate_stats([])
        assert result["total_runs"] == 0
        assert result["per_tool"] == {}

    def test_single_entry(self):
        """Single entry is aggregated."""
        entries = [
            {"tool": "gemini", "success": True, "duration_s": 1.5, "timestamp": datetime.now().isoformat()},
        ]
        
        result = aggregate_stats(entries)
        
        assert result["total_runs"] == 1
        assert result["per_tool"]["gemini"]["runs"] == 1
        assert result["per_tool"]["gemini"]["success_rate"] == 1.0

    def test_multiple_entries(self):
        """Multiple entries are aggregated correctly."""
        entries = [
            {"tool": "gemini", "success": True, "duration_s": 1.0, "timestamp": datetime.now().isoformat()},
            {"tool": "gemini", "success": False, "duration_s": 2.0, "timestamp": datetime.now().isoformat()},
            {"tool": "codex", "success": True, "duration_s": 1.5, "timestamp": datetime.now().isoformat()},
        ]
        
        result = aggregate_stats(entries)
        
        assert result["total_runs"] == 3
        assert result["per_tool"]["gemini"]["runs"] == 2
        assert result["per_tool"]["gemini"]["success_rate"] == 0.5
        assert result["per_tool"]["codex"]["success_rate"] == 1.0

    def test_failure_reasons_counted(self):
        """Failure reasons are counted."""
        entries = [
            {"tool": "gemini", "success": False, "failure_reason": "quota"},
            {"tool": "gemini", "success": False, "failure_reason": "quota"},
            {"tool": "codex", "success": False, "failure_reason": "auth"},
        ]
        
        result = aggregate_stats(entries)
        
        assert result["failure_reasons"]["quota"] == 2
        assert result["failure_reasons"]["auth"] == 1

    def test_fallback_frequency_counted(self):
        """Fallback frequencies are counted."""
        entries = [
            {"tool": "gemini", "success": True, "fallbacks": ["goose", "codex"]},
            {"tool": "gemini", "success": True, "fallbacks": ["goose"]},
        ]
        
        result = aggregate_stats(entries)
        
        assert result["fallback_frequency"]["goose"] == 2
        assert result["fallback_frequency"]["codex"] == 1


class TestAnalyzeLogs:
    """Tests for analyze_logs function."""

    def test_empty_logs(self, tmp_path):
        """Empty logs return default analysis."""
        log_file = tmp_path / "log.jsonl"
        
        result = analyze_logs(log_file)
        
        assert result["total_entries"] == 0
        assert result["success_rate_by_backend"] == {}
        assert result["coaching_coverage"] is None

    def test_analyze_success_rates(self, tmp_path):
        """Success rates are calculated."""
        log_file = tmp_path / "log.jsonl"
        log_file.write_text('\n'.join([
            json.dumps({"tool": "gemini", "success": True, "timestamp": "2024-01-01T10:00:00"}),
            json.dumps({"tool": "gemini", "success": False, "timestamp": "2024-01-01T11:00:00"}),
            json.dumps({"tool": "codex", "success": True, "timestamp": "2024-01-01T12:00:00"}),
        ]))
        
        result = analyze_logs(log_file)
        
        assert result["success_rate_by_backend"]["gemini"] == 0.5
        assert result["success_rate_by_backend"]["codex"] == 1.0
        assert result["total_entries"] == 3

    def test_analyze_by_hour(self, tmp_path):
        """Hour-by-hour analysis."""
        log_file = tmp_path / "log.jsonl"
        log_file.write_text('\n'.join([
            json.dumps({"tool": "gemini", "success": True, "timestamp": "2024-01-01T10:00:00"}),
            json.dumps({"tool": "gemini", "success": True, "timestamp": "2024-01-01T10:30:00"}),
            json.dumps({"tool": "gemini", "success": False, "timestamp": "2024-01-01T14:00:00"}),
        ]))
        
        result = analyze_logs(log_file)
        
        assert "10" in result["success_rate_by_hour"]
        assert "14" in result["success_rate_by_hour"]

    def test_coaching_coverage_no_failures(self, tmp_path):
        """No failures means no coaching coverage calculation."""
        log_file = tmp_path / "log.jsonl"
        log_file.write_text(json.dumps({"tool": "gemini", "success": True, "timestamp": "2024-01-01T10:00:00"}))
        
        result = analyze_logs(log_file)
        
        assert result["coaching_coverage"] is None
        assert result["coaching_gap"] is None

    def test_plan_complexity_duration(self, tmp_path):
        """Duration by plan complexity (file count)."""
        log_file = tmp_path / "log.jsonl"
        log_file.write_text('\n'.join([
            json.dumps({"tool": "gemini", "success": True, "duration_s": 1.0, "files_changed": 1, "timestamp": "2024-01-01T10:00:00"}),
            json.dumps({"tool": "gemini", "success": True, "duration_s": 2.0, "files_changed": 1, "timestamp": "2024-01-01T11:00:00"}),
            json.dumps({"tool": "gemini", "success": True, "duration_s": 5.0, "files_changed": 3, "timestamp": "2024-01-01T12:00:00"}),
        ]))
        
        result = analyze_logs(log_file)
        
        assert 1 in result["avg_duration_by_plan_complexity"]
        assert 3 in result["avg_duration_by_plan_complexity"]
        # avg of 1.0 and 2.0 = 1.5
        assert result["avg_duration_by_plan_complexity"][1] == 1.5
