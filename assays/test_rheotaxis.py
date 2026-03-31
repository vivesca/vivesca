"""Tests for metabolon.enzymes.rheotaxis."""

from __future__ import annotations

from unittest.mock import MagicMock

from metabolon.enzymes.rheotaxis import rheotaxis_search


def test_single_query_uses_parallel_search_and_formats_results(monkeypatch) -> None:
    mock_parallel_search = MagicMock(return_value=["result"])
    mock_format_results = MagicMock(return_value="formatted")
    mock_multi_query_search = MagicMock()

    monkeypatch.setattr(
        "metabolon.enzymes.rheotaxis.rheotaxis_engine.parallel_search",
        mock_parallel_search,
    )
    monkeypatch.setattr(
        "metabolon.enzymes.rheotaxis.rheotaxis_engine.format_results",
        mock_format_results,
    )
    monkeypatch.setattr(
        "metabolon.enzymes.rheotaxis.rheotaxis_engine.multi_query_search",
        mock_multi_query_search,
    )

    result = rheotaxis_search(
        "latest hkma ai circular",
        backends="perplexity, exa",
        depth="thorough",
        timeout=42,
    )

    assert result == "formatted"
    mock_parallel_search.assert_called_once_with(
        "latest hkma ai circular",
        backends=["perplexity", "exa"],
        depth="thorough",
        timeout=42,
    )
    mock_format_results.assert_called_once_with(["result"])
    mock_multi_query_search.assert_not_called()


def test_multi_query_uses_multi_query_search_and_formats_each_block(monkeypatch) -> None:
    mock_parallel_search = MagicMock()
    mock_multi_query_search = MagicMock(
        return_value={
            "first framing": ["first-result"],
            "second framing": ["second-result"],
        }
    )
    mock_format_results = MagicMock(side_effect=["formatted-first", "formatted-second"])

    monkeypatch.setattr(
        "metabolon.enzymes.rheotaxis.rheotaxis_engine.parallel_search",
        mock_parallel_search,
    )
    monkeypatch.setattr(
        "metabolon.enzymes.rheotaxis.rheotaxis_engine.multi_query_search",
        mock_multi_query_search,
    )
    monkeypatch.setattr(
        "metabolon.enzymes.rheotaxis.rheotaxis_engine.format_results",
        mock_format_results,
    )

    result = rheotaxis_search(
        "first framing | second framing",
        backends="serper,tavily",
        depth="quick",
        timeout=9,
    )

    assert result == "# first framing\nformatted-first\n# second framing\nformatted-second"
    mock_multi_query_search.assert_called_once_with(
        ["first framing", "second framing"],
        backends=["serper", "tavily"],
        depth="quick",
        timeout=9,
    )
    mock_parallel_search.assert_not_called()
    assert mock_format_results.call_count == 2
    mock_format_results.assert_any_call(["first-result"])
    mock_format_results.assert_any_call(["second-result"])


def test_query_and_backend_strings_are_stripped(monkeypatch) -> None:
    mock_parallel_search = MagicMock(return_value=[])
    mock_format_results = MagicMock(return_value="")

    monkeypatch.setattr(
        "metabolon.enzymes.rheotaxis.rheotaxis_engine.parallel_search",
        mock_parallel_search,
    )
    monkeypatch.setattr(
        "metabolon.enzymes.rheotaxis.rheotaxis_engine.format_results",
        mock_format_results,
    )

    rheotaxis_search("  one query  ", backends=" perplexity , tavily ")

    mock_parallel_search.assert_called_once_with(
        "one query",
        backends=["perplexity", "tavily"],
        depth="quick",
        timeout=20,
    )
