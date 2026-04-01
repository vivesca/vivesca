from __future__ import annotations

"""Tests for effectors/chromatin-decay-report — find orphan and stale notes.

Chromatin-decay-report is a script — loaded via exec(), never imported.
"""

import io
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

CHROMATIN_REPORT_PATH = (
    Path(__file__).resolve().parents[1] / "effectors" / "chromatin-decay-report.py"
)


# ── Fixture ────────────────────────────────────────────────────────────────


@pytest.fixture()
def cr(tmp_path):
    """Load chromatin-decay-report via exec, redirecting paths to tmp_path."""
    notes = tmp_path / "notes"
    notes.mkdir()
    ns: dict = {
        "__name__": "test_chromatin_decay",
        "__file__": str(CHROMATIN_REPORT_PATH),
    }
    source = CHROMATIN_REPORT_PATH.read_text(encoding="utf-8")
    exec(source, ns)
    ns["CHROMATIN_PATH"] = notes
    ns["DAILY_NOTES_PATH"] = notes / "memory"

    # Wrap main() so sys.argv is clean (argparse.parse_args reads sys.argv,
    # which under pytest contains test-runner args that argparse rejects).
    _real_main = ns["main"]

    def _wrapped_main(*a, **kw):
        prev = sys.argv
        sys.argv = ["chromatin-decay-report"]
        try:
            return _real_main(*a, **kw)
        finally:
            sys.argv = prev

    ns["main"] = _wrapped_main
    return ns


def _note(notes_dir: Path, name: str, content: str, **frontmatter) -> Path:
    """Create a markdown note under notes_dir."""
    path = notes_dir / f"{name}.md"
    if frontmatter:
        fm = "---\n"
        for k, v in frontmatter.items():
            fm += f"{k}: {v}\n"
        fm += "---\n"
        content = fm + content
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


# ── File basics ────────────────────────────────────────────────────────────


class TestBasics:
    def test_file_exists(self):
        assert CHROMATIN_REPORT_PATH.exists()

    def test_shebang(self):
        first = CHROMATIN_REPORT_PATH.read_text().split("\n")[0]
        assert first.startswith("#!/usr/bin/env python")

    def test_has_docstring(self):
        content = CHROMATIN_REPORT_PATH.read_text()
        assert '"""' in content


# ── parse_frontmatter ──────────────────────────────────────────────────────


class TestParseFrontmatter:
    def test_valid(self, cr):
        content = "---\ntitle: Test\ntags: [a, b]\n---\n# Content"
        result = cr["parse_frontmatter"](content)
        assert result["title"] == "Test"
        assert result["tags"] == ["a", "b"]

    def test_no_frontmatter(self, cr):
        assert cr["parse_frontmatter"]("# Just content") == {}

    def test_invalid_yaml(self, cr):
        content = "---\ninvalid: [unclosed\n---\nContent"
        assert cr["parse_frontmatter"](content) == {}

    def test_empty(self, cr):
        assert cr["parse_frontmatter"]("") == {}

    def test_empty_frontmatter_block(self, cr):
        result = cr["parse_frontmatter"]("---\n---\n# Content")
        assert result == {}


# ── find_wikilinks ────────────────────────────────────────────────────────


class TestFindWikilinks:
    def test_basic(self, cr):
        assert cr["find_wikilinks"]("See [[A]] and [[B]].") == {"A", "B"}

    def test_alias(self, cr):
        assert cr["find_wikilinks"]("[[Target|display text]]") == {"Target"}

    def test_subpath(self, cr):
        assert "folder/Note" in cr["find_wikilinks"]("[[folder/Note]]")

    def test_no_links(self, cr):
        assert cr["find_wikilinks"]("No links [here](url).") == set()

    def test_dedup(self, cr):
        assert cr["find_wikilinks"]("[[X]] [[X]] [[X]]") == {"X"}

    def test_mixed(self, cr):
        content = "See [[A]], [[B|alias]], [[C/D]], and [[A]] again."
        result = cr["find_wikilinks"](content)
        assert result == {"A", "B", "C/D"}


# ── should_exclude ────────────────────────────────────────────────────────


class TestShouldExclude:
    def test_archive(self, cr):
        assert cr["should_exclude"](Path("/notes/Archive/old.md"))

    def test_templates(self, cr):
        assert cr["should_exclude"](Path("/notes/templates/t.md"))

    def test_obsidian(self, cr):
        assert cr["should_exclude"](Path("/notes/.obsidian/config"))

    def test_normal(self, cr):
        assert not cr["should_exclude"](Path("/notes/projects/idea.md"))

    def test_exclude_patterns_constant(self, cr):
        assert "Archive/" in cr["EXCLUDE_PATTERNS"]
        assert "templates/" in cr["EXCLUDE_PATTERNS"]
        assert ".obsidian/" in cr["EXCLUDE_PATTERNS"]


# ── main ──────────────────────────────────────────────────────────────────


class TestMain:
    def test_empty_dir(self, cr, capsys):
        cr["main"]()
        out = capsys.readouterr().out
        assert "Total notes indexed: 0" in out

    def test_indexes_notes(self, cr, capsys):
        notes = cr["CHROMATIN_PATH"]
        _note(notes, "alpha", "# Alpha\n[[beta]]")
        _note(notes, "beta", "# Beta")
        cr["main"]()
        out = capsys.readouterr().out
        assert "Total notes indexed: 2" in out

    def test_orphan_detection(self, cr, capsys):
        notes = cr["CHROMATIN_PATH"]
        # alpha links to beta → alpha has no incoming → alpha is orphan
        _note(notes, "alpha", "# Alpha\n[[beta]]")
        _note(notes, "beta", "# Beta")
        cr["main"]()
        out = capsys.readouterr().out
        assert "ORPHANS" in out

    def test_no_orphans_when_mutually_linked(self, cr, capsys):
        notes = cr["CHROMATIN_PATH"]
        _note(notes, "a", "# A\n[[b]]")
        _note(notes, "b", "# B\n[[a]]")
        cr["main"]()
        out = capsys.readouterr().out
        assert "ORPHANS (no incoming links): 0" in out

    def test_daily_notes_not_orphans(self, cr, capsys):
        notes = cr["CHROMATIN_PATH"]
        _note(notes, "2024-01-15", "# Daily\nNo links")
        cr["main"]()
        out = capsys.readouterr().out
        assert "ORPHANS (no incoming links): 0" in out

    def test_hub_files_excluded_from_orphans(self, cr, capsys):
        notes = cr["CHROMATIN_PATH"]
        _note(notes, "TODO", "# TODO\nNothing links here")
        cr["main"]()
        out = capsys.readouterr().out
        assert "ORPHANS (no incoming links): 0" in out

    def test_cold_note_detected(self, cr, capsys):
        notes = cr["CHROMATIN_PATH"]
        old = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
        _note(notes, "cold", "# Cold", last_accessed=old, access_count=5)
        cr["main"]()
        out = capsys.readouterr().out
        assert "COLD NOTES" in out

    def test_recent_note_not_cold(self, cr, capsys):
        notes = cr["CHROMATIN_PATH"]
        recent = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        _note(notes, "recent", "# Recent", last_accessed=recent, access_count=1)
        cr["main"]()
        out = capsys.readouterr().out
        assert "COLD NOTES (last accessed > 30 days): 0" in out

    def test_excludes_archive(self, cr, capsys):
        notes = cr["CHROMATIN_PATH"]
        _note(notes, "Archive/old", "# Archived")
        _note(notes, "real", "# Real")
        cr["main"]()
        out = capsys.readouterr().out
        assert "Total notes indexed: 1" in out

    def test_truncates_many_orphans(self, cr, capsys):
        notes = cr["CHROMATIN_PATH"]
        for i in range(25):
            _note(notes, f"lonely_{i}", f"# Lonely {i}")
        cr["main"]()
        out = capsys.readouterr().out
        assert "more" in out

    def test_access_tracking_displayed(self, cr, capsys):
        notes = cr["CHROMATIN_PATH"]
        _note(notes, "tracked", "# Tracked", access_count=3, last_accessed="2025-06-01")
        cr["main"]()
        out = capsys.readouterr().out
        assert "access tracking" in out.lower()

    def test_all_hub_files_excluded_from_orphans(self, cr, capsys):
        """CLAUDE, TODO, Active Pipeline, Job Hunting, Contact Index are never orphans."""
        notes = cr["CHROMATIN_PATH"]
        for name in ["CLAUDE", "TODO", "Active Pipeline", "Job Hunting", "Contact Index"]:
            _note(notes, name, f"# {name}")
        cr["main"]()
        out = capsys.readouterr().out
        assert "ORPHANS (no incoming links): 0" in out

    def test_wikilink_heading_fragment_stripped(self, cr, capsys):
        """Links like [[note#section]] resolve to 'note' in the link graph."""
        notes = cr["CHROMATIN_PATH"]
        _note(notes, "alpha", "# Alpha\n[[beta#intro]]")
        _note(notes, "beta", "# Beta\n[[alpha]]")  # backlink ensures 0 orphans
        cr["main"]()
        out = capsys.readouterr().out
        assert "ORPHANS (no incoming links): 0" in out

    def test_subpath_link_resolves_to_stem(self, cr, capsys):
        """[[folder/deep-note]] counts as incoming link for 'deep-note'."""
        notes = cr["CHROMATIN_PATH"]
        _note(notes, "alpha", "# Alpha\n[[folder/deep-note]]")
        _note(notes, "deep-note", "# Deep\n[[alpha]]")  # backlink ensures 0 orphans
        cr["main"]()
        out = capsys.readouterr().out
        assert "ORPHANS (no incoming links): 0" in out

    def test_invalid_last_accessed_date_ignored(self, cr, capsys):
        """A malformed last_accessed does not crash — just skipped."""
        notes = cr["CHROMATIN_PATH"]
        _note(notes, "baddate", "# Bad", last_accessed="not-a-date", access_count=2)
        cr["main"]()
        out = capsys.readouterr().out
        assert "COLD NOTES (last accessed > 30 days): 0" in out

    def test_mixed_scenario(self, cr, capsys):
        """One orphan, one cold, one tracked — all reported correctly."""
        notes = cr["CHROMATIN_PATH"]
        _note(notes, "orphan", "# Orphan")  # no incoming links
        old = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        _note(notes, "coldy", "# Cold", last_accessed=old, access_count=10)
        _note(notes, "fresh", "# Fresh\n[[coldy]]", access_count=1,
              last_accessed=datetime.now().strftime("%Y-%m-%d"))
        cr["main"]()
        out = capsys.readouterr().out
        assert "Total notes indexed: 3" in out
        assert "ORPHANS (no incoming links): 2" in out
        assert "COLD NOTES (last accessed > 30 days): 1" in out
        assert "access tracking: 2" in out or "Notes with access tracking: 2" in out

    def test_excludes_templates_and_obsidian(self, cr, capsys):
        """Notes under templates/ and .obsidian/ are excluded."""
        notes = cr["CHROMATIN_PATH"]
        _note(notes, "templates/daily", "# Template")
        _note(notes, ".obsidian/config", "# Config")
        _note(notes, "real", "# Real")
        cr["main"]()
        out = capsys.readouterr().out
        assert "Total notes indexed: 1" in out

    def test_cold_note_reports_days(self, cr, capsys):
        """Cold notes show the number of days since last access."""
        notes = cr["CHROMATIN_PATH"]
        old = (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d")
        _note(notes, "stale", "# Stale", last_accessed=old)
        cr["main"]()
        out = capsys.readouterr().out
        assert "45 days ago" in out


# ── CLI subprocess tests ──────────────────────────────────────────────────


class TestCLI:
    def test_runs_without_error(self):
        result = subprocess.run(
            [sys.executable, str(CHROMATIN_REPORT_PATH)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Chromatin Decay Report" in result.stdout
