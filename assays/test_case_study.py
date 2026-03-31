"""Tests for case study packager."""
from pathlib import Path
import pytest

SAMPLE_USE_CASE = """---
domain: banking-ai
jurisdiction: Hong Kong
maturity: candidate
---

# AI Model Validation Framework for Retail Banking

## Challenge
A major Hong Kong bank needed to validate 200+ ML models used in credit scoring,
fraud detection, and customer segmentation. Current validation was manual, taking
6 months per model with no standardised methodology.

## Approach
Designed a tiered validation framework:
- Tier 1 (Critical): Full independent validation with challenger models
- Tier 2 (Material): Automated statistical tests with human review
- Tier 3 (Low-risk): Automated monitoring with exception-based review

Reduced validation cycle from 6 months to 6 weeks for Tier 2/3 models.

## Result
- 70% reduction in validation cycle time
- $2.5M annual cost savings from automation
- HKMA compliance achieved ahead of deadline
- Framework adopted by 3 other business units
"""

def test_extract_section():
    from metabolon.organelles.case_study import _extract_section
    result = _extract_section(SAMPLE_USE_CASE, "Challenge")
    assert "Hong Kong bank" in result
    assert "200+ ML models" in result

def test_extract_metrics():
    from metabolon.organelles.case_study import _extract_metrics
    result = _extract_metrics(SAMPLE_USE_CASE)
    assert any("70%" in m for m in result)

def test_anonymise():
    from metabolon.organelles.case_study import _anonymise
    result = _anonymise("HSBC needs to comply with HKMA guidelines")
    assert "HSBC" not in result
    assert "Major International Bank" in result

def test_package_use_case(tmp_path):
    from metabolon.organelles.case_study import package_use_case
    f = tmp_path / "test-case.md"
    f.write_text(SAMPLE_USE_CASE)
    result = package_use_case(f)
    assert "AI Model Validation" in result.title
    assert result.challenge != ""
    assert result.approach != ""
    assert result.result != ""
    assert result.domain == "banking-ai"

def test_package_use_case_anonymised(tmp_path):
    from metabolon.organelles.case_study import package_use_case
    f = tmp_path / "test-case.md"
    f.write_text(SAMPLE_USE_CASE)
    result = package_use_case(f, anonymise=True)
    assert result.anonymised is True

def test_package_missing_file():
    from metabolon.organelles.case_study import package_use_case
    result = package_use_case("/nonexistent/file.md")
    assert "not found" in result.challenge.lower()

def test_case_study_to_car_arc(tmp_path):
    from metabolon.organelles.case_study import package_use_case
    f = tmp_path / "test.md"
    f.write_text(SAMPLE_USE_CASE)
    cs = package_use_case(f)
    arc = cs.to_car_arc()
    assert "## Challenge" in arc
    assert "## Approach" in arc
    assert "## Result" in arc

def test_case_study_to_executive_summary(tmp_path):
    from metabolon.organelles.case_study import package_use_case
    f = tmp_path / "test.md"
    f.write_text(SAMPLE_USE_CASE)
    cs = package_use_case(f)
    summary = cs.to_executive_summary()
    assert isinstance(summary, str)
    assert len(summary) > 50

def test_case_study_to_slide_notes(tmp_path):
    from metabolon.organelles.case_study import package_use_case
    f = tmp_path / "test.md"
    f.write_text(SAMPLE_USE_CASE)
    cs = package_use_case(f)
    notes = cs.to_slide_notes()
    assert "Challenge:" in notes
    assert "Result:" in notes

def test_list_use_cases():
    from metabolon.organelles.case_study import list_use_cases
    result = list_use_cases()
    assert isinstance(result, list)
