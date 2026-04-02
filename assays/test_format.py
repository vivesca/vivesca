"""Tests for metabolon.lysin.format."""
from __future__ import annotations

import json

import pytest

from metabolon.lysin.fetch import BioArticle
from metabolon.lysin.format import format_json, format_text


def _article(**overrides):
    """Build a BioArticle with sensible defaults."""
    defaults = dict(
        title="TP53",
        definition="Tumor protein p53.",
        mechanism="Acts as a tumor suppressor.",
        url="https://www.uniprot.org/uniprotkb/P04637",
        sections=[{"title": "Function", "text": "Suppresses tumors."}],
        sources=["UniProt"],
    )
    defaults.update(overrides)
    return BioArticle(**defaults)


class TestFormatText:
    def test_basic_output_has_headers(self):
        art = _article()
        out = format_text(art)
        assert "LYSIN: TP53" in out
        assert "Source: UniProt" in out
        assert "DEFINITION" in out
        assert "MECHANISM" in out
        assert "URL" in out

    def test_full_includes_sections(self):
        art = _article()
        out = format_text(art, full=True)
        assert "SECTIONS" in out
        assert "## Function" in out
        assert "Suppresses tumors." in out

    def test_no_sections_without_full(self):
        art = _article()
        out = format_text(art, full=False)
        assert "SECTIONS" not in out

    def test_multiple_sources_joined(self):
        art = _article(sources=["UniProt", "Reactome"])
        out = format_text(art)
        assert "Source: UniProt, Reactome" in out

    def test_no_sources_shows_unknown(self):
        art = _article(sources=[])
        out = format_text(art)
        assert "Source: unknown" in out

    def test_separators_present(self):
        art = _article()
        out = format_text(art)
        assert "═══════════════════════════════════════" in out


class TestFormatJson:
    def test_basic_fields(self):
        art = _article()
        out = format_json(art)
        data = json.loads(out)
        assert data["title"] == "TP53"
        assert data["definition"] == "Tumor protein p53."
        assert data["mechanism"] == "Acts as a tumor suppressor."
        assert data["url"] == "https://www.uniprot.org/uniprotkb/P04637"
        assert data["sources"] == ["UniProt"]

    def test_full_includes_sections(self):
        art = _article()
        out = format_json(art, full=True)
        data = json.loads(out)
        assert data["sections"] == [{"title": "Function", "text": "Suppresses tumors."}]

    def test_no_sections_without_full(self):
        art = _article()
        out = format_json(art, full=False)
        data = json.loads(out)
        assert "sections" not in data

    def test_valid_json_output(self):
        art = _article()
        out = format_json(art)
        # Must not raise
        json.loads(out)
