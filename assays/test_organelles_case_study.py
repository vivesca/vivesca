from __future__ import annotations

"""Tests for metabolon.organelles.case_study."""

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.organelles.case_study import (
    CaseStudy,
    _anonymise,
    _extract_metrics,
    _extract_section,
    generate_from_template,
    list_use_cases,
    package_use_case,
)


# ---------------------------------------------------------------------------
# CaseStudy dataclass
# ---------------------------------------------------------------------------

class TestCaseStudyConstruction:
    def test_defaults(self):
        cs = CaseStudy(title="T", challenge="C", approach="A", result="R")
        assert cs.metrics == []
        assert cs.domain == ""
        assert cs.jurisdiction == ""
        assert cs.source_file == ""
        assert cs.anonymised is False

    def test_all_fields(self):
        cs = CaseStudy(
            title="T",
            challenge="C",
            approach="A",
            result="R",
            metrics=["m1", "m2"],
            domain="Banking",
            jurisdiction="HK",
            source_file="/tmp/x.md",
            anonymised=True,
        )
        assert cs.metrics == ["m1", "m2"]
        assert cs.domain == "Banking"
        assert cs.jurisdiction == "HK"
        assert cs.source_file == "/tmp/x.md"
        assert cs.anonymised is True


# ---------------------------------------------------------------------------
# to_executive_summary
# ---------------------------------------------------------------------------

class TestExecutiveSummary:
    def test_basic(self):
        cs = CaseStudy(title="Alpha", challenge="big problem", approach="did X", result="won")
        summary = cs.to_executive_summary()
        assert summary.startswith("Alpha:")
        assert "big problem" in summary
        assert "did X" in summary
        assert "won" in summary

    def test_is_one_paragraph(self):
        cs = CaseStudy(title="T", challenge="C", approach="A", result="R")
        assert "\n\n" not in cs.to_executive_summary()


# ---------------------------------------------------------------------------
# to_car_arc
# ---------------------------------------------------------------------------

class TestCarArc:
    def test_basic_structure(self):
        cs = CaseStudy(title="Beta", challenge="hard", approach="clever", result="great")
        arc = cs.to_car_arc()
        assert "# Beta" in arc
        assert "## Challenge" in arc
        assert "## Approach" in arc
        assert "## Result" in arc
        assert "hard" in arc
        assert "clever" in arc
        assert "great" in arc

    def test_with_metrics(self):
        cs = CaseStudy(
            title="T", challenge="C", approach="A", result="R",
            metrics=["99% uptime", "$2M saved"],
        )
        arc = cs.to_car_arc()
        assert "## Key Metrics" in arc
        assert "- 99% uptime" in arc
        assert "- $2M saved" in arc

    def test_without_metrics(self):
        cs = CaseStudy(title="T", challenge="C", approach="A", result="R", metrics=[])
        arc = cs.to_car_arc()
        assert "## Key Metrics" not in arc


# ---------------------------------------------------------------------------
# to_slide_notes
# ---------------------------------------------------------------------------

class TestSlideNotes:
    def test_basic(self):
        cs = CaseStudy(
            title="Gamma",
            challenge="x" * 200,
            approach="y" * 200,
            result="z" * 200,
        )
        notes = cs.to_slide_notes()
        assert "**Gamma**" in notes
        # Truncated to 100 chars
        for line in notes.split("\n"):
            if line.startswith("Challenge:"):
                assert len(line) <= len("Challenge: ") + 100
                break

    def test_with_metrics_shows_max_three(self):
        cs = CaseStudy(
            title="T", challenge="C", approach="A", result="R",
            metrics=["m1", "m2", "m3", "m4"],
        )
        notes = cs.to_slide_notes()
        assert "m1" in notes
        assert "m2" in notes
        assert "m3" in notes
        assert "m4" not in notes

    def test_without_metrics(self):
        cs = CaseStudy(title="T", challenge="C", approach="A", result="R")
        notes = cs.to_slide_notes()
        assert "Metrics:" not in notes


# ---------------------------------------------------------------------------
# _extract_section
# ---------------------------------------------------------------------------

class TestExtractSection:
    def test_finds_heading(self):
        md = textwrap.dedent("""\
        # Title
        ## Challenge
        The big challenge here.
        ## Approach
        Do things.
        """)
        assert _extract_section(md, "Challenge") == "The big challenge here."

    def test_case_insensitive(self):
        md = "## CHALLENGE\nSome text.\n"
        assert _extract_section(md, "challenge") == "Some text."

    def test_missing_heading_returns_empty(self):
        assert _extract_section("no headings here", "Challenge") == ""

    def test_heading_with_hashes(self):
        md = "### Challenge\nContent with multiple lines.\nLine two.\n"
        result = _extract_section(md, "Challenge")
        assert "Content with multiple lines." in result


# ---------------------------------------------------------------------------
# _extract_metrics
# ---------------------------------------------------------------------------

class TestExtractMetrics:
    def test_percentage(self):
        text = "We achieved a 45% reduction in costs."
        metrics = _extract_metrics(text)
        assert any("45%" in m for m in metrics)

    def test_currency(self):
        text = "The project saved $2,500,000 in year one."
        metrics = _extract_metrics(text)
        assert len(metrics) >= 1

    def test_max_ten(self):
        # Generate 15 percentage matches
        text = " ".join(f"Saw {i}% improvement." for i in range(15))
        assert len(_extract_metrics(text)) <= 10

    def test_no_metrics(self):
        assert _extract_metrics("Nothing quantitative here.") == []


# ---------------------------------------------------------------------------
# _anonymise
# ---------------------------------------------------------------------------

class TestAnonymise:
    def test_replaces_hsbc(self):
        assert "[Major International Bank]" in _anonymise("HSBC was involved")

    def test_replaces_standard_chartered(self):
        assert "[Regional Bank]" in _anonymise("Standard Chartered approved")

    def test_replaces_capco(self):
        assert "[Consulting Partner]" in _anonymise("Capco delivered")

    def test_replaces_cncbi(self):
        assert "[Previous Employer]" in _anonymise("CNCBI supported")

    def test_case_insensitive(self):
        assert "[Major International Bank]" in _anonymise("hsbc and HSBC")

    def test_no_replacement_when_clean(self):
        text = "Generic consulting work"
        assert _anonymise(text) == text


# ---------------------------------------------------------------------------
# package_use_case
# ---------------------------------------------------------------------------

class TestPackageUseCase:
    def test_file_not_found(self, tmp_path):
        missing = tmp_path / "nonexistent.md"
        cs = package_use_case(missing)
        assert cs.title == "nonexistent"
        assert cs.challenge == "File not found"
        assert cs.source_file == str(missing)

    def test_basic_markdown(self, tmp_path):
        md = textwrap.dedent("""\
        # My Case Study
        ## Challenge
        Tough problem to solve.
        ## Approach
        Applied novel methods.
        ## Result
        Outstanding success.
        """)
        p = tmp_path / "case.md"
        p.write_text(md, encoding="utf-8")
        cs = package_use_case(p)
        assert cs.title == "My Case Study"
        assert "Tough problem" in cs.challenge
        assert "novel methods" in cs.approach
        assert "Outstanding success" in cs.result
        assert cs.source_file == str(p)
        assert cs.anonymised is False

    def test_anonymise_flag(self, tmp_path):
        md = "# HSBC Project\n## Challenge\nHSBC needed help.\n## Approach\nWe acted.\n## Result\nDone.\n"
        p = tmp_path / "hsbc.md"
        p.write_text(md, encoding="utf-8")
        cs = package_use_case(p, anonymise=True)
        assert "[Major International Bank]" in cs.title
        assert cs.anonymised is True

    def test_fallback_headings(self, tmp_path):
        md = textwrap.dedent("""\
        # Title
        ## Problem
        The issue.
        ## Solution
        The fix.
        ## Outcome
        The gain.
        """)
        p = tmp_path / "alt.md"
        p.write_text(md, encoding="utf-8")
        cs = package_use_case(p)
        assert "The issue." in cs.challenge
        assert "The fix." in cs.approach
        assert "The gain." in cs.result

    def test_paragraph_fallback(self, tmp_path):
        md = textwrap.dedent("""\
        # No Sections

        This is the first paragraph and it is longer than thirty characters for sure.

        This is the second paragraph which is also definitely longer than thirty characters.

        This is the third paragraph that similarly exceeds the thirty character minimum length.
        """)
        p = tmp_path / "plain.md"
        p.write_text(md, encoding="utf-8")
        cs = package_use_case(p)
        assert "first paragraph" in cs.challenge
        assert "second paragraph" in cs.approach
        assert "third paragraph" in cs.result

    def test_extracts_domain_and_jurisdiction(self, tmp_path):
        md = textwrap.dedent("""\
        # T
        domain: Banking
        jurisdiction: HK
        ## Challenge
        C
        ## Approach
        A
        ## Result
        R
        """)
        p = tmp_path / "meta.md"
        p.write_text(md, encoding="utf-8")
        cs = package_use_case(p)
        assert cs.domain == "Banking"
        assert cs.jurisdiction == "HK"

    def test_title_fallback_to_stem(self, tmp_path):
        md = "No heading here but some text."
        p = tmp_path / "my_file.md"
        p.write_text(md, encoding="utf-8")
        cs = package_use_case(p)
        assert cs.title == "my_file"

    def test_metrics_extraction(self, tmp_path):
        md = textwrap.dedent("""\
        # Title
        ## Challenge
        A 30% reduction was needed.
        ## Approach
        We did things.
        ## Result
        Achieved 50% savings.
        """)
        p = tmp_path / "metrics.md"
        p.write_text(md, encoding="utf-8")
        cs = package_use_case(p)
        assert len(cs.metrics) >= 1


# ---------------------------------------------------------------------------
# generate_from_template
# ---------------------------------------------------------------------------

class TestGenerateFromTemplate:
    def test_basic(self):
        cs = generate_from_template(
            title="T", context="ctx", action="act", result="res",
        )
        assert cs.title == "T"
        assert cs.challenge == "ctx"
        assert cs.approach == "act"
        assert cs.result == "res"
        assert cs.metrics == []
        assert cs.source_file == ""
        assert cs.anonymised is False

    def test_with_all_params(self):
        cs = generate_from_template(
            title="T",
            context="c",
            action="a",
            result="r",
            metrics=["m1"],
            domain="FinTech",
            jurisdiction="SG",
        )
        assert cs.metrics == ["m1"]
        assert cs.domain == "FinTech"
        assert cs.jurisdiction == "SG"


# ---------------------------------------------------------------------------
# list_use_cases
# ---------------------------------------------------------------------------

class TestListUseCases:
    def test_dir_not_exists(self):
        with patch("metabolon.organelles.case_study.USE_CASE_DIR") as mock_dir:
            mock_dir.exists.return_value = False
            assert list_use_cases() == []

    def test_lists_md_files(self, tmp_path):
        (tmp_path / "case_a.md").write_text("# A")
        (tmp_path / "case_b.md").write_text("# B")
        (tmp_path / "notes.txt").write_text("ignore me")
        with patch("metabolon.organelles.case_study.USE_CASE_DIR", tmp_path):
            cases = list_use_cases()
        assert len(cases) == 2
        assert cases[0]["filename"] == "case_a.md"
        assert cases[1]["filename"] == "case_b.md"
        assert cases[0]["title"] == "case_a"

    def test_empty_dir(self, tmp_path):
        with patch("metabolon.organelles.case_study.USE_CASE_DIR", tmp_path):
            assert list_use_cases() == []
