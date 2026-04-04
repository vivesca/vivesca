"""Comprehensive tests for metabolon.metabolism.variants.Genome.

Covers edge cases, error paths, cap enforcement details, and mocks
external filesystem calls where appropriate.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.metabolism.variants import DEFAULT_ROOT, Genome

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_store(tmp_path: Path, allele_cap: int = 5) -> Genome:
    return Genome(germ_line=tmp_path, allele_cap=allele_cap)


def _seed_and_variants(store: Genome, tool: str, count: int) -> list[int]:
    """Seed a tool and create *count* additional variants. Return variant ids."""
    store.seed_tool(tool, "v0 content")
    ids = []
    for i in range(1, count):
        vid = store.express_variant(tool, f"v{i} content")
        ids.append(vid)
    return ids


# ---------------------------------------------------------------------------
# DEFAULT_ROOT sanity
# ---------------------------------------------------------------------------


class TestDefaultRoot:
    def test_default_root_is_under_home(self):
        assert Path.home() / ".local" / "share" / "vivesca" / "variants" == DEFAULT_ROOT

    def test_default_root_instantiates(self):
        g = Genome()
        assert g.germ_line == DEFAULT_ROOT
        assert g.allele_cap == 5


# ---------------------------------------------------------------------------
# _read_meta / _write_meta edge cases
# ---------------------------------------------------------------------------


class TestMetaIO:
    def test_read_meta_missing_file(self, tmp_path):
        store = _make_store(tmp_path)
        meta = store._read_meta("nonexistent")
        assert meta == {"active": 0, "next_id": 1}

    def test_write_meta_round_trip(self, tmp_path):
        store = _make_store(tmp_path)
        store.seed_tool("t", "desc")
        meta = {"active": 3, "next_id": 7}
        store._write_meta("t", meta)
        got = store._read_meta("t")
        assert got == meta


# ---------------------------------------------------------------------------
# seed_tool
# ---------------------------------------------------------------------------


class TestSeedTool:
    def test_creates_directory_and_v0(self, tmp_path):
        store = _make_store(tmp_path)
        store.seed_tool("my_tool", "hello world")
        d = tmp_path / "my_tool"
        assert d.is_dir()
        assert (d / "v0.md").read_text() == "hello world"

    def test_metadata_initialized(self, tmp_path):
        store = _make_store(tmp_path)
        store.seed_tool("t", "desc")
        meta = json.loads((tmp_path / "t" / "metadata.json").read_text())
        assert meta == {"active": 0, "next_id": 1}

    def test_idempotent_second_seed_ignored(self, tmp_path):
        store = _make_store(tmp_path)
        store.seed_tool("t", "first")
        store.seed_tool("t", "second")
        assert (tmp_path / "t" / "v0.md").read_text() == "first"

    def test_nested_tool_name_creates_no_subdirs(self, tmp_path):
        """Tool name with / should still create a flat directory (path component)."""
        store = _make_store(tmp_path)
        store.seed_tool("foo/bar", "desc")
        # Path / concatenation makes this foo/bar/ directory
        assert (tmp_path / "foo/bar" / "v0.md").exists()


# ---------------------------------------------------------------------------
# active_allele / founding_allele
# ---------------------------------------------------------------------------


class TestActiveAllele:
    def test_active_after_seed_is_v0(self, tmp_path):
        store = _make_store(tmp_path)
        store.seed_tool("t", "orig")
        assert store.active_allele("t") == "orig"

    def test_active_after_promote(self, tmp_path):
        store = _make_store(tmp_path)
        store.seed_tool("t", "orig")
        store.express_variant("t", "new")
        store.promote("t", 1)
        assert store.active_allele("t") == "new"

    def test_founding_unchanged_after_promote(self, tmp_path):
        store = _make_store(tmp_path)
        store.seed_tool("t", "founding")
        store.express_variant("t", "v1")
        store.promote("t", 1)
        assert store.founding_allele("t") == "founding"


# ---------------------------------------------------------------------------
# express_variant
# ---------------------------------------------------------------------------


class TestExpressVariant:
    def test_returns_sequential_ids(self, tmp_path):
        store = _make_store(tmp_path)
        store.seed_tool("t", "v0")
        assert store.express_variant("t", "v1") == 1
        assert store.express_variant("t", "v2") == 2
        assert store.express_variant("t", "v3") == 3

    def test_variant_files_written(self, tmp_path):
        store = _make_store(tmp_path)
        store.seed_tool("t", "v0")
        store.express_variant("t", "custom content")
        assert (tmp_path / "t" / "v1.md").read_text() == "custom content"

    def test_next_id_increments(self, tmp_path):
        store = _make_store(tmp_path)
        store.seed_tool("t", "v0")
        store.express_variant("t", "v1")
        store.express_variant("t", "v2")
        meta = store._read_meta("t")
        assert meta["next_id"] == 3


# ---------------------------------------------------------------------------
# promote errors
# ---------------------------------------------------------------------------


class TestPromoteErrors:
    def test_promote_nonexistent_raises(self, tmp_path):
        store = _make_store(tmp_path)
        store.seed_tool("t", "v0")
        with pytest.raises(ValueError, match="does not exist"):
            store.promote("t", 99)

    def test_promote_nonexistent_tool_raises_file_not_found(self, tmp_path):
        store = _make_store(tmp_path)
        with pytest.raises(FileNotFoundError):
            store.active_allele("no_such_tool")


# ---------------------------------------------------------------------------
# allele_variants
# ---------------------------------------------------------------------------


class TestAlleleVariants:
    def test_returns_sorted_ids(self, tmp_path):
        store = _make_store(tmp_path)
        store.seed_tool("t", "v0")
        store.express_variant("t", "v1")
        store.express_variant("t", "v2")
        assert store.allele_variants("t") == [0, 1, 2]

    def test_ignores_non_variant_files(self, tmp_path):
        store = _make_store(tmp_path)
        store.seed_tool("t", "v0")
        # Drop a non-matching file in the directory
        (tmp_path / "t" / "notes.txt").write_text("irrelevant")
        (tmp_path / "t" / "v_ambiguous.md").write_text("bad name")
        assert store.allele_variants("t") == [0]

    def test_empty_for_unseeded_tool(self, tmp_path):
        store = _make_store(tmp_path)
        # No directory exists yet
        assert store.allele_variants("nope") == []


# ---------------------------------------------------------------------------
# expressed_tools
# ---------------------------------------------------------------------------


class TestExpressedTools:
    def test_returns_tool_names(self, tmp_path):
        store = _make_store(tmp_path)
        store.seed_tool("alpha", "a")
        store.seed_tool("beta", "b")
        assert set(store.expressed_tools()) == {"alpha", "beta"}

    def test_empty_when_no_root(self, tmp_path):
        store = _make_store(tmp_path / "nonexistent")
        assert store.expressed_tools() == []

    def test_ignores_files_in_root(self, tmp_path):
        store = _make_store(tmp_path)
        (tmp_path / "orphan.md").write_text("not a tool")
        assert store.expressed_tools() == []


# ---------------------------------------------------------------------------
# _enforce_cap (detailed eviction logic)
# ---------------------------------------------------------------------------


class TestEnforceCap:
    def test_cap_2_keeps_founder_and_active(self, tmp_path):
        store = _make_store(tmp_path, allele_cap=2)
        store.seed_tool("t", "v0")
        store.express_variant("t", "v1")
        store.express_variant("t", "v2")  # v1 should be evicted
        variants = store.allele_variants("t")
        assert 0 in variants  # founding always kept
        assert len(variants) <= 2

    def test_active_not_evicted(self, tmp_path):
        """When active is v1, v0 is founding, and cap=3 with 4 variants,
        the oldest non-founding non-active (v2) should be evicted."""
        store = _make_store(tmp_path, allele_cap=3)
        store.seed_tool("t", "v0")
        store.express_variant("t", "v1")
        store.promote("t", 1)  # v1 is active
        store.express_variant("t", "v2")
        store.express_variant("t", "v3")  # now 4 variants, cap=3
        variants = store.allele_variants("t")
        assert 1 in variants  # active preserved
        assert 0 in variants  # founding preserved
        assert len(variants) <= 3

    def test_cap_not_triggered_when_at_limit(self, tmp_path):
        store = _make_store(tmp_path, allele_cap=3)
        store.seed_tool("t", "v0")
        store.express_variant("t", "v1")
        store.express_variant("t", "v2")
        # Exactly 3 variants, no eviction needed
        assert store.allele_variants("t") == [0, 1, 2]

    def test_eviction_prefers_oldest_recessive(self, tmp_path):
        """With cap=3, v0=founder, v1=active, v2+v3+v4 = recessive.
        Expressing v4 should evict v2 (oldest recessive)."""
        store = _make_store(tmp_path, allele_cap=4)
        store.seed_tool("t", "v0")
        store.express_variant("t", "v1")
        store.promote("t", 1)
        store.express_variant("t", "v2")
        store.express_variant("t", "v3")
        # Now at cap=4. Add one more.
        store.express_variant("t", "v4")
        variants = store.allele_variants("t")
        # v2 should have been evicted (oldest non-founding non-active)
        assert 2 not in variants
        assert 0 in variants  # founder
        assert 1 in variants  # active
        assert len(variants) <= 4


# ---------------------------------------------------------------------------
# Mocked filesystem: verify no real disk access when patched
# ---------------------------------------------------------------------------


class TestMockedFilesystem:
    def test_seed_tool_creates_locus_dir(self, tmp_path):
        """Verify seed_tool creates the locus directory."""
        store = _make_store(tmp_path)
        locus = tmp_path / "mytool"
        assert not locus.exists()
        store.seed_tool("mytool", "desc")
        assert locus.is_dir()
        assert (locus / "v0.md").read_text() == "desc"

    def test_read_meta_with_mocked_path(self, tmp_path):
        """When metadata file doesn't exist, default dict is returned."""
        store = _make_store(tmp_path)
        with patch.object(Path, "exists", return_value=False):
            meta = store._read_meta("anything")
            assert meta == {"active": 0, "next_id": 1}

    def test_write_meta_with_mocked_path(self, tmp_path):
        """Verify write_text is called with valid JSON."""
        store = _make_store(tmp_path)
        store.seed_tool("t", "desc")  # need directory to exist
        with patch.object(Path, "write_text") as mock_write:
            store._write_meta("t", {"active": 5, "next_id": 10})
            mock_write.assert_called_once_with(json.dumps({"active": 5, "next_id": 10}))


# ---------------------------------------------------------------------------
# Integration: full lifecycle
# ---------------------------------------------------------------------------


class TestLifecycle:
    def test_full_lifecycle(self, tmp_path):
        store = _make_store(tmp_path, allele_cap=4)
        # Seed
        store.seed_tool("tool_a", "original description")
        assert store.active_allele("tool_a") == "original description"
        assert store.founding_allele("tool_a") == "original description"

        # Express variant
        v1 = store.express_variant("tool_a", "improved description")
        assert v1 == 1
        assert store.allele_variants("tool_a") == [0, 1]

        # Promote
        store.promote("tool_a", 1)
        assert store.active_allele("tool_a") == "improved description"
        assert store.founding_allele("tool_a") == "original description"

        # Express more variants up to cap
        store.express_variant("tool_a", "v2")
        store.express_variant("tool_a", "v3")
        store.express_variant("tool_a", "v4")
        # Cap enforced: at most 4 variants
        assert len(store.allele_variants("tool_a")) <= 4

        # Expressed tools
        assert "tool_a" in store.expressed_tools()

    def test_multiple_tools_independent(self, tmp_path):
        store = _make_store(tmp_path)
        store.seed_tool("x", "x desc")
        store.seed_tool("y", "y desc")
        store.express_variant("x", "x v1")
        assert store.allele_variants("x") == [0, 1]
        assert store.allele_variants("y") == [0]
        assert store.active_allele("y") == "y desc"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_promote_idempotent(self, tmp_path):
        """Promoting the same allele twice does not change state."""
        store = _make_store(tmp_path)
        store.seed_tool("t", "v0")
        store.express_variant("t", "v1")
        store.promote("t", 1)
        assert store.active_allele("t") == "v1"
        store.promote("t", 1)
        assert store.active_allele("t") == "v1"

    def test_promote_to_v0_resets_active(self, tmp_path):
        """Can promote back to the founding variant."""
        store = _make_store(tmp_path)
        store.seed_tool("t", "founding")
        store.express_variant("t", "v1")
        store.promote("t", 1)
        assert store.active_allele("t") == "v1"
        store.promote("t", 0)
        assert store.active_allele("t") == "founding"

    def test_express_variant_unseeded_tool_creates_no_dir(self, tmp_path):
        """express_variant on an unseeded tool fails — no locus dir exists."""
        store = _make_store(tmp_path)
        with pytest.raises(FileNotFoundError):
            store.express_variant("ghost", "content")

    def test_cap_one_keeps_founder_and_active(self, tmp_path):
        """With cap=1, after seeding only v0 exists (at limit)."""
        store = _make_store(tmp_path, allele_cap=1)
        store.seed_tool("t", "v0")
        assert store.allele_variants("t") == [0]

    def test_cap_one_evicts_recessive(self, tmp_path):
        """With cap=2, seed v0, express v1, promote v1, express v2.
        v0 is founding (kept), v1 is active (kept), v2 evicts nothing.
        But if we express v3, the oldest recessive should be evicted."""
        store = _make_store(tmp_path, allele_cap=3)
        store.seed_tool("t", "v0")
        store.express_variant("t", "v1")
        store.promote("t", 1)
        store.express_variant("t", "v2")
        store.express_variant("t", "v3")
        variants = store.allele_variants("t")
        # cap=3: v0 (founding), v1 (active), and newest should remain
        assert 0 in variants
        assert 1 in variants
        assert 3 in variants
        assert len(variants) <= 3

    def test_allele_variants_ignores_v_prefix_non_numeric(self, tmp_path):
        """Files like vX.md where X is not a number are skipped."""
        store = _make_store(tmp_path)
        store.seed_tool("t", "v0")
        (tmp_path / "t" / "vNaN.md").write_text("bad")
        assert store.allele_variants("t") == [0]

    def test_seed_tool_with_empty_description(self, tmp_path):
        """Seeding with empty string is valid — creates empty v0.md."""
        store = _make_store(tmp_path)
        store.seed_tool("t", "")
        assert store.active_allele("t") == ""
        assert store.founding_allele("t") == ""
