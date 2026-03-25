#!/usr/bin/env python3
"""Detective control: LLM-based PII audit of staged or committed code.

Complements the regex pre-commit hook (preventive) by catching novel
PII patterns the regex doesn't know about. Runs as a periodic check
or on-demand before making a repo public.

Usage:
    python scripts/audit-pii.py              # audit all tracked files
    python scripts/audit-pii.py --staged     # audit staged changes only
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


# Inline to avoid import dependency on vivesca itself
def _query_llm(prompt: str) -> str:
    """Query LLM via synthase for cheap classification."""
    result = subprocess.run(
        ["synthase", "--timeout", "60", prompt],
        capture_output=True,
        text=True,
        timeout=65,
    )
    return result.stdout.strip()


def _get_files(staged: bool) -> list[str]:
    if staged:
        cmd = ["git", "diff", "--cached", "--name-only"]
    else:
        cmd = ["git", "ls-files", "--", "src/", "assays/"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return [f for f in result.stdout.strip().split("\n") if f.endswith(".py")]


def _audit_file(path: str) -> str | None:
    content = Path(path).read_text()
    if len(content) > 8000:
        content = content[:8000]

    prompt = f"""Review this Python source file for personally identifiable information (PII).

PII includes: real names, home addresses, phone numbers, email addresses,
social media handles, employer names, bank account details, government IDs,
hardcoded filesystem paths containing usernames (e.g., /Users/someone).

Exclude:
- Generic placeholders (Jane Doe, user@example.com, /home/user)
- Bank names used as parser identifiers (hsbc, mox, ccba)
- Config imports (user_name(), vault_dir()) -- these are parameterised

Reply with ONLY one of:
- "CLEAN" if no PII found
- "PII: <description>" if PII found (be specific about what and where)

File: {path}
```python
{content}
```"""

    return _query_llm(prompt)


def _extract_pattern(finding: str) -> str | None:
    """Ask LLM to derive a regex pattern from a PII finding.

    Antigen presentation: adaptive immunity teaches innate immunity.
    """
    prompt = f"""A PII audit found this in source code:
{finding}

Derive a single regex pattern that would catch this PII in future commits.
The pattern should be specific enough to avoid false positives but general
enough to catch variants (e.g., different casings, slight reformatting).

Reply with ONLY the regex pattern, nothing else. No explanation."""

    pattern = _query_llm(prompt)
    # Basic sanity: must be non-empty, no newlines, looks like regex
    if pattern and "\n" not in pattern and len(pattern) < 100:
        return pattern
    return None


def _present_antigen(findings: list[tuple[str, str]], patterns_file: Path) -> int:
    """Feed novel findings back to the innate immune system (pii-patterns.txt).

    Returns the number of new patterns added.
    """
    if not patterns_file.exists():
        return 0

    existing = patterns_file.read_text()
    new_patterns = []

    for path, detail in findings:
        pattern = _extract_pattern(detail)
        if pattern and pattern not in existing:
            new_patterns.append(f"# Auto-learned from {path}\n{pattern}")

    if new_patterns:
        with open(patterns_file, "a") as f:
            f.write("\n# -- Antigen presentation (auto-learned) --\n")
            for p in new_patterns:
                f.write(p + "\n")

    return len(new_patterns)


def main():
    parser = argparse.ArgumentParser(description="LLM-based PII audit")
    parser.add_argument("--staged", action="store_true", help="Audit staged files only")
    parser.add_argument(
        "--no-learn",
        action="store_true",
        help="Don't update pii-patterns.txt with findings",
    )
    args = parser.parse_args()

    patterns_file = Path(
        os.environ.get(
            "VIVESCA_PII_PATTERNS",
            Path.home() / ".config" / "vivesca" / "pii-patterns.txt",
        )
    )

    files = _get_files(args.staged)
    if not files:
        print("No files to audit.")
        return

    print(f"Auditing {len(files)} files...")
    findings = []

    for path in files:
        if not Path(path).exists():
            continue
        result = _audit_file(path)
        if result and not result.startswith("CLEAN"):
            findings.append((path, result))
            print(f"  FOUND: {path} -- {result}")
        else:
            print(f"  clean: {path}")

    print(f"\n{'=' * 40}")
    if findings:
        print(f"PII detected in {len(findings)} file(s):")
        for path, detail in findings:
            print(f"  {path}: {detail}")

        if not args.no_learn:
            learned = _present_antigen(findings, patterns_file)
            if learned:
                print(f"\nAntigen presentation: {learned} new pattern(s) added to {patterns_file}")
                print("Future commits will be caught by the regex pre-commit hook.")

        sys.exit(1)
    else:
        print("All files clean.")


if __name__ == "__main__":
    main()
