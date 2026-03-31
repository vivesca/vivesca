"""Tests for coaching CLI commands."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from metabolon.sortase.coaching_cli import coaching


class TestCoachingList:
    @patch("metabolon.sortase.coaching_cli.load_coaching_notes")
    def test_list_with_notes(self, mock_load: object) -> None:
        """coaching list shows table with categories and note counts."""
        mock_load.return_value = [
            {"category": "Category A", "notes": ["Note 1", "Note 2"]},
            {"category": "Category B", "notes": ["Note 3"]},
        ]

        runner = CliRunner()
        result = runner.invoke(coaching, ["list"])
        assert result.exit_code == 0
        assert "Category A" in result.output
        assert "2" in result.output
        assert "Category B" in result.output
        assert "1" in result.output

    @patch("metabolon.sortase.coaching_cli.load_coaching_notes")
    def test_list_empty(self, mock_load: object) -> None:
        """coaching list shows message when no notes found."""
        mock_load.return_value = []

        runner = CliRunner()
        result = runner.invoke(coaching, ["list"])
        assert result.exit_code == 0
        assert "No coaching notes found." in result.output


class TestCoachingAdd:
    @patch("metabolon.sortase.coaching_cli.add_coaching_note")
    def test_add_note(self, mock_add: object) -> None:
        """coaching add calls add_coaching_note with correct arguments."""
        runner = CliRunner()
        result = runner.invoke(coaching, ["add", "--category", "Test Cat", "--note", "Test Note"])
        assert result.exit_code == 0
        assert "Added note to 'Test Cat'" in result.output
        mock_add.assert_called_once_with(category="Test Cat", note="Test Note")

    def test_add_missing_options(self) -> None:
        """coaching add fails if required options are missing."""
        runner = CliRunner()
        result = runner.invoke(coaching, ["add", "--category", "Test Cat"])
        assert result.exit_code != 0
        assert "Error: Missing option '--note'" in result.output


class TestCoachingSearch:
    @patch("metabolon.sortase.coaching_cli.search_coaching")
    def test_search_results(self, mock_search: object) -> None:
        """coaching search shows table with matches."""
        mock_search.return_value = [
            {"category": "Category X", "notes": ["Match 1", "Match 2"]},
        ]

        runner = CliRunner()
        result = runner.invoke(coaching, ["search", "match"])
        assert result.exit_code == 0
        assert "Category X" in result.output
        assert "Match 1" in result.output
        assert "Match 2" in result.output

    @patch("metabolon.sortase.coaching_cli.search_coaching")
    def test_search_no_matches(self, mock_search: object) -> None:
        """coaching search shows message when no matches found."""
        mock_search.return_value = []

        runner = CliRunner()
        result = runner.invoke(coaching, ["search", "nothing"])
        assert result.exit_code == 0
        assert "No matches for 'nothing'" in result.output
