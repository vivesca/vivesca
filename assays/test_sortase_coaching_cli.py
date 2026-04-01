"""Tests for metabolon/sortase/coaching_cli.py."""

from click.testing import CliRunner

from metabolon.sortase.coaching_cli import coaching


class TestCoachingList:
    """Tests for the 'coaching list' command."""

    def test_list_shows_categories_and_counts(self, monkeypatch):
        """Should display categories with note counts in a table."""
        monkeypatch.setattr(
            "metabolon.sortase.coaching_cli.load_coaching_notes",
            lambda: [
                {"category": "Code patterns", "notes": ["note1", "note2", "note3"]},
                {"category": "Execution", "notes": ["note4"]},
            ],
        )
        runner = CliRunner()
        result = runner.invoke(coaching, ["list"])
        assert result.exit_code == 0
        assert "Code patterns" in result.output
        assert "3" in result.output
        assert "Execution" in result.output
        assert "1" in result.output

    def test_list_empty_notes(self, monkeypatch):
        """Should show message when no notes exist."""
        monkeypatch.setattr(
            "metabolon.sortase.coaching_cli.load_coaching_notes",
            lambda: [],
        )
        runner = CliRunner()
        result = runner.invoke(coaching, ["list"])
        assert result.exit_code == 0
        assert "No coaching notes found" in result.output

    def test_list_category_with_zero_notes(self, monkeypatch):
        """Should handle category with empty notes list."""
        monkeypatch.setattr(
            "metabolon.sortase.coaching_cli.load_coaching_notes",
            lambda: [
                {"category": "Empty category", "notes": []},
            ],
        )
        runner = CliRunner()
        result = runner.invoke(coaching, ["list"])
        assert result.exit_code == 0
        assert "Empty category" in result.output
        assert "0" in result.output


class TestCoachingAdd:
    """Tests for the 'coaching add' command."""

    def test_add_note_success(self, monkeypatch):
        """Should call add_coaching_note and print success message."""
        calls = []

        def mock_add(category: str, note: str):
            calls.append({"category": category, "note": note})

        monkeypatch.setattr(
            "metabolon.sortase.coaching_cli.add_coaching_note",
            mock_add,
        )
        runner = CliRunner()
        result = runner.invoke(
            coaching, ["add", "--category", "Testing", "--note", "Always write tests"]
        )
        assert result.exit_code == 0
        assert "Added note to 'Testing'" in result.output
        assert calls == [{"category": "Testing", "note": "Always write tests"}]

    def test_add_missing_category(self):
        """Should fail when category is not provided."""
        runner = CliRunner()
        result = runner.invoke(coaching, ["add", "--note", "Some note"])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_add_missing_note(self):
        """Should fail when note is not provided."""
        runner = CliRunner()
        result = runner.invoke(coaching, ["add", "--category", "Testing"])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()

    def test_add_with_special_characters(self, monkeypatch):
        """Should handle notes with special characters."""
        calls = []

        def mock_add(category: str, note: str):
            calls.append({"category": category, "note": note})

        monkeypatch.setattr(
            "metabolon.sortase.coaching_cli.add_coaching_note",
            mock_add,
        )
        runner = CliRunner()
        result = runner.invoke(
            coaching,
            [
                "add",
                "--category",
                "Syntax",
                "--note",
                "Avoid `TODO` and `FIXME` placeholders!",
            ],
        )
        assert result.exit_code == 0
        assert calls[0]["note"] == "Avoid `TODO` and `FIXME` placeholders!"


class TestCoachingSearch:
    """Tests for the 'coaching search' command."""

    def test_search_finds_matches(self, monkeypatch):
        """Should display matching notes in a table."""
        monkeypatch.setattr(
            "metabolon.sortase.coaching_cli.search_coaching",
            lambda query: [
                {
                    "category": "Code patterns",
                    "notes": ["No hallucinated imports", "Never duplicate imports"],
                }
            ],
        )
        runner = CliRunner()
        result = runner.invoke(coaching, ["search", "imports"])
        assert result.exit_code == 0
        assert "imports" in result.output.lower()
        assert "Code patterns" in result.output

    def test_search_no_matches(self, monkeypatch):
        """Should show message when no matches found."""
        monkeypatch.setattr(
            "metabolon.sortase.coaching_cli.search_coaching",
            lambda query: [],
        )
        runner = CliRunner()
        result = runner.invoke(coaching, ["search", "nonexistent"])
        assert result.exit_code == 0
        assert "No matches for 'nonexistent'" in result.output

    def test_search_multiple_categories(self, monkeypatch):
        """Should display results from multiple categories."""
        monkeypatch.setattr(
            "metabolon.sortase.coaching_cli.search_coaching",
            lambda query: [
                {"category": "Code patterns", "notes": ["Test first"]},
                {"category": "Execution", "notes": ["Test twice"]},
            ],
        )
        runner = CliRunner()
        result = runner.invoke(coaching, ["search", "test"])
        assert result.exit_code == 0
        assert "Code patterns" in result.output
        assert "Execution" in result.output

    def test_search_preserves_query(self, monkeypatch):
        """Should pass query correctly to search function."""
        captured = {}

        def mock_search(query: str):
            captured["query"] = query
            return []

        monkeypatch.setattr(
            "metabolon.sortase.coaching_cli.search_coaching",
            mock_search,
        )
        runner = CliRunner()
        runner.invoke(coaching, ["search", "case-sensitive"])
        assert captured["query"] == "case-sensitive"


class TestCoachingGroup:
    """Tests for the coaching CLI group."""

    def test_help_shows_subcommands(self):
        """Should list all available subcommands in help."""
        runner = CliRunner()
        result = runner.invoke(coaching, ["--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "add" in result.output
        assert "search" in result.output

    def test_list_help(self):
        """Should show help for list subcommand."""
        runner = CliRunner()
        result = runner.invoke(coaching, ["list", "--help"])
        assert result.exit_code == 0
        assert "Show all coaching categories" in result.output

    def test_add_help(self):
        """Should show help for add subcommand."""
        runner = CliRunner()
        result = runner.invoke(coaching, ["add", "--help"])
        assert result.exit_code == 0
        assert "--category" in result.output
        assert "--note" in result.output

    def test_search_help(self):
        """Should show help for search subcommand."""
        runner = CliRunner()
        result = runner.invoke(coaching, ["search", "--help"])
        assert result.exit_code == 0
        assert "QUERY" in result.output or "keyword" in result.output.lower()
