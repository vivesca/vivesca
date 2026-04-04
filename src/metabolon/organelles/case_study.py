"""case_study — package consulting use cases into presentation-ready formats.

Takes a use case markdown file and generates:
- Executive summary (1-paragraph)
- Challenge-Approach-Result arc
- Key metrics extraction
- Client-safe version (anonymised)
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

CONSULTING_DIR = Path.home() / "epigenome" / "chromatin" / "Consulting"
USE_CASE_DIR = CONSULTING_DIR / "Use Cases"


@dataclass
class CaseStudy:
    title: str
    challenge: str
    approach: str
    result: str
    metrics: list[str] = field(default_factory=list)
    domain: str = ""
    jurisdiction: str = ""
    source_file: str = ""
    anonymised: bool = False

    def to_executive_summary(self) -> str:
        """One-paragraph executive summary."""
        return (
            f"{self.title}: {self.challenge} Our approach: {self.approach} Result: {self.result}"
        )

    def to_car_arc(self) -> str:
        """Challenge-Approach-Result format."""
        lines = [
            f"# {self.title}",
            "",
            "## Challenge",
            self.challenge,
            "",
            "## Approach",
            self.approach,
            "",
            "## Result",
            self.result,
        ]
        if self.metrics:
            lines.extend(["", "## Key Metrics"])
            for m in self.metrics:
                lines.append(f"- {m}")
        return "\n".join(lines)

    def to_slide_notes(self) -> str:
        """Concise format for presentation slide notes."""
        lines = [
            f"**{self.title}**",
            f"Challenge: {self.challenge[:100]}",
            f"Approach: {self.approach[:100]}",
            f"Result: {self.result[:100]}",
        ]
        if self.metrics:
            lines.append(f"Metrics: {'; '.join(self.metrics[:3])}")
        return "\n".join(lines)


def _extract_section(text: str, heading: str) -> str:
    """Extract content under a markdown heading."""
    pattern = rf"(?:^|\n)#+\s*{re.escape(heading)}\s*\n(.*?)(?=\n#+\s|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def _extract_metrics(text: str) -> list[str]:
    """Extract quantitative metrics from text."""
    metrics = []
    # Look for percentage patterns
    for match in re.finditer(r"(\d+(?:\.\d+)?%\s*[^.]*)", text):
        metrics.append(match.group(1).strip()[:100])
    # Look for currency/number patterns with context
    for match in re.finditer(
        r"([\$\£\€HK]*\d+(?:,\d{3})*(?:\.\d+)?\s*[kKmMbB]?\s*[^.]{5,40})", text
    ):
        candidate = match.group(1).strip()[:100]
        if candidate not in metrics:
            metrics.append(candidate)
    return metrics[:10]


def _anonymise(text: str) -> str:
    """Remove client-specific identifiers."""
    # Replace common bank/company names with generic labels
    replacements = {
        r"\bHSBC\b": "[Major International Bank]",
        r"\bStandard Chartered\b": "[Regional Bank]",
        r"\bCapco\b": "[Consulting Partner]",
        r"\bCNCBI\b": "[Previous Employer]",
    }
    result = text
    for pattern, replacement in replacements.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def package_use_case(file_path: str | Path, anonymise: bool = False) -> CaseStudy:
    """Package a use case markdown file into a CaseStudy.

    Args:
        file_path: Path to the use case markdown file.
        anonymise: Whether to replace client names with generic labels.
    """
    path = Path(file_path)
    if not path.exists():
        return CaseStudy(
            title=path.stem,
            challenge="File not found",
            approach="",
            result="",
            source_file=str(path),
        )

    text = path.read_text(encoding="utf-8")
    if anonymise:
        text = _anonymise(text)

    # Extract title
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = title_match.group(1) if title_match else path.stem

    # Extract domain from frontmatter
    domain_match = re.search(r"domain:\s*(.+)", text)
    domain = domain_match.group(1).strip() if domain_match else ""

    jurisdiction_match = re.search(r"jurisdiction:\s*(.+)", text)
    jurisdiction = jurisdiction_match.group(1).strip() if jurisdiction_match else ""

    # Try to extract C-A-R sections
    challenge = (
        _extract_section(text, "Challenge")
        or _extract_section(text, "Problem")
        or _extract_section(text, "Context")
    )
    approach = (
        _extract_section(text, "Approach")
        or _extract_section(text, "Solution")
        or _extract_section(text, "Method")
    )
    result = (
        _extract_section(text, "Result")
        or _extract_section(text, "Outcome")
        or _extract_section(text, "Impact")
    )

    # If no structured sections, use first paragraphs
    if not challenge:
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
        if len(paragraphs) >= 1:
            challenge = paragraphs[0][:300]
        if len(paragraphs) >= 2 and not approach:
            approach = paragraphs[1][:300]
        if len(paragraphs) >= 3 and not result:
            result = paragraphs[2][:300]

    return CaseStudy(
        title=title,
        challenge=challenge,
        approach=approach,
        result=result,
        metrics=_extract_metrics(text),
        domain=domain,
        jurisdiction=jurisdiction,
        source_file=str(path),
        anonymised=anonymise,
    )


def generate_from_template(
    title: str,
    context: str,
    action: str,
    result: str,
    metrics: list[str] | None = None,
    domain: str = "",
    jurisdiction: str = "",
) -> CaseStudy:
    """Generate a CaseStudy from CAR framework components (Context, Action, Result).

    The CAR framework structures case studies as:
    - Context: The background situation and challenges faced
    - Action: What was done to address the situation
    - Result: The outcomes and impact achieved

    Args:
        title: Title of the case study.
        context: Background context and challenges (CAR - Context).
        action: Actions taken to address the situation (CAR - Action).
        result: Results and outcomes achieved (CAR - Result).
        metrics: Optional list of key metrics/outcomes.
        domain: Optional domain classification (e.g., "Banking", "Healthcare").
        jurisdiction: Optional jurisdiction/region.

    Returns:
        A CaseStudy instance with CAR framework mapped to internal fields.
    """
    return CaseStudy(
        title=title,
        challenge=context,  # CAR Context maps to challenge
        approach=action,  # CAR Action maps to approach
        result=result,  # CAR Result maps to result
        metrics=metrics or [],
        domain=domain,
        jurisdiction=jurisdiction,
        source_file="",
        anonymised=False,
    )


def list_use_cases() -> list[dict]:
    """List available use case files."""
    if not USE_CASE_DIR.exists():
        return []
    cases = []
    for f in sorted(USE_CASE_DIR.glob("*.md")):
        cases.append({"filename": f.name, "path": str(f), "title": f.stem})
    return cases
