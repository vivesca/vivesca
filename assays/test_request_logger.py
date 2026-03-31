from __future__ import annotations

"""Tests for metabolon.server — RequestLogger JSONL persistence."""

import json
from unittest.mock import patch

import pytest

from metabolon.server import RequestLogger


class TestRequestLoggerInit:
    def test_default_path(self):
        rl = RequestLogger()
        assert rl._path.name == "requests.jsonl"
        assert "vivesca" in str(rl._path)

    def test_custom_path(self, tmp_path):
        custom = tmp_path / "custom.jsonl"
        rl = RequestLogger(custom)
        assert rl._path == custom

    def test_path_is_always_path_object(self, tmp_path):
        rl = RequestLogger(str(tmp_path / "x.jsonl"))
        assert isinstance(rl._path, type(tmp_path / "x.jsonl"))


class TestRequestLoggerLog:
    def test_appends_entry(self, tmp_path):
        log_path = tmp_path / "req.jsonl"
        rl = RequestLogger(log_path)
        rl.log(tool="search", duration_ms=42, success=True)

        lines = log_path.read_text().strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["tool"] == "search"
        assert entry["duration_ms"] == 42
        assert entry["success"] is True
        assert "ts" in entry

    def test_multiple_entries(self, tmp_path):
        log_path = tmp_path / "req.jsonl"
        rl = RequestLogger(log_path)
        rl.log(tool="a", duration_ms=10, success=True)
        rl.log(tool="b", duration_ms=20, success=False)

        lines = log_path.read_text().strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["tool"] == "a"
        assert json.loads(lines[1])["tool"] == "b"

    def test_creates_parent_dirs(self, tmp_path):
        log_path = tmp_path / "deep" / "nested" / "dir" / "req.jsonl"
        rl = RequestLogger(log_path)
        rl.log(tool="x", duration_ms=1, success=True)
        assert log_path.exists()

    def test_timestamp_is_iso8601(self, tmp_path):
        log_path = tmp_path / "req.jsonl"
        rl = RequestLogger(log_path)
        rl.log(tool="t", duration_ms=5, success=True)

        entry = json.loads(log_path.read_text().strip())
        # ISO-8601 strings contain 'T' and timezone
        assert "T" in entry["ts"]
        assert "+" in entry["ts"] or entry["ts"].endswith("Z") or "UTC" in entry["ts"] or "-0" in entry["ts"]

    def test_success_false(self, tmp_path):
        log_path = tmp_path / "req.jsonl"
        rl = RequestLogger(log_path)
        rl.log(tool="fail", duration_ms=99, success=False)

        entry = json.loads(log_path.read_text().strip())
        assert entry["success"] is False

    def test_write_failure_suppressed(self, tmp_path):
        log_path = tmp_path / "readonly" / "req.jsonl"
        # Make the parent dir read-only so writing fails
        log_path.parent.mkdir()
        log_path.parent.chmod(0o444)
        try:
            rl = RequestLogger(log_path)
            # Should not raise — exception is suppressed
            rl.log(tool="x", duration_ms=1, success=True)
        finally:
            log_path.parent.chmod(0o755)

    def test_each_line_valid_json(self, tmp_path):
        log_path = tmp_path / "req.jsonl"
        rl = RequestLogger(log_path)
        for i in range(5):
            rl.log(tool=f"tool{i}", duration_ms=i * 10, success=i % 2 == 0)

        for line in log_path.read_text().strip().splitlines():
            entry = json.loads(line)
            assert {"ts", "tool", "duration_ms", "success"} == set(entry.keys())


class TestRequestLoggerEdgeCases:
    def test_duration_zero(self, tmp_path):
        log_path = tmp_path / "req.jsonl"
        rl = RequestLogger(log_path)
        rl.log(tool="fast", duration_ms=0, success=True)
        assert json.loads(log_path.read_text().strip())["duration_ms"] == 0

    def test_large_duration(self, tmp_path):
        log_path = tmp_path / "req.jsonl"
        rl = RequestLogger(log_path)
        rl.log(tool="slow", duration_ms=999999, success=True)
        assert json.loads(log_path.read_text().strip())["duration_ms"] == 999999

    def test_special_chars_in_tool_name(self, tmp_path):
        log_path = tmp_path / "req.jsonl"
        rl = RequestLogger(log_path)
        rl.log(tool="tool/with:special-chars", duration_ms=1, success=True)
        assert json.loads(log_path.read_text().strip())["tool"] == "tool/with:special-chars"
