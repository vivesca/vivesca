"""Tests for endocytosis_rss/migration.py - markdown to JSONL migration."""

from pathlib import Path

from metabolon.organelles.endocytosis_rss.migration import migrate_markdown_to_jsonl


def test_migrate_empty_file(tmp_path):
    """Test migrate_markdown_to_jsonl returns 0 for nonexistent file."""
    result = migrate_markdown_to_jsonl(
        tmp_path / "nonexistent.md",
        tmp_path / "cargo.jsonl"
    )
    assert result == 0


def test_migrate_empty_markdown(tmp_path):
    """Test migrate_markdown_to_jsonl returns 0 for empty markdown."""
    md_path = tmp_path / "news.md"
    md_path.write_text("")
    
    result = migrate_markdown_to_jsonl(md_path, tmp_path / "cargo.jsonl")
    assert result == 0


def test_migrate_extracts_articles(tmp_path):
    """Test migrate_markdown_to_jsonl extracts articles from markdown."""
    md_path = tmp_path / "news.md"
    md_path.write_text(
        "## 2024-01-15\n"
        "### TechCrunch\n"
        "- **[Bitcoin Hits New High](https://example.com/btc)** — Price surged today\n"
        "- **[Ethereum Update](https://example.com/eth)** (2024-01-14) — Major upgrade\n"
    )
    cargo_path = tmp_path / "cargo.jsonl"
    
    result = migrate_markdown_to_jsonl(md_path, cargo_path)
    assert result == 2
    
    # Verify cargo was written
    import json
    lines = cargo_path.read_text().strip().split("\n")
    assert len(lines) == 2
    
    entry = json.loads(lines[0])
    assert entry["title"] == "Bitcoin Hits New High"
    assert entry["source"] == "TechCrunch"
    assert entry["link"] == "https://example.com/btc"


def test_migrate_handles_starred_articles(tmp_path):
    """Test migrate_markdown_to_jsonl marks starred articles as transcytose."""
    md_path = tmp_path / "news.md"
    md_path.write_text(
        "## 2024-01-15\n"
        "### Source\n"
        "- [★] **[Important Article](https://example.com)** — Key news\n"
    )
    cargo_path = tmp_path / "cargo.jsonl"
    
    migrate_markdown_to_jsonl(md_path, cargo_path)
    
    import json
    entry = json.loads(cargo_path.read_text().strip())
    assert entry["fate"] == "transcytose"
    assert entry["score"] == 7


def test_migrate_handles_unstarred_articles(tmp_path):
    """Test migrate_markdown_to_jsonl marks unstarred articles as store."""
    md_path = tmp_path / "news.md"
    md_path.write_text(
        "## 2024-01-15\n"
        "### Source\n"
        "- **[Regular Article](https://example.com)** — News\n"
    )
    cargo_path = tmp_path / "cargo.jsonl"
    
    migrate_markdown_to_jsonl(md_path, cargo_path)
    
    import json
    entry = json.loads(cargo_path.read_text().strip())
    assert entry["fate"] == "store"
    assert entry["score"] == 5


def test_migrate_handles_banking_angle(tmp_path):
    """Test migrate_markdown_to_jsonl extracts banking_angle."""
    md_path = tmp_path / "news.md"
    md_path.write_text(
        "## 2024-01-15\n"
        "### Source\n"
        "- **[Article](https://x.com)** (banking_angle: Payment rails) — News\n"
    )
    cargo_path = tmp_path / "cargo.jsonl"
    
    migrate_markdown_to_jsonl(md_path, cargo_path)
    
    import json
    entry = json.loads(cargo_path.read_text().strip())
    assert entry["banking_angle"] == "Payment rails"


def test_migrate_handles_date_in_parens(tmp_path):
    """Test migrate_markdown_to_jsonl extracts date from parentheses."""
    md_path = tmp_path / "news.md"
    md_path.write_text(
        "## 2024-01-15\n"
        "### Source\n"
        "- **[Article](https://x.com)** (2024-01-10) — Summary\n"
    )
    cargo_path = tmp_path / "cargo.jsonl"
    
    migrate_markdown_to_jsonl(md_path, cargo_path)
    
    import json
    entry = json.loads(cargo_path.read_text().strip())
    assert entry["date"] == "2024-01-10"


def test_migrate_uses_section_date(tmp_path):
    """Test migrate_markdown_to_jsonl uses section date when no inline date."""
    md_path = tmp_path / "news.md"
    md_path.write_text(
        "## 2024-01-15\n"
        "### Source\n"
        "- **[Article](https://x.com)** — Summary\n"
    )
    cargo_path = tmp_path / "cargo.jsonl"
    
    migrate_markdown_to_jsonl(md_path, cargo_path)
    
    import json
    entry = json.loads(cargo_path.read_text().strip())
    assert entry["date"] == "2024-01-15"


def test_migrate_handles_plain_title(tmp_path):
    """Test migrate_markdown_to_jsonl handles title without link."""
    md_path = tmp_path / "news.md"
    md_path.write_text(
        "## 2024-01-15\n"
        "### Source\n"
        "- **Plain Title Here** — Some summary\n"
    )
    cargo_path = tmp_path / "cargo.jsonl"
    
    migrate_markdown_to_jsonl(md_path, cargo_path)
    
    import json
    entry = json.loads(cargo_path.read_text().strip())
    assert entry["title"] == "Plain Title Here"
    assert entry["link"] == ""


def test_migrate_multiple_sources(tmp_path):
    """Test migrate_markdown_to_jsonl handles multiple source sections."""
    md_path = tmp_path / "news.md"
    md_path.write_text(
        "## 2024-01-15\n"
        "### FeedA\n"
        "- **[Article A](https://a.com)**\n"
        "### FeedB\n"
        "- **[Article B](https://b.com)**\n"
    )
    cargo_path = tmp_path / "cargo.jsonl"
    
    result = migrate_markdown_to_jsonl(md_path, cargo_path)
    assert result == 2
    
    import json
    lines = cargo_path.read_text().strip().split("\n")
    sources = [json.loads(line)["source"] for line in lines]
    assert "FeedA" in sources
    assert "FeedB" in sources


def test_migrate_skips_non_article_lines(tmp_path):
    """Test migrate_markdown_to_jsonl skips non-article lines."""
    md_path = tmp_path / "news.md"
    md_path.write_text(
        "## 2024-01-15\n"
        "Some random text\n"
        "### Source\n"
        "- Not a valid article line\n"
        "- **[Valid Article](https://x.com)**\n"
    )
    cargo_path = tmp_path / "cargo.jsonl"
    
    result = migrate_markdown_to_jsonl(md_path, cargo_path)
    assert result == 1


def test_migrate_appends_to_existing_cargo(tmp_path):
    """Test migrate_markdown_to_jsonl appends to existing cargo file."""
    cargo_path = tmp_path / "cargo.jsonl"
    
    # Write existing entry
    import json
    cargo_path.write_text(json.dumps({"title": "Existing"}) + "\n")
    
    md_path = tmp_path / "news.md"
    md_path.write_text(
        "## 2024-01-15\n"
        "### Source\n"
        "- **[New Article](https://x.com)**\n"
    )
    
    result = migrate_markdown_to_jsonl(md_path, cargo_path)
    assert result == 1
    
    lines = cargo_path.read_text().strip().split("\n")
    assert len(lines) == 2
