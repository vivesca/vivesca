from __future__ import annotations

"""Tests for metabolon.organelles.crispr — adaptive immunity spacer system."""

import json
import re
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from metabolon.organelles.crispr import (
    _regexify,
    acquire_spacer,
    compile_guides,
    is_self_test,
    prune_spacers,
    scan,
    spacer_count,
)


# ---------------------------------------------------------------------------
# Test _regexify
# ---------------------------------------------------------------------------

class TestRegexify:
    def test_replaces_paths(self):
        pattern, regex = _regexify("File /usr/local/lib/error.py not found")
        assert "{path}" in pattern
        # Ensure regex matches similar paths
        compiled = re.compile(regex, re.IGNORECASE)
        assert compiled.search("File /home/user/foo.py not found")
        assert not compiled.search("File not found")

    def test_replaces_numbers(self):
        pattern, regex = _regexify("line 42: syntax error")
        assert "{n}" in pattern
        compiled = re.compile(regex, re.IGNORECASE)
        assert compiled.search("line 99: syntax error")
        assert not compiled.search("line: syntax error")

    def test_replaces_strings_double_quotes(self):
        pattern, regex = _regexify('Error: "something went wrong"')
        assert '"{str}"' in pattern
        compiled = re.compile(regex, re.IGNORECASE)
        assert compiled.search('Error: "different message"')
        assert compiled.search("Error: \"\"")  # empty string

    def test_replaces_strings_single_quotes(self):
        pattern, regex = _regexify("Error: 'something went wrong'")
        assert "'{str}'" in pattern
        compiled = re.compile(regex, re.IGNORECASE)
        assert compiled.search("Error: 'different message'")

    def test_replaces_uppercase_names(self):
        pattern, regex = _regexify("ERROR_CODE_500: something")
        assert "{name}" in pattern
        compiled = re.compile(regex, re.IGNORECASE)
        assert compiled.search("ERROR_CODE_404: something")
        # lowercase not matched
        assert not compiled.search("error_code: something")
        # uppercase inside quotes should be string
        pattern2, _ = _regexify('Error "MODULE_NOT_FOUND"')
        assert '"{str}"' in pattern2
        pattern3, _ = _regexify("Error 'MODULE_NOT_FOUND'")
        assert "'{str}'" in pattern3

    def test_mixed_replacements(self):
        pattern, regex = _regexify('File "/tmp/foo.py", line 42, in main')
        assert '"{str}"' in pattern
        assert "{n}" in pattern
        compiled = re.compile(regex, re.IGNORECASE)
        assert compiled.search('File "/home/bar.py", line 99, in main')
        assert not compiled.search('File "", line , in main')


# ---------------------------------------------------------------------------
# Test is_self_test
# ---------------------------------------------------------------------------

class TestIsSelfTest:
    def test_inflammasome(self):
        assert is_self_test("inflammasome:probe_x") is True

    def test_autoimmunity(self):
        assert is_self_test("autoimmunity:check") is True

    def test_normal_tool(self):
        assert is_self_test("rheotaxis") is False

    def test_partial_prefix(self):
        assert is_self_test("inflammasome") is False  # no colon
        assert is_self_test("inflammasome:") is True  # empty suffix
        assert is_self_test("autoimmunity:foo:bar") is True


# ---------------------------------------------------------------------------
# Test acquire_spacer
# ---------------------------------------------------------------------------

class TestAcquireSpacer:
    def test_acquires_and_returns(self, tmp_path):
        spacer_file = tmp_path / "spacers.jsonl"
        with patch("metabolon.organelles.crispr._SPACER_DIR", tmp_path), \
             patch("metabolon.organelles.crispr._SPACER_FILE", spacer_file):
            result = acquire_spacer("ImportError: no module named foo", "goose")
        assert result["tool"] == "goose"
        assert "pattern" in result
        assert "regex" in result
        assert "raw_error" in result
        assert "ts" in result
        assert spacer_file.exists()
        # Verify written line is valid JSON
        lines = spacer_file.read_text().strip().splitlines()
        assert len(lines) == 1
        written = json.loads(lines[0])
        assert written["tool"] == "goose"

    def test_blocks_self_test(self):
        result = acquire_spacer("test error", "inflammasome:probe")
        assert result == {}

    def test_handles_write_error(self, tmp_path):
        spacer_file = tmp_path / "spacers.jsonl"
        # Make directory read-only to cause write error? Simpler: mock open to raise Exception
        with patch("metabolon.organelles.crispr._SPACER_DIR", tmp_path), \
             patch("metabolon.organelles.crispr._SPACER_FILE", spacer_file), \
             patch("builtins.open", side_effect=Exception("disk full")):
            result = acquire_spacer("error", "tool")
        # Should still return spacer dict (since exception is caught)
        assert result["tool"] == "tool"

    def test_timestamp_is_utc(self, tmp_path):
        spacer_file = tmp_path / "spacers.jsonl"
        fake_now = datetime(2026, 4, 1, 12, 0, 0, tzinfo=UTC)
        with patch("metabolon.organelles.crispr._SPACER_DIR", tmp_path), \
             patch("metabolon.organelles.crispr._SPACER_FILE", spacer_file), \
             patch("metabolon.organelles.crispr.datetime") as mock_dt:
            mock_dt.now.return_value = fake_now
            result = acquire_spacer("error", "tool")
        assert result["ts"] == fake_now.isoformat()


# ---------------------------------------------------------------------------
# Test compile_guides
# ---------------------------------------------------------------------------

class TestCompileGuides:
    def test_compiles_from_file(self, tmp_path):
        _, regex = _regexify("ImportError: no module")
        entry = json.dumps({
            "tool": "goose",
            "pattern": "test",
            "regex": regex,
            "ts": "2026-01-01T00:00:00+00:00",
            "raw_error": "ImportError: no module",
        })
        spacer_file = tmp_path / "spacers.jsonl"
        spacer_file.write_text(entry + "\n")
        with patch("metabolon.organelles.crispr._SPACER_FILE", spacer_file):
            guides = compile_guides()
        assert len(guides) == 1
        assert "regex_compiled" in guides[0]
        assert guides[0]["tool"] == "goose"
        assert guides[0]["pattern"] == "test"
        assert isinstance(guides[0]["regex_compiled"], re.Pattern)

    def test_empty_file(self, tmp_path):
        with patch("metabolon.organelles.crispr._SPACER_FILE", tmp_path / "nope.jsonl"):
            assert compile_guides() == []

    def test_missing_keys_skipped(self, tmp_path):
        entry = json.dumps({"tool": "x"})  # missing regex
        spacer_file = tmp_path / "spacers.jsonl"
        spacer_file.write_text(entry + "\n")
        with patch("metabolon.organelles.crispr._SPACER_FILE", spacer_file):
            guides = compile_guides()
        assert guides == []

    def test_invalid_regex_skipped(self, tmp_path):
        entry = json.dumps({
            "tool": "x",
            "regex": "[invalid",
            "pattern": "",
            "ts": "",
            "raw_error": "",
        })
        spacer_file = tmp_path / "spacers.jsonl"
        spacer_file.write_text(entry + "\n")
        with patch("metabolon.organelles.crispr._SPACER_FILE", spacer_file):
            guides = compile_guides()
        assert guides == []

    def test_read_error_returns_empty(self, tmp_path):
        spacer_file = tmp_path / "spacers.jsonl"
        with patch("metabolon.organelles.crispr._SPACER_FILE", spacer_file), \
             patch("pathlib.Path.read_text", side_effect=Exception("permission")):
            guides = compile_guides()
        assert guides == []


# ---------------------------------------------------------------------------
# Test scan
# ---------------------------------------------------------------------------

class TestScan:
    def test_matches_known_pattern(self, tmp_path):
        spacer_file = tmp_path / "spacers.jsonl"
        with patch("metabolon.organelles.crispr._SPACER_DIR", tmp_path), \
             patch("metabolon.organelles.crispr._SPACER_FILE", spacer_file):
            acquire_spacer("Error at /tmp/foo.py line 10", "goose")
            result = scan("Error at /var/bar.py line 99")
        assert result is not None
        assert result["tool"] == "goose"
        assert "pattern" in result
        assert "acquired_ts" in result
        assert "raw_error" in result

    def test_novel_returns_none(self, tmp_path):
        with patch("metabolon.organelles.crispr._SPACER_FILE", tmp_path / "empty.jsonl"):
            assert scan("something completely new") is None

    def test_self_test_tool_skips(self):
        # If tool_name is self-test, scan returns None even if match exists
        # We need to set up a spacer first
        with patch("metabolon.organelles.crispr.is_self_test") as mock_self:
            mock_self.return_value = True
            result = scan("any error", tool_name="inflammasome:probe")
        assert result is None

    def test_matching_tool_name_not_self(self, tmp_path):
        spacer_file = tmp_path / "spacers.jsonl"
        with patch("metabolon.organelles.crispr._SPACER_DIR", tmp_path), \
             patch("metabolon.organelles.crispr._SPACER_FILE", spacer_file):
            acquire_spacer("Error at /tmp/foo.py line 10", "goose")
            result = scan("Error at /var/bar.py line 99", tool_name="goose")
        assert result is not None


# ---------------------------------------------------------------------------
# Test spacer_count
# ---------------------------------------------------------------------------

class TestSpacerCount:
    def test_counts(self, tmp_path):
        f = tmp_path / "spacers.jsonl"
        f.write_text('{"a":1}\n{"b":2}\n')
        with patch("metabolon.organelles.crispr._SPACER_FILE", f):
            assert spacer_count() == 2

    def test_no_file(self, tmp_path):
        with patch("metabolon.organelles.crispr._SPACER_FILE", tmp_path / "nope"):
            assert spacer_count() == 0

    def test_empty_lines_ignored(self, tmp_path):
        f = tmp_path / "spacers.jsonl"
        f.write_text('{"a":1}\n\n\n{"b":2}\n')
        with patch("metabolon.organelles.crispr._SPACER_FILE", f):
            assert spacer_count() == 2

    def test_read_error_returns_zero(self, tmp_path):
        f = tmp_path / "spacers.jsonl"
        with patch("metabolon.organelles.crispr._SPACER_FILE", f), \
             patch("pathlib.Path.read_text", side_effect=Exception("io")):
            assert spacer_count() == 0


# ---------------------------------------------------------------------------
# Test prune_spacers
# ---------------------------------------------------------------------------

class TestPruneSpacers:
    def test_prunes_old(self, tmp_path):
        f = tmp_path / "spacers.jsonl"
        old = json.dumps({"ts": "2020-01-01T00:00:00+00:00", "tool": "old"})
        new = json.dumps({"ts": "2026-03-30T00:00:00+00:00", "tool": "new"})
        f.write_text(old + "\n" + new + "\n")
        with patch("metabolon.organelles.crispr._SPACER_FILE", f):
            pruned = prune_spacers(max_age_days=90)
        assert pruned == 1
        remaining = f.read_text().strip().splitlines()
        assert len(remaining) == 1
        assert json.loads(remaining[0])["tool"] == "new"

    def test_no_file(self, tmp_path):
        with patch("metabolon.organelles.crispr._SPACER_FILE", tmp_path / "missing"):
            assert prune_spacers() == 0

    def test_read_error_returns_zero(self, tmp_path):
        f = tmp_path / "spacers.jsonl"
        with patch("metabolon.organelles.crispr._SPACER_FILE", f), \
             patch("pathlib.Path.read_text", side_effect=Exception("io")):
            assert prune_spacers() == 0

    def test_write_error_returns_zero(self, tmp_path):
        f = tmp_path / "spacers.jsonl"
        f.write_text('{"ts": "2020-01-01T00:00:00+00:00", "tool": "old"}\n')
        with patch("metabolon.organelles.crispr._SPACER_FILE", f), \
             patch("pathlib.Path.write_text", side_effect=Exception("write")):
            pruned = prune_spacers(max_age_days=90)
        assert pruned == 0  # error caught, pruned reset to 0

    def test_timestamp_without_timezone_assumed_utc(self, tmp_path):
        # The code adds UTC if tzinfo is None
        f = tmp_path / "spacers.jsonl"
        # timestamp without timezone
        entry = json.dumps({"ts": "2020-01-01T00:00:00", "tool": "old"})
        f.write_text(entry + "\n")
        with patch("metabolon.organelles.crispr._SPACER_FILE", f):
            pruned = prune_spacers(max_age_days=1)
        # Should be pruned (old)
        assert pruned == 1

    def test_invalid_timestamp_kept(self, tmp_path):
        f = tmp_path / "spacers.jsonl"
        entry = json.dumps({"ts": "not-a-date", "tool": "x"})
        f.write_text(entry + "\n")
        with patch("metabolon.organelles.crispr._SPACER_FILE", f):
            pruned = prune_spacers(max_age_days=90)
        assert pruned == 0  # kept due to exception
        remaining = f.read_text().strip().splitlines()
        assert len(remaining) == 1

    def test_empty_json_object_kept(self, tmp_path):
        f = tmp_path / "spacers.jsonl"
        f.write_text("{}\n")
        with patch("metabolon.organelles.crispr._SPACER_FILE", f):
            pruned = prune_spacers(max_age_days=90)
        assert pruned == 0
        remaining = f.read_text().strip().splitlines()
        assert len(remaining) == 1