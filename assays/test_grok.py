#!/usr/bin/env python3
from __future__ import annotations

"""Tests for grok effector — mocks all external API calls."""


import json
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Execute the grok file directly into the namespace
grok_path = Path.home() / "germline" / "effectors" / "grok"
grok_code = grok_path.read_text()
_grok_dict = {}
exec(grok_code, _grok_dict)


# Make attributes accessible via dot notation
class GrokModule:
    def __getattr__(self, name):
        return _grok_dict[name]

    def __setattr__(self, name, value):
        _grok_dict[name] = value


grok = GrokModule()

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------


def test_api_url_is_set():
    """Test API_URL is correctly configured."""
    assert grok.API_URL == "https://api.x.ai/v1/responses"


def test_grok_default_model():
    """Test DEFAULT_MODEL is set correctly."""
    assert grok.DEFAULT_MODEL == "grok-4-1-fast-reasoning"


def test_plain_model():
    """Test PLAIN_MODEL is set correctly."""
    assert grok.PLAIN_MODEL == "grok-3-mini-fast"


# ---------------------------------------------------------------------------
# Test _keychain (works on macOS only, on Linux it will just return None)
# ---------------------------------------------------------------------------


def test_keychain_does_not_crash():
    """Test _keychain doesn't crash and just returns None on non-macOS."""
    # Since we're on Linux, this will just return None because security command doesn't exist
    # This test just verifies it doesn't crash, not that it actually extracts a key
    result = None
    try:
        result = grok._keychain("xai-api-key")
    except Exception:
        pytest.fail("_keychain crashed")
    # Either we get None (expected on Linux) or we get a string (if on macOS with keychain)
    assert result is None or isinstance(result, str)


def test_keychain_exception_returns_none():
    """Test _keychain returns None on exception."""

    def mock_run(*args, **kwargs):
        raise Exception("permission denied")

    with patch("subprocess.run", side_effect=mock_run):
        result = grok._keychain("xai-api-key")
        assert result is None


# ---------------------------------------------------------------------------
# Test argument parsing
# ---------------------------------------------------------------------------


def test_main_parses_query():
    """Test main parses a basic query."""
    mock_search = MagicMock()
    with patch.dict(_grok_dict, {"search": mock_search}):
        with patch("sys.argv", ["grok", "test", "query"]):
            grok.main()
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            assert call_args[0][0] == "test query"
            assert call_args[1]["allowed_domains"] is None
            assert call_args[1]["raw"] is False
            assert call_args[1]["no_search"] is False


def test_main_parses_x_only():
    """Test --x-only adds x.com domain."""
    mock_search = MagicMock()
    with patch.dict(_grok_dict, {"search": mock_search}):
        with patch("sys.argv", ["grok", "--x-only", "search"]):
            grok.main()
            assert mock_search.call_args[1]["allowed_domains"] == ["x.com"]


def test_main_parses_single_domain():
    """Test --domain adds a single domain."""
    mock_search = MagicMock()
    with patch.dict(_grok_dict, {"search": mock_search}):
        with patch("sys.argv", ["grok", "--domain", "example.com", "query"]):
            grok.main()
            assert mock_search.call_args[1]["allowed_domains"] == ["example.com"]


def test_main_parses_multiple_domains():
    """Test multiple --domain arguments."""
    mock_search = MagicMock()
    with patch.dict(_grok_dict, {"search": mock_search}):
        with patch("sys.argv", ["grok", "--domain", "a.com", "--domain", "b.com", "query"]):
            grok.main()
            assert mock_search.call_args[1]["allowed_domains"] == ["a.com", "b.com"]


def test_main_parses_no_search():
    """Test --no-search flag."""
    mock_search = MagicMock()
    with patch.dict(_grok_dict, {"search": mock_search}):
        with patch("sys.argv", ["grok", "--no-search", "query"]):
            grok.main()
            assert mock_search.call_args[1]["no_search"] is True


def test_main_parses_raw():
    """Test --raw flag."""
    mock_search = MagicMock()
    with patch.dict(_grok_dict, {"search": mock_search}):
        with patch("sys.argv", ["grok", "--raw", "query"]):
            grok.main()
            assert mock_search.call_args[1]["raw"] is True


def test_main_parses_custom_model():
    """Test custom --model argument."""
    mock_search = MagicMock()
    with patch.dict(_grok_dict, {"search": mock_search}):
        with patch("sys.argv", ["grok", "--model", "grok-4", "query"]):
            grok.main()
            assert mock_search.call_args[1]["model"] == "grok-4"


# ---------------------------------------------------------------------------
# Test search function - model selection
# ---------------------------------------------------------------------------


def test_search_uses_default_model_for_search():
    """Test search uses DEFAULT_MODEL when no_search is False."""
    with patch.dict(_grok_dict["os"].environ, {}, clear=True):
        with patch.dict(_grok_dict, {"_keychain": MagicMock(return_value="test-key")}):
            with patch.object(_grok_dict["urllib"].request, "urlopen") as mock_urlopen:
                mock_resp = MagicMock()
                mock_resp.read.return_value = b'{"output": []}'
                mock_urlopen.return_value.__enter__.return_value = mock_resp
                grok.search("test query", allowed_domains=None, no_search=False)
                # Check the request has the correct model
                called_request = mock_urlopen.call_args[0][0]
                payload = json.loads(called_request.data.decode())
                assert payload["model"] == grok.DEFAULT_MODEL


def test_search_uses_plain_model_for_no_search():
    """Test search uses PLAIN_MODEL when no_search is True."""
    with patch.dict(_grok_dict["os"].environ, {}, clear=True):
        with patch.dict(_grok_dict, {"_keychain": MagicMock(return_value="test-key")}):
            with patch.object(_grok_dict["urllib"].request, "urlopen") as mock_urlopen:
                mock_resp = MagicMock()
                mock_resp.read.return_value = b'{"output": []}'
                mock_urlopen.return_value.__enter__.return_value = mock_resp
                grok.search("test query", no_search=True)
                called_request = mock_urlopen.call_args[0][0]
                payload = json.loads(called_request.data.decode())
                assert payload["model"] == grok.PLAIN_MODEL


def test_search_uses_overridden_model():
    """Test search uses provided model when specified."""
    with patch.dict(_grok_dict["os"].environ, {}, clear=True):
        with patch.dict(_grok_dict, {"_keychain": MagicMock(return_value="test-key")}):
            with patch.object(_grok_dict["urllib"].request, "urlopen") as mock_urlopen:
                mock_resp = MagicMock()
                mock_resp.read.return_value = b'{"output": []}'
                mock_urlopen.return_value.__enter__.return_value = mock_resp
                grok.search("test query", model="custom-model", no_search=False)
                called_request = mock_urlopen.call_args[0][0]
                payload = json.loads(called_request.data.decode())
                assert payload["model"] == "custom-model"


# ---------------------------------------------------------------------------
# Test search tool configuration
# ---------------------------------------------------------------------------


def test_search_adds_web_search_tool():
    """Test search adds web_search tool when no_search is False."""
    with patch.dict(_grok_dict["os"].environ, {}, clear=True):
        with patch.dict(_grok_dict, {"_keychain": MagicMock(return_value="test-key")}):
            with patch.object(_grok_dict["urllib"].request, "urlopen") as mock_urlopen:
                mock_resp = MagicMock()
                mock_resp.read.return_value = b'{"output": []}'
                mock_urlopen.return_value.__enter__.return_value = mock_resp
                grok.search("test query")
                called_request = mock_urlopen.call_args[0][0]
                payload = json.loads(called_request.data.decode())
                assert "tools" in payload
                assert len(payload["tools"]) == 1
                assert payload["tools"][0]["type"] == "web_search"


def test_search_adds_domain_filter():
    """Test search adds allowed_domains filter when domains are provided."""
    with patch.dict(_grok_dict["os"].environ, {}, clear=True):
        with patch.dict(_grok_dict, {"_keychain": MagicMock(return_value="test-key")}):
            with patch.object(_grok_dict["urllib"].request, "urlopen") as mock_urlopen:
                mock_resp = MagicMock()
                mock_resp.read.return_value = b'{"output": []}'
                mock_urlopen.return_value.__enter__.return_value = mock_resp
                grok.search("test query", allowed_domains=["example.com", "github.com"])
                called_request = mock_urlopen.call_args[0][0]
                payload = json.loads(called_request.data.decode())
                assert payload["tools"][0]["filters"]["allowed_domains"] == [
                    "example.com",
                    "github.com",
                ]


def test_search_no_tool_when_no_search():
    """Test search doesn't add tool when no_search is True."""
    with patch.dict(_grok_dict["os"].environ, {}, clear=True):
        with patch.dict(_grok_dict, {"_keychain": MagicMock(return_value="test-key")}):
            with patch.object(_grok_dict["urllib"].request, "urlopen") as mock_urlopen:
                mock_resp = MagicMock()
                mock_resp.read.return_value = b'{"output": []}'
                mock_urlopen.return_value.__enter__.return_value = mock_resp
                grok.search("test query", no_search=True)
                called_request = mock_urlopen.call_args[0][0]
                payload = json.loads(called_request.data.decode())
                assert "tools" not in payload


# ---------------------------------------------------------------------------
# Test API key handling
# ---------------------------------------------------------------------------


def test_search_uses_env_api_key():
    """Test search uses XAI_API_KEY from environment."""
    mock_keychain = MagicMock()
    with patch.dict(_grok_dict["os"].environ, {"XAI_API_KEY": "env-key-123"}, clear=True):
        with patch.dict(_grok_dict, {"_keychain": mock_keychain}):
            with patch.object(_grok_dict["urllib"].request, "urlopen") as mock_urlopen:
                mock_resp = MagicMock()
                mock_resp.read.return_value = b'{"output": []}'
                mock_urlopen.return_value.__enter__.return_value = mock_resp
                grok.search("test query")
                mock_keychain.assert_not_called()
                called_request = mock_urlopen.call_args[0][0]
                assert called_request.headers["Authorization"] == "Bearer env-key-123"


def test_search_falls_back_to_keychain():
    """Test search falls back to keychain when env var not set."""
    mock_keychain = MagicMock(return_value="keychain-key")
    with patch.dict(_grok_dict["os"].environ, {}, clear=True):
        with patch.dict(_grok_dict, {"_keychain": mock_keychain}):
            with patch.object(_grok_dict["urllib"].request, "urlopen") as mock_urlopen:
                mock_resp = MagicMock()
                mock_resp.read.return_value = b'{"output": []}'
                mock_urlopen.return_value.__enter__.return_value = mock_resp
                grok.search("test query")
                mock_keychain.assert_called_once()
                called_request = mock_urlopen.call_args[0][0]
                assert called_request.headers["Authorization"] == "Bearer keychain-key"


def test_search_exits_when_no_api_key():
    """Test search exits with error when no API key available."""
    with patch.dict(_grok_dict["os"].environ, {}, clear=True):
        with patch.dict(_grok_dict, {"_keychain": MagicMock(return_value=None)}):
            with pytest.raises(SystemExit) as exc_info:
                grok.search("test query")
            assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Test response parsing
# ---------------------------------------------------------------------------


def test_search_prints_raw_json_when_raw_flag():
    """Test search prints raw JSON when --raw is set."""
    response_data = {
        "output": [
            {"type": "message", "content": [{"type": "output_text", "text": "hello world"}]}
        ]
    }

    with patch.dict(_grok_dict["os"].environ, {"XAI_API_KEY": "test-key"}, clear=True):
        with patch.object(_grok_dict["urllib"].request, "urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(response_data).encode()
            mock_urlopen.return_value.__enter__.return_value = mock_resp
            with patch("builtins.print") as mock_print:
                grok.search("test query", raw=True)
                # Should have printed the formatted JSON
                printed_calls = [call[0][0] for call in mock_print.call_args_list]
                assert any("hello world" in (str(c) if c else "") for c in printed_calls)


def test_search_extracts_text_from_output():
    """Test search extracts and prints text from response."""
    response_data = {
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "output_text", "text": "first part"},
                    {"type": "output_text", "text": " second part"},
                ],
            }
        ]
    }

    with patch.dict(_grok_dict["os"].environ, {"XAI_API_KEY": "test-key"}, clear=True):
        with patch.object(_grok_dict["urllib"].request, "urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.read.return_value = json.dumps(response_data).encode()
            mock_urlopen.return_value.__enter__.return_value = mock_resp
            with patch("builtins.print") as mock_print:
                grok.search("test query")
                printed_calls = [str(call[0][0]) for call in mock_print.call_args_list]
                assert "first part second part" in printed_calls


# ---------------------------------------------------------------------------
# Test error handling
# ---------------------------------------------------------------------------


def test_search_handles_http_error():
    """Test search handles HTTP errors gracefully."""
    with patch.dict(_grok_dict["os"].environ, {"XAI_API_KEY": "test-key"}, clear=True):
        mock_http_error = urllib.error.HTTPError(
            "url", 401, "unauthorized", None, MagicMock(read=lambda: b"unauthorized")
        )
        with patch.object(_grok_dict["urllib"].request, "urlopen", side_effect=mock_http_error):
            with pytest.raises(SystemExit) as exc_info:
                grok.search("test query")
            assert exc_info.value.code == 1


def test_search_handles_url_error():
    """Test search handles connection errors gracefully."""
    with patch.dict(_grok_dict["os"].environ, {"XAI_API_KEY": "test-key"}, clear=True):
        mock_error = MagicMock()
        mock_error.reason = "connection refused"
        with patch.object(
            _grok_dict["urllib"].request, "urlopen", side_effect=urllib.error.URLError(mock_error)
        ):
            with pytest.raises(SystemExit) as exc_info:
                grok.search("test query")
            assert exc_info.value.code == 1
