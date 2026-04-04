from __future__ import annotations

"""Comprehensive tests for metabolon.organelles.engagement_scope.

Covers all public functions, edge cases, branch logic, and to_markdown output.
"""


from metabolon.organelles.engagement_scope import (
    RiskFlag,
    ScopeResult,
    detect_engagement_type,
    detect_risks,
    extract_budget,
    extract_deliverables,
    extract_regulatory_context,
    extract_skills,
    extract_timeline,
    scope_engagement,
)

# ── extract_timeline ──────────────────────────────────────────────


class TestExtractTimeline:
    def test_weeks(self):
        assert extract_timeline("12 weeks engagement") == 12

    def test_weeks_singular(self):
        assert extract_timeline("1 week") == 1

    def test_weeks_abbreviation(self):
        assert extract_timeline("6 wks timeline") == 6

    def test_months_converted_to_weeks(self):
        assert extract_timeline("3 month project") == 12

    def test_days_converted_to_weeks(self):
        assert extract_timeline("10 days") == 2

    def test_days_less_than_one_week_rounds_up(self):
        assert extract_timeline("3 days") == 1  # max(1, 3//5) = max(1,0) = 1

    def test_sprints_converted_to_weeks(self):
        assert extract_timeline("4 sprints") == 8

    def test_first_match_wins(self):
        # "6 weeks" appears before "3 months"
        assert extract_timeline("6 weeks, then 3 months later") == 6

    def test_no_match_returns_none(self):
        assert extract_timeline("no time info here") is None

    def test_case_insensitive(self):
        assert extract_timeline("8 WEEKS") == 8

    def test_zero_value(self):
        assert extract_timeline("0 weeks") == 0


# ── extract_budget ────────────────────────────────────────────────


class TestExtractBudget:
    def test_dollar_amount(self):
        assert extract_budget("budget of $500k") != ""

    def test_hk_dollar(self):
        result = extract_budget("Budget: HK$2.5M")
        assert result != ""

    def test_pound(self):
        result = extract_budget("cost: £100k")
        assert result != ""

    def test_euro(self):
        result = extract_budget("fee €50,000")
        assert result != ""

    def test_budget_qualifier_low(self):
        result = extract_budget("low budget project")
        assert "low" in result.lower()

    def test_budget_qualifier_medium(self):
        result = extract_budget("medium budget engagement")
        assert "medium" in result.lower()

    def test_budget_qualifier_high(self):
        result = extract_budget("high budget initiative")
        assert "high" in result.lower()

    def test_no_budget_info(self):
        assert extract_budget("no money mentioned") == ""


# ── extract_deliverables ─────────────────────────────────────────


class TestExtractDeliverables:
    def test_numbered_list_after_deliverable(self):
        text = "Deliverables:\n1. Report\n2. Dashboard\n3. Training"
        result = extract_deliverables(text)
        assert len(result) >= 3

    def test_bulleted_list_after_output(self):
        text = "Outputs:\n- Gap analysis\n- Roadmap\n- Training docs"
        result = extract_deliverables(text)
        assert len(result) >= 1

    def test_milestone_section(self):
        text = "Milestone items:\n- Phase 1 review\n- Phase 2 delivery"
        result = extract_deliverables(text)
        assert len(result) >= 1

    def test_no_deliverable_section(self):
        text = "This project has no listed deliverables keyword."
        result = extract_deliverables(text)
        assert result == []

    def test_caps_section_header(self):
        text = "DELIVER:\n- Item A\n- Item B"
        result = extract_deliverables(text)
        assert len(result) >= 1


# ── extract_regulatory_context ────────────────────────────────────


class TestExtractRegulatoryContext:
    def test_hkma(self):
        assert "HKMA" in extract_regulatory_context("Subject to HKMA guidelines")

    def test_sfc(self):
        assert "SFC" in extract_regulatory_context("SFC licensing requirements")

    def test_mas(self):
        assert "MAS" in extract_regulatory_context("MAS technology risk guidelines")

    def test_basel(self):
        assert "Basel" in extract_regulatory_context("Basel III capital requirements")

    def test_gdpr(self):
        assert "GDPR" in extract_regulatory_context("GDPR data protection")

    def test_pci_dss(self):
        assert "PCI-DSS" in extract_regulatory_context("PCI-DSS compliance needed")

    def test_dora(self):
        assert "DORA" in extract_regulatory_context("EU DORA regulation")

    def test_multiple_regulations(self):
        text = "Must comply with HKMA, SFC, and GDPR requirements"
        result = extract_regulatory_context(text)
        assert len(result) >= 3

    def test_no_regulations(self):
        assert extract_regulatory_context("no regulations here") == []

    def test_case_insensitive_match(self):
        assert "AI governance" in extract_regulatory_context("ai governance framework")


# ── extract_skills ────────────────────────────────────────────────


class TestExtractSkills:
    def test_python(self):
        result = extract_skills("Requires Python programming")
        assert "python" in result

    def test_cloud(self):
        result = extract_skills("Cloud migration project")
        assert "cloud" in result

    def test_multiple_skills(self):
        text = "Needs Python, AWS, and Docker experience"
        result = extract_skills(text)
        assert "python" in result
        assert "aws" in result
        assert "docker" in result

    def test_no_skills(self):
        assert extract_skills("generic text with no skill keywords") == []

    def test_word_boundary(self):
        # "java" should not match "javascript"
        result = extract_skills("We use JavaScript frameworks")
        assert "java" not in result

    def test_banking(self):
        result = extract_skills("Banking sector experience required")
        assert "banking" in result


# ── detect_engagement_type ────────────────────────────────────────


class TestDetectEngagementType:
    def test_advisory(self):
        assert detect_engagement_type("Please advise on governance") == "advisory"

    def test_implementation(self):
        assert detect_engagement_type("Build and deploy the platform") == "implementation"

    def test_assessment(self):
        assert detect_engagement_type("Conduct an assessment of controls") == "assessment"

    def test_hybrid_implementation_advisory(self):
        # "implement" + "review" should trigger hybrid
        text = "Implement the system and review existing processes for gaps"
        assert detect_engagement_type(text) == "hybrid"

    def test_default_when_no_signals(self):
        assert detect_engagement_type("random text with no signals") == "advisory"

    def test_develop_is_implementation(self):
        assert detect_engagement_type("Develop a new risk engine") == "implementation"

    def test_audit_is_assessment(self):
        assert detect_engagement_type("Perform an audit of access controls") == "assessment"

    def test_migrate_is_implementation(self):
        assert detect_engagement_type("Migrate to cloud infrastructure") == "implementation"

    def test_evaluate_is_assessment(self):
        assert detect_engagement_type("Evaluate current vendor landscape") == "assessment"


# ── detect_risks ──────────────────────────────────────────────────


class TestDetectRisks:
    def _make_scope(self, **overrides):
        defaults = dict(
            client="Test",
            engagement_type="advisory",
            summary="test",
        )
        defaults.update(overrides)
        return ScopeResult(**defaults)

    def test_short_timeline_high_severity(self):
        scope = self._make_scope(timeline_weeks=2)
        risks = detect_risks("normal text", scope)
        timeline_risks = [r for r in risks if r.category == "timeline"]
        assert any(r.severity == "high" for r in timeline_risks)

    def test_urgency_language(self):
        scope = self._make_scope()
        risks = detect_risks("we need this ASAP please", scope)
        assert any(r.category == "timeline" and "urgency" in r.description.lower() for r in risks)

    def test_immediately_flagged(self):
        scope = self._make_scope()
        risks = detect_risks("start immediately", scope)
        assert any(r.category == "timeline" for r in risks)

    def test_many_deliverables_scope_creep(self):
        scope = self._make_scope(deliverables=[f"item {i}" for i in range(7)])
        risks = detect_risks("normal text", scope)
        assert any(r.category == "scope_creep" for r in risks)

    def test_few_deliverables_no_scope_risk(self):
        scope = self._make_scope(deliverables=["one item"])
        risks = detect_risks("normal text", scope)
        assert not any(r.category == "scope_creep" for r in risks)

    def test_multi_phase_scope_creep(self):
        scope = self._make_scope()
        risks = detect_risks("This is phase 1 of the engagement", scope)
        assert any(
            r.category == "scope_creep" and "multi-phase" in r.description.lower() for r in risks
        )

    def test_many_regulations_risk(self):
        scope = self._make_scope(regulatory_context=["HKMA", "SFC", "GDPR", "SOX"])
        risks = detect_risks("normal text", scope)
        assert any(r.category == "regulatory" for r in risks)

    def test_few_regulations_no_risk(self):
        scope = self._make_scope(regulatory_context=["HKMA"])
        risks = detect_risks("normal text", scope)
        assert not any(r.category == "regulatory" for r in risks)

    def test_large_team_resource_risk(self):
        scope = self._make_scope(team_size=15)
        risks = detect_risks("normal text", scope)
        assert any(r.category == "resource" for r in risks)

    def test_small_team_no_resource_risk(self):
        scope = self._make_scope(team_size=3)
        risks = detect_risks("normal text", scope)
        assert not any(r.category == "resource" for r in risks)

    def test_no_risks_clean_engagement(self):
        scope = self._make_scope(timeline_weeks=12, team_size=4, deliverables=["report"])
        risks = detect_risks("standard engagement text", scope)
        assert risks == []

    def test_combined_risks(self):
        scope = self._make_scope(
            timeline_weeks=2,
            deliverables=[f"item {i}" for i in range(7)],
            regulatory_context=["HKMA", "SFC", "GDPR", "SOX"],
            team_size=15,
        )
        risks = detect_risks("urgent asap phase 1 delivery", scope)
        categories = {r.category for r in risks}
        assert "timeline" in categories
        assert "scope_creep" in categories
        assert "regulatory" in categories
        assert "resource" in categories


# ── ScopeResult.to_markdown ──────────────────────────────────────


class TestScopeResultToMarkdown:
    def test_minimal_fields(self):
        r = ScopeResult(client="Acme", engagement_type="advisory", summary="Test scope")
        md = r.to_markdown()
        assert "# Engagement Scope: Acme" in md
        assert "**Type:** advisory" in md
        assert "**Summary:** Test scope" in md

    def test_timeline_in_output(self):
        r = ScopeResult(client="X", engagement_type="advisory", summary="s", timeline_weeks=8)
        assert "**Timeline:** 8 weeks" in r.to_markdown()

    def test_budget_in_output(self):
        r = ScopeResult(
            client="X", engagement_type="advisory", summary="s", budget_indicator="$500k"
        )
        assert "**Budget:** $500k" in r.to_markdown()

    def test_team_size_in_output(self):
        r = ScopeResult(client="X", engagement_type="advisory", summary="s", team_size=6)
        assert "**Team Size:** 6" in r.to_markdown()

    def test_deliverables_section(self):
        r = ScopeResult(
            client="X",
            engagement_type="advisory",
            summary="s",
            deliverables=["Report", "Dashboard"],
        )
        md = r.to_markdown()
        assert "## Deliverables" in md
        assert "- Report" in md
        assert "- Dashboard" in md

    def test_skills_section(self):
        r = ScopeResult(
            client="X", engagement_type="advisory", summary="s", required_skills=["Python", "AWS"]
        )
        md = r.to_markdown()
        assert "## Required Skills" in md
        assert "- Python" in md

    def test_regulatory_section(self):
        r = ScopeResult(
            client="X",
            engagement_type="advisory",
            summary="s",
            regulatory_context=["HKMA", "GDPR"],
        )
        md = r.to_markdown()
        assert "## Regulatory Context" in md
        assert "- HKMA" in md

    def test_risk_flags_section(self):
        rf = RiskFlag(category="timeline", description="Too short", severity="high")
        r = ScopeResult(client="X", engagement_type="advisory", summary="s", risk_flags=[rf])
        md = r.to_markdown()
        assert "## Risk Flags" in md
        assert "[HIGH] timeline: Too short" in md

    def test_empty_fields_omitted(self):
        r = ScopeResult(client="X", engagement_type="advisory", summary="s")
        md = r.to_markdown()
        assert "Timeline" not in md
        assert "Budget" not in md
        assert "Team Size" not in md
        assert "Deliverables" not in md
        assert "Required Skills" not in md
        assert "Regulatory Context" not in md
        assert "Risk Flags" not in md

    def test_zero_timeline_not_shown(self):
        r = ScopeResult(client="X", engagement_type="advisory", summary="s", timeline_weeks=0)
        md = r.to_markdown()
        # 0 is falsy so timeline line should be omitted
        assert "Timeline" not in md


# ── scope_engagement (integration) ───────────────────────────────


class TestScopeEngagement:
    SAMPLE = """
    Client: TestBank
    Advisory engagement for AI governance.

    We need you to advise on our model risk framework.
    Must comply with HKMA and MAS requirements.

    Deliverables:
    - Governance framework document
    - Policy templates
    - Training materials

    Timeline: 8 weeks
    Budget: $200k

    Required: Python, machine learning, risk management experience.
    """

    def test_client_name(self):
        result = scope_engagement(self.SAMPLE, client="TestBank")
        assert result.client == "TestBank"

    def test_default_client(self):
        result = scope_engagement("some text")
        assert result.client == "Unknown"

    def test_engagement_type_detected(self):
        result = scope_engagement(self.SAMPLE)
        assert result.engagement_type in ("advisory", "assessment", "implementation", "hybrid")

    def test_timeline_extracted(self):
        result = scope_engagement(self.SAMPLE)
        assert result.timeline_weeks == 8

    def test_budget_extracted(self):
        result = scope_engagement(self.SAMPLE)
        assert result.budget_indicator != ""

    def test_regulatory_extracted(self):
        result = scope_engagement(self.SAMPLE)
        assert "HKMA" in result.regulatory_context
        assert "MAS" in result.regulatory_context

    def test_skills_extracted(self):
        result = scope_engagement(self.SAMPLE)
        assert "python" in result.required_skills

    def test_deliverables_extracted(self):
        result = scope_engagement(self.SAMPLE)
        assert len(result.deliverables) >= 1

    def test_raw_text_stored(self):
        result = scope_engagement(self.SAMPLE)
        assert result.raw_text == self.SAMPLE

    def test_summary_is_first_200_chars(self):
        result = scope_engagement(self.SAMPLE)
        assert len(result.summary) <= 200

    def test_risks_populated(self):
        result = scope_engagement(self.SAMPLE)
        assert isinstance(result.risk_flags, list)

    def test_to_markdown_works(self):
        result = scope_engagement(self.SAMPLE)
        md = result.to_markdown()
        assert "TestBank" in md
        assert isinstance(md, str)


# ── RiskFlag dataclass ───────────────────────────────────────────


class TestRiskFlag:
    def test_fields(self):
        rf = RiskFlag(category="scope_creep", description="Too broad", severity="high")
        assert rf.category == "scope_creep"
        assert rf.description == "Too broad"
        assert rf.severity == "high"

    def test_all_severities(self):
        for sev in ("low", "medium", "high"):
            rf = RiskFlag(category="x", description="y", severity=sev)
            assert rf.severity == sev


# ── Edge cases ────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_text(self):
        result = scope_engagement("")
        assert result.client == "Unknown"
        assert result.summary == ""
        assert result.timeline_weeks is None
        assert result.budget_indicator == ""
        assert result.deliverables == []
        assert result.regulatory_context == []
        assert result.required_skills == []
        assert result.risk_flags == []

    def test_very_long_text(self):
        text = "advisory " * 5000
        result = scope_engagement(text, client="LongClient")
        assert result.client == "LongClient"
        assert len(result.summary) <= 200

    def test_unicode_text(self):
        text = "Engagement for 客户 with €50k budget over 4 weeks"
        result = scope_engagement(text)
        assert result.timeline_weeks == 4
