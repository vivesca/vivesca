"""Tests for metabolon.lysin.fetch – edge cases and uncovered paths."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from metabolon.lysin.fetch import (
    BioArticle,
    _fetch_reactome,
    _fetch_uniprot,
    _fetch_wikipedia,
    _looks_like_gene,
    _strip_html,
    _strip_pubmed_refs,
    fetch_sections,
    fetch_summary,
)


# ── _strip_html edge cases ─────────────────────────────────────────────


def test_strip_html_empty_string():
    assert _strip_html("") == ""


def test_strip_html_self_closing_tag():
    assert _strip_html("line 1<br/>line 2") == "line 1line 2"


def test_strip_html_preserves_whitespace_outside_tags():
    assert _strip_html("  hello  ") == "hello"


# ── _strip_pubmed_refs edge cases ──────────────────────────────────────


def test_strip_pubmed_refs_multiple_comma_separated():
    text = "Involved in repair (PubMed:111, PubMed:222, PubMed:333)."
    result = _strip_pubmed_refs(text)
    assert "PubMed" not in result
    assert "Involved in repair" in result


# ── _looks_like_gene edge cases ────────────────────────────────────────


def test_looks_like_gene_numeric_suffix():
    assert _looks_like_gene("cdk2a") is True


def test_looks_like_gene_spaces_false():
    assert _looks_like_gene("dna repair") is False


def test_looks_like_gene_exactly_15_chars_true():
    assert _looks_like_gene("a" * 15) is True


def test_looks_like_gene_16_chars_false():
    assert _looks_like_gene("a" * 16) is False


# ── BioArticle default factories ───────────────────────────────────────


def test_bio_article_independent_defaults():
    a1 = BioArticle(title="A", definition="d", mechanism="m", url="u")
    a2 = BioArticle(title="B", definition="d", mechanism="m", url="u")
    a1.sections.append({"title": "X", "text": "Y"})
    assert a2.sections == []  # default_factory gives independent lists


# ── UniProt subunit extraction ─────────────────────────────────────────


def test_fetch_uniprot_extracts_subunit():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [{
            "primaryAccession": "P99999",
            "proteinDescription": {
                "recommendedName": {"fullName": {"value": "Subunit Protein"}}
            },
            "comments": [
                {"commentType": "FUNCTION", "texts": [{"value": "Test function."}]},
                {"commentType": "SUBUNIT", "texts": [{"value": "Forms a heterodimer."}]},
            ],
        }]
    }

    with patch("httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.get.return_value = mock_resp
        result = _fetch_uniprot("SUBP")

    assert result is not None
    assert any(s["title"] == "Subunit interactions" for s in result.sections)


# ── UniProt skips result with no sections ──────────────────────────────


def test_fetch_uniprot_skips_empty_comments():
    """A result with no FUNCTION/CTALYTIC/DOMAIN/SUBUNIT comments is skipped."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [{
            "primaryAccession": "P00000",
            "proteinDescription": {
                "recommendedName": {"fullName": {"value": "Bare Protein"}}
            },
            "comments": [{"commentType": "OTHER", "texts": [{"value": "Ignored."}]}],
        }]
    }

    with patch("httpx.Client") as MockClient:
        MockClient.return_value.__enter__.return_value.get.return_value = mock_resp
        result = _fetch_uniprot("BAREP")

    assert result is None


# ── Reactome with HTML in name ─────────────────────────────────────────


def test_fetch_reactome_strips_html_from_name():
    mock_search = MagicMock()
    mock_search.status_code = 200
    mock_search.json.return_value = {
        "results": [{"entries": [{"stId": "R-HSA-1", "name": "<b>Apoptosis</b> pathway"}]}]
    }

    mock_detail = MagicMock()
    mock_detail.status_code = 200
    mock_detail.json.return_value = {
        "summation": [{"text": "Apoptosis is programmed cell death."}]
    }

    with patch("httpx.Client") as MockClient:
        client = MockClient.return_value.__enter__.return_value
        client.get.side_effect = [mock_search, mock_detail]
        result = _fetch_reactome("Apoptosis")

    assert result is not None
    assert "<b>" not in result.title


# ── Wikipedia sections filtered by length > 50 ────────────────────────


def test_fetch_wikipedia_sections_filters_short():
    mock_summary = MagicMock()
    mock_summary.status_code = 200
    mock_summary.json.return_value = {
        "title": "Test",
        "extract": "A short test extract.",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Test"}},
    }

    mock_secs = MagicMock()
    mock_secs.status_code = 200
    mock_secs.json.return_value = {
        "remaining": {
            "sections": [
                {"line": "Short", "text": "Too short."},
                {"line": "Long enough", "text": "A" * 60},
            ]
        }
    }

    with patch("httpx.Client") as MockClient:
        client = MockClient.return_value.__enter__.return_value
        client.get.side_effect = [mock_summary, mock_secs]
        result = _fetch_wikipedia("Test")

    assert result is not None
    assert len(result.sections) == 1
    assert result.sections[0]["title"] == "Long enough"


# ── fetch_summary routes non-gene to Reactome first ────────────────────


def test_fetch_summary_non_gene_skips_uniprot():
    """Multi-word terms skip UniProt and try Reactome first."""
    mock_reactome = MagicMock()
    mock_reactome.status_code = 200
    mock_reactome.json.return_value = {
        "results": [{"entries": [{"stId": "R-HSA-42", "name": "Apoptosis pathway"}]}]
    }

    mock_detail = MagicMock()
    mock_detail.status_code = 200
    mock_detail.json.return_value = {
        "summation": [{"text": "Apoptosis is a form of programmed cell death."}]
    }

    with patch("httpx.Client") as MockClient:
        client = MockClient.return_value.__enter__.return_value
        client.get.side_effect = [mock_reactome, mock_detail]
        result = fetch_summary("apoptosis pathway")

    assert result is not None
    assert "Reactome" in result.sources
