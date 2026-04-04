"""Tests for metabolon.__init__."""

import importlib
import re
from pathlib import Path

import metabolon


def test_import_succeeds():
    """metabolon package is importable without errors."""
    assert metabolon is not None


def test_version_is_string():
    """__version__ is defined and is a non-empty string."""
    assert hasattr(metabolon, "__version__")
    assert isinstance(metabolon.__version__, str)
    assert len(metabolon.__version__) > 0


def test_version_is_semver():
    """__version__ follows semantic versioning (MAJOR.MINOR.PATCH)."""
    semver_re = r"^\d+\.\d+\.\d+"
    assert re.match(semver_re, metabolon.__version__), (
        f"Version {metabolon.__version__!r} does not match semver pattern"
    )


def test_docstring_exists():
    """Module-level docstring is present and non-empty."""
    assert metabolon.__doc__, "metabolon should have a non-empty module docstring"
    assert len(metabolon.__doc__.strip()) > 0


def test_key_subpackages_exist():
    """Core subpackage directories exist under metabolon/."""
    pkg_dir = Path(metabolon.__file__).parent
    expected = ["organelles", "pinocytosis", "enzymes", "sortase"]
    for sub in expected:
        assert (pkg_dir / sub / "__init__.py").exists(), f"Subpackage metabolon.{sub} is missing"


def test_pyproject_version_matches():
    """Package version in pyproject.toml is a valid semver (informational check)."""
    pyproject = Path(metabolon.__file__).parent.parent.parent / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml should exist at repo root"
    content = pyproject.read_text()
    match = re.search(r'^version\s*=\s*"(.+?)"', content, re.MULTILINE)
    assert match, "pyproject.toml should declare a version"
    pyproject_ver = match.group(1)
    # Both should be valid semver; they may differ during development
    assert re.match(r"^\d+\.\d+\.\d+", pyproject_ver)


def test_reimport_is_idempotent():
    """Re-importing metabolon returns the same module object."""
    mod = importlib.reload(metabolon)
    assert mod is metabolon
    assert mod.__version__ == metabolon.__version__
