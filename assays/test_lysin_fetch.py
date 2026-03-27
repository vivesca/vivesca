from unittest.mock import MagicMock, patch

import pytest

from metabolon.lysin.fetch import (
    _strip_html,
    fetch_sections,
    fetch_summary,
    search_term,
)


def test_strip_html():
    assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"
    assert _strip_html("No html here") == "No html here"


@patch("httpx.Client.get")
def test_search_term(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        "endocytosis",
        ["Endocytosis", "Endocytosis (virus)"],
        [],
        [],
    ]
    mock_get.return_value = mock_response

    results = search_term("endocytosis")
    assert results == ["Endocytosis", "Endocytosis (virus)"]


@patch("httpx.Client.get")
def test_fetch_summary_exact_match(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "title": "Endocytosis",
        "extract": "Endocytosis is a cellular process. It involves cells taking in substances.",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Endocytosis"}},
    }
    mock_get.return_value = mock_response

    article = fetch_summary("Endocytosis")
    assert article.title == "Endocytosis"
    assert article.definition == "Endocytosis is a cellular process."
    assert (
        article.mechanism
        == "Endocytosis is a cellular process. It involves cells taking in substances."
    )
    assert article.url == "https://en.wikipedia.org/wiki/Endocytosis"


@patch("metabolon.lysin.fetch.search_term")
@patch("httpx.Client.get")
def test_fetch_summary_fallback_search(mock_get, mock_search):
    mock_404 = MagicMock()
    mock_404.status_code = 404

    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {
        "title": "Endocytosis",
        "extract": "Endocytosis is a cellular process.",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Endocytosis"}},
    }

    # First call is exact match (404), second call is summary for searched term (200)
    mock_get.side_effect = [mock_404, mock_200]
    mock_search.return_value = ["Endocytosis"]

    article = fetch_summary("endocytosi")
    assert article.title == "Endocytosis"
    mock_search.assert_called_once_with("endocytosi")


@patch("metabolon.lysin.fetch.search_term")
@patch("httpx.Client.get")
def test_fetch_summary_not_found(mock_get, mock_search):
    mock_404 = MagicMock()
    mock_404.status_code = 404
    mock_get.return_value = mock_404
    mock_search.return_value = []

    with pytest.raises(LookupError, match="not found"):
        fetch_summary("nonexistent_term_xyz")


@patch("httpx.Client.get")
def test_fetch_summary_disambiguation(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "title": "ATP",
        "extract": "ATP may refer to: Adenosine triphosphate, etc.",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/ATP"}},
    }
    mock_get.return_value = mock_response

    with pytest.raises(LookupError, match="disambiguation"):
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
