from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from metabolon.sortase.coaching_cli import coaching


class TestCoachingList:
    """Tests for the `coaching list` CLI command."""

    def test_list_shows_categories_and_counts(self) -> None:
        fake_entries = [
            {"category": "Syntax", "notes": ["note A", "note B"]},
            {"category": "Testing", "notes": ["note C"]},
        ]
        runner = CliRunner()
        with patch(
            "metabolon.sortase.coaching_cli.load_coaching_notes",
            return_value=fake_entries,
        ):
            result = runner.invoke(coaching, ["list"])

        assert result.exit_code == 0
        assert "Syntax" in result.output
        assert "Testing" in result.output
        assert "2" in result.output
        assert "1" in result.output

    def test_list_empty_notes(self) -> None:
        runner = CliRunner()
        with patch(
            "metabolon.sortase.coaching_cli.load_coaching_notes",
            return_value=[],
        ):
            result = runner.invoke(coaching, ["list"])

        assert result.exit_code == 0
        assert "No coaching notes found" in result.output


class TestCoachingAdd:
    """Tests for the `coaching add` CLI command."""

    def test_add_calls_add_coaching_note(self) -> None:
        runner = CliRunner()
        with patch("metabolon.sortase.coaching_cli.add_coaching_note") as mock_add:
            result = runner.invoke(
                coaching, ["add", "--category", "Patterns", "--note", "Use flat params"]
            )

        assert result.exit_code == 0
        mock_add.assert_called_once_with(category="Patterns", note="Use flat params")

    def test_add_prints_success(self) -> None:
        runner = CliRunner()
        with patch("metabolon.sortase.coaching_cli.add_coaching_note"):
            result = runner.invoke(
                coaching, ["add", "--category", "Bugfix", "--note", "Fix the thing"]
            )

        assert result.exit_code == 0
        assert "Bugfix" in result.output

    def test_add_missing_category_option(self) -> None:
        runner = CliRunner()
        with patch("metabolon.sortase.coaching_cli.add_coaching_note"):
            result = runner.invoke(coaching, ["add", "--note", "orphan"])

        assert result.exit_code != 0

    def test_add_missing_note_option(self) -> None:
        runner = CliRunner()
        with patch("metabolon.sortase.coaching_cli.add_coaching_note"):
            result = runner.invoke(coaching, ["add", "--category", "Cat"])

        assert result.exit_code != 0


class TestCoachingSearch:
    """Tests for the `coaching search` CLI command."""

    def test_search_returns_matching_results(self) -> None:
        fake_results = [
            {"category": "Patterns", "notes": ["Use if/elif dispatch"]},
        ]
        runner = CliRunner()
        with patch(
            "metabolon.sortase.coaching_cli.search_coaching",
            return_value=fake_results,
        ):
            result = runner.invoke(coaching, ["search", "dispatch"])

        assert result.exit_code == 0
        assert "Patterns" in result.output
        assert "Use if/elif dispatch" in result.output

    def test_search_no_matches(self) -> None:
        runner = CliRunner()
        with patch(
            "metabolon.sortase.coaching_cli.search_coaching",
            return_value=[],
        ):
            result = runner.invoke(coaching, ["search", "nonexistent"])

        assert result.exit_code == 0
        assert "No matches for 'nonexistent'" in result.output

    def test_search_multiple_results(self) -> None:
        fake_results = [
            {"category": "A", "notes": ["match one"]},
            {"category": "B", "notes": ["match two"]},
        ]
        runner = CliRunner()
        with patch(
            "metabolon.sortase.coaching_cli.search_coaching",
            return_value=fake_results,
        ):
            result = runner.invoke(coaching, ["search", "match"])

        assert result.exit_code == 0
        assert "A" in result.output
        assert "B" in result.output
        assert "match one" in result.output
        assert "match two" in result.output
