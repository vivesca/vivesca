from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.rheotaxis_engine import (
    RheotaxisResult,
    _get_key,
    _perplexity_key,
    _perplexity_query,
    format_results,
    multi_query_search,
    parallel_search,
    perplexity_deep,
    perplexity_quick,
    perplexity_thorough,
    search_exa,
    search_perplexity,
    search_serper,
    search_tavily,
)


class TestPerplexityKey:
    def test_perplexity_key_present(self):
        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            assert _perplexity_key() == "test-key"

    def test_perplexity_key_missing_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="PERPLEXITY_API_KEY not set"):
                _perplexity_key()


class TestGetKey:
    def test_get_key_present(self):
        with patch.dict("os.environ", {"TEST_KEY": "my-key"}):
            assert _get_key("TEST_KEY") == "my-key"

    def test_get_key_missing_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="TEST_KEY not set"):
                _get_key("TEST_KEY")


class TestPerplexityQuery:
    @patch("metabolon.organelles.rheotaxis_engine.urllib.request.urlopen")
    @patch("metabolon.organelles.rheotaxis_engine._perplexity_key")
    def test_perplexity_query_success_no_citations(self, mock_key, mock_urlopen):
        mock_key.return_value = "test-key"

        # Mock response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"choices": [{"message": {"content": "Test answer"}}]}
        ).encode()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_context

        result = _perplexity_query("sonar", "test query", timeout=10)

        assert "Test answer" in result
        mock_key.assert_called_once()
        mock_urlopen.assert_called_once()

    @patch("metabolon.organelles.rheotaxis_engine.urllib.request.urlopen")
    @patch("metabolon.organelles.rheotaxis_engine._perplexity_key")
    def test_perplexity_query_with_citations(self, mock_key, mock_urlopen):
        mock_key.return_value = "test-key"

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {
                "choices": [{"message": {"content": "Test answer"}}],
                "citations": ["https://example.com", "https://example.org"],
            }
        ).encode()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_context

        result = _perplexity_query("sonar", "test query", timeout=10)

        assert "Test answer" in result
        assert "Sources:" in result
        assert "https://example.com" in result
        assert "https://example.org" in result

    @patch("metabolon.organelles.rheotaxis_engine.urllib.request.urlopen")
    @patch("metabolon.organelles.rheotaxis_engine._perplexity_key")
    def test_perplexity_query_api_error(self, mock_key, mock_urlopen):
        mock_key.return_value = "test-key"
        mock_urlopen.side_effect = Exception("API error")

        with pytest.raises(Exception, match="API error"):
            _perplexity_query("sonar", "test query", timeout=10)


class TestPerplexityTierFunctions:
    @patch("metabolon.organelles.rheotaxis_engine._perplexity_query")
    def test_perplexity_quick(self, mock_query):
        mock_query.return_value = "quick result"
        result = perplexity_quick("test")
        mock_query.assert_called_once_with("sonar", "test", timeout=30)
        assert result == "quick result"

    @patch("metabolon.organelles.rheotaxis_engine._perplexity_query")
    def test_perplexity_thorough(self, mock_query):
        mock_query.return_value = "thorough result"
        result = perplexity_thorough("test")
        mock_query.assert_called_once_with("sonar-pro", "test", timeout=60)
        assert result == "thorough result"

    @patch("metabolon.organelles.rheotaxis_engine._perplexity_query")
    def test_perplexity_deep_no_save(self, mock_query):
        mock_query.return_value = "deep result"
        result = perplexity_deep("test")
        mock_query.assert_called_once_with("sonar-deep-research", "test", timeout=300)
        assert result == "deep result"

    @patch("metabolon.organelles.rheotaxis_engine._perplexity_query")
    @patch("builtins.open")
    @patch("os.makedirs")
    def test_perplexity_deep_with_save(self, mock_makedirs, mock_open, mock_query):
        mock_query.return_value = "deep result"
        result = perplexity_deep("test", save_path="/tmp/output/test.txt")
        mock_makedirs.assert_called_once()
        mock_open.assert_called_once_with("/tmp/output/test.txt", "w")
        assert result == "deep result"


class TestSearchExa:
    @patch("metabolon.organelles.rheotaxis_engine.urllib.request.urlopen")
    @patch.dict("os.environ", {"EXA_API_KEY": "test-exa-key"})
    def test_search_exa_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {
                "results": [
                    {
                        "title": "Test Result",
                        "url": "https://exa.com/test",
                        "text": "This is a test snippet",
                    }
                ]
            }
        ).encode()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_context

        result = search_exa("test query", timeout=10)
        assert isinstance(result, RheotaxisResult)
        assert result.backend == "exa"
        assert result.query == "test query"
        assert len(result.results) == 1
        assert result.results[0]["title"] == "Test Result"
        assert result.results[0]["url"] == "https://exa.com/test"
        assert "This is a test snippet" in result.results[0]["snippet"]
        assert result.error == ""

    @patch.dict("os.environ", {}, clear=True)
    def test_search_exa_missing_key(self):
        result = search_exa("test query")
        assert "EXA_API_KEY not set" in result.error
        assert len(result.results) == 0

    @patch("metabolon.organelles.rheotaxis_engine.urllib.request.urlopen")
    @patch.dict("os.environ", {"EXA_API_KEY": "test-exa-key"})
    def test_search_exa_api_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Network error")
        result = search_exa("test query")
        assert "Network error" in result.error
        assert len(result.results) == 0


class TestSearchTavily:
    @patch("metabolon.organelles.rheotaxis_engine.urllib.request.urlopen")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test-tavily-key"})
    def test_search_tavily_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {
                "answer": "Test answer from Tavily",
                "results": [
                    {
                        "title": "Tavily Result",
                        "url": "https://tavily.com/test",
                        "content": "Tavily snippet content",
                    }
                ],
            }
        ).encode()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_context

        result = search_tavily("test query", timeout=10)
        assert isinstance(result, RheotaxisResult)
        assert result.backend == "tavily"
        assert result.answer == "Test answer from Tavily"
        assert len(result.results) == 1
        assert result.error == ""

    @patch.dict("os.environ", {}, clear=True)
    def test_search_tavily_missing_key(self):
        result = search_tavily("test query")
        assert "TAVILY_API_KEY not set" in result.error
        assert len(result.results) == 0

    @patch("metabolon.organelles.rheotaxis_engine.urllib.request.urlopen")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test-tavily-key"})
    def test_search_tavily_api_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Tavily error")
        result = search_tavily("test query")
        assert "Tavily error" in result.error
        assert len(result.results) == 0


class TestSearchSerper:
    @patch("metabolon.organelles.rheotaxis_engine.urllib.request.urlopen")
    @patch.dict("os.environ", {"SERPER_API_KEY": "test-serper-key"})
    def test_search_serper_success_no_knowledge_graph(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {
                "organic": [
                    {
                        "title": "Serper Result",
                        "link": "https://serper.dev/test",
                        "snippet": "Serper snippet",
                    }
                ]
            }
        ).encode()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_context

        result = search_serper("test query", timeout=10)
        assert isinstance(result, RheotaxisResult)
        assert result.backend == "serper"
        assert len(result.results) == 1
        assert result.answer == ""
        assert result.error == ""

    @patch("metabolon.organelles.rheotaxis_engine.urllib.request.urlopen")
    @patch.dict("os.environ", {"SERPER_API_KEY": "test-serper-key"})
    def test_search_serper_with_knowledge_graph(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {
                "organic": [],
                "knowledgeGraph": {"title": "Python", "description": "Programming language"},
            }
        ).encode()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_context

        result = search_serper("Python", timeout=10)
        assert "Python: Programming language" in result.answer
        assert len(result.results) == 0
        assert result.error == ""

    @patch.dict("os.environ", {}, clear=True)
    def test_search_serper_missing_key(self):
        result = search_serper("test query")
        assert "SERPER_API_KEY not set" in result.error
        assert len(result.results) == 0

    @patch("metabolon.organelles.rheotaxis_engine.urllib.request.urlopen")
    @patch.dict("os.environ", {"SERPER_API_KEY": "test-serper-key"})
    def test_search_serper_api_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Serper error")
        result = search_serper("test query")
        assert "Serper error" in result.error
        assert len(result.results) == 0


class TestParallelSearch:
    @patch("metabolon.organelles.rheotaxis_engine.search_perplexity")
    @patch("metabolon.organelles.rheotaxis_engine.search_exa")
    @patch("metabolon.organelles.rheotaxis_engine.search_tavily")
    @patch("metabolon.organelles.rheotaxis_engine.search_serper")
    def test_parallel_search_all_backends(self, mock_serper, mock_tavily, mock_exa, mock_perp):
        mock_perp.return_value = RheotaxisResult(
            backend="perplexity", query="test", results=[], answer="perp answer"
        )
        mock_exa.return_value = RheotaxisResult(
            backend="exa", query="test", results=[{"title": "exa"}], error=""
        )
        mock_tavily.return_value = RheotaxisResult(
            backend="tavily", query="test", results=[], answer="tavily answer"
        )
        mock_serper.return_value = RheotaxisResult(
            backend="serper", query="test", results=[{"title": "serper"}], error=""
        )

        results = parallel_search("test query")
        assert len(results) == 4
        backends = {r.backend for r in results}
        assert backends == {"perplexity", "exa", "tavily", "serper"}

    def test_parallel_search_unknown_backend_skipped(self):
        with patch("metabolon.organelles.rheotaxis_engine.search_perplexity") as mock_perp:
            mock_perp.return_value = RheotaxisResult(
                backend="perplexity", query="test", results=[], error=""
            )
            # Unknown backend should be skipped
            results = parallel_search("test query", backends=["perplexity", "nonexistent"])
            assert len(results) == 1
            assert results[0].backend == "perplexity"


class TestMultiQuerySearch:
    @patch("metabolon.organelles.rheotaxis_engine.search_perplexity")
    @patch("metabolon.organelles.rheotaxis_engine.search_exa")
    def test_multi_query_search_multiple_queries(self, mock_exa, mock_perp):
        mock_perp.side_effect = lambda q, *args: RheotaxisResult(
            backend="perplexity", query=q, results=[], answer=f"answer for {q}"
        )
        mock_exa.side_effect = lambda q, *args: RheotaxisResult(
            backend="exa", query=q, results=[], error=""
        )

        results = multi_query_search(["query1", "query2"], backends=["perplexity", "exa"])
        assert isinstance(results, dict)
        assert "query1" in results
        assert "query2" in results
        assert len(results["query1"]) == 2
        assert len(results["query2"]) == 2
        assert any(r.backend == "perplexity" for r in results["query1"])
        assert any(r.backend == "exa" for r in results["query1"])

    def test_multi_query_unknown_backend_skipped(self):
        with patch("metabolon.organelles.rheotaxis_engine.search_perplexity") as mock_perp:
            mock_perp.side_effect = lambda q, *args: RheotaxisResult(
                backend="perplexity", query=q, results=[], error=""
            )
            results = multi_query_search(["q1"], backends=["perplexity", "unknown"])
            assert len(results["q1"]) == 1


class TestFormatResults:
    def test_format_results_with_error(self):
        result = RheotaxisResult(
            backend="test", query="q", results=[], error="Something went wrong"
        )
        formatted = format_results([result])
        assert "## test (q)" in formatted
        assert "ERROR: Something went wrong" in formatted

    def test_format_results_with_answer(self):
        result = RheotaxisResult(
            backend="perplexity", query="test", results=[], answer="This is the answer"
        )
        formatted = format_results([result])
        assert "Answer: This is the answer" in formatted

    def test_format_results_with_results(self):
        result = RheotaxisResult(
            backend="exa",
            query="test",
            results=[
                {
                    "title": "Result Title",
                    "url": "https://example.com",
                    "snippet": "Result snippet text",
                }
            ],
        )
        formatted = format_results([result])
        assert "Result Title" in formatted


class TestSearchPerplexity:
    @patch("metabolon.organelles.rheotaxis_engine._DEPTH_FN")
    def test_search_perplexity_success_quick(self, mock_depth_fn):
        mock_fn = MagicMock()
        mock_fn.return_value = "answer text"
        mock_depth_fn.get.return_value = mock_fn
        result = search_perplexity("test query", depth="quick")
        assert isinstance(result, RheotaxisResult)
        assert result.backend == "perplexity"
        assert result.query == "test query"
        assert result.answer == "answer text"
        assert result.error == ""
        assert result.results == []

    @patch("metabolon.organelles.rheotaxis_engine._DEPTH_FN")
    def test_search_perplexity_success_thorough(self, mock_depth_fn):
        mock_fn = MagicMock()
        mock_fn.return_value = "thorough answer"
        mock_depth_fn.get.return_value = mock_fn
        result = search_perplexity("test query", depth="thorough")
        assert result.answer == "thorough answer"
        assert result.error == ""

    @patch("metabolon.organelles.rheotaxis_engine._DEPTH_FN")
    def test_search_perplexity_error(self, mock_depth_fn):
        mock_fn = MagicMock()
        mock_fn.side_effect = Exception("API failure")
        mock_depth_fn.get.return_value = mock_fn
        result = search_perplexity("test query")
        assert result.error == "API failure"
        assert result.answer == ""

    def test_parallel_search_subset_backends(self):
        with patch("metabolon.organelles.rheotaxis_engine._BACKENDS") as mock_backends:
            mock_perp = MagicMock()
            mock_perp.return_value = RheotaxisResult(
                backend="perplexity", query="test", results=[], answer=""
            )
            mock_exa = MagicMock()
            mock_exa.return_value = RheotaxisResult(
                backend="exa", query="test", results=[], error=""
            )
            mock_backends.__getitem__.side_effect = lambda key: {
                "perplexity": mock_perp,
                "exa": mock_exa,
            }[key]
            mock_backends.__contains__.side_effect = lambda key: key in {"perplexity", "exa"}

            results = parallel_search("test query", backends=["perplexity", "exa"])
            assert len(results) == 2
            assert mock_perp.called
            assert mock_exa.called
