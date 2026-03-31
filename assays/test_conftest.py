from __future__ import annotations

from pathlib import Path


def test_home_dir_fixture(home_dir):
    """home_dir returns a Path that is an existing directory."""
    assert isinstance(home_dir, Path)
    assert home_dir.is_dir()


def test_germline_dir_fixture(germline_dir):
    """germline_dir is ~/germline and exists."""
    assert isinstance(germline_dir, Path)
    assert germline_dir == Path.home() / "germline"
    assert germline_dir.is_dir()


def test_effectors_dir_fixture(effectors_dir, germline_dir):
    """effectors_dir is ~/germline/effectors and exists."""
    assert isinstance(effectors_dir, Path)
    assert effectors_dir == germline_dir / "effectors"
    assert effectors_dir.is_dir()
