#!/usr/bin/env python3
"""Tests for taste-score effector."""

import pytest
import os
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import time

# Execute the taste-score file directly
taste_score_path = Path("/home/terry/germline/effectors/taste-score")
taste_score_code = taste_score_path.read_text()
namespace = {}
exec(taste_score_code, namespace)

# Extract module
taste_score = type('taste_score_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(taste_score, key, value)


def test_parse_manifest():
    """Test parse_manifest extracts paths correctly."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Copia session
- Some introduction
- Wrote ~/germline/effectors/new-script.py — adds new effector
- Generated ~/tmp/output.pdf → saved to disk
- Completed ✓ ~/docs/report.md — final analysis
- Another line without path
- Checked out branch main
""")
        temp_path = Path(f.name)

    try:
        items = taste_score.parse_manifest(temp_path)
        assert len(items) == 3
        # First item
        assert items[0]['raw'] == '~/germline/effectors/new-script.py'
        assert items[0]['desc'] == 'adds new effector'
        assert str(items[0]['path']) == str(Path.home() / "germline" / "effectors" / "new-script.py")
        # Second item
        assert items[1]['raw'] == '~/tmp/output.pdf'
        # Third item
        assert items[2]['raw'] == '~/docs/report.md'
        assert items[2]['desc'] == 'final analysis'
    finally:
        temp_path.unlink()


def test_parse_manifest_empty():
    """Test parse_manifest on empty/no paths."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# No paths here
- Just a bullet
- Another bullet without path
""")
        temp_path = Path(f.name)

    try:
        items = taste_score.parse_manifest(temp_path)
        assert len(items) == 0
    finally:
        temp_path.unlink()


def test_score_items_missing():
    """Test scoring correctly handles missing files."""
    items = [
        {"path": Path("/nonexistent/path/file.txt"), "raw": "~/nonexistent/path/file.txt", "desc": "missing"},
    ]
    scored = taste_score.score_items(items, time.time())
    assert scored[0]['status'] == 'missing'
    assert scored[0]['consumed'] is False


def test_score_items_consumed():
    """Test scoring correctly identifies consumed files."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)

    try:
        # Create file earlier than manifest mtime
        old_time = time.time() - 3600
        os.utime(temp_path, (old_time, old_time))

        items = [{"path": temp_path, "raw": "test.txt", "desc": "test"}]
        # Manifest is newer, so not consumed
        scored = taste_score.score_items(items, time.time())
        assert scored[0]['consumed'] is False
        assert scored[0]['status'] == 'ignored'

        # Now touch the file to update mtime/atime to after manifest
        new_time = time.time() + 10
        os.utime(temp_path, (new_time, new_time))

        scored = taste_score.score_items(items, time.time() - 10)
        assert scored[0]['consumed'] is True
        assert scored[0]['status'] == 'read'
        assert 'hours_since' in scored[0]
    finally:
        temp_path.unlink()


@patch('sys.argv')
@patch('builtins.print')
def test_main_no_manifest(mock_print, mock_argv):
    """Test main exits with 1 when no manifests found in test scenario."""
    mock_argv.__len__.return_value = 1
    with patch.object(taste_score, 'Path') as mock_path:
        mock_tmp = MagicMock()
        mock_tmp.glob.return_value = []
        mock_home = MagicMock()
        mock_home.__truediv__.return_value = mock_tmp
        mock_path.home.return_value = mock_home

        with pytest.raises(SystemExit) as excinfo:
            taste_score.main()
        assert excinfo.value.code == 1
