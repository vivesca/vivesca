"""Tests for generate-solutions-index.py effector."""

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
    # Should skip frontmatter and get content
    assert "Content after frontmatter" in result


def test_extract_description_extracts_title_from_frontmatter(tmp_path):
    """Test extract_description extracts title from frontmatter."""
    f = tmp_path / "test.md"
    f.write_text("---\ntitle: \"My Document Title\"\n---\n\nOther content.")
    
    result = gensi.extract_description(f)
    assert result == "My Document Title"


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


def test_extract_description_skips_module_category(tmp_path):
    """Test extract_description skips module: and category: lines."""
    f = tmp_path / "test.md"
    f.write_text("---\nmodule: test\ncategory: example\ntitle: Real Title\n---\n\nActual content.")
    
    result = gensi.extract_description(f)
    # Should get title, not module or category
    assert result == "Real Title"


# ---------------------------------------------------------------------------
# Test generate_index
# ---------------------------------------------------------------------------

def test_generate_index_returns_string():
    """Test generate_index returns a string."""
    # This will use the actual ~/docs/solutions directory
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


def test_generate_index_skips_index_md(tmp_path):
    """Test generate_index skips INDEX.md files."""
    # Create a mock SOLUTIONS directory
    solutions = tmp_path / "solutions"
    solutions.mkdir()
    (solutions / "test.md").write_text("# Test\n\nContent")
    (solutions / "INDEX.md").write_text("# Index\n\nThis should be skipped.")
    (solutions / "schema.md").write_text("# Schema\n\nSchema content.")
    
    # Patch SOLUTIONS path
    with patch.object(gensi, 'SOLUTIONS', solutions):
        result = gensi.generate_index()
    
    # Should include test.md but not INDEX.md or schema.md
    assert "test" in result.lower()
    assert "schema" not in result.lower()


def test_generate_index_handles_categories(tmp_path):
    """Test generate_index creates categories from subdirectories."""
    solutions = tmp_path / "solutions"
    solutions.mkdir()
    (solutions / "general.md").write_text("# General\n\nGeneral content.")
    
    category_dir = solutions / "category1"
    category_dir.mkdir()
    (category_dir / "item.md").write_text("# Item\n\nItem content.")
    
    with patch.object(gensi, 'SOLUTIONS', solutions):
        result = gensi.generate_index()
    
    assert "General" in result
    assert "Category1" in result or "category1" in result


def test_generate_index_general_first():
    """Test generate_index puts 'general' category first."""
    solutions = tmp_path / "solutions"
    solutions.mkdir()
    (solutions / "aaa.md").write_text("# A\n\nA content.")
    
    zzz_dir = solutions / "zzz"
    zzz_dir.mkdir()
    (zzz_dir / "item.md").write_text("# Z\n\nZ content.")
    
    with patch.object(gensi, 'SOLUTIONS', solutions):
        result = gensi.generate_index()
    
    # General should appear before zzz in output
    general_pos = result.find("General")
    zzz_pos = result.find("Zzz")
    assert general_pos < zzz_pos


def test_generate_index_includes_dates():
    """Test generate_index includes dates."""
    solutions = tmp_path / "solutions"
    solutions.mkdir()
    (solutions / "test.md").write_text("# Test\n\nContent")
    
    with patch.object(gensi, 'SOLUTIONS', solutions):
        result = gensi.generate_index()
    
    # Should have a date in format YYYY-MM-DD
    import re
    dates = re.findall(r'\d{4}-\d{2}-\d{2}', result)
    assert len(dates) > 0


def test_generate_index_sorts_by_mtime(tmp_path):
    """Test generate_index sorts entries by modification time."""
    solutions = tmp_path / "solutions"
    solutions.mkdir()
    
    # Create files with different mtimes
    f1 = solutions / "older.md"
    f1.write_text("# Older\n\nOlder content")
    
    f2 = solutions / "newer.md"
    f2.write_text("# Newer\n\nNewer content")
    
    # Set different mtimes
    import time
    os.utime(f1, (1000000000, 1000000000))  # Old
    os.utime(f2, (2000000000, 2000000000))  # Newer
    
    with patch.object(gensi, 'SOLUTIONS', solutions):
        result = gensi.generate_index()
    
    # Newer should appear first (reverse sort)
    newer_pos = result.find("Newer")
    older_pos = result.find("Older")
    assert newer_pos < older_pos


def test_generate_index_format():
    """Test generate_index uses correct markdown format for entries."""
    solutions = tmp_path / "solutions"
    solutions.mkdir()
    (solutions / "my-solution.md").write_text("# My Solution\n\nDescription here.")
    
    with patch.object(gensi, 'SOLUTIONS', solutions):
        result = gensi.generate_index()
    
    # Should use proper markdown list format
    assert "- **" in result  # Bold name
    assert "my solution" in result.lower()


def test_generate_index_handles_description_or_not(tmp_path):
    """Test generate_index handles entries with and without descriptions."""
    solutions = tmp_path / "solutions"
    solutions.mkdir()
    (solutions / "with_desc.md").write_text("# Test\n\nHas description.")
    (solutions / "no_desc.md").write_text("# Test\n\n")  # Empty after heading
    
    with patch.object(gensi, 'SOLUTIONS', solutions):
        result = gensi.generate_index()
    
    # Both should appear (one with description, one with date only)
    assert "with desc" in result.lower()
    assert "no desc" in result.lower()


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


# ---------------------------------------------------------------------------
# Test main function
# ---------------------------------------------------------------------------

def test_main_dry_run_calls_generate():
    """Test main with --dry-run generates index without writing."""
    mock_content = "# Test Index\n\nTest content."
    
    with patch.object(gensi, 'generate_index', return_value=mock_content):
        with patch('sys.argv', ['generate-solutions-index.py', '--dry-run']):
            with patch('builtins.print') as mock_print:
                gensi.main()
                # Should print the content
                printed = [str(call) for call in mock_print.call_args_list]
                assert any("Test Index" in p for p in printed)


def test_main_writes_file():
    """Test main writes to INDEX path when not dry-run."""
    mock_content = "# Test Index\n\nTest content."
    mock_path = MagicMock()
    
    with patch.object(gensi, 'generate_index', return_value=mock_content):
        with patch.object(gensi, 'INDEX', mock_path):
            with patch('sys.argv', ['generate-solutions-index.py']):
                with patch('builtins.print'):
                    gensi.main()
                    # Should have written to INDEX
                    mock_path.write_text.assert_called_once_with(mock_content)


# ---------------------------------------------------------------------------
# Test edge cases
# ---------------------------------------------------------------------------

def test_extract_description_permission_error(tmp_path):
    """Test extract_description handles PermissionError."""
    f = tmp_path / "test.md"
    f.write_text("Content")
    
    with patch('builtins.open', side_effect=PermissionError("No access")):
        result = gensi.extract_description(f)
        assert result == ""


def test_generate_index_empty_directory(tmp_path):
    """Test generate_index handles empty directory."""
    solutions = tmp_path / "solutions"
    solutions.mkdir()
    
    with patch.object(gensi, 'SOLUTIONS', solutions):
        result = gensi.generate_index()
    
    assert "# Solutions KB Index" in result
    assert "0 files" in result


def test_generate_index_hidden_files_ignored(tmp_path):
    """Test generate_index ignores hidden files."""
    solutions = tmp_path / "solutions"
    solutions.mkdir()
    (solutions / "visible.md").write_text("# Visible\n\nContent")
    (solutions / ".hidden.md").write_text("# Hidden\n\nHidden content")
    
    with patch.object(gensi, 'SOLUTIONS', solutions):
        result = gensi.generate_index()
    
    assert "visible" in result.lower()
    # Hidden file should not appear (it would have "hidden" in stem)
    # But we check that .hidden.md specifically isn't there
    assert ".hidden" not in result
