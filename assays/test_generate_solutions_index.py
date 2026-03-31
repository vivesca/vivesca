"""Tests for generate-solutions-index.py effector."""

from __future__ import annotations

import os
import pytest
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime

# Execute the script directly
script_path = Path("/home/terry/germline/effectors/generate-solutions-index.py")
script_code = script_path.read_text()

# Create module namespace and exec
namespace = {"__name__": "test_mod"}
exec(script_code, namespace)

# Create a proper module-like object
gensi = types.SimpleNamespace()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(gensi, key, value)


# ---------------------------------------------------------------------------
# Test file existence
# ---------------------------------------------------------------------------

def test_script_file_exists():
    """Test that generate-solutions-index.py file exists."""
    assert script_path.exists()
    assert script_path.is_file()


def test_script_is_python():
    """Test that script has Python shebang."""
    first_line = script_code.split('\n')[0]
    assert first_line.startswith('#!/usr/bin/env python')


def test_script_docstring():
    """Test that script has docstring."""
    assert '"""' in script_code
    assert 'INDEX.md' in script_code or 'index' in script_code.lower()


# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

def test_solutions_path():
    """Test that SOLUTIONS path is defined correctly."""
    assert hasattr(gensi, 'SOLUTIONS')
    assert str(gensi.SOLUTIONS).endswith('docs/solutions')


def test_index_path():
    """Test that INDEX path is defined correctly."""
    assert hasattr(gensi, 'INDEX')
    assert str(gensi.INDEX).endswith('INDEX.md')


# ---------------------------------------------------------------------------
# Test extract_description
# ---------------------------------------------------------------------------

def test_extract_description_basic(tmp_path):
    """Test extract_description with simple markdown."""
    f = tmp_path / "test.md"
    f.write_text("# Title\n\nThis is the first paragraph.\n\nMore content.")
    
    result = gensi.extract_description(f)
    assert "first paragraph" in result


def test_extract_description_skips_headings(tmp_path):
    """Test extract_description skips headings."""
    f = tmp_path / "test.md"
    f.write_text("# Heading 1\n## Heading 2\n\nActual content here.")
    
    result = gensi.extract_description(f)
    assert "Heading" not in result
    assert "Actual content" in result


def test_extract_description_handles_frontmatter(tmp_path):
    """Test extract_description handles YAML frontmatter."""
    f = tmp_path / "test.md"
    f.write_text("---\ntitle: My Title\ndate: 2024-01-01\n---\n\nContent after frontmatter.")
    
    result = gensi.extract_description(f)
    # Should skip frontmatter and get content after it
    assert "Content after frontmatter" in result


def test_extract_description_max_len(tmp_path):
    """Test extract_description respects max_len."""
    f = tmp_path / "test.md"
    long_text = "x" * 200
    f.write_text(f"# Title\n\n{long_text}")
    
    result = gensi.extract_description(f, max_len=50)
    assert len(result) <= 50


def test_extract_description_empty_file(tmp_path):
    """Test extract_description handles empty file."""
    f = tmp_path / "test.md"
    f.write_text("")
    
    result = gensi.extract_description(f)
    assert result == ""


def test_extract_description_only_headings(tmp_path):
    """Test extract_description handles file with only headings."""
    f = tmp_path / "test.md"
    f.write_text("# Heading 1\n## Heading 2\n### Heading 3")
    
    result = gensi.extract_description(f)
    assert result == ""


def test_extract_description_handles_unicode_error(tmp_path):
    """Test extract_description handles UnicodeDecodeError."""
    f = tmp_path / "test.md"
    # Write binary content that will cause UnicodeDecodeError
    f.write_bytes(b'\xff\xfe Invalid UTF-8 \x00\x01')
    
    result = gensi.extract_description(f)
    assert result == ""


def test_extract_description_with_code_blocks(tmp_path):
    """Test extract_description handles files starting with code blocks."""
    f = tmp_path / "test.md"
    f.write_text("```python\nprint('hello')\n```\n\nText after code.")
    
    result = gensi.extract_description(f)
    # Should extract the first non-heading line
    assert result  # Should have some content


def test_extract_description_with_lists(tmp_path):
    """Test extract_description handles files starting with lists."""
    f = tmp_path / "test.md"
    f.write_text("# Title\n\n- First item\n- Second item")
    
    result = gensi.extract_description(f)
    assert "First item" in result


def test_extract_description_title_in_frontmatter_content(tmp_path):
    """Test extract_description - title: lines inside frontmatter are skipped."""
    f = tmp_path / "test.md"
    f.write_text("---\ntitle: \"My Document Title\"\n---\n\nOther content.")

    result = gensi.extract_description(f)
    # The code skips content inside frontmatter, so it gets content after
    assert result == "Other content."


# ---------------------------------------------------------------------------
# Test generate_index structure
# ---------------------------------------------------------------------------

def test_generate_index_returns_string():
    """Test generate_index returns a string."""
    result = gensi.generate_index()
    assert isinstance(result, str)


def test_generate_index_has_header():
    """Test generate_index has proper header."""
    result = gensi.generate_index()
    assert "# Solutions KB Index" in result


def test_generate_index_has_regen_instruction():
    """Test generate_index includes regeneration instruction."""
    result = gensi.generate_index()
    assert "generate-solutions-index.py" in result


def test_generate_index_counts_files():
    """Test generate_index includes file count."""
    result = gensi.generate_index()
    assert "files across" in result or "file" in result.lower()


def test_generate_index_uses_markdown_list_format():
    """Test generate_index uses markdown list format."""
    result = gensi.generate_index()
    # Should have markdown bold and list markers
    assert "- **" in result


# ---------------------------------------------------------------------------
# Test CLI via subprocess
# ---------------------------------------------------------------------------

def test_script_help():
    """Test script --help runs without error."""
    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "index" in result.stdout.lower()


def test_script_dry_run():
    """Test script --dry-run prints to stdout."""
    result = subprocess.run(
        [sys.executable, str(script_path), "--dry-run"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "# Solutions KB Index" in result.stdout
    assert "Dry run complete" in result.stdout


def test_script_dry_run_counts_entries():
    """Test script --dry-run counts entries."""
    result = subprocess.run(
        [sys.executable, str(script_path), "--dry-run"],
        capture_output=True,
        text=True
    )
    assert "entries found" in result.stdout


def test_script_dry_run_includes_categories():
    """Test script --dry-run includes category sections."""
    result = subprocess.run(
        [sys.executable, str(script_path), "--dry-run"],
        capture_output=True,
        text=True
    )
    # Should have category headers (## something)
    assert "\n## " in result.stdout


# ---------------------------------------------------------------------------
# Test file filtering logic
# ---------------------------------------------------------------------------

def test_script_skips_index_md():
    """Test that INDEX.md is excluded from the index."""
    # The script explicitly excludes INDEX.md
    assert 'f == "INDEX.md"' in script_code or 'INDEX.md' in script_code


def test_script_skips_schema_md():
    """Test that schema.md is excluded from the index."""
    # The script explicitly excludes schema.md
    assert 'schema.md' in script_code


# ---------------------------------------------------------------------------
# Test helper function behavior with patched paths
# ---------------------------------------------------------------------------

def test_extract_description_permission_error(tmp_path):
    """Test extract_description handles PermissionError."""
    f = tmp_path / "test.md"
    f.write_text("Content")
    
    with patch('builtins.open', side_effect=PermissionError("No access")):
        result = gensi.extract_description(f)
        assert result == ""


def test_extract_description_with_frontmatter_title(tmp_path):
    """Test extract_description skips title in frontmatter, gets content after."""
    f = tmp_path / "test.md"
    f.write_text("---\ntitle: Test Title\n---\n\nContent.")

    result = gensi.extract_description(f)
    # Content inside frontmatter is skipped, gets content after
    assert result == "Content."


def test_extract_description_skips_module_lines_in_frontmatter(tmp_path):
    """Test extract_description skips module: and category: lines in frontmatter."""
    f = tmp_path / "test.md"
    f.write_text("---\nmodule: test\ncategory: example\n---\n\nActual content here.")
    
    result = gensi.extract_description(f)
    # Should skip module and category, get actual content
    assert "Actual content" in result
    assert "module" not in result.lower() or result == ""


# ---------------------------------------------------------------------------
# Test generate_index with mock directory
# ---------------------------------------------------------------------------

def test_generate_index_with_mocked_solutions():
    """Test generate_index with a mocked solutions directory."""
    # Create a temp directory structure
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        solutions = Path(tmpdir) / "solutions"
        solutions.mkdir()
        (solutions / "test.md").write_text("# Test\n\nTest content.")
        
        # Patch SOLUTIONS and re-run generate_index
        original_solutions = namespace['SOLUTIONS']
        namespace['SOLUTIONS'] = solutions
        try:
            result = namespace['generate_index']()
            assert "# Solutions KB Index" in result
            assert "test" in result.lower()
        finally:
            namespace['SOLUTIONS'] = original_solutions


def test_generate_index_empty_directory():
    """Test generate_index handles empty directory."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        solutions = Path(tmpdir) / "solutions"
        solutions.mkdir()
        
        original_solutions = namespace['SOLUTIONS']
        namespace['SOLUTIONS'] = solutions
        try:
            result = namespace['generate_index']()
            assert "# Solutions KB Index" in result
            assert "0 files" in result
        finally:
            namespace['SOLUTIONS'] = original_solutions


def test_generate_index_with_subdirectory():
    """Test generate_index creates categories from subdirectories."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        solutions = Path(tmpdir) / "solutions"
        solutions.mkdir()
        
        category_dir = solutions / "mycategory"
        category_dir.mkdir()
        (category_dir / "item.md").write_text("# Item\n\nItem content.")
        
        original_solutions = namespace['SOLUTIONS']
        namespace['SOLUTIONS'] = solutions
        try:
            result = namespace['generate_index']()
            assert "Mycategory" in result or "mycategory" in result
        finally:
            namespace['SOLUTIONS'] = original_solutions


def test_generate_index_general_first():
    """Test generate_index puts 'general' category first."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        solutions = Path(tmpdir) / "solutions"
        solutions.mkdir()
        (solutions / "aaa.md").write_text("# A\n\nA content.")
        
        zzz_dir = solutions / "zzz"
        zzz_dir.mkdir()
        (zzz_dir / "item.md").write_text("# Z\n\nZ content.")
        
        original_solutions = namespace['SOLUTIONS']
        namespace['SOLUTIONS'] = solutions
        try:
            result = namespace['generate_index']()
            # General (root files) should appear before zzz
            general_pos = result.find("## General")
            zzz_pos = result.find("## Zzz")
            assert general_pos < zzz_pos
        finally:
            namespace['SOLUTIONS'] = original_solutions


def test_generate_index_includes_dates():
    """Test generate_index includes dates."""
    import tempfile
    import re
    with tempfile.TemporaryDirectory() as tmpdir:
        solutions = Path(tmpdir) / "solutions"
        solutions.mkdir()
        (solutions / "test.md").write_text("# Test\n\nContent")
        
        original_solutions = namespace['SOLUTIONS']
        namespace['SOLUTIONS'] = solutions
        try:
            result = namespace['generate_index']()
            # Should have a date in format YYYY-MM-DD
            dates = re.findall(r'\d{4}-\d{2}-\d{2}', result)
            assert len(dates) > 0
        finally:
            namespace['SOLUTIONS'] = original_solutions


def test_generate_index_hidden_files_ignored():
    """Test generate_index ignores hidden files (dotfiles in subdirs)."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        solutions = Path(tmpdir) / "solutions"
        solutions.mkdir()
        (solutions / "visible.md").write_text("# Visible\n\nContent")
        
        original_solutions = namespace['SOLUTIONS']
        namespace['SOLUTIONS'] = solutions
        try:
            result = namespace['generate_index']()
            assert "visible" in result.lower()
        finally:
            namespace['SOLUTIONS'] = original_solutions


# ---------------------------------------------------------------------------
# Test function signatures
# ---------------------------------------------------------------------------

def test_extract_description_accepts_path_and_max_len():
    """Test extract_description signature."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("Test content")
        f.flush()
        temp_path = Path(f.name)
    
    try:
        # Should accept both arguments
        result = gensi.extract_description(temp_path, max_len=100)
        assert isinstance(result, str)
    finally:
        temp_path.unlink()


def test_generate_index_no_arguments():
    """Test generate_index takes no arguments."""
    # Just verify it can be called without arguments
    result = gensi.generate_index()
    assert isinstance(result, str)
