"""Tests for genome variant storage."""

from metabolon.metabolism.variants import Genome


def test_seed_tool_creates_v0(tmp_path):
    store = Genome(germ_line=tmp_path)
    store.seed_tool("fasti_list_events", "List calendar events for a date.")

    assert (tmp_path / "fasti_list_events" / "v0.md").exists()
    assert store.active_allele("fasti_list_events") == "List calendar events for a date."


def test_seed_tool_idempotent(tmp_path):
    store = Genome(germ_line=tmp_path)
    store.seed_tool("t", "original")
    store.seed_tool("t", "updated")  # should not overwrite v0
    assert store.founding_allele("t") == "original"


def test_express_variant(tmp_path):
    store = Genome(germ_line=tmp_path)
    store.seed_tool("t", "original")
    store.express_variant("t", "mutated version")

    variants = store.allele_variants("t")
    assert len(variants) == 2  # v0 + v1


def test_promote_variant(tmp_path):
    store = Genome(germ_line=tmp_path)
    store.seed_tool("t", "original")
    store.express_variant("t", "better version")
    store.promote("t", 1)  # promote v1

    assert store.active_allele("t") == "better version"


def test_founding_allele_never_changes(tmp_path):
    store = Genome(germ_line=tmp_path)
    store.seed_tool("t", "founding")
    store.express_variant("t", "v1")
    store.promote("t", 1)
    assert store.founding_allele("t") == "founding"


def test_expressed_tools(tmp_path):
    store = Genome(germ_line=tmp_path)
    store.seed_tool("a", "desc a")
    store.seed_tool("b", "desc b")
    assert set(store.expressed_tools()) == {"a", "b"}


def test_max_variants_cap(tmp_path):
    store = Genome(germ_line=tmp_path, allele_cap=3)
    store.seed_tool("t", "v0")
    store.express_variant("t", "v1")
    store.express_variant("t", "v2")
    store.express_variant("t", "v3")  # should evict lowest non-active, non-founding

    assert len(store.allele_variants("t")) <= 3
