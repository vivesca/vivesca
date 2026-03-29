from __future__ import annotations

from datetime import UTC, datetime

from metabolon.organelles.endocytosis_rss.log import (
    _title_prefix,
    cycle_log,
    generate_daily_markdown,
    is_noise,
    record_cargo,
    serialize_markdown,
)


def test_title_prefix():
    result = _title_prefix("The Future of Agent Systems: A Practical Guide")
    assert result == "the future agent systems practical guide"


def test_is_noise():
    assert is_noise("subscribe") is True
    assert is_noise("tiny") is True
    assert is_noise("A substantial technical update about inference latency") is False


def test_serialize_markdown():
    results = {
        "Example": [
            {
                "title": "Article 1",
                "date": "2026-02-24",
                "summary": "Summary text",
                "link": "https://example.com/a1",
            }
        ]
    }

    md = serialize_markdown(results, "2026-02-24")

    assert "## 2026-02-24 (Automated Daily Scan)" in md
    assert "### Example" in md
    assert "- **[Article 1](https://example.com/a1)** (2026-02-24) — Summary text" in md


def test_serialize_markdown_high_relevance_marker():
    results = {
        "Example": [
            {
                "title": "Banking launch",
                "date": "2026-02-24",
                "summary": "Summary text",
                "link": "https://example.com/bank",
                "score": "8",
                "banking_angle": "Directly relevant to regulated deployments",
            }
        ]
    }

    md = serialize_markdown(results, "2026-02-24")

    assert (
        "- [★] **[Banking launch](https://example.com/bank)**"
        " (banking_angle: Directly relevant to regulated deployments)"
        " (2026-02-24) — Summary text"
    ) in md


def test_record_cargo_with_marker(tmp_path):
    log_path = tmp_path / "news.md"
    log_path.write_text("# Header\n\n<!-- News entries below -->\n", encoding="utf-8")

    record_cargo(log_path, "## 2026-02-24 (Automated Daily Scan)")

    content = log_path.read_text(encoding="utf-8")
    assert "<!-- News entries below -->\n\n## 2026-02-24 (Automated Daily Scan)" in content


def test_record_cargo_without_marker(tmp_path):
    log_path = tmp_path / "news.md"
    log_path.write_text("# Header\n", encoding="utf-8")

    record_cargo(log_path, "## 2026-02-24 (Automated Daily Scan)")

    content = log_path.read_text(encoding="utf-8")
    assert content.endswith("\n\n## 2026-02-24 (Automated Daily Scan)")


def test_generate_daily_markdown(tmp_path):
    from metabolon.organelles.endocytosis_rss.cargo import append_cargo

    cargo_path = tmp_path / "cargo.jsonl"
    append_cargo(cargo_path, [
        {
            "timestamp": "2026-03-29T14:00:00+00:00",
            "date": "2026-03-29",
            "title": "Banking AI Update",
            "source": "FT",
            "link": "https://ft.com/article",
            "summary": "Banks adopt AI",
            "score": 8,
            "banking_angle": "Direct impact",
            "talking_point": "Meeting line",
            "fate": "transcytose",
        },
    ])

    md = generate_daily_markdown(cargo_path, "2026-03-29")
    assert "## 2026-03-29" in md
    assert "### FT" in md
    assert "[Banking AI Update](https://ft.com/article)" in md
    assert "[★]" in md  # transcytose marker


def test_cycle_log(tmp_path):
    log_path = tmp_path / "AI News Log.md"
    archive_dir = tmp_path / "archive"

    content = "\n".join(
        [
            "# AI News Log",
            "<!-- News entries below -->",
            "## 2026-02-20 (Automated Daily Scan)",
            "- old",
            "## 2026-02-09 (Automated Daily Scan)",
            "- older",
        ]
    )
    log_path.write_text(content + "\n", encoding="utf-8")

    now = datetime(2026, 2, 24, 12, 0, tzinfo=UTC)
    cycle_log(log_path, archive_dir, max_lines=4, now=now)

    rotated = log_path.read_text(encoding="utf-8")
    assert "## 2026-02-09" not in rotated

    archive_file = archive_dir / "AI News Log - Archive 2026-02.md"
    assert archive_file.exists()
    archived = archive_file.read_text(encoding="utf-8")
    assert "## 2026-02-09" in archived
