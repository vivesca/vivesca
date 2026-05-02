"""Tests for pinocytosis curl_cffi impersonation tier.

Covers: (a) CLI subcommand returns valid JSON, (b) profile flag changes UA, (c) auto-routing picks impersonate when configured.
"""

from __future__ import annotations

import json
import subprocess
import sys


def _run_pinocytosis(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "/home/vivesca/germline/effectors/pinocytosis", *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_impersonate_cli_returns_valid_json():
    """impersonate subcommand on httpbin returns parseable JSON with expected fields."""
    r = _run_pinocytosis("impersonate", "https://httpbin.org/get", "--json")
    assert r.returncode == 0, f"exit={r.returncode} stderr={r.stderr}"
    data = json.loads(r.stdout)
    assert data["success"] is True
    assert data["method"] == "impersonate"
    assert data["wall_time"] > 0
    assert "text" in data and len(data["text"]) > 0
    assert data["url"] == "https://httpbin.org/get"


def test_impersonate_profile_changes_user_agent():
    """Different profiles produce different User-Agent strings in httpbin response."""
    r_chrome = _run_pinocytosis(
        "impersonate", "https://httpbin.org/get", "--json", "--profile", "chrome120"
    )
    r_firefox = _run_pinocytosis(
        "impersonate", "https://httpbin.org/get", "--json", "--profile", "firefox133"
    )
    assert r_chrome.returncode == 0, f"chrome stderr={r_chrome.stderr}"
    assert r_firefox.returncode == 0, f"firefox stderr={r_firefox.stderr}"

    chrome_data = json.loads(r_chrome.stdout)
    firefox_data = json.loads(r_firefox.stdout)

    chrome_body = json.loads(chrome_data["text"])
    firefox_body = json.loads(firefox_data["text"])

    ua_chrome = chrome_body["headers"]["User-Agent"]
    ua_firefox = firefox_body["headers"]["User-Agent"]
    assert ua_chrome != ua_firefox, f"UA should differ: chrome={ua_chrome} firefox={ua_firefox}"
    assert "Chrome" in ua_chrome or "chrome" in ua_chrome.lower() or "chrom" in ua_chrome.lower()


def test_impersonate_in_auto_route():
    """Auto-route chain includes impersonate as a method option, exercised via --method flag."""
    r = _run_pinocytosis("--method", "impersonate", "--json", "https://httpbin.org/get")
    assert r.returncode == 0, f"exit={r.returncode} stderr={r.stderr}"
    data = json.loads(r.stdout)
    assert data["success"] is True
    assert data["method"] == "impersonate"
    assert "wall_time" in data
