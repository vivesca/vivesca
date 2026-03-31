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
format_text = _mod["format_text"]
format_json = _mod["format_json"]
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


def test_parser_no_subcommand_returns_1():
    """Running with no subcommand prints help and returns 1."""
    rc = main([])
    assert rc == 1


# ── format_text / format_json tests ──────────────────────────────────


def test_format_text_basic():
    """format_text renders body plus metadata footer."""
    result = {"url": "https://x.com", "title": "X", "text": "Hello", "status": 200}
    out = format_text(result)
    assert "Hello" in out
    assert "title: X" in out
    assert "status: 200" in out


def test_format_text_empty_fields():
    """format_text omits metadata for empty/missing fields."""
    result = {"text": "Body only"}
    out = format_text(result)
    assert out.strip() == "Body only"
    assert "---" not in out


def test_format_json_produces_valid_json():
    """format_json returns valid JSON with expected keys."""
    result = {"url": "https://x.com", "title": "X", "text": "Hi", "status": 200}
    out = format_json(result)
    parsed = json.loads(out)
    assert parsed["url"] == "https://x.com"
    assert parsed["title"] == "X"


# ── fetch output tests (mocked) ──────────────────────────────────────


_FAKE_RESULT = {
    "url": "https://example.com",
    "title": "Example Domain",
    "text": "This domain is for use in illustrative examples.",
    "status": 200,
    "screenshot": None,
    "pdf": None,
}


@pytest.fixture()
def mock_fetch():
    """Replace fetch in the exec namespace with an AsyncMock; restore after."""
    original = _mod["fetch"]
    mock = AsyncMock(return_value=_FAKE_RESULT)
    _mod["fetch"] = mock
    yield mock
    _mod["fetch"] = original


def test_fetch_prints_text_by_default(mock_fetch, capsys):
    """Default output uses format_text (body + metadata footer)."""
    rc = main(["fetch", "https://example.com"])
    assert rc == 0
    captured = capsys.readouterr()
    assert _FAKE_RESULT["text"] in captured.out
    assert "title: Example Domain" in captured.out


def test_fetch_json_flag_outputs_json(mock_fetch, capsys):
    """--json flag outputs structured JSON via format_json."""
    rc = main(["fetch", "https://example.com", "--json"])
    assert rc == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["url"] == "https://example.com"
    assert parsed["status"] == 200
    assert parsed["title"] == "Example Domain"


def test_fetch_passes_all_options(mock_fetch, capsys):
    """All CLI options are forwarded to the fetch function."""
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


def test_fetch_file_not_found_raises(mock_fetch):
    """FileNotFoundError from fetch propagates."""
    mock_fetch.side_effect = FileNotFoundError("Cookie file not found: /nope")
    with pytest.raises(FileNotFoundError, match="Cookie file not found"):
        main(["fetch", "https://example.com", "--cookies", "/nope"])


def test_fetch_generic_exception_raises(mock_fetch):
    """Generic exceptions from fetch propagate."""
    mock_fetch.side_effect = RuntimeError("playwright blew up")
    with pytest.raises(RuntimeError, match="playwright blew up"):
        main(["fetch", "https://example.com"])


def test_fetch_defaults_pass_none(mock_fetch, capsys):
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
