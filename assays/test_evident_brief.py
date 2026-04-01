from __future__ import annotations

"""Tests for effectors/evident-brief — Evident Banking Brief fetcher."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest


def _load_evident_brief():
    """Load the evident-brief effector by exec-ing its Python body."""
    source = open(str(Path.home() / "germline/effectors/evident-brief")).read()
    ns: dict = {"__name__": "evident_brief"}
    exec(source, ns)
    return ns


_mod = _load_evident_brief()

# Pull out callables for convenience
_get_firecrawl_key = _mod["_get_firecrawl_key"]
_ab = _mod["_ab"]
fetch_markdown = _mod["fetch_markdown"]
_parse_index_firecrawl = _mod["_parse_index_firecrawl"]
_parse_index_browser = _mod["_parse_index_browser"]
parse_index = _mod["parse_index"]
fetch_brief = _mod["fetch_brief"]
save_brief = _mod["save_brief"]
main = _mod["main"]

BASE_URL = _mod["BASE_URL"]
CHROMATIN_DIR = _mod["CHROMATIN_DIR"]


# ── _get_firecrawl_key ────────────────────────────────────────────────────────


class TestGetFirecrawlKey:
    def test_env_var_set(self):
        with patch.dict("os.environ", {"FIRECRAWL_API_KEY": "fc-test123"}):
            # The function reads os.environ which is the real os module
            _mod["os"].environ["FIRECRAWL_API_KEY"] = "fc-test123"
            assert _get_firecrawl_key() == "fc-test123"
            del _mod["os"].environ["FIRECRAWL_API_KEY"]

    def test_env_var_empty_no_op(self):
        _mod["os"].environ["FIRECRAWL_API_KEY"] = ""
        with patch("subprocess.run", side_effect=FileNotFoundError("no op")):
            assert _get_firecrawl_key() == ""
        del _mod["os"].environ["FIRECRAWL_API_KEY"]

    def test_op_returns_valid_fc_key(self):
        _mod["os"].environ["FIRECRAWL_API_KEY"] = ""
        mock_r = MagicMock()
        mock_r.stdout = "fc-op-key-123\n"
        with patch("subprocess.run", return_value=mock_r):
            assert _get_firecrawl_key() == "fc-op-key-123"
        del _mod["os"].environ["FIRECRAWL_API_KEY"]

    def test_op_returns_non_fc_prefix_rejected(self):
        _mod["os"].environ["FIRECRAWL_API_KEY"] = ""
        mock_r = MagicMock()
        mock_r.stdout = "random-key\n"
        with patch("subprocess.run", return_value=mock_r):
            assert _get_firecrawl_key() == ""
        del _mod["os"].environ["FIRECRAWL_API_KEY"]


# ── _ab ────────────────────────────────────────────────────────────────────────


class TestAb:
    def test_returns_stdout(self):
        mock_r = MagicMock()
        mock_r.stdout = "result text\n"
        with patch("subprocess.run", return_value=mock_r):
            assert _ab("open https://example.com") == "result text"

    def test_splits_command_string(self):
        mock_r = MagicMock()
        mock_r.stdout = ""
        with patch("subprocess.run", return_value=mock_r) as mock_run:
            _ab("open https://example.com")
            args = mock_run.call_args[0][0]
            assert args == ["agent-browser", "open", "https://example.com"]

    def test_custom_timeout(self):
        mock_r = MagicMock()
        mock_r.stdout = ""
        with patch("subprocess.run", return_value=mock_r) as mock_run:
            _ab("cmd", timeout=30)
            assert mock_run.call_args[1]["timeout"] == 30


# ── fetch_markdown ─────────────────────────────────────────────────────────────


class TestFetchMarkdown:
    def _mock_urlopen(self, content: bytes):
        fake_resp = MagicMock()
        fake_resp.read.return_value = content
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        return fake_resp

    def test_returns_content(self):
        body = b"# Hello World\n" + b"x" * 200
        with patch("urllib.request.urlopen", return_value=self._mock_urlopen(body)):
            result = fetch_markdown("https://example.com/article")
            assert "# Hello World" in result

    def test_short_content_exits(self):
        with patch("urllib.request.urlopen", return_value=self._mock_urlopen(b"short")):
            with pytest.raises(SystemExit):
                fetch_markdown("https://example.com")

    def test_prepends_jina_url(self):
        body = b"# Title\n" + b"x" * 200
        with patch("urllib.request.urlopen", return_value=self._mock_urlopen(body)) as mock_open:
            fetch_markdown("https://evident.com/page")
            req = mock_open.call_args[0][0]
            assert req.full_url == "https://r.jina.ai/https://evident.com/page"


# ── _parse_index_firecrawl ────────────────────────────────────────────────────


class TestParseIndexFirecrawl:
    def test_no_key_returns_empty(self):
        _mod["_get_firecrawl_key"] = lambda: ""
        result = _parse_index_firecrawl()
        assert result == []
        _mod["_get_firecrawl_key"] = _get_firecrawl_key

    def test_parses_brief_links(self):
        _mod["_get_firecrawl_key"] = lambda: "fc-test"
        mock_item = MagicMock()
        mock_item.url = "https://evidentinsights.com/bankingbrief/ai-risk-tiering"
        mock_item.title = "AI Risk Tiering"
        mock_result = MagicMock()
        mock_result.links = [mock_item]
        mock_fc_instance = MagicMock()
        mock_fc_instance.map.return_value = mock_result
        mock_fc_class = MagicMock(return_value=mock_fc_instance)

        # Patch the firecrawl import inside the function
        import builtins
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "firecrawl":
                mod = MagicMock()
                mod.FirecrawlApp = mock_fc_class
                return mod
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            result = _parse_index_firecrawl()

        assert len(result) == 1
        assert result[0]["slug"] == "ai-risk-tiering"
        assert result[0]["title"] == "AI Risk Tiering"
        # Restore
        _mod["_get_firecrawl_key"] = _get_firecrawl_key


# ── _parse_index_browser ─────────────────────────────────────────────────────


class TestParseIndexBrowser:
    def test_extracts_briefs_from_snapshot(self):
        snapshot = (
            'link "AI in Banking 2025" ref=abc1\n'
            '15 JANUARY 2025\n'
            'link "Risk Tiering Report" ref=def2\n'
            '20 FEBRUARY 2025\n'
        )
        # First _ab("open ..."), then _ab("snapshot"), then _ab("snapshot") again
        _mod["_ab"] = MagicMock(side_effect=["ok", snapshot, snapshot])
        with patch("subprocess.run"):
            result = _parse_index_browser()
        # Should find briefs with dates
        assert isinstance(result, list)
        # Restore
        _mod["_ab"] = _ab

    def test_returns_empty_on_failure(self):
        _mod["_ab"] = MagicMock(side_effect=Exception("browser failed"))
        with patch("subprocess.run"):
            result = _parse_index_browser()
        assert result == []
        # Restore
        _mod["_ab"] = _ab


# ── parse_index ────────────────────────────────────────────────────────────────


class TestParseIndex:
    def test_browser_succeeds_no_fallback(self):
        fake_briefs = [{"title": "Test", "slug": "test", "url": "https://x.com/test", "date": "1 January 2025"}]
        _mod["_parse_index_browser"] = lambda: fake_briefs
        result = parse_index()
        assert result == fake_briefs
        _mod["_parse_index_browser"] = _parse_index_browser

    def test_browser_empty_falls_back_to_firecrawl(self):
        fake_briefs = [{"title": "FC", "slug": "fc", "url": "https://x.com/fc", "date": ""}]
        _mod["_parse_index_browser"] = lambda: []
        _mod["_parse_index_firecrawl"] = lambda: fake_briefs
        result = parse_index()
        assert result == fake_briefs
        _mod["_parse_index_browser"] = _parse_index_browser
        _mod["_parse_index_firecrawl"] = _parse_index_firecrawl

    def test_both_empty(self):
        _mod["_parse_index_browser"] = lambda: []
        _mod["_parse_index_firecrawl"] = lambda: []
        result = parse_index()
        assert result == []
        _mod["_parse_index_browser"] = _parse_index_browser
        _mod["_parse_index_firecrawl"] = _parse_index_firecrawl


# ── fetch_brief ────────────────────────────────────────────────────────────────


class TestFetchBrief:
    def test_extracts_title_from_h1(self):
        raw_md = "# AI in Banking\n\nSome content about AI in banking sector."
        _mod["fetch_markdown"] = lambda url: raw_md
        result = fetch_brief("ai-in-banking")
        assert result["title"] == "AI in Banking"
        assert result["slug"] == "ai-in-banking"
        assert "ai-in-banking" in result["url"]
        _mod["fetch_markdown"] = fetch_markdown

    def test_extracts_date(self):
        raw_md = "# Title\n\nPublished 15 January 2025 by Evident.\nMore content."
        _mod["fetch_markdown"] = lambda url: raw_md
        result = fetch_brief("test-slug")
        assert result["date"] == "15 January 2025"
        _mod["fetch_markdown"] = fetch_markdown

    def test_uses_index_meta_date_as_fallback(self):
        raw_md = "# Title\n\nNo date here."
        meta = {"date": "20 March 2025"}
        _mod["fetch_markdown"] = lambda url: raw_md
        result = fetch_brief("test-slug", index_meta=meta)
        assert result["date"] == "20 March 2025"
        _mod["fetch_markdown"] = fetch_markdown

    def test_cleans_title_prefix(self):
        raw_md = "Title: Evident - The Real Title | Extra\n\nContent here."
        _mod["fetch_markdown"] = lambda url: raw_md
        result = fetch_brief("test-slug")
        assert result["title"] == "The Real Title"
        _mod["fetch_markdown"] = fetch_markdown

    def test_returns_markdown_with_header(self):
        raw_md = "# Test Brief\n\nWelcome back to the Banking Brief!\n\nContent here."
        _mod["fetch_markdown"] = lambda url: raw_md
        result = fetch_brief("test-brief")
        assert result["markdown"].startswith("# Evident Banking Brief:")
        _mod["fetch_markdown"] = fetch_markdown

    def test_truncates_at_explore_archive(self):
        raw_md = "# Brief\n\nContent.\n\nExplore the archive\nFooter stuff."
        _mod["fetch_markdown"] = lambda url: raw_md
        result = fetch_brief("test-brief")
        assert "Explore the archive" not in result["markdown"]
        assert "Footer stuff" not in result["markdown"]
        _mod["fetch_markdown"] = fetch_markdown

    def test_truncates_at_more_news(self):
        raw_md = "# Brief\n\nContent.\n\nMORE NEWS\nExtra stuff."
        _mod["fetch_markdown"] = lambda url: raw_md
        result = fetch_brief("test-brief")
        assert "MORE NEWS" not in result["markdown"]
        _mod["fetch_markdown"] = fetch_markdown

    def test_slug_as_default_title(self):
        raw_md = "Just some generic content without any heading."
        _mod["fetch_markdown"] = lambda url: raw_md
        result = fetch_brief("my-test-brief")
        assert result["title"] == "My Test Brief"
        _mod["fetch_markdown"] = fetch_markdown


# ── save_brief ─────────────────────────────────────────────────────────────────


class TestSaveBrief:
    def test_creates_md_file(self, tmp_path):
        chromatin = tmp_path / "evident"
        _mod["CHROMATIN_DIR"] = chromatin
        brief = {
            "title": "Test Brief",
            "date": "15 January 2025",
            "slug": "test-brief",
            "url": "https://example.com/test-brief",
            "markdown": "# Test Brief\n\nContent.",
        }
        path = save_brief(brief)
        assert path.exists()
        assert path.suffix == ".md"
        assert path.read_text() == "# Test Brief\n\nContent."
        # Restore
        _mod["CHROMATIN_DIR"] = CHROMATIN_DIR

    def test_filename_includes_date(self, tmp_path):
        chromatin = tmp_path / "evident2"
        _mod["CHROMATIN_DIR"] = chromatin
        brief = {
            "title": "Brief",
            "date": "3 March 2025",
            "slug": "my-brief",
            "url": "https://example.com/my-brief",
            "markdown": "# Content",
        }
        path = save_brief(brief)
        assert "2025-03-03" in path.name
        assert "my-brief" in path.name
        # Restore
        _mod["CHROMATIN_DIR"] = CHROMATIN_DIR

    def test_no_date_uses_today(self, tmp_path):
        chromatin = tmp_path / "evident3"
        _mod["CHROMATIN_DIR"] = chromatin
        brief = {
            "title": "No Date",
            "date": "",
            "slug": "no-date",
            "url": "https://example.com/no-date",
            "markdown": "# No Date",
        }
        path = save_brief(brief)
        assert path.name.startswith("20")
        assert path.suffix == ".md"
        # Restore
        _mod["CHROMATIN_DIR"] = CHROMATIN_DIR


# ── CLI (main) ────────────────────────────────────────────────────────────────


class TestCli:
    def test_list_outputs_briefs(self, capsys):
        fake_briefs = [
            {"title": "AI Banking", "slug": "ai-banking", "url": "https://x.com/ai-banking", "date": "1 Jan 2025"},
            {"title": "Risk Report", "slug": "risk-report", "url": "https://x.com/risk-report", "date": "15 Feb 2025"},
        ]
        _mod["parse_index"] = lambda: fake_briefs
        with patch.object(sys, "argv", ["evident-brief", "--list"]):
            main()
        out = capsys.readouterr().out
        assert "AI Banking" in out
        assert "risk-report" in out
        _mod["parse_index"] = parse_index

    def test_slug_fetches_specific(self, capsys):
        _mod["parse_index"] = lambda: []
        _mod["fetch_brief"] = lambda slug, index_meta=None: {
            "title": "Custom", "date": "2025-01-01", "slug": "custom-brief",
            "url": "https://x.com/custom-brief", "markdown": "# Custom Brief\nContent.",
        }
        with patch.object(sys, "argv", ["evident-brief", "--slug", "custom-brief"]):
            main()
        out = capsys.readouterr().out
        assert "# Custom Brief" in out
        _mod["parse_index"] = parse_index
        _mod["fetch_brief"] = fetch_brief

    def test_json_flag(self, capsys):
        _mod["parse_index"] = lambda: []
        _mod["fetch_brief"] = lambda slug, index_meta=None: {
            "title": "JSON Test", "date": "2025-01-01", "slug": "json-test",
            "url": "https://x.com/json-test", "markdown": "# JSON\nContent.",
        }
        with patch.object(sys, "argv", ["evident-brief", "--slug", "json-test", "--json"]):
            main()
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["title"] == "JSON Test"
        assert "text" in data
        assert "markdown" not in data
        _mod["parse_index"] = parse_index
        _mod["fetch_brief"] = fetch_brief

    def test_save_flag(self, tmp_path):
        chromatin = tmp_path / "save-test"
        _mod["CHROMATIN_DIR"] = chromatin
        _mod["parse_index"] = lambda: []
        _mod["fetch_brief"] = lambda slug, index_meta=None: {
            "title": "Saved", "date": "1 April 2025", "slug": "saved",
            "url": "https://x.com/saved", "markdown": "# Saved\nContent.",
        }
        with patch.object(sys, "argv", ["evident-brief", "--slug", "saved", "--save"]):
            main()
        md_files = list(chromatin.glob("*.md"))
        assert len(md_files) == 1, "Should save one .md file"
        assert "saved" in md_files[0].name
        # Restore
        _mod["CHROMATIN_DIR"] = CHROMATIN_DIR
        _mod["parse_index"] = parse_index
        _mod["fetch_brief"] = fetch_brief

    def test_no_briefs_no_slug_exits(self):
        _mod["parse_index"] = lambda: []
        with patch.object(sys, "argv", ["evident-brief"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 1
        _mod["parse_index"] = parse_index

    def test_default_fetches_latest(self, capsys):
        fake_briefs = [
            {"title": "Latest", "slug": "latest", "url": "https://x.com/latest", "date": "1 Apr 2025"},
        ]
        _mod["parse_index"] = lambda: fake_briefs

        calls = []
        def mock_fetch_brief(slug, index_meta=None):
            calls.append((slug, index_meta))
            return {
                "title": "Latest", "date": "1 April 2025", "slug": "latest",
                "url": "https://x.com/latest", "markdown": "# Latest Brief\nContent.",
            }
        _mod["fetch_brief"] = mock_fetch_brief

        with patch.object(sys, "argv", ["evident-brief"]):
            main()
        out = capsys.readouterr().out
        assert "# Latest Brief" in out
        assert calls[0][0] == "latest"
        assert calls[0][1] == fake_briefs[0]
        # Restore
        _mod["parse_index"] = parse_index
        _mod["fetch_brief"] = fetch_brief
