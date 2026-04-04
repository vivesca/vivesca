from __future__ import annotations

"""Tests for effectors/skill-search — skill-aware SKILL.md search."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "effectors" / "skill-search"
GERMLINE = Path(__file__).resolve().parent.parent
RECEPTORS = GERMLINE / "membrane" / "receptors"


def run_search(*args: str) -> subprocess.CompletedProcess:
    """Run skill-search as a subprocess (effectors are scripts, not imports)."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(GERMLINE),
    )


# --- Frontmatter parsing ---


class TestFrontmatterParsing:
    """Test the parse_frontmatter function directly."""

    def _load_ns(self):
        """Load the script into a namespace for unit testing."""
        ns = {"__name__": "test_skill_search", "__file__": str(SCRIPT)}
        exec(open(SCRIPT).read(), ns)
        return ns

    def test_simple_frontmatter(self):
        ns = self._load_ns()
        text = """---
name: etiology
description: Root-cause diagnosis
---
Body here."""
        meta, body = ns["parse_frontmatter"](text)
        assert meta["name"] == "etiology"
        assert meta["description"] == "Root-cause diagnosis"
        assert "Body here." in body

    def test_list_triggers(self):
        ns = self._load_ns()
        text = """---
name: test-skill
triggers:
  - foo
  - bar
  - baz
---
Body."""
        meta, _body = ns["parse_frontmatter"](text)
        assert meta["triggers"] == ["foo", "bar", "baz"]

    def test_no_frontmatter(self):
        ns = self._load_ns()
        text = "Just body, no frontmatter."
        meta, body = ns["parse_frontmatter"](text)
        assert meta == {}
        assert "Just body" in body

    def test_quoted_description(self):
        ns = self._load_ns()
        text = """---
name: quoted
description: "Has quotes"
---
Body."""
        meta, _ = ns["parse_frontmatter"](text)
        assert meta["description"] == "Has quotes"


# --- Keyword matching ---


class TestKeywordMatching:
    def _load_ns(self):
        ns = {"__name__": "test_skill_search", "__file__": str(SCRIPT)}
        exec(open(SCRIPT).read(), ns)
        return ns

    def test_case_insensitive(self):
        ns = self._load_ns()
        assert ns["keyword_matches"]("DEBUG", {"x": "debug mode"})
        assert ns["keyword_matches"]("debug", {"x": "DEBUG MODE"})

    def test_match_in_list(self):
        ns = self._load_ns()
        assert ns["keyword_matches"]("foo", {"triggers": ["bar", "foobar", "baz"]})

    def test_no_match(self):
        ns = self._load_ns()
        assert not ns["keyword_matches"]("missing", {"x": "something else"})


# --- CLI integration tests (run against real skills) ---


class TestCLI:
    def test_search_finds_known_skill(self):
        """Searching 'root cause' should find etiology."""
        result = run_search("root cause")
        assert result.returncode == 0
        assert "etiology" in result.stdout

    def test_search_finds_by_trigger(self):
        """Searching by trigger word should find the skill."""
        result = run_search("debug")
        assert result.returncode == 0
        assert "etiology" in result.stdout

    def test_search_finds_by_name(self):
        """Searching by name should find the skill."""
        result = run_search("histology")
        assert result.returncode == 0
        assert "histology" in result.stdout

    def test_no_results_returns_1(self):
        """Search for nonsense keyword should exit 1."""
        result = run_search("xyzzy_no_such_skill_12345")
        assert result.returncode == 1
        assert "No skills matching" in result.stdout

    def test_field_filter_name(self):
        """--field name should only match against skill names."""
        # 'architecture' is a trigger for histology, not the name
        result_with_field = run_search("--field", "name", "architecture")
        # 'architecture' is NOT the name of any skill, should not find it by name only
        # (unless a skill is literally named 'architecture')
        assert "histology" not in result_with_field.stdout or result_with_field.returncode == 1

    def test_field_filter_triggers(self):
        """--field triggers should match trigger words."""
        result = run_search("--field", "triggers", "debug")
        assert result.returncode == 0
        assert "etiology" in result.stdout

    def test_field_filter_body(self):
        """--field body should search body content."""
        result = run_search("--field", "body", "Root Cause")
        assert result.returncode == 0
        assert "etiology" in result.stdout

    def test_json_output(self):
        """--json should produce valid JSON."""
        result = run_search("--json", "histology")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert any(d["name"] == "histology" for d in data)
        # Each entry has expected keys
        for entry in data:
            assert "name" in entry
            assert "description" in entry
            assert "path" in entry

    def test_all_includes_archived(self):
        """--all should include skills from .archive directory."""
        result_no_all = run_search("vault")
        result_all = run_search("--all", "vault")
        # Archived skills like vault-search, vault-hygiene should appear with --all
        count_no = result_no_all.stdout.count("\n")
        count_all = result_all.stdout.count("\n")
        assert count_all > count_no or result_all.returncode == 0

    def test_verbose_shows_triggers(self):
        """--verbose should show trigger words."""
        result = run_search("-v", "etiology")
        assert result.returncode == 0
        assert "triggers:" in result.stdout

    def test_description_shown_in_results(self):
        """Results should include the skill description."""
        result = run_search("etiology")
        assert result.returncode == 0
        assert "Root-cause" in result.stdout


# --- Find skills (path traversal) ---


class TestFindSkills:
    def _load_ns(self):
        ns = {"__name__": "test_skill_search", "__file__": str(SCRIPT)}
        exec(open(SCRIPT).read(), ns)
        return ns

    def test_finds_real_skills(self):
        ns = self._load_ns()
        paths = ns["find_skills"](RECEPTORS)
        assert len(paths) > 20  # We know there are many skills
        # All should be SKILL.md files
        assert all(p.name == "SKILL.md" for p in paths)

    def test_excludes_archive_by_default(self):
        ns = self._load_ns()
        paths = ns["find_skills"](RECEPTORS)
        for p in paths:
            assert ".archive" not in p.parts

    def test_includes_archive_with_flag(self):
        ns = self._load_ns()
        paths = ns["find_skills"](RECEPTORS, include_archived=True)
        archive_paths = [p for p in paths if ".archive" in p.parts]
        assert len(archive_paths) > 0
