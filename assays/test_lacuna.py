from __future__ import annotations
"""Tests for effectors/lacuna - Regulatory Gap Analysis CLI."""


import os
import re
from unittest.mock import patch, MagicMock, Mock

import httpx
import pytest
import typer

# Add the effectors directory to path so we can import lacuna
import sys
sys.path.insert(0, '/home/terry/germline/effectors')

# Import the module functions we need to test
import lacuna
from lacuna import (
    _client,
    s,
    resolve,
    validate_doc_id,
    handle_request_error,
    ALIASES,
    BASELINES,
    DISPLAY_NAMES,
    _UUID_RE,
    BASE_URL,
    TIMEOUT,
)


# ─────────────────────────────────────────────────────────────────────────────
# Constant and static data tests
# ─────────────────────────────────────────────────────────────────────────────

def test_alias_uuid_format():
    """Test all aliases resolve to valid UUID format."""
    for alias, uuid_val in ALIASES.items():
        assert _UUID_RE.match(uuid_val), f"Alias {alias} resolves to invalid UUID: {uuid_val}"


def test_baselines_are_valid_uuids():
    """Test all baseline entries are valid UUIDs that exist in display names."""
    for baseline in BASELINES:
        assert _UUID_RE.match(baseline), f"Baseline {baseline} is not a valid UUID"
        assert baseline in DISPLAY_NAMES, f"Baseline {baseline} missing from DISPLAY_NAMES"


def test_display_names_all_keys_uuids():
    """Test all keys in DISPLAY_NAMES are valid UUIDs."""
    for doc_id in DISPLAY_NAMES:
        assert _UUID_RE.match(doc_id), f"DISPLAY_NAMES key {doc_id} is not a valid UUID"


def test_uuid_regex_pattern():
    """Test UUID regex matches valid UUIDs and rejects invalid ones."""
    # Valid UUIDs
    valid_uuids = [
        "33432979-fcf8-4388-837c-4e51b82cfe2b",
        "de2b712a-bf43-4c33-b045-6bcfecef0d65",
        "00000000-0000-0000-0000-000000000000",
    ]
    for uuid_val in valid_uuids:
        assert _UUID_RE.match(uuid_val), f"Should match valid UUID: {uuid_val}"
    
    # Invalid UUIDs
    invalid_uuids = [
        "not-a-uuid",
        "demo-baseline",
        "33432979-fcf8-4388-837c",  # too short
        "33432979-fcf8-4388-837c-4e51b82cfe2bx",  # invalid character
        "g3432979-fcf8-4388-837c-4e51b82cfe2b",  # invalid first character
    ]
    for uuid_val in invalid_uuids:
        assert not _UUID_RE.match(uuid_val), f"Should not match invalid UUID: {uuid_val}"


def test_default_base_url_from_env():
    """Test BASE_URL defaults correctly when env var not set."""
    # The module already loaded, if LACUNA_API_URL wasn't set, should default to https://lacuna.sh
    expected = os.getenv("LACUNA_API_URL", "https://lacuna.sh")
    assert BASE_URL == expected


def test_timeout_value():
    """Test TIMEOUT is set to a reasonable value."""
    assert TIMEOUT.connect == 45.0
    assert TIMEOUT.read == 45.0
    assert TIMEOUT.write == 45.0


# ─────────────────────────────────────────────────────────────────────────────
# _client tests
# ─────────────────────────────────────────────────────────────────────────────

@patch.dict(os.environ, {}, clear=True)
def test_client_no_api_key():
    """Test client created without API key when env var not set."""
    client = _client()
    assert isinstance(client, httpx.Client)
    # No X-API-Key header when not provided
    assert "X-API-Key" not in client.headers
    client.close()


@patch.dict(os.environ, {"LACUNA_API_KEY": "test-api-key-123"}, clear=True)
def test_client_with_api_key():
    """Test client includes API key in headers when set via env var."""
    client = _client()
    assert client.headers["X-API-Key"] == "test-api-key-123"
    client.close()


def test_client_custom_timeout():
    """Test client accepts custom timeout."""
    custom_timeout = httpx.Timeout(10.0)
    client = _client(timeout=custom_timeout)
    assert client.timeout == custom_timeout
    client.close()


# ─────────────────────────────────────────────────────────────────────────────
# s (escape) function tests
# ─────────────────────────────────────────────────────────────────────────────

def test_s_escape_rich_markup():
    """Test Rich markup is escaped."""
    text = "[bold]Hello[/bold]"
    result = s(text)
    # Rich.escape adds backslashes before opening brackets
    assert "\\" in result
    assert "Hello" in result
    assert result != text  # Should be escaped


def test_s_empty_text():
    """Test empty text returns empty string."""
    assert s("") == ""
    assert s(None) == ""


def test_s_plain_text():
    """Test plain text unchanged except for string conversion."""
    result = s(123)
    assert result == "123"
    result = s("Hello World")
    assert result == "Hello World"


# ─────────────────────────────────────────────────────────────────────────────
# resolve function tests
# ─────────────────────────────────────────────────────────────────────────────

def test_resolve_alias():
    """Test known aliases resolve to their UUIDs."""
    assert resolve("demo-baseline") == ALIASES["demo-baseline"]
    assert resolve("hkma-cp") == ALIASES["hkma-cp"]
    assert resolve("eu-ai-act") == ALIASES["eu-ai-act"]


def test_resolve_uuid():
    """Test UUID strings return themselves unchanged."""
    uuid_val = "33432979-fcf8-4388-837c-4e51b82cfe2b"
    assert resolve(uuid_val) == uuid_val


def test_resolve_strips_whitespace():
    """Test whitespace is stripped from input."""
    assert resolve("  demo-baseline  ") == ALIASES["demo-baseline"]
    assert resolve("\n33432979-fcf8-4388-837c-4e51b82cfe2b\n") == "33432979-fcf8-4388-837c-4e51b82cfe2b"


def test_resolve_unknown():
    """Test unknown names return themselves unchanged."""
    assert resolve("unknown-alias") == "unknown-alias"


# ─────────────────────────────────────────────────────────────────────────────
# validate_doc_id tests
# ─────────────────────────────────────────────────────────────────────────────

def test_validate_valid_uuid():
    """Test valid UUID (after alias resolution) passes."""
    result = validate_doc_id("demo-baseline", "baseline")
    assert result == ALIASES["demo-baseline"]
    result = validate_doc_id("33432979-fcf8-4388-837c-4e51b82cfe2b", "circular")
    assert result == "33432979-fcf8-4388-837c-4e51b82cfe2b"


def test_validate_invalid_exits():
    """Test invalid doc ID exits with typer.Exit."""
    with pytest.raises((typer.Exit, SystemExit)):
        validate_doc_id("not-a-valid-uuid", "circular")


# ─────────────────────────────────────────────────────────────────────────────
# handle_request_error tests
# ─────────────────────────────────────────────────────────────────────────────

def test_handle_timeout_exception():
    """Test timeout exception handled correctly."""
    err = httpx.TimeoutException("Request timed out")
    with pytest.raises((typer.Exit, SystemExit)):
        handle_request_error(err)


def test_handle_http_status_error():
    """Test HTTP status error handled correctly."""
    response = Mock()
    response.status_code = 500
    err = httpx.HTTPStatusError("Error", request=Mock(), response=response)
    with pytest.raises((typer.Exit, SystemExit)):
        handle_request_error(err)


def test_handle_request_error():
    """Test connection error handled correctly."""
    err = httpx.RequestError("Connection failed", request=Mock())
    with pytest.raises((typer.Exit, SystemExit)):
        handle_request_error(err)


def test_handle_generic_exception():
    """Test generic exception handled correctly."""
    err = ValueError("Unexpected error")
    with pytest.raises((typer.Exit, SystemExit)):
        handle_request_error(err)


# ─────────────────────────────────────────────────────────────────────────────
# docs command tests
# ─────────────────────────────────────────────────────────────────────────────

@patch('lacuna._client')
def test_docs_success(mock_client_factory):
    """Test docs command with successful API response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "documents": [
            {
                "doc_id": "33432979-fcf8-4388-837c-4e51b82cfe2b",
                "jurisdiction": "Demo",
                "chunks_count": 100,
                "requirements": [{"id": 1}, {"id": 2}, {"id": 3}],
            }
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_client.get.return_value = mock_response
    mock_client_factory.return_value.__enter__.return_value = mock_client
    
    # Should not raise
    lacuna.docs()
    
    # Verify API called correctly
    mock_client.get.assert_called_once_with(f"{BASE_URL}/documents")


@patch('lacuna._client')
def test_docs_api_error_handled(mock_client_factory):
    """Test docs command handles API errors correctly."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.RequestError("Connection failed", request=Mock())
    mock_client_factory.return_value.__enter__.return_value = mock_client
    
    with pytest.raises((typer.Exit, SystemExit)):
        lacuna.docs()


# ─────────────────────────────────────────────────────────────────────────────
# gap command tests
# ─────────────────────────────────────────────────────────────────────────────

@patch('lacuna._client')
def test_gap_analysis_success(mock_client_factory):
    """Test gap analysis command with successful API response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "complete",
        "summary": {"full": 10, "partial": 5, "gap": 2},
        "findings": [
            {"status": "Full", "description": "All requirements covered"},
            {"status": "Gap", "description": "Missing consumer protection disclosure"},
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_client.post.return_value = mock_response
    mock_client_factory.return_value.__enter__.return_value = mock_client
    
    # Should not raise
    lacuna.gap(
        circular="hkma-cp",
        baseline="demo-baseline",
        verbose=False,
        amendments=False,
        interactive=False
    )
    
    # Verify API called with correct payload
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert call_args[0][0] == f"{BASE_URL}/gap-analysis"
    payload = call_args[1]["json"]
    assert payload["circular_doc_id"] == ALIASES["hkma-cp"]
    assert payload["baseline_id"] == ALIASES["demo-baseline"]
    assert payload["include_amendments"] is False
    assert payload["interactive"] is False


@patch('lacuna._client')
def test_gap_analysis_invalid_circular(mock_client_factory):
    """Test gap analysis exits on invalid circular ID."""
    with pytest.raises((typer.Exit, SystemExit)):
        lacuna.gap(
            circular="invalid-id",
            baseline="demo-baseline",
            verbose=False,
            amendments=False,
            interactive=False
        )
    # Should not have made any API calls
    mock_client_factory.assert_not_called()


@patch('lacuna._client')
def test_gap_analysis_invalid_baseline(mock_client_factory):
    """Test gap analysis exits on invalid baseline ID."""
    with pytest.raises((typer.Exit, SystemExit)):
        lacuna.gap(
            circular="hkma-cp",
            baseline="invalid-baseline",
            verbose=False,
            amendments=False,
            interactive=False
        )
    # Should not have made any API calls
    mock_client_factory.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# query command tests
# ─────────────────────────────────────────────────────────────────────────────

@patch('lacuna._client')
def test_query_success(mock_client_factory):
    """Test natural language query succeeds."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "summary": "GenAI governance requires risk management frameworks",
        "results": [
            {
                "document": "Relevant text segment from regulatory document",
                "metadata": {"filename": "hkma-genai.pdf"}
            }
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_client.post.return_value = mock_response
    mock_client_factory.return_value.__enter__.return_value = mock_client
    
    # Should not raise
    lacuna.query("What are the GenAI governance requirements?", jurisdiction=None)
    
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert call_args[0][0] == f"{BASE_URL}/query"
    payload = call_args[1]["json"]
    assert payload["query"] == "What are the GenAI governance requirements?"
    assert "jurisdiction" not in payload


@patch('lacuna._client')
def test_query_with_jurisdiction_filter(mock_client_factory):
    """Test query with jurisdiction filtering works."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"summary": "OK", "results": []}
    mock_response.raise_for_status.return_value = None
    mock_client.post.return_value = mock_response
    mock_client_factory.return_value.__enter__.return_value = mock_client
    
    lacuna.query("What are the requirements?", jurisdiction="hk")
    
    call_args = mock_client.post.call_args
    payload = call_args[1]["json"]
    assert payload["jurisdiction"] == "Hong Kong"
    
    # Test another jurisdiction
    mock_client.post.reset_mock()
    lacuna.query("What are the requirements?", jurisdiction="sg")
    call_args = mock_client.post.call_args
    payload = call_args[1]["json"]
    assert payload["jurisdiction"] == "Singapore"


# ─────────────────────────────────────────────────────────────────────────────
# warmup command tests
# ─────────────────────────────────────────────────────────────────────────────

@patch('lacuna._client')
def test_warmup_success(mock_client_factory):
    """Test warmup command succeeds with valid response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "summary": {"full": 5, "partial": 3, "gap": 1}
    }
    mock_response.raise_for_status.return_value = None
    mock_client.post.return_value = mock_response
    mock_client_factory.return_value.__enter__.return_value = mock_client
    
    # Should not raise
    lacuna.warmup()
    
    # Verify it uses the default demo pair
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    payload = call_args[1]["json"]
    assert payload["circular_doc_id"] == ALIASES["hkma-cp"]
    assert payload["baseline_id"] == ALIASES["demo-baseline"]


@patch('lacuna._client')
def test_warmup_empty_summary_fails(mock_client_factory):
    """Test warmup fails when backend returns empty summary."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"summary": {}}
    mock_response.raise_for_status.return_value = None
    mock_client.post.return_value = mock_response
    mock_client_factory.return_value.__enter__.return_value = mock_client
    
    with pytest.raises((typer.Exit, SystemExit)):
        lacuna.warmup()


# ─────────────────────────────────────────────────────────────────────────────
# upload command tests
# ─────────────────────────────────────────────────────────────────────────────

@patch('pathlib.Path.exists')
def test_upload_file_not_found(mock_exists):
    """Test upload exits when file not found."""
    mock_exists.return_value = False
    
    with pytest.raises((typer.Exit, SystemExit)):
        lacuna.upload(file="/nonexistent/file.pdf", name="Test Document", no_llm=False)


@patch('pathlib.Path.exists')
def test_upload_unsupported_format(mock_exists):
    """Test upload exits on unsupported file format."""
    mock_exists.return_value = True
    
    with patch('pathlib.Path.suffix', ".zip"):
        with pytest.raises((typer.Exit, SystemExit)):
            lacuna.upload(file="file.zip", name="Test", no_llm=False)


# ─────────────────────────────────────────────────────────────────────────────
# multi_gap command tests
# ─────────────────────────────────────────────────────────────────────────────

def test_multi_gap_invalid_jurisdiction():
    """Test multi_gap exits on invalid jurisdiction."""
    with pytest.raises((typer.Exit, SystemExit)):
        lacuna.multi_gap(baseline="demo-baseline", jurisdiction="invalid")


@patch('lacuna._client')
def test_multi_gap_all_jurisdictions(mock_client_factory):
    """Test multi_gap runs for all jurisdictions when jurisdiction='all'."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"summary": {"full": 10, "partial": 5, "gap": 2}}
    mock_response.raise_for_status.return_value = None
    mock_client.post.return_value = mock_response
    mock_client_factory.return_value.__enter__.return_value = mock_client
    
    # Should not raise (even if every request succeeds, it should render the table)
    lacuna.multi_gap(baseline="demo-baseline", jurisdiction="all")
    
    # Should have made multiple calls - one for each circular in all jurisdictions
    assert mock_client.post.call_count > 1


# ─────────────────────────────────────────────────────────────────────────────
# export command tests (Markdown export)
# ─────────────────────────────────────────────────────────────────────────────

@patch('lacuna._client')
@patch('builtins.open', new_callable=MagicMock)
def test_export_markdown_to_file(mock_open, mock_client_factory, tmp_path):
    """Test exporting gap analysis to Markdown file."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "summary": {"full": 10, "partial": 5, "gap": 2},
        "findings": [
            {"status": "Full", "description": "All good", "reasoning": "Everything covered"},
            {"status": "Gap", "description": "Missing requirement", "reasoning": "Not covered anywhere"},
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_client.post.return_value = mock_response
    mock_client_factory.return_value.__enter__.return_value = mock_client
    
    output_file = tmp_path / "report.md"
    lacuna.export(
        circular="hkma-cp",
        baseline="demo-baseline",
        output=str(output_file),
        format="md"
    )
    
    # Verify file was written
    mock_open.assert_called_once()


@patch('lacuna._client')
def test_export_pdf_handles_binary_response(mock_client_factory):
    """Test PDF export handles binary response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = b"%PDF-1.4 fake pdf content"
    mock_response.raise_for_status.return_value = None
    mock_client.post.return_value = mock_response
    mock_client_factory.return_value.__enter__.return_value = mock_client
    
    with patch('builtins.open', MagicMock()) as mock_open:
        lacuna.export(
            circular="hkma-cp",
            baseline="demo-baseline",
            output="/tmp/report.pdf",
            format="pdf"
        )
        mock_open.assert_called_once()
        # Verify content was written
        handle = mock_open.return_value.__enter__.return_value
        handle.write.assert_called_with(b"%PDF-1.4 fake pdf content")


# ─────────────────────────────────────────────────────────────────────────────
# preflight command tests
# ─────────────────────────────────────────────────────────────────────────────

@patch('lacuna._client')
def test_preflight_all_checks_pass(mock_client_factory):
    """Test preflight passes when all checks succeed."""
    mock_client = MagicMock()
    # First call: /documents
    docs_response = MagicMock()
    docs_response.json.return_value = {
        "documents": [{"doc_id": uid} for uid in ALIASES.values()]
    }
    docs_response.raise_for_status.return_value = None
    
    # Second call: gap-analysis warmup
    gap_response = MagicMock()
    gap_response.json.return_value = {"summary": {"full": 5, "partial": 3, "gap": 1}}
    gap_response.raise_for_status.return_value = None
    
    # Third call: decompose
    decompose_response = MagicMock()
    decompose_response.json.return_value = {"total": 42}
    decompose_response.raise_for_status.return_value = None
    
    mock_client.get.side_effect = [docs_response]
    mock_client.post.side_effect = [gap_response, decompose_response]
    mock_client_factory.return_value.__enter__.return_value = mock_client
    
    # Should pass (not raise)
    lacuna.preflight()
    
    # Verify all three endpoints were called
    mock_client.get.assert_called_once_with(f"{BASE_URL}/documents")
    assert mock_client.post.call_count == 2


@patch('lacuna._client')
def test_preflight_api_unreachable_fails(mock_client_factory):
    """Test preflight fails when API is unreachable."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.RequestError("Connection failed", request=Mock())
    mock_client_factory.return_value.__enter__.return_value = mock_client
    
    with pytest.raises((typer.Exit, SystemExit)):
        lacuna.preflight()


# ─────────────────────────────────────────────────────────────────────────────
# synthesize command tests
# ─────────────────────────────────────────────────────────────────────────────

def test_synthesize_invalid_circular_exits():
    """Test synthesize exits when any circular is invalid."""
    with pytest.raises((typer.Exit, SystemExit)):
        lacuna.synthesize(
            circulars=["hkma-cp", "invalid-circular"],
            baseline="demo-baseline",
            include_amendments=False
        )


def test_synthesize_invalid_baseline_exits():
    """Test synthesize exits when baseline is invalid."""
    with pytest.raises((typer.Exit, SystemExit)):
        lacuna.synthesize(
            circulars=["hkma-cp", "mas-mrmf"],
            baseline="invalid-baseline",
            include_amendments=False
        )


@patch('lacuna._client')
def test_synthesize_success(mock_client_factory):
    """Test cross-jurisdiction synthesis succeeds."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "jurisdictions": [
            {
                "circular_id": ALIASES["hkma-cp"],
                "jurisdiction": "Hong Kong",
                "summary": {"Full": 10, "Partial": 3, "Gap": 2}
            },
            {
                "circular_id": ALIASES["mas-mrmf"],
                "jurisdiction": "Singapore",
                "summary": {"Full": 8, "Partial": 4, "Gap": 1}
            }
        ],
        "cross_jurisdiction_summary": "This is a cross-jurisdictional summary of the gaps..."
    }
    mock_response.raise_for_status.return_value = None
    mock_client.post.return_value = mock_response
    mock_client_factory.return_value.__enter__.return_value = mock_client
    
    # Should not raise
    lacuna.synthesize(
        circulars=["hkma-cp", "mas-mrmf"],
        baseline="demo-baseline",
        include_amendments=True
    )
    
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert call_args[0][0] == f"{BASE_URL}/synthesis"
    payload = call_args[1]["json"]
    assert len(payload["circular_ids"]) == 2
    assert payload["baseline_id"] == ALIASES["demo-baseline"]
    assert payload["include_amendments"] is True


# ─────────────────────────────────────────────────────────────────────────────
# Edge cases
# ─────────────────────────────────────────────────────────────────────────────

def test_s_handles_none():
    """Test s() handles None correctly."""
    result = s(None)
    assert result == ""


def test_resolve_empty_string():
    """Test resolve handles empty string."""
    assert resolve("") == ""


def test_uuid_re_case_insensitive():
    """Test UUID regex is case-insensitive."""
    # Upper case UUID
    assert _UUID_RE.match("33432979-FCF8-4388-837C-4E51B82CFE2B")
