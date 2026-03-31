"""Tests for effectors/lustro-analyze.

Load the effector via exec() with a non-__main__ __name__ so the
if __name__ == "__main__" guard does not fire during import.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest


EFFECTOR = Path(__file__).resolve().parent.parent / "effectors" / "lustro-analyze"


@pytest.fixture()
def lustro():
    """Import the effector namespace without triggering main()."""
    ns = {"__name__": "lustro_analyze_test", "__file__": str(EFFECTOR)}
    exec(open(EFFECTOR).read(), ns)  # noqa: S102
    return ns


@pytest.fixture()
def article_dir(tmp_path):
    """Create a temp directory with sample lustro articles."""
    articles = [
        {
            "file": "2026-03-01_openai_abc123.json",
            "data": {
                "title": "GPT-5 Launches with Reasoning Capabilities",
                "date": "2026-03-01",
                "source": "OpenAI News",
                "tier": 1,
                "link": "https://openai.com/gpt5",
                "summary": "",
                "text": "OpenAI today announced GPT-5, a large language model with "
                        "advanced reasoning and agentic capabilities. The model "
                        "achieves state-of-the-art results on multiple benchmarks.",
            },
        },
        {
            "file": "2026-03-02_hkma_def456.json",
            "data": {
                "title": "HKMA Issues AI Governance Framework for Banks",
                "date": "2026-03-02",
                "source": "HKMA Press Releases",
                "tier": 1,
                "link": "https://hkma.gov/ai-framework",
                "summary": "",
                "text": "The Hong Kong Monetary Authority has published a comprehensive "
                        "AI governance framework requiring banks to implement model risk "
                        "management practices for all AI systems used in lending, "
                        "fraud detection, and compliance. Banks must appoint a chief AI "
                        "officer and submit annual AI audit reports.",
            },
        },
        {
            "file": "2026-03-03_willison_ghi789.json",
            "data": {
                "title": "Django 6.0 Released with Async Improvements",
                "date": "2026-03-03",
                "source": "Simon Willison",
                "tier": 1,
                "link": "https://simonwillison.net/django6",
                "summary": "",
                "text": "Django 6.0 brings major improvements to async view handling, "
                        "a new ORM query compiler, and better Python 3.14 support. "
                        "The framework continues to be a popular choice for web developers.",
            },
        },
        {
            "file": "2026-03-04_fca_jkl012.json",
            "data": {
                "title": "FCA Consults on AI Model Risk in Financial Services",
                "date": "2026-03-04",
                "source": "UK FCA (AI/FS)",
                "tier": 1,
                "link": "https://fca.org/ai-risk",
                "summary": "",
                "text": "The UK Financial Conduct Authority published a consultation "
                        "paper on managing AI model risk in financial services. "
                        "The paper covers stress testing, algorithmic accountability, "
                        "and data protection requirements for banks deploying AI.",
            },
        },
    ]
    for art in articles:
        p = tmp_path / art["file"]
        p.write_text(json.dumps(art["data"]), encoding="utf-8")

    # Also add a .md file to test markdown parsing.
    (tmp_path / "2026-03-05_notes_xyz.md").write_text(
        textwrap.dedent("""\
            # Banking AI Trends Q1 2026
            Banks are accelerating AI adoption for fraud detection, credit scoring,
            and customer service chatbots. Regulatory pressure from HKMA and EBA
            continues to shape deployment strategies.
        """),
        encoding="utf-8",
    )
    return tmp_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestClassifyTopic:
    """Tests for classify_topic()."""

    def test_ai_article(self, lustro):
        topic = lustro["classify_topic"](
            "GPT-5 Launches", "OpenAI News",
            "A new large language model with reasoning capabilities.",
        )
        assert topic == "AI"

    def test_banking_article(self, lustro):
        topic = lustro["classify_topic"](
            "HSBC Digital Banking Expansion", "Evident Banking Brief",
            "HSBC is expanding its digital banking platform with new lending tools.",
        )
        assert topic == "banking"

    def test_regulation_article(self, lustro):
        topic = lustro["classify_topic"](
            "EU AI Act Implementation", "Norton Rose Fulbright",
            "New regulation requiring AI governance and compliance for banks.",
        )
        assert topic == "regulation"

    def test_technology_article(self, lustro):
        topic = lustro["classify_topic"](
            "Kubernetes 2.0 Released", "Tech Blog",
            "New features for cloud infrastructure and devops pipelines.",
        )
        assert topic == "technology"

    def test_other_article(self, lustro):
        topic = lustro["classify_topic"](
            "A Motorcycle for the Mind", "Naval Ravikant",
            "Philosophical reflections on wealth, happiness, and meditation.",
        )
        assert topic == "other"


class TestRelevanceScore:
    """Tests for relevance_score()."""

    def test_high_relevance_banking_ai(self, lustro):
        score = lustro["relevance_score"](
            "HKMA Issues AI Governance Framework for Banks",
            "HKMA Press Releases",
            "The HKMA has published AI governance requirements for banks "
            "covering model risk management and compliance.",
        )
        assert score > 20, f"Expected high relevance, got {score}"

    def test_low_relevance_tech(self, lustro):
        score = lustro["relevance_score"](
            "Django 6.0 Released",
            "Simon Willison",
            "Django 6.0 brings async improvements for web developers.",
        )
        assert score < 5, f"Expected low relevance, got {score}"

    def test_medium_relevance_regulation(self, lustro):
        score = lustro["relevance_score"](
            "FCA Consults on AI Model Risk",
            "UK FCA (AI/FS)",
            "The FCA published a consultation on AI model risk in banking.",
        )
        assert score > 10, f"Expected medium relevance, got {score}"


class TestExtractThemes:
    """Tests for extract_themes()."""

    def test_detects_generative_ai_theme(self, lustro):
        articles = [
            {"title": "GPT-5 Launch", "text": "OpenAI launches a new large language model "
             "with generative AI capabilities and foundation model improvements."},
        ]
        themes = lustro["extract_themes"](articles)
        labels = [t[0] for t in themes]
        assert "Generative AI / LLMs" in labels

    def test_detects_multiple_themes(self, lustro):
        articles = [
            {"title": "Banks Adopt AI", "text": "HSBC and other banks are deploying AI "
             "agents for fraud detection under new HKMA AI governance regulations."},
        ]
        themes = lustro["extract_themes"](articles)
        labels = [t[0] for t in themes]
        assert len(themes) >= 2

    def test_empty_articles(self, lustro):
        themes = lustro["extract_themes"]([])
        assert themes == []


class TestLoadArticles:
    """Tests for load_articles()."""

    def test_loads_json_files(self, lustro, article_dir):
        articles = lustro["load_articles"](article_dir)
        json_articles = [a for a in articles if a["file"].endswith(".json")]
        assert len(json_articles) == 4

    def test_loads_md_files(self, lustro, article_dir):
        articles = lustro["load_articles"](article_dir)
        md_articles = [a for a in articles if a["file"].endswith(".md")]
        assert len(md_articles) == 1

    def test_md_file_has_title(self, lustro, article_dir):
        articles = lustro["load_articles"](article_dir)
        md = [a for a in articles if a["file"].endswith(".md")][0]
        assert md["title"] == "Banking AI Trends Q1 2026"

    def test_json_file_has_all_fields(self, lustro, article_dir):
        articles = lustro["load_articles"](article_dir)
        art = [a for a in articles if "hkma" in a["file"]][0]
        assert art["title"] == "HKMA Issues AI Governance Framework for Banks"
        assert art["source"] == "HKMA Press Releases"
        assert art["date"] == "2026-03-02"
        assert "HKMA" in art["snippet"]

    def test_missing_dir_exits(self, lustro):
        with pytest.raises(SystemExit):
            lustro["load_articles"](Path("/nonexistent/path"))


class TestFormatSummaryTable:
    """Tests for format_summary_table()."""

    def test_contains_topic_headers(self, lustro, article_dir):
        articles = lustro["load_articles"](article_dir)
        for a in articles:
            a["topic"] = lustro["classify_topic"](a["title"], a["source"], a["text"])
        table = lustro["format_summary_table"](articles)
        for topic in lustro["TOPICS"]:
            assert topic in table

    def test_contains_total_count(self, lustro, article_dir):
        articles = lustro["load_articles"](article_dir)
        for a in articles:
            a["topic"] = lustro["classify_topic"](a["title"], a["source"], a["text"])
        table = lustro["format_summary_table"](articles)
        assert f"Total articles: {len(articles)}" in table


class TestFormatTopArticles:
    """Tests for format_top_articles()."""

    def test_respects_top_n(self, lustro, article_dir):
        articles = lustro["load_articles"](article_dir)
        for a in articles:
            a["topic"] = lustro["classify_topic"](a["title"], a["source"], a["text"])
            a["relevance"] = lustro["relevance_score"](a["title"], a["source"], a["text"])
        output = lustro["format_top_articles"](articles, 2)
        assert "TOP 2 ARTICLES" in output

    def test_banking_ai_article_ranks_first(self, lustro, article_dir):
        articles = lustro["load_articles"](article_dir)
        for a in articles:
            a["topic"] = lustro["classify_topic"](a["title"], a["source"], a["text"])
            a["relevance"] = lustro["relevance_score"](a["title"], a["source"], a["text"])
        output = lustro["format_top_articles"](articles, 3)
        assert "HKMA" in output.split("\n")[3]


class TestFormatThemes:
    """Tests for format_themes()."""

    def test_with_themes(self, lustro):
        themes = [("AI in banking / finance", 42), ("Generative AI / LLMs", 30)]
        output = lustro["format_themes"](themes)
        assert "AI in banking" in output
        assert "Generative AI" in output

    def test_empty_themes(self, lustro):
        output = lustro["format_themes"]([])
        assert "no significant themes" in output


class TestBuildParser:
    """Tests for CLI argument parser."""

    def test_default_args(self, lustro):
        parser = lustro["build_parser"]()
        args = parser.parse_args([])
        assert args.top == 20
        assert args.topic is None
        assert args.output is None

    def test_custom_args(self, lustro):
        parser = lustro["build_parser"]()
        args = parser.parse_args(["--top", "5", "--topic", "banking", "--output", "out.txt"])
        assert args.top == 5
        assert args.topic == "banking"
        assert args.output == "out.txt"
