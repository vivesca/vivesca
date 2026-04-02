"""Tests for metabolon.metabolism.substrates.spending."""
from __future__ import annotations

from pathlib import Path

import pytest

from metabolon.metabolism.substrates.spending import SpendingSubstrate


def _write_statement(tmp: Path, filename: str, categories: dict[str, float], meta: dict[str, str] | None = None) -> Path:
    """Helper to create a minimal statement markdown file."""
    if meta is None:
        meta = {"bank": "test", "statement_date": filename[:7]}
    lines = ["---"]
    for k, v in meta.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Category | Count | Total (HKD) |")
    lines.append("|----------|-------|-------------|")
    for cat, total in categories.items():
        lines.append(f"| {cat} | 1 | {total:,.2f} |")
    lines.append(f"| **Total** | **1** | **{sum(categories.values()):,.2f}** |")
    p = tmp / filename
    p.write_text("\n".join(lines) + "\n")
    return p


class TestSense:
    def test_reads_statement_files(self, tmp_path):
        _write_statement(tmp_path, "2025-01-test.md", {"Food": -500.00})
        sub = SpendingSubstrate(spending_dir=tmp_path)
        results = sub.sense()
        assert len(results) == 1
        assert results[0]["file"] == "2025-01-test.md"
        assert results[0]["categories"]["Food"] == -500.00

    def test_skips_summary_files(self, tmp_path):
        _write_statement(tmp_path, "2025-01-test.md", {"Food": -500.00})
        _write_statement(tmp_path, "2025-01-summary.md", {"Food": -500.00})
        sub = SpendingSubstrate(spending_dir=tmp_path)
        results = sub.sense()
        assert len(results) == 1
        assert results[0]["file"] == "2025-01-test.md"

    def test_skips_files_without_frontmatter(self, tmp_path):
        (tmp_path / "2025-03-nofm.md").write_text("No frontmatter here\n")
        sub = SpendingSubstrate(spending_dir=tmp_path)
        results = sub.sense()
        assert results == []

    def test_extracts_meta_fields(self, tmp_path):
        _write_statement(
            tmp_path, "2025-02-test.md", {"Food": -200.00},
            meta={"bank": "hsbc", "statement_date": "2025-02-28"},
        )
        sub = SpendingSubstrate(spending_dir=tmp_path)
        results = sub.sense()
        assert results[0]["meta"]["bank"] == "hsbc"
        assert results[0]["meta"]["statement_date"] == "2025-02-28"

    def test_skips_bold_total_rows(self, tmp_path):
        """Bold total rows (| **Total** | ...) must not appear as categories."""
        _write_statement(tmp_path, "2025-04-test.md", {"Food": -100.00})
        sub = SpendingSubstrate(spending_dir=tmp_path)
        results = sub.sense()
        assert "**Total**" not in results[0]["categories"]

    def test_comma_separated_amounts(self, tmp_path):
        """Amounts with commas (e.g. -1,234.56) must parse correctly."""
        content = (
            "---\nbank: test\n---\n\n"
            "## Summary\n\n"
            "| Category | Count | Total (HKD) |\n"
            "|----------|-------|-------------|\n"
            "| Education | 1 | -1,234.56 |\n"
            "| **Total** | **1** | **-1,234.56** |\n"
        )
        (tmp_path / "2025-05-test.md").write_text(content)
        sub = SpendingSubstrate(spending_dir=tmp_path)
        results = sub.sense()
        assert results[0]["categories"]["Education"] == -1234.56


class TestCandidates:
    def test_flags_category_with_30pct_increase(self):
        sub = SpendingSubstrate()
        sensed = [
            {"file": "2025-01-test.md", "meta": {}, "categories": {"Food": -200.00}},
            {"file": "2025-02-test.md", "meta": {}, "categories": {"Food": -350.00}},
        ]
        cands = sub.candidates(sensed)
        assert len(cands) == 1
        assert cands[0]["category"] == "Food"
        # (-350 - (-200)) / |-200| * 100 = -75%
        assert cands[0]["flux_delta"] < -30

    def test_no_flag_for_stable_spending(self):
        sub = SpendingSubstrate()
        sensed = [
            {"file": "2025-01-test.md", "meta": {}, "categories": {"Food": -200.00}},
            {"file": "2025-02-test.md", "meta": {}, "categories": {"Food": -220.00}},
        ]
        cands = sub.candidates(sensed)
        assert cands == []

    def test_returns_empty_for_single_month(self):
        sub = SpendingSubstrate()
        sensed = [
            {"file": "2025-01-test.md", "meta": {}, "categories": {"Food": -500.00}},
        ]
        assert sub.candidates(sensed) == []

    def test_new_category_not_flagged(self):
        """A category present only in recent month is not flagged (prior_amount=0)."""
        sub = SpendingSubstrate()
        sensed = [
            {"file": "2025-01-test.md", "meta": {}, "categories": {"Food": -100.00}},
            {"file": "2025-02-test.md", "meta": {}, "categories": {"Travel": -500.00}},
        ]
        cands = sub.candidates(sensed)
        # Travel has no prior, Food is absent from recent — neither flagged
        assert cands == []


class TestAct:
    def test_formats_review_string(self):
        sub = SpendingSubstrate()
        candidate = {
            "category": "Tech/AI",
            "current": -3000.00,
            "prior": -1500.00,
            "flux_delta": -100.0,
        }
        result = sub.act(candidate)
        assert "Tech/AI" in result
        assert "-100%" in result
        assert "Review" in result


class TestReport:
    def test_report_with_no_proposals(self):
        sub = SpendingSubstrate()
        report = sub.report(sensed=[{"file": "a.md"}], acted=[])
        assert "1 statement(s)" in report

    def test_report_with_proposals(self):
        sub = SpendingSubstrate()
        report = sub.report(
            sensed=[{"file": "a.md"}, {"file": "b.md"}],
            acted=["Review Food: spending changed -75%"],
        )
        assert "2 statement(s)" in report
        assert "Proposals:" in report
        assert "Review Food" in report
