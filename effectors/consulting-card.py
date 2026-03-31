#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["openai"]
# ///
"""
Consulting Insight Card Generator.

Takes a topic, generates a structured consulting insight card
(problem, impact, approach, evidence, so-what) via an LLM call,
and writes it as a markdown file to the euchromatin consulting cards directory.

Usage:
    consulting-card.py "AI model risk governance in APAC banks"
    consulting-card.py --list
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

from openai import OpenAI

CARDS_DIR = (
    Path.home()
    / "epigenome"
    / "chromatin"
    / "euchromatin"
    / "consulting"
    / "cards"
)

SYSTEM_PROMPT = """\
You are a management consultant at a top-tier firm. Given a topic, produce a
structured insight card with exactly these five sections. Be specific, cite
real frameworks or examples where possible. Write in concise consulting prose —
no fluff, no hedging.

Sections (use these exact headers):
## Problem
What is the core challenge or unrecognised risk?

## Impact
What happens if this is not addressed? Quantify where possible.

## Approach
What should the client do? Give a concrete 2-4 step plan.

## Evidence
Cite 2-4 specific data points, case studies, regulatory references, or
industry benchmarks that support the insight.

## So What
One sentence: the actionable takeaway a decision-maker should remember.
"""

MODEL = "gpt-4.1-mini"


def slugify(text: str) -> str:
    """Convert a topic string into a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s_-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")[:80]


def generate_card(topic: str, model: str = MODEL) -> str:
    """Call the LLM and return the insight card body as markdown."""
    client = OpenAI()  # uses OPENAI_API_KEY env var
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Topic: {topic}"},
        ],
        temperature=0.7,
        max_tokens=2000,
    )
    return response.choices[0].message.content.strip()


def build_markdown(topic: str, body: str) -> str:
    """Wrap the LLM output in a complete markdown file with frontmatter."""
    today = date.today().isoformat()
    slug = slugify(topic)
    return f"""\
---
tags: [consulting-card, insight]
topic: "{topic}"
created: {today}
slug: {slug}
---

# Insight Card: {topic}

{body}
"""


def list_cards() -> list[Path]:
    """Return all existing card files sorted by name."""
    if not CARDS_DIR.exists():
        return []
    return sorted(CARDS_DIR.glob("*.md"))


def write_card(topic: str, body: str) -> Path:
    """Write the card to disk and return the path."""
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    slug = slugify(topic)
    filename = f"{today}-{slug}.md"
    path = CARDS_DIR / filename
    path.write_text(build_markdown(topic, body), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Generate a structured consulting insight card."
    )
    parser.add_argument(
        "topic",
        nargs="?",
        help="The topic to generate an insight card for.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing cards and exit.",
    )
    parser.add_argument(
        "--model",
        default=MODEL,
        help=f"LLM model to use (default: {MODEL}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the card to stdout without writing a file.",
    )
    args = parser.parse_args(argv)

    if args.list:
        cards = list_cards()
        if not cards:
            print("No cards found.")
        for card in cards:
            print(f"  {card.name}")
        return

    if not args.topic:
        parser.error("topic is required unless using --list")

    print(f"Generating insight card for: {args.topic}", file=sys.stderr)
    body = generate_card(args.topic, model=args.model)

    if args.dry_run:
        print(build_markdown(args.topic, body))
        return

    path = write_card(args.topic, body)
    print(f"Card written to: {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
