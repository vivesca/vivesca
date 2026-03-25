"""Tests for genome variant storage."""

from metabolon.metabolism.variants import Genome


def test_init_tool_creates_v0(tmp_path):
    store = Genome(germ_line=tmp_path)
    store.init_tool("fasti_list_events", "List calendar events for a date.")

    assert (tmp_path / "fasti_list_events" / "v0.md").exists()
    assert store.get_active("fasti_list_events") == "List calendar events for a date."


def test_init_tool_idempotent(tmp_path):
    store = Genome(germ_line=tmp_path)
    store.init_tool("t", "original")
    store.init_tool("t", "updated")  # should not overwrite v0
    assert store.get_founding("t") == "original"


def test_add_variant(tmp_path):
    store = Genome(germ_line=tmp_path)
    store.init_tool("t", "original")
    store.add_variant("t", "mutated version")

    variants = store.list_variants("t")
    assert len(variants) == 2  # v0 + v1


def test_promote_variant(tmp_path):
    store = Genome(germ_line=tmp_path)
    store.init_tool("t", "original")
    store.add_variant("t", "better version")
    store.promote("t", 1)  # promote v1

    assert store.get_active("t") == "better version"


def test_get_founding_never_changes(tmp_path):
    store = Genome(germ_line=tmp_path)
    store.init_tool("t", "founding")
    store.add_variant("t", "v1")
    store.promote("t", 1)
    assert store.get_founding("t") == "founding"


def test_list_tools(tmp_path):
    store = Genome(germ_line=tmp_path)
    store.init_tool("a", "desc a")
    store.init_tool("b", "desc b")
    assert set(store.list_tools()) == {"a", "b"}


def test_max_variants_cap(tmp_path):
    store = Genome(germ_line=tmp_path, allele_cap=3)
    store.init_tool("t", "v0")
    store.add_variant("t", "v1")
    store.add_variant("t", "v2")
    store.add_variant("t", "v3")  # should evict lowest non-active, non-founding

    assert len(store.list_variants("t")) <= 3
