from __future__ import annotations

"""Tests for effectors/cibus — Hong Kong restaurant finder (OpenRice)."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

CIBUS = Path.home() / "germline" / "effectors" / "cibus.py"


def _load_cibus():
    """Load the cibus effector by exec-ing its Python body."""
    source = CIBUS.read_text()
    ns: dict = {"__name__": "cibus_test"}
    exec(source, ns)
    return ns


_mod = _load_cibus()
resolve_id = _mod["resolve_id"]
current_hours = _mod["current_hours"]
format_table = _mod["format_table"]
list_options = _mod["list_options"]
fetch = _mod["fetch"]
CUISINES = _mod["CUISINES"]
DISTRICTS = _mod["DISTRICTS"]
PRICE_LABELS = _mod["PRICE_LABELS"]


# ── resolve_id tests ───────────────────────────────────────────────────────


class TestResolveId:
    """Tests for resolve_id fuzzy matching."""

    def test_exact_match(self):
        assert resolve_id("italian", CUISINES, "cuisine") == 3006

    def test_case_insensitive(self):
        assert resolve_id("Italian", CUISINES, "cuisine") == 3006
        assert resolve_id("ITALIAN", CUISINES, "cuisine") == 3006

    def test_chinese_name(self):
        assert resolve_id("意大利", CUISINES, "cuisine") == 3006

    def test_empty_string_returns_none(self):
        assert resolve_id("", CUISINES, "cuisine") is None

    def test_none_returns_none(self):
        """resolve_id(None, ...) returns None because 'not None' is True."""
        assert resolve_id(None, CUISINES, "cuisine") is None

    def test_district_exact_match(self):
        assert resolve_id("central", DISTRICTS, "district") == 1003

    def test_district_alias_tst(self):
        assert resolve_id("tst", DISTRICTS, "district") == 2008

    def test_substring_match_single(self):
        """Substring match returns id when exactly one match."""
        # "mong" is a substring of "mong kok" — single match
        result = resolve_id("mong", DISTRICTS, "district")
        assert result == 2010

    def test_unknown_returns_none(self, capsys):
        """Unknown name prints error and returns None."""
        result = resolve_id("zebra", CUISINES, "cuisine")
        assert result is None
        captured = capsys.readouterr()
        assert "Unknown cuisine" in captured.err

    def test_ambiguous_picks_first(self, capsys):
        """Ambiguous match picks first result and warns."""
        # "wan" matches "sheung wan" and "wan chai" — ambiguous
        result = resolve_id("wan", DISTRICTS, "district")
        assert result is not None
        captured = capsys.readouterr()
        assert "Ambiguous" in captured.err

    def test_whitespace_stripped(self):
        assert resolve_id("  italian  ", CUISINES, "cuisine") == 3006


# ── current_hours tests ────────────────────────────────────────────────────


class TestCurrentHours:
    """Tests for current_hours time extraction."""

    @pytest.fixture()
    def _fake_datetime(self):
        """Temporarily replace _mod['datetime'] with a fake returning a fixed Monday."""
        from datetime import datetime as real_dt

        monday = real_dt(2026, 3, 30, 12, 0)  # Monday (weekday 0 → OR dow 1)
        original = _mod["datetime"]

        class FakeDT:
            @staticmethod
            def now(tz=None):
                return monday

        _mod["datetime"] = FakeDT
        yield
        _mod["datetime"] = original

    def test_closed_today(self, _fake_datetime):
        poi = {"poiHours": [{"dayOfWeek": 1, "isClose": True}]}
        assert current_hours(poi) == "Closed"

    def test_24hr(self, _fake_datetime):
        poi = {"poiHours": [{"dayOfWeek": 1, "is24hr": True}]}
        assert current_hours(poi) == "24h"

    def test_normal_hours(self, _fake_datetime):
        poi = {"poiHours": [{"dayOfWeek": 1, "period1Start": "1100", "period1End": "2300"}]}
        assert current_hours(poi) == "1100-2300"

    def test_no_matching_day(self, _fake_datetime):
        poi = {"poiHours": [{"dayOfWeek": 3, "period1Start": "1100", "period1End": "2300"}]}
        assert current_hours(poi) == "—"

    def test_empty_hours_list(self):
        assert current_hours({"poiHours": []}) == "—"

    def test_no_poi_hours_key(self):
        assert current_hours({}) == "—"


# ── format_table tests ─────────────────────────────────────────────────────


class TestFormatTable:
    """Tests for format_table output formatting."""

    def test_empty_results(self):
        assert format_table([]) == "No results found."

    def test_single_result_has_headers(self):
        results = [
            {
                "name": "Test Restaurant",
                "categories": [{"name": "Italian", "categoryTypeId": 1}],
                "district": {"name": "Central"},
                "scoreOverall": 4.5,
                "scoreSmile": 10,
                "scoreCry": 1,
                "reviewCount": 50,
                "priceRangeId": 3,
                "phones": ["23456789"],
                "openNow": True,
                "poiHours": [],
                "shortenUrl": "https://example.com",
                "address": "123 Test St",
            }
        ]
        output = format_table(results)
        assert "Name" in output
        assert "Test Restaurant" in output
        assert "Italian" in output
        assert "Central" in output
        assert "4.5" in output

    def test_price_label_resolved(self):
        results = [
            {
                "name": "Cheap Eats",
                "categories": [],
                "district": {"name": "Mong Kok"},
                "scoreOverall": None,
                "scoreSmile": 0,
                "scoreCry": 0,
                "reviewCount": 0,
                "priceRangeId": 1,
                "phones": ["23456789"],
                "openNow": False,
                "poiHours": [],
                "shortenUrl": "",
                "address": "",
            }
        ]
        output = format_table(results)
        assert "<$50" in output

    def test_multiple_results_numbered(self):
        results = [
            {
                "name": f"R{i}",
                "categories": [],
                "district": {"name": "?"},
                "scoreOverall": None,
                "scoreSmile": 0,
                "scoreCry": 0,
                "reviewCount": 0,
                "priceRangeId": 0,
                "phones": ["00000000"],
                "openNow": False,
                "poiHours": [],
                "shortenUrl": "",
                "address": "",
            }
            for i in range(3)
        ]
        output = format_table(results)
        assert "[1]" in output
        assert "[2]" in output
        assert "[3]" in output


# ── list_options tests ─────────────────────────────────────────────────────


class TestListOptions:
    """Tests for list_options output."""

    def test_prints_cuisines_and_districts(self, capsys):
        list_options()
        captured = capsys.readouterr()
        assert "Cuisines:" in captured.out
        assert "Districts:" in captured.out
        assert "italian" in captured.out
        assert "central" in captured.out

    def test_no_chinese_chars_in_output(self, capsys):
        list_options()
        captured = capsys.readouterr()
        # English names only — Chinese filtered out
        for line in captured.out.splitlines():
            if (
                line.strip()
                and not line.startswith("Cuisines")
                and not line.startswith("Districts")
            ):
                assert all(ord(c) < 128 or c in " \t" for c in line), f"Non-ASCII in: {line}"


# ── CLI tests (subprocess) ─────────────────────────────────────────────────


class TestCli:
    """Integration tests via subprocess.run."""

    def test_help_flag(self):
        r = subprocess.run(
            [sys.executable, str(CIBUS), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 0
        assert "Hong Kong restaurant finder" in r.stdout

    def test_list_flag(self):
        r = subprocess.run(
            [sys.executable, str(CIBUS), "--list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode == 0
        assert "Cuisines:" in r.stdout
        assert "Districts:" in r.stdout

    def test_no_args_exits_error(self):
        r = subprocess.run(
            [sys.executable, str(CIBUS)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode != 0

    def test_unknown_cuisine_exits_error(self):
        r = subprocess.run(
            [sys.executable, str(CIBUS), "-c", "zebracuisine999"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert r.returncode != 0
        assert "Unknown cuisine" in r.stderr


# ── fetch tests (mocked network) ───────────────────────────────────────────


class TestFetch:
    """Tests for fetch with mocked urlopen."""

    def _make_fake_urlopen(self, body: bytes):
        """Build a fake urlopen that returns the given body bytes."""
        captured_url = {}

        def fake_urlopen(req, timeout=15):
            captured_url["url"] = req.full_url if hasattr(req, "full_url") else str(req)
            mock_resp = MagicMock()
            mock_resp.read.return_value = body
            mock_resp.__enter__ = lambda s: mock_resp
            mock_resp.__exit__ = MagicMock(return_value=False)
            return mock_resp

        return fake_urlopen, captured_url

    def test_fetch_builds_correct_url(self):
        body = json.dumps({"paginationResult": {"results": [{"name": "Sushi Place"}]}}).encode()
        fake, captured_url = self._make_fake_urlopen(body)

        original = _mod["urlopen"]
        _mod["urlopen"] = fake
        try:
            results = fetch(5, 3006, 1003, 3)
        finally:
            _mod["urlopen"] = original

        assert len(results) == 1
        assert results[0]["name"] == "Sushi Place"
        url = captured_url["url"]
        assert "cuisineId=3006" in url
        assert "districtId=1003" in url
        assert "priceRangeId=3" in url
        assert "rows=5" in url

    def test_fetch_no_optional_params(self):
        body = json.dumps({"paginationResult": {"results": []}}).encode()
        fake, captured_url = self._make_fake_urlopen(body)

        original = _mod["urlopen"]
        _mod["urlopen"] = fake
        try:
            results = fetch(10, None, None, None)
        finally:
            _mod["urlopen"] = original

        assert results == []
        url = captured_url["url"]
        assert "cuisineId" not in url
        assert "districtId" not in url
        assert "priceRangeId" not in url
        assert "rows=10" in url

    def test_fetch_html_response_exits(self):
        fake, _ = self._make_fake_urlopen(b"<html>captcha</html>")

        original = _mod["urlopen"]
        _mod["urlopen"] = fake
        try:
            with pytest.raises(SystemExit):
                fetch(5, None, None, None)
        finally:
            _mod["urlopen"] = original

    def test_fetch_invalid_json_exits(self):
        fake, _ = self._make_fake_urlopen(b"not json")

        original = _mod["urlopen"]
        _mod["urlopen"] = fake
        try:
            with pytest.raises(SystemExit):
                fetch(5, None, None, None)
        finally:
            _mod["urlopen"] = original


# ── PRICE_LABELS sanity ────────────────────────────────────────────────────


class TestPriceLabels:
    """Verify price label mapping."""

    def test_all_budget_choices_present(self):
        for i in range(1, 6):
            assert i in PRICE_LABELS

    def test_labels_are_strings(self):
        for v in PRICE_LABELS.values():
            assert isinstance(v, str)
            assert "$" in v
