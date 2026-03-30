from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from metabolon.organelles.endocytosis_rss.config import restore_config
from metabolon.organelles.endocytosis_rss.digest import (
    _resolve_week_label,
    metabolize_digest,
    metabolize_weekly,
    recall_log_entries,
    secrete_weekly_digest,
)


def _write_month_data(cfg, month: str):
    cfg.article_cache_dir.mkdir(parents=True, exist_ok=True)
    article = {
        "title": "Agent frameworks harden for enterprise adoption",
        "date": f"{month}-24",
        "source": "Example Source",
        "summary": "A short summary",
        "link": "https://example.com/post",
        "text": "Full text body for clustering.",
    }
    path = cfg.article_cache_dir / f"{month}-24_example_abc12345.json"
    path.write_text(json.dumps(article), encoding="utf-8")

    cfg.log_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.log_path.write_text(
        "\n".join(
            [
                f"## {month}-24 (Automated Daily Scan)",
                "### Example Log Source",
                "- [★] **[AI regulation update](https://example.com/reg)**"
                " (banking_angle: Material for bank governance discussions)"
                " (2026-02-24) — New policy activity",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _fake_llm_call_factory(outputs: list[str]):
    """Return a fake _llm_call that pops from outputs sequentially."""
    def _fake(model, system, user):
        return outputs.pop(0)
    return _fake


def test_metabolize_digest_dry_run_with_mock_llm(xdg_env, monkeypatch):
    cfg = restore_config()
    _write_month_data(cfg, "2026-02")

    fake = _fake_llm_call_factory([
        json.dumps([
            {
                "theme": "Agentic orchestration for enterprise ops",
                "description": "Teams are moving from simple chat to workflow agents.",
                "article_indices": [0, 1],
                "banking_relevance": "Impacts ops and compliance design.",
            }
        ])
    ])
    monkeypatch.setattr(
        "metabolon.organelles.endocytosis_rss.digest._llm_call", fake,
    )

    themes, output_path = metabolize_digest(
        cfg,
        month="2026-02",
        dry_run=True,
        themes=5,
        model="gemini-3.1-flash",
    )

    assert output_path is None
    assert len(themes) == 1
    assert themes[0]["theme"] == "Agentic orchestration for enterprise ops"


def test_cmd_digest_writes_output_file(xdg_env, monkeypatch):
    cfg = restore_config()
    _write_month_data(cfg, "2026-02")

    fake = _fake_llm_call_factory([
        json.dumps([
            {
                "theme": "Regulatory pressure on model governance",
                "description": "Banks need stronger controls and evidence trails.",
                "article_indices": [0, 1],
                "banking_relevance": "Model risk and governance requirements increase.",
            }
        ]),
        "## Regulatory pressure on model governance\n\n"
        "### Summary\nTighter controls are becoming mandatory.",
    ])
    monkeypatch.setattr(
        "metabolon.organelles.endocytosis_rss.digest._llm_call", fake,
    )

    _themes_result, output_path = metabolize_digest(
        cfg=cfg,
        month="2026-02",
        dry_run=False,
        themes=8,
        model="gemini-3.1-flash",
    )

    assert output_path is not None
    output_file = cfg.digest_output_dir / "2026-02 AI Thematic Digest.md"
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "# AI Thematic Digest — 2026-02" in content
    assert "## Regulatory pressure on model governance" in content


# ---------------------------------------------------------------------------
# Weekly digest tests
# ---------------------------------------------------------------------------


def _write_weekly_log(cfg, log_date: str) -> None:
    """Seed the JSONL cargo store with a mix of transcytose and plain items."""
    from metabolon.organelles.endocytosis_rss.cargo import append_cargo

    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    cfg.cargo_path.parent.mkdir(parents=True, exist_ok=True)
    append_cargo(cfg.cargo_path, [
        {
            "timestamp": f"{log_date}T12:00:00+00:00",
            "date": log_date,
            "title": "Claude 3.7 Sonnet released",
            "source": "Anthropic Blog",
            "link": "https://anthropic.com/news/claude-3-7",
            "summary": "New extended thinking capability",
            "score": 8,
            "banking_angle": "Major model upgrade for enterprise deployments",
            "talking_point": "N/A",
            "fate": "transcytose",
        },
        {
            "timestamp": f"{log_date}T12:00:00+00:00",
            "date": log_date,
            "title": "Weekly AI roundup",
            "source": "The Batch",
            "link": "https://deeplearning.ai/batch",
            "summary": "Summary of this week in AI",
            "score": 5,
            "banking_angle": "N/A",
            "talking_point": "N/A",
            "fate": "store",
        },
        {
            "timestamp": f"{log_date}T12:00:00+00:00",
            "date": log_date,
            "title": "LLM tool use patterns",
            "source": "Simon Willison",
            "link": "https://simonwillison.net/llm-tool-use",
            "summary": "Practical patterns for tool-calling agents",
            "score": 8,
            "banking_angle": "Agentic workflows for operations automation",
            "talking_point": "N/A",
            "fate": "transcytose",
        },
    ])


def test_resolve_week_label_returns_correct_format():
    """_resolve_week_label returns YYYY-WNN label and 7-day window."""
    anchor = datetime(2026, 3, 25, 12, 0, 0, tzinfo=UTC)  # Wednesday W13
    since, until, label = _resolve_week_label(anchor)
    assert label == "2026-W13"
    assert until == "2026-03-25"
    assert since == "2026-03-18"


def test_recall_log_entries_parses_transcytose_and_plain(xdg_env):
    """recall_log_entries distinguishes transcytose from plain entries."""
    cfg = restore_config()
    _write_weekly_log(cfg, "2026-03-24")

    entries = recall_log_entries(cfg.cargo_path, "2026-03-20")
    assert len(entries) == 3

    transcytose = [e for e in entries if e["_transcytose"] == "1"]
    plain = [e for e in entries if e["_transcytose"] == "0"]
    assert len(transcytose) == 2
    assert len(plain) == 1

    titles = [e["title"] for e in transcytose]
    assert "Claude 3.7 Sonnet released" in titles
    assert "LLM tool use patterns" in titles


def test_recall_log_entries_filters_by_date(xdg_env):
    """recall_log_entries excludes entries before since_date."""
    from metabolon.organelles.endocytosis_rss.cargo import append_cargo

    cfg = restore_config()
    cfg.cargo_path.parent.mkdir(parents=True, exist_ok=True)
    append_cargo(cfg.cargo_path, [
        {
            "timestamp": "2026-03-10T12:00:00+00:00",
            "date": "2026-03-10",
            "title": "Old article",
            "source": "Old Source",
            "link": "https://example.com/old",
            "summary": "Old news",
            "score": 5,
            "banking_angle": "N/A",
            "talking_point": "N/A",
            "fate": "store",
        },
        {
            "timestamp": "2026-03-22T12:00:00+00:00",
            "date": "2026-03-22",
            "title": "New article",
            "source": "New Source",
            "link": "https://example.com/new",
            "summary": "Fresh signal",
            "score": 8,
            "banking_angle": "N/A",
            "talking_point": "N/A",
            "fate": "transcytose",
        },
    ])
    # Only entries on or after 2026-03-20 should be returned
    entries = recall_log_entries(cfg.cargo_path, "2026-03-20")
    assert len(entries) == 1
    assert entries[0]["title"] == "New article"


def test_secrete_weekly_digest_creates_file_with_transcytose_section(tmp_path):
    """secrete_weekly_digest secretes transcytose section and per-source grouping."""
    output_path = tmp_path / "weekly-ai-digest-2026-W13.md"
    entries = [
        {
            "title": "Claude 3.7 Sonnet released",
            "source": "Anthropic Blog",
            "date": "2026-03-24",
            "link": "https://anthropic.com/news/claude-3-7",
            "banking_angle": "Major model upgrade for enterprise deployments",
            "summary": "New extended thinking capability",
            "_transcytose": "1",
        },
        {
            "title": "Weekly AI roundup",
            "source": "The Batch",
            "date": "2026-03-24",
            "link": "https://deeplearning.ai/batch",
            "banking_angle": "",
            "summary": "Summary of this week",
            "_transcytose": "0",
        },
    ]
    # Affinity index provides scores — transcytose item scores 8, plain scores 6
    affinity_index = {
        "Claude 3.7 Sonnet released": {
            "score": 8,
            "banking_angle": "Major model upgrade for enterprise deployments",
            "talking_point": "Ask clients about their model upgrade cadence.",
        },
        "Weekly AI roundup": {
            "score": 6,
            "banking_angle": "N/A",
            "talking_point": "N/A",
        },
    }

    result = secrete_weekly_digest(
        output_path=output_path,
        week_label="2026-W13",
        since_date="2026-03-18",
        until_date="2026-03-25",
        entries=entries,
        affinity_index=affinity_index,
    )

    assert result == output_path
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")

    assert "# Weekly AI Digest — 2026-W13" in content
    assert "Period: 2026-03-18 to 2026-03-25" in content
    assert "## Transcytose" in content
    assert "Claude 3.7 Sonnet released" in content
    assert "Ask clients about their model upgrade cadence." in content
    assert "## By Source" in content
    assert "### Anthropic Blog" in content
    assert "### The Batch" in content
    # Scheduling comment is present
    assert "Sunday" in content


def test_secrete_weekly_digest_omits_low_score_items(tmp_path):
    """Items with score < WEEKLY_STORE_THRESHOLD are dropped (lysosomal fate)."""
    from metabolon.organelles.endocytosis_rss.digest import WEEKLY_STORE_THRESHOLD

    output_path = tmp_path / "weekly-ai-digest-2026-W13.md"
    entries = [
        {
            "title": "Low signal item",
            "source": "Noisy Blog",
            "date": "2026-03-24",
            "link": "https://example.com/noisy",
            "banking_angle": "",
            "summary": "Not relevant",
            "_transcytose": "0",
        },
    ]
    affinity_index = {
        "Low signal item": {
            "score": WEEKLY_STORE_THRESHOLD - 1,  # Below threshold — lysosomal fate
            "banking_angle": "N/A",
            "talking_point": "N/A",
        },
    }

    secrete_weekly_digest(
        output_path=output_path,
        week_label="2026-W13",
        since_date="2026-03-18",
        until_date="2026-03-25",
        entries=entries,
        affinity_index=affinity_index,
    )

    content = output_path.read_text(encoding="utf-8")
    assert "Low signal item" not in content
    assert "No items met the score threshold" in content


def test_metabolize_weekly_returns_count_and_path(xdg_env, monkeypatch, tmp_path):
    """metabolize_weekly writes file and returns correct item count."""
    cfg = restore_config()
    _write_weekly_log(cfg, "2026-03-24")

    # Point output to tmp_path (metabolize_weekly uses ~/epigenome/chromatin/euchromatin)
    notes_ref = tmp_path / "code" / "epigenome" / "chromatin" / "Reference"
    notes_ref.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("metabolon.organelles.endocytosis_rss.digest.Path.home", lambda: tmp_path)

    # Stub out affinity log loading so no external files needed
    monkeypatch.setattr(
        "metabolon.organelles.endocytosis_rss.digest.recall_affinity_entries", lambda _since: []
    )

    item_count, output_path = metabolize_weekly(cfg=cfg)

    # Two ★ items were logged; without affinity scores they pass via transcytose flag
    assert item_count >= 2
    assert output_path is not None
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "# Weekly AI Digest" in content


def test_cli_digest_weekly_flag(xdg_env, monkeypatch, tmp_path):
    """lustro digest --weekly routes to the weekly secretion pathway."""
    from typer.testing import CliRunner

    from metabolon.organelles.endocytosis_rss.cli import app

    cfg = restore_config()
    _write_weekly_log(cfg, "2026-03-24")

    called: dict[str, bool] = {"weekly": False}

    def fake_run_weekly(cfg, week_date=None, tags=None, dry_run=False):
        called["weekly"] = True
        out = tmp_path / "weekly-ai-digest-2026-W13.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("# Weekly AI Digest — 2026-W13\n", encoding="utf-8")
        return 3, out

    import metabolon.organelles.endocytosis_rss.digest as _digest_mod

    monkeypatch.setattr(_digest_mod, "metabolize_weekly", fake_run_weekly)

    runner = CliRunner()
    result = runner.invoke(app, ["digest", "--weekly"])

    assert result.exit_code == 0, result.output
    assert called["weekly"]
    assert "Weekly digest" in result.output or "Written" in result.output
