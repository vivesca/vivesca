from __future__ import annotations
"""Tests for metabolon/enzymes/expression.py — career forge pre-flight checks."""


import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fn():
    """Return the raw function behind the @tool decorator."""
    from metabolon.enzymes import expression as mod

    return mod.expression


# ---------------------------------------------------------------------------
# _count_sparks unit tests
# ---------------------------------------------------------------------------

class TestCountSparks:
    """Tests for _count_sparks helper."""

    def test_missing_file_returns_zero(self, tmp_path):
        from metabolon.enzymes.expression import _count_sparks

        assert _count_sparks(tmp_path / "nope.md") == 0

    def test_empty_file_returns_zero(self, tmp_path):
        from metabolon.enzymes.expression import _count_sparks

        p = tmp_path / "sparks.md"
        p.write_text("", encoding="utf-8")
        assert _count_sparks(p) == 0

    def test_only_headers_returns_zero(self, tmp_path):
        from metabolon.enzymes.expression import _count_sparks

        p = tmp_path / "sparks.md"
        p.write_text("# Header\n## Another\n   # Indented\n", encoding="utf-8")
        assert _count_sparks(p) == 0

    def test_counts_content_lines(self, tmp_path):
        from metabolon.enzymes.expression import _count_sparks

        p = tmp_path / "sparks.md"
        p.write_text("# Header\nspark one\nspark two\n\nspark three\n", encoding="utf-8")
        assert _count_sparks(p) == 3

    def test_blank_lines_ignored(self, tmp_path):
        from metabolon.enzymes.expression import _count_sparks

        p = tmp_path / "sparks.md"
        p.write_text("\n\n\nonly one\n\n", encoding="utf-8")
        assert _count_sparks(p) == 1


# ---------------------------------------------------------------------------
# _file_age_days unit tests
# ---------------------------------------------------------------------------

class TestFileAgeDays:
    """Tests for _file_age_days helper."""

    def test_missing_file_returns_none(self, tmp_path):
        from metabolon.enzymes.expression import _file_age_days

        assert _file_age_days(tmp_path / "nope.md") is None

    def test_recent_file_near_zero(self, tmp_path):
        from metabolon.enzymes.expression import _file_age_days

        p = tmp_path / "fresh.md"
        p.write_text("x", encoding="utf-8")
        age = _file_age_days(p)
        assert age is not None
        assert age < 0.01  # just created

    def test_old_file_positive_age(self, tmp_path):
        from metabolon.enzymes.expression import _file_age_days

        p = tmp_path / "old.md"
        p.write_text("x", encoding="utf-8")
        # Backdate mtime by 10 days
        old_ts = (datetime.datetime.now() - datetime.timedelta(days=10)).timestamp()
        import os
        os.utime(p, (old_ts, old_ts))
        age = _file_age_days(p)
        assert age is not None
        assert 9.5 < age < 10.5


# ---------------------------------------------------------------------------
# expression("preflight") tests
# ---------------------------------------------------------------------------

class TestPreflight:
    """Tests for the preflight action."""

    @pytest.fixture()
    def _setup_paths(self, tmp_path):
        """Create fake directory structure and patch module-level path constants."""
        sparks = tmp_path / "sparks.md"
        thalamus = tmp_path / "Thalamus.md"
        cargo = tmp_path / "cargo.jsonl"
        north_star = tmp_path / "North Star.md"
        consulting = tmp_path / "Consulting"
        consulting.mkdir()

        # Default content: sparks with items
        sparks.write_text("# Sparks\nspark A\nspark B\nspark C\n", encoding="utf-8")
        thalamus.write_text("thalamus content", encoding="utf-8")
        cargo.write_text("{}", encoding="utf-8")
        north_star.write_text("north star content", encoding="utf-8")

        return {
            "_SPARKS": sparks,
            "_THALAMUS": thalamus,
            "_NEWS_LOG": cargo,
            "_NORTH_STAR": north_star,
            "_CONSULTING": consulting,
        }

    def _patch_paths(self, paths):
        """Return a dict suitable for patch.multiple on the expression module."""
        import metabolon.enzymes.expression as mod
        return {
            f"{mod.__name__}._SPARKS": paths["_SPARKS"],
            f"{mod.__name__}._THALAMUS": paths["_THALAMUS"],
            f"{mod.__name__}._NEWS_LOG": paths["_NEWS_LOG"],
            f"{mod.__name__}._NORTH_STAR": paths["_NORTH_STAR"],
            f"{mod.__name__}._CONSULTING": paths["_CONSULTING"],
        }

    def test_preflight_all_present_ready(self, _setup_paths):
        import metabolon.enzymes.expression as mod

        paths = _setup_paths
        with (
            patch.object(mod, "_SPARKS", paths["_SPARKS"]),
            patch.object(mod, "_THALAMUS", paths["_THALAMUS"]),
            patch.object(mod, "_NEWS_LOG", paths["_NEWS_LOG"]),
            patch.object(mod, "_NORTH_STAR", paths["_NORTH_STAR"]),
        ):
            result = _fn()("preflight")
            assert isinstance(result, mod.ForgePreflightResult)
            assert result.ready is True
            assert result.spark_count == 3
            assert result.missing_files == []
            assert "READY" in result.summary

    def test_preflight_missing_files_not_ready(self, _setup_paths):
        import metabolon.enzymes.expression as mod

        paths = _setup_paths
        # Delete two required files
        paths["_THALAMUS"].unlink()
        paths["_NORTH_STAR"].unlink()

        with (
            patch.object(mod, "_SPARKS", paths["_SPARKS"]),
            patch.object(mod, "_THALAMUS", paths["_THALAMUS"]),
            patch.object(mod, "_NEWS_LOG", paths["_NEWS_LOG"]),
            patch.object(mod, "_NORTH_STAR", paths["_NORTH_STAR"]),
        ):
            result = _fn()("preflight")
            assert result.ready is False
            assert "Thalamus.md" in result.missing_files
            assert "North Star.md" in result.missing_files
            assert "NOT READY" in result.summary

    def test_preflight_zero_sparks_not_ready(self, _setup_paths):
        import metabolon.enzymes.expression as mod

        paths = _setup_paths
        # Empty sparks (only header)
        paths["_SPARKS"].write_text("# Sparks\n", encoding="utf-8")

        with (
            patch.object(mod, "_SPARKS", paths["_SPARKS"]),
            patch.object(mod, "_THALAMUS", paths["_THALAMUS"]),
            patch.object(mod, "_NEWS_LOG", paths["_NEWS_LOG"]),
            patch.object(mod, "_NORTH_STAR", paths["_NORTH_STAR"]),
        ):
            result = _fn()("preflight")
            assert result.ready is False
            assert result.spark_count == 0
            # Should warn about empty sparks
            assert any("empty" in w.lower() for w in result.warnings)

    def test_preflight_low_sparks_warning(self, _setup_paths):
        import metabolon.enzymes.expression as mod

        paths = _setup_paths
        # Only 2 sparks (below threshold of 3)
        paths["_SPARKS"].write_text("# S\nspark A\nspark B\n", encoding="utf-8")

        with (
            patch.object(mod, "_SPARKS", paths["_SPARKS"]),
            patch.object(mod, "_THALAMUS", paths["_THALAMUS"]),
            patch.object(mod, "_NEWS_LOG", paths["_NEWS_LOG"]),
            patch.object(mod, "_NORTH_STAR", paths["_NORTH_STAR"]),
        ):
            result = _fn()("preflight")
            assert result.ready is True  # still has sparks
            assert result.spark_count == 2
            assert any("Low spark count" in w for w in result.warnings)

    def test_preflight_stale_thalamus_warning(self, _setup_paths):
        import os
        import metabolon.enzymes.expression as mod

        paths = _setup_paths
        # Make thalamus 10 days old
        old_ts = (datetime.datetime.now() - datetime.timedelta(days=10)).timestamp()
        os.utime(paths["_THALAMUS"], (old_ts, old_ts))

        with (
            patch.object(mod, "_SPARKS", paths["_SPARKS"]),
            patch.object(mod, "_THALAMUS", paths["_THALAMUS"]),
            patch.object(mod, "_NEWS_LOG", paths["_NEWS_LOG"]),
            patch.object(mod, "_NORTH_STAR", paths["_NORTH_STAR"]),
        ):
            result = _fn()("preflight")
            assert result.ready is True
            assert any("stale" in w.lower() for w in result.warnings)

    def test_preflight_missing_sparks_file(self, _setup_paths):
        import metabolon.enzymes.expression as mod

        paths = _setup_paths
        paths["_SPARKS"].unlink()

        with (
            patch.object(mod, "_SPARKS", paths["_SPARKS"]),
            patch.object(mod, "_THALAMUS", paths["_THALAMUS"]),
            patch.object(mod, "_NEWS_LOG", paths["_NEWS_LOG"]),
            patch.object(mod, "_NORTH_STAR", paths["_NORTH_STAR"]),
        ):
            result = _fn()("preflight")
            assert result.ready is False
            assert "_sparks.md" in result.missing_files
            assert result.spark_count == 0


# ---------------------------------------------------------------------------
# expression("library") tests
# ---------------------------------------------------------------------------

class TestLibrary:
    """Tests for the library action."""

    def test_library_empty_dirs(self, tmp_path):
        import metabolon.enzymes.expression as mod

        consulting = tmp_path / "Consulting"
        consulting.mkdir()

        lib_dirs = {
            "Policies": consulting / "Policies",
            "Architectures": consulting / "Architectures",
            "Use Cases": consulting / "Use Cases",
            "Experiments": consulting / "Experiments",
            "Weekly": consulting / "_weekly",
        }

        with patch.object(mod, "_LIBRARY_DIRS", lib_dirs):
            result = _fn()("library")
            assert isinstance(result, mod.ForgeLibraryResult)
            assert all(v == 0 for v in result.totals.values())
            assert all(v == 0 for v in result.recent_7d.values())
            assert "0 assets" in result.summary

    def test_library_with_files(self, tmp_path):
        import os
        import metabolon.enzymes.expression as mod

        consulting = tmp_path / "Consulting"
        consulting.mkdir()
        policies = consulting / "Policies"
        policies.mkdir()

        # Create 3 markdown files in Policies
        for i in range(3):
            (policies / f"pol{i}.md").write_text(f"policy {i}", encoding="utf-8")

        # Create 1 old file (>7 days)
        old_file = policies / "old_pol.md"
        old_file.write_text("old policy", encoding="utf-8")
        old_ts = (datetime.datetime.now() - datetime.timedelta(days=10)).timestamp()
        os.utime(old_file, (old_ts, old_ts))

        lib_dirs = {
            "Policies": policies,
            "Architectures": consulting / "Architectures",  # doesn't exist
            "Use Cases": consulting / "Use Cases",          # doesn't exist
            "Experiments": consulting / "Experiments",       # doesn't exist
            "Weekly": consulting / "_weekly",                # doesn't exist
        }

        with patch.object(mod, "_LIBRARY_DIRS", lib_dirs):
            result = _fn()("library")
            assert isinstance(result, mod.ForgeLibraryResult)
            assert result.totals["Policies"] == 4  # 3 recent + 1 old
            assert result.recent_7d["Policies"] == 3  # only recent ones
            assert result.totals["Architectures"] == 0
            assert "4 assets" in result.summary

    def test_library_missing_dirs_counted_zero(self, tmp_path):
        import metabolon.enzymes.expression as mod

        consulting = tmp_path / "Consulting"
        consulting.mkdir()

        lib_dirs = {
            "Policies": consulting / "Policies",  # doesn't exist on disk
        }

        with patch.object(mod, "_LIBRARY_DIRS", lib_dirs):
            result = _fn()("library")
            assert result.totals["Policies"] == 0
            assert result.recent_7d["Policies"] == 0

    def test_library_ignores_non_md_files(self, tmp_path):
        import metabolon.enzymes.expression as mod

        consulting = tmp_path / "Consulting"
        consulting.mkdir()
        policies = consulting / "Policies"
        policies.mkdir()

        (policies / "doc.md").write_text("md file", encoding="utf-8")
        (policies / "data.json").write_text("{}", encoding="utf-8")
        (policies / "image.png").write_bytes(b"\x89PNG")

        lib_dirs = {"Policies": policies}

        with patch.object(mod, "_LIBRARY_DIRS", lib_dirs):
            result = _fn()("library")
            assert result.totals["Policies"] == 1  # only the .md file


# ---------------------------------------------------------------------------
# expression unknown action
# ---------------------------------------------------------------------------

class TestUnknownAction:
    """Tests for invalid action dispatch."""

    def test_unknown_action_returns_error_string(self):
        result = _fn()("bogus")
        assert isinstance(result, str)
        assert "Unknown action" in result
        assert "bogus" in result

    def test_empty_action_returns_error(self):
        result = _fn()("")
        assert isinstance(result, str)
        assert "Unknown action" in result
