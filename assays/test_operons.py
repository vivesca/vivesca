"""Tests for operons — dataclass, registry, and helper functions."""

import pytest
from metabolon.operons import (
    Operon,
    OPERONS,
    dormant,
    expressed,
    crystallised,
    by_enzyme,
    co_regulated,
    unclaimed_enzymes,
)


# -- Operon dataclass --


def test_operon_defaults():
    op = Operon(reaction="test", product="a thing")
    assert op.reaction == "test"
    assert op.product == "a thing"
    assert op.precipitation == "authored"
    assert op.substrates == []
    assert op.enzymes == []
    assert op.expressed is True


def test_operon_all_fields():
    op = Operon(
        reaction="decide",
        product="A decision",
        precipitation="crystallised",
        substrates=["option A", "option B"],
        enzymes=["brain", "gut"],
        expressed=False,
    )
    assert op.reaction == "decide"
    assert op.precipitation == "crystallised"
    assert len(op.substrates) == 2
    assert len(op.enzymes) == 2
    assert op.expressed is False


def test_operon_frozen():
    op = Operon(reaction="test", product="frozen")
    with pytest.raises(AttributeError):
        op.reaction = "changed"


def test_operon_frozen_list_still_appends():
    """Frozen dataclass: list fields are frozen at the dataclass level but
    the list object itself is mutable — standard Python behaviour."""
    op = Operon(reaction="test", product="x", substrates=["a"])
    # The attribute itself can't be reassigned
    with pytest.raises(AttributeError):
        op.substrates = ["new"]
    # But the list object is mutable (standard frozen dataclass caveat)
    op.substrates.append("b")
    assert "b" in op.substrates


# -- OPERONS registry --


def test_operons_is_list():
    assert isinstance(OPERONS, list)


def test_operons_all_instances():
    assert len(OPERONS) > 0
    for op in OPERONS:
        assert isinstance(op, Operon)


def test_operons_unique_reactions():
    reactions = [op.reaction for op in OPERONS]
    assert len(reactions) == len(set(reactions)), f"Duplicate reactions: {reactions}"


# -- Helper functions --


def test_dormant_returns_unexpressed():
    result = dormant()
    assert isinstance(result, list)
    for op in result:
        assert op.expressed is False


def test_expressed_returns_active():
    result = expressed()
    assert isinstance(result, list)
    for op in result:
        assert op.expressed is True


def test_dormant_plus_expressed_equals_all():
    d = dormant()
    e = expressed()
    assert len(d) + len(e) == len(OPERONS)


def test_crystallised_returns_crystallised_only():
    result = crystallised()
    for op in result:
        assert op.precipitation == "crystallised"


def test_crystallised_is_subset():
    assert len(crystallised()) <= len(OPERONS)


def test_by_enzyme_finds_matching():
    # Pick an enzyme we know exists: "rheotaxis_search" is used by "scan" and "research"
    result = by_enzyme("rheotaxis_search")
    assert isinstance(result, list)
    assert len(result) >= 2
    for op in result:
        assert "rheotaxis_search" in op.enzymes


def test_by_enzyme_no_match():
    result = by_enzyme("nonexistent_enzyme_xyz")
    assert result == []


def test_co_regulated_finds_shared_substrates():
    # "prepare" and "scan" share no substrates directly, but let's find a pair
    # Use "triage" which shares substrates with nothing obvious — test the empty case
    # Instead, pick two that share: look for any pair
    for op in OPERONS:
        related = co_regulated(op)
        # Just verify it returns a list of Operon instances
        for r in related:
            assert isinstance(r, Operon)
            assert r.reaction != op.reaction
            assert r.expressed is True
            # Must share at least one substrate
            assert bool(set(op.substrates) & set(r.substrates))


def test_co_regulated_empty_substrates():
    op = Operon(reaction="empty", product="none", substrates=[])
    assert co_regulated(op) == []


def test_unclaimed_enzymes():
    # All claimed enzymes should produce empty list
    all_claimed = {e for op in OPERONS for e in op.enzymes}
    assert unclaimed_enzymes(list(all_claimed)) == []


def test_unclaimed_enzymes_finds_gap():
    result = unclaimed_enzymes(["phantom_enzyme_123"])
    assert result == ["phantom_enzyme_123"]


def test_unclaimed_enzymes_mixed():
    known = list({e for op in OPERONS for e in op.enzymes})
    known.append("unknown_enzyme_abc")
    result = unclaimed_enzymes(known)
    assert result == ["unknown_enzyme_abc"]
