"""Tests for crispr — adaptive immunity spacer system."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest


class TestRegexify:
    def test_replaces_paths(self):
        from metabolon.organelles.crispr import _regexify
        pattern, regex = _regexify("File /usr/local/lib/error.py not found")
        assert "{path}" in pattern

    def test_replaces_numbers(self):
        from metabolon.organelles.crispr import _regexify
        pattern, regex = _regexify("line 42: syntax error")
        assert "{n}" in pattern

    def test_regex_compiles(self):
        import re
        from metabolon.organelles.crispr import _regexify
        _, regex = _regexify("Error at /tmp/foo.py line 10")
        compiled = re.compile(regex)
        assert compiled.search("Error at /var/bar.py line 99")


class TestIsSelfTest:
    def test_inflammasome(self):
        from metabolon.organelles.crispr import is_self_test
        assert is_self_test("inflammasome:probe_x") is True

    def test_autoimmunity(self):
        from metabolon.organelles.crispr import is_self_test
        assert is_self_test("autoimmunity:check") is True

    def test_normal_tool(self):
        from metabolon.organelles.crispr import is_self_test
        assert is_self_test("rheotaxis") is False


class TestAcquireSpacer:
    def test_acquires_and_returns(self, tmp_path):
        from metabolon.organelles.crispr import acquire_spacer
        import metabolon.organelles.crispr as crispr
        spacer_file = tmp_path / "spacers.jsonl"
        with patch.object(crispr, "_SPACER_DIR", tmp_path), \
             patch.object(crispr, "_SPACER_FILE", spacer_file):
            result = acquire_spacer("ImportError: no module named foo", "goose")
        assert result["tool"] == "goose"
        assert "pattern" in result
        assert spacer_file.exists()

    def test_blocks_self_test(self, tmp_path):
        from metabolon.organelles.crispr import acquire_spacer
        result = acquire_spacer("test error", "inflammasome:probe")
        assert result == {}


class TestCompileGuides:
    def test_compiles_from_file(self, tmp_path):
        from metabolon.organelles.crispr import compile_guides, _regexify
        import metabolon.organelles.crispr as crispr
        _, regex = _regexify("ImportError: no module")
        entry = json.dumps({"tool": "goose", "pattern": "test", "regex": regex, "ts": "2026-01-01T00:00:00"})
        spacer_file = tmp_path / "spacers.jsonl"
        spacer_file.write_text(entry + "\n")
        with patch.object(crispr, "_SPACER_FILE", spacer_file):
            guides = compile_guides()
        assert len(guides) == 1
        assert "regex_compiled" in guides[0]

    def test_empty_file(self, tmp_path):
        from metabolon.organelles.crispr import compile_guides
        import metabolon.organelles.crispr as crispr
        with patch.object(crispr, "_SPACER_FILE", tmp_path / "nope.jsonl"):
            assert compile_guides() == []


class TestScan:
    def test_matches_known_pattern(self, tmp_path):
        from metabolon.organelles.crispr import acquire_spacer, scan
        import metabolon.organelles.crispr as crispr
        spacer_file = tmp_path / "spacers.jsonl"
        with patch.object(crispr, "_SPACER_DIR", tmp_path), \
             patch.object(crispr, "_SPACER_FILE", spacer_file):
            acquire_spacer("Error at /tmp/foo.py line 10", "goose")
            result = scan("Error at /var/bar.py line 99")
        assert result is not None
        assert result["tool"] == "goose"

    def test_novel_returns_none(self, tmp_path):
        from metabolon.organelles.crispr import scan
        import metabolon.organelles.crispr as crispr
        with patch.object(crispr, "_SPACER_FILE", tmp_path / "empty.jsonl"):
            assert scan("something completely new") is None


class TestSpacerCount:
    def test_counts(self, tmp_path):
        from metabolon.organelles.crispr import spacer_count
        import metabolon.organelles.crispr as crispr
        f = tmp_path / "spacers.jsonl"
        f.write_text('{"a":1}\n{"b":2}\n')
        with patch.object(crispr, "_SPACER_FILE", f):
            assert spacer_count() == 2

    def test_no_file(self, tmp_path):
        from metabolon.organelles.crispr import spacer_count
        import metabolon.organelles.crispr as crispr
        with patch.object(crispr, "_SPACER_FILE", tmp_path / "nope"):
            assert spacer_count() == 0


class TestPruneSpacer:
    def test_prunes_old(self, tmp_path):
        from metabolon.organelles.crispr import prune_spacers
        import metabolon.organelles.crispr as crispr
        f = tmp_path / "spacers.jsonl"
        old = json.dumps({"ts": "2020-01-01T00:00:00+00:00", "tool": "old"})
        new = json.dumps({"ts": "2026-03-30T00:00:00+00:00", "tool": "new"})
        f.write_text(old + "\n" + new + "\n")
        with patch.object(crispr, "_SPACER_FILE", f):
            pruned = prune_spacers(max_age_days=90)
        assert pruned == 1
        remaining = f.read_text().strip().splitlines()
        assert len(remaining) == 1
