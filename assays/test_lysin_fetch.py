from unittest.mock import MagicMock, patch

import pytest

from metabolon.lysin.fetch import (
    _search_wikipedia,
    _strip_html,
    fetch_sections,
    fetch_summary,
)


def test_strip_html():
    assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"
    assert _strip_html("No html here") == "No html here"


@patch("httpx.Client.get")
def test_search_wikipedia(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        "endocytosis",
        ["Endocytosis", "Endocytosis (virus)"],
        [],
        [],
    ]
    mock_get.return_value = mock_response

    results = _search_wikipedia("endocytosis")
    assert results == ["Endocytosis", "Endocytosis (virus)"]


@patch("metabolon.lysin.fetch._fetch_wikipedia")
@patch("metabolon.lysin.fetch._fetch_reactome", return_value=None)
@patch("metabolon.lysin.fetch._fetch_uniprot", return_value=None)
def test_fetch_summary_exact_match(_mock_uni, _mock_react, mock_wiki):
    from metabolon.lysin.fetch import BioArticle

    mock_wiki.return_value = BioArticle(
        title="Endocytosis",
        definition="Endocytosis is a cellular process.",
        mechanism="Endocytosis is a cellular process. It involves cells taking in substances.",
        url="https://en.wikipedia.org/wiki/Endocytosis",
    )

    article = fetch_summary("Endocytosis")
    assert article.title == "Endocytosis"
    assert article.definition == "Endocytosis is a cellular process."
    assert (
        article.mechanism
        == "Endocytosis is a cellular process. It involves cells taking in substances."
    )
    assert article.url == "https://en.wikipedia.org/wiki/Endocytosis"


@patch("metabolon.lysin.fetch._fetch_wikipedia")
@patch("metabolon.lysin.fetch._fetch_reactome", return_value=None)
@patch("metabolon.lysin.fetch._fetch_uniprot", return_value=None)
def test_fetch_summary_fallback_search(_mock_uni, _mock_react, mock_wiki):
    from metabolon.lysin.fetch import BioArticle

    mock_wiki.return_value = BioArticle(
        title="Endocytosis",
        definition="Endocytosis is a cellular process.",
        mechanism="Endocytosis is a cellular process.",
        url="https://en.wikipedia.org/wiki/Endocytosis",
    )

    article = fetch_summary("endocytosi")
    assert article.title == "Endocytosis"
    mock_wiki.assert_called_once_with("endocytosi")


@patch("metabolon.lysin.fetch._fetch_wikipedia", return_value=None)
@patch("metabolon.lysin.fetch._fetch_reactome", return_value=None)
@patch("metabolon.lysin.fetch._fetch_uniprot", return_value=None)
def test_fetch_summary_not_found(_mock_uni, _mock_react, _mock_wiki):
    with pytest.raises(LookupError, match="not found"):
        fetch_summary("nonexistent_term_xyz")


@patch("metabolon.lysin.fetch._fetch_wikipedia", return_value=None)
@patch("metabolon.lysin.fetch._fetch_reactome", return_value=None)
@patch("metabolon.lysin.fetch._fetch_uniprot", return_value=None)
def test_fetch_summary_all_sources_exhausted(_mock_uni, _mock_react, _mock_wiki):
    with pytest.raises(LookupError, match="not found"):
        fetch_summary("ATP")


@patch("httpx.Client.get")
def test_fetch_sections(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "lead": {
            "sections": [{"id": 0, "text": "<p>Lead text</p>"}]
        },  # Typically no line in lead, should be skipped or parsed
        "remaining": {
            "sections": [{"id": 1, "line": "<b>Types</b>", "text": "<p>Some types</p>"}]
        },
    }
    mock_get.return_value = mock_response

    sections = fetch_sections("Endocytosis")
    assert len(sections) == 1
    assert sections[0]["title"] == "Types"
    assert sections[0]["text"] == "Some types"
