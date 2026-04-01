from __future__ import annotations

"""Tests for metabolon.organelles.engram — chat session archive search."""

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.engram import (
    EngramRecord,
    TraceFragment,
    _color_enabled,
    _date_to_range_ms,
    _extract_text,
    _highlight_matches,
    _is_plain_word,
    _make_line_context,
    _make_snippet,
    _matches_role,
    _ms_to_hkt,
    _now_hkt,
    _parse_rfc3339,
    _print_json_scan,
    _print_json_search,
    _print_scan,
    _print_search,
    _read_opencode_text,
    _resolve_date,
    _scan_history,
    _scan_opencode,
    _search_prompts,
    _search_transcripts,
    scan,
    search,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_HKT = timezone(timedelta(hours=8))


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------


class TestNowHkt:
    def test_returns_aware_datetime(self):
        result = _now_hkt()
        assert result.tzinfo is not None

    def test_timezone_is_utc8(self):
        result = _now_hkt()
        assert result.utcoffset() == timedelta(hours=8)


class TestResolveDate:
    @patch("metabolon.organelles.engram._now_hkt")
    def test_today(self, mock_now):
        mock_now.return_value = datetime(2025, 6, 15, 10, 30, tzinfo=_HKT)
        assert _resolve_date("today") == "2025-06-15"

    @patch("metabolon.organelles.engram._now_hkt")
    def test_yesterday(self, mock_now):
        mock_now.return_value = datetime(2025, 6, 15, 10, 30, tzinfo=_HKT)
        assert _resolve_date("yesterday") == "2025-06-14"

    def test_valid_iso_date(self):
        assert _resolve_date("2025-03-01") == "2025-03-01"

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            _resolve_date("not-a-date")

    def test_invalid_month_raises(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            _resolve_date("2025-13-01")


class TestDateToRangeMs:
    def test_range_is_exactly_one_day(self):
        start, end = _date_to_range_ms("2025-06-15")
        assert end - start == 86400_000  # 24 hours in ms

    def test_start_is_midnight_hkt(self):
        start, end = _date_to_range_ms("2025-06-15")
        dt = datetime.fromtimestamp(start / 1000, tz=_HKT)
        assert dt.hour == 0
        assert dt.minute == 0
        assert dt.second == 0
        assert dt.day == 15


class TestMsToHkt:
    def test_converts_correctly(self):
        # 2025-06-15 08:00:00 HKT = 2025-06-15 00:00:00 UTC
        utc_midnight = datetime(2025, 6, 15, 0, 0, 0, tzinfo=timezone.utc)
        ms = int(utc_midnight.timestamp() * 1000)
        result = _ms_to_hkt(ms)
        assert result.hour == 8
        assert result.day == 15


class TestParseRfc3339:
    def test_z_suffix(self):
        result = _parse_rfc3339("2025-06-15T10:30:00Z")
        assert result is not None
        assert result.year == 2025
        assert result.month == 6
        assert result.day == 15

    def test_offset_suffix(self):
        result = _parse_rfc3339("2025-06-15T10:30:00+08:00")
        assert result is not None
        assert result.utcoffset() == timedelta(hours=8)

    def test_invalid_returns_none(self):
        assert _parse_rfc3339("not-a-date") is None

    def test_empty_returns_none(self):
        assert _parse_rfc3339("") is None


# ---------------------------------------------------------------------------
# Content extraction
# ---------------------------------------------------------------------------


class TestExtractText:
    def test_plain_string(self):
        assert _extract_text("hello world") == "hello world"

    def test_text_block(self):
        content = [{"type": "text", "text": "Hello there"}]
        assert _extract_text(content) == "Hello there"

    def test_tool_use_block(self):
        content = [{"type": "tool_use", "name": "Bash"}]
        assert _extract_text(content) == "[tool: Bash]"

    def test_mixed_blocks(self):
        content = [
            {"type": "text", "text": "Let me check"},
            {"type": "tool_use", "name": "Read"},
            {"type": "text", "text": "the file"},
        ]
        assert _extract_text(content) == "Let me check [tool: Read] the file"

    def test_empty_list(self):
        assert _extract_text([]) == ""

    def test_non_dict_items_ignored(self):
        content = ["string_item", 42, {"type": "text", "text": "valid"}]
        assert _extract_text(content) == "valid"

    def test_non_string_non_list(self):
        assert _extract_text(42) == ""

    def test_block_without_text_key(self):
        content = [{"type": "text"}]
        assert _extract_text(content) == ""

    def test_tool_use_without_name(self):
        content = [{"type": "tool_use"}]
        assert _extract_text(content) == ""


# ---------------------------------------------------------------------------
# Snippet helpers
# ---------------------------------------------------------------------------


class TestMakeSnippet:
    def test_short_text_no_truncation(self):
        text = "hello world"
        result = _make_snippet(text, 0, 5)
        assert result == "hello world"

    def test_truncation_at_start(self):
        text = "x" * 200
        result = _make_snippet(text, 100, 105)
        assert result.startswith("...")
        assert not result.endswith("...")

    def test_truncation_at_end(self):
        text = "x" * 200
        result = _make_snippet(text, 0, 5)
        assert result.endswith("...")
        assert not result.startswith("...")

    def test_newlines_replaced(self):
        text = "line1\nline2\nline3"
        result = _make_snippet(text, 5, 10)
        assert "\n" not in result

    def test_both_elipses(self):
        text = "x" * 300
        result = _make_snippet(text, 150, 155)
        assert result.startswith("...")
        assert result.endswith("...")


class TestMakeLineContext:
    def test_empty_text(self):
        match_line, before, after = _make_line_context("", 0, 2)
        assert match_line == ""
        assert before == []
        assert after == []

    def test_single_line(self):
        match_line, before, after = _make_line_context("hello world", 5, 0)
        assert match_line == "hello world"
        assert before == []
        assert after == []

    def test_context_lines_zero(self):
        text = "line1\nline2\nline3"
        match_line, before, after = _make_line_context(text, 6, 0)
        assert match_line == "line2"
        assert before == []
        assert after == []

    def test_context_lines_one(self):
        text = "line1\nline2\nline3\nline4"
        match_line, before, after = _make_line_context(text, 6, 1)
        assert match_line == "line2"
        assert before == ["line1"]
        assert after == ["line3"]

    def test_context_at_beginning(self):
        text = "line1\nline2\nline3"
        match_line, before, after = _make_line_context(text, 2, 2)
        assert match_line == "line1"
        assert before == []
        assert after == ["line2", "line3"]

    def test_context_at_end(self):
        text = "line1\nline2\nline3"
        match_line, before, after = _make_line_context(text, 15, 2)
        assert match_line == "line3"
        assert before == ["line1", "line2"]
        assert after == []


# ---------------------------------------------------------------------------
# Role matching
# ---------------------------------------------------------------------------


class TestMatchesRole:
    @pytest.mark.parametrize(
        "filt",
        ["you", "You", "YOU", "user", "me"],
    )
    def test_user_role(self, filt):
        assert _matches_role("you", filt) is True

    @pytest.mark.parametrize(
        "filt",
        ["claude", "Claude", "assistant", "ai", "AI"],
    )
    def test_claude_role(self, filt):
        assert _matches_role("claude", filt) is True

    def test_opencode_role(self):
        assert _matches_role("opencode", "opencode") is True

    def test_exact_match(self):
        assert _matches_role("custom", "custom") is True

    def test_no_match(self):
        assert _matches_role("you", "claude") is False

    def test_claude_role_matches_opencode(self):
        # "assistant" filter matches "opencode" role via the claude/opencode branch
        assert _matches_role("opencode", "assistant") is True

    def test_claude_does_not_match_you(self):
        assert _matches_role("claude", "you") is False


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class TestEngramRecord:
    def test_creation(self):
        r = EngramRecord(
            time_str="10:30",
            timestamp_ms=1000,
            session="abcd1234",
            session_full="abcd1234efgh5678",
            prompt="test prompt",
            tool="Claude",
        )
        assert r.time_str == "10:30"
        assert r.prompt == "test prompt"
        assert r.tool == "Claude"


class TestTraceFragment:
    def test_default_fields(self):
        f = TraceFragment(
            date="2025-06-15",
            time_str="10:30",
            timestamp_ms=1000,
            session="abcd1234",
            role="you",
            snippet="test snippet",
            tool="Claude",
        )
        assert f.match_line == ""
        assert f.context_before == []
        assert f.context_after == []

    def test_with_context(self):
        f = TraceFragment(
            date="2025-06-15",
            time_str="10:30",
            timestamp_ms=1000,
            session="abcd1234",
            role="you",
            snippet="test",
            tool="Claude",
            match_line="matched line",
            context_before=["line before"],
            context_after=["line after"],
        )
        assert f.match_line == "matched line"
        assert f.context_before == ["line before"]


# ---------------------------------------------------------------------------
# _is_plain_word
# ---------------------------------------------------------------------------


class TestIsPlainWord:
    def test_simple_word(self):
        assert _is_plain_word("hello") is True

    def test_with_hyphen(self):
        assert _is_plain_word("my-var") is True

    def test_with_digits(self):
        assert _is_plain_word("test123") is True

    def test_with_regex_chars(self):
        assert _is_plain_word("test.*") is False

    def test_with_parens(self):
        assert _is_plain_word("test()") is False

    def test_empty_string(self):
        assert _is_plain_word("") is False


# ---------------------------------------------------------------------------
# Highlighting
# ---------------------------------------------------------------------------


class TestHighlightMatches:
    def test_no_color_returns_unmodified(self):
        text = "hello world"
        regex = re.compile("world")
        assert _highlight_matches(text, regex, color=False) == text

    def test_empty_text(self):
        regex = re.compile("test")
        assert _highlight_matches("", regex, color=True) == ""

    def test_highlight_with_color(self):
        text = "find this word here"
        regex = re.compile("this")
        result = _highlight_matches(text, regex, color=True)
        assert "\033[1;31m" in result
        assert "\033[0m" in result
        assert "this" in result

    def test_no_match(self):
        text = "hello world"
        regex = re.compile("xyz")
        result = _highlight_matches(text, regex, color=True)
        assert result == text

    def test_multiple_matches(self):
        text = "cat and cat"
        regex = re.compile("cat")
        result = _highlight_matches(text, regex, color=True)
        assert result.count("\033[1;31m") == 2


class TestColorEnabled:
    def test_no_color_env(self, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")
        assert _color_enabled() is False


# ---------------------------------------------------------------------------
# _read_opencode_text
# ---------------------------------------------------------------------------


class TestReadOpencodeText:
    def test_nonexistent_dir_returns_empty(self, tmp_path):
        result = _read_opencode_text(tmp_path, "nonexistent-msg-id")
        assert result == ""

    def test_reads_parts(self, tmp_path):
        msg_id = "msg_001"
        part_dir = tmp_path / "part" / msg_id
        part_dir.mkdir(parents=True)
        (part_dir / "001.json").write_text(json.dumps({"text": "Hello "}))
        (part_dir / "002.json").write_text(json.dumps({"text": "World"}))
        result = _read_opencode_text(tmp_path, msg_id)
        assert result == "Hello World"

    def test_skips_bad_json(self, tmp_path):
        msg_id = "msg_002"
        part_dir = tmp_path / "part" / msg_id
        part_dir.mkdir(parents=True)
        (part_dir / "001.json").write_text(json.dumps({"text": "Good"}))
        (part_dir / "002.json").write_text("bad json{{{")
        result = _read_opencode_text(tmp_path, msg_id)
        assert result == "Good"

    def test_skips_empty_text(self, tmp_path):
        msg_id = "msg_003"
        part_dir = tmp_path / "part" / msg_id
        part_dir.mkdir(parents=True)
        (part_dir / "001.json").write_text(json.dumps({"text": ""}))
        (part_dir / "002.json").write_text(json.dumps({"text": "Data"}))
        result = _read_opencode_text(tmp_path, msg_id)
        assert result == "Data"


# ---------------------------------------------------------------------------
# _scan_opencode (mocked filesystem)
# ---------------------------------------------------------------------------


class TestScanOpencode:
    @patch("metabolon.organelles.engram._opencode_storage")
    def test_no_session_dir(self, mock_storage, tmp_path):
        mock_storage.return_value = tmp_path
        result = _scan_opencode(0, 9999999999999)
        assert result == []

    @patch("metabolon.organelles.engram._opencode_storage")
    def test_finds_user_prompts(self, mock_storage, tmp_path):
        start_ms = 1000000
        end_ms = start_ms + 86400_000

        # Build session structure
        sess_dir = tmp_path / "session" / "sess_abc"
        sess_dir.mkdir(parents=True)
        sess_data = {"id": "sess_abc12345678", "time": {"created": start_ms + 1000, "updated": start_ms + 2000}}
        (sess_dir / "session.json").write_text(json.dumps(sess_data))

        # Build message structure
        msg_dir = tmp_path / "message" / "sess_abc12345678"
        msg_dir.mkdir(parents=True)
        msg_data = {
            "id": "msg_001",
            "role": "user",
            "time": {"created": start_ms + 5000},
        }
        (msg_dir / "msg_001.json").write_text(json.dumps(msg_data))

        # Build part structure
        part_dir = tmp_path / "part" / "msg_001"
        part_dir.mkdir(parents=True)
        (part_dir / "001.json").write_text(json.dumps({"text": "What is the weather?"}))

        mock_storage.return_value = tmp_path
        result = _scan_opencode(start_ms, end_ms)
        assert len(result) == 1
        assert result[0].prompt == "What is the weather?"
        assert result[0].tool == "OpenCode"

    @patch("metabolon.organelles.engram._opencode_storage")
    def test_skips_non_user_messages(self, mock_storage, tmp_path):
        start_ms = 1000000
        end_ms = start_ms + 86400_000

        sess_dir = tmp_path / "session" / "sess_abc"
        sess_dir.mkdir(parents=True)
        sess_data = {"id": "sess_abc12345678", "time": {"created": start_ms + 1000}}
        (sess_dir / "session.json").write_text(json.dumps(sess_data))

        msg_dir = tmp_path / "message" / "sess_abc12345678"
        msg_dir.mkdir(parents=True)
        msg_data = {
            "id": "msg_002",
            "role": "assistant",
            "time": {"created": start_ms + 5000},
        }
        (msg_dir / "msg_002.json").write_text(json.dumps(msg_data))

        mock_storage.return_value = tmp_path
        result = _scan_opencode(start_ms, end_ms)
        assert result == []


# ---------------------------------------------------------------------------
# _scan_history (mocked filesystem)
# ---------------------------------------------------------------------------


class TestScanHistory:
    @patch("metabolon.organelles.engram._scan_opencode", return_value=[])
    @patch("metabolon.organelles.engram._history_files")
    def test_reads_history_jsonl(self, mock_hf, mock_oc, tmp_path):
        date_str = "2025-06-15"
        start_ms, end_ms = _date_to_range_ms(date_str)

        # Create a fake history file
        hist_file = tmp_path / "history.jsonl"
        ts_ms = start_ms + 3600_000  # 1 hour in
        entry = {
            "timestamp": ts_ms,
            "display": "Fix the bug",
            "sessionId": "sess1234567890",
        }
        hist_file.write_text(json.dumps(entry) + "\n")

        mock_hf.return_value = [("Claude", hist_file)]
        result = _scan_history(date_str)
        assert len(result) == 1
        assert result[0].prompt == "Fix the bug"
        assert result[0].tool == "Claude"

    @patch("metabolon.organelles.engram._scan_opencode", return_value=[])
    @patch("metabolon.organelles.engram._history_files")
    def test_tool_filter(self, mock_hf, mock_oc, tmp_path):
        date_str = "2025-06-15"
        start_ms, end_ms = _date_to_range_ms(date_str)
        ts_ms = start_ms + 3600_000

        hist_file = tmp_path / "history.jsonl"
        entry = {"timestamp": ts_ms, "display": "test", "sessionId": "sess1"}
        hist_file.write_text(json.dumps(entry) + "\n")

        mock_hf.return_value = [("Claude", hist_file), ("Codex", tmp_path / "codex.jsonl")]

        # Filter for Codex only — should skip Claude entries
        result = _scan_history(date_str, tool_filter="Codex")
        assert len(result) == 0

    @patch("metabolon.organelles.engram._scan_opencode", return_value=[])
    @patch("metabolon.organelles.engram._history_files")
    def test_missing_file_skipped(self, mock_hf, mock_oc):
        missing = Path("/nonexistent/path/history.jsonl")
        mock_hf.return_value = [("Claude", missing)]
        result = _scan_history("2025-06-15")
        assert result == []

    @patch("metabolon.organelles.engram._scan_opencode", return_value=[])
    @patch("metabolon.organelles.engram._history_files")
    def test_sorts_by_timestamp(self, mock_hf, mock_oc, tmp_path):
        date_str = "2025-06-15"
        start_ms, end_ms = _date_to_range_ms(date_str)

        hist_file = tmp_path / "history.jsonl"
        ts1 = start_ms + 7200_000
        ts2 = start_ms + 3600_000
        lines = [
            json.dumps({"timestamp": ts1, "display": "later", "sessionId": "s1"}),
            json.dumps({"timestamp": ts2, "display": "earlier", "sessionId": "s2"}),
        ]
        hist_file.write_text("\n".join(lines) + "\n")

        mock_hf.return_value = [("Claude", hist_file)]
        result = _scan_history(date_str)
        assert len(result) == 2
        assert result[0].prompt == "earlier"
        assert result[1].prompt == "later"


# ---------------------------------------------------------------------------
# _search_prompts (mocked)
# ---------------------------------------------------------------------------


class TestSearchPrompts:
    @patch("metabolon.organelles.engram._iter_opencode_messages", return_value=[])
    @patch("metabolon.organelles.engram._opencode_storage")
    @patch("metabolon.organelles.engram._history_files")
    def test_finds_match(self, mock_hf, mock_storage, mock_iter, tmp_path):
        start_ms = 1000000
        end_ms = start_ms + 86400_000

        hist_file = tmp_path / "history.jsonl"
        ts = start_ms + 3600_000
        entry = {"timestamp": ts, "display": "debug the flask app", "sessionId": "sess1234"}
        hist_file.write_text(json.dumps(entry) + "\n")

        mock_hf.return_value = [("Claude", hist_file)]
        mock_storage.return_value = tmp_path

        regex = re.compile("flask", re.IGNORECASE)
        result = _search_prompts(regex, start_ms, end_ms, None, None, None)
        assert len(result) == 1
        assert "flask" in result[0].snippet.lower()

    @patch("metabolon.organelles.engram._iter_opencode_messages", return_value=[])
    @patch("metabolon.organelles.engram._opencode_storage")
    @patch("metabolon.organelles.engram._history_files")
    def test_role_filter_skips_non_user(self, mock_hf, mock_storage, mock_iter):
        # Prompts are always role "you" — filtering for "claude" should return []
        regex = re.compile("test", re.IGNORECASE)
        result = _search_prompts(regex, 0, 9999999999999, None, "claude", None)
        assert result == []

    @patch("metabolon.organelles.engram._iter_opencode_messages", return_value=[])
    @patch("metabolon.organelles.engram._opencode_storage")
    @patch("metabolon.organelles.engram._history_files")
    def test_tool_filter(self, mock_hf, mock_storage, mock_iter, tmp_path):
        start_ms = 1000000
        end_ms = start_ms + 86400_000

        hist_file = tmp_path / "history.jsonl"
        ts = start_ms + 3600_000
        entry = {"timestamp": ts, "display": "test query", "sessionId": "sess1234"}
        hist_file.write_text(json.dumps(entry) + "\n")

        mock_hf.return_value = [("Claude", hist_file)]
        mock_storage.return_value = tmp_path

        regex = re.compile("test", re.IGNORECASE)
        # Filter for Codex — should skip Claude
        result = _search_prompts(regex, start_ms, end_ms, "Codex", None, None)
        assert result == []


# ---------------------------------------------------------------------------
# _search_transcripts (mocked)
# ---------------------------------------------------------------------------


class TestSearchTranscripts:
    @patch("metabolon.organelles.engram._iter_opencode_messages", return_value=[])
    @patch("metabolon.organelles.engram._opencode_storage")
    @patch("metabolon.organelles.engram._projects_dir")
    @patch("metabolon.organelles.engram._history_files")
    def test_searches_claude_transcripts(self, mock_hf, mock_proj, mock_storage, mock_iter, tmp_path):
        start_ms = 1000000
        end_ms = start_ms + 86400_000

        # Build a fake project dir with a session file
        proj_dir = tmp_path / "projects"
        proj_dir.mkdir()
        session_file = proj_dir / "test-session.jsonl"

        # The mtime needs to be within range
        import os

        ts_str = "2025-06-15T08:00:00+08:00"
        entry = {
            "type": "user",
            "timestamp": ts_str,
            "sessionId": "test-session-id",
            "message": {"content": [{"type": "text", "text": "deploy to production server"}]},
        }
        session_file.write_text(json.dumps(entry) + "\n")

        # Set mtime to be in range
        mid_epoch = (start_ms + end_ms) // 2 // 1000
        os.utime(session_file, (mid_epoch, mid_epoch))

        mock_proj.return_value = proj_dir
        mock_hf.return_value = []
        mock_storage.return_value = tmp_path

        regex = re.compile("production", re.IGNORECASE)
        result = _search_transcripts(regex, start_ms, end_ms, None, None, None)
        assert len(result) == 1
        assert result[0].role == "you"
        assert "production" in result[0].snippet.lower()

    @patch("metabolon.organelles.engram._iter_opencode_messages", return_value=[])
    @patch("metabolon.organelles.engram._opencode_storage")
    @patch("metabolon.organelles.engram._projects_dir")
    def test_role_filter(self, mock_proj, mock_storage, mock_iter, tmp_path):
        # No project dir — just test that role filter works with OpenCode too
        mock_proj.return_value = tmp_path / "nonexistent"
        mock_storage.return_value = tmp_path

        regex = re.compile("test", re.IGNORECASE)
        result = _search_transcripts(regex, 0, 9999999999999, None, "claude", None)
        # No data, no matches
        assert result == []


# ---------------------------------------------------------------------------
# Public API: scan
# ---------------------------------------------------------------------------


class TestScanApi:
    @patch("metabolon.organelles.engram._scan_history")
    @patch("metabolon.organelles.engram._resolve_date")
    def test_scan_default(self, mock_resolve, mock_scan):
        mock_resolve.return_value = "2025-06-15"
        mock_scan.return_value = []
        result = scan()
        mock_resolve.assert_called_once_with("today")
        mock_scan.assert_called_once_with("2025-06-15", None)

    @patch("metabolon.organelles.engram._scan_history")
    @patch("metabolon.organelles.engram._resolve_date")
    def test_scan_with_tool(self, mock_resolve, mock_scan):
        mock_resolve.return_value = "2025-06-15"
        mock_scan.return_value = []
        scan(tool="Claude")
        mock_scan.assert_called_once_with("2025-06-15", "Claude")


# ---------------------------------------------------------------------------
# Public API: search
# ---------------------------------------------------------------------------


class TestSearchApi:
    @patch("metabolon.organelles.engram._search_transcripts")
    @patch("metabolon.organelles.engram._now_hkt")
    def test_search_deep(self, mock_now, mock_transcripts):
        mock_now.return_value = datetime(2025, 6, 15, 10, 0, tzinfo=_HKT)
        mock_transcripts.return_value = []
        result = search("test", days=7, deep=True)
        assert result == []
        mock_transcripts.assert_called_once()

    @patch("metabolon.organelles.engram._search_prompts")
    @patch("metabolon.organelles.engram._now_hkt")
    def test_search_prompts_only(self, mock_now, mock_prompts):
        mock_now.return_value = datetime(2025, 6, 15, 10, 0, tzinfo=_HKT)
        mock_prompts.return_value = []
        result = search("test", deep=False)
        assert result == []
        mock_prompts.assert_called_once()

    def test_search_invalid_regex(self):
        with pytest.raises(ValueError, match="Invalid regex"):
            search("[invalid")


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------


class TestPrintScan:
    def test_prints_header(self, capsys):
        prompts = [
            EngramRecord(
                time_str="10:30",
                timestamp_ms=1000000,
                session="abcd1234",
                session_full="abcd1234efgh",
                prompt="test prompt",
                tool="Claude",
            )
        ]
        _print_scan(prompts, "2025-06-15", full=False)
        output = capsys.readouterr().out
        assert "Date: 2025-06-15" in output
        assert "Total: 1 prompts" in output
        assert "test prompt" in output

    def test_empty_prompts(self, capsys):
        _print_scan([], "2025-06-15", full=False)
        output = capsys.readouterr().out
        assert "Total: 0 prompts" in output

    def test_full_flag(self, capsys):
        prompts = [
            EngramRecord(
                time_str="10:30",
                timestamp_ms=i * 1000,
                session="sess",
                session_full="sessfull",
                prompt=f"prompt {i}",
                tool="Claude",
            )
            for i in range(5)
        ]
        _print_scan(prompts, "2025-06-15", full=True)
        output = capsys.readouterr().out
        assert "All prompts:" in output


class TestPrintSearch:
    def test_no_matches(self, capsys):
        regex = re.compile("test")
        _print_search([], regex, "test", 7, False, None, None, 0)
        output = capsys.readouterr().out
        assert "No matches found" in output

    def test_with_matches(self, capsys):
        regex = re.compile("flask")
        matches = [
            TraceFragment(
                date="2025-06-15",
                time_str="10:30",
                timestamp_ms=1000000,
                session="abcd1234",
                role="you",
                snippet="use flask for the api",
                tool="Claude",
            )
        ]
        _print_search(matches, regex, "flask", 7, True, None, None, 0)
        output = capsys.readouterr().out
        assert "Found 1 matches" in output
        assert "2025-06-15" in output


class TestPrintJsonScan:
    def test_outputs_valid_json(self, capsys):
        prompts = [
            EngramRecord(
                time_str="10:30",
                timestamp_ms=1000,
                session="abcd",
                session_full="abcdefgh",
                prompt="test",
                tool="Claude",
            )
        ]
        _print_json_scan(prompts, "2025-06-15")
        output = capsys.readouterr().out
        data = json.loads(output)
        assert data["date"] == "2025-06-15"
        assert data["total"] == 1
        assert len(data["prompts"]) == 1


class TestPrintJsonSearch:
    def test_outputs_valid_json(self, capsys):
        matches = [
            TraceFragment(
                date="2025-06-15",
                time_str="10:30",
                timestamp_ms=1000,
                session="abcd",
                role="you",
                snippet="found it",
                tool="Claude",
            )
        ]
        _print_json_search(matches)
        output = capsys.readouterr().out
        data = json.loads(output)
        assert len(data) == 1
        assert data[0]["snippet"] == "found it"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestCli:
    @patch("metabolon.organelles.engram._print_scan")
    @patch("metabolon.organelles.engram._scan_history")
    @patch("metabolon.organelles.engram._resolve_date")
    def test_scan_default(self, mock_resolve, mock_scan, mock_print, capsys):
        import sys

        mock_resolve.return_value = "2025-06-15"
        mock_scan.return_value = []
        mock_print.return_value = None

        with patch.object(sys, "argv", ["engram"]):
            from metabolon.organelles.engram import _cli

            _cli()

        mock_resolve.assert_called_once_with("today")

    @patch("metabolon.organelles.engram._print_json_scan")
    @patch("metabolon.organelles.engram._scan_history")
    @patch("metabolon.organelles.engram._resolve_date")
    def test_scan_json_output(self, mock_resolve, mock_scan, mock_print_json, capsys):
        import sys

        mock_resolve.return_value = "2025-06-15"
        mock_scan.return_value = []
        mock_print_json.return_value = None

        with patch.object(sys, "argv", ["engram", "scan", "--json"]):
            from metabolon.organelles.engram import _cli

            _cli()

        mock_print_json.assert_called_once()

    @patch("metabolon.organelles.engram._print_search")
    @patch("metabolon.organelles.engram._now_hkt")
    def test_search_cli(self, mock_now, mock_print, capsys):
        import sys

        mock_now.return_value = datetime(2025, 6, 15, 10, 0, tzinfo=_HKT)
        mock_print.return_value = None

        with patch.object(sys, "argv", ["engram", "search", "flask", "--days", "3"]):
            from metabolon.organelles.engram import _cli

            _cli()

        mock_print.assert_called_once()
        # Check that --days 3 was propagated
        call_args = mock_print.call_args
        assert call_args[0][3] == 3  # days argument
