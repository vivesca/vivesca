"""Tests for effectors/lacuna - Regulatory Gap Analysis CLI."""

import os
import re
from unittest.mock import patch, MagicMock, mock_open

import pytest
from typer.testing import CliRunner
import httpx

# Add the effectors directory to path so we can import lacuna
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'effectors'))

from lacuna import (
    app,
    _client,
    s,
    resolve,
    validate_doc_id,
    handle_request_error,
    BASE_URL,
    _UUID_RE,
    ALIASES,
    BASELINES,
    DISPLAY_NAMES,
)

runner = CliRunner()


# ─────────────────────────────────────────────────────────────────────────────
# Constant and regex tests
# ─────────────────────────────────────────────────────────────────────────────

def test_uuid_regex_matches_valid_uuids():
    """Test _UUID_RE matches valid UUIDs."""
    valid_uuids = [
        "f3db2d97-2201-4555-a81e-43a8721b2761",
        "F3DB2D97-2201-4555-A81E-43A8721B2761",
    ]
    for uuid in valid_uuids:
        assert _UUID_RE.match(uuid) is not None


def test_uuid_regex_rejects_invalid_uuids():
    """Test _UUID_RE rejects invalid UUIDs."""
    invalid_uuids = [
        "f3db2d97",
        "f3db2d97-2201-4555-a81e",
        "not-a-uuid",
        "demo-baseline",
    ]
    for uuid in invalid_uuids:
        assert _UUID_RE.match(uuid) is None


def test_aliases_all_resolve_to_valid_uuids():
    """Test all ALIASES entries resolve to valid UUIDs."""
    for alias, uuid_val in ALIASES.items():
        assert _UUID_RE.match(uuid_val) is not None


def test_baselines_are_valid_uuids():
    """Test all BASELINES are valid UUIDs."""
    for uuid_val in BASELINES:
        assert _UUID_RE.match(uuid_val) is not None


def test_display_names_cover_all_uuids():
    """Test all aliased and baseline UUIDs have display names."""
    for alias, uuid_val in ALIASES.items():
        assert uuid_val in DISPLAY_NAMES


# ─────────────────────────────────────────────────────────────────────────────
# Helper function tests
# ─────────────────────────────────────────────────────────────────────────────

def test_s_escapes_rich_markup():
    """Test s() escapes Rich markup."""
    assert s("[bold]test[/bold]") == r"\[bold\]test\[\/bold\]"
    assert s(None) == ""


def test_resolve_returns_alias_value():
    """Test resolve resolves aliases correctly."""
    assert resolve("demo-baseline") == ALIASES["demo-baseline"]
    assert resolve("unknown") == "unknown"
    assert resolve("  eu-ai-act  ") == ALIASES["eu-ai-act"]


def test_client_creates_client_with_api_key(monkeypatch):
    """Test _client creates client with correct headers when API key present."""
    monkeypatch.setenv("LACUNA_API_KEY", "test-key")
    
    client = _client()
    assert client.timeout == httpx.Timeout(45.0)
    assert client.headers["X-API-Key"] == "test-key"


def test_client_creates_client_without_api_key(monkeypatch):
    """Test _client creates client without headers when API key missing."""
    monkeypatch.delenv("LACUNA_API_KEY", raising=False)
    
    client = _client()
    assert "X-API-Key" not in client.headers


# ─────────────────────────────────────────────────────────────────────────────
# CLI tests with mocked HTTP
# ─────────────────────────────────────────────────────────────────────────────

def test_docs_command_success():
    """Test docs command succeeds with mocked API response."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "documents": [
            {
                "doc_id": "f3db2d97-2201-4555-a81e-43a8721b2761",
                "jurisdiction": "HK",
                "chunks_count": 120,
                "requirements": [{"id": 1}, {"id": 2}, {"id": 3}],
                "filename": "HKMA-GenAI-CP.pdf",
            }
        ]
    }
    
    with patch("lacuna._client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client_factory.return_value.__enter__.return_value = mock_client
        
        result = runner.invoke(app, ["docs"])
        assert result.exit_code == 0
        mock_client.get.assert_called_once_with(f"{BASE_URL}/documents")


def test_docs_command_handles_timeout():
    """Test docs command handles timeout correctly."""
    with patch("lacuna._client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.TimeoutException("Request timed out")
        mock_client_factory.return_value.__enter__.return_value = mock_client
        
        result = runner.invoke(app, ["docs"])
        assert result.exit_code == 1
        assert "Request timed out" in result.output


def test_docs_command_handles_connection_error():
    """Test docs command handles connection error correctly."""
    with patch("lacuna._client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        mock_client_factory.return_value.__enter__.return_value = mock_client
        
        result = runner.invoke(app, ["docs"])
        assert result.exit_code == 1
        assert "Connection failed" in result.output


def test_gap_command_invalid_circular_alias():
    """Test gap command exits with invalid circular document."""
    result = runner.invoke(app, ["gap", "--circular", "invalid", "--baseline", "demo-baseline"])
    assert result.exit_code == 1
    assert "Unknown circular" in result.output


def test_gap_command_invalid_baseline():
    """Test gap command exits with invalid baseline."""
    result = runner.invoke(app, ["gap", "--circular", "hkma-cp", "--baseline", "invalid"])
    assert result.exit_code == 1
    assert "Unknown baseline" in result.output


def test_gap_command_success():
    """Test gap command succeeds with valid inputs and good API response."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "status": "completed",
        "summary": {"full": 10, "partial": 5, "gap": 2},
        "findings": [
            {
                "status": "Gap",
                "description": "Missing transparency requirements for AI-generated content",
            },
            {
                "status": "Full",
                "description": "Risk assessment framework is complete",
            },
        ],
    }
    
    with patch("lacuna._client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_factory.return_value.__enter__.return_value = mock_client
        
        result = runner.invoke(app, ["gap", "--circular", "hkma-cp", "--baseline", "demo-baseline"])
        assert result.exit_code == 0
        assert "Gap Analysis" in result.output
        assert "Full: 10" in result.output
        assert "Partial: 5" in result.output
        assert "Gap: 2" in result.output


def test_gap_command_with_verbose_output():
    """Test gap command with verbose flag shows reasoning and provenance."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "status": "completed",
        "summary": {"full": 1, "partial": 0, "gap": 1},
        "findings": [
            {
                "status": "Gap",
                "description": "Missing documentation requirements",
                "reasoning": "The circular requires documentation but baseline doesn't mention it",
                "provenance": [
                    {"text_segment": "All AI systems must have documentation requirements"},
                ],
            },
        ],
    }
    
    with patch("lacuna._client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_factory.return_value.__enter__.return_value = mock_client
        
        result = runner.invoke(app, ["gap", "--circular", "hkma-cp", "--baseline", "demo-baseline", "--verbose"])
        assert result.exit_code == 0
        assert "Missing documentation requirements" in result.output
        assert "reasoning" in result.output


def test_query_command_success():
    """Test query command succeeds with mocked response."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "summary": "HKMA requires all GenAI systems to have risk assessments",
        "results": [
            {
                "metadata": {"filename": "HKMA-GenAI-CP.pdf"},
                "document": "All organizations deploying GenAI must conduct periodic risk assessments",
            },
        ],
    }
    
    with patch("lacuna._client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_factory.return_value.__enter__.return_value = mock_client
        
        result = runner.invoke(app, ["query", "What are the risk assessment requirements?", "--jurisdiction", "hk"])
        assert result.exit_code == 0
        assert "HKMA requires all GenAI systems" in result.output


def test_warmup_command_success():
    """Test warmup command succeeds with good response."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "summary": {"full": 15, "partial": 8, "gap": 3},
    }
    
    with patch("lacuna._client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_factory.return_value.__enter__.return_value = mock_client
        
        result = runner.invoke(app, ["warmup"])
        assert result.exit_code == 0
        assert "Cache is hot" in result.output
        assert "Full:15" in result.output


def test_warmup_command_fails_empty_summary():
    """Test warmup command fails with empty summary."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "summary": {},
    }
    
    with patch("lacuna._client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_factory.return_value.__enter__.return_value = mock_client
        
        result = runner.invoke(app, ["warmup"])
        assert result.exit_code == 1
        assert "Warmup failed" in result.output


def test_multi_gap_command_success():
    """Test multi_gap command succeeds with multiple successful responses."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "summary": {"full": 5, "partial": 2, "gap": 1},
    }
    
    with patch("lacuna._client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_factory.return_value.__enter__.return_value = mock_client
        
        result = runner.invoke(app, ["multi-gap", "--baseline", "demo-baseline", "--jurisdiction", "sg"])
        assert result.exit_code == 0
        assert "Multi-Gap Analysis" in result.output


def test_multi_gap_invalid_jurisdiction():
    """Test multi_gap exits with invalid jurisdiction."""
    result = runner.invoke(app, ["multi-gap", "--baseline", "demo-baseline", "--jurisdiction", "invalid"])
    assert result.exit_code == 1
    assert "Invalid jurisdiction" in result.output


def test_export_command_markdown_to_stdout():
    """Test export command outputs markdown to stdout."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "summary": {"full": 10, "partial": 5, "gap": 2},
        "findings": [
            {
                "status": "Gap",
                "description": "Missing transparency requirements",
                "reasoning": "The baseline policy doesn't address transparency requirements",
            },
        ],
    }
    
    with patch("lacuna._client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_factory.return_value.__enter__.return_value = mock_client
        
        result = runner.invoke(app, ["export", "--circular", "hkma-cp", "--baseline", "demo-baseline", "--format", "md"])
        assert result.exit_code == 0
        assert "# Gap Analysis Report" in result.output
        assert "## Summary" in result.output
        assert "## Findings" in result.output


def test_export_command_markdown_to_file():
    """Test export command writes markdown to file."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "summary": {"full": 10, "partial": 5, "gap": 2},
        "findings": [],
    }
    
    with patch("lacuna._client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_factory.return_value.__enter__.return_value = mock_client
        
        with patch("builtins.open", mock_open()) as mock_file:
            result = runner.invoke(
                app,
                ["export", "--circular", "hkma-cp", "--baseline", "demo-baseline", "--output", "report.md", "--format", "md"]
            )
            assert result.exit_code == 0
            mock_file.assert_called_once_with("report.md", "w")
            mock_file().write.assert_called_once()


def test_export_command_pdf_writes_bytes():
    """Test export command writes PDF bytes to file."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.content = b"%PDF-1.4 fake pdf content"
    
    with patch("lacuna._client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_factory.return_value.__enter__.return_value = mock_client
        
        with patch("builtins.open", mock_open()) as mock_file:
            result = runner.invoke(
                app,
                ["export", "--circular", "hkma-cp", "--baseline", "demo-baseline", "--output", "report.pdf", "--format", "pdf"]
            )
            assert result.exit_code == 0
            mock_file.assert_called_once_with("report.pdf", "wb")
            mock_file().write.assert_called_once_with(b"%PDF-1.4 fake pdf content")


def test_synthesize_command_success():
    """Test synthesize command succeeds with mocked response."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "jurisdictions": [
            {
                "circular_id": ALIASES["hkma-cp"],
                "jurisdiction": "Hong Kong",
                "summary": {"Full": 8, "Partial": 3, "Gap": 1},
            }
        ],
        "cross_jurisdiction_summary": "The baseline meets most requirements across jurisdictions with minor gaps.",
    }
    
    with patch("lacuna._client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_factory.return_value.__enter__.return_value = mock_client
        
        result = runner.invoke(
            app,
            ["synthesize", "--circulars", "hkma-cp", "--circulars", "hkma-gai", "--baseline", "demo-baseline"]
        )
        assert result.exit_code == 0
        assert "Cross-Jurisdiction Synthesis" in result.output
        assert "Cross-Jurisdiction Summary" in result.output


def test_preflight_command_all_checks_pass():
    """Test preflight command passes when all checks succeed."""
    mock_docs_response = MagicMock()
    mock_docs_response.raise_for_status.return_value = None
    mock_docs_response.json.return_value = {
        "documents": [{"doc_id": uuid} for uuid in DISPLAY_NAMES.keys()],
    }
    
    mock_gap_response = MagicMock()
    mock_gap_response.raise_for_status.return_value = None
    mock_gap_response.json.return_value = {
        "summary": {"full": 5, "partial": 2, "gap": 1},
    }
    
    mock_decompose_response = MagicMock()
    mock_decompose_response.raise_for_status.return_value = None
    mock_decompose_response.json.return_value = {
        "total": 42,
    }
    
    with patch("lacuna._client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.get.return_value = mock_docs_response
        mock_client.post.side_effect = [mock_gap_response, mock_decompose_response]
        mock_client_factory.return_value.__enter__.return_value = mock_client
        
        result = runner.invoke(app, ["preflight"])
        assert result.exit_code == 0
        assert "PASS" in result.output
        assert "API reachable" in result.output


def test_preflight_command_fails_when_api_unreachable():
    """Test preflight command fails when API is unreachable."""
    with patch("lacuna._client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        mock_client_factory.return_value.__enter__.return_value = mock_client
        
        result = runner.invoke(app, ["preflight"])
        assert result.exit_code == 1
        assert "FAIL" in result.output
        assert "Preflight failed — API unreachable" in result.output


def test_preflight_fails_when_documents_missing():
    """Test preflight fails when expected documents are missing."""
    mock_docs_response = MagicMock()
    mock_docs_response.raise_for_status.return_value = None
    mock_docs_response.json.return_value = {
        "documents": [],  # No documents found
    }
    
    with patch("lacuna._client") as mock_client_factory:
        mock_client = MagicMock()
        mock_client.get.return_value = mock_docs_response
        mock_client_factory.return_value.__enter__.return_value = mock_client
        
        result = runner.invoke(app, ["preflight"])
        assert result.exit_code == 1
        assert "FAIL" in result.output
        assert "documents present" in result.output


def test_upload_command_file_not_found():
    """Test upload command fails when file not found."""
    result = runner.invoke(app, ["upload", "--file", "nonexistent.pdf", "--name", "Test Document"])
    assert result.exit_code == 1
    assert "File not found" in result.output


def test_upload_command_unsupported_format():
    """Test upload command fails with unsupported format."""
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = True
        result = runner.invoke(app, ["upload", "--file", "document.exe", "--name", "Test"])
        assert result.exit_code == 1
        assert "Unsupported format" in result.output


# ─────────────────────────────────────────────────────────────────────────────
# Error handling tests
# ─────────────────────────────────────────────────────────────────────────────

def test_handle_request_error_timeout():
    """Test handle_request_error handles timeout exception."""
    with pytest.raises(SystemExit):
        with patch("lacuna.console.print"):
            handle_request_error(httpx.TimeoutException("timeout"))


def test_handle_request_error_http_status():
    """Test handle_request_error handles HTTP status error."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    err = httpx.HTTPStatusError("error", request=MagicMock(), response=mock_response)
    with pytest.raises(SystemExit):
        with patch("lacuna.console.print"):
            handle_request_error(err)


def test_handle_request_error_request_error():
    """Test handle_request_error handles request error."""
    err = httpx.RequestError("connection error", request=MagicMock())
    with pytest.raises(SystemExit):
        with patch("lacuna.console.print"):
            handle_request_error(err)


def test_validate_doc_id_passes_valid_uuid():
    """Test validate_doc_id accepts valid UUID through alias."""
    resolved = validate_doc_id("demo-baseline", "baseline")
    assert resolved == ALIASES["demo-baseline"]


def test_validate_doc_id_exits_on_invalid():
    """Test validate_doc_id exits on invalid doc ID."""
    with pytest.raises(SystemExit):
        with patch("lacuna.console.print"):
            validate_doc_id("invalid-id", "document")
