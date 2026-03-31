from __future__ import annotations
"""Tests for chat_history.py — Claude/Codex/OpenCode history scanner."""

import json
import subprocess
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest


# ── Module loading ──────────────────────────────────────────────────────

def _load_chat_history():
    """Load chat_history.py by exec-ing its source into a namespace."""
    source = (Path.home() / "germline" / "effectors" / "chat_history.py").read_text()
    ns: dict = {"__name__": "chat_history_test"}
    exec(source, ns)
    return ns


_mod = _load_chat_history()

extract_text_from_content = _mod["extract_text_from_content"]
search_prompts = _mod["search_prompts"]
search_transcripts = _mod["search_transcripts"]
scan_opencode = _mod["scan_opencode"]
scan_history = _mod["scan_history"]
print_results = _mod["print_results"]
print_search_results = _mod["print_search_results"]
HKT = _mod["HKT"]
HISTORY_FILES = _mod["HISTORY_FILES"]
PROJECTS_DIR = _mod["PROJECTS_DIR"]
OPENCODE_STORAGE = _mod["OPENCODE_STORAGE"]

EFFECTOR_PATH = Path.home() / "germline" / "effectors" / "chat_history.py"


# ── Helpers ─────────────────────────────────────────────────────────────

def _hkt_date_str(days_offset: int = 0) -> str:
    """Return YYYY-MM-DD in HKT, offset by days_offset from today."""
    now = datetime.now(HKT) + timedelta(days=days_offset)
    return now.strftime("%Y-%m-%d")


def _hkt_ms(days_offset: int = 0, hour: int = 12) -> int:
    """Return epoch-millisecond for a specific date/hour in HKT."""
    now = datetime.now(HKT)
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=days_offset)
    return int(target.timestamp() * 1000)


def _make_history_jsonl(path: Path, entries: list[dict]) -> None:
    """Write a JSONL history file with given entries."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def _make_session_jsonl(path: Path, entries: list[dict]) -> None:
    """Write a session JSONL file with given entries."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


# ── extract_text_from_content tests ────────────────────────────────────

class TestExtractTextFromContent:
    """Tests for extract_text_from_content helper."""

    def test_string_input(self):
        assert extract_text_from_content("hello world") == "hello world"

    def test_empty_string(self):
        assert extract_text_from_content("") == ""

    def test_list_with_text_blocks(self):
        content = [
            {"type": "text", "text": "Hello"},
            {"type": "text", "text": "World"},
        ]
        assert extract_text_from_content(content) == "Hello World"

    def test_list_with_tool_use(self):
        content = [
            {"type": "text", "text": "Do thing"},
            {"type": "tool_use", "name": "Bash", "input": {"cmd": "ls"}},
        ]
        result = extract_text_from_content(content)
        assert "Do thing" in result
        assert "[tool: Bash]" in result

    def test_list_skips_tool_result(self):
        content = [
            {"type": "text", "text": "prompt"},
            {"type": "tool_result", "content": "noisy output"},
        ]
        result = extract_text_from_content(content)
        assert "prompt" in result
        assert "noisy" not in result

    def test_list_skips_thinking_blocks(self):
        content = [
            {"type": "thinking", "thinking": "inner monologue"},
            {"type": "text", "text": "visible"},
        ]
        result = extract_text_from_content(content)
        assert "visible" in result
        assert "monologue" not in result

    def test_empty_list(self):
        assert extract_text_from_content([]) == ""

    def test_none_input(self):
        assert extract_text_from_content(None) == ""

    def test_integer_input(self):
        assert extract_text_from_content(42) == ""

    def test_text_block_missing_text_key(self):
        content = [{"type": "text"}]
        assert extract_text_from_content(content) == ""

    def test_tool_use_without_name(self):
        content = [{"type": "tool_use"}]
        # Should not crash, and should not append anything
        assert extract_text_from_content(content) == ""


# ── scan_history tests ─────────────────────────────────────────────────

class TestScanHistory:
    """Tests for scan_history function with mock history files."""

    def test_scan_history_finds_prompts(self, tmp_path):
        """scan_history returns prompts from history file for target date."""
        ts = _hkt_ms(0, 10)
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, [
            {"timestamp": ts, "sessionId": "sess1", "display": "hello claude"},
            {"timestamp": ts + 3600000, "sessionId": "sess1", "display": "second prompt"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            result = scan_history(_hkt_date_str(0))
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert result["total"] == 2
        assert result["date"] == _hkt_date_str(0)
        assert any("hello claude" in p["prompt"] for p in result["all_prompts"])

    def test_scan_history_filters_by_date(self, tmp_path):
        """scan_history only returns prompts within the target date in HKT."""
        today_ts = _hkt_ms(0, 10)
        yesterday_ts = _hkt_ms(-1, 10)
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, [
            {"timestamp": yesterday_ts, "sessionId": "old", "display": "yesterday"},
            {"timestamp": today_ts, "sessionId": "new", "display": "today"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            result = scan_history(_hkt_date_str(0))
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert result["total"] == 1
        assert result["all_prompts"][0]["prompt"] == "today"

    def test_scan_history_limit(self, tmp_path):
        """scan_history respects the limit parameter for prompts list."""
        ts = _hkt_ms(0, 10)
        entries = [
            {"timestamp": ts + i * 60000, "sessionId": "s1", "display": f"prompt {i}"}
            for i in range(10)
        ]
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, entries)

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            result = scan_history(_hkt_date_str(0), limit=3)
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert len(result["prompts"]) == 3
        assert result["total"] == 10  # all_prompts has all

    def test_scan_history_limit_zero_returns_all(self, tmp_path):
        """scan_history with limit=0 returns all prompts."""
        ts = _hkt_ms(0, 10)
        entries = [
            {"timestamp": ts + i * 60000, "sessionId": "s1", "display": f"p{i}"}
            for i in range(10)
        ]
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, entries)

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            result = scan_history(_hkt_date_str(0), limit=0)
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert len(result["prompts"]) == 10

    def test_scan_history_sessions_grouped(self, tmp_path):
        """scan_history groups prompts into sessions correctly."""
        ts = _hkt_ms(0, 10)
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, [
            {"timestamp": ts, "sessionId": "aaa111", "display": "p1"},
            {"timestamp": ts + 60000, "sessionId": "aaa111", "display": "p2"},
            {"timestamp": ts + 120000, "sessionId": "bbb222", "display": "p3"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            result = scan_history(_hkt_date_str(0))
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert len(result["sessions"]) == 2
        # First session should have 2 prompts
        session_counts = {s["count"] for s in result["sessions"]}
        assert 2 in session_counts
        assert 1 in session_counts

    def test_scan_history_missing_file(self, tmp_path):
        """scan_history returns empty result when history file doesn't exist."""
        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": tmp_path / "nonexistent.jsonl"}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            result = scan_history(_hkt_date_str(0))
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert result["total"] == 0
        assert result["sessions"] == []

    def test_scan_history_tool_filter(self, tmp_path):
        """scan_history filters by tool when specified."""
        ts = _hkt_ms(0, 10)
        claude_path = tmp_path / ".claude" / "history.jsonl"
        codex_path = tmp_path / ".codex" / "history.jsonl"
        _make_history_jsonl(claude_path, [
            {"timestamp": ts, "sessionId": "c1", "display": "claude prompt"},
        ])
        _make_history_jsonl(codex_path, [
            {"timestamp": ts, "sessionId": "x1", "display": "codex prompt"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": claude_path, "Codex": codex_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            result = scan_history(_hkt_date_str(0), tool="Claude")
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert result["total"] == 1
        assert result["all_prompts"][0]["tool"] == "Claude"

    def test_scan_history_unknown_tool_returns_empty(self, tmp_path):
        """scan_history returns empty when tool doesn't match known tools."""
        ts = _hkt_ms(0, 10)
        claude_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(claude_path, [
            {"timestamp": ts, "sessionId": "c1", "display": "prompt"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": claude_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            result = scan_history(_hkt_date_str(0), tool="UnknownTool")
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert result["total"] == 0

    def test_scan_history_uses_prompt_fallback(self, tmp_path):
        """scan_history falls back to 'prompt' field when 'display' missing."""
        ts = _hkt_ms(0, 10)
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, [
            {"timestamp": ts, "sessionId": "s1", "prompt": "fallback prompt"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            result = scan_history(_hkt_date_str(0))
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert result["total"] == 1
        assert result["all_prompts"][0]["prompt"] == "fallback prompt"

    def test_scan_history_skips_non_int_timestamps(self, tmp_path):
        """scan_history skips entries with non-integer timestamps."""
        ts = _hkt_ms(0, 10)
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, [
            {"timestamp": ts, "sessionId": "s1", "display": "valid"},
            {"timestamp": "not_a_number", "sessionId": "s2", "display": "bad"},
            {"timestamp": 12.5, "sessionId": "s3", "display": "float"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            result = scan_history(_hkt_date_str(0))
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert result["total"] == 1


# ── search_prompts tests ───────────────────────────────────────────────

class TestSearchPrompts:
    """Tests for search_prompts function."""

    def test_search_finds_matching_prompts(self, tmp_path):
        """search_prompts returns prompts matching the pattern."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, [
            {"timestamp": ts, "sessionId": "s1", "display": "find ME please"},
            {"timestamp": ts + 60000, "sessionId": "s1", "display": "no match here"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            matches = search_prompts("find ME", start_ms, end_ms)
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert len(matches) == 1
        assert "find ME" in matches[0]["snippet"]

    def test_search_is_case_insensitive(self, tmp_path):
        """search_prompts matches case-insensitively."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, [
            {"timestamp": ts, "sessionId": "s1", "display": "UPPERCASE word"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            matches = search_prompts("uppercase", start_ms, end_ms)
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert len(matches) == 1

    def test_search_respects_date_range(self, tmp_path):
        """search_prompts only returns results within date range."""
        old_ts = _hkt_ms(-10, 10)
        recent_ts = _hkt_ms(0, 10)
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, [
            {"timestamp": old_ts, "sessionId": "s1", "display": "old keyword match"},
            {"timestamp": recent_ts, "sessionId": "s2", "display": "recent keyword match"},
        ])

        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            matches = search_prompts("keyword", start_ms, end_ms)
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert len(matches) == 1
        assert "recent" in matches[0]["snippet"]

    def test_search_no_results(self, tmp_path):
        """search_prompts returns empty list when nothing matches."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, [
            {"timestamp": ts, "sessionId": "s1", "display": "nothing relevant"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            matches = search_prompts("xyzzy123", start_ms, end_ms)
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert matches == []

    def test_search_respects_limit(self, tmp_path):
        """search_prompts truncates results to limit."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)
        entries = [
            {"timestamp": ts + i * 60000, "sessionId": f"s{i}", "display": f"match number {i}"}
            for i in range(20)
        ]
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, entries)

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            matches = search_prompts("match", start_ms, end_ms, limit=5)
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert len(matches) == 5

    def test_search_tool_filter(self, tmp_path):
        """search_prompts filters by tool name."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)
        claude_path = tmp_path / ".claude" / "history.jsonl"
        codex_path = tmp_path / ".codex" / "history.jsonl"
        _make_history_jsonl(claude_path, [
            {"timestamp": ts, "sessionId": "c1", "display": "claude match"},
        ])
        _make_history_jsonl(codex_path, [
            {"timestamp": ts, "sessionId": "x1", "display": "codex match"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": claude_path, "Codex": codex_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            matches = search_prompts("match", start_ms, end_ms, tool="Codex")
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert len(matches) == 1
        assert matches[0]["tool"] == "Codex"

    def test_search_results_sorted_by_timestamp_desc(self, tmp_path):
        """search_prompts returns results sorted newest first."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, [
            {"timestamp": ts, "sessionId": "s1", "display": "early match"},
            {"timestamp": ts + 3600000, "sessionId": "s2", "display": "later match"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            matches = search_prompts("match", start_ms, end_ms)
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert len(matches) == 2
        assert matches[0]["timestamp"] > matches[1]["timestamp"]

    def test_search_snippet_has_ellipsis(self, tmp_path):
        """search_prompts adds ... when snippet is truncated."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)
        long_prefix = "x" * 100
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, [
            {"timestamp": ts, "sessionId": "s1", "display": f"{long_prefix} keyword here"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            matches = search_prompts("keyword", start_ms, end_ms)
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert len(matches) == 1
        assert "..." in matches[0]["snippet"]

    def test_search_skips_empty_prompts(self, tmp_path):
        """search_prompts skips entries with empty display/prompt."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, [
            {"timestamp": ts, "sessionId": "s1", "display": ""},
            {"timestamp": ts + 60000, "sessionId": "s2", "display": "actual keyword match"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            matches = search_prompts("keyword", start_ms, end_ms)
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert len(matches) == 1


# ── search_transcripts tests ───────────────────────────────────────────

class TestSearchTranscripts:
    """Tests for search_transcripts function with mock session files."""

    def test_search_transcripts_finds_user_message(self, tmp_path):
        """search_transcripts finds pattern in user messages."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        # Create a mock session file
        ts_iso = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        session_dir = tmp_path / "proj1"
        session_dir.mkdir()
        session_file = session_dir / "sess1.jsonl"
        _make_session_jsonl(session_file, [
            {
                "type": "user",
                "timestamp": ts_iso,
                "sessionId": "sess1",
                "message": {"content": "find this unique pattern"},
            },
        ])

        orig_projects = _mod["PROJECTS_DIR"]
        try:
            _mod["PROJECTS_DIR"] = tmp_path
            matches = search_transcripts("unique pattern", start_ms, end_ms)
        finally:
            _mod["PROJECTS_DIR"] = orig_projects

        assert len(matches) == 1
        assert matches[0]["role"] == "you"

    def test_search_transcripts_finds_assistant_message(self, tmp_path):
        """search_transcripts finds pattern in assistant messages."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        ts_iso = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        session_dir = tmp_path / "proj1"
        session_dir.mkdir()
        session_file = session_dir / "sess1.jsonl"
        _make_session_jsonl(session_file, [
            {
                "type": "assistant",
                "timestamp": ts_iso,
                "sessionId": "sess1",
                "message": {"content": "here is the assistant answer"},
            },
        ])

        orig_projects = _mod["PROJECTS_DIR"]
        try:
            _mod["PROJECTS_DIR"] = tmp_path
            matches = search_transcripts("assistant answer", start_ms, end_ms)
        finally:
            _mod["PROJECTS_DIR"] = orig_projects

        assert len(matches) == 1
        assert matches[0]["role"] == "claude"

    def test_search_transcripts_skips_non_user_assistant(self, tmp_path):
        """search_transcripts skips entries that aren't user or assistant."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        ts_iso = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        session_dir = tmp_path / "proj1"
        session_dir.mkdir()
        session_file = session_dir / "sess1.jsonl"
        _make_session_jsonl(session_file, [
            {
                "type": "system",
                "timestamp": ts_iso,
                "sessionId": "sess1",
                "message": {"content": "system keyword message"},
            },
        ])

        orig_projects = _mod["PROJECTS_DIR"]
        try:
            _mod["PROJECTS_DIR"] = tmp_path
            matches = search_transcripts("keyword", start_ms, end_ms)
        finally:
            _mod["PROJECTS_DIR"] = orig_projects

        assert matches == []

    def test_search_transcripts_respects_date_range(self, tmp_path):
        """search_transcripts only returns results within the time range."""
        old_ts = _hkt_ms(-10, 10)
        recent_ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        old_iso = datetime.fromtimestamp(old_ts / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        recent_iso = datetime.fromtimestamp(recent_ts / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")

        session_dir = tmp_path / "proj1"
        session_dir.mkdir()
        session_file = session_dir / "sess1.jsonl"
        _make_session_jsonl(session_file, [
            {
                "type": "user",
                "timestamp": old_iso,
                "sessionId": "sess1",
                "message": {"content": "old keyword match"},
            },
            {
                "type": "user",
                "timestamp": recent_iso,
                "sessionId": "sess1",
                "message": {"content": "recent keyword match"},
            },
        ])

        orig_projects = _mod["PROJECTS_DIR"]
        try:
            _mod["PROJECTS_DIR"] = tmp_path
            matches = search_transcripts("keyword", start_ms, end_ms)
        finally:
            _mod["PROJECTS_DIR"] = orig_projects

        assert len(matches) == 1
        assert "recent" in matches[0]["snippet"]

    def test_search_transcripts_no_projects_dir(self, tmp_path):
        """search_transcripts returns empty when PROJECTS_DIR doesn't exist."""
        orig_projects = _mod["PROJECTS_DIR"]
        try:
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            matches = search_transcripts("anything", 0, 9999999999999)
        finally:
            _mod["PROJECTS_DIR"] = orig_projects

        assert matches == []

    def test_search_transcripts_handles_malformed_json(self, tmp_path):
        """search_transcripts skips malformed JSON lines gracefully."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        ts_iso = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        session_dir = tmp_path / "proj1"
        session_dir.mkdir()
        session_file = session_dir / "sess1.jsonl"
        session_file.write_text("not valid json\n" + json.dumps({
            "type": "user",
            "timestamp": ts_iso,
            "sessionId": "sess1",
            "message": {"content": "valid keyword entry"},
        }) + "\n")

        orig_projects = _mod["PROJECTS_DIR"]
        try:
            _mod["PROJECTS_DIR"] = tmp_path
            matches = search_transcripts("keyword", start_ms, end_ms)
        finally:
            _mod["PROJECTS_DIR"] = orig_projects

        assert len(matches) == 1


# ── scan_opencode tests ────────────────────────────────────────────────

class TestScanOpencode:
    """Tests for scan_opencode function with mock OpenCode storage."""

    def test_scan_opencode_finds_prompts(self, tmp_path):
        """scan_opencode returns prompts from OpenCode storage."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        storage = tmp_path
        sess_dir = storage / "session" / "sess1"
        sess_dir.mkdir(parents=True)
        (sess_dir / "sess1.json").write_text(json.dumps({
            "id": "sess1",
            "time": {"created": ts, "updated": ts},
        }))

        msg_dir = storage / "message" / "sess1"
        msg_dir.mkdir(parents=True)
        (msg_dir / "msg_001.json").write_text(json.dumps({
            "id": "msg_001",
            "role": "user",
            "time": {"created": ts},
        }))

        part_dir = storage / "part" / "msg_001"
        part_dir.mkdir(parents=True)
        (part_dir / "prt_001.json").write_text(json.dumps({"text": "hello opencode"}))

        orig = _mod["OPENCODE_STORAGE"]
        try:
            _mod["OPENCODE_STORAGE"] = storage
            prompts = scan_opencode(start_ms, end_ms)
        finally:
            _mod["OPENCODE_STORAGE"] = orig

        assert len(prompts) == 1
        assert prompts[0]["prompt"] == "hello opencode"
        assert prompts[0]["tool"] == "OpenCode"

    def test_scan_opencode_no_storage_dir(self, tmp_path):
        """scan_opencode returns empty when storage dir doesn't exist."""
        orig = _mod["OPENCODE_STORAGE"]
        try:
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            prompts = scan_opencode(0, 9999999999999)
        finally:
            _mod["OPENCODE_STORAGE"] = orig

        assert prompts == []

    def test_scan_opencode_filters_by_date(self, tmp_path):
        """scan_opencode only returns prompts within date range."""
        old_ts = _hkt_ms(-10, 10)
        recent_ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        storage = tmp_path

        # Old session
        old_sess_dir = storage / "session" / "old"
        old_sess_dir.mkdir(parents=True)
        (old_sess_dir / "old.json").write_text(json.dumps({
            "id": "old", "time": {"created": old_ts},
        }))
        old_msg_dir = storage / "message" / "old"
        old_msg_dir.mkdir(parents=True)
        (old_msg_dir / "msg_old.json").write_text(json.dumps({
            "id": "msg_old", "role": "user", "time": {"created": old_ts},
        }))
        old_part_dir = storage / "part" / "msg_old"
        old_part_dir.mkdir(parents=True)
        (old_part_dir / "prt_001.json").write_text(json.dumps({"text": "old prompt"}))

        # Recent session
        rec_sess_dir = storage / "session" / "recent"
        rec_sess_dir.mkdir(parents=True)
        (rec_sess_dir / "recent.json").write_text(json.dumps({
            "id": "recent", "time": {"created": recent_ts},
        }))
        rec_msg_dir = storage / "message" / "recent"
        rec_msg_dir.mkdir(parents=True)
        (rec_msg_dir / "msg_rec.json").write_text(json.dumps({
            "id": "msg_rec", "role": "user", "time": {"created": recent_ts},
        }))
        rec_part_dir = storage / "part" / "msg_rec"
        rec_part_dir.mkdir(parents=True)
        (rec_part_dir / "prt_001.json").write_text(json.dumps({"text": "recent prompt"}))

        orig = _mod["OPENCODE_STORAGE"]
        try:
            _mod["OPENCODE_STORAGE"] = storage
            prompts = scan_opencode(start_ms, end_ms)
        finally:
            _mod["OPENCODE_STORAGE"] = orig

        assert len(prompts) == 1
        assert prompts[0]["prompt"] == "recent prompt"

    def test_scan_opencode_skips_non_user_messages(self, tmp_path):
        """scan_opencode skips messages with role != user."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        storage = tmp_path
        sess_dir = storage / "session" / "sess1"
        sess_dir.mkdir(parents=True)
        (sess_dir / "sess1.json").write_text(json.dumps({
            "id": "sess1", "time": {"created": ts},
        }))

        msg_dir = storage / "message" / "sess1"
        msg_dir.mkdir(parents=True)
        (msg_dir / "msg_001.json").write_text(json.dumps({
            "id": "msg_001", "role": "assistant", "time": {"created": ts},
        }))

        orig = _mod["OPENCODE_STORAGE"]
        try:
            _mod["OPENCODE_STORAGE"] = storage
            prompts = scan_opencode(start_ms, end_ms)
        finally:
            _mod["OPENCODE_STORAGE"] = orig

        assert prompts == []

    def test_scan_opencode_handles_malformed_session(self, tmp_path):
        """scan_opencode skips malformed session files gracefully."""
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        storage = tmp_path
        sess_dir = storage / "session" / "bad"
        sess_dir.mkdir(parents=True)
        (sess_dir / "bad.json").write_text("not valid json")

        orig = _mod["OPENCODE_STORAGE"]
        try:
            _mod["OPENCODE_STORAGE"] = storage
            prompts = scan_opencode(start_ms, end_ms)
        finally:
            _mod["OPENCODE_STORAGE"] = orig

        assert prompts == []


# ── print_results tests ────────────────────────────────────────────────

class TestPrintResults:
    """Tests for print_results function."""

    def test_print_results_basic(self, capsys):
        """print_results displays date, total, and session info."""
        result = {
            "date": "2026-01-15",
            "total": 3,
            "sessions": [
                {
                    "id": "abc12345",
                    "full_id": "abc12345def",
                    "count": 3,
                    "tool": "Claude",
                    "first": "10:00",
                    "last": "11:30",
                    "range": "10:00-11:30",
                },
            ],
            "prompts": [
                {"time": "10:05", "session": "abc1", "tool": "Claude", "prompt": "hello"},
                {"time": "10:10", "session": "abc1", "tool": "Claude", "prompt": "world"},
                {"time": "11:30", "session": "abc1", "tool": "Claude", "prompt": "bye"},
            ],
            "all_prompts": [
                {"time": "10:05", "session": "abc1", "tool": "Claude", "prompt": "hello"},
                {"time": "10:10", "session": "abc1", "tool": "Claude", "prompt": "world"},
                {"time": "11:30", "session": "abc1", "tool": "Claude", "prompt": "bye"},
            ],
        }
        print_results(result)
        out = capsys.readouterr().out
        assert "2026-01-15" in out
        assert "3 prompts" in out
        assert "10:00-11:30" in out
        assert "hello" in out

    def test_print_results_error(self, capsys):
        """print_results prints error message when present."""
        print_results({"error": "Something went wrong"})
        out = capsys.readouterr().out
        assert "Something went wrong" in out

    def test_print_results_empty_sessions(self, capsys):
        """print_results handles empty sessions list."""
        result = {
            "date": "2026-01-15",
            "total": 0,
            "sessions": [],
            "prompts": [],
            "all_prompts": [],
        }
        print_results(result)
        out = capsys.readouterr().out
        assert "0 prompts" in out

    def test_print_results_full_mode(self, capsys):
        """print_results in full mode shows all prompts."""
        long_prompt = "x" * 100
        result = {
            "date": "2026-01-15",
            "total": 1,
            "sessions": [],
            "prompts": [],
            "all_prompts": [
                {"time": "10:00", "session": "abc1", "tool": "Claude", "prompt": long_prompt},
            ],
        }
        print_results(result, full=True)
        out = capsys.readouterr().out
        assert "All prompts:" in out

    def test_print_results_truncates_long_prompts(self, capsys):
        """print_results truncates prompts longer than 80 chars."""
        long_prompt = "a" * 120
        result = {
            "date": "2026-01-15",
            "total": 1,
            "sessions": [],
            "prompts": [
                {"time": "10:00", "session": "abc1", "tool": "Claude", "prompt": long_prompt},
            ],
            "all_prompts": [
                {"time": "10:00", "session": "abc1", "tool": "Claude", "prompt": long_prompt},
            ],
        }
        print_results(result)
        out = capsys.readouterr().out
        assert "..." in out


# ── print_search_results tests ─────────────────────────────────────────

class TestPrintSearchResults:
    """Tests for print_search_results function."""

    def test_print_search_no_matches(self, capsys):
        """print_search_results says no matches when empty."""
        print_search_results([], "test", 7, False)
        out = capsys.readouterr().out
        assert "No matches found" in out

    def test_print_search_with_matches(self, capsys):
        """print_search_results displays matches grouped by date."""
        matches = [
            {
                "date": "2026-01-15",
                "time": "10:00",
                "timestamp": 1705305600000,
                "session": "abc1",
                "session_full": "abc12345",
                "role": "you",
                "snippet": "match found here",
                "tool": "Claude",
            },
        ]
        print_search_results(matches, "match", 7, False)
        out = capsys.readouterr().out
        assert "1 matches" in out
        assert "match found here" in out

    def test_print_search_deep_mode(self, capsys):
        """print_search_results shows role tags in deep mode."""
        matches = [
            {
                "date": "2026-01-15",
                "time": "10:00",
                "timestamp": 1705305600000,
                "session": "abc1",
                "session_full": "abc12345",
                "role": "claude",
                "snippet": "assistant match",
                "tool": "Claude",
            },
        ]
        print_search_results(matches, "match", 7, True)
        out = capsys.readouterr().out
        assert "(claude)" in out

    def test_print_search_prompt_mode_no_role(self, capsys):
        """print_search_results hides role tags in non-deep mode."""
        matches = [
            {
                "date": "2026-01-15",
                "time": "10:00",
                "timestamp": 1705305600000,
                "session": "abc1",
                "session_full": "abc12345",
                "role": "you",
                "snippet": "user match",
                "tool": "Claude",
            },
        ]
        print_search_results(matches, "match", 7, False)
        out = capsys.readouterr().out
        assert "(you)" not in out


# ── CLI integration tests (subprocess) ─────────────────────────────────

class TestCLI:
    """Integration tests via subprocess.run."""

    def test_help_flag(self):
        """--help prints usage and exits 0."""
        result = subprocess.run(
            ["python3", str(EFFECTOR_PATH), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "chat_history.py" in result.stdout or "Scan and search" in result.stdout

    def test_h_flag(self):
        """-h prints usage and exits 0."""
        result = subprocess.run(
            ["python3", str(EFFECTOR_PATH), "-h"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "Scan and search" in result.stdout

    def test_specific_date_json(self):
        """YYYY-MM-DD --json outputs valid JSON."""
        result = subprocess.run(
            ["python3", str(EFFECTOR_PATH), "2026-01-15", "--json"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["date"] == "2026-01-15"

    def test_invalid_date_format(self):
        """Invalid date format exits with error."""
        result = subprocess.run(
            ["python3", str(EFFECTOR_PATH), "not-a-date"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 1
        assert "Invalid date format" in result.stdout

    def test_today_default(self):
        """No args defaults to today in HKT."""
        today_str = datetime.now(HKT).strftime("%Y-%m-%d")
        result = subprocess.run(
            ["python3", str(EFFECTOR_PATH), "--json"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["date"] == today_str

    def test_yesterday(self):
        """yesterday arg returns yesterday's date."""
        yesterday_str = (datetime.now(HKT) - timedelta(days=1)).strftime("%Y-%m-%d")
        result = subprocess.run(
            ["python3", str(EFFECTOR_PATH), "yesterday", "--json"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["date"] == yesterday_str

    def test_search_mode_json(self):
        """--search with --json outputs a JSON array."""
        result = subprocess.run(
            ["python3", str(EFFECTOR_PATH), "--search=test_query_12345", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_full_flag_json(self):
        """--full --json includes all_prompts key."""
        result = subprocess.run(
            ["python3", str(EFFECTOR_PATH), "2026-01-15", "--full", "--json"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "all_prompts" in data

    def test_no_full_flag_json_omits_all_prompts(self):
        """Without --full, --json omits all_prompts key."""
        result = subprocess.run(
            ["python3", str(EFFECTOR_PATH), "2026-01-15", "--json"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "all_prompts" not in data

    def test_search_specific_date_invalid(self):
        """--search with invalid date exits with error."""
        result = subprocess.run(
            ["python3", str(EFFECTOR_PATH), "--search=test", "bad-date"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 1
        assert "Invalid date format" in result.stdout

    def test_search_deep_mode(self):
        """--search --deep searches transcripts and outputs text."""
        result = subprocess.run(
            ["python3", str(EFFECTOR_PATH), "--search=definitely_not_a_real_match_xyzzy", "--deep"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "No matches found" in result.stdout

    def test_search_with_specific_date(self):
        """--search with YYYY-MM-DD searches that specific day."""
        result = subprocess.run(
            ["python3", str(EFFECTOR_PATH), "--search=test", "2026-01-15", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_search_with_days_flag(self):
        """--days=N overrides default 7-day range."""
        result = subprocess.run(
            ["python3", str(EFFECTOR_PATH), "--search=test", "--days=30", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_today_explicit(self):
        """'today' positional arg produces today's date."""
        today_str = datetime.now(HKT).strftime("%Y-%m-%d")
        result = subprocess.run(
            ["python3", str(EFFECTOR_PATH), "today", "--json"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["date"] == today_str

    def test_search_deep_json(self):
        """--search --deep --json outputs JSON list."""
        result = subprocess.run(
            ["python3", str(EFFECTOR_PATH), "--search=xyzzy_not_real", "--deep", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_search_human_readable_output(self):
        """--search without --json outputs human-readable text."""
        result = subprocess.run(
            ["python3", str(EFFECTOR_PATH), "--search=xyzzy_not_real"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "Search:" in result.stdout


# ── Additional scan_history edge-case tests ──────────────────────────────


class TestScanHistoryEdgeCases:
    """Edge-case tests for scan_history."""

    def test_scan_history_multiple_tools(self, tmp_path):
        """scan_history collects from both Claude and Codex files."""
        ts = _hkt_ms(0, 10)
        claude_path = tmp_path / ".claude" / "history.jsonl"
        codex_path = tmp_path / ".codex" / "history.jsonl"
        _make_history_jsonl(claude_path, [
            {"timestamp": ts, "sessionId": "c1", "display": "claude prompt"},
        ])
        _make_history_jsonl(codex_path, [
            {"timestamp": ts, "sessionId": "x1", "display": "codex prompt"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": claude_path, "Codex": codex_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            result = scan_history(_hkt_date_str(0))
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert result["total"] == 2
        tools = {p["tool"] for p in result["all_prompts"]}
        assert tools == {"Claude", "Codex"}

    def test_scan_history_sessions_time_range(self, tmp_path):
        """scan_history sessions track first/last times correctly."""
        ts = _hkt_ms(0, 10)
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, [
            {"timestamp": ts, "sessionId": "sess1", "display": "first"},
            {"timestamp": ts + 3600000, "sessionId": "sess1", "display": "second"},
            {"timestamp": ts + 7200000, "sessionId": "sess1", "display": "third"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            result = scan_history(_hkt_date_str(0))
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert len(result["sessions"]) == 1
        s = result["sessions"][0]
        assert s["count"] == 3
        assert s["range"] == f"{s['first']}-{s['last']}"

    def test_scan_history_malformed_json_line(self, tmp_path):
        """scan_history skips malformed JSON lines gracefully."""
        ts = _hkt_ms(0, 10)
        history_path = tmp_path / ".claude" / "history.jsonl"
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(history_path, "w") as f:
            f.write("not json\n")
            f.write(json.dumps({"timestamp": ts, "sessionId": "s1", "display": "valid"}) + "\n")

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            result = scan_history(_hkt_date_str(0))
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert result["total"] == 1


# ── Additional search_transcripts edge-case tests ────────────────────────


class TestSearchTranscriptsEdgeCases:
    """Edge-case tests for search_transcripts."""

    def test_search_transcripts_list_content(self, tmp_path):
        """search_transcripts handles content as a list of blocks."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        ts_iso = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        session_dir = tmp_path / "proj1"
        session_dir.mkdir()
        session_file = session_dir / "sess1.jsonl"
        _make_session_jsonl(session_file, [
            {
                "type": "user",
                "timestamp": ts_iso,
                "sessionId": "sess1",
                "message": {
                    "content": [
                        {"type": "text", "text": "find this listcontent pattern"},
                    ]
                },
            },
        ])

        orig_projects = _mod["PROJECTS_DIR"]
        try:
            _mod["PROJECTS_DIR"] = tmp_path
            matches = search_transcripts("listcontent", start_ms, end_ms)
        finally:
            _mod["PROJECTS_DIR"] = orig_projects

        assert len(matches) == 1
        assert "listcontent" in matches[0]["snippet"]

    def test_search_transcripts_empty_content_skipped(self, tmp_path):
        """search_transcripts skips entries with empty content."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        ts_iso = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        session_dir = tmp_path / "proj1"
        session_dir.mkdir()
        session_file = session_dir / "sess1.jsonl"
        _make_session_jsonl(session_file, [
            {
                "type": "user",
                "timestamp": ts_iso,
                "sessionId": "sess1",
                "message": {"content": ""},
            },
        ])

        orig_projects = _mod["PROJECTS_DIR"]
        try:
            _mod["PROJECTS_DIR"] = tmp_path
            matches = search_transcripts("anything", start_ms, end_ms)
        finally:
            _mod["PROJECTS_DIR"] = orig_projects

        assert matches == []

    def test_search_transcripts_no_timestamp_skipped(self, tmp_path):
        """search_transcripts skips entries without a timestamp."""
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        session_dir = tmp_path / "proj1"
        session_dir.mkdir()
        session_file = session_dir / "sess1.jsonl"
        _make_session_jsonl(session_file, [
            {
                "type": "user",
                "timestamp": "",
                "sessionId": "sess1",
                "message": {"content": "no timestamp keyword"},
            },
        ])

        orig_projects = _mod["PROJECTS_DIR"]
        try:
            _mod["PROJECTS_DIR"] = tmp_path
            matches = search_transcripts("keyword", start_ms, end_ms)
        finally:
            _mod["PROJECTS_DIR"] = orig_projects

        assert matches == []

    def test_search_transcripts_session_id_fallback(self, tmp_path):
        """search_transcripts uses filename stem when sessionId missing."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        ts_iso = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        session_dir = tmp_path / "proj1"
        session_dir.mkdir()
        session_file = session_dir / "my_session_file.jsonl"
        _make_session_jsonl(session_file, [
            {
                "type": "user",
                "timestamp": ts_iso,
                "sessionId": "",
                "message": {"content": "find fallback pattern"},
            },
        ])

        orig_projects = _mod["PROJECTS_DIR"]
        try:
            _mod["PROJECTS_DIR"] = tmp_path
            matches = search_transcripts("fallback", start_ms, end_ms)
        finally:
            _mod["PROJECTS_DIR"] = orig_projects

        assert len(matches) == 1
        assert matches[0]["session_full"] == "my_session_file"

    def test_search_transcripts_sorts_by_timestamp_desc(self, tmp_path):
        """search_transcripts returns results sorted newest first."""
        ts1 = _hkt_ms(0, 9)
        ts2 = _hkt_ms(0, 11)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        ts1_iso = datetime.fromtimestamp(ts1 / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        ts2_iso = datetime.fromtimestamp(ts2 / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")

        session_dir = tmp_path / "proj1"
        session_dir.mkdir()
        session_file = session_dir / "sess1.jsonl"
        _make_session_jsonl(session_file, [
            {
                "type": "user",
                "timestamp": ts1_iso,
                "sessionId": "sess1",
                "message": {"content": "early sortmatch"},
            },
            {
                "type": "user",
                "timestamp": ts2_iso,
                "sessionId": "sess1",
                "message": {"content": "later sortmatch"},
            },
        ])

        orig_projects = _mod["PROJECTS_DIR"]
        try:
            _mod["PROJECTS_DIR"] = tmp_path
            matches = search_transcripts("sortmatch", start_ms, end_ms)
        finally:
            _mod["PROJECTS_DIR"] = orig_projects

        assert len(matches) == 2
        assert matches[0]["timestamp"] > matches[1]["timestamp"]


# ── Additional scan_opencode edge-case tests ─────────────────────────────


class TestScanOpencodeEdgeCases:
    """Edge-case tests for scan_opencode."""

    def test_scan_opencode_multi_part_prompt(self, tmp_path):
        """scan_opencode concatenates multiple parts into one prompt."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        storage = tmp_path
        sess_dir = storage / "session" / "sess1"
        sess_dir.mkdir(parents=True)
        (sess_dir / "sess1.json").write_text(json.dumps({
            "id": "sess1", "time": {"created": ts},
        }))

        msg_dir = storage / "message" / "sess1"
        msg_dir.mkdir(parents=True)
        (msg_dir / "msg_001.json").write_text(json.dumps({
            "id": "msg_001", "role": "user", "time": {"created": ts},
        }))

        part_dir = storage / "part" / "msg_001"
        part_dir.mkdir(parents=True)
        (part_dir / "prt_001.json").write_text(json.dumps({"text": "hello "}))
        (part_dir / "prt_002.json").write_text(json.dumps({"text": "world"}))

        orig = _mod["OPENCODE_STORAGE"]
        try:
            _mod["OPENCODE_STORAGE"] = storage
            prompts = scan_opencode(start_ms, end_ms)
        finally:
            _mod["OPENCODE_STORAGE"] = orig

        assert len(prompts) == 1
        assert prompts[0]["prompt"] == "hello world"

    def test_scan_opencode_fallback_to_updated_time(self, tmp_path):
        """scan_opencode falls back to 'updated' time when created is out of range."""
        old_ts = _hkt_ms(-5, 10)
        recent_ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        storage = tmp_path
        sess_dir = storage / "session" / "sess1"
        sess_dir.mkdir(parents=True)
        (sess_dir / "sess1.json").write_text(json.dumps({
            "id": "sess1",
            "time": {"created": old_ts, "updated": recent_ts},
        }))

        msg_dir = storage / "message" / "sess1"
        msg_dir.mkdir(parents=True)
        (msg_dir / "msg_001.json").write_text(json.dumps({
            "id": "msg_001", "role": "user", "time": {"created": recent_ts},
        }))

        part_dir = storage / "part" / "msg_001"
        part_dir.mkdir(parents=True)
        (part_dir / "prt_001.json").write_text(json.dumps({"text": "fallback prompt"}))

        orig = _mod["OPENCODE_STORAGE"]
        try:
            _mod["OPENCODE_STORAGE"] = storage
            prompts = scan_opencode(start_ms, end_ms)
        finally:
            _mod["OPENCODE_STORAGE"] = orig

        assert len(prompts) == 1
        assert prompts[0]["prompt"] == "fallback prompt"

    def test_scan_opencode_no_message_dir(self, tmp_path):
        """scan_opencode skips session when message dir doesn't exist."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        storage = tmp_path
        sess_dir = storage / "session" / "sess1"
        sess_dir.mkdir(parents=True)
        (sess_dir / "sess1.json").write_text(json.dumps({
            "id": "sess1", "time": {"created": ts},
        }))
        # No message dir created

        orig = _mod["OPENCODE_STORAGE"]
        try:
            _mod["OPENCODE_STORAGE"] = storage
            prompts = scan_opencode(start_ms, end_ms)
        finally:
            _mod["OPENCODE_STORAGE"] = orig

        assert prompts == []

    def test_scan_opencode_no_part_dir(self, tmp_path):
        """scan_opencode skips messages when part dir doesn't exist."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        storage = tmp_path
        sess_dir = storage / "session" / "sess1"
        sess_dir.mkdir(parents=True)
        (sess_dir / "sess1.json").write_text(json.dumps({
            "id": "sess1", "time": {"created": ts},
        }))

        msg_dir = storage / "message" / "sess1"
        msg_dir.mkdir(parents=True)
        (msg_dir / "msg_001.json").write_text(json.dumps({
            "id": "msg_001", "role": "user", "time": {"created": ts},
        }))
        # No part dir — prompt_text will be empty, so it gets skipped

        orig = _mod["OPENCODE_STORAGE"]
        try:
            _mod["OPENCODE_STORAGE"] = storage
            prompts = scan_opencode(start_ms, end_ms)
        finally:
            _mod["OPENCODE_STORAGE"] = orig

        assert prompts == []


# ── Additional search_prompts edge-case tests ────────────────────────────


class TestSearchPromptsEdgeCases:
    """Edge-case tests for search_prompts."""

    def test_search_prompts_opencode_tool_filter(self, tmp_path):
        """search_prompts with tool='OpenCode' searches OpenCode storage."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        # Set up OpenCode storage
        storage = tmp_path / "opencode"
        sess_dir = storage / "session" / "sess1"
        sess_dir.mkdir(parents=True)
        (sess_dir / "sess1.json").write_text(json.dumps({
            "id": "sess1", "time": {"created": ts},
        }))
        msg_dir = storage / "message" / "sess1"
        msg_dir.mkdir(parents=True)
        (msg_dir / "msg_001.json").write_text(json.dumps({
            "id": "msg_001", "role": "user", "time": {"created": ts},
        }))
        part_dir = storage / "part" / "msg_001"
        part_dir.mkdir(parents=True)
        (part_dir / "prt_001.json").write_text(json.dumps({"text": "opencode searchterm match"}))

        orig_files = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": tmp_path / "nope.jsonl"}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = storage
            matches = search_prompts("searchterm", start_ms, end_ms, tool="OpenCode")
        finally:
            _mod["HISTORY_FILES"] = orig_files
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert len(matches) == 1
        assert matches[0]["tool"] == "OpenCode"

    def test_search_prompts_unknown_tool_returns_empty(self, tmp_path):
        """search_prompts with unknown tool and no OpenCode returns empty."""
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)

        orig_files = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": tmp_path / "nope.jsonl"}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            matches = search_prompts("test", start_ms, end_ms, tool="UnknownTool")
        finally:
            _mod["HISTORY_FILES"] = orig_files
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert matches == []

    def test_search_prompts_regex_pattern(self, tmp_path):
        """search_prompts supports regex patterns."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, [
            {"timestamp": ts, "sessionId": "s1", "display": "test123 and test456"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            matches = search_prompts(r"test\d+", start_ms, end_ms)
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert len(matches) == 1

    def test_search_prompts_match_fields(self, tmp_path):
        """search_prompts returns all expected fields in match dict."""
        ts = _hkt_ms(0, 10)
        start_ms = _hkt_ms(-1, 0)
        end_ms = _hkt_ms(1, 0)
        history_path = tmp_path / ".claude" / "history.jsonl"
        _make_history_jsonl(history_path, [
            {"timestamp": ts, "sessionId": "session12345", "display": "check fields"},
        ])

        orig = dict(_mod["HISTORY_FILES"])
        orig_projects = _mod["PROJECTS_DIR"]
        orig_opencode = _mod["OPENCODE_STORAGE"]
        try:
            _mod["HISTORY_FILES"] = {"Claude": history_path}
            _mod["PROJECTS_DIR"] = tmp_path / "nonexistent"
            _mod["OPENCODE_STORAGE"] = tmp_path / "nonexistent"
            matches = search_prompts("fields", start_ms, end_ms)
        finally:
            _mod["HISTORY_FILES"] = orig
            _mod["PROJECTS_DIR"] = orig_projects
            _mod["OPENCODE_STORAGE"] = orig_opencode

        assert len(matches) == 1
        m = matches[0]
        assert "date" in m
        assert "time" in m
        assert m["timestamp"] == ts
        assert m["session"] == "session1"  # truncated to 8 chars
        assert m["session_full"] == "session12345"
        assert m["role"] == "you"
        assert "snippet" in m
        assert m["tool"] == "Claude"


# ── Additional extract_text_from_content edge-case tests ─────────────────


class TestExtractTextFromContentEdgeCases:
    """Edge-case tests for extract_text_from_content."""

    def test_mixed_block_types(self):
        """extract_text_from_content handles mix of text, tool_use, tool_result."""
        content = [
            {"type": "text", "text": "Start"},
            {"type": "tool_use", "name": "Read", "input": {}},
            {"type": "tool_result", "content": "output"},
            {"type": "text", "text": "End"},
            {"type": "thinking", "thinking": "private"},
        ]
        result = extract_text_from_content(content)
        assert "Start" in result
        assert "[tool: Read]" in result
        assert "End" in result
        assert "output" not in result
        assert "private" not in result

    def test_nested_dict_in_list(self):
        """extract_text_from_content handles unknown block types gracefully."""
        content = [
            {"type": "text", "text": "known"},
            {"type": "unknown_type", "data": "ignored"},
        ]
        result = extract_text_from_content(content)
        assert "known" in result
        assert "ignored" not in result
