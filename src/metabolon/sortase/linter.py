"""Plan file linter with structured issue reporting.

Checks plan files for common problems: missing sections, forbidden
paths, placeholder markers, and absent do-NOT instructions.
"""

import re
from dataclasses import dataclass


@dataclass
class LintIssue:
    """A single lint finding from a plan file."""

    severity: str  # "error", "warning", or "info"
    message: str
    line_number: int | None = None

    def __str__(self) -> str:
        loc = f":{self.line_number}" if self.line_number is not None else ""
        return f"[{self.severity.upper()}]{loc} {self.message}"


def lint_plan(plan_text: str) -> list[LintIssue]:
    """Check a plan file for common issues.

    Returns a list of LintIssue objects sorted by severity (error first).
    An empty list means no issues found.
    """
    issues: list[LintIssue] = []

    if not plan_text.strip():
        issues.append(LintIssue("error", "Plan file is empty"))
        return issues

    lines = plan_text.splitlines()
    text = plan_text.strip()
    text_lower = text.lower()

    _check_output_path(text, issues)
    _check_constraints_section(text, issues)
    _check_verification_command(text, issues)
    _check_tmp_references(lines, issues)
    _check_placeholder_markers(lines, issues)
    _check_do_not_instructions(text_lower, issues)
    _check_file_paths(text, issues)

    severity_order = {"error": 0, "warning": 1, "info": 2}
    issues.sort(key=lambda issue: severity_order.get(issue.severity, 9))
    return issues


def format_lint_report(issues: list[LintIssue]) -> str:
    """Format lint issues into a human-readable report grouped by severity."""
    if not issues:
        return "No issues found."

    grouped: dict[str, list[LintIssue]] = {}
    for issue in issues:
        grouped.setdefault(issue.severity, []).append(issue)

    parts: list[str] = []
    for severity in ("error", "warning", "info"):
        group = grouped.get(severity, [])
        if not group:
            continue
        label = severity.upper()
        count = len(group)
        header = f"{label}S ({count})" if count > 1 else f"{label}"
        lines = [header]
        lines.append("=" * len(header))
        for issue in group:
            loc = f" (line {issue.line_number})" if issue.line_number is not None else ""
            lines.append(f"  {issue.message}{loc}")
        parts.append("\n".join(lines))

    total = len(issues)
    summary = f"\n{total} issue(s) found."
    return "\n\n".join(parts) + summary


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

_OUTPUT_INDICATORS = [
    r"(?i)output\s+path",
    r"(?i)write\s+(?:the\s+result\s+)?to\b",
    r"(?i)save\s+to\b",
    r"(?i)deliverable\b",
    r"(?:^|\n)\s*##\s*Output\b",
]

_CONSTRAINTS_PATTERN = re.compile(r"(?i)^#{1,3}\s*constraints?\b", re.MULTILINE)

_VERIFICATION_PATTERN = re.compile(r"(?i)^#{1,3}\s*verification\b", re.MULTILINE)

_DO_NOT_PATTERN = re.compile(r"(?i)\bdo\s+not\b|\bdon't\b|\bmust\s+not\b|\bnever\b")

_FILE_PATH_PATTERN = re.compile(r"(?:~/|/)(?:[\w.-]+/)+[\w.-]+\.\w+")


def _check_output_path(text: str, issues: list[LintIssue]) -> None:
    if not any(re.search(pattern, text) for pattern in _OUTPUT_INDICATORS):
        issues.append(LintIssue("warning", "No output path specified"))


def _check_constraints_section(text: str, issues: list[LintIssue]) -> None:
    if not _CONSTRAINTS_PATTERN.search(text):
        issues.append(LintIssue("warning", "No constraints section found"))


def _check_verification_command(text: str, issues: list[LintIssue]) -> None:
    if not _VERIFICATION_PATTERN.search(text):
        issues.append(LintIssue("warning", "No verification command found"))


def _check_tmp_references(lines: list[str], issues: list[LintIssue]) -> None:
    for line_number, line in enumerate(lines, start=1):
        for match in re.finditer(r"/tmp/[\w/.-]+", line):
            path = match.group()
            issues.append(
                LintIssue(
                    "error",
                    f"References /tmp/ path: {path} — use ~/germline/loci/plans/ instead",
                    line_number,
                )
            )


_NEGATION_BEFORE_MARKER = re.compile(r"(?i)\b(?:do\s+not|don'?t|never)\b.*\b(?:TODO|FIXME)\b")


def _check_placeholder_markers(lines: list[str], issues: list[LintIssue]) -> None:
    for line_number, line in enumerate(lines, start=1):
        for marker in ("TODO", "FIXME"):
            if re.search(rf"\b{marker}\b", line) and not _NEGATION_BEFORE_MARKER.search(line):
                issues.append(
                    LintIssue(
                        "error",
                        f"Contains placeholder marker: {marker}",
                        line_number,
                    )
                )


def _check_do_not_instructions(text_lower: str, issues: list[LintIssue]) -> None:
    if not _DO_NOT_PATTERN.search(text_lower):
        issues.append(
            LintIssue(
                "info",
                "No 'do NOT' instructions found — consider adding constraints on what to avoid",
            )
        )


def _check_file_paths(text: str, issues: list[LintIssue]) -> None:
    if not _FILE_PATH_PATTERN.search(text):
        issues.append(LintIssue("info", "No file paths found in plan — specify target files"))
