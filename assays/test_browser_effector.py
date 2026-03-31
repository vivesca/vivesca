"""Tests for effectors/browser — CLI wrapper around metabolon.organelles.browser."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

EFFECTOR_PATH = Path(__file__).parent.parent / "effectors" / "browser"


def _load_browser():
    """Load the browser effector by exec-ing its Python body."""
    source = EFFECTOR_PATH.read_text()
    ns: dict = {"__name__": "browser_effector"}
    exec(source, ns)
    return ns


_mod = _load_browser()
build_parser = _mod["build_parser"]
main = _mod["main"]


# ── parser tests ──────────────────────────────────────────────────────


def test_parser_fetch_subcommand():
    """Parser recognises 'fetch' subcommand with a URL."""
    parser = build_parser()
    args = parser.parse_args(["fetch", "https://example.com"])
    assert args.command == "fetch"
    assert args.url == "https://example.com"


def test_parser_all_options():
    """Parser wires every option to the correct attribute."""
    parser = build_parser()
    args = parser.parse_args([
        "fetch", "https://example.com",
        "--cookies", "/tmp/cookies.json",
        "--selector", "main",
        "--screenshot", "/tmp/shot.png",
        "--pdf", "/tmp/out.pdf",
        "--wait", "2000",
        "--json",
    ])
    assert args.cookies == "/tmp/cookies.json"
    assert args.selector == "main"
    assert args.screenshot == "/tmp/shot.png"
    assert args.pdf == "/tmp/out.pdf"
    assert args.wait == 2000
    assert args.json_output is True


def test_parser_defaults():
    """Parser supplies sensible defaults."""
    parser = build_parser()
    args = parser.parse_args(["fetch", "https://example.com"])
    assert args.cookies is None
    assert args.selector is None
    assert args.screenshot is None
    assert args.pdf is None
    assert args.wait == 0
    assert args.json_output is False


def test_parser_no_subcommand_exits():
    """Running with no subcommand prints help and exits 1."""
    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code == 1


def test_parser_unknown_subcommand_exits():
    """Unknown subcommand exits 1."""
    with pytest.raises(SystemExit) as exc_info:
        main(["bogus"])
    assert exc_info.value.code == 1


# ── fetch output tests (mocked) ──────────────────────────────────────

_FAKE_RESULT = {
    "title": "Example Domain",
    "url": "https://example.com",
    "text": "This domain is for use in illustrative examples.",
    "status": 200,
    "cookies_loaded": 0,
    "screenshot_saved": False,
    "pdf_saved": False,
}


@pytest.fixture()
def mock_fetch():
    """Replace _async_fetch in the exec namespace with an AsyncMock."""
    original = _mod["_async_fetch"]
    mock = AsyncMock(return_value=_FAKE_RESULT)
    _mod["_async_fetch"] = mock
    yield mock
    _mod["_async_fetch"] = original


def test_fetch_plain_text_output(mock_fetch, capsys):
    """Default output is result['text'] printed to stdout."""
    main(["fetch", "https://example.com"])
    captured = capsys.readouterr()
    assert captured.out.strip() == _FAKE_RESULT["text"]


def test_fetch_json_output(mock_fetch, capsys):
    """--json flag outputs structured JSON."""
    main(["fetch", "https://example.com", "--json"])
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["title"] == "Example Domain"
    assert parsed["status"] == 200
    assert parsed["url"] == "https://example.com"
    assert parsed["text"] == _FAKE_RESULT["text"]


def test_fetch_passes_all_options(mock_fetch, capsys):
    """All CLI options are forwarded to _async_fetch."""
    main([
        "fetch", "https://example.com",
        "--cookies", "/tmp/c.json",
        "--selector", "article",
        "--screenshot", "/tmp/s.png",
        "--pdf", "/tmp/o.pdf",
        "--wait", "3000",
    ])
    mock_fetch.assert_called_once_with(
        "https://example.com",
        cookies="/tmp/c.json",
        selector="article",
        screenshot="/tmp/s.png",
        pdf="/tmp/o.pdf",
        wait=3000,
    )


def test_fetch_defaults(mock_fetch, capsys):
    """When optional flags omitted, None/0 defaults are passed."""
    main(["fetch", "https://example.com"])
    mock_fetch.assert_called_once_with(
        "https://example.com",
        cookies=None,
        selector=None,
        screenshot=None,
        pdf=None,
        wait=0,
    )


def test_fetch_error_exits(mock_fetch, capsys):
    """Exceptions from fetch are printed to stderr and exit 1."""
    mock_fetch.side_effect = FileNotFoundError("Cookie file not found: /nope")
    with pytest.raises(SystemExit) as exc_info:
        main(["fetch", "https://example.com", "--cookies", "/nope"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Cookie file not found" in captured.err


def test_fetch_generic_error_exits(mock_fetch, capsys):
    """Generic exceptions are caught and reported on stderr."""
    mock_fetch.side_effect = RuntimeError("playwright blew up")
    with pytest.raises(SystemExit) as exc_info:
        main(["fetch", "https://example.com"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "playwright blew up" in captured.err
