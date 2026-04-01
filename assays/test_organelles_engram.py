from __future__ import annotations

"""Tests for metabolon/organelles/engram.py — chat session archive search."""

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
    _parse_rfc3339,
    _resolve_date,
    scan,
    search,
)

_HKT = timezone(timedelta(hours=8))


# ── Time helpers ────────────────────────────────────────────────────────────


class TestResolveDate:
    """Tests for _resolve_date."""

    def test_yyyy_mm_dd_passthrough(self):
        assert _resolve_date("2025-06-15") == "2025-06-15"

    def test_today(self):
        with patch("metabolon.organelles.engram._now_hkt") as mock_now:
            mock_now.return_value = datetime(2025, 6, 15, 10, 30, tzinfo=_HKT)
            assert _resolve_date("today") == "2025-06-15"

    def test_yesterday(self):
        with patch("metabolon.organelles.engram._now_hkt") as mock_now:
            mock_now.return_value = datetime(2025, 6, 15, 10, 30, tzinfo=_HKT)
            assert _resolve_date("yesterday") == "2025-06-14"

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            _resolve_date("15-06-2025")

    def test_garbage_raises(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            _resolve_date("not-a-date")


class TestDateToRangeMs:
    """Tests for _date_to_range_ms."""

    def test_midnight_to_midnight(self):
        start, end = _date_to_range_ms("2025-06-15")
        # start should be 2025-06-15 00:00 HKT, end 2025-06-16 00:00 HKT
        assert end - start == 86400_000  # exactly 1 day in ms

    def test_start_before_end(self):
        start, end = _date_to_range_ms("2025-01-01")
        assert start < end


class TestMsToHkt:
    """Tests for _ms_to_hkt."""

    def test_roundtrip(self):
        dt = datetime(2025, 6, 15, 8, 0, 0, tzinfo=_HKT)
        ms = int(dt.timestamp() * 1000)
        result = _ms_to_hkt(ms)
        assert result.tzinfo == _HKT
        assert result.hour == 8
        assert result.day == 15


class TestParseRfc3339:
    """Tests for _parse_rfc3339."""

    def test_utc_z_suffix(self):
        dt = _parse_rfc3339("2025-06-15T08:30:00Z")
        assert dt is not None
        assert dt.hour == 8
        assert dt.minute == 30

    def test_with_offset(self):
        dt = _parse_rfc3339("2025-06-15T08:30:00+08:00")
        assert dt is not None

    def test_invalid_returns_none(self):
        assert _parse_rfc3339("garbage") is None

    def test_empty_returns_none(self):
        assert _parse_rfc3339("") is None


# ── Content extraction ──────────────────────────────────────────────────────


class TestExtractText:
    """Tests for _extract_text."""

    def test_string_passthrough(self):
        assert _extract_text("hello world") == "hello world"

    def test_text_block(self):
        content = [{"type": "text", "text": "hello"}]
        assert _extract_text(content) == "hello"

    def test_tool_use_block(self):
        content = [{"type": "tool_use", "name": "bash"}]
        assert _extract_text(content) == "[tool: bash]"

    def test_mixed_blocks(self):
        content = [
            {"type": "text", "text": "run it"},
            {"type": "tool_use", "name": "bash"},
            {"type": "text", "text": "done"},
        ]
        assert _extract_text(content) == "run it [tool: bash] done"

    def test_empty_list(self):
        assert _extract_text([]) == ""

    def test_non_dict_items_ignored(self):
        content = ["str_item", 42, {"type": "text", "text": "ok"}]
        assert _extract_text(content) == "ok"

    def test_none_returns_empty(self):
        assert _extract_text(None) == ""

    def test_int_returns_empty(self):
        assert _extract_text(42) == ""

    def test_text_block_empty_text_ignored(self):
        content = [{"type": "text", "text": ""}]
        assert _extract_text(content) == ""

    def test_unknown_block_type_ignored(self):
        content = [{"type": "image", "data": "..."}]
        assert _extract_text(content) == ""


# ── Snippet helpers ─────────────────────────────────────────────────────────


class TestMakeSnippet:
    """Tests for _make_snippet."""

    def test_short_text_full(self):
        text = "hello world"
        result = _make_snippet(text, 0, 5)
        assert "hello" in result
        assert not result.startswith("...")
        assert not result.endswith("...")

    def test_long_text_start_ellipsis(self):
        text = "x" * 200
        # match at end
        result = _make_snippet(text, 180, 195)
        assert result.startswith("...")

    def test_long_text_end_ellipsis(self):
        text = "y" * 200
        # match at start
        result = _make_snippet(text, 0, 5)
        assert result.endswith("...")

    def test_newlines_replaced(self):
        text = "line1\nline2\nline3"
        result = _make_snippet(text, 0, 5)
        assert "\n" not in result


class TestMakeLineContext:
    """Tests for _make_line_context."""

    def test_empty_text(self):
        line, before, after = _make_line_context("", 0, 0)
        assert line == ""
        assert before == []
        assert after == []

    def test_single_line(self):
        text = "hello world"
        # _make_line_context(text, match_start, context_lines)
        line, before, after = _make_line_context(text, 0, 2)
        assert line == "hello world"
        assert before == []
        assert after == []

    def test_multi_line_with_context(self):
        text = "line0\nline1\nline2\nline3\nline4"
        # match_start=12 is inside "line2" (offset: line0=0, line1=6, line2=12)
        line, before, after = _make_line_context(text, 12, 1)
        assert line == "line2"
        assert before == ["line1"]
        assert after == ["line3"]

    def test_zero_context_lines(self):
        text = "a\nb\nc"
        # match_start=2 is inside "b" (a=0, b=2)
        line, before, after = _make_line_context(text, 2, 0)
        assert line == "b"
        assert before == []
        assert after == []


# ── Role matching ───────────────────────────────────────────────────────────


class TestMatchesRole:
    """Tests for _matches_role."""

    @pytest.mark.parametrize(
        "filt,expected",
        [
            ("you", True),
            ("user", True),
            ("me", True),
            ("You", True),
            ("claude", False),
        ],
    )
    def test_user_roles(self, filt, expected):
        assert _matches_role("you", filt) is expected

    @pytest.mark.parametrize(
        "filt,expected",
        [
            ("claude", True),
            ("assistant", True),
            ("ai", True),
            ("you", False),
        ],
    )
    def test_assistant_roles(self, filt, expected):
        assert _matches_role("claude", filt) is expected

    def test_opencode_role(self):
        assert _matches_role("opencode", "opencode") is True
        assert _matches_role("opencode", "claude") is True  # opencode matches assistant
        assert _matches_role("opencode", "you") is False

    def test_case_insensitive(self):
        assert _matches_role("you", "USER") is True
        assert _matches_role("claude", "ASSISTANT") is True

    def test_exact_match_fallback(self):
        assert _matches_role("custom", "custom") is True
        assert _matches_role("custom", "other") is False


# ── Color / highlight ──────────────────────────────────────────────────────


class TestColorEnabled:
    def test_no_color_env(self):
        with patch.dict("os.environ", {"NO_COLOR": "1"}):
            assert _color_enabled() is False

    def test_no_tty(self):
        with patch("sys.stdout") as mock_out:
            mock_out.isatty.return_value = False
            assert _color_enabled() is False


class TestHighlightMatches:
    def test_color_false_returns_original(self):
        text = "hello world"
        regex = re.compile("world")
        assert _highlight_matches(text, regex, color=False) == text

    def test_empty_text(self):
        regex = re.compile("test")
        assert _highlight_matches("", regex, color=True) == ""

    def test_highlights_match(self):
        text = "find the needle here"
        regex = re.compile("needle")
        result = _highlight_matches(text, regex, color=True)
        assert "\033[1;31m" in result
        assert "\033[0m" in result
        assert "needle" in result

    def test_no_match_returns_original(self):
        text = "nothing to see"
        regex = re.compile("missing")
        assert _highlight_matches(text, regex, color=True) == text


# ── Plain word detection ───────────────────────────────────────────────────


class TestIsPlainWord:
    def test_simple_word(self):
        assert _is_plain_word("hello") is True

    def test_word_with_hyphen(self):
        assert _is_plain_word("my-variable") is True

    def test_regex_chars(self):
        assert _is_plain_word("test.*") is False
        assert _is_plain_word("a|b") is False
        assert _is_plain_word("(group)") is False


# ── Data structures ─────────────────────────────────────────────────────────


class TestEngramRecord:
    def test_fields(self):
        r = EngramRecord(
            time_str="10:30",
            timestamp_ms=1000,
            session="abcd1234",
            session_full="abcd12345678",
            prompt="hello",
            tool="Claude",
        )
        assert r.time_str == "10:30"
        assert r.tool == "Claude"


class TestTraceFragment:
    def test_defaults(self):
        f = TraceFragment(
            date="2025-06-15",
            time_str="10:30",
            timestamp_ms=1000,
            session="abcd1234",
            role="you",
            snippet="hello",
            tool="Claude",
        )
        assert f.match_line == ""
        assert f.context_before == []
        assert f.context_after == []


# ── Scan (with mocked file reads) ──────────────────────────────────────────


class TestScanHistory:
    """Tests for _scan_history via public scan() function."""

    @patch("metabolon.organelles.engram._scan_history")
    @patch("metabolon.organelles.engram._resolve_date")
    def test_scan_today(self, mock_resolve, mock_scan):
        mock_resolve.return_value = "2025-06-15"
        mock_scan.return_value = []
        result = scan()
        mock_resolve.assert_called_once_with("today")
        assert result == []

    @patch("metabolon.organelles.engram._scan_history")
    @patch("metabolon.organelles.engram._resolve_date")
    def test_scan_specific_date(self, mock_resolve, mock_scan):
        mock_resolve.return_value = "2025-06-15"
        mock_scan.return_value = [
            EngramRecord("10:00", 1000, "sess1234", "sess12345678", "hi", "Claude")
        ]
        result = scan(date="2025-06-15")
        assert len(result) == 1
        assert result[0].prompt == "hi"


class TestScanHistoryInternal:
    """Tests for _scan_history with mocked filesystem."""

    def _make_entry(self, ts_ms, session="sess1", display="prompt text"):
        return json.dumps({
            "timestamp": ts_ms,
            "sessionId": session,
            "display": display,
        })

    @patch("metabolon.organelles.engram._opencode_storage")
    @patch("metabolon.organelles.engram._history_files")
    def test_reads_history_file(self, mock_hf, mock_os):
        from metabolon.organelles.engram import _scan_history

        mock_os.return_value = Path("/fake/opencode")
        # Create a fake file content
        lines = [
            self._make_entry(1718409600000, "sessAAA", "first prompt"),
            self._make_entry(1718413200000, "sessAAA", "second prompt"),
            "",  # empty line skipped
            "bad json{",  # invalid json skipped
        ]
        content = "\n".join(lines)

        fake_path = MagicMock()
        fake_path.exists.return_value = True
        fake_path.open.return_value.__enter__ = lambda s: iter(content.splitlines())
        fake_path.open.return_value.__exit__ = MagicMock(return_value=False)
        # Make the context manager work with 'for line in f'
        fake_path.open.return_value.__iter__ = lambda s: iter(content.splitlines())
        mock_hf.return_value = [("Claude", fake_path)]

        # 2025-06-15 in HKT
        result = _scan_history("2025-06-15")
        assert isinstance(result, list)

    @patch("metabolon.organelles.engram._opencode_storage")
    @patch("metabolon.organelles.engram._history_files")
    def test_tool_filter(self, mock_hf, mock_os):
        from metabolon.organelles.engram import _scan_history

        mock_os.return_value = Path("/fake/opencode")
        claude_path = MagicMock()
        claude_path.exists.return_value = True
        claude_path.open.return_value.__iter__ = lambda s: iter([])
        codex_path = MagicMock()
        codex_path.exists.return_value = True
        codex_path.open.return_value.__iter__ = lambda s: iter([])
        mock_hf.return_value = [("Claude", claude_path), ("Codex", codex_path)]

        result = _scan_history("2025-06-15", tool_filter="Codex")
        # Claude path should be skipped
        claude_path.open.assert_not_called()
        codex_path.open.assert_called_once()


# ── Search (with mocked internals) ─────────────────────────────────────────


class TestSearch:
    """Tests for the public search() function."""

    @patch("metabolon.organelles.engram._search_transcripts")
    @patch("metabolon.organelles.engram._now_hkt")
    def test_search_deep(self, mock_now, mock_st):
        mock_now.return_value = datetime(2025, 6, 15, 12, 0, tzinfo=_HKT)
        frag = TraceFragment(
            date="2025-06-14",
            time_str="10:00",
            timestamp_ms=1000,
            session="abcd1234",
            role="claude",
            snippet="found it",
            tool="Claude",
        )
        mock_st.return_value = [frag]
        results = search("found", deep=True)
        assert len(results) == 1
        assert results[0].snippet == "found it"

    @patch("metabolon.organelles.engram._search_prompts")
    @patch("metabolon.organelles.engram._now_hkt")
    def test_search_prompts_only(self, mock_now, mock_sp):
        mock_now.return_value = datetime(2025, 6, 15, 12, 0, tzinfo=_HKT)
        mock_sp.return_value = []
        results = search("missing", deep=False)
        assert results == []

    def test_search_invalid_regex(self):
        with pytest.raises(ValueError, match="Invalid regex"):
            search("[invalid")


# ── _search_prompts internal ───────────────────────────────────────────────


class TestSearchPrompts:
    """Tests for _search_prompts with mocked filesystem."""

    @patch("metabolon.organelles.engram._opencode_storage")
    @patch("metabolon.organelles.engram._history_files")
    def test_finds_match_in_history(self, mock_hf, mock_os):
        from metabolon.organelles.engram import _search_prompts
        from io import StringIO

        mock_os.return_value = Path("/fake/opencode")
        ts_ms = 1718409600000  # some timestamp in range
        entry = json.dumps({
            "timestamp": ts_ms,
            "sessionId": "sessABC1",
            "display": "deploy the application now",
        })
        fake_path = MagicMock()
        fake_path.exists.return_value = True
        fake_path.open.return_value.__enter__ = lambda s: StringIO(entry)
        fake_path.open.return_value.__exit__ = MagicMock(return_value=False)
        mock_hf.return_value = [("Claude", fake_path)]

        # Use wide time range
        start_ms = ts_ms - 86400_000
        end_ms = ts_ms + 86400_000
        regex = re.compile("deploy", re.IGNORECASE)
        results = _search_prompts(regex, start_ms, end_ms, None, None, None)
        assert len(results) == 1
        assert results[0].role == "you"
        assert "deploy" in results[0].snippet

    @patch("metabolon.organelles.engram._opencode_storage")
    @patch("metabolon.organelles.engram._history_files")
    def test_role_filter_skips_prompts(self, mock_hf, mock_os):
        from metabolon.organelles.engram import _search_prompts

        mock_os.return_value = Path("/fake/opencode")
        # When role filter is "claude", prompts (always role "you") should be skipped
        regex = re.compile("anything", re.IGNORECASE)
        results = _search_prompts(regex, 0, 9999999999999, None, "claude", None)
        assert results == []


# ── _search_transcripts internal ────────────────────────────────────────────


class TestSearchTranscripts:
    """Tests for _search_transcripts with mocked filesystem."""

    @patch("metabolon.organelles.engram._opencode_storage")
    @patch("metabolon.organelles.engram._history_files")
    def test_claude_transcript_match(self, mock_hf, mock_os):
        from metabolon.organelles.engram import _search_transcripts
        import os
        import tempfile

        mock_os.return_value = Path("/fake/opencode")
        mock_hf.return_value = []

        # Build a fake transcript entry
        ts_str = "2025-06-15T10:30:00+08:00"
        entry = json.dumps({
            "type": "user",
            "timestamp": ts_str,
            "sessionId": "sessXYZ123456",
            "message": {
                "content": [{"type": "text", "text": "please refactor the module"}]
            },
        })

        ts_ms = int(datetime.fromisoformat(ts_str).timestamp() * 1000)

        with tempfile.TemporaryDirectory() as tmpdir:
            proj_dir = Path(tmpdir) / "test-project"
            proj_dir.mkdir()
            jsonl_file = proj_dir / "sessXYZ123456.jsonl"
            jsonl_file.write_text(entry + "\n")
            # Set mtime to match the timestamp epoch so it falls within the range
            epoch = ts_ms // 1000
            os.utime(jsonl_file, (epoch, epoch))

            with patch("metabolon.organelles.engram._projects_dir", return_value=Path(tmpdir)):
                start_ms = ts_ms - 86400_000
                end_ms = ts_ms + 86400_000
                regex = re.compile("refactor", re.IGNORECASE)
                results = _search_transcripts(regex, start_ms, end_ms, None, None, None)
                assert len(results) == 1
                assert results[0].role == "you"
                assert "refactor" in results[0].snippet

    @patch("metabolon.organelles.engram._opencode_storage")
    @patch("metabolon.organelles.engram._history_files")
    def test_tool_filter_skips_non_matching(self, mock_hf, mock_os):
        from metabolon.organelles.engram import _search_transcripts

        mock_os.return_value = Path("/fake/opencode")
        mock_hf.return_value = []
        regex = re.compile("anything", re.IGNORECASE)
        # tool_filter="OpenCode" should skip Claude transcripts
        results = _search_transcripts(regex, 0, 9999999999999, "OpenCode", None, None)
        assert results == []  # no Claude scan happened


# ── Fuzzy search ────────────────────────────────────────────────────────────


class TestFuzzySearch:
    """Tests for _fuzzy_search."""

    @patch("metabolon.organelles.engram._collect_words_from_transcripts")
    def test_no_candidates_returns_empty(self, mock_collect):
        from metabolon.organelles.engram import _fuzzy_search

        mock_collect.return_value = set()
        result = _fuzzy_search("test", 0, 9999999999999, None, None, None, deep=False)
        assert result == []

    @patch("metabolon.organelles.engram._search_prompts")
    @patch("metabolon.organelles.engram._collect_words_from_transcripts")
    def test_fuzzy_returns_note_fragment(self, mock_collect, mock_sp):
        from metabolon.organelles.engram import _fuzzy_search

        mock_collect.return_value = {"testing", "tester", "tested"}
        frag = TraceFragment(
            date="2025-06-15",
            time_str="10:00",
            timestamp_ms=1000,
            session="abcd1234",
            role="you",
            snippet="testing here",
            tool="Claude",
        )
        mock_sp.return_value = [frag]
        results = _fuzzy_search("tset", 0, 9999999999999, None, None, None, deep=False)
        # First result should be the fuzzy note
        assert len(results) >= 2
        assert results[0].role == "note"
        assert "Fuzzy match" in results[0].snippet


# ── OpenCode helpers ────────────────────────────────────────────────────────


class TestReadOpencodeText:
    """Tests for _read_opencode_text."""

    def test_missing_dir_returns_empty(self):
        from metabolon.organelles.engram import _read_opencode_text

        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            result = _read_opencode_text(Path(tmpdir), "nonexistent")
            assert result == ""

    def test_reads_parts(self):
        from metabolon.organelles.engram import _read_opencode_text

        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            part_dir = Path(tmpdir) / "part" / "msg1"
            part_dir.mkdir(parents=True)
            (part_dir / "001.json").write_text(json.dumps({"text": "hello "}))
            (part_dir / "002.json").write_text(json.dumps({"text": "world"}))
            result = _read_opencode_text(Path(tmpdir), "msg1")
            assert result == "hello world"


# ── Print helpers ───────────────────────────────────────────────────────────


class TestPrintScan:
    def test_empty_prompts(self, capsys):
        from metabolon.organelles.engram import _print_scan

        _print_scan([], "2025-06-15", full=False)
        captured = capsys.readouterr()
        assert "Date: 2025-06-15" in captured.out
        assert "Total: 0 prompts" in captured.out

    def test_with_prompts(self, capsys):
        from metabolon.organelles.engram import _print_scan

        records = [
            EngramRecord("10:00", 1000, "abcd1234", "abcd12345678", "test prompt here", "Claude"),
        ]
        _print_scan(records, "2025-06-15", full=True)
        captured = capsys.readouterr()
        assert "test prompt here" in captured.out
        assert "Claude" in captured.out


class TestPrintSearch:
    def test_no_matches(self, capsys):
        from metabolon.organelles.engram import _print_search

        regex = re.compile("test")
        _print_search([], regex, "test", days=7, deep=True, role_filter=None, session_filter=None, context_lines=0)
        captured = capsys.readouterr()
        assert "No matches found" in captured.out

    def test_with_matches(self, capsys):
        from metabolon.organelles.engram import _print_search

        regex = re.compile("needle")
        matches = [
            TraceFragment(
                date="2025-06-14",
                time_str="10:00",
                timestamp_ms=1000,
                session="abcd1234",
                role="you",
                snippet="find the needle here",
                tool="Claude",
            ),
        ]
        _print_search(matches, regex, "needle", days=7, deep=False, role_filter=None, session_filter=None, context_lines=0)
        captured = capsys.readouterr()
        assert "Found 1 matches" in captured.out
        assert "2025-06-14" in captured.out


class TestPrintJsonScan:
    def test_outputs_valid_json(self, capsys):
        from metabolon.organelles.engram import _print_json_scan

        records = [
            EngramRecord("10:00", 1000, "abcd1234", "abcd12345678", "hi", "Claude"),
        ]
        _print_json_scan(records, "2025-06-15")
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["date"] == "2025-06-15"
        assert data["total"] == 1
        assert len(data["prompts"]) == 1


class TestPrintJsonSearch:
    def test_outputs_valid_json(self, capsys):
        from metabolon.organelles.engram import _print_json_search

        fragments = [
            TraceFragment(
                date="2025-06-15",
                time_str="10:00",
                timestamp_ms=1000,
                session="abcd1234",
                role="you",
                snippet="test",
                tool="Claude",
            ),
        ]
        _print_json_search(fragments)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert data[0]["snippet"] == "test"


# ── CLI ─────────────────────────────────────────────────────────────────────


class TestCli:
    """Test _cli entry point with mocked internals."""

    @patch("metabolon.organelles.engram._scan_history")
    @patch("metabolon.organelles.engram._resolve_date")
    def test_cli_scan_default(self, mock_resolve, mock_scan, capsys):
        from metabolon.organelles.engram import _cli

        mock_resolve.return_value = "2025-06-15"
        mock_scan.return_value = []

        with patch("sys.argv", ["engram", "scan", "today"]):
            _cli()

        captured = capsys.readouterr()
        assert "Date: 2025-06-15" in captured.out

    @patch("metabolon.organelles.engram._scan_history")
    @patch("metabolon.organelles.engram._resolve_date")
    def test_cli_scan_json(self, mock_resolve, mock_scan, capsys):
        from metabolon.organelles.engram import _cli

        mock_resolve.return_value = "2025-06-15"
        mock_scan.return_value = [
            EngramRecord("10:00", 1000, "abcd1234", "abcd12345678", "hi", "Claude"),
        ]

        with patch("sys.argv", ["engram", "scan", "today", "--json"]):
            _cli()

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["total"] == 1

    @patch("metabolon.organelles.engram._search_transcripts")
    @patch("metabolon.organelles.engram._now_hkt")
    def test_cli_search(self, mock_now, mock_st, capsys):
        from metabolon.organelles.engram import _cli

        mock_now.return_value = datetime(2025, 6, 15, 12, 0, tzinfo=_HKT)
        mock_st.return_value = []

        with patch("sys.argv", ["engram", "search", "test"]):
            _cli()

        captured = capsys.readouterr()
        assert "No matches found" in captured.out

    @patch("metabolon.organelles.engram._resolve_date")
    def test_cli_invalid_date_exits(self, mock_resolve, capsys):
        from metabolon.organelles.engram import _cli

        mock_resolve.side_effect = ValueError("Invalid date format: bad. Use YYYY-MM-DD.")

        with pytest.raises(SystemExit):
            with patch("sys.argv", ["engram", "scan", "bad"]):
                _cli()

    @patch("metabolon.organelles.engram._now_hkt")
    def test_cli_invalid_regex_exits(self, mock_now, capsys):
        from metabolon.organelles.engram import _cli

        mock_now.return_value = datetime(2025, 6, 15, 12, 0, tzinfo=_HKT)

        with pytest.raises(SystemExit):
            with patch("sys.argv", ["engram", "search", "[invalid"]):
                _cli()

    @patch("metabolon.organelles.engram._scan_history")
    @patch("metabolon.organelles.engram._resolve_date")
    def test_cli_no_subcommand_defaults_scan(self, mock_resolve, mock_scan, capsys):
        from metabolon.organelles.engram import _cli

        mock_resolve.return_value = "2025-06-15"
        mock_scan.return_value = []

        with patch("sys.argv", ["engram"]):
            _cli()

        captured = capsys.readouterr()
        assert "Date: 2025-06-15" in captured.out
