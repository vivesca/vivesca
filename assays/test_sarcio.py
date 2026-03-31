#!/usr/bin/env python3
"""Tests for sarcio effector — symlink wrapper test."""

import pytest
import os
from pathlib import Path


def test_sarcio_symlink_entry_exists():
    """Test that sarcio symlink entry exists in the effectors directory."""
    sarcio_path = Path("/home/terry/germline/effectors/sarcio")
    assert os.path.lexists(sarcio_path)
    assert sarcio_path.is_symlink()


def test_sarcio_has_correct_target():
    """Test that sarcio points to the expected Python installation."""
    sarcio_path = Path("/home/terry/germline/effectors/sarcio")
    assert os.path.lexists(sarcio_path)
    target = sarcio_path.readlink()
    assert str(target) == "/Users/terry/.local/share/mise/installs/python/3.13.12/bin/sarcio"
