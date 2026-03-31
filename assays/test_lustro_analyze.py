from __future__ import annotations
"""Tests for lustro-analyze — article classification and ranking effector."""

import json
import subprocess
import textwrap
from pathlib import Path

import pytest


def _load_module():
    """Load lustro-analyze by exec-ing its source."""
    source = open("/home/terry/germline/effectors/lustro-analyze").read()
    ns: dict = {"__name__": "lustro_analyze"}
    exec(source, ns)
    return ns


_mod = _load_module()

classify_topic = _mod["classify_topic"]
relevance_score = _mod["relevance_score"]
extract_themes = _mod["extract_themes"]
load_articles = _mod["load_articles"]
format_summary_table = _mod["format_summary_table"]
format_top_articles = _mod["format_top_articles"]
format_themes = _mod["format_themes"]
build_parser = _mod["build_parser"]
TOPICS = _mod["TOPICS"]


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture()
def tmp_article_dir(tmp_path):
    """Create a temp directory with mixed article files."""
    # JSON article — banking + AI
    (tmp_path / "bank_ai.json").write_text(json.dumps({
        "title": "Banks Adopt LLMs for Trading",
        "source": "Evident",
        "date": "2026-03-10",
        "text": "JPMorgan and Goldman Sachs use large language models for "
                "trading and risk management in banking.",
    }))

    # JSON article — pure AI
    (tmp_path / "pure_ai.json").write_text(json.dumps({
        "title": "OpenAI Releases GPT-5.4",
        "source": "TechCrunch",
        "date": "2026-03-12",
        "text": "OpenAI announces new foundation model with improved reasoning "
                "and NLP benchmarks for generative AI.",
    }))

    # JSON article — regulation
    (tmp_path / "regulation.json").write_text(json.dumps({
        "title": "FCA Updates AI Regulation for Financial Services",
        "source": "UK FCA",
        "date": "2026-03-08",
        "text": "The FCA issued new regulatory guidance on AI governance, "
                "compliance, and supervision for financial services.",
    }))

    # JSON article — technology (no AI/banking keywords)
    (tmp_path / "tech.json").write_text(json.dumps({
        "title": "New Kubernetes Monitoring Tool",
        "source": "DevOps Weekly",
        "date": "2026-03-05",
        "text": "A new open source tool for monitoring kubernetes clusters "
                "with improved observability and ci/cd integration.",
    }))

    # Markdown article — generic
    (tmp_path / "2026-03-01_notes.md").write_text(textwrap.dedent("""\
        # Random Startup Notes
        Some notes about venture capital and startup culture.
        Nothing specific about banking or AI here.
    """))

    # Non-article file (should be skipped)
    (tmp_path / "readme.txt").write_text("not an article")

    return tmp_path


@pytest.fixture()
def classified_articles(tmp_article_dir):
    """Load articles, classify and score them — ready for formatting."""
    articles = load_articles(tmp_article_dir)
    for a in articles:
        a["topic"] = classify_topic(a["title"], a["source"], a["text"])
        a["relevance"] = relevance_score(a["title"], a["source"], a["text"])
    return articles


# ── classify_topic ────────────────────────────────────────────────────


class TestClassifyTopic:
    def test_pure_ai_article(self):
        assert classify_topic(
            "OpenAI Releases GPT-5.4", "TechCrunch",
            "The new foundation model improves generative AI capabilities.",
        ) == "AI"

    def test_banking_article(self):
        assert classify_topic(
            "HSBC Deploys AI in Lending", "Evident",
            "HSBC uses machine learning for lending and credit decisions.",
        ) == "banking"

    def test_regulation_article(self):
        result = classify_topic(
            "FCA AI Regulation Update", "UK FCA",
            "The FCA issued new regulatory guidance on governance, compliance, "
            "supervision, and enforcement of data protection legislation.",
        )
        assert result == "regulation"

    def test_technology_article(self):
        assert classify_topic(
            "New Kubernetes Tool", "DevOps Weekly",
            "A new open source tool for monitoring kubernetes clusters "
            "with devops and ci/cd integration.",
        ) == "technology"

    def test_no_keywords_is_other(self):
        assert classify_topic(
            "Random Musing", "Personal Blog",
            "Today I walked to the park and saw a bird sitting on a fence.",
        ) == "other"

    def test_classify_uses_first_2000_chars(self):
        """Classification only examines first 2000 chars of text."""
        long_text = "x" * 2000 + " bank banking lending credit fintech"
        result = classify_topic("Boring Title", "Boring Source", long_text)
        assert result == "other"


# ── relevance_score ───────────────────────────────────────────────────


class TestRelevanceScore:
    def test_banking_ai_scores_high(self):
        score = relevance_score(
            "Banks Use AI for Fraud Detection", "Evident",
            "JPMorgan and HSBC deploy AI models for banking compliance "
            "and risk management in financial services.",
        )
        assert score >= 10.0, f"Expected high score, got {score}"

    def test_pure_ai_scores_moderate(self):
        score = relevance_score(
            "GPT-5.4 Released", "TechCrunch",
            "The new foundation model shows improvements in generative AI.",
        )
        assert score >= 1.0

    def test_irrelevant_scores_low(self):
        score = relevance_score(
            "Weather Report", "Local News",
            "Expect clear skies across the region today.",
        )
        assert score < 1.0

    def test_source_bonus(self):
        """Known finance sources get bonus score."""
        score_evident = relevance_score("Update", "Evident Banking Brief", "Minor update.")
        score_generic = relevance_score("Update", "Random Blog", "Minor update.")
        assert score_evident > score_generic

    def test_banking_weight_double_ai(self):
        """Banking keywords weigh 2x vs AI at 1.5x."""
        score_bank = relevance_score(
            "Banking News", "Generic",
            "bank banking financial services lending credit trading.",
        )
        score_ai = relevance_score(
            "AI News", "Generic",
            "artificial intelligence llm gpt claude transformer chatbot.",
        )
        assert score_bank > score_ai


# ── load_articles ─────────────────────────────────────────────────────


class TestLoadArticles:
    def test_loads_json_and_md(self, tmp_article_dir):
        articles = load_articles(tmp_article_dir)
        filenames = [a["file"] for a in articles]
        assert "bank_ai.json" in filenames
        assert "pure_ai.json" in filenames
        assert "regulation.json" in filenames
        assert "tech.json" in filenames
        assert "2026-03-01_notes.md" in filenames
        assert "readme.txt" not in filenames
        assert len(articles) == 5

    def test_article_has_required_keys(self, tmp_article_dir):
        articles = load_articles(tmp_article_dir)
        for a in articles:
            assert "file" in a
            assert "title" in a
            assert "source" in a
            assert "date" in a
            assert "snippet" in a
            assert "text" in a

    def test_json_snippet_truncated(self, tmp_article_dir):
        articles = load_articles(tmp_article_dir)
        for a in articles:
            if a["file"].endswith(".json"):
                assert len(a["snippet"]) <= 200

    def test_md_extracts_date_from_filename(self, tmp_article_dir):
        articles = load_articles(tmp_article_dir)
        md = [a for a in articles if a["file"] == "2026-03-01_notes.md"][0]
        assert md["date"] == "2026-03-01"

    def test_md_extracts_title_from_heading(self, tmp_path):
        (tmp_path / "notes.md").write_text("# My Great Article\n\nBody text.\n")
        articles = load_articles(tmp_path)
        assert articles[0]["title"] == "My Great Article"

    def test_md_no_heading_uses_first_line(self, tmp_path):
        (tmp_path / "notes.md").write_text("Just plain text here.\nMore lines.\n")
        articles = load_articles(tmp_path)
        assert articles[0]["title"] == "Just plain text here."

    def test_missing_dir_exits(self):
        """load_articles calls sys.exit(1) for missing directory."""
        with pytest.raises(SystemExit) as exc_info:
            load_articles(Path("/nonexistent/path/abc123"))
        assert exc_info.value.code == 1


# ── format_summary_table ──────────────────────────────────────────────


class TestFormatSummaryTable:
    def test_contains_headers(self, classified_articles):
        output = format_summary_table(classified_articles)
        assert "LUSTRO ARTICLE ANALYSIS SUMMARY" in output
        assert "Total articles:" in output

    def test_shows_topic_rows(self, classified_articles):
        output = format_summary_table(classified_articles)
        for topic in TOPICS:
            assert topic in output

    def test_shows_unique_sources(self, classified_articles):
        output = format_summary_table(classified_articles)
        assert "Unique sources:" in output


# ── format_top_articles ───────────────────────────────────────────────


class TestFormatTopArticles:
    def test_respects_n_limit(self, classified_articles):
        output = format_top_articles(classified_articles, top_n=2)
        numbered = [l for l in output.split("\n")
                    if l.strip() and l.strip()[0].isdigit() and "." in l[:5]]
        assert len(numbered) <= 2

    def test_shows_ranking_header(self, classified_articles):
        output = format_top_articles(classified_articles, top_n=3)
        assert "BANKING AI CONSULTING RELEVANCE" in output

    def test_shows_source_and_date(self, classified_articles):
        output = format_top_articles(classified_articles, top_n=1)
        assert "Source:" in output
        assert "Date:" in output

    def test_shows_topic(self, classified_articles):
        output = format_top_articles(classified_articles, top_n=1)
        assert "Topic:" in output


# ── extract_themes / format_themes ────────────────────────────────────


class TestThemes:
    def test_extract_returns_tuples(self, classified_articles):
        themes = extract_themes(classified_articles, top_n=5)
        assert isinstance(themes, list)
        for item in themes:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], str)
            assert isinstance(item[1], int)

    def test_detects_ai_theme(self, classified_articles):
        themes = extract_themes(classified_articles, top_n=15)
        labels = [t for t, _ in themes]
        assert any("LLM" in l or "Generative" in l for l in labels)

    def test_format_produces_header(self, classified_articles):
        themes = extract_themes(classified_articles)
        output = format_themes(themes)
        assert "KEY THEMES" in output

    def test_format_empty_themes(self):
        output = format_themes([])
        assert "no significant themes" in output


# ── build_parser ──────────────────────────────────────────────────────


class TestParser:
    def test_defaults(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert args.top == 20
        assert args.topic is None
        assert args.output is None
        assert args.dir is None

    def test_custom_args(self):
        parser = build_parser()
        args = parser.parse_args(["--top", "5", "--topic", "AI", "--output", "out.txt"])
        assert args.top == 5
        assert args.topic == "AI"
        assert args.output == "out.txt"


# ── CLI (subprocess) ──────────────────────────────────────────────────


class TestCLI:
    def test_help_flag(self):
        result = subprocess.run(
            ["python3", "/home/terry/germline/effectors/lustro-analyze", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "--top" in result.stdout
        assert "--topic" in result.stdout

    def test_cli_with_dir(self, tmp_article_dir):
        result = subprocess.run(
            ["python3", "/home/terry/germline/effectors/lustro-analyze",
             "--dir", str(tmp_article_dir), "--top", "3"],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0
        assert "LUSTRO ARTICLE ANALYSIS SUMMARY" in result.stdout
        assert "BANKING AI CONSULTING RELEVANCE" in result.stdout
        assert "KEY THEMES" in result.stdout

    def test_cli_topic_filter(self, tmp_article_dir):
        result = subprocess.run(
            ["python3", "/home/terry/germline/effectors/lustro-analyze",
             "--dir", str(tmp_article_dir), "--topic", "AI"],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0
        assert "LUSTRO ARTICLE ANALYSIS SUMMARY" in result.stdout

    def test_cli_output_file(self, tmp_article_dir, tmp_path):
        outfile = tmp_path / "report.txt"
        result = subprocess.run(
            ["python3", "/home/terry/germline/effectors/lustro-analyze",
             "--dir", str(tmp_article_dir), "--output", str(outfile)],
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0
        assert outfile.exists()
        content = outfile.read_text()
        assert "LUSTRO ARTICLE ANALYSIS SUMMARY" in content
