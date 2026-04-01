from __future__ import annotations

"""Tests for metabolon.respirometry.categories."""

from pathlib import Path

import pytest
import yaml

from metabolon.respirometry.categories import categorise, restore_categories


# ── restore_categories ────────────────────────────────────────────────


class TestRestoreCategories:
    """Tests for restore_categories()."""

    def test_missing_file_returns_empty(self, tmp_path: Path):
        assert restore_categories(tmp_path / "nope.yml") == {}

    def test_valid_yaml_file(self, tmp_path: Path):
        p = tmp_path / "cats.yml"
        p.write_text(yaml.dump({"AMAZON": "Shopping", "TESCO": "Groceries"}))
        result = restore_categories(p)
        assert result == {"AMAZON": "Shopping", "TESCO": "Groceries"}

    def test_empty_file_returns_empty(self, tmp_path: Path):
        p = tmp_path / "empty.yml"
        p.write_text("")
        assert restore_categories(p) == {}

    def test_non_dict_yaml_returns_empty(self, tmp_path: Path):
        p = tmp_path / "list.yml"
        p.write_text("- a\n- b\n")
        assert restore_categories(p) == {}

    def test_nested_dict_still_dict(self, tmp_path: Path):
        """Top-level is dict → returned as-is (values may not be str)."""
        p = tmp_path / "nested.yml"
        p.write_text("FOO:\n  bar: baz\n")
        result = restore_categories(p)
        assert isinstance(result, dict)
        assert "FOO" in result


# ── categorise ────────────────────────────────────────────────────────


class TestCategorise:
    """Tests for categorise()."""

    CATEGORIES = {
        "AMAZON": "Shopping",
        "TESCO": "Groceries",
        "UBER": "Transport",
        "NETFLIX": "Entertainment",
    }

    def test_exact_match(self):
        assert categorise("AMAZON", self.CATEGORIES) == "Shopping"

    def test_case_insensitive(self):
        assert categorise("amazon marketplace", self.CATEGORIES) == "Shopping"
        assert categorise("Uber Trip", self.CATEGORIES) == "Transport"

    def test_prefix_match(self):
        assert categorise("TESCO STORE 1234", self.CATEGORIES) == "Groceries"

    def test_first_match_wins(self):
        cats = {"FOO": "First", "FOO BAR": "Second"}
        assert categorise("FOO BAR BAZ", cats) == "First"

    def test_no_match_returns_uncategorised(self):
        assert categorise("UNKNOWN MERCHANT", self.CATEGORIES) == "Uncategorised"

    def test_empty_categories(self):
        assert categorise("ANYTHING", {}) == "Uncategorised"

    def test_empty_merchant(self):
        assert categorise("", self.CATEGORIES) == "Uncategorised"

    def test_partial_prefix_no_false_positive(self):
        """'AMAZ' alone should not match 'AMAZON' prefix."""
        assert categorise("AMAZ", self.CATEGORIES) == "Uncategorised"
