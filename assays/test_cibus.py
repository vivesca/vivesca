"""Tests for effectors/cibus.py — HK restaurant finder via OpenRice API.

Effectors are scripts, loaded via exec(). Mock external HTTP calls.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

CIBUS_PATH = Path(__file__).resolve().parent.parent / "effectors" / "cibus.py"


@pytest.fixture()
def cibus():
    """Load cibus.py into an isolated namespace (script, not importable module)."""
    ns = {
        "__name__": "cibus_test",
        "__file__": str(CIBUS_PATH),
    }
    exec(open(CIBUS_PATH).read(), ns)
    return ns


# ── resolve_id ────────────────────────────────────────────────


class TestResolveId:
    def _call(self, ns, name, table, label="test"):
        return ns["resolve_id"](name, table, label)

    def test_exact_match(self, cibus):
        table = {"foo": 10, "bar": 20}
        assert self._call(cibus, "foo", table) == 10

    def test_case_insensitive(self, cibus):
        table = {"hello": 42}
        assert self._call(cibus, "HELLO", table) == 42

    def test_strips_whitespace(self, cibus):
        table = {"hello": 42}
        assert self._call(cibus, "  hello  ", table) == 42

    def test_substring_match_unique(self, cibus):
        table = {"long name here": 7}
        assert self._call(cibus, "long name", table) == 7

    def test_empty_name_returns_none(self, cibus):
        assert self._call(cibus, "", {"a": 1}) is None

    def test_none_on_no_match(self, cibus):
        assert self._call(cibus, "zzz", {"a": 1}) is None

    def test_ambiguous_returns_first_match(self, cibus):
        table = {"alpha one": 1, "alpha two": 2}
        result = self._call(cibus, "alpha", table, "field")
        assert result is not None
        assert result in (1, 2)

    def test_ambiguous_prints_to_stderr(self, cibus, capsys):
        table = {"alpha one": 1, "alpha two": 2}
        self._call(cibus, "alpha", table, "field")
        captured = capsys.readouterr()
        assert "Ambiguous field" in captured.err

    def test_unknown_prints_to_stderr(self, cibus, capsys):
        table = {"foo": 1}
        self._call(cibus, "unknown", table, "cuisine")
        captured = capsys.readouterr()
        assert "Unknown cuisine" in captured.err

    def test_real_cuisine_lookup(self, cibus):
        assert self._call(cibus, "japanese", cibus["CUISINES"]) == 2009

    def test_real_district_lookup(self, cibus):
        assert self._call(cibus, "central", cibus["DISTRICTS"]) == 1003


# ── current_hours ─────────────────────────────────────────────


class TestCurrentHours:
    def _call(self, ns, poi):
        return ns["current_hours"](poi)

    def _today_dow(self):
        """Get today's day-of-week in OpenRice convention (1=Mon..7=Sun)."""
        from datetime import datetime
        from zoneinfo import ZoneInfo

        now = datetime.now(ZoneInfo("Asia/Hong_Kong"))
        return now.weekday() + 1

    def test_no_hours_returns_dash(self, cibus):
        assert self._call(cibus, {}) == "—"

    def test_empty_hours_list(self, cibus):
        assert self._call(cibus, {"poiHours": []}) == "—"

    def test_closed(self, cibus):
        dow = self._today_dow()
        poi = {"poiHours": [{"dayOfWeek": dow, "isClose": True}]}
        assert self._call(cibus, poi) == "Closed"

    def test_24hr(self, cibus):
        dow = self._today_dow()
        poi = {"poiHours": [{"dayOfWeek": dow, "is24hr": True}]}
        assert self._call(cibus, poi) == "24h"

    def test_open_range(self, cibus):
        dow = self._today_dow()
        poi = {
            "poiHours": [
                {
                    "dayOfWeek": dow,
                    "period1Start": "11:00",
                    "period1End": "23:00",
                }
            ]
        }
        assert self._call(cibus, poi) == "11:00-23:00"

    def test_open_range_no_colons(self, cibus):
        """API may return '1100' format; code takes [:5] which preserves both."""
        dow = self._today_dow()
        poi = {
            "poiHours": [
                {
                    "dayOfWeek": dow,
                    "period1Start": "1100",
                    "period1End": "2300",
                }
            ]
        }
        result = self._call(cibus, poi)
        # [:5] on "1100" gives "1100", on "11:00" gives "11:00"
        assert result == "1100-2300"

    def test_wrong_day_returns_dash(self, cibus):
        poi = {"poiHours": [{"dayOfWeek": 99, "period1Start": "1100", "period1End": "2300"}]}
        assert self._call(cibus, poi) == "—"


# ── format_table ──────────────────────────────────────────────


class TestFormatTable:
    def _call(self, ns, results):
        return ns["format_table"](results)

    def test_empty_results(self, cibus):
        assert self._call(cibus, []) == "No results found."

    def test_single_result(self, cibus):
        results = [
            {
                "name": "Test Restaurant",
                "categories": [{"name": "Italian", "categoryTypeId": 1, "categoryId": 3006}],
                "district": {"name": "Central", "districtId": 1003},
                "scoreOverall": 4.5,
                "scoreSmile": 100,
                "scoreCry": 5,
                "reviewCount": 200,
                "priceRangeId": 3,
                "phones": ["23456789"],
                "openNow": True,
                "shortenUrl": "https://or.test/1",
                "address": "123 Test St",
            }
        ]
        output = self._call(cibus, results)
        assert "Test Restaurant" in output
        assert "Italian" in output
        assert "Central" in output
        assert "4.5" in output
        assert "$101-200" in output
        assert "Yes" in output

    def test_no_score_shows_dash(self, cibus):
        results = [
            {
                "name": "No Score Place",
                "categories": [],
                "district": {"name": "Wan Chai"},
                "reviewCount": 0,
                "priceRangeId": 0,
                "phones": [],
            }
        ]
        output = self._call(cibus, results)
        # With no scoreOverall, the score column should be "—"
        assert "No Score Place" in output
        # The dash character appears in score, cuisine, and hours columns
        assert "—" in output

    def test_url_and_address_appended(self, cibus):
        results = [
            {
                "name": "X",
                "categories": [],
                "district": {"name": "Y"},
                "shortenUrl": "https://short.url/abc",
                "address": "1 Main St",
                "phones": ["98765432"],
                "reviewCount": 0,
                "priceRangeId": 0,
            }
        ]
        output = self._call(cibus, results)
        assert "https://short.url/abc" in output
        assert "1 Main St" in output
        assert "tel:98765432" in output

    def test_multiple_results_numbered(self, cibus):
        results = [
            {
                "name": f"R{i}",
                "categories": [],
                "district": {"name": "D"},
                "reviewCount": 0,
                "priceRangeId": 0,
            }
            for i in range(3)
        ]
        output = self._call(cibus, results)
        assert "[1]" in output
        assert "[2]" in output
        assert "[3]" in output


# ── fetch (mocked HTTP) ──────────────────────────────────────


class TestFetch:
    def _call(self, ns, rows, cuisine_id, district_id, budget):
        return ns["fetch"](rows, cuisine_id, district_id, budget)

    def _mock_urlopen(self, cibus, body_bytes):
        """Patch the urlopen that was imported into the cibus namespace."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = body_bytes
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        return patch.object(cibus, "urlopen", return_value=mock_resp)

    def test_basic_fetch(self, cibus):
        body = json.dumps({
            "paginationResult": {
                "results": [{"name": "Sushi Place", "district": {"name": "TST"}}]
            }
        }).encode()
        with self._mock_urlopen(cibus, body):
            results = self._call(cibus, 5, None, None, None)
        assert len(results) == 1
        assert results[0]["name"] == "Sushi Place"

    def test_fetch_with_cuisine_filter(self, cibus):
        body = json.dumps({"paginationResult": {"results": []}}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch.object(cibus, "urlopen", return_value=mock_resp) as mock_urlopen:
            self._call(cibus, 3, 2009, None, None)
            req = mock_urlopen.call_args[0][0]
            assert "cuisineId=2009" in req.full_url

    def test_fetch_with_budget(self, cibus):
        body = json.dumps({"paginationResult": {"results": []}}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch.object(cibus, "urlopen", return_value=mock_resp) as mock_urlopen:
            self._call(cibus, 5, None, None, 4)
            req = mock_urlopen.call_args[0][0]
            assert "priceRangeId=4" in req.full_url

    def test_fetch_with_district(self, cibus):
        body = json.dumps({"paginationResult": {"results": []}}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch.object(cibus, "urlopen", return_value=mock_resp) as mock_urlopen:
            self._call(cibus, 5, None, 1003, None)
            req = mock_urlopen.call_args[0][0]
            assert "districtId=1003" in req.full_url

    def test_fetch_html_response_exits(self, cibus):
        body = b"<html>rate limited</html>"
        mock_resp = MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch.object(cibus, "urlopen", return_value=mock_resp):
            with pytest.raises(SystemExit):
                self._call(cibus, 5, None, None, None)

    def test_fetch_no_filters(self, cibus):
        body = json.dumps({"paginationResult": {"results": []}}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = body
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch.object(cibus, "urlopen", return_value=mock_resp) as mock_urlopen:
            self._call(cibus, 5, None, None, None)
            req = mock_urlopen.call_args[0][0]
            # Should have rows and regionId but no cuisine/district/price
            assert "rows=5" in req.full_url
            assert "cuisineId" not in req.full_url


# ── list_options ──────────────────────────────────────────────


class TestListOptions:
    def test_prints_cuisines_and_districts(self, cibus, capsys):
        cibus["list_options"]()
        captured = capsys.readouterr()
        assert "Cuisines:" in captured.out
        assert "Districts:" in captured.out
        # Spot-check known values
        assert "japanese" in captured.out
        assert "central" in captured.out
        # CJK names should NOT appear (filtered by ord > 127 check)
        assert "日本" not in captured.out
        assert "中環" not in captured.out


# ── main (integration-level) ─────────────────────────────────


class TestMain:
    def _make_mock_results(self):
        return [
            {
                "name": "Ramen Shop",
                "categories": [{"name": "Japanese", "categoryTypeId": 1, "categoryId": 2009}],
                "district": {"name": "Causeway Bay", "districtId": 1019},
                "scoreOverall": 4.0,
                "scoreSmile": 50,
                "scoreCry": 2,
                "reviewCount": 80,
                "priceRangeId": 2,
                "phones": ["21112222"],
                "openNow": True,
                "shortenUrl": "https://or.test/ramen",
                "address": "1 CWB Rd",
            }
        ]

    def _patch_fetch(self, cibus, results=None):
        """Return a context manager that patches the fetch function in cibus ns."""
        if results is None:
            results = self._make_mock_results()

        def fake_fetch(rows, cuisine_id, district_id, budget):
            return results

        return patch.dict(cibus, {"fetch": fake_fetch})

    def test_list_flag(self, cibus, capsys):
        with patch.object(sys, "argv", ["cibus", "--list"]):
            cibus["main"]()
        captured = capsys.readouterr()
        assert "Cuisines:" in captured.out

    def test_cuisine_and_area_args(self, cibus, capsys):
        with self._patch_fetch(cibus):
            with patch.object(sys, "argv", ["cibus", "-c", "japanese", "-a", "central"]):
                cibus["main"]()
        captured = capsys.readouterr()
        assert "Ramen Shop" in captured.out

    def test_json_flag(self, cibus, capsys):
        with self._patch_fetch(cibus):
            with patch.object(sys, "argv", ["cibus", "-c", "japanese", "-a", "central", "--json"]):
                cibus["main"]()
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)

    def test_positional_shorthand(self, cibus, capsys):
        with self._patch_fetch(cibus) as pd:
            with patch.object(sys, "argv", ["cibus", "italian", "central"]):
                cibus["main"]()
        # Should have called fetch — just verify it didn't crash

    def test_no_args_exits_with_error(self, cibus):
        with patch.object(sys, "argv", ["cibus"]):
            with pytest.raises(SystemExit):
                cibus["main"]()

    def test_unknown_cuisine_exits(self, cibus):
        with self._patch_fetch(cibus):
            with patch.object(sys, "argv", ["cibus", "-c", "nonexistent"]):
                with pytest.raises(SystemExit):
                    cibus["main"]()

    def test_fetch_error_exits(self, cibus):
        def bad_fetch(*a, **kw):
            raise RuntimeError("timeout")

        with patch.dict(cibus, {"fetch": bad_fetch}):
            with patch.object(sys, "argv", ["cibus", "-c", "japanese", "-a", "central"]):
                with pytest.raises(SystemExit):
                    cibus["main"]()

    def test_budget_arg(self, cibus, capsys):
        fetch_calls = []

        def spy_fetch(rows, cuisine_id, district_id, budget):
            fetch_calls.append((rows, cuisine_id, district_id, budget))
            return self._make_mock_results()

        with patch.dict(cibus, {"fetch": spy_fetch}):
            with patch.object(sys, "argv", ["cibus", "-c", "thai", "-b", "3"]):
                cibus["main"]()

        assert fetch_calls[0][3] == 3  # budget=3

    def test_rows_arg(self, cibus, capsys):
        fetch_calls = []

        def spy_fetch(rows, cuisine_id, district_id, budget):
            fetch_calls.append((rows, cuisine_id, district_id, budget))
            return self._make_mock_results()

        with patch.dict(cibus, {"fetch": spy_fetch}):
            with patch.object(sys, "argv", ["cibus", "-c", "thai", "--rows", "10"]):
                cibus["main"]()

        assert fetch_calls[0][0] == 10  # rows=10

    def test_post_filter_by_cuisine(self, cibus, capsys):
        """Results not matching the requested cuisine_id should be filtered out."""
        mixed_results = [
            {
                "name": "Japanese Place",
                "categories": [{"name": "Japanese", "categoryTypeId": 1, "categoryId": 2009}],
                "district": {"name": "Central", "districtId": 1003},
                "reviewCount": 10,
                "priceRangeId": 2,
                "phones": [],
            },
            {
                "name": "Italian Place",
                "categories": [{"name": "Italian", "categoryTypeId": 1, "categoryId": 3006}],
                "district": {"name": "Central", "districtId": 1003},
                "reviewCount": 5,
                "priceRangeId": 3,
                "phones": [],
            },
        ]

        with self._patch_fetch(cibus, mixed_results):
            with patch.object(sys, "argv", ["cibus", "-c", "japanese", "-a", "central", "--json"]):
                cibus["main"]()
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 1
        assert data[0]["name"] == "Japanese Place"

    def test_post_filter_by_district(self, cibus, capsys):
        """Results not matching the requested district_id should be filtered out."""
        mixed_results = [
            {
                "name": "Central Place",
                "categories": [{"name": "Japanese", "categoryTypeId": 1, "categoryId": 2009}],
                "district": {"name": "Central", "districtId": 1003},
                "reviewCount": 10,
                "priceRangeId": 2,
                "phones": [],
            },
            {
                "name": "TST Place",
                "categories": [{"name": "Japanese", "categoryTypeId": 1, "categoryId": 2009}],
                "district": {"name": "TST", "districtId": 2008},
                "reviewCount": 5,
                "priceRangeId": 3,
                "phones": [],
            },
        ]

        with self._patch_fetch(cibus, mixed_results):
            with patch.object(sys, "argv", ["cibus", "-c", "japanese", "-a", "central", "--json"]):
                cibus["main"]()
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 1
        assert data[0]["name"] == "Central Place"


# ── Constants ─────────────────────────────────────────────────


class TestConstants:
    def test_price_labels_complete(self, cibus):
        labels = cibus["PRICE_LABELS"]
        assert labels[1] == "<$50"
        assert labels[5] == "$401-800"
        assert len(labels) == 5

    def test_cuisines_have_ids(self, cibus):
        cuisines = cibus["CUISINES"]
        assert isinstance(cuisines, dict)
        assert all(isinstance(v, int) for v in cuisines.values())
        assert "japanese" in cuisines
        assert "italian" in cuisines
        assert "cantonese" in cuisines

    def test_districts_have_ids(self, cibus):
        districts = cibus["DISTRICTS"]
        assert isinstance(districts, dict)
        assert all(isinstance(v, int) for v in districts.values())
        assert "central" in districts
        assert "tst" in districts

    def test_api_url(self, cibus):
        assert cibus["API"].startswith("https://www.openrice.com/api/")
