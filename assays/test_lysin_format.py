from __future__ import annotations

"""Tests for metabolon/lysin/format.py - BioArticle formatting."""

import json

from metabolon.lysin.fetch import BioArticle
from metabolon.lysin.format import format_text, format_json


# ── Test fixtures ────────────────────────────────────────────────────────


def make_article(**kwargs) -> BioArticle:
    """Create a test BioArticle with defaults."""

    defaults = {
        "title": "Test Article",
        "definition": "A test definition.",
        "mechanism": "The mechanism of action.",
        "url": "https://example.com/test",
        "sections": [],
        "sources": ["TestSource"],
    }
    defaults.update(kwargs)
    return BioArticle(**defaults)


# ── format_text tests ────────────────────────────────────────────────────


def test_format_text_basic():
    """format_text produces human-readable text output."""
    article = make_article()
    result = format_text(article)
    
    assert "LYSIN: Test Article" in result
    assert "Source: TestSource" in result
    assert "DEFINITION" in result
    assert "A test definition." in result
    assert "MECHANISM" in result
    assert "The mechanism of action." in result
    assert "URL" in result
    assert "https://example.com/test" in result


def test_format_text_multiple_sources():
    """format_text joins multiple sources with comma."""
    article = make_article(sources=["UniProt", "Reactome", "Wikipedia"])
    result = format_text(article)
    
    assert "Source: UniProt, Reactome, Wikipedia" in result


def test_format_text_no_sources():
    """format_text handles missing sources gracefully."""
    article = make_article(sources=[])
    result = format_text(article)
    
    assert "Source: unknown" in result


def test_format_text_wraps_lines():
    """format_text wraps long lines to 80 characters."""
    long_def = "This is a very long definition that should be wrapped to multiple lines because it exceeds the 80 character limit for text output formatting."
    article = make_article(definition=long_def)
    result = format_text(article)
    
    # All lines should be <= 80 chars (roughly)
    lines = result.split("\n")
    for line in lines:
        # Allow some flexibility for the header lines
        if line.startswith("═") or not line:
            continue
        assert len(line) <= 85, f"Line too long: {line}"


def test_format_text_full_includes_sections():
    """format_text with full=True includes sections."""
    article = make_article(
        sections=[
            {"title": "Function", "text": "The protein functions in DNA repair."},
            {"title": "Domain", "text": "Contains a DNA-binding domain."},
        ]
    )
    result = format_text(article, full=True)
    
    assert "SECTIONS" in result
    assert "## Function" in result
    assert "## Domain" in result
    assert "DNA repair" in result


def test_format_text_full_false_no_sections():
    """format_text with full=False excludes sections."""
    article = make_article(
        sections=[{"title": "Function", "text": "Some function."}]
    )
    result = format_text(article, full=False)
    
    assert "SECTIONS" not in result
    assert "## Function" not in result


def test_format_text_full_empty_sections():
    """format_text handles empty sections gracefully."""
    article = make_article(sections=[])
    result = format_text(article, full=True)
    
    # Should not include SECTIONS header if no sections
    assert "SECTIONS" not in result


def test_format_text_unicode():
    """format_text handles unicode characters."""
    article = make_article(
        title="β-catenin",
        definition="Protein involved in cell–cell adhesion.",
        mechanism="Interacts with α-catenin."
    )
    result = format_text(article)
    
    assert "β-catenin" in result
    assert "cell–cell" in result


# ── format_json tests ─────────────────────────────────────────────────────


def test_format_json_basic():
    """format_json produces valid JSON output."""
    article = make_article()
    result = format_json(article)
    
    # Should be valid JSON
    data = json.loads(result)
    assert data["title"] == "Test Article"
    assert data["definition"] == "A test definition."
    assert data["mechanism"] == "The mechanism of action."
    assert data["url"] == "https://example.com/test"
    assert data["sources"] == ["TestSource"]


def test_format_json_full_includes_sections():
    """format_json with full=True includes sections."""
    article = make_article(
        sections=[{"title": "Function", "text": "Does things."}]
    )
    result = format_json(article, full=True)
    
    data = json.loads(result)
    assert "sections" in data
    assert len(data["sections"]) == 1
    assert data["sections"][0]["title"] == "Function"


def test_format_json_full_false_excludes_sections():
    """format_json with full=False excludes sections."""
    article = make_article(
        sections=[{"title": "Function", "text": "Does things."}]
    )
    result = format_json(article, full=False)
    
    data = json.loads(result)
    assert "sections" not in data


def test_format_json_indentation():
    """format_json uses 2-space indentation."""
    article = make_article()
    result = format_json(article)
    
    # Check for 2-space indentation
    assert "\n  " in result  # 2 spaces for nested items


def test_format_json_unicode():
    """format_json handles unicode characters properly."""
    article = make_article(
        title="β-catenin",
        definition="Cell–cell adhesion protein."
    )
    result = format_json(article)

    # Should be valid JSON (unicode may be escaped in output but parsed correctly)
    data = json.loads(result)
    assert data["title"] == "β-catenin"
    assert data["definition"] == "Cell–cell adhesion protein."


def test_format_json_empty_sources():
    """format_json handles empty sources list."""
    article = make_article(sources=[])
    result = format_json(article)
    
    data = json.loads(result)
    assert data["sources"] == []


# ── Comparison tests ─────────────────────────────────────────────────────


def test_both_formats_same_article():
    """Both formats should represent the same article data."""
    article = make_article(
        title="TP53",
        definition="Tumor suppressor protein.",
        mechanism="DNA repair and apoptosis.",
        url="https://uniprot.org/tp53",
        sources=["UniProt"]
    )
    
    text = format_text(article)
    json_out = format_json(article)
    data = json.loads(json_out)
    
    # Both should contain the same key information
    assert "TP53" in text
    assert data["title"] == "TP53"
    assert "Tumor suppressor" in text
    assert data["definition"] == "Tumor suppressor protein."
