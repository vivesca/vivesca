from __future__ import annotations

"""Tests for engagement scoping tool."""


SAMPLE_RFP = """
Client: HSBC Asia Pacific
Engagement: AI Model Risk Management Framework Assessment

We are seeking a consulting team to assess our current AI/ML model risk management
framework against HKMA guidance and SR 11-7 requirements. The engagement should
deliver:

1. Gap analysis report comparing current framework to regulatory expectations
2. Target operating model for AI model validation
3. Implementation roadmap with prioritised recommendations
4. Training materials for model risk team

Timeline: 12 weeks
Budget: HK$2.5M
Team: 4-5 consultants including a senior banking AI specialist

Requirements:
- Experience with HKMA AI governance guidelines
- Python and machine learning expertise
- Model risk management certification preferred
- Agile delivery methodology
"""


def test_extract_timeline():
    from metabolon.organelles.engagement_scope import extract_timeline

    assert extract_timeline("The project runs for 12 weeks") == 12
    assert extract_timeline("3 month engagement") == 12
    assert extract_timeline("30 days") == 6
    assert extract_timeline("No timeline mentioned") is None


def test_extract_budget():
    from metabolon.organelles.engagement_scope import extract_budget

    assert extract_budget("Budget: HK$2.5M") != ""
    assert extract_budget("No budget info") == ""


def test_extract_deliverables():
    from metabolon.organelles.engagement_scope import extract_deliverables

    result = extract_deliverables(SAMPLE_RFP)
    assert len(result) >= 1


def test_extract_regulatory():
    from metabolon.organelles.engagement_scope import extract_regulatory_context

    result = extract_regulatory_context(SAMPLE_RFP)
    assert "HKMA" in result
    assert "SR 11-7" in result


def test_extract_skills():
    from metabolon.organelles.engagement_scope import extract_skills

    result = extract_skills(SAMPLE_RFP)
    assert "python" in result or "Python" in result
    assert "machine learning" in result or "agile" in result


def test_detect_engagement_type():
    from metabolon.organelles.engagement_scope import detect_engagement_type

    assert detect_engagement_type("We need an assessment of our framework") == "assessment"
    assert detect_engagement_type("Build and deploy a new system") == "implementation"
    assert detect_engagement_type("Advise on best practices") == "advisory"


def test_scope_engagement_full():
    from metabolon.organelles.engagement_scope import scope_engagement

    result = scope_engagement(SAMPLE_RFP, client="HSBC")
    assert result.client == "HSBC"
    assert result.timeline_weeks == 12
    assert len(result.regulatory_context) >= 1
    assert len(result.deliverables) >= 1
    assert isinstance(result.to_markdown(), str)
    assert "HSBC" in result.to_markdown()


def test_scope_result_to_markdown():
    from metabolon.organelles.engagement_scope import ScopeResult

    r = ScopeResult(client="Test", engagement_type="advisory", summary="Test engagement")
    md = r.to_markdown()
    assert "# Engagement Scope: Test" in md


def test_detect_risks_short_timeline():
    from metabolon.organelles.engagement_scope import ScopeResult, detect_risks

    scope = ScopeResult(client="X", engagement_type="advisory", summary="", timeline_weeks=2)
    risks = detect_risks("urgent delivery needed asap", scope)
    assert any(r.category == "timeline" for r in risks)


def test_risk_flag_dataclass():
    from metabolon.organelles.engagement_scope import RiskFlag

    rf = RiskFlag(category="scope_creep", description="too broad", severity="high")
    assert rf.severity == "high"
