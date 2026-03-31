#!/usr/bin/env python3
"""Tests for sortase effector — tests that wrapper imports and calls main."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Execute the sortase file
sortase_code = Path("/home/terry/germline/effectors/sortase").read_text()

def test_sortase_imports_correctly():
    """Test that sortase wrapper can be parsed and imports correctly."""
    # Check code content
    assert "from metabolon.sortase.cli import main" in sortase_code
    assert "main()" in sortase_code


@patch('metabolon.sortase.cli.main')
def test_sortase_calls_main(mock_main):
    """Test that when executed, sortase calls main from metabolon."""
    namespace = {}
    exec(sortase_code, namespace)
    mock_main.assert_called_once()


def test_sortase_wrapper_exists():
    """Test sortase file exists."""
    sortase_path = Path("/home/terry/germline/effectors/sortase")
    assert sortase_path.exists()
    assert sortase_path.is_file()
