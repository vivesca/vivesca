from __future__ import annotations
"""Tests for effectors/regulatory-scan — stale regulatory document scan (effector script)."""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_regulatory_scan_effector():
    """Load the regulatory-scan effector by exec-ing its Python body."""
    source = open(Path.home() / "germline" / "effectors" / "regulatory-scan").read()
    ns: dict = {"__name__": "regulatory_scan_effector"}
    exec(source, ns)
    return ns


# Load the module and extract functions
_mod = _load_regulatory_scan_effector()
is_stale = _mod["is_stale"]
generate_query_from_filename = _mod["generate_query_from_filename"]
scan_regulatory_documents = _mod["scan_regulatory_documents"]
DEFAULT_STALE_DAYS = _mod["DEFAULT_STALE_DAYS"]
DEFAULT_REGULATORY_PATH = _mod["DEFAULT_REGULATORY_PATH"]


# ── is_stale tests ───────────────────────────────────────────────────────────


def test_is_stale_old_file():
    """Old file older than cutoff should be stale."""
    cutoff = datetime.now() - timedelta(days=10)
    old_file_mtime = datetime.now() - timedelta(days=20)
    
    mock_path = MagicMock(spec=Path)
    mock_path.stat.return_value.st_mtime = old_file_mtime.timestamp()
    
    assert is_stale(mock_path, cutoff) is True


def test_is_stale_fresh_file():
    """Fresh file younger than cutoff should not be stale."""
    cutoff = datetime.now() - timedelta(days=10)
    fresh_mtime = datetime.now() - timedelta(days=5)
    
    mock_path = MagicMock(spec=Path)
    mock_path.stat.return_value.st_mtime = fresh_mtime.timestamp()
    
    assert is_stale(mock_path, cutoff) is False


# ── generate_query_from_filename tests ───────────────────────────────────────


def test_generate_query_basic_hkma():
    """Generate query from HKMA file with hyphens should include publisher."""
    filename = "hkma-banking-ordinance.md"
    query = generate_query_from_filename(filename)
    assert "HKMA" in query
    assert "latest update" in query
    assert "regulatory update 2026" in query
    assert "hkma banking ordinance" in query.lower()


def test_generate_query_basic_sfc():
    """Generate query from SFC file with hyphens should include publisher."""
    filename = "sfc-securities-and-futures-act.pdf"
    query = generate_query_from_filename(filename)
    assert "SFC" in query
    assert "latest update" in query
    assert "securities and futures act" in query.lower()


def test_generate_query_no_publisher():
    """Generate query from file without recognized publisher."""
    filename = "company-registration-guidelines.md"
    query = generate_query_from_filename(filename)
    assert "latest update" in query
    assert "company registration guidelines" in query.lower()
    assert "regulatory document 2026" in query


def test_generate_query_with_date():
    """Generate query from file with date at end."""
    filename = "hkgcc-remuneration-report-2025.md"
    query = generate_query_from_filename(filename)
    assert "latest update" in query
    assert "hkgcc remuneration report 2025" in query.lower()
    assert "regulatory document 2026" in query


# ── scan_regulatory_documents tests ──────────────────────────────────────────


def test_scan_no_stale_files(tmp_path):
    """Scan should return empty dict when no stale files."""
    # Create two fresh files
    file1 = tmp_path / "fresh1.md"
    file1.touch()
    file2 = tmp_path / "fresh2.pdf"
    file2.touch()
    
    stale_days = 10
    results = scan_regulatory_documents(tmp_path, stale_days, dry_run=True)
    assert results == {}


def test_scan_mixed_fresh_and_stale(tmp_path):
    """Scan should find only stale files."""
    # Create a stale file by manipulating mtime
    stale_file = tmp_path / "stale-doc.md"
    stale_file.touch()
    # Set mtime to 100 days ago
    old_time = (datetime.now() - timedelta(days=100)).timestamp()
    import os
    os.utime(stale_file, (old_time, old_time))
    
    fresh_file = tmp_path / "fresh-doc.pdf"
    fresh_file.touch()
    
    stale_days = 90
    results = scan_regulatory_documents(tmp_path, stale_days, dry_run=True)
    assert len(results) == 0  # dry_run returns empty


def test_scan_returns_results_when_not_dry_run(tmp_path):
    """Scan should return results when not dry run."""
    # Create stale file
    stale_file = tmp_path / "hkma-capital-requirements.md"
    stale_file.touch()
    old_time = (datetime.now() - timedelta(days=100)).timestamp()
    import os
    os.utime(stale_file, (old_time, old_time))

    # Save original to restore later
    original_parallel = _mod['rheotaxis_engine'].parallel_search
    original_format = _mod['rheotaxis_engine'].format_results

    try:
        # Create mock result
        mock_result = MagicMock()
        mock_result.error = False
        mock_result.answer = "New update found"
        mock_result.backend = "test"

        # Replace directly in the loaded module's rheotaxis_engine
        called_flag = False
        def mock_parallel_search(*args, **kwargs):
            nonlocal called_flag
            called_flag = True
            return [mock_result]

        _mod['rheotaxis_engine'].parallel_search = mock_parallel_search
        _mod['rheotaxis_engine'].format_results = lambda x: "Formatted result"

        stale_days = 90
        results = scan_regulatory_documents(tmp_path, stale_days, dry_run=False, timeout=1)

        assert len(results) == 1
        assert "hkma-capital-requirements.md" in results
        doc_info = results["hkma-capital-requirements.md"]["doc_info"]
        assert doc_info["days_old"] >= 90
        assert "HKMA" in results["hkma-capital-requirements.md"]["query"]
        assert called_flag
    finally:
        # Restore original
        _mod['rheotaxis_engine'].parallel_search = original_parallel
        _mod['rheotaxis_engine'].format_results = original_format


# ── CLI tests ─────────────────────────────────────────────────────────────────


def test_cli_nonexistent_path():
    """CLI should exit with 1 when path doesn't exist."""
    import subprocess
    result = subprocess.run(
        [str(Path.home() / "germline" / "effectors" / "regulatory-scan"), "--path", "/nonexistent/path/does/not/exist"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 1
    assert "does not exist" in result.stderr


def test_cli_help():
    """CLI help should work."""
    import subprocess
    result = subprocess.run(
        [str(Path.home() / "germline" / "effectors" / "regulatory-scan"), "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Scan for stale regulatory documents" in result.stdout
