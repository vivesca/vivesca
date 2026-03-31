"""Tests for browser effector — CLI wrapper for headless page fetcher."""
from __future__ import annotations

import contextlib
import json
from pathlib import Path

import pytest


def _load_effector() -> dict:
    """Load the browser effector by exec-ing its Python body."""
    source = (Path.home() / "germline" / "effectors" / "browser").read_text()
    ns: dict = {"__name__": "browser_effector"}
    exec(source, ns)
    return ns


_mod = _load_effector()
build_parser = _mod["build_parser"]
format_text = _mod["format_text"]
format_json = _mod["format_json"]
run_fetch = _mod["run_fetch"]
main = _mod["main"]


# ── helpers ──────────────────────────────────────────────────────────

_SAMPLE_RESULT = {
    "text": "Hello world",
    "title": "Example Page",
    "url": "https://example.com",
    "status": 200,
    "cookies_loaded": 0,
    "screenshot_saved": False,
    "pdf_saved": False,
}


@contextlib.contextmanager
def _patch_fetch(result: dict):
    """Temporarily replace fetch in the effector namespace with an async mock."""
    original = _mod["fetch"]

    async def _mock(*args, **kwargs):
        return result

    _mod["fetch"] = _mock
    try:
        yield
    finally:
        _mod["fetch"] = original


# ── build_parser tests ──────────────────────────────────────────────


def test_parser_fetch_basic():
    """Parser extracts URL from fetch subcommand."""
    args = build_parser().parse_args(["fetch", "https://example.com"])
    assert args.command == "fetch"
    assert args.url == "https://example.com"


def test_parser_fetch_all_options():
    """Parser extracts every optional flag."""
    args = build_parser().parse_args([
        "fetch", "https://example.com",
        "--cookies", "/tmp/ck.json",
        "--selector", "article",
        "--screenshot", "/tmp/shot.png",
        "--pdf", "/tmp/page.pdf",
        "--wait", "2000",
        "--json",
    ])
    assert args.cookies == "/tmp/ck.json"
    assert args.selector == "article"
    assert args.screenshot == "/tmp/shot.png"
    assert args.pdf == "/tmp/page.pdf"
    assert args.wait == 2000
    assert args.json_output is True


def test_parser_no_command():
    """Parser sets command=None when no subcommand given."""
    args = build_parser().parse_args([])
    assert args.command is None


def test_parser_defaults():
    """Parser defaults: no cookies, no selector, wait=0, json=False."""
    args = build_parser().parse_args(["fetch", "https://x.com"])
    assert args.cookies is None
    assert args.selector is None
    assert args.screenshot is None
    assert args.pdf is None
    assert args.wait == 0
    assert args.json_output is False


# ── format_text tests ───────────────────────────────────────────────


def test_format_text_includes_body_and_meta():
    """format_text outputs page text followed by a metadata block."""
    out = format_text(_SAMPLE_RESULT)
    assert "Hello world" in out
    assert "title: Example Page" in out
    assert "url: https://example.com" in out
    assert "status: 200" in out
    assert "---" in out


def test_format_text_empty_fields():
    """format_text handles empty strings without error."""
    result = {"text": "", "title": "", "url": "", "status": 0}
    out = format_text(result)
    assert isinstance(out, str)


def test_format_text_multiline_body():
    """format_text preserves newlines in page text."""
    result = dict(_SAMPLE_RESULT, text="Line 1\nLine 2\nLine 3")
    out = format_text(result)
    assert "Line 1\nLine 2\nLine 3" in out


def test_format_text_no_title():
    """format_text omits title line when title is empty."""
    result = dict(_SAMPLE_RESULT, title="")
    out = format_text(result)
    assert "title:" not in out


# ── format_json tests ───────────────────────────────────────────────


def test_format_json_roundtrip():
    """format_json produces valid JSON with every key."""
    out = format_json(_SAMPLE_RESULT)
    parsed = json.loads(out)
    assert parsed["text"] == "Hello world"
    assert parsed["status"] == 200
    assert parsed["cookies_loaded"] == 0
    assert parsed["screenshot_saved"] is False


def test_format_json_unicode():
    """format_json preserves non-ASCII characters."""
    result = dict(_SAMPLE_RESULT, text="日本語テスト", title="テスト")
    out = format_json(result)
    assert "日本語テスト" in out
    assert json.loads(out)["text"] == "日本語テスト"


# ── main tests ──────────────────────────────────────────────────────


def test_main_no_command_returns_1(capsys):
    """main prints help to stderr and returns 1 with no subcommand."""
    rc = main([])
    assert rc == 1


def test_main_fetch_text_output(capsys):
    """main prints human-readable text for a fetch."""
    with _patch_fetch(_SAMPLE_RESULT):
        rc = main(["fetch", "https://example.com"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Hello world" in out
    assert "title: Example Page" in out


def test_main_fetch_json_output(capsys):
    """main prints JSON when --json flag is set."""
    with _patch_fetch(_SAMPLE_RESULT):
        rc = main(["fetch", "https://example.com", "--json"])
    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["text"] == "Hello world"
    assert parsed["status"] == 200


def test_main_fetch_passes_all_options(capsys):
    """main forwards every CLI option to the fetch function."""
    captured: dict = {}

    async def _spy(url, *, cookies=None, selector=None,
                   screenshot=None, pdf=None, wait=0):
        captured.update(url=url, cookies=cookies, selector=selector,
                        screenshot=screenshot, pdf=pdf, wait=wait)
        return _SAMPLE_RESULT

    original = _mod["fetch"]
    _mod["fetch"] = _spy
    try:
        rc = main([
            "fetch", "https://example.com",
            "--cookies", "/tmp/ck.json",
            "--selector", "main",
            "--screenshot", "/tmp/s.png",
            "--pdf", "/tmp/p.pdf",
            "--wait", "1500",
        ])
    finally:
        _mod["fetch"] = original

    assert rc == 0
    assert captured["url"] == "https://example.com"
    assert captured["cookies"] == "/tmp/ck.json"
    assert captured["selector"] == "main"
    assert captured["screenshot"] == "/tmp/s.png"
    assert captured["pdf"] == "/tmp/p.pdf"
    assert captured["wait"] == 1500


def test_main_fetch_default_wait(capsys):
    """main passes wait=0 when --wait is not specified."""
    captured: dict = {}

    async def _spy(url, **kw):
        captured.update(kw)
        return _SAMPLE_RESULT

    original = _mod["fetch"]
    _mod["fetch"] = _spy
    try:
        main(["fetch", "https://example.com"])
    finally:
        _mod["fetch"] = original

    assert captured["wait"] == 0


def test_main_returns_0_on_success(capsys):
    """main returns exit code 0 on a successful fetch."""
    with _patch_fetch(_SAMPLE_RESULT):
        assert main(["fetch", "https://example.com"]) == 0
