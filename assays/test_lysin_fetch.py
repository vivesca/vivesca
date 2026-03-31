from __future__ import annotations

"""Tests for metabolon/lysin/fetch.py - biology article fetching."""


import re
from unittest.mock import MagicMock, patch

import pytest

from metabolon.lysin.fetch import (
    BioArticle,
    _strip_html,
    _strip_pubmed_refs,
    _looks_like_gene,
    fetch_summary,
    fetch_sections,
    _fetch_uniprot,
    _fetch_reactome,
    _fetch_wikipedia,
    _search_wikipedia,
)


# ── BioArticle dataclass tests ─────────────────────────────────────────


def test_bio_article_creation():
    """BioArticle can be created with required fields."""
    article = BioArticle(
        title="TP53",
        definition="Tumor protein p53.",
        mechanism="P53 acts as a tumor suppressor.",
        url="https://example.com/tp53",
    )
    assert article.title == "TP53"
    assert article.definition == "Tumor protein p53."
    assert article.mechanism == "P53 acts as a tumor suppressor."
    assert article.url == "https://example.com/tp53"
    assert article.sections == []
    assert article.sources == []


def test_bio_article_with_sections_and_sources():
    """BioArticle can have optional sections and sources."""
    article = BioArticle(
        title="BRCA1",
        definition="Breast cancer type 1 susceptibility protein.",
        mechanism="DNA repair mechanism.",
        url="https://example.com/brca1",
        sections=[{"title": "Function", "text": "DNA repair"}],
        sources=["UniProt", "Wikipedia"],
    )
    assert len(article.sections) == 1
    assert article.sections[0]["title"] == "Function"
    assert article.sources == ["UniProt", "Wikipedia"]


# ── Helper function tests ──────────────────────────────────────────────


def test_strip_html_removes_tags():
    """_strip_html removes HTML tags from text."""
    assert _strip_html("<p>Hello</p>") == "Hello"
    assert _strip_html("<b>Bold</b> text") == "Bold text"
    assert _strip_html("No tags") == "No tags"
    assert _strip_html("<a href='url'>link</a>") == "link"


def test_strip_html_handles_nested_tags():
    """_strip_html handles nested HTML tags."""
    assert _strip_html("<div><span>nested</span></div>") == "nested"
    assert _strip_html("<ul><li>item</li></ul>") == "item"


def test_strip_pubmed_refs_removes_single_ref():
    """_strip_pubmed_refs removes single PubMed references."""
    text = "Protein function (PubMed:12345678)."
    result = _strip_pubmed_refs(text)
    assert "(PubMed:12345678)" not in result
    assert "Protein function" in result


def test_strip_pubmed_refs_removes_multiple_refs():
    """_strip_pubmed_refs removes multiple PubMed references."""
    text = "Function (PubMed:111, PubMed:222)."
    result = _strip_pubmed_refs(text)
    assert "PubMed" not in result


def test_strip_pubmed_refs_no_refs():
    """_strip_pubmed_refs returns unchanged text if no refs."""
    text = "No references here."
    assert _strip_pubmed_refs(text) == text


def test_looks_like_gene_all_caps():
    """_looks_like_gene returns True for all-caps gene names."""
    assert _looks_like_gene("TP53") is True
    assert _looks_like_gene("BRCA1") is True
    assert _looks_like_gene("DNMT3A") is True


def test_looks_like_gene_lowercase_with_digit():
    """_looks_like_gene returns True for lowercase+digits pattern."""
    assert _looks_like_gene("ras1") is True
    assert _looks_like_gene("myc2") is True


def test_looks_like_gene_short_single_word():
    """_looks_like_gene returns True for short single words."""
    assert _looks_like_gene("insulin") is True
    assert _looks_like_gene("p53") is True


def test_looks_like_gene_false_for_phrases():
    """_looks_like_gene returns False for multi-word phrases."""
    assert _looks_like_gene("cell signaling") is False
    assert _looks_like_gene("apoptosis pathway") is False


def test_looks_like_gene_false_for_long_words():
    """_looks_like_gene returns False for very long words."""
    assert _looks_like_gene("supercalifragilisticexpialidocious") is False


# ── UniProt fetch tests ────────────────────────────────────────────────


def test_fetch_uniprot_success():
    """_fetch_uniprot returns BioArticle for valid gene."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [{
            "primaryAccession": "P04637",
            "proteinDescription": {
                "recommendedName": {"fullName": {"value": "Cellular tumor antigen p53"}}
            },
            "comments": [{
                "commentType": "FUNCTION",
                "texts": [{"value": "Tumor suppressor. Acts as a transcription factor."}]
            }]
        }]
    }

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = _fetch_uniprot("TP53")

    assert result is not None
    assert result.title == "Cellular tumor antigen p53"
    assert "UniProt" in result.sources


def test_fetch_uniprot_no_results():
    """_fetch_uniprot returns None when no results found."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = _fetch_uniprot("NOTAREALGENEXYZ123")

    assert result is None


def test_fetch_uniprot_non_200_status():
    """_fetch_uniprot handles non-200 status codes."""
    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = _fetch_uniprot("TP53")

    assert result is None


def test_fetch_uniprot_extracts_catalytic_activity():
    """_fetch_uniprot extracts catalytic activity from comments."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [{
            "primaryAccession": "P12345",
            "proteinDescription": {
                "recommendedName": {"fullName": {"value": "Test Enzyme"}}
            },
            "comments": [
                {"commentType": "FUNCTION", "texts": [{"value": "Test function."}]},
                {"commentType": "CATALYTIC ACTIVITY", "reaction": {"name": "ATP hydrolysis", "ecNumber": "3.6.1.3"}}
            ]
        }]
    }

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = _fetch_uniprot("TEST")

    assert result is not None
    assert any("Catalytic activity" in s["title"] for s in result.sections)


def test_fetch_uniprot_extracts_domains():
    """_fetch_uniprot extracts domain information."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [{
            "primaryAccession": "P12345",
            "proteinDescription": {
                "recommendedName": {"fullName": {"value": "Domain Protein"}}
            },
            "comments": [
                {"commentType": "FUNCTION", "texts": [{"value": "Test function."}]},
                {"commentType": "DOMAIN", "texts": [{"value": "Kinase domain."}]}
            ]
        }]
    }

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = _fetch_uniprot("TEST")

    assert result is not None
    assert any(s["title"] == "Domain" for s in result.sections)


# ── Reactome fetch tests ───────────────────────────────────────────────


def test_fetch_reactome_success():
    """_fetch_reactome returns BioArticle for pathway term."""
    mock_search_response = MagicMock()
    mock_search_response.status_code = 200
    mock_search_response.json.return_value = {
        "results": [{
            "entries": [{
                "stId": "R-HSA-12345",
                "name": "Apoptosis pathway"
            }]
        }]
    }

    mock_detail_response = MagicMock()
    mock_detail_response.status_code = 200
    mock_detail_response.json.return_value = {
        "summation": [{"text": "Apoptosis is programmed cell death."}]
    }

    with patch("httpx.Client") as mock_client:
        client_mock = mock_client.return_value.__enter__.return_value
        client_mock.get.side_effect = [mock_search_response, mock_detail_response]
        result = _fetch_reactome("Apoptosis")

    assert result is not None
    assert "pathway" in result.title.lower()
    assert result.sources == ["Reactome"]


def test_fetch_reactome_no_results():
    """_fetch_reactome returns None when no pathways found."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = _fetch_reactome("notarealpathway123")

    assert result is None


def test_fetch_reactome_skips_irrelevant():
    """_fetch_reactome returns None when pathway name doesn't match term."""
    mock_search_response = MagicMock()
    mock_search_response.status_code = 200
    mock_search_response.json.return_value = {
        "results": [{
            "entries": [{
                "stId": "R-HSA-99999",
                "name": "Completely unrelated pathway"
            }]
        }]
    }

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_search_response
        result = _fetch_reactome("Apoptosis")

    assert result is None


# ── Wikipedia fetch tests ───────────────────────────────────────────────


def test_fetch_wikipedia_success():
    """_fetch_wikipedia returns BioArticle for valid term."""
    mock_summary_response = MagicMock()
    mock_summary_response.status_code = 200
    mock_summary_response.json.return_value = {
        "title": "Apoptosis",
        "extract": "Apoptosis is programmed cell death.",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Apoptosis"}}
    }

    mock_sections_response = MagicMock()
    mock_sections_response.status_code = 200
    mock_sections_response.json.return_value = {
        "remaining": {"sections": []}
    }

    with patch("httpx.Client") as mock_client:
        client_mock = mock_client.return_value.__enter__.return_value
        client_mock.get.side_effect = [mock_summary_response, mock_sections_response]
        result = _fetch_wikipedia("Apoptosis")

    assert result is not None
    assert result.title == "Apoptosis"
    assert result.sources == ["Wikipedia"]


def test_fetch_wikipedia_disambiguation():
    """_fetch_wikipedia returns None for disambiguation pages."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "title": "Test",
        "extract": "Test may refer to:",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Test"}}
    }

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = _fetch_wikipedia("Test")

    assert result is None


def test_fetch_wikipedia_404_falls_back_to_search():
    """_fetch_wikipedia falls back to search on 404."""
    mock_404_response = MagicMock()
    mock_404_response.status_code = 404

    mock_summary_response = MagicMock()
    mock_summary_response.status_code = 200
    mock_summary_response.json.return_value = {
        "title": "Apoptosis",
        "extract": "Programmed cell death.",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Apoptosis"}}
    }

    mock_sections_response = MagicMock()
    mock_sections_response.status_code = 200
    mock_sections_response.json.return_value = {"remaining": {"sections": []}}

    # Create a mock client instance that properly supports context manager
    mock_client_instance = MagicMock()
    mock_client_instance.get.side_effect = [
        mock_404_response,  # Initial 404
        mock_summary_response,  # Summary after search
        mock_sections_response,  # Sections
    ]
    mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
    mock_client_instance.__exit__ = MagicMock(return_value=False)

    with patch("metabolon.lysin.fetch._search_wikipedia", return_value=["Apoptosis"]):
        with patch("httpx.Client", return_value=mock_client_instance):
            result = _fetch_wikipedia("nonexistentterm123")

    assert result is not None
    assert result.title == "Apoptosis"


def test_search_wikipedia_returns_results():
    """_search_wikipedia returns list of titles."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = ["apoptosis", ["Apoptosis", "Programmed cell death"]]

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = _search_wikipedia("apoptosis")

    assert isinstance(result, list)


def test_search_wikipedia_empty_results():
    """_search_wikipedia returns empty list on no results."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = ["term", []]

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = _search_wikipedia("nonexistentterm123xyz")

    assert result == []


# ── fetch_summary tests ─────────────────────────────────────────────────


def test_fetch_summary_routes_gene_to_uniprot():
    """fetch_summary routes gene-like terms to UniProt first."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [{
            "primaryAccession": "P04637",
            "proteinDescription": {
                "recommendedName": {"fullName": {"value": "Tumor protein p53"}}
            },
            "comments": [{
                "commentType": "FUNCTION",
                "texts": [{"value": "Tumor suppressor protein."}]
            }]
        }]
    }

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = fetch_summary("TP53")

    assert result.title == "Tumor protein p53"


def test_fetch_summary_raises_lookup_error_not_found():
    """fetch_summary raises LookupError when term not found anywhere."""
    # Mock all three sources to return None
    with patch("metabolon.lysin.fetch._fetch_uniprot", return_value=None):
        with patch("metabolon.lysin.fetch._fetch_reactome", return_value=None):
            with patch("metabolon.lysin.fetch._fetch_wikipedia", return_value=None):
                with pytest.raises(LookupError) as exc_info:
                    fetch_summary("zzzznonexistentterm123xyz")
                assert "not found" in str(exc_info.value).lower()


# ── fetch_sections tests ────────────────────────────────────────────────


def test_fetch_sections_returns_list():
    """fetch_sections returns list of section dicts."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "remaining": {
            "sections": [
                {"line": "Mechanism", "text": "Details about mechanism."},
                {"line": "Function", "text": "Function details."}
            ]
        }
    }

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = fetch_sections("Apoptosis")

    assert isinstance(result, list)
    assert len(result) == 2


def test_fetch_sections_non_200_returns_empty():
    """fetch_sections returns empty list on non-200 status."""
    mock_response = MagicMock()
    mock_response.status_code = 404

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = fetch_sections("NonExistentPage")

    assert result == []


def test_fetch_sections_filters_empty():
    """fetch_sections filters out sections with empty title or text."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "remaining": {
            "sections": [
                {"line": "Valid", "text": "Good content"},
                {"line": "", "text": "No title"},
                {"line": "No text", "text": ""},
            ]
        }
    }

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        result = fetch_sections("Test")

    assert len(result) == 1
    assert result[0]["title"] == "Valid"
