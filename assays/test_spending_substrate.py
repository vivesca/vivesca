"""Tests for SpendingSubstrate."""

from metabolon.metabolism.substrates.spending import SpendingSubstrate


def test_spending_substrate_name():
    s = SpendingSubstrate()
    assert s.name == "spending"


def test_sense_empty_dir(tmp_path):
    s = SpendingSubstrate(spending_dir=tmp_path)
    assert s.sense() == []


def test_sense_skips_summary(tmp_path):
    (tmp_path / "2026-03-summary.md").write_text("---\nbank: HSBC\n---\ndata")
    s = SpendingSubstrate(spending_dir=tmp_path)
    assert s.sense() == []


def test_sense_parses_frontmatter(tmp_path):
    md = tmp_path / "2026-03-HSBC.md"
    md.write_text("---\nbank: HSBC\ntotal: -5000.00\n---\nBody text\n")
    s = SpendingSubstrate(spending_dir=tmp_path)
    result = s.sense()
    assert len(result) == 1
    assert result[0]["meta"]["bank"] == "HSBC"


def test_sense_parses_categories(tmp_path):
    md = tmp_path / "2026-03-HSBC.md"
    md.write_text(
        "---\nbank: HSBC\n---\n"
        "| Category | Count | Total |\n"
        "| Food | 15 | -3,200.50 |\n"
        "| Transport | 8 | -1,100.00 |\n"
    )
    s = SpendingSubstrate(spending_dir=tmp_path)
    result = s.sense()
    assert len(result) == 1
    assert result[0]["categories"]["Food"] == -3200.50
    assert result[0]["categories"]["Transport"] == -1100.00


def test_candidates_needs_two_months(tmp_path):
    s = SpendingSubstrate(spending_dir=tmp_path)
    assert s.candidates([{"categories": {"Food": -100}}]) == []


def test_candidates_flags_increase(tmp_path):
    s = SpendingSubstrate(spending_dir=tmp_path)
    prior = {"categories": {"Food": -1000}}
    recent = {"categories": {"Food": -2000}}
    cands = s.candidates([prior, recent])
    assert len(cands) >= 1
    assert cands[0]["category"] == "Food"


def test_candidates_no_flag_when_stable(tmp_path):
    s = SpendingSubstrate(spending_dir=tmp_path)
    prior = {"categories": {"Food": -1000}}
    recent = {"categories": {"Food": -1100}}
    cands = s.candidates([prior, recent])
    assert len(cands) == 0


def test_act_formats_proposal():
    s = SpendingSubstrate()
    result = s.act({"category": "Food", "flux_delta": -50.0, "prior": -1000, "current": -1500})
    assert "Food" in result
    assert "-50%" in result


def test_report_basic():
    s = SpendingSubstrate()
    report = s.report([{"file": "a.md"}], ["Review Food"])
    assert "1 statement" in report
    assert "Review Food" in report


def test_report_no_actions():
    s = SpendingSubstrate()
    report = s.report([{"file": "a.md"}, {"file": "b.md"}], [])
    assert "2 statement" in report
    assert "Proposals" not in report
