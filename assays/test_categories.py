from __future__ import annotations

"""Tests for metabolon.respirometry.categories."""

from pathlib import Path
import tempfile
from metabolon.respirometry.categories import restore_categories, categorise


class TestRestoreCategories:
    """Tests for restore_categories."""


    def test_file_not_exists_returns_empty_dict(self) -> None:
        """If file doesn't exist, return empty dict."""
        result = restore_categories(Path("/nonexistent/path.yaml"))
        assert result == {}

    def test_valid_yaml_returns_map(self) -> None:
        """Valid YAML returns the category map."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
STARBUCKS: Food
APPLE: Electronics
HSBC: Banking
""")
            path = Path(f.name)

        try:
            result = restore_categories(path)
            assert result == {
                "STARBUCKS": "Food",
                "APPLE": "Electronics",
                "HSBC": "Banking",
            }
        finally:
            path.unlink()

    def test_invalid_yaml_returns_empty(self) -> None:
        """If YAML is not a dict, return empty dict."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("just a string, not a dict")
            path = Path(f.name)

        try:
            result = restore_categories(path)
            assert result == {}
        finally:
            path.unlink()


class TestCategorise:
    """Tests for categorise."""

    def test_no_match_returns_uncategorised(self) -> None:
        """No prefix match -> Uncategorised."""
        cat_map = {"STARBUCKS": "Food", "APPLE": "Electronics"}
        result = categorise("GOOGLE", cat_map)
        assert result == "Uncategorised"

    def test_exact_match(self) -> None:
        """Exact prefix match works."""
        cat_map = {"STARBUCKS": "Food", "APPLE": "Electronics"}
        result = categorise("STARBUCKS", cat_map)
        assert result == "Food"

    def test_prefix_match_case_insensitive(self) -> None:
        """Match is case-insensitive on merchant and prefix."""
        cat_map = {"starbucks": "Food"}
        result = categorise("Starbucks Reserve", cat_map)
        assert result == "Food"

        cat_map2 = {"STARBUCKS": "Food"}
        result2 = categorise("starbucks", cat_map2)
        assert result2 == "Food"

    def test_first_match_wins(self) -> None:
        """First matching prefix wins."""
        cat_map = {
            "APP": "Fruit",
            "APPLE": "Electronics",
        }
        result = categorise("APPLE STORE", cat_map)
        assert result == "Fruit"  # First match "APP" wins
