"""Tests for regulatory-scan effector — scans stale regulatory documents."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_regulatory_scan():
    """Load the regulatory-scan module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/regulatory-scan").read()
    ns: dict = {"__name__": "regulatory_scan"}
    exec(source, ns)
    return ns


_mod = _load_regulatory_scan()
is_stale = _mod["is_stale"]
generate_query_from_filename = _mod["generate_query_from_filename"]
scan_regulatory_documents = _mod["scan_regulatory_documents"]
generate_freshness_report = _mod["generate_freshness_report"]
DEFAULT_STALE_DAYS = _mod["DEFAULT_STALE_DAYS"]


# ── is_stale tests ─────────────────────────────────────────────────────────


def test_is_stale_returns_true_for_old_file():
    """is_stale correctly identifies stale files older than cutoff."""
    cutoff = datetime.now() - timedelta(days=DEFAULT_STALE_DAYS)
    file = MagicMock(spec=Path)
    old_mtime = (cutoff - timedelta(days=1)).timestamp()
    file.stat.return_value.st_mtime = old_mtime
    assert is_stale(file, cutoff) is True


def test_is_stale_returns_false_for_fresh_file():
    """is_stale correctly identifies fresh files newer than cutoff."""
    cutoff = datetime.now() - timedelta(days=DEFAULT_STALE_DAYS)
    file = MagicMock(spec=Path)
    new_mtime = (cutoff + timedelta(days=1)).timestamp()
    file.stat.return_value.st_mtime = new_mtime
    assert is_stale(file, cutoff) is False


def test_is_stale_returns_false_for_exact_cutoff():
    """is_stale returns False for file exactly at cutoff (not older)."""
    cutoff = datetime.now() - timedelta(days=DEFAULT_STALE_DAYS)
    file = MagicMock(spec=Path)
    file.stat.return_value.st_mtime = cutoff.timestamp()
    assert is_stale(file, cutoff) is False


# ── generate_query_from_filename tests ─────────────────────────────────────


def test_generate_query_adds_hkma_for_hkma_in_name():
    """generate_query_from_filename includes HKMA publisher when filename has hkma."""
    filename = "hkma-circular-2025-01.md"
    query = generate_query_from_filename(filename)
    assert "HKMA" in query
    assert "latest update" in query
    assert "2026" in query
    assert "hkma circular" in query
    assert "regulatory document" not in query  # because publisher is present


def test_generate_query_adds_sfc_for_sfc_in_name():
    """generate_query_from_filename includes SFC publisher when filename has sfc."""
    filename = "sfc-code-of-conduct.pdf"
    query = generate_query_from_filename(filename)
    assert "SFC" in query
    assert "latest update" in query
    assert "sfc code of conduct" in query


def test_generate_query_no_publisher():
    """generate_query_from_filename works without recognized publisher."""
    filename = "ma-general-circular.md"
    query = generate_query_from_filename(filename)
    assert "latest update ma general circular" in query
    assert "regulatory document 2026" in query
    assert "HKMA" not in query
    assert "SFC" not in query


def test_generate_query_handles_hyphenated_filename():
    """generate_query_from_filename replaces hyphens with spaces correctly."""
    filename = "anti-money-laundering-guidelines.md"
    query = generate_query_from_filename(filename)
    assert "anti money laundering guidelines" in query


def test_generate_query_preserves_words_with_hkma_in_middle():
    """generate_query_from_filename detects HKMA even if not first word."""
    filename = "circular-hkma-2025.md"
    query = generate_query_from_filename(filename)
    assert "HKMA" in query


# ── scan_regulatory_documents tests ────────────────────────────────────────


def test_scan_regulatory_returns_empty_when_no_files(tmp_path):
    """scan_regulatory_documents returns empty dict when no files in path."""
    with patch("datetime.datetime") as mock_dt:
        mock_now = datetime(2026, 4, 1)
        mock_dt.now.return_value = mock_now
        result = scan_regulatory_documents(tmp_path, 90, dry_run=True)
        assert result == {}


def test_scan_regulatory_finds_stale_files(tmp_path):
    """scan_regulatory_documents correctly identifies stale files."""
    # Create test files
    stale_file = tmp_path / "stale-doc.md"
    stale_file.write_text("# Test\n")
    fresh_file = tmp_path / "fresh-doc.md"
    fresh_file.write_text("# Fresh\n")
    
    # Set mtimes: stale is 100 days ago, fresh 10 days ago
    stale_cutoff_days = 90
    now = datetime.now()
    stale_mtime = (now - timedelta(days=100)).timestamp()
    fresh_mtime = (now - timedelta(days=10)).timestamp()
    
    # Need to actually change the mtime
    import os
    os.utime(stale_file, (stale_mtime, stale_mtime))
    os.utime(fresh_file, (fresh_mtime, fresh_mtime))
    
    with patch("metabolon.organelles.rheotaxis_engine.parallel_search") as mock_search:
        mock_search.return_value = []
        result = scan_regulatory_documents(tmp_path, stale_cutoff_days, dry_run=False)
        assert len(result) == 1
        assert "stale-doc.md" in result
        assert result["stale-doc.md"]["doc_info"]["days_old"] >= 90


def test_scan_regulatory_includes_pdfs_and_mds(tmp_path):
    """scan_regulatory_documents scans both .md and .pdf files."""
    now = datetime.now()
    old_mtime = (now - timedelta(days=100)).timestamp()
    
    file1 = tmp_path / "doc1.md"
    file1.touch()
    import os
    os.utime(file1, (old_mtime, old_mtime))
    
    file2 = tmp_path / "doc2.pdf"
    file2.touch()
    os.utime(file2, (old_mtime, old_mtime))
    
    with patch("metabolon.organelles.rheotaxis_engine.parallel_search") as mock_search:
        mock_search.return_value = []
        result = scan_regulatory_documents(tmp_path, 90, dry_run=False)
        assert len(result) == 2
        assert "doc1.md" in result
        assert "doc2.pdf" in result


def test_scan_regulatory_calls_rheotaxis_with_correct_query(tmp_path):
    """scan_regulatory_documents calls rheotaxis with generated query."""
    now = datetime.now()
    old_mtime = (now - timedelta(days=100)).timestamp()
    
    hkma_file = tmp_path / "hkma-banking-requirements.md"
    hkma_file.touch()
    import os
    os.utime(hkma_file, (old_mtime, old_mtime))
    
    with patch("metabolon.organelles.rheotaxis_engine.parallel_search") as mock_search:
        mock_result = MagicMock()
        mock_result.error = False
        mock_result.answer = "Update found 2026"
        mock_result.backend = "test"
        mock_search.return_value = [mock_result]
        
        result = scan_regulatory_documents(tmp_path, 90, dry_run=False, backends="test")
        
        mock_search.assert_called_once()
        call_args = mock_search.call_args
        assert "HKMA" in call_args[0][0]
        assert call_args[1]["backends"] == ["test"]
        assert "hkma banking requirements" in call_args[0][0]
        assert result["hkma-banking-requirements.md"]["query"] == call_args[0][0]


def test_generate_freshness_report_prints_summary(capsys, tmp_path):
    """generate_freshness_report outputs correct summary statistics."""
    now = datetime.now()
    
    # Create mock results
    mock_result = {
        "doc1.md": {
            "doc_info": {
                "name": "doc1.md",
                "days_old": 100,
            },
            "results": [
                MagicMock(error=False, answer="New update available")
            ]
        },
        "doc2.pdf": {
            "doc_info": {
                "name": "doc2.pdf", 
                "days_old": 120,
            },
            "results": [
                MagicMock(error=True, answer=None)
            ]
        }
    }
    
    generate_freshness_report(mock_result)
    out = capsys.readouterr().out
    
    assert "FRESHNESS REPORT" in out
    assert "Total stale documents scanned: 2" in out
    assert "Documents with potential updates: 1" in out
    assert "doc1.md" in out
    assert "doc2.pdf" in out
    assert "UPDATE AVAILABLE" in out
    assert "NO UPDATES FOUND" in out


def test_generate_freshness_report_empty_result_no_output():
    """generate_freshness_report does nothing for empty results."""
    # Should not error, just return
    generate_freshness_report({})


# ── Integration test: subprocess invocation ──────────────────────────────────


def test_subprocess_help_flag():
    """Test that the script can be executed with --help."""
    import subprocess
    result = subprocess.run(
        ["/home/terry/germline/effectors/regulatory-scan", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Scan for stale regulatory documents" in result.stdout
    assert "--days" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--backend" in result.stdout


def test_subprocess_nonexistent_path_exits_with_error():
    """Test that the script exits with error when path doesn't exist."""
    import subprocess
    result = subprocess.run(
        ["/home/terry/germline/effectors/regulatory-scan", "--path", "/nonexistent/path/that/never/exists"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 1
    assert "does not exist" in result.stderr
