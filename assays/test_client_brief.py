from __future__ import annotations

"""Tests for effectors/client-brief — client brief generator."""


import importlib.machinery
import importlib.util
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import module with hyphen in filename (no .py extension)
_MOD_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "effectors", "client-brief"))
_loader = importlib.machinery.SourceFileLoader("client_brief", _MOD_PATH)
spec = importlib.util.spec_from_file_location("client_brief", _MOD_PATH, loader=_loader)
client_brief = importlib.util.module_from_spec(spec)
sys.modules["client_brief"] = client_brief
spec.loader.exec_module(client_brief)


# ── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def fake_chromatin(tmp_path):
    """Create a temporary chromatin tree with sample files."""
    f1 = tmp_path / "HSBC AI Risk Tiering.md"
    f1.write_text(
        "---\ntags: [banking, ai-governance]\n---\n"
        "# HSBC AI Risk Tiering\n"
        "HSBC is a global bank with 200k+ employees.\n"
        "AI governance framework covers model risk management.\n"
        "Regulatory sandbox participation with HKMA.\n",
        encoding="utf-8",
    )
    f2 = tmp_path / "Consulting Landscape.md"
    f2.write_text(
        "# Consulting Landscape\n"
        "Standard Chartered has strong fintech and AML capabilities.\n"
        "Risk tiering is a growing concern for tier-1 banks.\n",
        encoding="utf-8",
    )
    f3 = tmp_path / "unrelated.md"
    f3.write_text("# Random Notes\nNothing relevant here.\n", encoding="utf-8")
    return tmp_path


# ── _read_frontmatter ───────────────────────────────────────────────────────


class TestReadFrontmatter:
    def test_valid_frontmatter(self):
        content = "---\ntitle: Test\ntags: [a]\n---\nBody"
        result = client_brief._read_frontmatter(content)
        assert result["title"] == "Test"
        assert result["tags"] == ["a"]

    def test_no_frontmatter(self):
        assert client_brief._read_frontmatter("Just content") == {}

    def test_empty_string(self):
        assert client_brief._read_frontmatter("") == {}

    def test_invalid_yaml(self):
        content = "---\ninvalid: [unclosed\n---\nBody"
        assert client_brief._read_frontmatter(content) == {}


# ── _should_skip ─────────────────────────────────────────────────────────────


class TestShouldSkip:
    def test_excludes_obsidian(self):
        assert client_brief._should_skip(Path("/notes/.obsidian/config"))

    def test_excludes_git(self):
        assert client_brief._should_skip(Path("/notes/.git/HEAD"))

    def test_excludes_archive(self):
        assert client_brief._should_skip(Path("/notes/Archive/old.md"))

    def test_passes_normal_path(self):
        assert not client_brief._should_skip(Path("/notes/HSBC Risk.md"))


# ── _tokenize ────────────────────────────────────────────────────────────────


class TestTokenize:
    def test_splits_and_lowercases(self):
        assert "hello" in client_brief._tokenize("Hello World!")

    def test_removes_short_tokens(self):
        tokens = client_brief._tokenize("I am a teapot")
        # "a" (1 char) and "I" (1 char) should be excluded
        assert "a" not in tokens
        assert all(len(t) > 2 for t in tokens)

    def test_empty_input(self):
        assert client_brief._tokenize("") == []


# ── _company_tokens ──────────────────────────────────────────────────────────


class TestCompanyTokens:
    def test_single_word(self):
        assert client_brief._company_tokens("HSBC") == ["hsbc"]

    def test_multi_word(self):
        assert client_brief._company_tokens("Standard Chartered") == ["standard", "chartered"]

    def test_strips_punctuation(self):
        tokens = client_brief._company_tokens("HSBC (HK)")
        assert "hk" in tokens
        assert "hsbc" in tokens


# ── _extract_snippets ────────────────────────────────────────────────────────


class TestExtractSnippets:
    def test_finds_matching_lines(self):
        content = (
            "HSBC is a major international banking institution.\n"
            "Short.\n"
            "HSBC has AI governance policies in place across all regions."
        )
        snippets = client_brief._extract_snippets(content, ["hsbc"])
        assert len(snippets) == 2
        assert any("AI governance" in s for s in snippets)

    def test_respects_max_snippets(self):
        lines = [f"HSBC line number {i} with enough text to pass filter." for i in range(10)]
        content = "\n".join(lines)
        snippets = client_brief._extract_snippets(content, ["hsbc"], max_snippets=3)
        assert len(snippets) == 3

    def test_skips_frontmatter_delimiter(self):
        content = "---\ntags: [a]\n---\nHSBC real content line here."
        snippets = client_brief._extract_snippets(content, ["hsbc"])
        assert all(not s.startswith("---") for s in snippets)

    def test_no_match(self):
        content = "Nothing about anyone."
        assert client_brief._extract_snippets(content, ["hsbc"]) == []


# ── search_chromatin ─────────────────────────────────────────────────────────


class TestSearchChromatin:
    def test_finds_relevant_files(self, fake_chromatin):
        with patch.object(client_brief, "CHROMATIN_PATH", fake_chromatin):
            hits = client_brief.search_chromatin("HSBC")
        assert len(hits) >= 1
        assert any("hsbc" in h.path.stem.lower() for h in hits)

    def test_ranks_by_score(self, fake_chromatin):
        with patch.object(client_brief, "CHROMATIN_PATH", fake_chromatin):
            hits = client_brief.search_chromatin("HSBC")
        # HSBC file should score highest
        if len(hits) > 1:
            assert hits[0].score >= hits[1].score

    def test_empty_query(self, fake_chromatin):
        with patch.object(client_brief, "CHROMATIN_PATH", fake_chromatin):
            hits = client_brief.search_chromatin("")
        assert hits == []

    def test_no_results(self, fake_chromatin):
        with patch.object(client_brief, "CHROMATIN_PATH", fake_chromatin):
            hits = client_brief.search_chromatin("NonexistentCompany12345")
        assert hits == []

    def test_respects_top_k(self, fake_chromatin):
        with patch.object(client_brief, "CHROMATIN_PATH", fake_chromatin):
            hits = client_brief.search_chromatin("HSBC", top_k=1)
        assert len(hits) <= 1

    def test_skips_excluded_dirs(self, fake_chromatin):
        archive = fake_chromatin / "Archive"
        archive.mkdir()
        (archive / "old_hsbc.md").write_text("HSBC archived content about banking.", encoding="utf-8")
        with patch.object(client_brief, "CHROMATIN_PATH", fake_chromatin):
            hits = client_brief.search_chromatin("HSBC")
        assert not any("Archive" in str(h.path) for h in hits)


# ── _detect_industry ─────────────────────────────────────────────────────────


class TestDetectIndustry:
    def test_detects_banking(self):
        assert "Banking" in client_brief._detect_industry(["HSBC is a major bank."])

    def test_detects_consulting(self):
        assert "Consulting" in client_brief._detect_industry(["Capco is a consulting firm."])

    def test_unknown(self):
        assert "Not yet determined" in client_brief._detect_industry(["Something completely random."])


# ── _detect_size ─────────────────────────────────────────────────────────────


class TestDetectSize:
    def test_detects_global(self):
        assert "global" in client_brief._detect_size(["A global enterprise with thousands of staff."]).lower()

    def test_unknown(self):
        assert "Not yet determined" in client_brief._detect_size(["Random text."])


# ── _summarise_ai_posture ───────────────────────────────────────────────────


class TestSummariseAiPosture:
    def test_detects_governance(self):
        result = client_brief._summarise_ai_posture(["AI governance framework established."], "HSBC")
        assert "AI governance" in result

    def test_detects_genai(self):
        result = client_brief._summarise_ai_posture(["Exploring generative AI use cases."], "Bank")
        assert "Generative AI" in result

    def test_detects_sandbox(self):
        result = client_brief._summarise_ai_posture(["HKMA sandbox participant."], "HSBC")
        assert "sandbox" in result.lower()

    def test_no_evidence(self):
        result = client_brief._summarise_ai_posture(["Random stuff."], "Foo")
        assert "Limited evidence" in result


# ── _find_consulting_opportunities ───────────────────────────────────────────


class TestFindConsultingOpportunities:
    def test_detects_regulatory(self):
        opps = client_brief._find_consulting_opportunities(["regulatory compliance needs."], "X")
        assert any("Regulatory" in o for o in opps)

    def test_detects_aml(self):
        opps = client_brief._find_consulting_opportunities(["AML model updates needed."], "X")
        assert any("AML" in o for o in opps)

    def test_fallback(self):
        opps = client_brief._find_consulting_opportunities(["nothing relevant."], "X")
        assert any("General AI strategy" in o for o in opps)


# ── generate_brief ───────────────────────────────────────────────────────────


class TestGenerateBrief:
    def test_produces_markdown(self, fake_chromatin):
        with patch.object(client_brief, "CHROMATIN_PATH", fake_chromatin):
            hits = client_brief.search_chromatin("HSBC")
        brief = client_brief.generate_brief("HSBC", hits)
        assert brief.startswith("# Client Brief: HSBC")
        assert "## Overview" in brief
        assert "## Recent News" in brief
        assert "## AI Posture" in brief
        assert "## Consulting Opportunities" in brief
        assert "## Sources" in brief

    def test_empty_hits(self):
        brief = client_brief.generate_brief("UnknownCorp", [])
        assert "UnknownCorp" in brief
        assert "Not yet determined" in brief

    def test_includes_sources(self, fake_chromatin):
        with patch.object(client_brief, "CHROMATIN_PATH", fake_chromatin):
            hits = client_brief.search_chromatin("HSBC")
        brief = client_brief.generate_brief("HSBC", hits)
        assert "HSBC AI Risk Tiering" in brief


# ── CLI (main) ───────────────────────────────────────────────────────────────


class TestCli:
    def test_no_args_exits(self):
        with patch.object(sys, "argv", ["client-brief"]):
            with pytest.raises(SystemExit) as exc_info:
                client_brief.main()
        assert exc_info.value.code == 1

    def test_no_results_exits_cleanly(self, fake_chromatin, capsys):
        with patch.object(client_brief, "CHROMATIN_PATH", fake_chromatin):
            with patch.object(sys, "argv", ["client-brief", "NonexistentCorp999"]):
                with pytest.raises(SystemExit) as exc_info:
                    client_brief.main()
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "No relevant files found" in out

    def test_normal_run(self, fake_chromatin, capsys):
        with patch.object(client_brief, "CHROMATIN_PATH", fake_chromatin):
            with patch.object(sys, "argv", ["client-brief", "HSBC"]):
                client_brief.main()
        out = capsys.readouterr().out
        assert "# Client Brief: HSBC" in out
        assert "## Overview" in out
