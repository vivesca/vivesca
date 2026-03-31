from __future__ import annotations
"""Tests for effectors/poiesis — search Capco vault notes by keyword."""


import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "effectors" / "poiesis"
    loader = SourceFileLoader("poiesis", str(module_path))
    spec = importlib.util.spec_from_loader("poiesis", loader)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── read_file / warn_missing ─────────────────────────────────────────────────


class TestReadFile:
    def test_returns_content(self, tmp_path):
        mod = _load_module()
        f = tmp_path / "test.md"
        f.write_text("hello world", encoding="utf-8")
        assert mod.read_file(f) == "hello world"

    def test_returns_none_when_missing(self, tmp_path, capsys):
        mod = _load_module()
        missing = tmp_path / "nonexistent.md"
        assert mod.read_file(missing) is None
        captured = capsys.readouterr()
        assert "Warning" in captured.err

    def test_warn_missing_prints_warning(self, capsys):
        mod = _load_module()
        mod.warn_missing(Path("/no/such/file"))
        captured = capsys.readouterr()
        assert "Warning" in captured.err
        assert "/no/such/file" in captured.err


# ── split_sections ────────────────────────────────────────────────────────────


class TestSplitSections:
    def test_splits_h2_and_h3(self):
        mod = _load_module()
        text = "## Heading One\ncontent one\n### Sub\nsub content\n## Heading Two\ntwo content"
        sections = mod.split_sections(text)
        assert len(sections) == 3
        assert sections[0]["heading"] == "Heading One"
        assert sections[0]["level"] == 2
        assert sections[1]["heading"] == "Sub"
        assert sections[1]["level"] == 3
        assert sections[2]["heading"] == "Heading Two"

    def test_empty_text(self):
        mod = _load_module()
        assert mod.split_sections("") == []

    def test_no_headings(self):
        mod = _load_module()
        assert mod.split_sections("just plain text\nno headings") == []

    def test_single_heading(self):
        mod = _load_module()
        text = "## Only\nbody text here"
        sections = mod.split_sections(text)
        assert len(sections) == 1
        assert "body text here" in sections[0]["content"]


# ── score_section ─────────────────────────────────────────────────────────────


class TestScoreSection:
    def test_counts_hits(self):
        mod = _load_module()
        score = mod.score_section(["ai", "risk"], "AI Risk Management", "Risk of AI in banking")
        assert score >= 3

    def test_no_hits(self):
        mod = _load_module()
        score = mod.score_section(["quantum"], "AI stuff", "Machine learning content")
        assert score == 0

    def test_case_insensitive(self):
        mod = _load_module()
        score = mod.score_section(["banking"], "BANKING", "Banking sector")
        # "banking banking sector" lowercased: "banking" occurs 2 times
        assert score >= 2


# ── excerpt ───────────────────────────────────────────────────────────────────


class TestExcerpt:
    def test_returns_keyword_window(self):
        mod = _load_module()
        content = "line one\nkeyword match here\nline three\nline four"
        result = mod.excerpt(content, ["keyword"])
        assert "keyword" in result.lower()

    def test_fallback_first_lines(self):
        mod = _load_module()
        content = "first line\nsecond line\nthird line"
        result = mod.excerpt(content, ["xyznotfound"])
        assert "first line" in result

    def test_truncates_long_content(self):
        mod = _load_module()
        content = " ".join(["word"] * 500)
        result = mod.excerpt(content, ["word"], max_chars=50)
        assert len(result) <= 50


# ── search ────────────────────────────────────────────────────────────────────


class TestSearch:
    def test_search_finds_matches(self, capsys):
        mod = _load_module()
        fake_text = "## AI Strategy\nArtificial intelligence strategy for banking.\n## Other\nUnrelated."
        with patch.dict(mod.FILES, {"cases": Path("/fake/cases.md")}):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "read_text", return_value=fake_text):
                    mod.search("AI banking")
        out = capsys.readouterr().out
        assert "AI Strategy" in out

    def test_search_no_matches(self, capsys):
        mod = _load_module()
        fake_text = "## Something\nContent here."
        with patch.dict(mod.FILES, {"cases": Path("/fake/cases.md")}):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "read_text", return_value=fake_text):
                    mod.search("xyznotfound123")
        out = capsys.readouterr().out
        assert "No matches found" in out

    def test_search_skips_missing_files(self, capsys):
        mod = _load_module()
        with patch.dict(mod.FILES, {"cases": Path("/fake/missing.md")}):
            with patch.object(Path, "exists", return_value=False):
                mod.search("anything")
        out = capsys.readouterr().out
        assert "No matches found" in out


# ── list_* commands ───────────────────────────────────────────────────────────


class TestListCommands:
    def test_list_cases(self, capsys):
        mod = _load_module()
        fake_text = "## Case Study: Fraud Detection\nDetails here.\n## Another Case\nMore."
        with patch.dict(mod.FILES, {"cases": Path("/fake/cases.md")}):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "read_text", return_value=fake_text):
                    mod.list_cases()
        out = capsys.readouterr().out
        assert "Case Study: Fraud Detection" in out
        assert "Another Case" in out

    def test_list_cases_missing_file(self, capsys):
        mod = _load_module()
        with patch.dict(mod.FILES, {"cases": Path("/fake/missing.md")}):
            with patch.object(Path, "exists", return_value=False):
                mod.list_cases()
        err = capsys.readouterr().err
        assert "Warning" in err

    def test_list_objections(self, capsys):
        mod = _load_module()
        fake_text = "## Objection: Too Expensive\nResponse.\n## Objection: Not Ready\nResponse."
        with patch.dict(mod.FILES, {"objections": Path("/fake/obj.md")}):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "read_text", return_value=fake_text):
                    mod.list_objections()
        out = capsys.readouterr().out
        assert "Objection: Too Expensive" in out

    def test_list_objections_none_found(self, capsys):
        mod = _load_module()
        fake_text = "## Something Else\nNo objections here."
        with patch.dict(mod.FILES, {"objections": Path("/fake/obj.md")}):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "read_text", return_value=fake_text):
                    mod.list_objections()
        out = capsys.readouterr().out
        assert "No objection headings found" in out

    def test_list_questions(self, capsys):
        mod = _load_module()
        fake_text = "## Discovery Questions\nQ1?\n## Technical Questions\nQ2?"
        with patch.dict(mod.FILES, {"questions": Path("/fake/q.md")}):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "read_text", return_value=fake_text):
                    mod.list_questions()
        out = capsys.readouterr().out
        assert "Discovery Questions" in out
        assert "Technical Questions" in out

    def test_list_questions_missing(self, capsys):
        mod = _load_module()
        with patch.dict(mod.FILES, {"questions": Path("/fake/q.md")}):
            with patch.object(Path, "exists", return_value=False):
                mod.list_questions()
        err = capsys.readouterr().err
        assert "Warning" in err


# ── show_help / main ──────────────────────────────────────────────────────────


class TestMain:
    def test_help_flag(self, capsys):
        mod = _load_module()
        with patch("sys.argv", ["poiesis", "--help"]):
            mod.main()
        out = capsys.readouterr().out
        assert "poiesis" in out or "Usage" in out or "copia" in out

    def test_search_by_args(self):
        mod = _load_module()
        with patch("sys.argv", ["poiesis", "test", "query"]):
            with patch.object(mod, "search") as mock_search:
                mod.main()
                mock_search.assert_called_once_with("test query")

    def test_cases_flag(self):
        mod = _load_module()
        with patch("sys.argv", ["poiesis", "--cases"]):
            with patch.object(mod, "list_cases") as mock_list:
                mod.main()
                mock_list.assert_called_once()

    def test_objections_flag(self):
        mod = _load_module()
        with patch("sys.argv", ["poiesis", "--objections"]):
            with patch.object(mod, "list_objections") as mock_list:
                mod.main()
                mock_list.assert_called_once()

    def test_questions_flag(self):
        mod = _load_module()
        with patch("sys.argv", ["poiesis", "--questions"]):
            with patch.object(mod, "list_questions") as mock_list:
                mod.main()
                mock_list.assert_called_once()
