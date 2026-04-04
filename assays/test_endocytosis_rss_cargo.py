from __future__ import annotations

from datetime import UTC, datetime

from metabolon.organelles.endocytosis_rss.cargo import (
    append_cargo,
    recall_cargo,
    recall_title_prefixes,
    rotate_cargo,
)


def _make_article(**overrides):
    base = {
        "timestamp": "2026-03-29T14:00:00+00:00",
        "date": "2026-03-29",
        "title": "Test Article",
        "source": "Test Source",
        "link": "https://example.com/test",
        "summary": "A test summary",
        "score": 5,
        "banking_angle": "N/A",
        "talking_point": "N/A",
        "fate": "store",
    }
    base.update(overrides)
    return base


def test_append_and_recall(tmp_path):
    cargo_path = tmp_path / "cargo.jsonl"
    articles = [
        _make_article(title="Article A", date="2026-03-28"),
        _make_article(title="Article B", date="2026-03-29"),
    ]
    append_cargo(cargo_path, articles)

    recalled = recall_cargo(cargo_path)
    assert len(recalled) == 2
    assert recalled[0]["title"] == "Article A"
    assert recalled[1]["title"] == "Article B"


def test_recall_with_date_range(tmp_path):
    cargo_path = tmp_path / "cargo.jsonl"
    articles = [
        _make_article(title="Old", date="2026-03-20"),
        _make_article(title="Recent", date="2026-03-28"),
        _make_article(title="Today", date="2026-03-29"),
    ]
    append_cargo(cargo_path, articles)

    recalled = recall_cargo(cargo_path, since="2026-03-27")
    assert len(recalled) == 2
    assert recalled[0]["title"] == "Recent"


def test_recall_with_month_filter(tmp_path):
    cargo_path = tmp_path / "cargo.jsonl"
    articles = [
        _make_article(title="February", date="2026-02-15"),
        _make_article(title="March", date="2026-03-15"),
    ]
    append_cargo(cargo_path, articles)

    recalled = recall_cargo(cargo_path, month="2026-03")
    assert len(recalled) == 1
    assert recalled[0]["title"] == "March"


def test_recall_title_prefixes(tmp_path):
    cargo_path = tmp_path / "cargo.jsonl"
    articles = [
        _make_article(title="The Future of Agent Systems: A Practical Guide"),
        _make_article(title="Banking AI Regulatory Update"),
    ]
    append_cargo(cargo_path, articles)

    prefixes = recall_title_prefixes(cargo_path)
    assert "the future agent systems practical guide" in prefixes
    assert "banking regulatory update" in prefixes


def test_rotate_cargo(tmp_path):
    cargo_path = tmp_path / "cargo.jsonl"
    archive_dir = tmp_path / "archive"
    articles = [
        _make_article(title="Old", date="2026-02-01"),
        _make_article(title="Recent", date="2026-03-28"),
    ]
    append_cargo(cargo_path, articles)

    now = datetime(2026, 3, 29, 12, 0, tzinfo=UTC)
    rotate_cargo(cargo_path, archive_dir, retain_days=14, now=now)

    remaining = recall_cargo(cargo_path)
    assert len(remaining) == 1
    assert remaining[0]["title"] == "Recent"

    archive_files = list(archive_dir.glob("*.jsonl"))
    assert len(archive_files) == 1
    archived = recall_cargo(archive_files[0])
    assert len(archived) == 1
    assert archived[0]["title"] == "Old"


def test_append_to_nonexistent(tmp_path):
    cargo_path = tmp_path / "subdir" / "cargo.jsonl"
    append_cargo(cargo_path, [_make_article()])
    assert cargo_path.exists()
    assert len(recall_cargo(cargo_path)) == 1


def test_recall_empty_file(tmp_path):
    cargo_path = tmp_path / "cargo.jsonl"
    assert recall_cargo(cargo_path) == []
