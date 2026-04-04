from __future__ import annotations

"""Tests for effectors/browser — CLI wrapper around metabolon.organelles.browser."""

import asyncio
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
    args = parser.parse_args(
        [
            "fetch",
            "https://example.com",
            "--cookies",
            "/tmp/cookies.json",
            "--selector",
            "main",
            "--screenshot",
            "/tmp/shot.png",
            "--pdf",
            "/tmp/out.pdf",
            "--wait",
            "2000",
            "--json",
        ]
    )
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
    main(
        [
            "fetch",
            "https://example.com",
            "--cookies",
            "/tmp/c.json",
            "--selector",
            "article",
            "--screenshot",
            "/tmp/s.png",
            "--pdf",
            "/tmp/o.pdf",
            "--wait",
            "3000",
        ]
    )
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


# ── format_output unit tests ───────────────────────────────────────────


def test_format_output_text():
    """format_output returns text field by default."""
    result = {"text": "Hello world", "title": "Test", "status": 200}
    output = _mod["format_output"](result)
    assert output == "Hello world"


def test_format_output_missing_text():
    """format_output returns empty string when text key missing."""
    result = {"title": "Test", "status": 200}
    output = _mod["format_output"](result)
    assert output == ""


def test_format_output_json():
    """format_output with as_json=True returns indented JSON."""
    result = {"text": "Hello", "title": "Test", "status": 200}
    output = _mod["format_output"](result, as_json=True)
    parsed = json.loads(output)
    assert parsed == result


def test_format_output_json_unicode():
    """format_output preserves unicode characters in JSON output."""
    result = {"text": "日本語テスト", "title": "中文标题"}
    output = _mod["format_output"](result, as_json=True)
    assert "日本語テスト" in output
    assert "中文标题" in output


# ── main return value tests ─────────────────────────────────────────────


def test_main_returns_zero_on_success(mock_fetch):
    """main() returns 0 (not via sys.exit) on successful fetch."""
    code = main(["fetch", "https://example.com"])
    assert code == 0


def test_main_unknown_command():
    """Unknown subcommand raises SystemExit with code 2 (argparse error)."""
    with pytest.raises(SystemExit) as exc_info:
        main(["unknown-command"])
    assert exc_info.value.code == 2


# ── additional edge case tests ───────────────────────────────────────────


def test_fetch_empty_result(mock_fetch, capsys):
    """Fetch returning empty dict outputs empty string."""
    mock_fetch.return_value = {}
    main(["fetch", "https://example.com"])
    captured = capsys.readouterr()
    assert captured.out == "\n"


def test_fetch_result_with_only_status(mock_fetch, capsys):
    """Fetch result without text field outputs empty string."""
    mock_fetch.return_value = {"status": 404, "url": "https://example.com"}
    main(["fetch", "https://example.com"])
    captured = capsys.readouterr()
    assert captured.out.strip() == ""


def test_fetch_json_with_all_fields(mock_fetch, capsys):
    """--json outputs all fields from result dict."""
    mock_fetch.return_value = {
        "title": "Test Page",
        "url": "https://test.com",
        "text": "Page content",
        "status": 200,
        "cookies_loaded": 5,
        "screenshot_saved": True,
        "pdf_saved": False,
        "headers": {"content-type": "text/html"},
    }
    main(["fetch", "https://test.com", "--json"])
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["cookies_loaded"] == 5
    assert parsed["screenshot_saved"] is True
    assert parsed["headers"]["content-type"] == "text/html"


def test_format_output_empty_dict():
    """format_output handles empty dict."""
    output = _mod["format_output"]({})
    assert output == ""


def test_format_output_json_empty():
    """format_output handles empty dict as JSON."""
    output = _mod["format_output"]({}, as_json=True)
    parsed = json.loads(output)
    assert parsed == {}


def test_format_output_json_special_chars():
    """format_output escapes special characters in JSON."""
    result = {"text": "Line1\nLine2\tTabbed", "quotes": '"quoted"'}
    output = _mod["format_output"](result, as_json=True)
    parsed = json.loads(output)
    assert parsed["text"] == "Line1\nLine2\tTabbed"
    assert parsed["quotes"] == '"quoted"'


# ── parser edge case tests ───────────────────────────────────────────────


def test_parser_missing_url():
    """Parser exits with error when URL is missing."""
    with pytest.raises(SystemExit) as exc_info:
        main(["fetch"])
    assert exc_info.value.code == 2


def test_parser_wait_non_integer():
    """Parser exits with error when --wait is not an integer."""
    with pytest.raises(SystemExit) as exc_info:
        main(["fetch", "https://example.com", "--wait", "abc"])
    assert exc_info.value.code == 2


def test_parser_wait_negative():
    """Parser accepts negative wait values (no validation in argparse)."""
    parser = build_parser()
    args = parser.parse_args(["fetch", "https://example.com", "--wait", "-100"])
    assert args.wait == -100


def test_parser_relative_path_cookies():
    """Parser accepts relative paths for --cookies."""
    parser = build_parser()
    args = parser.parse_args(["fetch", "https://example.com", "--cookies", "cookies.json"])
    assert args.cookies == "cookies.json"


def test_parser_url_without_scheme():
    """Parser accepts URL without scheme (validation happens in fetch)."""
    parser = build_parser()
    args = parser.parse_args(["fetch", "example.com"])
    assert args.url == "example.com"


# ── async fetch edge cases ─────────────────────────────────────────────


def test_fetch_timeout_error(mock_fetch, capsys):
    """TimeoutError from fetch is caught and reported."""
    mock_fetch.side_effect = TimeoutError("Page load timed out")
    with pytest.raises(SystemExit) as exc_info:
        main(["fetch", "https://slow.example.com"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "timed out" in captured.err.lower() or "timeout" in captured.err.lower()


def test_fetch_returns_coroutine_not_awaited(mock_fetch):
    """Verify that asyncio.run properly awaits the coroutine."""
    main(["fetch", "https://example.com"])
    # If asyncio.run wasn't used correctly, the test would hang or fail
    assert mock_fetch.called


# ── _do_fetch function tests ─────────────────────────────────────────────


def test_do_fetch_forwards_args(mock_fetch):
    """_do_fetch correctly forwards namespace attributes to _async_fetch."""
    import argparse

    args = argparse.Namespace(
        url="https://test.com",
        cookies="c.json",
        selector="main",
        screenshot="s.png",
        pdf="p.pdf",
        wait=500,
    )

    # Run the async function
    result = asyncio.run(_mod["_do_fetch"](args))
    assert result == _FAKE_RESULT
    mock_fetch.assert_called_once_with(
        "https://test.com",
        cookies="c.json",
        selector="main",
        screenshot="s.png",
        pdf="p.pdf",
        wait=500,
    )


# ── integration-style tests (subprocess) ─────────────────────────────────


def test_browser_effector_cli_help_flag():
    """--help flag prints usage and exits 0."""
    import subprocess

    result = subprocess.run(
        ["python", str(EFFECTOR_PATH), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "fetch" in result.stdout.lower() or "usage" in result.stdout.lower()


def test_cli_no_args_exits_1():
    """Running with no arguments exits 1 and prints help to stderr."""
    import subprocess

    result = subprocess.run(
        ["python", str(EFFECTOR_PATH)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "usage" in result.stderr.lower() or "fetch" in result.stderr.lower()
