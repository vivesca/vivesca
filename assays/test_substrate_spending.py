"""Tests for SpendingSubstrate (spending substrate)."""

from pathlib import Path
from metabolon.metabolism.substrates.spending import SpendingSubstrate


def test_name():
    """Verify substrate name is correct."""
    s = SpendingSubstrate()
    assert s.name == "spending"


def test_init_default():
    """Test default initialization uses SPENDING_DIR."""
    from metabolon.locus import spending
    s = SpendingSubstrate()
    assert s.spending_dir == spending


def test_init_custom_dir():
    """Test initialization with custom directory."""
    custom_dir = Path("/tmp/custom")
    s = SpendingSubstrate(spending_dir=custom_dir)
    assert s.spending_dir == custom_dir


def test_sense_empty_dir(tmp_path):
    """Test sense returns empty for empty directory."""
    s = SpendingSubstrate(spending_dir=tmp_path)
    assert s.sense() == []


def test_sense_skips_summary_files(tmp_path):
    """Test sense skips files ending with -summary.md."""
    (tmp_path / "2026-03-summary.md").write_text("---\nbank: HSBC\n---\ndata")
    s = SpendingSubstrate(spending_dir=tmp_path)
    assert s.sense() == []


def test_sense_skips_no_frontmatter(tmp_path):
    """Test sense skips files without frontmatter."""
    (tmp_path / "2026-03-HSBC.md").write_text("No frontmatter here\nJust plain text\n")
    s = SpendingSubstrate(spending_dir=tmp_path)
    assert s.sense() == []


def test_sense_parses_frontmatter(tmp_path):
    """Test sense parses YAML-like frontmatter from markdown."""
    md = tmp_path / "2026-03-HSBC.md"
    md.write_text("---\nbank: HSBC\ntotal: -5000.00\naccount: checking\n---\nBody text\n")
    s = SpendingSubstrate(spending_dir=tmp_path)
    result = s.sense()
    assert len(result) == 1
    assert result[0]["file"] == "2026-03-HSBC.md"
    assert result[0]["meta"]["bank"] == "HSBC"
    assert result[0]["meta"]["total"] == "-5000.00"
    assert result[0]["meta"]["account"] == "checking"


def test_sense_parses_categories(tmp_path):
    """Test sense extracts category totals from markdown table."""
    md = tmp_path / "2026-03-HSBC.md"
    md.write_text(
        "---\nbank: HSBC\n---\n"
        "| Category | Count | Total |\n"
        "| -------- | ----- | ----- |\n"
        "| Food | 15 | -3,200.50 |\n"
        "| Transport | 8 | -1,100.00 |\n"
        "| Dining | 12 | -850.75 |\n"
    )
    s = SpendingSubstrate(spending_dir=tmp_path)
    result = s.sense()
    assert len(result) == 1
    categories = result[0]["categories"]
    assert categories["Food"] == -3200.50
    assert categories["Transport"] == -1100.00
    assert categories["Dining"] == -850.75


def test_sense_skips_bold_category_headers(tmp_path):
    """Test sense skips bold category rows (section headers)."""
    md = tmp_path / "2026-03-HSBC.md"
    md.write_text(
        "---\nbank: HSBC\n---\n"
        "| **Food** | 15 | -3200.50 |\n"
    )
    s = SpendingSubstrate(spending_dir=tmp_path)
    result = s.sense()
    assert "**Food**" not in result[0]["categories"]
    assert len(result[0]["categories"]) == 0


def test_candidates_needs_at_least_two_months():
    """Test candidates requires at least two months of data."""
    s = SpendingSubstrate()
    assert s.candidates([{"categories": {"Food": -100}}]) == []
    assert s.candidates([]) == []


def test_candidates_flags_large_spending_increase():
    """Test candidates flags categories with >30% spending increase."""
    s = SpendingSubstrate()
    prior = {"categories": {"Food": -1000}}
    recent = {"categories": {"Food": -1500}}
    cands = s.candidates([prior, recent])
    assert len(cands) >= 1
    assert cands[0]["category"] == "Food"
    # 50% increase ->  50% flux delta negative
    assert cands[0]["flux_delta"] == -50.0


def test_candidates_no_flag_when_small_change(tmp_path):
    """Test candidates doesn't flag <30% changes."""
    s = SpendingSubstrate()
    prior = {"categories": {"Food": -1000}}
    recent = {"categories": {"Food": -1100}}
    cands = s.candidates([prior, recent])
    assert len(cands) == 0


def test_candidates_handles_new_categories(tmp_path):
    """Test candidates doesn't flag new categories (prior_amount 0)."""
    s = SpendingSubstrate()
    prior = {"categories": {}}
    recent = {"categories": {"NewCategory": -100}}
    cands = s.candidates([prior, recent])
    assert len(cands) == 0


def test_candidates_handles_positive_refunds(tmp_path):
    """Test candidates handles positive amounts (refunds/income)."""
    s = SpendingSubstrate()
    prior = {"categories": {"Income": 1000}}
    recent = {"categories": {"Income": 500}}
    cands = s.candidates([prior, recent])
    # Doesn't flag since amount is not < 0 (spending increase means more negative)
    assert len(cands) == 0


def test_act_formats_proposal_correctly():
    """Test act formats a human-readable proposal string."""
    s = SpendingSubstrate()
    candidate = {
        "category": "Food",
        "flux_delta": -50.0,
        "prior": -1000,
        "current": -1500
    }
    result = s.act(candidate)
    assert "Review Food" in result
    assert "-50%" in result
    assert "(-1,000 -> -1,500 HKD)" in result


def test_report_basic():
    """Test report includes basic information."""
    s = SpendingSubstrate()
    report = s.report([{"file": "a.md"}, {"file": "b.md"}], ["Review Food"])
    assert "2 statement(s)" in report
    assert "Proposals:" in report
    assert "Review Food" in report


def test_report_no_actions():
    """Test report works when there are no actions."""
    s = SpendingSubstrate()
    report = s.report([{"file": "a.md"}], [])
    assert "1 statement" in report
    assert "Proposals" not in report


def test_sense_sorts_files_correctly(tmp_path):
    """Test sense returns files in sorted order."""
    (tmp_path / "2026-01-statement.md").write_text("---\nbank: X\n---\n")
    (tmp_path / "2026-03-statement.md").write_text("---\nbank: X\n---\n")
    (tmp_path / "2026-02-statement.md").write_text("---\nbank: X\n---\n")
    s = SpendingSubstrate(spending_dir=tmp_path)
    result = s.sense()
    assert len(result) == 3
    assert result[0]["file"] == "2026-01-statement.md"
    assert result[1]["file"] == "2026-02-statement.md"
    assert result[2]["file"] == "2026-03-statement.md"
