from __future__ import annotations

from metabolon.organelles.endocytosis_rss.migration import migrate_markdown_to_jsonl


def test_migrate_markdown_to_jsonl(tmp_path):
    md_path = tmp_path / "AI News Log.md"
    cargo_path = tmp_path / "cargo.jsonl"

    md_path.write_text(
        "# AI News Log\n"
        "<!-- News entries below -->\n\n"
        "## 2026-03-28 (Automated Daily Scan)\n\n"
        "### FT\n\n"
        "- [*] **[Banking AI](https://ft.com/a)** (banking_angle: Direct) (2026-03-28) -- Summary\n"
        "- **[Other Article](https://ft.com/b)** (2026-03-28) -- Other summary\n",
        encoding="utf-8",
    )

    count = migrate_markdown_to_jsonl(md_path, cargo_path)
    assert count == 2

    from metabolon.organelles.endocytosis_rss.cargo import recall_cargo

    entries = recall_cargo(cargo_path)
    assert len(entries) == 2
    assert entries[0]["title"] == "Banking AI"
    assert entries[0]["link"] == "https://ft.com/a"
    assert entries[0]["date"] == "2026-03-28"
    assert entries[0]["source"] == "FT"


def test_migrate_nonexistent_returns_zero(tmp_path):
    md_path = tmp_path / "nonexistent.md"
    cargo_path = tmp_path / "cargo.jsonl"
    count = migrate_markdown_to_jsonl(md_path, cargo_path)
    assert count == 0
    assert not cargo_path.exists()


def test_migrate_empty_log(tmp_path):
    md_path = tmp_path / "empty.md"
    md_path.write_text("# AI News Log\n\nNo articles yet.\n", encoding="utf-8")
    cargo_path = tmp_path / "cargo.jsonl"
    count = migrate_markdown_to_jsonl(md_path, cargo_path)
    assert count == 0


def test_migrate_preserves_transcytose_flag(tmp_path):
    md_path = tmp_path / "AI News Log.md"
    cargo_path = tmp_path / "cargo.jsonl"

    md_path.write_text(
        "## 2026-03-28 (Automated Daily Scan)\n\n"
        "### Reuters\n\n"
        "- [★] **[HKMA AI circular](https://reuters.com/a)** (banking_angle: Regulatory) (2026-03-28) -- Major update\n"
        "- **[Consumer app update](https://techblog.com/b)** (2026-03-28) -- Minor feature\n",
        encoding="utf-8",
    )

    count = migrate_markdown_to_jsonl(md_path, cargo_path)
    assert count == 2

    from metabolon.organelles.endocytosis_rss.cargo import recall_cargo

    entries = recall_cargo(cargo_path)
    transcytose = [e for e in entries if e["fate"] == "transcytose"]
    store = [e for e in entries if e["fate"] == "store"]
    assert len(transcytose) == 1
    assert len(store) == 1
    assert transcytose[0]["title"] == "HKMA AI circular"
