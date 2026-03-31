from __future__ import annotations

"""Assays for porta — Chrome cookie bridge organelle and MCP tool.

Tests use mocked pycookiecheat and subprocess to avoid Chrome/Keychain/
agent-browser dependencies in CI.
"""


import sys
import types
from unittest.mock import patch

# Ensure pycookiecheat is importable even when not installed, so
# patch("pycookiecheat.chrome_cookies", ...) can resolve the target.
if "pycookiecheat" not in sys.modules:
    _fake = types.ModuleType("pycookiecheat")
    _fake.chrome_cookies = lambda url: {}  # type: ignore[attr-defined]
    sys.modules["pycookiecheat"] = _fake

# ---------------------------------------------------------------------------
# Organelle unit tests (metabolon.organelles.porta)
# ---------------------------------------------------------------------------


def test_inject_no_cookies_returns_failure():
    """Empty cookie dict → failure with localStorage hint."""
    with (
        patch("metabolon.organelles.porta._ab", return_value=(True, "")),
        patch("pycookiecheat.chrome_cookies", return_value={}),
    ):
        from metabolon.organelles.porta import inject

        result = inject("example.com")

    assert result["success"] is False
    assert result["count"] == 0
    assert "example.com" in result["message"]


def test_inject_happy_path():
    """Valid cookies → navigates and injects all, returns success."""
    cookies = {"session": "abc123", "csrf": "xyz"}

    def fake_ab(args, timeout=15):
        # open and eval both succeed
        return (True, "")

    with (
        patch("metabolon.organelles.porta._ab", side_effect=fake_ab),
        patch("pycookiecheat.chrome_cookies", return_value=cookies),
    ):
        from metabolon.organelles.porta import inject

        result = inject("bigmodel.cn")

    assert result["success"] is True
    assert result["count"] == 2
    assert "bigmodel.cn" in result["message"]


def test_inject_navigation_failure_both_methods():
    """Both nav methods fail → failure before any cookie injection."""
    nav_results = iter([(False, "open failed"), (False, "eval failed")])

    def fake_ab(args, timeout=15):
        if args[0] in ("open", "eval") and "window.location" in (args[1] if len(args) > 1 else ""):
            return next(nav_results, (False, "failed"))
        return next(nav_results, (False, "failed"))

    with (
        patch("metabolon.organelles.porta._ab", side_effect=fake_ab),
        patch("pycookiecheat.chrome_cookies", return_value={"session": "abc"}),
    ):
        from metabolon.organelles.porta import inject

        result = inject("example.com")

    assert result["success"] is False
    assert result["count"] == 0
    assert "navigate" in result["message"].lower()


def test_inject_strips_protocol():
    """https:// prefix should be stripped; URL sent to agent-browser is normalised."""
    captured_urls: list[str] = []

    def fake_ab(args, timeout=15):
        if args[0] == "open":
            captured_urls.append(args[1])
        return (True, "")

    with (
        patch("metabolon.organelles.porta._ab", side_effect=fake_ab),
        patch("pycookiecheat.chrome_cookies", return_value={"tok": "v"}),
    ):
        from metabolon.organelles.porta import inject

        inject("https://bigmodel.cn")

    assert len(captured_urls) >= 1
    assert captured_urls[0] == "https://bigmodel.cn"


def test_inject_pycookiecheat_missing():
    """ImportError on pycookiecheat → graceful failure message."""
    import sys

    # Remove cached module so our import inside inject() raises ImportError
    sys.modules.pop("pycookiecheat", None)

    import builtins

    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "pycookiecheat":
            raise ImportError("No module named 'pycookiecheat'")
        return real_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=mock_import):
        # Re-import inject so it sees the patched builtins
        import importlib

        import metabolon.organelles.porta as porta_mod

        importlib.reload(porta_mod)
        result = porta_mod.inject("example.com")

    # Restore fake module for subsequent tests
    if "pycookiecheat" not in sys.modules:
        _fake_restore = types.ModuleType("pycookiecheat")
        _fake_restore.chrome_cookies = lambda url: {}  # type: ignore[attr-defined]
        sys.modules["pycookiecheat"] = _fake_restore
    importlib.reload(porta_mod)

    assert result["success"] is False
    assert "pycookiecheat" in result["message"]


def test_inject_partial_failure():
    """If some cookie evals fail, success=True with partial count."""
    cookies = {"a": "1", "b": "2", "c": "3"}
    call_count = {"n": 0}

    def fake_ab(args, timeout=15):
        if args[0] == "open":
            return (True, "")
        # Fail every other eval call
        call_count["n"] += 1
        return (call_count["n"] % 2 != 0, "")

    with (
        patch("metabolon.organelles.porta._ab", side_effect=fake_ab),
        patch("pycookiecheat.chrome_cookies", return_value=cookies),
    ):
        from metabolon.organelles.porta import inject

        result = inject("example.com")

    # At least some injected (not all, since alternating failures)
    assert result["success"] is True
    assert 0 < result["count"] <= 3


def test_inject_chrome_exception():
    """Exception from pycookiecheat → structured failure, not a crash."""
    with patch("pycookiecheat.chrome_cookies", side_effect=Exception("Keychain locked")):
        from metabolon.organelles.porta import inject

        result = inject("example.com")

    assert result["success"] is False
    assert "Keychain" in result["message"] or "extraction failed" in result["message"]


# ---------------------------------------------------------------------------
# MCP tool layer (metabolon.enzymes.pseudopod)
# ---------------------------------------------------------------------------


def test_mcp_tool_wraps_organelle():
    """porta_inject tool delegates to organelle and maps to EffectorResult."""
    with patch(
        "metabolon.organelles.porta.inject",
        return_value={"success": True, "message": "Injected 3 cookies for test.com", "count": 3},
    ):
        from metabolon.enzymes.pseudopod import porta_inject

        result = porta_inject("test.com")

    assert result.success is True
    assert result.data["count"] == 3
    assert result.data["domain"] == "test.com"


def test_mcp_tool_failure_propagates():
    """Organelle failure maps to EffectorResult with success=False."""
    with patch(
        "metabolon.organelles.porta.inject",
        return_value={"success": False, "message": "No cookies found", "count": 0},
    ):
        from metabolon.enzymes.pseudopod import porta_inject

        result = porta_inject("nowhere.com")

    assert result.success is False
    assert result.data["count"] == 0
