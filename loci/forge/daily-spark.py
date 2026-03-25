#!/usr/bin/env python3
"""Daily spark agent — scans lustro output + calendar, appends sparks to _sparks.md.

Uses claude --print (Max20 plan) instead of Anthropic API directly.
Idempotency: writes under date headers. Duplicate runs for same date are harmless.
"""

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# --- Paths ---
AI_NEWS_LOG = Path.home() / "notes/AI News Log.md"
SPARKS = Path.home() / "notes/Consulting/_sparks.md"
CONSULTING = Path.home() / "notes/Consulting"

TODAY = datetime.now().strftime("%Y-%m-%d")
TODAY_HEADER = f"## {TODAY}"


def get_recent_news(hours: int = 28) -> str:
    """Extract last ~24h of AI news (with 4h buffer for timezone/timing)."""
    if not AI_NEWS_LOG.exists():
        return "(no AI news log found)"

    lines = AI_NEWS_LOG.read_text().splitlines()
    # Walk backwards to find entries from the last ~28 hours
    # News log uses date headers like "## 2026-03-19" or similar
    cutoff = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d")
    recent = []
    capturing = False
    for line in lines:
        if line.startswith("## ") and line[3:13] >= cutoff:
            capturing = True
        if capturing:
            recent.append(line)

    return "\n".join(recent[-200:]) if recent else "(no recent news)"


def get_calendar() -> str:
    """Get today + tomorrow calendar via fasti."""
    try:
        result = subprocess.run(
            ["fasti", "list", "--days", "2"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return result.stdout.strip() or "(no events)"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "(calendar unavailable)"


def get_existing_sparks() -> str:
    """Read existing sparks for dedup context."""
    if not SPARKS.exists():
        return "(no existing sparks)"
    text = SPARKS.read_text()
    # Only return last 100 lines for context window
    lines = text.splitlines()
    return "\n".join(lines[-100:])


def already_ran_today() -> bool:
    """Check if today's date header already exists in sparks."""
    if not SPARKS.exists():
        return False
    return TODAY_HEADER in SPARKS.read_text()


def notify(msg: str) -> None:
    """Send notification via deltos (matching garden-auto.py pattern)."""
    try:
        subprocess.run(
            f'echo "{msg}" | deltos "forge-spark"',
            shell=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def main():
    # Idempotency: skip if already ran today (but don't fail)
    if already_ran_today():
        print(f"Already ran for {TODAY}, skipping.")
        return

    # Ensure _sparks.md exists
    if not SPARKS.exists():
        SPARKS.parent.mkdir(parents=True, exist_ok=True)
        SPARKS.write_text("# Sparks\n\nDaily agent output.\n\n---\n\n")

    news = get_recent_news()
    calendar = get_calendar()
    existing = get_existing_sparks()

    prompt = f"""You are a daily intelligence agent for an AI governance consultant at Capco (financial services).

Scan today's AI news and calendar. Produce sparks — concise flags for a weekly batch that creates consulting IP.

## Today's AI News (last 24h)
{news}

## Calendar (today + tomorrow)
{calendar}

## Existing sparks (for dedup — don't repeat these)
{existing}

## Output format

Write a date-headed section. Each spark is one line with a tag:

```
## {TODAY}

### Talking Points
- [meeting name]: [bullet point relevant to that meeting]

### Sparks
- #policy-gap — [regulatory news with P&P implications]
- #architecture — [new tool/pattern worth documenting]
- #use-case — [FS AI application spotted]
- #experiment-idea — [something worth testing]
- #garden-seed — [opinionated take worth writing about]
- #linkedin-seed — [hook + 3 bullets + suggested angle — NEVER a full post]
- #competitor — [McKinsey/Deloitte/EY/Accenture AI governance move]
```

Rules:
- Only include tags that have genuine signal. Skip empty categories.
- If nothing notable today, write: `## {TODAY}\\n- Nothing notable`
- Be concise — each spark is 1-2 lines max.
- LinkedIn seeds: hook + 3 bullets + angle. NEVER a full post draft.
- Don't fabricate signal. Silence is fine.
- Focus on financial services AI governance relevance."""

    # Use max20 CLI wrapper (handles Max20 auth — strips CLAUDECODE + ANTHROPIC_API_KEY)
    result = subprocess.run(
        ["/Users/terry/reticulum/bin/max20", "sonnet", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        print(f"claude --print failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    output = result.stdout.strip()

    # Append to _sparks.md
    with open(SPARKS, "a") as f:
        f.write(f"\n{output}\n")

    # Count actual sparks (lines starting with "- #")
    spark_count = sum(1 for line in output.splitlines() if line.strip().startswith("- #"))
    print(f"Wrote {spark_count} sparks for {TODAY}")

    # Only notify on failure or zero sparks (anomaly). Normal runs are silent.
    if spark_count == 0:
        notify(f"Forge spark: nothing notable for {TODAY} (check sources?)")


if __name__ == "__main__":
    main()
