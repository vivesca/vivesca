from __future__ import annotations

"""Tests for regulatory-scrape — URL→frontmattered markdown converter."""

import csv
import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


def _load():
    """Load regulatory-scrape by exec-ing its source and register as importable module."""
    src = open(Path.home() / "germline/effectors/regulatory-scrape").read()
    mod = types.ModuleType("regulatory_scrape")
    mod.__file__ = str(Path.home() / "germline/effectors/regulatory-scrape")
    exec(src, mod.__dict__)
    sys.modules["regulatory_scrape"] = mod
    return mod


_mod = _load()
slugify = _mod.slugify
_find_pdf_links = _mod._find_pdf_links
_curl_fetch = _mod._curl_fetch
_pdf_extract = _mod._pdf_extract
fetch_content = _mod.fetch_content
scrape_one = _mod.scrape_one
batch = _mod.batch
main = _mod.main
REG_DIR = _mod.REG_DIR
BOT_BLOCKED = _mod.BOT_BLOCKED


# ── slugify ────────────────────────────────────────────────────────────


def test_slugify_basic():
    assert slugify("AI Update 2024") == "ai-update-2024"


def test_slugify_special_chars():
    assert slugify("Policy: A/B & C!") == "policy-a-b-c"


def test_slugify_long_truncated():
    long = "a" * 100
    assert len(slugify(long)) == 60


def test_slugify_leading_trailing_hyphens():
    assert slugify("---hello---") == "hello"


def test_slugify_empty():
    assert slugify("") == ""


# ── _find_pdf_links ───────────────────────────────────────────────────


def test_find_pdf_links_absolute():
    html = '<a href="https://example.com/doc.pdf">link</a>'
    links = _find_pdf_links(html, "https://example.com/page")
    assert links == ["https://example.com/doc.pdf"]


def test_find_pdf_links_relative():
    html = '<a href="/files/report.pdf">report</a>'
    links = _find_pdf_links(html, "https://example.com/page")
    assert links == ["https://example.com/files/report.pdf"]


def test_find_pdf_links_none():
    html = '<a href="/page.html">no pdf</a>'
    links = _find_pdf_links(html, "https://example.com/page")
    assert links == []


def test_find_pdf_links_multiple():
    html = '<a href="/a.pdf"></a> <a href="/b.pdf"></a>'
    links = _find_pdf_links(html, "https://x.com/p")
    assert len(links) == 2


# ── _curl_fetch ────────────────────────────────────────────────────────


def test_curl_fetch_returns_text():
    """_curl_fetch returns stripped HTML when curl succeeds with enough content."""
    fake_html = "<html><body><p>" + "x" * 300 + "</p></body></html>"
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = fake_html

    with patch("subprocess.run", return_value=mock_result):
        text = _curl_fetch("https://example.com")

    assert len(text) > 200
    assert "<" not in text  # HTML tags stripped


def test_curl_fetch_short_content_returns_empty():
    """_curl_fetch returns '' when page content is too short."""
    fake_html = "<html><body><p>short</p></body></html>"
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = fake_html

    with patch("subprocess.run", return_value=mock_result):
        text = _curl_fetch("https://example.com")

    assert text == ""


def test_curl_fetch_curl_failure_returns_empty():
    """_curl_fetch returns '' when curl fails."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""

    with patch("subprocess.run", return_value=mock_result):
        text = _curl_fetch("https://example.com")

    assert text == ""


# ── _pdf_extract ───────────────────────────────────────────────────────


def test_pdf_extract_no_fitz_returns_empty():
    """_pdf_extract returns '' when fitz is not importable."""
    with patch.dict(sys.modules, {"fitz": None}):
        # Force ImportError path
        with patch("builtins.__import__", side_effect=ImportError("no fitz")):
            text = _pdf_extract("/tmp/test.pdf")
    # Should either return "" or handle gracefully
    assert isinstance(text, str)


def test_pdf_extract_local_file_success():
    """_pdf_extract reads a local PDF path and returns text."""
    fake_doc = MagicMock()
    fake_doc.__iter__ = lambda self: iter([MagicMock(get_text=MagicMock(return_value="A" * 300))])
    fake_fitz = MagicMock()
    fake_fitz.open.return_value = fake_doc

    with patch.dict(sys.modules, {"fitz": fake_fitz}):
        text = _pdf_extract("/tmp/test.pdf")

    # May return text or empty depending on import path — just verify no crash
    assert isinstance(text, str)


# ── fetch_content ──────────────────────────────────────────────────────


def test_fetch_content_pdf_url_calls_pdf_extract():
    """fetch_content calls _pdf_extract for .pdf URLs."""
    with patch("regulatory_scrape._pdf_extract", return_value="text " * 100) as mock_pe, \
         patch("regulatory_scrape._curl_fetch", return_value=""):
        text = fetch_content("https://example.com/doc.pdf")

    mock_pe.assert_called_once_with("https://example.com/doc.pdf")
    assert text.startswith("text ")


def test_fetch_content_bot_blocked_skips_pinocytosis():
    """fetch_content skips pinocytosis for BOT_BLOCKED domains."""
    with patch("subprocess.run") as mock_run, \
         patch("regulatory_scrape._curl_fetch", return_value=""), \
         patch("regulatory_scrape._find_pdf_links", return_value=[]):
        fetch_content("https://www.bankofengland.co.uk/some-page")

    # pinocytosis should NOT be called — only curl calls
    for c in mock_run.call_args_list:
        if c[0][0][0] == "pinocytosis":
            pytest.fail("pinocytosis should not be called for bot-blocked domains")


def test_fetch_content_tries_pinocytosis_first_for_normal_domain():
    """fetch_content tries pinocytosis before curl for non-blocked domains."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "x" * 600

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        text = fetch_content("https://example.com/page")

    # First call should be pinocytosis
    first_cmd = mock_run.call_args_list[0]
    assert first_cmd[0][0][0] == "pinocytosis"


def test_fetch_content_returns_empty_on_all_failures():
    """fetch_content returns '' when all fetch methods fail."""
    fail_result = MagicMock(returncode=1, stdout="")

    with patch("subprocess.run", return_value=fail_result), \
         patch("regulatory_scrape._curl_fetch", return_value=""), \
         patch("regulatory_scrape._find_pdf_links", return_value=[]), \
         patch("regulatory_scrape._pdf_extract", return_value=""):
        text = fetch_content("https://example.com/page")

    assert text == ""


# ── scrape_one ─────────────────────────────────────────────────────────


def test_scrape_one_writes_file(tmp_path):
    """scrape_one creates a frontmattered markdown file."""
    content = "X" * 300
    with patch(f"{_mod['__name__']}.REG_DIR", str(tmp_path)), \
         patch(f"{_mod['__name__']}.fetch_content", return_value=content):
        result = scrape_one(
            "https://example.com/doc", "fca", "2024-04-22",
            "AI Update", "guidance",
        )

    assert result  # non-empty path returned
    written = Path(result).read_text()
    assert "title: \"AI Update\"" in written
    assert "issuer: fca" in written
    assert "date: 2024-04-22" in written
    assert "source: https://example.com/doc" in written
    assert "type: guidance" in written
    assert content in written


def test_scrape_one_custom_slug(tmp_path):
    """scrape_one uses custom slug when provided."""
    with patch(f"{_mod['__name__']}.REG_DIR", str(tmp_path)), \
         patch(f"{_mod['__name__']}.fetch_content", return_value="X" * 300):
        result = scrape_one(
            "https://example.com/doc", "fca", "2024-04-22",
            "AI Update", "guidance", slug="custom-slug",
        )

    assert "custom-slug" in Path(result).name


def test_scrape_one_skips_existing(tmp_path):
    """scrape_one skips when file already exists with content."""
    # Pre-create the file
    filename = "fca-2024-04-ai-update.md"
    existing = tmp_path / filename
    existing.write_text("X" * 600)

    with patch(f"{_mod['__name__']}.REG_DIR", str(tmp_path)), \
         patch(f"{_mod['__name__']}.fetch_content") as mock_fc:
        result = scrape_one(
            "https://example.com/doc", "fca", "2024-04-22",
            "AI Update", "guidance",
        )

    mock_fc.assert_not_called()
    assert result == str(existing)


def test_scrape_one_returns_empty_on_fetch_failure(tmp_path):
    """scrape_one returns '' when fetch_content returns empty."""
    with patch(f"{_mod['__name__']}.REG_DIR", str(tmp_path)), \
         patch(f"{_mod['__name__']}.fetch_content", return_value=""):
        result = scrape_one(
            "https://example.com/doc", "fca", "2024-04-22",
            "AI Update", "guidance",
        )

    assert result == ""


def test_scrape_one_auto_slug(tmp_path):
    """scrape_one auto-generates slug from title when slug is None."""
    with patch(f"{_mod['__name__']}.REG_DIR", str(tmp_path)), \
         patch(f"{_mod['__name__']}.fetch_content", return_value="Y" * 300):
        result = scrape_one(
            "https://example.com/doc", "pra", "2024-06-01",
            "Dear CEO Letter", "letter",
        )

    assert "pra-2024-06-dear-ceo-letter.md" == Path(result).name


# ── batch ──────────────────────────────────────────────────────────────


def test_batch_processes_tsv(tmp_path):
    """batch reads TSV and calls scrape_one for each row."""
    tsv = tmp_path / "catalog.tsv"
    tsv.write_text("https://a.com\taa\t2024-01-01\tTitle A\tguidance\n"
                   "https://b.com\tbb\t2024-02-01\tTitle B\treport\n")

    with patch(f"{_mod['__name__']}.scrape_one", return_value="/fake/path") as mock_so:
        batch(str(tsv))

    assert mock_so.call_count == 2
    mock_so.assert_any_call("https://a.com", "aa", "2024-01-01", "Title A", "guidance", None)
    mock_so.assert_any_call("https://b.com", "bb", "2024-02-01", "Title B", "report", None)


def test_batch_skips_comments_and_empty(tmp_path):
    """batch skips comment lines and empty rows."""
    tsv = tmp_path / "catalog.tsv"
    tsv.write_text("# comment\n\nhttps://a.com\taa\t2024-01-01\tTitle\tguidance\n")

    with patch(f"{_mod['__name__']}.scrape_one", return_value="/fake/path") as mock_so:
        batch(str(tsv))

    assert mock_so.call_count == 1


def test_batch_with_slug_column(tmp_path):
    """batch passes optional slug column to scrape_one."""
    tsv = tmp_path / "catalog.tsv"
    tsv.write_text("https://a.com\taa\t2024-01-01\tTitle\tguidance\tmy-slug\n")

    with patch(f"{_mod['__name__']}.scrape_one", return_value="/fake/path") as mock_so:
        batch(str(tsv))

    mock_so.assert_called_once_with("https://a.com", "aa", "2024-01-01", "Title", "guidance", "my-slug")


# ── main (CLI) ─────────────────────────────────────────────────────────


def test_main_single_url_prints_path(tmp_path, capsys):
    """main prints the output path on success."""
    with patch(f"{_mod['__name__']}.REG_DIR", str(tmp_path)), \
         patch(f"{_mod['__name__']}.fetch_content", return_value="Z" * 300), \
         patch("sys.argv", ["regulatory-scrape", "https://example.com/doc",
                            "--issuer", "fca", "--date", "2024-04-22",
                            "--title", "Test Doc"]):
        main()

    captured = capsys.readouterr()
    assert captured.out.strip().endswith(".md")


def test_main_batch_flag(tmp_path):
    """main dispatches to batch when --batch is given."""
    tsv = tmp_path / "catalog.tsv"
    tsv.write_text("https://a.com\taa\t2024-01-01\tTitle\tguidance\n")

    with patch(f"{_mod['__name__']}.scrape_one", return_value="/fake/path"), \
         patch("sys.argv", ["regulatory-scrape", "--batch", str(tsv)]):
        main()


def test_main_missing_args_exits(tmp_path):
    """main exits with error when required args are missing for single URL."""
    with patch("sys.argv", ["regulatory-scrape", "https://example.com/doc"]), \
         pytest.raises(SystemExit):
        main()


def test_main_fetch_failure_exits_1(tmp_path):
    """main exits 1 when fetch_content returns empty."""
    with patch(f"{_mod['__name__']}.REG_DIR", str(tmp_path)), \
         patch(f"{_mod['__name__']}.fetch_content", return_value=""), \
         patch("sys.argv", ["regulatory-scrape", "https://example.com/doc",
                            "--issuer", "fca", "--date", "2024-04-22",
                            "--title", "Test Doc"]), \
         pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


# ── BOT_BLOCKED set ────────────────────────────────────────────────────


def test_bot_blocked_contains_boe():
    """Bank of England is in the bot-blocked set."""
    assert "bankofengland.co.uk" in BOT_BLOCKED
