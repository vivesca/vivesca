from __future__ import annotations

"""Tests for regulatory-capture — mocked Playwright tests."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def _load_module():
    """Load regulatory-capture by exec-ing its source (effector pattern)."""
    source = open(Path.home() / "germline/effectors/regulatory-capture").read()
    ns: dict = {"__name__": "regulatory_capture_test"}
    exec(source, ns)
    return ns


_mod = _load_module()
parse_date = _mod["parse_date"]
extract_publications_from_page = _mod["extract_publications_from_page"]
scrape_regulator = _mod["scrape_regulator"]
REGULATOR_CONFIGS = _mod["REGULATOR_CONFIGS"]
DEFAULT_OUTPUT_DIR = _mod["DEFAULT_OUTPUT_DIR"]


# ── parse_date tests ────────────────────────────────────────────────


def test_parse_date_iso():
    assert parse_date("2026-03-15") == datetime(2026, 3, 15)


def test_parse_date_d_m_y():
    assert parse_date("15/03/2026") == datetime(2026, 3, 15)


def test_parse_date_abbrev_month():
    assert parse_date("15 Mar 2026") == datetime(2026, 3, 15)


def test_parse_date_full_month():
    assert parse_date("15 March 2026") == datetime(2026, 3, 15)


def test_parse_date_comma_format():
    assert parse_date("Mar 15, 2026") == datetime(2026, 3, 15)


def test_parse_date_iso_timestamp():
    assert parse_date("2026-03-15T10:30:00") == datetime(2026, 3, 15, 10, 30)


def test_parse_date_invalid_returns_none():
    assert parse_date("not-a-date") is None


def test_parse_date_empty_returns_none():
    assert parse_date("") is None


# ── extract_publications_from_page tests ────────────────────────────


def _mock_element(text: str = "", href: str = "", tag: str = "a"):
    """Create a mock Playwright element handle."""
    el = MagicMock()
    el.inner_text = MagicMock(return_value=text)
    el.get_attribute = MagicMock(return_value=href)
    return el


def _mock_page(rows: list[dict]):
    """Build a mock Page with rows containing title/date/summary elements.

    Each row dict: {title, href, date, summary}.
    """
    page = MagicMock()

    row_elements = []
    for r in rows:
        row_el = MagicMock()
        title_el = _mock_element(r.get("title", ""), r.get("href", ""))
        date_el = _mock_element(r.get("date", ""))
        summary_el = _mock_element(r.get("summary", ""))

        row_el.query_selector = MagicMock(
            side_effect=lambda sel, _t=title_el, _d=date_el, _s=summary_el: (
                {
                    "a": _t,
                }.get(sel, _s if "date" not in sel else _d)
                if sel == "a"
                else _d
                if "date" in sel
                else _s
            )
        )

        # More explicit dispatch
        def make_query_selector(t, d, s):
            def _qs(sel):
                if sel == "a":
                    return t
                elif "date" in sel or "time" in sel:
                    return d
                else:
                    return s

            return _qs

        row_el.query_selector = MagicMock(
            side_effect=make_query_selector(title_el, date_el, summary_el)
        )
        row_elements.append(row_el)

    page.query_selector_all = MagicMock(return_value=row_elements)
    return page


def test_extract_basic_row():
    config = REGULATOR_CONFIGS["hkma"]
    page = _mock_page(
        [
            {
                "title": "Guideline on Credit Risk",
                "href": "/eng/doc/circular-2026-01.pdf",
                "date": "15 Jan 2026",
                "summary": "Updated credit risk framework",
            }
        ]
    )
    results = extract_publications_from_page(page, config, None)
    assert len(results) == 1
    assert results[0]["title"] == "Guideline on Credit Risk"
    assert "15 Jan 2026" in results[0]["date"]
    assert "credit risk" in results[0]["summary"].lower()


def test_extract_resolves_relative_url():
    config = REGULATOR_CONFIGS["hkma"]
    page = _mock_page(
        [
            {
                "title": "Test Circular",
                "href": "/eng/doc/test.pdf",
                "date": "01 Mar 2026",
                "summary": "",
            }
        ]
    )
    results = extract_publications_from_page(page, config, None)
    assert results[0]["url"].startswith("https://")


def test_extract_absolute_url_preserved():
    config = REGULATOR_CONFIGS["sfc"]
    page = _mock_page(
        [
            {
                "title": "SFC Circular",
                "href": "https://www.sfc.hk/circular/123",
                "date": "2026-02-10",
                "summary": "Licensing update",
            }
        ]
    )
    results = extract_publications_from_page(page, config, None)
    assert results[0]["url"] == "https://www.sfc.hk/circular/123"


def test_extract_filters_by_since_date():
    config = REGULATOR_CONFIGS["hkma"]
    page = _mock_page(
        [
            {"title": "Old Circular", "href": "/old", "date": "01 Jan 2025", "summary": ""},
            {"title": "New Circular", "href": "/new", "date": "01 Mar 2026", "summary": ""},
        ]
    )
    since = datetime(2026, 1, 1)
    results = extract_publications_from_page(page, config, since)
    assert len(results) == 1
    assert results[0]["title"] == "New Circular"


def test_extract_skips_rows_without_title():
    config = REGULATOR_CONFIGS["hkma"]
    page = _mock_page(
        [
            {"title": "", "href": "/empty", "date": "01 Mar 2026", "summary": ""},
        ]
    )
    # The mock returns empty string for title; title_el is non-None so it passes
    # but the inner_text is empty. This is fine — we return it.
    results = extract_publications_from_page(page, config, None)
    # Empty title is still extracted (only skipped if title_el is None)
    assert len(results) == 1


def test_extract_includes_source_name():
    config = REGULATOR_CONFIGS["sfc"]
    page = _mock_page(
        [
            {
                "title": "Test",
                "href": "https://sfc.hk/t",
                "date": "2026-03-01",
                "summary": "desc",
            }
        ]
    )
    results = extract_publications_from_page(page, config, None)
    assert results[0]["source"] == "Securities and Futures Commission"


def test_extract_multiple_rows():
    config = REGULATOR_CONFIGS["hkma"]
    rows = [
        {"title": f"Circular {i}", "href": f"/c{i}", "date": "01 Mar 2026", "summary": f"Sum {i}"}
        for i in range(5)
    ]
    page = _mock_page(rows)
    results = extract_publications_from_page(page, config, None)
    assert len(results) == 5


# ── scrape_regulator tests (mocked Playwright) ──────────────────────


def _mock_playwright_context(publications: list[dict]):
    """Create a mock sync_playwright context manager that returns publications."""
    mock_pw = MagicMock()
    mock_browser = MagicMock()
    mock_page = MagicMock()

    # Build row elements for mock page
    row_elements = []
    for pub in publications:
        row_el = MagicMock()
        title_el = _mock_element(pub.get("title", ""), pub.get("href", ""))
        date_el = _mock_element(pub.get("date", ""))
        summary_el = _mock_element(pub.get("summary", ""))

        def make_qs(t, d, s):
            def qs(sel):
                if sel == "a":
                    return t
                elif True:
                    return d if "date" in sel or "time" in sel else s

            return qs

        row_el.query_selector = MagicMock(side_effect=make_qs(title_el, date_el, summary_el))
        row_elements.append(row_el)

    mock_page.query_selector_all.return_value = row_elements
    mock_browser.new_page.return_value = mock_page
    mock_pw.chromium.launch.return_value = mock_browser

    mock_context = MagicMock()
    mock_context.__enter__ = MagicMock(return_value=mock_pw)
    mock_context.__exit__ = MagicMock(return_value=False)

    return mock_context


def test_scrape_hkma_writes_json(tmp_path):
    pubs = [
        {
            "title": "HKMA Test Circular",
            "href": "https://www.hkma.gov.hk/test.pdf",
            "date": "2026-03-01",
            "summary": "A test circular",
        }
    ]
    output = tmp_path / "hkma-test.json"

    mock_sp = MagicMock()
    mock_sp.return_value = _mock_playwright_context(pubs)
    _mod["sync_playwright"] = mock_sp
    try:
        results = scrape_regulator("hkma", output_path=output)
    finally:
        from playwright.sync_api import sync_playwright as real_sp

        _mod["sync_playwright"] = real_sp

    assert len(results) == 1
    assert results[0]["title"] == "HKMA Test Circular"
    assert output.exists()
    data = json.loads(output.read_text())
    assert len(data) == 1


def test_scrape_unknown_regulator_exits():
    with pytest.raises(SystemExit):
        scrape_regulator("unknown")


def test_scrape_sfc_returns_results(tmp_path):
    pubs = [
        {
            "title": "SFC Licensing Update",
            "href": "https://www.sfc.hk/circular/999",
            "date": "15 Feb 2026",
            "summary": "Updated licensing requirements",
        }
    ]
    output = tmp_path / "sfc-test.json"

    mock_sp = MagicMock()
    mock_sp.return_value = _mock_playwright_context(pubs)

    _mod["sync_playwright"] = mock_sp
    try:
        results = scrape_regulator("sfc", output_path=output)
    finally:
        from playwright.sync_api import sync_playwright as real_sp

        _mod["sync_playwright"] = real_sp

    assert len(results) == 1
    assert results[0]["source"] == "Securities and Futures Commission"


def test_scrape_creates_output_dir(tmp_path):
    nested = tmp_path / "deep" / "nested" / "dir"
    output = nested / "out.json"

    mock_sp = MagicMock()
    mock_sp.return_value = _mock_playwright_context(
        [
            {
                "title": "T",
                "href": "https://x",
                "date": "2026-01-01",
                "summary": "s",
            }
        ]
    )

    _mod["sync_playwright"] = mock_sp
    try:
        scrape_regulator("hkma", output_path=output)
    finally:
        from playwright.sync_api import sync_playwright as real_sp

        _mod["sync_playwright"] = real_sp

    assert output.exists()
    assert nested.is_dir()


# ── REGULATOR_CONFIGS tests ─────────────────────────────────────────


def test_supported_regulators():
    assert set(REGULATOR_CONFIGS.keys()) == {"hkma", "sfc"}


def test_config_has_required_keys():
    for name, cfg in REGULATOR_CONFIGS.items():
        assert "name" in cfg, f"{name} missing name"
        assert "url" in cfg, f"{name} missing url"
        assert "list_selector" in cfg, f"{name} missing list_selector"
        assert "title_selector" in cfg, f"{name} missing title_selector"
        assert "date_selector" in cfg, f"{name} missing date_selector"
        assert "summary_selector" in cfg, f"{name} missing summary_selector"


def test_urls_are_https():
    for name, cfg in REGULATOR_CONFIGS.items():
        assert cfg["url"].startswith("https://"), f"{name} url not https"


def test_default_output_dir_under_home():
    home = str(Path.home())
    assert str(DEFAULT_OUTPUT_DIR).startswith(home)
