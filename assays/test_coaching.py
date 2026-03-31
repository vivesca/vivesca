from __future__ import annotations
"""Tests for metabolon.sortase.coaching."""

import tempfile
from pathlib import Path

from metabolon.sortase.coaching import (
    load_coaching_notes,
    list_categories,
    add_coaching_note,
    search_coaching,
)


def test_load_coaching_notes_parses():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("""
### Testing
- Write more unit tests
- Run tests before committing

### Refactoring
- Keep functions small
- Respect single responsibility principle
""".lstrip())
    path = Path(f.name)
    try:
        entries = load_coaching_notes(path)
        assert len(entries) == 2
        assert entries[0]["category"] == "Testing"
        assert len(entries[0]["notes"]) == 2
        assert "Write more unit tests" in entries[0]["notes"]
        assert entries[1]["category"] == "Refactoring"
    finally:
        path.unlink()


def test_load_coaching_notes_missing_file():
    entries = load_coaching_notes(Path("/nonexistent.md"))
    assert entries == []


def test_list_categories():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("""
### CatA
- note 1

### CatB
- note 2
""")
    path = Path(f.name)
    try:
        categories = list_categories(path)
        assert categories == ["CatA", "CatB"]
    finally:
        path.unlink()


def test_add_coaching_note_appends_to_existing():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("""
### Testing
- First note
""")
    path = Path(f.name)
    try:
        add_coaching_note(path, "Testing", "Second note")
        content = path.read_text()
        assert "Second note" in content
        lines = content.splitlines()
        # Check that it was inserted after existing bullets
        bullet_count = sum(1 for line in lines if line.startswith("- "))
        assert bullet_count == 2
    finally:
        path.unlink()


def test_add_coaching_note_creates_new_category():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("""
### Existing
- note
""")
    path = Path(f.name)
    try:
        add_coaching_note(path, "NewCategory", "New note")
        content = path.read_text()
        assert "### NewCategory" in content
        assert "- New note" in content
    finally:
        path.unlink()


def test_search_coaching_finds_matches():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("""
### Testing
- Write tests
- Run CI

### Performance
- Optimize slow queries
""")
    path = Path(f.name)
    try:
        results = search_coaching(path, "tests")
        assert len(results) == 1
        assert results[0]["category"] == "Testing"
        assert len(results[0]["notes"]) == 1
    finally:
        path.unlink()


def test_search_coaching_no_match():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("""
### Testing
- Write tests
""")
    path = Path(f.name)
    try:
        results = search_coaching(path, "nonexistent")
        assert results == []
    finally:
        path.unlink()
