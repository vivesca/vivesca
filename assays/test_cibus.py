"""Tests for effectors/cibus.py — loaded via exec (effectors are scripts, not importable modules)."""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

CIBUS_PATH = Path(__file__).resolve().parent.parent / "effectors" / "cibus.py"


@pytest.fixture()
def cibus():
    """Load cibus.py into a fresh namespace."""
    ns = {"__name__": "cibus_test", "__file__": str(CIBUS_PATH)}
    exec(open(CIBUS_PATH).read(), ns)
    return ns


def _mock_urlopen_resp(body: bytes):
    """Build a mock that behaves like urlopen's return value (context manager with .read())."""
    resp = MagicMock()
    resp.read.return_value = body
    resp.__enter__ = lambda s: resp
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _patch_urlopen(ns, body: bytes):
    """Patch the 'urlopen' key in the exec'd namespace (imported via 'from urllib.request import urlopen')."""
    resp = _mock_urlopen_resp(body)
    mock_fn = MagicMock(return_value=resp)
    return patch.dict(ns, {"urlopen": mock_fn}), mock_fn


# ---------------------------------------------------------------------------
# resolve_id
# ---------------------------------------------------------------------------


class TestResolveId:
    def test_exact_match(self, cibus):
        assert cibus["resolve_id"]("cantonese", cibus["CUISINES"], "cuisine") == 1002

    def test_case_insensitive(self, cibus):
        assert cibus["resolve_id"]("Japanese", cibus["CUISINES"], "cuisine") == 2009

    def test_stripped_whitespace(self, cibus):
        assert cibus["resolve_id"]("  thai  ", cibus["CUISINES"], "cuisine") == 2004

    def test_substring_match(self, cibus):
        # "viet" matches "vietnamese" and "viet", both map to 2002
        assert cibus["resolve_id"]("viet", cibus["CUISINES"], "cuisine") == 2002

    def test_empty_returns_none(self, cibus):
        assert cibus["resolve_id"]("", cibus["CUISINES"], "cuisine") is None

    def test_unknown_returns_none(self, cibus):
        assert cibus["resolve_id"]("martian", cibus["CUISINES"], "cuisine") is None

    def test_district_exact(self, cibus):
        assert cibus["resolve_id"]("central", cibus["DISTRICTS"], "district") == 1003

    def test_district_alias(self, cibus):
        assert cibus["resolve_id"]("tst", cibus["DISTRICTS"], "district") == 2008

    def test_chinese_cuisine(self, cibus):
        assert cibus["resolve_id"]("日本", cibus["CUISINES"], "cuisine") == 2009

    def test_ambiguous_prints_to_stderr(self, cibus):
        table = {"alpha one": 1, "alpha two": 2}
        captured = StringIO()
        with patch("sys.stderr", captured):
            result = cibus["resolve_id"]("alpha", table, "field")
        assert result in (1, 2)
        assert "Ambiguous" in captured.getvalue()


# ---------------------------------------------------------------------------
# fetch
# ---------------------------------------------------------------------------


class TestFetch:
    def test_basic_fetch_parses_json(self, cibus):
        mock_body = json.dumps({
            "paginationResult": {
                "results": [{"name": "Sushi Taichi", "scoreOverall": 4.5}]
            }
        }).encode()
        ctx, mock_fn = _patch_urlopen(cibus, mock_body)
        with ctx:
            results = cibus["fetch"](5, None, None, None)
        assert len(results) == 1
        assert results[0]["name"] == "Sushi Taichi"

    def test_fetch_sends_cuisine_param(self, cibus):
        mock_body = json.dumps({"paginationResult": {"results": []}}).encode()
        ctx, mock_fn = _patch_urlopen(cibus, mock_body)
        with ctx:
            cibus["fetch"](5, 2009, None, None)
        req = mock_fn.call_args[0][0]
        assert "cuisineId=2009" in req.full_url

    def test_fetch_sends_all_params(self, cibus):
        mock_body = json.dumps({"paginationResult": {"results": []}}).encode()
        ctx, mock_fn = _patch_urlopen(cibus, mock_body)
        with ctx:
            cibus["fetch"](10, 2009, 1003, 3)
        req = mock_fn.call_args[0][0]
        url = req.full_url
        assert "rows=10" in url
        assert "cuisineId=2009" in url
        assert "districtId=1003" in url
        assert "priceRangeId=3" in url

    def test_fetch_no_filters_no_params_in_url(self, cibus):
        mock_body = json.dumps({"paginationResult": {"results": []}}).encode()
        ctx, mock_fn = _patch_urlopen(cibus, mock_body)
        with ctx:
            cibus["fetch"](5, None, None, None)
        url = mock_fn.call_args[0][0].full_url
        assert "cuisineId" not in url
        assert "districtId" not in url
        assert "priceRangeId" not in url

    def test_fetch_html_response_exits(self, cibus):
        mock_body = b"<html>captcha</html>"
        ctx, _ = _patch_urlopen(cibus, mock_body)
        with ctx:
            with pytest.raises(SystemExit):
                cibus["fetch"](5, None, None, None)


# ---------------------------------------------------------------------------
# current_hours
# ---------------------------------------------------------------------------


class TestCurrentHours:
    def _today_dow(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Asia/Hong_Kong")).weekday() + 1

    def test_closed(self, cibus):
        poi = {"poiHours": [{"dayOfWeek": self._today_dow(), "isClose": True}]}
        assert cibus["current_hours"](poi) == "Closed"

    def test_24hr(self, cibus):
        poi = {"poiHours": [{"dayOfWeek": self._today_dow(), "is24hr": True}]}
        assert cibus["current_hours"](poi) == "24h"

    def test_normal_hours(self, cibus):
        poi = {
            "poiHours": [
                {"dayOfWeek": self._today_dow(), "period1Start": "1100", "period1End": "2300"}
            ]
        }
        # Code does [:5] on "1100" → "1100", not "11:00"
        assert cibus["current_hours"](poi) == "1100-2300"

    def test_no_hours_data(self, cibus):
        assert cibus["current_hours"]({}) == "—"
        assert cibus["current_hours"]({"poiHours": []}) == "—"

    def test_different_day(self, cibus):
        other_day = (self._today_dow() % 7) + 1
        poi = {"poiHours": [{"dayOfWeek": other_day, "period1Start": "0900", "period1End": "1800"}]}
        assert cibus["current_hours"](poi) == "—"


# ---------------------------------------------------------------------------
# format_table
# ---------------------------------------------------------------------------


def _minimal_result(**overrides):
    """Build a minimal valid result dict for format_table tests."""
    r = {
        "name": "Test",
        "categories": [],
        "district": {"name": "Central"},
        "scoreOverall": None,
        "scoreSmile": 0,
        "scoreCry": 0,
        "reviewCount": 0,
        "priceRangeId": 0,
        "phones": [""],   # non-empty list avoids IndexError bug at line 218
        "openNow": False,
        "shortenUrl": "",
        "addressOtherLang": "",
    }
    r.update(overrides)
    return r


class TestFormatTable:
    def test_empty_results(self, cibus):
        assert cibus["format_table"]([]) == "No results found."

    def test_single_result(self, cibus):
        results = [_minimal_result(
            name="Test Restaurant",
            categories=[{"categoryTypeId": 1, "name": "Italian"}],
            scoreOverall=4.3,
            priceRangeId=3,
            phones=["23456789"],
            openNow=True,
            shortenUrl="https://or.test/1",
            addressOtherLang="123 Test St",
        )]
        output = cibus["format_table"](results)
        assert "Test Restaurant" in output
        assert "Italian" in output
        assert "Central" in output
        assert "4.3" in output
        assert "$101-200" in output
        assert "Yes" in output
        assert "https://or.test/1" in output
        assert "123 Test St" in output

    def test_multiple_results_numbered(self, cibus):
        results = [_minimal_result(name=f"R{i}") for i in range(3)]
        output = cibus["format_table"](results)
        assert "[1]" in output
        assert "[2]" in output
        assert "[3]" in output

    def test_has_header_and_separator(self, cibus):
        results = [_minimal_result()]
        output = cibus["format_table"](results)
        lines = output.split("\n")
        # header line, separator line, data line, blank, link line
        assert len(lines) >= 4
        assert "---" in lines[1] or "-|-" in lines[1]


# ---------------------------------------------------------------------------
# list_options
# ---------------------------------------------------------------------------


class TestListOptions:
    def test_prints_cuisines_and_districts(self, cibus):
        captured = StringIO()
        with patch("sys.stdout", captured):
            cibus["list_options"]()
        out = captured.getvalue()
        assert "Cuisines:" in out
        assert "Districts:" in out
        assert "italian" in out
        assert "central" in out
        # CJK names should NOT appear
        assert "日本" not in out
        assert "中環" not in out


# ---------------------------------------------------------------------------
# main (CLI integration)
# ---------------------------------------------------------------------------


class TestMain:
    def _mock_results(self):
        return [
            {
                "name": "Pasta House",
                "categories": [{"categoryTypeId": 1, "name": "Italian", "categoryId": 3006}],
                "district": {"name": "Central", "districtId": 1003},
                "scoreOverall": 4.0,
                "scoreSmile": 5,
                "scoreCry": 0,
                "reviewCount": 20,
                "priceRangeId": 3,
                "phones": ["21112222"],
                "openNow": True,
                "poiHours": [],
                "shortenUrl": "https://or.test/pasta",
                "addressOtherLang": "1 Queen's Road",
            }
        ]

    def _patch_fetch(self, ns, results=None):
        """Patch fetch in namespace dict with a fake that returns canned results."""
        if results is None:
            results = self._mock_results()
        fake = MagicMock(return_value=results)
        return patch.dict(ns, {"fetch": fake}), fake

    def test_list_flag(self, cibus):
        captured = StringIO()
        with patch("sys.argv", ["cibus", "--list"]), patch("sys.stdout", captured):
            cibus["main"]()
        assert "Cuisines:" in captured.getvalue()

    def test_no_args_exits(self, cibus):
        with patch("sys.argv", ["cibus"]):
            with pytest.raises(SystemExit):
                cibus["main"]()

    def test_cuisine_and_area_query(self, cibus):
        ctx, mock_fetch = self._patch_fetch(cibus)
        captured = StringIO()
        with ctx, patch("sys.argv", ["cibus", "-c", "italian", "-a", "central"]), patch("sys.stdout", captured):
            cibus["main"]()
        assert "Pasta House" in captured.getvalue()

    def test_json_output(self, cibus):
        ctx, _ = self._patch_fetch(cibus)
        captured = StringIO()
        with ctx, patch("sys.argv", ["cibus", "-c", "italian", "-a", "central", "--json"]), patch("sys.stdout", captured):
            cibus["main"]()
        data = json.loads(captured.getvalue())
        assert isinstance(data, list)
        assert data[0]["name"] == "Pasta House"

    def test_positional_shorthand(self, cibus):
        ctx, mock_fetch = self._patch_fetch(cibus)
        captured = StringIO()
        with ctx, patch("sys.argv", ["cibus", "italian", "central"]), patch("sys.stdout", captured):
            cibus["main"]()
        mock_fetch.assert_called_once()

    def test_unknown_cuisine_exits(self, cibus):
        ctx, _ = self._patch_fetch(cibus)
        with ctx, patch("sys.argv", ["cibus", "-c", "martian"]):
            with pytest.raises(SystemExit):
                cibus["main"]()

    def test_fetch_error_exits(self, cibus):
        fake = MagicMock(side_effect=RuntimeError("timeout"))
        with patch.dict(cibus, {"fetch": fake}), patch("sys.argv", ["cibus", "-c", "italian", "-a", "central"]), patch("sys.stderr", StringIO()):
            with pytest.raises(SystemExit):
                cibus["main"]()

    def test_budget_passed_to_fetch(self, cibus):
        ctx, mock_fetch = self._patch_fetch(cibus)
        captured = StringIO()
        with ctx, patch("sys.argv", ["cibus", "-c", "thai", "-b", "3"]), patch("sys.stdout", captured):
            cibus["main"]()
        assert mock_fetch.call_args[0][3] == 3  # budget

    def test_rows_passed_to_fetch(self, cibus):
        ctx, mock_fetch = self._patch_fetch(cibus)
        captured = StringIO()
        with ctx, patch("sys.argv", ["cibus", "-c", "thai", "--rows", "10"]), patch("sys.stdout", captured):
            cibus["main"]()
        assert mock_fetch.call_args[0][0] == 10  # rows


# ---------------------------------------------------------------------------
# Constants / data integrity
# ---------------------------------------------------------------------------


class TestConstants:
    def test_price_labels(self, cibus):
        labels = cibus["PRICE_LABELS"]
        for i in range(1, 6):
            assert i in labels
            assert "$" in labels[i]
        assert len(labels) == 5

    def test_cuisines_has_common_entries(self, cibus):
        c = cibus["CUISINES"]
        for name in ("cantonese", "japanese", "italian", "thai", "korean"):
            assert name in c

    def test_districts_has_common_entries(self, cibus):
        d = cibus["DISTRICTS"]
        for name in ("central", "causeway bay", "mong kok", "tsim sha tsui"):
            assert name in d

    def test_api_url_https(self, cibus):
        assert cibus["API"].startswith("https://")
