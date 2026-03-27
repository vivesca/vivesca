"""Tests for the spending MCP tool."""

from metabolon.enzymes.catabolism import CatabolismResult


def test_catabolism_result_is_secretion():
    from metabolon.morphology import Secretion

    assert issubclass(CatabolismResult, Secretion)


def test_catabolism_result_fields():
    r = CatabolismResult(
        summary="Processed 1 statement",
        statements_processed=1,
        total_alerts=0,
        details=[],
    )
    assert r.summary == "Processed 1 statement"
    assert r.statements_processed == 1
