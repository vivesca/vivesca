"""Tests for effectors/grok - xAI web search CLI."""

import json
import os
import sys
import urllib.error
from unittest.mock import patch, MagicMock

import pytest

# Add effectors directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'effectors')))

import grok


# ─────────────────────────────────────────────────────────────────────────────
# Constant tests
# ─────────────────────────────────────────────────────────────────────────────

def test_api_url():
    """Test API_URL is set correctly."""
    assert grok.API_URL == "https://api.x.ai/v1/responses"


def test_default_model():
    """Test DEFAULT_MODEL is set."""
    assert grok.DEFAULT_MODEL == "grok-4-1-fast-reasoning"


def test_plain_model():
    """Test PLAIN_MODEL is set."""
    assert grok.PLAIN_MODEL == "grok-3-mini-fast"


# ─────────────────────────────────────────────────────────────────────────────
# Keychain helper tests
# ─────────────────────────────────────────────────────────────────────────────

def test_keychain_success():
    """Test _keychain returns password on success."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="test-api-key\n",
        )
        result = grok._keychain("test-service")
        assert result == "test-api-key"
        mock_run.assert_called_once()


def test_keychain_failure():
    """Test _keychain returns None on failure."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
        )
        result = grok._keychain("test-service")
        assert result is None


def test_keychain_exception():
    """Test _keychain returns None on exception."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("boom")
        result = grok._keychain("test-service")
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# Search function tests
# ─────────────────────────────────────────────────────────────────────────────

def test_search_no_api_key_exits():
    """Test search exits when no API key available."""
    with patch.dict(os.environ, {"XAI_API_KEY": ""}, clear=False):
        with patch("grok._keychain", return_value=None):
            with pytest.raises(SystemExit) as exc_info:
                grok.search("test query")
            assert exc_info.value.code == 1


def test_search_uses_env_api_key():
    """Test search uses XAI_API_KEY from environment."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "output": [{"type": "message", "content": [{"type": "output_text", "text": "Hello world"}]}],
        "citations": [],
        "usage": {"total_tokens": 100, "cost_in_usd_ticks": 100000000},
    }).encode()

    with patch.dict(os.environ, {"XAI_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__ = lambda self: self
            mock_urlopen.return_value.__exit__ = lambda self, *args: None
            mock_urlopen.return_value.read = mock_response.read

            with patch("builtins.print") as mock_print:
                grok.search("test query")
                # Verify request was made with correct auth
                call_args = mock_urlopen.call_args
                req = call_args[0][0]
                assert req.headers.get("Authorization") == "Bearer test-key"


def test_search_with_domain_filter():
    """Test search includes domain filter in request."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "output": [{"type": "message", "content": [{"type": "output_text", "text": "Result"}]}],
    }).encode()

    with patch.dict(os.environ, {"XAI_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__ = lambda self: self
            mock_urlopen.return_value.__exit__ = lambda self, *args: None
            mock_urlopen.return_value.read = mock_response.read

            with patch("builtins.print"):
                grok.search("test query", allowed_domains=["reddit.com", "twitter.com"])
                
                call_args = mock_urlopen.call_args
                req = call_args[0][0]
                body = json.loads(req.data)
                assert "tools" in body
                assert body["tools"][0]["filters"]["allowed_domains"] == ["reddit.com", "twitter.com"]


def test_search_no_search_mode():
    """Test no_search mode doesn't include web_search tool."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "output": [{"type": "message", "content": [{"type": "output_text", "text": "Plain response"}]}],
    }).encode()

    with patch.dict(os.environ, {"XAI_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__ = lambda self: self
            mock_urlopen.return_value.__exit__ = lambda self, *args: None
            mock_urlopen.return_value.read = mock_response.read

            with patch("builtins.print"):
                grok.search("explain quantum", no_search=True)
                
                call_args = mock_urlopen.call_args
                req = call_args[0][0]
                body = json.loads(req.data)
                assert "tools" not in body
                assert body["model"] == grok.PLAIN_MODEL


def test_search_raw_mode():
    """Test raw mode prints JSON response."""
    mock_data = {"output": [{"type": "message", "content": [{"type": "output_text", "text": "Test"}]}]}
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(mock_data).encode()

    with patch.dict(os.environ, {"XAI_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__ = lambda self: self
            mock_urlopen.return_value.__exit__ = lambda self, *args: None
            mock_urlopen.return_value.read = mock_response.read

            with patch("builtins.print") as mock_print:
                grok.search("test query", raw=True)
                # Should print JSON
                printed_json = json.loads(mock_print.call_args[0][0])
                assert printed_json == mock_data


def test_search_http_error():
    """Test search handles HTTP errors."""
    with patch.dict(os.environ, {"XAI_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_error = urllib.error.HTTPError(
                "https://api.x.ai/v1/responses", 
                401, 
                "Unauthorized", 
                {}, 
                None
            )
            mock_error.fp = MagicMock()
            mock_error.fp.read.return_value = b'{"error": "Invalid API key"}'
            mock_urlopen.side_effect = mock_error

            with pytest.raises(SystemExit) as exc_info:
                grok.search("test query")
            assert exc_info.value.code == 1


def test_search_url_error():
    """Test search handles connection errors."""
    with patch.dict(os.environ, {"XAI_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

            with pytest.raises(SystemExit) as exc_info:
                grok.search("test query")
            assert exc_info.value.code == 1


def test_search_prints_citations():
    """Test search prints citations when present."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "output": [{"type": "message", "content": [{"type": "output_text", "text": "Response"}]}],
        "citations": [
            {"url": "https://example.com", "title": "Example"},
            "https://another.com"
        ],
    }).encode()

    with patch.dict(os.environ, {"XAI_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__ = lambda self: self
            mock_urlopen.return_value.__exit__ = lambda self, *args: None
            mock_urlopen.return_value.read = mock_response.read

            with patch("builtins.print") as mock_print:
                grok.search("test query")
                prints = [str(c[0][0]) if c[0] else "" for c in mock_print.call_args_list]
                assert any("Example" in p and "https://example.com" in p for p in prints)


def test_search_prints_cost():
    """Test search prints cost from usage."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "output": [{"type": "message", "content": [{"type": "output_text", "text": "Response"}]}],
        "usage": {"total_tokens": 150, "cost_in_usd_ticks": 150000000},  # 0.015 USD
    }).encode()

    with patch.dict(os.environ, {"XAI_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__ = lambda self: self
            mock_urlopen.return_value.__exit__ = lambda self, *args: None
            mock_urlopen.return_value.read = mock_response.read

            with patch("builtins.print") as mock_print:
                grok.search("test query")
                prints = [str(c[0][0]) if c[0] else "" for c in mock_print.call_args_list]
                assert any("150 tokens" in p and "$0.0150" in p for p in prints)


def test_search_custom_model():
    """Test search with custom model."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "output": [{"type": "message", "content": [{"type": "output_text", "text": "Response"}]}],
    }).encode()

    with patch.dict(os.environ, {"XAI_API_KEY": "test-key"}):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__ = lambda self: self
            mock_urlopen.return_value.__exit__ = lambda self, *args: None
            mock_urlopen.return_value.read = mock_response.read

            with patch("builtins.print"):
                grok.search("test query", model="custom-model")
                
                call_args = mock_urlopen.call_args
                req = call_args[0][0]
                body = json.loads(req.data)
                assert body["model"] == "custom-model"


# ─────────────────────────────────────────────────────────────────────────────
# Main/CLI tests
# ─────────────────────────────────────────────────────────────────────────────

def test_main_basic_query():
    """Test main parses basic query correctly."""
    with patch("sys.argv", ["grok", "hello", "world"]):
        with patch.dict(os.environ, {"XAI_API_KEY": "test-key"}):
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = json.dumps({
                    "output": [{"type": "message", "content": [{"type": "output_text", "text": "Hi"}]}],
                }).encode()
                mock_urlopen.return_value.__enter__ = lambda self: self
                mock_urlopen.return_value.__exit__ = lambda self, *args: None
                mock_urlopen.return_value.read = mock_response.read

                with patch("builtins.print"):
                    grok.main()
                    # Verify query was joined
                    call_args = mock_urlopen.call_args
                    req = call_args[0][0]
                    body = json.loads(req.data)
                    assert body["input"][0]["content"] == "hello world"


def test_main_x_only_flag():
    """Test main handles --x-only flag."""
    with patch("sys.argv", ["grok", "--x-only", "query"]):
        with patch.dict(os.environ, {"XAI_API_KEY": "test-key"}):
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = json.dumps({
                    "output": [{"type": "message", "content": [{"type": "output_text", "text": "Hi"}]}],
                }).encode()
                mock_urlopen.return_value.__enter__ = lambda self: self
                mock_urlopen.return_value.__exit__ = lambda self, *args: None
                mock_urlopen.return_value.read = mock_response.read

                with patch("builtins.print"):
                    grok.main()
                    call_args = mock_urlopen.call_args
                    req = call_args[0][0]
                    body = json.loads(req.data)
                    assert body["tools"][0]["filters"]["allowed_domains"] == ["x.com"]


def test_main_domain_flag():
    """Test main handles --domain flag."""
    with patch("sys.argv", ["grok", "--domain", "reddit.com", "query"]):
        with patch.dict(os.environ, {"XAI_API_KEY": "test-key"}):
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = json.dumps({
                    "output": [{"type": "message", "content": [{"type": "output_text", "text": "Hi"}]}],
                }).encode()
                mock_urlopen.return_value.__enter__ = lambda self: self
                mock_urlopen.return_value.__exit__ = lambda self, *args: None
                mock_urlopen.return_value.read = mock_response.read

                with patch("builtins.print"):
                    grok.main()
                    call_args = mock_urlopen.call_args
                    req = call_args[0][0]
                    body = json.loads(req.data)
                    assert body["tools"][0]["filters"]["allowed_domains"] == ["reddit.com"]
