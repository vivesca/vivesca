"""Tests for case study packager."""

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


# Tests for generate_from_template (CAR framework)
def test_generate_from_template_basic():
    """Test basic CAR framework case study generation."""
    from metabolon.organelles.case_study import generate_from_template

    cs = generate_from_template(
        title="Digital Transformation Project",
        context="A legacy bank needed to modernize its core systems",
        action="Implemented cloud-native architecture with microservices",
        result="Reduced infrastructure costs by 40%",
    )

    assert cs.title == "Digital Transformation Project"
    assert cs.challenge == "A legacy bank needed to modernize its core systems"
    assert cs.approach == "Implemented cloud-native architecture with microservices"
    assert cs.result == "Reduced infrastructure costs by 40%"
    assert cs.metrics == []
    assert cs.anonymised is False


def test_generate_from_template_with_metrics():
    """Test CAR framework with metrics."""
    from metabolon.organelles.case_study import generate_from_template

    cs = generate_from_template(
        title="Risk Model Optimization",
        context="Credit risk models were underperforming",
        action="Developed ensemble approach combining XGBoost and neural networks",
        result="Improved model accuracy significantly",
        metrics=["40% accuracy improvement", "$1.2M annual savings", "3-month delivery"],
    )

    assert len(cs.metrics) == 3
    assert "40% accuracy improvement" in cs.metrics


def test_generate_from_template_with_domain_and_jurisdiction():
    """Test CAR framework with domain and jurisdiction."""
    from metabolon.organelles.case_study import generate_from_template

    cs = generate_from_template(
        title="RegTech Implementation",
        context="Manual compliance processes were unsustainable",
        action="Built automated regulatory reporting platform",
        result="95% reduction in reporting errors",
        domain="Regulatory Technology",
        jurisdiction="Singapore",
    )

    assert cs.domain == "Regulatory Technology"
    assert cs.jurisdiction == "Singapore"


def test_generate_from_template_to_executive_summary():
    """Test that generate_from_template output can produce executive summary."""
    from metabolon.organelles.case_study import generate_from_template

    cs = generate_from_template(
        title="API Gateway Migration",
        context="Legacy API gateway was causing performance issues",
        action="Migrated to cloud-native API management platform",
        result="99.9% uptime achieved",
    )

    summary = cs.to_executive_summary()
    assert "API Gateway Migration" in summary
    assert "performance issues" in summary
    assert "cloud-native" in summary
    assert "99.9% uptime" in summary


def test_generate_from_template_to_car_arc():
    """Test that generate_from_template output produces correct CAR arc."""
    from metabolon.organelles.case_study import generate_from_template

    cs = generate_from_template(
        title="Data Lake Implementation",
        context="Siloed data across 50+ systems",
        action="Built unified data lake with real-time ingestion",
        result="Data access time reduced from days to minutes",
        metrics=["50+ systems integrated", "10x faster queries"],
    )

    arc = cs.to_car_arc()
    # Note: to_car_arc uses Challenge/Approach/Result labels
    assert "# Data Lake Implementation" in arc
    assert "## Challenge" in arc
    assert "Siloed data across 50+ systems" in arc
    assert "## Approach" in arc
    assert "Built unified data lake" in arc
    assert "## Result" in arc
    assert "Data access time reduced" in arc
    assert "## Key Metrics" in arc
    assert "50+ systems integrated" in arc


def test_generate_from_template_to_slide_notes():
    """Test that generate_from_template output can produce slide notes."""
    from metabolon.organelles.case_study import generate_from_template

    cs = generate_from_template(
        title="KYC Automation",
        context="Manual KYC taking 5 days per customer",
        action="Deployed ML-powered document processing",
        result="Average KYC time reduced to 2 hours",
    )

    notes = cs.to_slide_notes()
    assert "**KYC Automation**" in notes
    assert "Challenge:" in notes
    assert "Result:" in notes


def test_generate_from_template_car_semantics():
    """Test that CAR semantics are correctly mapped (Context→Challenge, Action→Approach)."""
    from metabolon.organelles.case_study import generate_from_template

    # CAR: Context, Action, Result
    # Internal: challenge, approach, result
    cs = generate_from_template(
        title="Cloud Migration",
        context="On-premise datacenter reaching end-of-life",
        action="Migrated to AWS with containerization",
        result="50% cost reduction achieved",
    )

    # Context maps to challenge
    assert cs.challenge == "On-premise datacenter reaching end-of-life"
    # Action maps to approach
    assert cs.approach == "Migrated to AWS with containerization"
    # Result stays as result
    assert cs.result == "50% cost reduction achieved"
