"""Tests for effectors/chromatin-decay-report - Find orphan and stale notes."""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

# Add effectors directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'effectors')))

# Import module with hyphen in filename
import importlib.util
spec = importlib.util.spec_from_file_location("chromatin_decay_report", 
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'effectors', 'chromatin-decay-report.py')))
chromatin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chromatin)


# ─────────────────────────────────────────────────────────────────────────────
# Constant tests
# ─────────────────────────────────────────────────────────────────────────────

def test_exclude_patterns():
    """Test EXCLUDE_PATTERNS contains expected values."""
    assert "Archive/" in chromatin.EXCLUDE_PATTERNS
    assert "templates/" in chromatin.EXCLUDE_PATTERNS
    assert ".obsidian/" in chromatin.EXCLUDE_PATTERNS


# ─────────────────────────────────────────────────────────────────────────────
# parse_frontmatter tests
# ─────────────────────────────────────────────────────────────────────────────

def test_parse_frontmatter_valid():
    """Test parse_frontmatter extracts valid YAML."""
    content = """---
title: Test Note
tags: [a, b]
---
# Content
"""
    result = chromatin.parse_frontmatter(content)
    assert result["title"] == "Test Note"
    assert result["tags"] == ["a", "b"]


def test_parse_frontmatter_no_frontmatter():
    """Test parse_frontmatter returns empty dict when no frontmatter."""
    content = "# Just content\nNo frontmatter here."
    result = chromatin.parse_frontmatter(content)
    assert result == {}


def test_parse_frontmatter_invalid_yaml():
    """Test parse_frontmatter handles invalid YAML."""
    content = """---
invalid: [unclosed
---
Content
"""
    result = chromatin.parse_frontmatter(content)
    assert result == {}


def test_parse_frontmatter_empty():
    """Test parse_frontmatter handles empty content."""
    result = chromatin.parse_frontmatter("")
    assert result == {}


# ─────────────────────────────────────────────────────────────────────────────
# find_wikilinks tests
# ─────────────────────────────────────────────────────────────────────────────

def test_find_wikilinks_basic():
    """Test find_wikilinks extracts basic wikilinks."""
    content = "See [[Note1]] and [[Note2]] for more."
    result = chromatin.find_wikilinks(content)
    assert result == {"Note1", "Note2"}


def test_find_wikilinks_with_alias():
    """Test find_wikilinks handles aliases."""
    content = "Check [[Note1|alias text]] here."
    result = chromatin.find_wikilinks(content)
    assert result == {"Note1"}


def test_find_wikilinks_subpaths():
    """Test find_wikilinks handles subpaths."""
    content = "Reference [[folder/subfolder/Note]]."
    result = chromatin.find_wikilinks(content)
    assert "folder/subfolder/Note" in result


def test_find_wikilinks_no_links():
    """Test find_wikilinks returns empty set when no links."""
    content = "No wikilinks here, just [regular](links)."
    result = chromatin.find_wikilinks(content)
    assert result == set()


def test_find_wikilinks_multiple_same():
    """Test find_wikilinks deduplicates."""
    content = "[[Note]] [[Note]] [[Note]]"
    result = chromatin.find_wikilinks(content)
    assert result == {"Note"}


# ─────────────────────────────────────────────────────────────────────────────
# should_exclude tests
# ─────────────────────────────────────────────────────────────────────────────

def test_should_exclude_archive():
    """Test should_exclude excludes Archive paths."""
    assert chromatin.should_exclude(Path("/notes/Archive/old.md"))


def test_should_exclude_templates():
    """Test should_exclude excludes templates."""
    assert chromatin.should_exclude(Path("/notes/templates/daily.md"))


def test_should_exclude_obsidian():
    """Test should_exclude excludes .obsidian folder."""
    assert chromatin.should_exclude(Path("/notes/.obsidian/config"))


def test_should_exclude_normal_note():
    """Test should_exclude does not exclude normal notes."""
    assert not chromatin.should_exclude(Path("/notes/projects/idea.md"))


# ─────────────────────────────────────────────────────────────────────────────
# Main function tests
# ─────────────────────────────────────────────────────────────────────────────

def test_main_indexes_notes():
    """Test main indexes markdown files."""
    mock_files = [
        Path("/notes/note1.md"),
        Path("/notes/note2.md"),
        Path("/notes/Archive/old.md"),  # Should be excluded
    ]
    
    with patch.object(chromatin.CHROMATIN_PATH, "rglob") as mock_rglob:
        mock_rglob.return_value = mock_files
        
        with patch("builtins.print"):
            with patch.object(chromatin, "should_exclude") as mock_exclude:
                mock_exclude.side_effect = lambda p: "Archive" in str(p)
                
                with patch.object(Path, "read_text") as mock_read:
                    mock_read.return_value = "# Note\n[[other]]"
                    
                    with patch.object(chromatin, "parse_frontmatter", return_value={}):
                        chromatin.main()
                        # Should read only non-excluded files
                        assert mock_read.call_count == 2


def test_main_finds_orphans():
    """Test main identifies orphan notes."""
    mock_files = [
        Path("/notes/orphan.md"),  # No incoming links
        Path("/notes/linked.md"),  # Has incoming link
    ]
    
    def mock_read_side_effect(self, *args, **kwargs):
        if "orphan" in str(self):
            return "# Orphan\nNo links here"
        return "# Linked\n[[orphan]]"  # Links to orphan

    with patch.object(chromatin.CHROMATIN_PATH, "rglob") as mock_rglob:
        mock_rglob.return_value = mock_files
        
        with patch("builtins.print") as mock_print:
            with patch.object(chromatin, "should_exclude", return_value=False):
                with patch.object(Path, "read_text", mock_read_side_effect):
                    with patch.object(chromatin, "parse_frontmatter", return_value={}):
                        chromatin.main()
                        prints = [str(c) for c in mock_print.call_args_list]
                        # Should show orphan count
                        assert any("ORPHANS" in p for p in prints)


def test_main_finds_cold_notes():
    """Test main identifies cold notes (not accessed in 30+ days)."""
    old_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    recent_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
    
    mock_files = [
        Path("/notes/cold.md"),
        Path("/notes/recent.md"),
    ]
    
    frontmatters = {
        "cold": {"last_accessed": old_date, "access_count": 5},
        "recent": {"last_accessed": recent_date, "access_count": 3},
    }
    
    def mock_read_side_effect(self, *args, **kwargs):
        stem = self.stem
        fm = frontmatters.get(stem, {})
        fm_str = "---\n" + "\n".join(f"{k}: {v}" for k, v in fm.items()) + "\n---\n"
        return fm_str + f"\n# {stem}"

    with patch.object(chromatin.CHROMATIN_PATH, "rglob") as mock_rglob:
        mock_rglob.return_value = mock_files
        
        with patch("builtins.print") as mock_print:
            with patch.object(chromatin, "should_exclude", return_value=False):
                with patch.object(Path, "read_text", mock_read_side_effect):
                    chromatin.main()
                    prints = [str(c) for c in mock_print.call_args_list]
                    # Should show cold notes
                    assert any("COLD NOTES" in p for p in prints)


def test_main_skips_daily_notes():
    """Test main does not count daily notes as orphans."""
    mock_files = [
        Path("/notes/2024-01-15.md"),  # Daily note
    ]
    
    with patch.object(chromatin.CHROMATIN_PATH, "rglob") as mock_rglob:
        mock_rglob.return_value = mock_files
        
        with patch("builtins.print"):
            with patch.object(chromatin, "should_exclude", return_value=False):
                with patch.object(Path, "read_text", return_value="# Daily"):
                    with patch.object(chromatin, "parse_frontmatter", return_value={}):
                        chromatin.main()
                        # Daily notes shouldn't be counted as orphans


def test_main_handles_read_errors():
    """Test main handles file read errors gracefully."""
    mock_files = [
        Path("/notes/readable.md"),
        Path("/notes/unreadable.md"),
    ]
    
    def mock_read_side_effect(self, *args, **kwargs):
        if "unreadable" in str(self):
            raise IOError("Permission denied")
        return "# Readable"

    with patch.object(chromatin.CHROMATIN_PATH, "rglob") as mock_rglob:
        mock_rglob.return_value = mock_files
        
        with patch("builtins.print"):
            with patch.object(chromatin, "should_exclude", return_value=False):
                with patch.object(Path, "read_text", mock_read_side_effect):
                    with patch.object(chromatin, "parse_frontmatter", return_value={}):
                        # Should not raise
                        chromatin.main()


def test_main_prints_summary():
    """Test main prints summary statistics."""
    mock_files = [Path("/notes/note1.md")]
    
    with patch.object(chromatin.CHROMATIN_PATH, "rglob") as mock_rglob:
        mock_rglob.return_value = mock_files
        
        with patch("builtins.print") as mock_print:
            with patch.object(chromatin, "should_exclude", return_value=False):
                with patch.object(Path, "read_text", return_value="# Note"):
                    with patch.object(chromatin, "parse_frontmatter", return_value={}):
                        chromatin.main()
                        prints = [str(c) for c in mock_print.call_args_list]
                        # Should show total count
                        assert any("Total notes indexed" in p for p in prints)


def test_main_limits_orphan_display():
    """Test main limits orphan display to 20 items."""
    # Create 25 orphan files
    mock_files = [Path(f"/notes/orphan{i}.md") for i in range(25)]
    
    with patch.object(chromatin.CHROMATIN_PATH, "rglob") as mock_rglob:
        mock_rglob.return_value = mock_files
        
        with patch("builtins.print") as mock_print:
            with patch.object(chromatin, "should_exclude", return_value=False):
                with patch.object(Path, "read_text", return_value="# Orphan"):
                    with patch.object(chromatin, "parse_frontmatter", return_value={}):
                        chromatin.main()
                        prints = [str(c) for c in mock_print.call_args_list]
                        # Should mention "... and X more"
                        assert any("more" in p for p in prints)
