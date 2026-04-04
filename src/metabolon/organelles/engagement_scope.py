from __future__ import annotations

"""engagement_scope — structured engagement scoping from RFP/RFI text.

Extracts: scope, timeline, budget indicators, deliverables, regulatory context,
team requirements, and risk flags from unstructured engagement text.

Output is a structured ScopeResult suitable for SOW/proposal generation.
"""


import re
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class RiskFlag:
    category: str  # scope_creep, timeline, budget, regulatory, resource
    description: str
    severity: Literal["low", "medium", "high"]


@dataclass
class ScopeResult:
    client: str
    engagement_type: str  # advisory, implementation, assessment, hybrid
    summary: str
    deliverables: list[str] = field(default_factory=list)
    timeline_weeks: int | None = None
    budget_indicator: str = ""  # low/medium/high or specific range
    team_size: int | None = None
    required_skills: list[str] = field(default_factory=list)
    regulatory_context: list[str] = field(default_factory=list)
    risk_flags: list[RiskFlag] = field(default_factory=list)
    raw_text: str = ""

    def to_markdown(self) -> str:
        """Generate markdown summary for SOW drafting."""
        lines = [
            f"# Engagement Scope: {self.client}",
            f"\n**Type:** {self.engagement_type}",
            f"**Summary:** {self.summary}",
        ]
        if self.timeline_weeks:
            lines.append(f"**Timeline:** {self.timeline_weeks} weeks")
        if self.budget_indicator:
            lines.append(f"**Budget:** {self.budget_indicator}")
        if self.team_size:
            lines.append(f"**Team Size:** {self.team_size}")

        if self.deliverables:
            lines.append("\n## Deliverables")
            for d in self.deliverables:
                lines.append(f"- {d}")

        if self.required_skills:
            lines.append("\n## Required Skills")
            for s in self.required_skills:
                lines.append(f"- {s}")

        if self.regulatory_context:
            lines.append("\n## Regulatory Context")
            for r in self.regulatory_context:
                lines.append(f"- {r}")

        if self.risk_flags:
            lines.append("\n## Risk Flags")
            for rf in self.risk_flags:
                lines.append(f"- [{rf.severity.upper()}] {rf.category}: {rf.description}")

        return "\n".join(lines)


# ── Deterministic extractors ──────────────────────────────────

_TIMELINE_PATTERNS = [
    (r"(\d+)\s*(?:week|wk)s?", "weeks"),
    (r"(\d+)\s*(?:month)s?", "months"),
    (r"(\d+)\s*(?:day)s?", "days"),
    (r"(\d+)\s*(?:sprint)s?", "sprints"),
]

_BUDGET_PATTERNS = [
    r"(?:budget|cost|fee|price)\s*(?:of|:)?\s*[\$\£\€]?\s*([\d,\.]+\s*[kKmM]?)",
    r"[\$\£\€HK]\s*([\d,\.]+\s*[kKmM]?)",
    r"(low|medium|high)\s*budget",
]

_REGULATORY_KEYWORDS = [
    "HKMA",
    "SFC",
    "MAS",
    "BIS",
    "Basel",
    "BCBS",
    "GDPR",
    "PDPO",
    "SOX",
    "PCI-DSS",
    "ISO 27001",
    "DORA",
    "NIS2",
    "CPS 234",
    "model risk",
    "SR 11-7",
    "SS1/23",
    "AI governance",
    "explainability",
]

_ENGAGEMENT_TYPE_SIGNALS = {
    "advisory": ["advise", "advisory", "counsel", "recommend", "review"],
    "implementation": ["implement", "build", "develop", "deploy", "migrate", "integrate"],
    "assessment": [
        "assess",
        "assessment",
        "audit",
        "evaluate",
        "gap analysis",
        "maturity",
        "benchmark",
    ],
}

_SKILL_KEYWORDS = [
    "python",
    "java",
    "cloud",
    "aws",
    "azure",
    "gcp",
    "kubernetes",
    "docker",
    "machine learning",
    "AI",
    "NLP",
    "LLM",
    "data science",
    "analytics",
    "risk management",
    "compliance",
    "regulatory",
    "governance",
    "project management",
    "agile",
    "scrum",
    "devops",
    "ci/cd",
    "banking",
    "payments",
    "capital markets",
    "insurance",
    "wealth",
]


def extract_timeline(text: str) -> int | None:
    """Extract timeline in weeks from text."""
    for pattern, unit in _TIMELINE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = int(match.group(1))
            if unit == "months":
                return value * 4
            elif unit == "days":
                return max(1, value // 5)
            elif unit == "sprints":
                return value * 2
            return value
    return None


def extract_budget(text: str) -> str:
    """Extract budget indicator from text."""
    for pattern in _BUDGET_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def extract_deliverables(text: str) -> list[str]:
    """Extract deliverable items from text."""
    deliverables = []
    # Look for numbered or bulleted lists after "deliverable" keywords
    sections = re.split(r"(?i)deliverable|deliver|output|work\s*product|milestone", text)
    if len(sections) > 1:
        for section in sections[1:]:
            # Extract bullet points
            items = re.findall(r"[-*\d.]+\s+(.+?)(?:\n|$)", section[:500])
            deliverables.extend(item.strip() for item in items[:10])
    return deliverables


def extract_regulatory_context(text: str) -> list[str]:
    """Extract mentioned regulatory frameworks."""
    found = []
    for kw in _REGULATORY_KEYWORDS:
        if re.search(re.escape(kw), text, re.IGNORECASE):
            found.append(kw)
    return found


def extract_skills(text: str) -> list[str]:
    """Extract required skills from text."""
    found = []
    for skill in _SKILL_KEYWORDS:
        if re.search(r"\b" + re.escape(skill) + r"\b", text, re.IGNORECASE):
            found.append(skill)
    return found


def detect_engagement_type(text: str) -> str:
    """Detect engagement type from text signals."""
    scores = {etype: 0 for etype in _ENGAGEMENT_TYPE_SIGNALS}
    t = text.lower()
    for etype, signals in _ENGAGEMENT_TYPE_SIGNALS.items():
        for signal in signals:
            scores[etype] += len(re.findall(r"\b" + re.escape(signal) + r"\b", t))
    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return "advisory"  # default
    # Check for hybrid (multiple types scoring high)
    top_scores = sorted(scores.values(), reverse=True)
    if top_scores[0] > 0 and top_scores[1] > 0 and top_scores[1] >= top_scores[0] * 0.5:
        return "hybrid"
    return best


def detect_risks(text: str, scope: ScopeResult) -> list[RiskFlag]:
    """Detect risk flags from text and extracted scope."""
    risks = []
    t = text.lower()

    # Timeline risk
    if scope.timeline_weeks and scope.timeline_weeks < 4:
        risks.append(RiskFlag("timeline", "Very short timeline (<4 weeks)", "high"))
    if "asap" in t or "urgent" in t or "immediately" in t:
        risks.append(RiskFlag("timeline", "Urgency language detected", "medium"))

    # Scope risk
    if len(scope.deliverables) > 5:
        risks.append(
            RiskFlag(
                "scope_creep",
                f"{len(scope.deliverables)} deliverables listed — scope may be too broad",
                "medium",
            )
        )
    if "phase 1" in t or "phase one" in t:
        risks.append(
            RiskFlag(
                "scope_creep", "Multi-phase engagement — scope boundaries need definition", "low"
            )
        )

    # Regulatory risk
    if len(scope.regulatory_context) > 3:
        risks.append(
            RiskFlag(
                "regulatory",
                f"Multiple regulatory frameworks ({len(scope.regulatory_context)}) — compliance overhead",
                "medium",
            )
        )

    # Resource risk
    if scope.team_size and scope.team_size > 10:
        risks.append(
            RiskFlag(
                "resource", f"Large team ({scope.team_size}) — coordination overhead", "medium"
            )
        )

    return risks


def scope_engagement(text: str, client: str = "Unknown") -> ScopeResult:
    """Parse engagement text and return structured scope."""
    result = ScopeResult(
        client=client,
        engagement_type=detect_engagement_type(text),
        summary=text[:200].strip(),
        deliverables=extract_deliverables(text),
        timeline_weeks=extract_timeline(text),
        budget_indicator=extract_budget(text),
        required_skills=extract_skills(text),
        regulatory_context=extract_regulatory_context(text),
        raw_text=text,
    )
    result.risk_flags = detect_risks(text, result)
    return result
