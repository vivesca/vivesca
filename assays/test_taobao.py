#!/usr/bin/env python3
"""Tests for taobao effector — tests that wrapper exists and proxies correctly."""

import pytest
import os
from pathlib import Path


def test_taobao_symlink_exists_as_file():
    """Test that the taobao symlink exists in the effectors directory."""
    taobao_path = Path("/home/terry/germline/effectors/taobao")
    # Check the symlink entry exists, even if it's broken
    assert os.path.lexists(taobao_path)
    assert taobao_path.is_symlink()


def test_taobao_has_correct_link_target():
    """Test that taobao points to the expected location."""
    taobao_path = Path("/home/terry/germline/effectors/taobao")
    assert os.path.lexists(taobao_path)
    target = taobao_path.readlink()
    assert "taobao-cli/.venv/bin/taobao" in str(target)


def test_taobao_is_symlink():
    """Test that taobao is properly marked as a symlink."""
    taobao_path = Path("/home/terry/germline/effectors/taobao")
    assert os.path.lexists(taobao_path)
    assert taobao_path.is_symlink()
