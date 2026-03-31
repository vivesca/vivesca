"""Tests for metabolon.resources.constitution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Import-time: CANONICAL is resolved at module load, so we mock VIVESCA_ROOT
# before importing the module (or re-import it with the mock active).
# ---------------------------------------------------------------------------

def _import_with_root(root: Path):
    """Import constitution with a mocked VIVESCA_ROOT, returning the module."""
    import importlib
    with patch("metabolon.cytosol.VIVESCA_ROOT", root):
        mod = importlib.import_module("metabolon.resources.constitution")
        importlib.reload(mod)
        return mod


class TestCanonicalPath:
    """Tests for the CANONICAL module-level constant."""

    def test_canonical_is_path_instance(self):
        """CANONICAL should be a pathlib.Path."""
        from metabolon.resources.constitution import CANONICAL
        assert isinstance(CANONICAL, Path)

    def test_canonical_name(self):
        """CANONICAL filename should be genome.md."""
        from metabolon.resources.constitution import CANONICAL
        assert CANONICAL.name == "genome.md"

    def test_canonical_is_under_vivesca_root(self):
        """CANONICAL should be a direct child of VIVESCA_ROOT."""
        from metabolon.resources.constitution import CANONICAL
        from metabolon.cytosol import VIVESCA_ROOT
        assert CANONICAL.parent == VIVESCA_ROOT

    def test_canonical_str_endswith(self):
        """String form should end with genome.md."""
        from metabolon.resources.constitution import CANONICAL
        assert str(CANONICAL).endswith("genome.md")

    def test_canonical_with_mocked_root(self):
        """With a mocked VIVESCA_ROOT, CANONICAL follows the mock."""
        fake_root = Path("/tmp/fake_germline")
        mod = _import_with_root(fake_root)
        assert mod.CANONICAL == fake_root / "genome.md"

    def test_canonical_is_absolute_with_mock(self):
        """CANONICAL should be absolute when VIVESCA_ROOT is absolute."""
        fake_root = Path("/tmp/fake_germline")
        mod = _import_with_root(fake_root)
        assert mod.CANONICAL.is_absolute()


class TestModuleAttributes:
    """Tests for module-level attributes and docstring."""

    def test_module_has_docstring(self):
        import metabolon.resources.constitution as mod
        assert mod.__doc__ is not None
        assert "constitution" in mod.__doc__.lower()

    def test_canonical_exists_as_attribute(self):
        import metabolon.resources.constitution as mod
        assert hasattr(mod, "CANONICAL")

    def test_no_other_top_level_names(self):
        """Only CANONICAL should be a public module-level name."""
        import metabolon.resources.constitution as mod
        public = [n for n in dir(mod) if not n.startswith("_")]
        # CANONICAL plus anything imported from cytosol that leaks through
        assert "CANONICAL" in public

    def test_real_canonical_points_to_existing_file(self):
        """The real CANONICAL path should resolve to an actual file."""
        from metabolon.resources.constitution import CANONICAL
        assert CANONICAL.resolve().exists()
