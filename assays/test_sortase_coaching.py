from __future__ import annotations

import textwrap
import unittest.mock
from pathlib import Path

import pytest

import metabolon.sortase.coaching as coaching_mod
from metabolon.sortase.coaching import (
    _load_coaching_patterns,
    add_coaching_note,
    list_categories,
    load_coaching_notes,
    search_coaching,
)


@pytest.fixture()
def coaching_file(tmp_path: Path) -> Path:
    """Create a minimal coaching markdown file."""
    content = textwrap.dedent("""\
        ---
        name: test coaching
        ---

        ## Test Coaching

        ### Code patterns
        - **No hallucinated imports.** Only import functions that already exist.
        - **Preserve return types.** Don't flatten distinct result classes.

        ### Execution discipline
        - **Read the original file fully** before rewriting.
        - **Run `ast.parse()`** on every Python file after editing.
    """)
    path = tmp_path / "test_coaching.md"
    path.write_text(content, encoding="utf-8")
    return path


class TestLoadCoachingNotes:
    def test_load_coaching_notes_parses_categories(self, coaching_file: Path) -> None:
        entries = load_coaching_notes(coaching_file)
        categories = [entry["category"] for entry in entries]

        assert "Code patterns" in categories
        assert "Execution discipline" in categories

    def test_load_coaching_notes_parses_notes(self, coaching_file: Path) -> None:
        entries = load_coaching_notes(coaching_file)
        code_patterns = next(e for e in entries if e["category"] == "Code patterns")

        assert len(code_patterns["notes"]) == 2
        assert any("hallucinated imports" in note for note in code_patterns["notes"])

    def test_load_coaching_notes_missing_file(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent.md"
        assert load_coaching_notes(missing) == []


class TestAddCoachingNote:
    def test_add_coaching_note_appends(self, coaching_file: Path) -> None:
        add_coaching_note(
            path=coaching_file,
            category="Code patterns",
            note="**Always check X before Y.** New rule.",
        )

        entries = load_coaching_notes(coaching_file)
        code_patterns = next(e for e in entries if e["category"] == "Code patterns")

        assert len(code_patterns["notes"]) == 3
        assert any("Always check X before Y" in note for note in code_patterns["notes"])

    def test_add_coaching_note_new_category(self, coaching_file: Path) -> None:
        add_coaching_note(
            path=coaching_file,
            category="New category",
            note="**Brand new note.** First entry.",
        )

        entries = load_coaching_notes(coaching_file)
        new_cat = next(e for e in entries if e["category"] == "New category")

        assert len(new_cat["notes"]) == 1
        assert "Brand new note" in new_cat["notes"][0]


class TestListCategories:
    def test_list_categories(self, coaching_file: Path) -> None:
        categories = list_categories(coaching_file)

        assert categories == ["Code patterns", "Execution discipline"]


class TestSearchCoaching:
    def test_search_coaching_finds_match(self, coaching_file: Path) -> None:
        results = search_coaching(coaching_file, "hallucinated")

        assert len(results) == 1
        assert results[0]["category"] == "Code patterns"
        assert any("hallucinated" in note.lower() for note in results[0]["notes"])

    def test_search_coaching_no_match(self, coaching_file: Path) -> None:
        results = search_coaching(coaching_file, "nonexistent_query_xyz")

        assert results == []


class TestLoadCoachingPatterns:
    def test_load_coaching_patterns_extracts_headings_and_bullets(
        self, coaching_file: Path
    ) -> None:
        patterns = _load_coaching_patterns(coaching_file)
        assert len(patterns) >= 4
        assert any("Code patterns" in p for p in patterns)
        assert any("Execution discipline" in p for p in patterns)
        assert any(p.startswith("- **") for p in patterns)

    def test_load_coaching_patterns_missing_file(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent.md"
        assert _load_coaching_patterns(missing) == []

    def test_load_coaching_patterns_uses_default_path(self, tmp_path: Path) -> None:
        notes = tmp_path / "coaching.md"
        notes.write_text("### Import hallucination\n- **No mocking** at wrong level\n")
        with unittest.mock.patch.object(coaching_mod, "DEFAULT_COACHING_PATH", notes):
            patterns = _load_coaching_patterns()
        assert len(patterns) >= 2
        assert patterns[0] == "### Import hallucination"
        assert patterns[1] == "- **No mocking** at wrong level"
