"""Tests for effectors/lustro-analyze.

Uses exec() to load the effector as a script (not importable module),
following the golem testing pattern for effectors.
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

# Load the effector via exec into an isolated namespace
_EFFECTOR = Path(__file__).resolve().parent.parent / "effectors" / "lustro-analyze"
_NS: dict = {}
exec(open(_EFFECTOR).read(), _NS)
# Now _NS contains all the functions: classify_topic, relevance_score, load_article, etc.

classify_topic = _NS["classify_topic"]
relevance_score = _NS["relevance_score"]
load_article = _NS["load_article"]
load_all_articles = _NS["load_all_articles"]
format_summary_table = _NS["format_summary_table"]
format_top_articles = _NS["format_top_articles"]
extract_themes = _NS["extract_themes"]
format_themes = _NS["format_themes"]
run = _NS["run"]


@pytest.fixture()
def sample_articles(tmp_path):
    """Create a temp directory with sample article JSON files."""
    articles = [
        {
            "title": "OpenAI releases GPT-5 with improved reasoning",
            "date": "2026-03-20",
            "source": "OpenAI News",
            "tier": 1,
            "link": "https://example.com/gpt5",
            "summary": "OpenAI has released its latest model with breakthrough reasoning.",
            "text": "GPT-5 shows major improvements in reasoning and code generation.",
            "fetched_at": "2026-03-20T10:00:00Z",
        },
        {
            "title": "TD Bank deploys AI for fraud detection",
            "date": "2026-03-18",
            "source": "Layer 6 (TD Bank)",
            "tier": 1,
            "link": "https://example.com/td-ai",
            "summary": "TD Bank uses machine learning models for real-time fraud detection.",
            "text": "TD Bank has deployed AI-powered fraud detection across its retail banking operations.",
            "fetched_at": "2026-03-18T10:00:00Z",
        },
        {
            "title": "FCA issues new AI regulation guidance",
            "date": "2026-03-15",
            "source": "UK FCA",
            "tier": 1,
            "link": "https://example.com/fca-ai",
            "summary": "The FCA published guidance on AI model governance for financial services.",
            "text": "Regulatory guidance for banks using AI systems in lending and compliance.",
            "fetched_at": "2026-03-15T10:00:00Z",
        },
        {
            "title": "Random startup raises funding",
            "date": "2026-03-10",
            "source": "TechCrunch",
            "tier": 2,
            "link": "https://example.com/startup",
            "summary": "A random startup raised series A funding.",
            "text": "A random startup making widgets raised a series A round.",
            "fetched_at": "2026-03-10T10:00:00Z",
        },
    ]
    for i, art in enumerate(articles):
        (tmp_path / f"article_{i}.json").write_text(json.dumps(art))
    return tmp_path


# ── classify_topic ──────────────────────────────────────────────────────────

class TestClassifyTopic:
    def test_ai_topic(self):
        art = {"title": "New GPT model released", "summary": "", "text": "OpenAI released a new LLM."}
        assert classify_topic(art) == "AI"

    def test_banking_topic(self):
        art = {"title": "Bank lending report", "summary": "", "text": "Banks are increasing lending to SMEs."}
        assert classify_topic(art) == "banking"

    def test_regulation_topic(self):
        art = {"title": "FCA regulation update", "summary": "", "text": "New regulatory framework for compliance."}
        assert classify_topic(art) == "regulation"

    def test_technology_topic(self):
        art = {"title": "Nvidia chip shortage", "summary": "", "text": "Semiconductor supply chain issues affect GPU production."}
        assert classify_topic(art) == "technology"

    def test_other_topic(self):
        art = {"title": "Weather report", "summary": "", "text": "It will rain tomorrow."}
        assert classify_topic(art) == "other"

    def test_multi_topic_picks_highest(self):
        # Both banking and AI keywords, but banking is heavier
        art = {
            "title": "Bank AI lending model",
            "summary": "",
            "text": "bank banking lending credit loan mortgage " * 5 + "AI model " * 2,
        }
        result = classify_topic(art)
        assert result == "banking"


# ── relevance_score ─────────────────────────────────────────────────────────

class TestRelevanceScore:
    def test_banking_ai_article_scores_high(self):
        art = {
            "title": "Bank uses AI for lending",
            "summary": "TD Bank deploys machine learning for credit decisions.",
            "text": "bank banking lending credit AI model LLM machine learning",
            "tier": 1,
        }
        score = relevance_score(art)
        assert score >= 5.0, f"Expected high score, got {score}"

    def test_irrelevant_article_scores_low(self):
        art = {
            "title": "Random weather data",
            "summary": "Sunny skies expected.",
            "text": "The weather will be sunny with temperatures around 70 degrees.",
            "tier": 99,
        }
        score = relevance_score(art)
        assert score < 2.0, f"Expected low score, got {score}"

    def test_banking_only_scores_moderate(self):
        art = {
            "title": "Bank quarterly results",
            "summary": "Bank reports earnings.",
            "text": "bank banking financial services lending credit",
            "tier": 2,
        }
        score = relevance_score(art)
        assert 1.0 <= score <= 6.0

    def test_score_capped_at_10(self):
        art = {
            "title": "Bank AI " * 20,
            "summary": "banking AI LLM GPT " * 20,
            "text": ("bank banking lending credit fintech AI LLM GPT openai regulation "
                     "compliance governance FCA ") * 20,
            "tier": 1,
        }
        score = relevance_score(art)
        assert score <= 10.0

    def test_tier_bonus(self):
        base = {"title": "bank AI", "summary": "", "text": "bank AI"}
        tier1 = {**base, "tier": 1}
        tier99 = {**base, "tier": 99}
        assert relevance_score(tier1) > relevance_score(tier99)


# ── load_article ────────────────────────────────────────────────────────────

class TestLoadArticle:
    def test_load_json(self, tmp_path):
        data = {"title": "Test", "source": "src", "date": "2026-01-01",
                "text": "body", "summary": "sum", "tier": 1}
        p = tmp_path / "test.json"
        p.write_text(json.dumps(data))
        result = load_article(p)
        assert result is not None
        assert result["title"] == "Test"
        assert result["source"] == "src"
        assert result["date"] == "2026-01-01"

    def test_load_md(self, tmp_path):
        p = tmp_path / "test.md"
        p.write_text("# My Title\n\nSome content here.")
        result = load_article(p)
        assert result is not None
        assert result["title"] == "My Title"
        assert result["source"] == "markdown"
        assert "Some content" in result["text"]

    def test_load_invalid_json(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{invalid json!!!")
        result = load_article(p)
        assert result is None

    def test_load_nonexistent(self, tmp_path):
        p = tmp_path / "missing.json"
        result = load_article(p)
        assert result is None

    def test_load_json_list(self, tmp_path):
        """A JSON file containing a list (not dict) should return None."""
        p = tmp_path / "list.json"
        p.write_text("[1, 2, 3]")
        result = load_article(p)
        assert result is None


# ── load_all_articles ───────────────────────────────────────────────────────

class TestLoadAllArticles:
    def test_loads_from_dir(self, sample_articles):
        arts = load_all_articles(sample_articles)
        assert len(arts) == 4

    def test_empty_dir(self, tmp_path):
        arts = load_all_articles(tmp_path)
        assert arts == []

    def test_nonexistent_dir(self, tmp_path):
        arts = load_all_articles(tmp_path / "nope")
        assert arts == []

    def test_ignores_non_article_files(self, tmp_path):
        (tmp_path / "readme.txt").write_text("ignore me")
        (tmp_path / "data.csv").write_text("a,b,c")
        arts = load_all_articles(tmp_path)
        assert len(arts) == 0


# ── format_summary_table ───────────────────────────────────────────────────

class TestFormatSummaryTable:
    def test_includes_topic_headers(self, sample_articles):
        arts = load_all_articles(sample_articles)
        for a in arts:
            a["_topic"] = classify_topic(a)
        table = format_summary_table(arts)
        assert "AI" in table
        assert "BANKING" in table
        assert "Total articles:" in table

    def test_empty_articles(self):
        table = format_summary_table([])
        assert "Total articles: 0" in table


# ── format_top_articles ─────────────────────────────────────────────────────

class TestFormatTopArticles:
    def test_top_n(self, sample_articles):
        arts = load_all_articles(sample_articles)
        for a in arts:
            a["_topic"] = classify_topic(a)
            a["_relevance"] = relevance_score(a)
        report = format_top_articles(arts, n=2)
        assert "TOP 2 ARTICLES" in report
        # Should not contain article 3 or 4
        assert "Random startup" not in report

    def test_scores_displayed(self, sample_articles):
        arts = load_all_articles(sample_articles)
        for a in arts:
            a["_topic"] = classify_topic(a)
            a["_relevance"] = relevance_score(a)
        report = format_top_articles(arts, n=4)
        # Should have numbered entries with scores
        assert "1." in report
        assert "topic:" in report


# ── extract_themes ──────────────────────────────────────────────────────────

class TestExtractThemes:
    def test_returns_counter(self, sample_articles):
        arts = load_all_articles(sample_articles)
        themes = extract_themes(arts, top_n=5)
        assert isinstance(themes, list)
        assert len(themes) <= 5
        assert all(isinstance(t, tuple) and len(t) == 2 for t in themes)

    def test_common_terms_present(self, sample_articles):
        arts = load_all_articles(sample_articles)
        themes = extract_themes(arts, top_n=20)
        terms = [t for t, _ in themes]
        # "ai" or "bank" should appear given our test data
        assert any(t in terms for t in ("ai", "bank", "model"))


# ── run (integration) ──────────────────────────────────────────────────────

class TestRun:
    def test_full_report(self, sample_articles):
        report = run(directory=sample_articles, top=3)
        assert "SUMMARY BY TOPIC" in report
        assert "BANKING AI CONSULTING RELEVANCE" in report
        assert "KEY THEMES" in report
        assert "TOP 3 ARTICLES" in report

    def test_topic_filter(self, sample_articles):
        report = run(directory=sample_articles, top=10, topic="AI")
        # Should only show AI articles in the summary
        assert "SUMMARY BY TOPIC" in report

    def test_output_file(self, sample_articles, tmp_path):
        out = tmp_path / "report.txt"
        report = run(directory=sample_articles, top=3, output=str(out))
        assert out.exists()
        content = out.read_text()
        assert "SUMMARY BY TOPIC" in content

    def test_empty_dir(self, tmp_path):
        report = run(directory=tmp_path)
        assert "No articles found" in report
