from __future__ import annotations

"""Tests for metabolon.organelles.engram — chat session archive search."""

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.engram import (
    EngramRecord,
    TraceFragment,
    _color_enabled,
    _date_to_range_ms,
    _extract_text,
    _fuzzy_search,
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
    _resolve_date,
    _scan_history,
    _scan_opencode,
    _search_prompts,
    _search_transcripts,
    scan,
    search,
)

# Fixed reference time: 2025-06-15 14:30:00 HKT (UTC+8)
_FIXED_HKT = datetime(2025, 6, 15, 14, 30, 0, tzinfo=timezone(timedelta(hours=8)))
_FIXED_MS = int(_FIXED_HKT.timestamp() * 1000)


# ---------------------------------------------------------------------------
# _resolve_date
# ---------------------------------------------------------------------------


class TestResolveDate:
    def test_today(self):
        with patch("metabolon.organelles.engram._now_hkt", return_value=_FIXED_HKT):
            assert _resolve_date("today") == "2025-06-15"

    def test_yesterday(self):
        with patch("metabolon.organelles.engram._now_hkt", return_value=_FIXED_HKT):
            assert _resolve_date("yesterday") == "2025-06-14"

    def test_valid_date_string(self):
        with patch("metabolon.organelles.engram._now_hkt", return_value=_FIXED_HKT):
            assert _resolve_date("2025-01-01") == "2025-01-01"

    def test_invalid_date_raises(self):
        with patch("metabolon.organelles.engram._now_hkt", return_value=_FIXED_HKT):
            with pytest.raises(ValueError, match="Invalid date format"):
                _resolve_date("not-a-date")

    def test_partial_date_raises(self):
        with patch("metabolon.organelles.engram._now_hkt", return_value=_FIXED_HKT):
            with pytest.raises(ValueError, match="Invalid date format"):
                _resolve_date("2025-13-01")


# ---------------------------------------------------------------------------
# _date_to_range_ms
# ---------------------------------------------------------------------------


class TestDateToRangeMs:
    def test_returns_start_and_end_ms(self):
        start, end = _date_to_range_ms("2025-06-15")
        # Should be exactly 1 day apart
        assert end - start == 86400_000

    def test_start_is_midnight_hkt(self):
        start, _ = _date_to_range_ms("2025-06-15")
        dt = _ms_to_hkt(start)
        assert dt.hour == 0
        assert dt.minute == 0
        assert dt.second == 0

    def test_end_is_next_midnight_hkt(self):
        _, end = _date_to_range_ms("2025-06-15")
        dt = _ms_to_hkt(end)
        assert dt.day == 16
        assert dt.hour == 0


# ---------------------------------------------------------------------------
# _ms_to_hkt
# ---------------------------------------------------------------------------


class TestMsToHkt:
    def test_converts_ms_to_hkt_datetime(self):
        dt = _ms_to_hkt(_FIXED_MS)
        assert dt.tzinfo is not None
        assert dt.hour == 14
        assert dt.minute == 30

    def test_timezone_is_hkt(self):
        dt = _ms_to_hkt(_FIXED_MS)
        utc_offset = dt.utcoffset()
        assert utc_offset == timedelta(hours=8)


# ---------------------------------------------------------------------------
# _parse_rfc3339
# ---------------------------------------------------------------------------


class TestParseRfc3339:
    def test_z_suffix(self):
        dt = _parse_rfc3339("2025-06-15T06:30:00Z")
        assert dt is not None
        assert dt.hour == 6

    def test_offset_suffix(self):
        dt = _parse_rfc3339("2025-06-15T14:30:00+08:00")
        assert dt is not None
        assert dt.hour == 14

    def test_invalid_returns_none(self):
        assert _parse_rfc3339("not-a-date") is None

    def test_empty_string_returns_none(self):
        assert _parse_rfc3339("") is None


# ---------------------------------------------------------------------------
# _extract_text
# ---------------------------------------------------------------------------


class TestExtractText:
    def test_plain_string(self):
        assert _extract_text("hello world") == "hello world"

    def test_text_blocks(self):
        content = [
            {"type": "text", "text": "line 1"},
            {"type": "text", "text": "line 2"},
        ]
        assert _extract_text(content) == "line 1 line 2"

    def test_tool_use_blocks(self):
        content = [
            {"type": "text", "text": "before"},
            {"type": "tool_use", "name": "Read"},
        ]
        assert _extract_text(content) == "before [tool: Read]"

    def test_empty_text_blocks_skipped(self):
        content = [
            {"type": "text", "text": ""},
            {"type": "text", "text": "visible"},
        ]
        assert _extract_text(content) == "visible"

    def test_non_dict_blocks_skipped(self):
        content = ["a string", {"type": "text", "text": "ok"}]
        assert _extract_text(content) == "ok"

    def test_other_types_skipped(self):
        content = [{"type": "image", "data": "..."}]
        assert _extract_text(content) == ""

    def test_unknown_type_returns_empty(self):
        assert _extract_text(42) == ""

    def test_none_returns_empty(self):
        assert _extract_text(None) == ""


# ---------------------------------------------------------------------------
# _make_snippet
# ---------------------------------------------------------------------------


class TestMakeSnippet:
    def test_short_text_unchanged(self):
        text = "short match here end"
        result = _make_snippet(text, 6, 11)
        assert "match" in result

    def test_elided_start(self):
        text = "x" * 100 + "MATCH" + "y" * 100
        result = _make_snippet(text, 100, 105)
        assert result.startswith("...")

    def test_elided_end(self):
        text = "a" * 50 + "MATCH" + "b" * 200
        result = _make_snippet(text, 50, 55)
        assert result.endswith("...")

    def test_newlines_replaced(self):
        text = "line1\nline2\nMATCH\nline4"
        result = _make_snippet(text, 13, 18)
        assert "\n" not in result


# ---------------------------------------------------------------------------
# _make_line_context
# ---------------------------------------------------------------------------


class TestMakeLineContext:
    def test_empty_text(self):
        line, before, after = _make_line_context("", 0, 0)
        assert line == ""
        assert before == []
        assert after == []

    def test_single_line(self):
        line, before, after = _make_line_context("hello world", 0, 0)
        assert line == "hello world"
        assert before == []
        assert after == []

    def test_multiline_with_context(self):
        text = "line0\nline1\nline2\nline3\nline4"
        # match_start=10 falls in "line1" (offset 6..11)
        line, before, after = _make_line_context(text, 10, context_lines=1)
        assert line == "line1"
        assert before == ["line0"]
        assert after == ["line2"]

    def test_zero_context_lines(self):
        text = "line0\nline1\nline2"
        line, before, after = _make_line_context(text, 6, context_lines=0)
        assert line == "line1"
        assert before == []
        assert after == []

    def test_context_at_start_of_file(self):
        text = "line0\nline1\nline2"
        line, before, after = _make_line_context(text, 0, context_lines=2)
        assert line == "line0"
        assert before == []
        assert after == ["line1", "line2"]


# ---------------------------------------------------------------------------
# _matches_role
# ---------------------------------------------------------------------------


class TestMatchesRole:
    @pytest.mark.parametrize(
        "filt",
        ["you", "You", "USER", "user", "me", "Me"],
    )
    def test_user_aliases(self, filt):
        assert _matches_role("you", filt) is True

    @pytest.mark.parametrize(
        "filt",
        ["claude", "Claude", "ASSISTANT", "assistant", "AI", "ai"],
    )
    def test_assistant_aliases(self, filt):
        assert _matches_role("claude", filt) is True

    def test_opencode_role(self):
        assert _matches_role("opencode", "opencode") is True

    def test_assistant_filter_matches_opencode(self):
        assert _matches_role("opencode", "assistant") is True

    def test_exact_match(self):
        assert _matches_role("custom", "custom") is True

    def test_no_match(self):
        assert _matches_role("you", "claude") is False


# ---------------------------------------------------------------------------
# _is_plain_word
# ---------------------------------------------------------------------------


class TestIsPlainWord:
    def test_simple_word(self):
        assert _is_plain_word("hello") is True

    def test_word_with_hyphen(self):
        assert _is_plain_word("my-var") is True

    def test_word_with_digits(self):
        assert _is_plain_word("test123") is True

    def test_regex_chars_false(self):
        assert _is_plain_word("hello.*") is False

    def test_parenthesis_false(self):
        assert _is_plain_word("func(") is False

    def test_empty_false(self):
        assert _is_plain_word("") is False


# ---------------------------------------------------------------------------
# _color_enabled
# ---------------------------------------------------------------------------


class TestColorEnabled:
    def test_not_a_tty(self):
        with patch.object(sys.stdout, "isatty", return_value=False):
            assert _color_enabled() is False

    def test_no_color_env(self):
        with patch.object(sys.stdout, "isatty", return_value=True), \
             patch.dict("os.environ", {"NO_COLOR": "1"}):
            assert _color_enabled() is False

    def test_enabled(self):
        with patch.object(sys.stdout, "isatty", return_value=True), \
             patch.dict("os.environ", {}, clear=True):
            assert _color_enabled() is True


# ---------------------------------------------------------------------------
# _highlight_matches
# ---------------------------------------------------------------------------


class TestHighlightMatches:
    def test_no_color_returns_text(self):
        regex = re.compile("test", re.IGNORECASE)
        assert _highlight_matches("test value", regex, color=False) == "test value"

    def test_empty_text(self):
        regex = re.compile("test", re.IGNORECASE)
        assert _highlight_matches("", regex, color=True) == ""

    def test_highlighted(self):
        regex = re.compile("test", re.IGNORECASE)
        result = _highlight_matches("a test b", regex, color=True)
        assert "\033[1;31m" in result
        assert "\033[0m" in result
        assert "test" in result

    def test_no_match_returns_original(self):
        regex = re.compile("xyz", re.IGNORECASE)
        assert _highlight_matches("hello world", regex, color=True) == "hello world"


# ---------------------------------------------------------------------------
# _scan_history
# ---------------------------------------------------------------------------


class TestScanHistory:
    def _make_jsonl(self, entries):
        return "\n".join(json.dumps(e) for e in entries) + "\n"

    @patch("metabolon.organelles.engram._scan_opencode", return_value=[])
    @patch("metabolon.organelles.engram._history_files")
    def test_basic_scan(self, mock_hf, mock_oc):
        ts_ms = _FIXED_MS
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.open.return_value.__enter__ = lambda s: StringIO(
            self._make_jsonl([{"timestamp": ts_ms, "display": "hello", "sessionId": "sess-abc123"}])
        )
        mock_path.open.return_value.__exit__ = MagicMock(return_value=False)
        mock_hf.return_value = [("Claude", mock_path)]

        result = _scan_history("2025-06-15")
        assert len(result) == 1
        assert result[0].prompt == "hello"
        assert result[0].tool == "Claude"
        assert result[0].session == "sess-abc"

    @patch("metabolon.organelles.engram._scan_opencode", return_value=[])
    @patch("metabolon.organelles.engram._history_files")
    def test_out_of_range_filtered(self, mock_hf, mock_oc):
        ts_ms = _FIXED_MS - 86400_000 * 10  # 10 days before
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.open.return_value.__enter__ = lambda s: StringIO(
            self._make_jsonl([{"timestamp": ts_ms, "display": "old", "sessionId": "sess-old"}])
        )
        mock_path.open.return_value.__exit__ = MagicMock(return_value=False)
        mock_hf.return_value = [("Claude", mock_path)]

        result = _scan_history("2025-06-15")
        assert len(result) == 0

    @patch("metabolon.organelles.engram._scan_opencode", return_value=[])
    @patch("metabolon.organelles.engram._history_files")
    def test_tool_filter(self, mock_hf, mock_oc):
        ts_ms = _FIXED_MS
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.open.return_value.__enter__ = lambda s: StringIO(
            self._make_jsonl([{"timestamp": ts_ms, "display": "claude prompt", "sessionId": "s1"}])
        )
        mock_path.open.return_value.__exit__ = MagicMock(return_value=False)
        mock_hf.return_value = [("Claude", mock_path)]

        result = _scan_history("2025-06-15", tool_filter="Claude")
        assert all(r.tool == "Claude" for r in result)

    @patch("metabolon.organelles.engram._scan_opencode", return_value=[])
    @patch("metabolon.organelles.engram._history_files")
    def test_missing_file_skipped(self, mock_hf, mock_oc):
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False
        mock_hf.return_value = [("Claude", mock_path)]

        result = _scan_history("2025-06-15")
        assert result == []

    @patch("metabolon.organelles.engram._scan_opencode", return_value=[])
    @patch("metabolon.organelles.engram._history_files")
    def test_malformed_jsonl_lines_skipped(self, mock_hf, mock_oc):
        ts_ms = _FIXED_MS
        data = "not json\n" + json.dumps({"timestamp": ts_ms, "display": "ok", "sessionId": "s1"}) + "\n"
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.open.return_value.__enter__ = lambda s: StringIO(data)
        mock_path.open.return_value.__exit__ = MagicMock(return_value=False)
        mock_hf.return_value = [("Claude", mock_path)]

        result = _scan_history("2025-06-15")
        assert len(result) == 1
        assert result[0].prompt == "ok"


# ---------------------------------------------------------------------------
# _search_prompts
# ---------------------------------------------------------------------------


class TestSearchPrompts:
    @patch("metabolon.organelles.engram._iter_opencode_messages", return_value=[])
    @patch("metabolon.organelles.engram._history_files")
    def test_finds_match(self, mock_hf, mock_iter):
        ts_ms = _FIXED_MS
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        data = json.dumps({"timestamp": ts_ms, "display": "findme please", "sessionId": "sess1"}) + "\n"
        mock_path.open.return_value.__enter__ = lambda s: StringIO(data)
        mock_path.open.return_value.__exit__ = MagicMock(return_value=False)
        mock_hf.return_value = [("Claude", mock_path)]

        regex = re.compile("findme", re.IGNORECASE)
        start, end = _date_to_range_ms("2025-06-15")
        results = _search_prompts(regex, start, end, None, None, None)
        assert len(results) == 1
        assert "findme" in results[0].snippet

    @patch("metabolon.organelles.engram._iter_opencode_messages", return_value=[])
    @patch("metabolon.organelles.engram._history_files")
    def test_role_filter_non_user_returns_empty(self, mock_hf, mock_iter):
        regex = re.compile("anything", re.IGNORECASE)
        start, end = _date_to_range_ms("2025-06-15")
        results = _search_prompts(regex, start, end, None, "claude", None)
        assert results == []


# ---------------------------------------------------------------------------
# _search_transcripts
# ---------------------------------------------------------------------------


class TestSearchTranscripts:
    @patch("metabolon.organelles.engram._iter_opencode_messages", return_value=[])
    @patch("metabolon.organelles.engram._projects_dir")
    @patch("metabolon.organelles.engram._opencode_storage")
    def test_searches_claude_transcripts(self, mock_os, mock_pd, mock_iter):
        ts_iso = "2025-06-15T14:30:00+08:00"
        entry = {
            "type": "user",
            "timestamp": ts_iso,
            "sessionId": "sess-transcript-1",
            "message": {
                "content": [{"type": "text", "text": "search for this pattern"}],
            },
        }
        data = json.dumps(entry) + "\n"

        # Build mock jsonl file with proper stat
        mock_jsonl = MagicMock(spec=Path)
        mock_jsonl.suffix = ".jsonl"
        mock_jsonl.stem = "session-abc"
        stat_result = MagicMock()
        stat_result.st_mtime = _FIXED_MS / 1000
        mock_jsonl.stat.return_value = stat_result
        mock_jsonl.open.return_value.__enter__ = lambda s: StringIO(data)
        mock_jsonl.open.return_value.__exit__ = MagicMock(return_value=False)

        # Mock project dir
        mock_proj_dir = MagicMock()
        mock_proj_dir.is_dir.return_value = True
        mock_proj_dir.iterdir.return_value = [mock_jsonl]

        mock_projects = MagicMock()
        mock_projects.exists.return_value = True
        mock_projects.iterdir.return_value = [mock_proj_dir]
        mock_pd.return_value = mock_projects

        mock_os.return_value = Path("/fake/opencode")

        regex = re.compile("pattern", re.IGNORECASE)
        start, end = _date_to_range_ms("2025-06-15")

        results = _search_transcripts(regex, start, end, None, None, None)
        assert len(results) == 1
        assert results[0].role == "you"


# ---------------------------------------------------------------------------
# _scan_opencode
# ---------------------------------------------------------------------------


class TestScanOpencode:
    @patch("metabolon.organelles.engram._opencode_storage", return_value=Path("/fake/opencode"))
    @patch("metabolon.organelles.engram._iter_opencode_messages")
    @patch("metabolon.organelles.engram._read_opencode_text")
    def test_scans_user_messages(self, mock_read, mock_iter, mock_storage):
        ts_ms = _FIXED_MS
        mock_iter.return_value = [
            ("sess-oc-1234", {"role": "user", "id": "msg-1"}, ts_ms),
            ("sess-oc-1234", {"role": "assistant", "id": "msg-2"}, ts_ms),
        ]
        mock_read.return_value = "my prompt text"

        storage = Path("/fake/opencode")
        result = _scan_opencode(0, ts_ms + 1)
        # Only user messages should be included
        assert len(result) == 1
        assert result[0].prompt == "my prompt text"
        assert result[0].tool == "OpenCode"

    @patch("metabolon.organelles.engram._opencode_storage", return_value=Path("/fake/opencode"))
    @patch("metabolon.organelles.engram._iter_opencode_messages")
    @patch("metabolon.organelles.engram._read_opencode_text")
    def test_empty_text_skipped(self, mock_read, mock_iter, mock_storage):
        ts_ms = _FIXED_MS
        mock_iter.return_value = [
            ("sess-oc-1234", {"role": "user", "id": "msg-1"}, ts_ms),
        ]
        mock_read.return_value = ""

        result = _scan_opencode(0, ts_ms + 1)
        assert result == []


# ---------------------------------------------------------------------------
# _print_scan / _print_json_scan
# ---------------------------------------------------------------------------


class TestPrintScan:
    def test_print_scan_output(self, capsys):
        prompts = [
            EngramRecord(
                time_str="14:30",
                timestamp_ms=_FIXED_MS,
                session="sess-abc",
                session_full="sess-abc12345",
                prompt="hello world",
                tool="Claude",
            ),
        ]
        _print_scan(prompts, "2025-06-15", full=False)
        captured = capsys.readouterr()
        assert "Date: 2025-06-15" in captured.out
        assert "Total: 1 prompts" in captured.out
        assert "hello world" in captured.out

    def test_print_json_scan_output(self, capsys):
        prompts = [
            EngramRecord(
                time_str="14:30",
                timestamp_ms=_FIXED_MS,
                session="sess-abc",
                session_full="sess-abc12345",
                prompt="test prompt",
                tool="Claude",
            ),
        ]
        _print_json_scan(prompts, "2025-06-15")
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["date"] == "2025-06-15"
        assert parsed["total"] == 1
        assert parsed["prompts"][0]["prompt"] == "test prompt"


# ---------------------------------------------------------------------------
# _print_search / _print_json_search
# ---------------------------------------------------------------------------


class TestPrintSearch:
    def test_print_search_with_matches(self, capsys):
        regex = re.compile("test", re.IGNORECASE)
        matches = [
            TraceFragment(
                date="2025-06-15",
                time_str="14:30",
                timestamp_ms=_FIXED_MS,
                session="sess-ab",
                role="you",
                snippet="this is a test match",
                tool="Claude",
            ),
        ]
        _print_search(matches, regex, "test", 7, deep=True, role_filter=None, session_filter=None, context_lines=0)
        captured = capsys.readouterr()
        assert "Found 1 matches" in captured.out
        assert "2025-06-15" in captured.out

    def test_print_search_no_matches(self, capsys):
        regex = re.compile("test", re.IGNORECASE)
        _print_search([], regex, "test", 7, deep=False, role_filter=None, session_filter=None, context_lines=0)
        captured = capsys.readouterr()
        assert "No matches found" in captured.out

    def test_print_json_search_output(self, capsys):
        matches = [
            TraceFragment(
                date="2025-06-15",
                time_str="14:30",
                timestamp_ms=_FIXED_MS,
                session="sess-ab",
                role="you",
                snippet="test snippet",
                tool="Claude",
            ),
        ]
        _print_json_search(matches)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert len(parsed) == 1
        assert parsed[0]["snippet"] == "test snippet"


# ---------------------------------------------------------------------------
# Public API: scan()
# ---------------------------------------------------------------------------


class TestScanApi:
    @patch("metabolon.organelles.engram._scan_history", return_value=[])
    @patch("metabolon.organelles.engram._resolve_date", return_value="2025-06-15")
    def test_scan_delegates(self, mock_rd, mock_sh):
        result = scan(date="2025-06-15")
        mock_sh.assert_called_once_with("2025-06-15", None)

    @patch("metabolon.organelles.engram._scan_history", return_value=[])
    @patch("metabolon.organelles.engram._resolve_date", return_value="2025-06-15")
    def test_scan_with_tool_filter(self, mock_rd, mock_sh):
        scan(date="2025-06-15", tool="Claude")
        mock_sh.assert_called_once_with("2025-06-15", "Claude")


# ---------------------------------------------------------------------------
# Public API: search()
# ---------------------------------------------------------------------------


class TestSearchApi:
    @patch("metabolon.organelles.engram._fuzzy_search", return_value=[])
    @patch("metabolon.organelles.engram._search_transcripts", return_value=[])
    @patch("metabolon.organelles.engram._search_prompts", return_value=[])
    @patch("metabolon.organelles.engram._now_hkt", return_value=_FIXED_HKT)
    def test_search_deep(self, mock_now, mock_sp, mock_st, mock_fz):
        result = search("pattern", days=7, deep=True)
        mock_st.assert_called_once()
        assert result == []

    @patch("metabolon.organelles.engram._fuzzy_search", return_value=[])
    @patch("metabolon.organelles.engram._search_transcripts", return_value=[])
    @patch("metabolon.organelles.engram._search_prompts", return_value=[])
    @patch("metabolon.organelles.engram._now_hkt", return_value=_FIXED_HKT)
    def test_search_prompts_only(self, mock_now, mock_sp, mock_st, mock_fz):
        result = search("pattern", days=7, deep=False)
        mock_sp.assert_called_once()

    @patch("metabolon.organelles.engram._now_hkt", return_value=_FIXED_HKT)
    def test_search_invalid_regex(self, mock_now):
        with pytest.raises(ValueError, match="Invalid regex"):
            search("[invalid")

    @patch("metabolon.organelles.engram._fuzzy_search")
    @patch("metabolon.organelles.engram._search_prompts", return_value=[])
    @patch("metabolon.organelles.engram._now_hkt", return_value=_FIXED_HKT)
    def test_fuzzy_fallback_on_plain_word(self, mock_now, mock_sp, mock_fz):
        mock_fz.return_value = [
            TraceFragment(
                date="2025-06-15",
                time_str="14:30",
                timestamp_ms=_FIXED_MS,
                session="sess-fz",
                role="note",
                snippet="Fuzzy match",
                tool="engram",
            ),
        ]
        result = search("helo", days=7, deep=False)
        mock_fz.assert_called_once()
        assert len(result) == 1

    @patch("metabolon.organelles.engram._search_prompts", return_value=[])
    @patch("metabolon.organelles.engram._now_hkt", return_value=_FIXED_HKT)
    def test_no_fuzzy_for_regex_pattern(self, mock_now, mock_sp):
        # pattern with regex metachar should NOT trigger fuzzy fallback
        result = search("test.*", days=7, deep=False)
        # _search_prompts returns [], and fuzzy should not be invoked
        assert result == []


# ---------------------------------------------------------------------------
# EngramRecord dataclass
# ---------------------------------------------------------------------------


class TestEngramRecord:
    def test_fields(self):
        r = EngramRecord(
            time_str="14:30",
            timestamp_ms=_FIXED_MS,
            session="sess-ab",
            session_full="sess-abc123",
            prompt="hello",
            tool="Claude",
        )
        assert r.time_str == "14:30"
        assert r.prompt == "hello"


# ---------------------------------------------------------------------------
# TraceFragment dataclass
# ---------------------------------------------------------------------------


class TestTraceFragment:
    def test_fields(self):
        f = TraceFragment(
            date="2025-06-15",
            time_str="14:30",
            timestamp_ms=_FIXED_MS,
            session="sess-ab",
            role="you",
            snippet="test",
            tool="Claude",
        )
        assert f.context_before == []
        assert f.context_after == []
        assert f.match_line == ""

    def test_with_context(self):
        f = TraceFragment(
            date="2025-06-15",
            time_str="14:30",
            timestamp_ms=_FIXED_MS,
            session="sess-ab",
            role="you",
            snippet="test",
            tool="Claude",
            match_line="test line",
            context_before=["before1"],
            context_after=["after1"],
        )
        assert f.match_line == "test line"
        assert f.context_before == ["before1"]
        assert f.context_after == ["after1"]


# ---------------------------------------------------------------------------
# _iter_opencode_messages
# ---------------------------------------------------------------------------


class TestIterOpencodeMessages:
    @patch("metabolon.organelles.engram._opencode_storage")
    def test_no_session_dir(self, mock_os):
        storage = MagicMock()
        session_dir = MagicMock()
        session_dir.exists.return_value = False
        storage.__truediv__ = MagicMock(return_value=session_dir)
        storage.__getattr__ = lambda self, name: MagicMock()
        mock_os.return_value = storage
        results = list(_iter_opencode_messages(0, 9999999999999, None))
        assert results == []


# ---------------------------------------------------------------------------
# _read_opencode_text
# ---------------------------------------------------------------------------


class TestReadOpencodeText:
    def test_missing_part_dir(self):
        storage = MagicMock()
        part_dir = MagicMock()
        part_dir.exists.return_value = False
        storage.__truediv__ = MagicMock(return_value=part_dir)
        result = _read_opencode_text.__wrapped__(storage, "msg-1") if hasattr(_read_opencode_text, '__wrapped__') else ""
        # Call with a mock storage that returns non-existent part dir
        from metabolon.organelles.engram import _read_opencode_text as _rot
        mock_storage = MagicMock()
        mock_part_dir = MagicMock()
        mock_part_dir.exists.return_value = False
        mock_storage.__truediv__ = MagicMock(return_value=mock_part_dir)
        assert _rot(mock_storage, "msg-1") == ""


# ---------------------------------------------------------------------------
# _fuzzy_search
# ---------------------------------------------------------------------------


class TestFuzzySearch:
    @patch("metabolon.organelles.engram._collect_words_from_transcripts", return_value=set())
    def test_no_candidates(self, mock_cw):
        result = _fuzzy_search("test", 0, 9999999999999, None, None, None, deep=False)
        assert result == []

    @patch("metabolon.organelles.engram._search_prompts")
    @patch("metabolon.organelles.engram._collect_words_from_transcripts")
    def test_fuzzy_returns_matches_with_note(self, mock_cw, mock_sp):
        mock_cw.return_value = {"hello", "world", "testing"}
        mock_sp.return_value = [
            TraceFragment(
                date="2025-06-15",
                time_str="14:30",
                timestamp_ms=_FIXED_MS,
                session="sess-ab",
                role="you",
                snippet="testing result",
                tool="Claude",
            ),
        ]
        result = _fuzzy_search("testng", 0, 9999999999999, None, None, None, deep=False)
        assert len(result) == 2  # 1 note + 1 match
        assert result[0].role == "note"
        assert "Fuzzy match" in result[0].snippet

    @patch("metabolon.organelles.engram._search_transcripts")
    @patch("metabolon.organelles.engram._collect_words_from_transcripts")
    def test_fuzzy_deep_mode(self, mock_cw, mock_st):
        mock_cw.return_value = {"hello", "world", "testing"}
        mock_st.return_value = [
            TraceFragment(
                date="2025-06-15",
                time_str="14:30",
                timestamp_ms=_FIXED_MS,
                session="sess-ab",
                role="you",
                snippet="testing result",
                tool="Claude",
            ),
        ]
        result = _fuzzy_search("testng", 0, 9999999999999, None, None, None, deep=True)
        mock_st.assert_called_once()
        assert len(result) == 2
