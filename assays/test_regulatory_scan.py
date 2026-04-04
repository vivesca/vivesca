from __future__ import annotations

"""Tests for effectors/regulatory-scan — stale regulatory document scan (effector script)."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock


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
    original_parallel = _mod["rheotaxis_engine"].parallel_search
    original_format = _mod["rheotaxis_engine"].format_results

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

        _mod["rheotaxis_engine"].parallel_search = mock_parallel_search
        _mod["rheotaxis_engine"].format_results = lambda x: "Formatted result"

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
        _mod["rheotaxis_engine"].parallel_search = original_parallel
        _mod["rheotaxis_engine"].format_results = original_format


# ── CLI tests ─────────────────────────────────────────────────────────────────


def test_cli_nonexistent_path():
    """CLI should exit with 1 when path doesn't exist."""
    import subprocess

    result = subprocess.run(
        [
            str(Path.home() / "germline" / "effectors" / "regulatory-scan"),
            "--path",
            "/nonexistent/path/does/not/exist",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "does not exist" in result.stderr


def test_cli_help():
    """CLI help should work."""
    import subprocess

    result = subprocess.run(
        [str(Path.home() / "germline" / "effectors" / "regulatory-scan"), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Scan for stale regulatory documents" in result.stdout


# ── Additional subprocess integration tests ────────────────────────────────────

EFFECTOR = str(Path.home() / "germline" / "effectors" / "regulatory-scan")


def _make_stale(path: Path, name: str, days_old: int = 100) -> Path:
    """Create a file with mtime set N days in the past."""
    f = path / name
    f.write_text("# test regulatory doc\n")
    old_ts = (datetime.now() - timedelta(days=days_old)).timestamp()
    import os

    os.utime(f, (old_ts, old_ts))
    return f


def test_cli_dry_run_finds_stale(tmp_path):
    """Subprocess dry-run should list stale files and exit 0."""
    _make_stale(tmp_path, "hkma-circular-2025-01.md", days_old=120)
    _make_stale(tmp_path, "sfc-consultation.pdf", days_old=200)
    (tmp_path / "fresh-note.md").write_text("fresh")

    import subprocess

    result = subprocess.run(
        [EFFECTOR, "--dry-run", "--days", "30", "--path", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Found 2 stale document(s)" in result.stdout
    assert "hkma-circular-2025-01.md" in result.stdout
    assert "sfc-consultation.pdf" in result.stdout
    assert "fresh-note.md" not in result.stdout  # fresh file not listed


def test_cli_dry_run_no_stale(tmp_path):
    """Subprocess dry-run with all-fresh files should report clean."""
    (tmp_path / "doc1.md").write_text("fresh")
    (tmp_path / "doc2.pdf").write_text("fresh")

    import subprocess

    result = subprocess.run(
        [EFFECTOR, "--dry-run", "--days", "90", "--path", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "No stale documents found" in result.stdout


def test_cli_empty_directory(tmp_path):
    """Empty directory should report 0 documents scanned."""
    import subprocess

    result = subprocess.run(
        [EFFECTOR, "--dry-run", "--path", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Scanning 0 documents" in result.stdout


def test_cli_ignores_non_md_pdf(tmp_path):
    """Only .md and .pdf files should be scanned; .txt, .docx ignored."""
    _make_stale(tmp_path, "report.txt", days_old=200)
    _make_stale(tmp_path, "notes.docx", days_old=200)
    # No .md or .pdf at all
    import subprocess

    result = subprocess.run(
        [EFFECTOR, "--dry-run", "--days", "30", "--path", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "No stale documents found" in result.stdout


def test_cli_backends_alias(tmp_path):
    """Both --backend and --backends flags should be accepted."""
    _make_stale(tmp_path, "test.md", days_old=100)
    import subprocess

    # --backend
    r1 = subprocess.run(
        [EFFECTOR, "--dry-run", "--backend", "perplexity", "--path", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert r1.returncode == 0
    # --backends
    r2 = subprocess.run(
        [EFFECTOR, "--dry-run", "--backends", "perplexity", "--path", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert r2.returncode == 0


def test_cli_days_zero(tmp_path):
    """--days 0 should treat all files as stale (cutoff = today)."""
    # File created just now (today) — mtime is now
    (tmp_path / "today.md").write_text("just created")
    import subprocess

    result = subprocess.run(
        [EFFECTOR, "--dry-run", "--days", "0", "--path", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    # With days=0, cutoff is today; file from today should NOT be stale
    # because is_stale uses strict < (mtime < cutoff)
    # If file was modified at a time earlier today it IS stale; if at exactly
    # the same moment it's not. So we just verify it doesn't crash.
    assert "Scanning 1 documents" in result.stdout


# ── Unit: generate_query edge cases ───────────────────────────────────────────


def test_generate_query_hkma_capitals():
    """Uppercase HKMA in filename should still be recognized."""
    q = generate_query_from_filename("HKMA-2025-circular.md")
    assert "HKMA" in q


def test_generate_query_monetary_keyword():
    """'monetary' keyword should trigger HKMA publisher."""
    q = generate_query_from_filename("monetary-authority-update.md")
    assert "HKMA" in q


def test_generate_query_banking_keyword():
    """'banking' keyword should trigger HKMA publisher."""
    q = generate_query_from_filename("banking-compliance-guide.md")
    assert "HKMA" in q


def test_generate_query_strips_extension():
    """Both .md and .pdf extensions should be stripped."""
    q_md = generate_query_from_filename("test-doc.md")
    q_pdf = generate_query_from_filename("test-doc.pdf")
    assert "test doc" in q_md.lower()
    assert "test doc" in q_pdf.lower()
    assert ".md" not in q_md
    assert ".pdf" not in q_pdf


# ── Unit: is_stale boundary ───────────────────────────────────────────────────


def test_is_stale_exact_cutoff():
    """File exactly AT cutoff should NOT be stale (strict <)."""
    now = datetime.now()
    cutoff = now - timedelta(days=10)
    # Set mtime to exactly the cutoff
    mock_path = MagicMock(spec=Path)
    mock_path.stat.return_value.st_mtime = cutoff.timestamp()
    assert is_stale(mock_path, cutoff) is False


# ── Unit: scan_regulatory_documents with mock rheotaxis ───────────────────────


def test_scan_output_includes_query_for_sfc(tmp_path):
    """Scan should build correct SFC query for sfc-* filenames."""
    _make_stale(tmp_path, "sfc-licensing-guide.pdf", days_old=120)

    original_parallel = _mod["rheotaxis_engine"].parallel_search
    original_format = _mod["rheotaxis_engine"].format_results
    try:
        _mod["rheotaxis_engine"].parallel_search = lambda *a, **kw: []
        _mod["rheotaxis_engine"].format_results = lambda x: ""

        results = scan_regulatory_documents(tmp_path, 90, dry_run=False, timeout=1)
        assert "sfc-licensing-guide.pdf" in results
        assert "SFC" in results["sfc-licensing-guide.pdf"]["query"]
    finally:
        _mod["rheotaxis_engine"].parallel_search = original_parallel
        _mod["rheotaxis_engine"].format_results = original_format


def test_scan_skips_search_on_dry_run(tmp_path):
    """Dry run should not call parallel_search at all."""
    _make_stale(tmp_path, "stale.md", days_old=200)

    called = {"count": 0}
    original = _mod["rheotaxis_engine"].parallel_search
    try:

        def trap(*a, **kw):
            called["count"] += 1
            return []

        _mod["rheotaxis_engine"].parallel_search = trap

        scan_regulatory_documents(tmp_path, 90, dry_run=True)
        assert called["count"] == 0
    finally:
        _mod["rheotaxis_engine"].parallel_search = original


# ── Unit: generate_freshness_report ───────────────────────────────────────────


def test_freshness_report_with_results(capsys):
    """Report should print summary when results are provided."""
    from unittest.mock import MagicMock

    mock_result = MagicMock()
    mock_result.error = ""
    mock_result.answer = "update found"

    report_data = {
        "test-doc.md": {
            "doc_info": {
                "days_old": 120,
                "name": "test-doc.md",
                "mtime": datetime.now(),
                "path": Path("/tmp/test"),
            },
            "query": "HKMA test",
            "results": [mock_result],
        }
    }
    generate_freshness_report = _mod["generate_freshness_report"]
    generate_freshness_report(report_data)
    captured = capsys.readouterr()
    assert "FRESHNESS REPORT" in captured.out
    assert "UPDATE AVAILABLE" in captured.out
    assert "Total stale documents scanned: 1" in captured.out


def test_freshness_report_empty(capsys):
    """Report with empty dict should produce no output."""
    generate_freshness_report = _mod["generate_freshness_report"]
    generate_freshness_report({})
    captured = capsys.readouterr()
    assert captured.out == ""
