from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Load the effector script
GERMLINE = Path(__file__).parent.parent
GOLEM_REVIEW = GERMLINE / "effectors" / "golem-review"
exec(open(GOLEM_REVIEW).read(), globals())


def test_parse_since():
    assert parse_since("30s") == timedelta(seconds=30)
    assert parse_since("1h") == timedelta(hours=1)
    assert parse_since("2d") == timedelta(days=2)
    assert parse_since("45") == timedelta(minutes=45)
    assert parse_since("invalid") == timedelta(minutes=30)
    assert parse_since(None) == timedelta(minutes=30)


def test_parse_log_timestamp():
    assert parse_log_timestamp("2026-03-31 14:00:00") is not None
    assert parse_log_timestamp("invalid") is None
    assert parse_log_timestamp(None) is None


def test_check_consulting_content_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Temporarily set GERMLINE to tmpdir for testing
        with patch("__main__.GERMLINE", tmp_path):
            (tmp_path / "loci").mkdir(parents=True, exist_ok=True)
            result = check_consulting_content(["non_existent.md"])
            assert len(result) == 1
            assert result[0]["exists"] is False


def test_check_consulting_content_short():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        copia_dir = tmp_path / "loci" / "copia"
        copia_dir.mkdir(parents=True, exist_ok=True)
        short_file = copia_dir / "short.md"
        short_file.write_text("This is short.")
        
        with patch("__main__.GERMLINE", tmp_path):
            result = check_consulting_content(["loci/copia/short.md"])
            assert len(result) == 1
            assert result[0]["exists"] is True
            assert result[0]["word_count"] < 200
            assert result[0]["adequate"] is False


def test_check_consulting_content_good():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        copia_dir = tmp_path / "loci" / "copia"
        copia_dir.mkdir(parents=True, exist_ok=True)
        good_file = copia_dir / "good.md"
        content = """# Introduction

This is a test consulting document. It has multiple sections, headings, and paragraphs.
We want to make sure that it passes the quality checks. Let's add enough words to exceed 200.
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

## Analysis

Here are some key points:
- Point 1
- Point 2
- Point 3

## Conclusion

This concludes our test document. It has headings, paragraphs, structure elements, and plenty of words.
"""
        good_file.write_text(content)
        
        with patch("__main__.GERMLINE", tmp_path):
            result = check_consulting_content(["loci/copia/good.md"])
            assert len(result) == 1
            assert result[0]["exists"] is True
            assert result[0]["word_count"] > 200
            assert result[0]["adequate"] is True
            assert result[0]["has_headings"] is True
            assert result[0]["structure_ok"] is True
            assert result[0]["has_introduction"] is True
            assert result[0]["has_conclusion"] is True


def test_diagnose_failure():
    assert diagnose_failure("cmd", "ModuleNotFoundError") == "import_error"
    assert diagnose_failure("cmd", "SyntaxError") == "syntax_error"
    assert diagnose_failure("cmd", "/Users/terry/") == "path_issue"
    assert diagnose_failure("cmd", "timeout") == "timeout"
    assert diagnose_failure("cmd", "Permission denied") == "permission_error"
    assert diagnose_failure("cmd", "exit=2") == "command_error"
    assert diagnose_failure("cmd", "assert False") == "assertion_error"
    assert diagnose_failure("cmd", "unknown error") == "unknown"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
